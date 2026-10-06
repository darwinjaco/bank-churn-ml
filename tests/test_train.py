"""CV de entrenamiento y tracking aislado de las corridas locales reales."""

import json

import numpy as np
import pytest
from mlflow.tracking import MlflowClient
from sklearn.model_selection import StratifiedKFold

from churn import train
from churn.config import FEATURE_SETS, RANDOM_SEED, TARGET
from churn.pipeline import build_pipeline
from churn.split import make_split


@pytest.fixture
def temporary_tracking(monkeypatch, tmp_path):
    # Aísla también cualquier directorio de artefactos predeterminado del SDK.
    monkeypatch.chdir(tmp_path)
    uri = f"sqlite:///{(tmp_path / 'tracking.db').as_posix()}"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", uri)
    return MlflowClient(tracking_uri=uri)


@pytest.fixture
def provenance():
    return {"git_commit": "a" * 40, "csv_sha256": "b" * 64, "split_manifest_sha256": "c" * 64}


def test_dummy_metrics_determinism_and_sample_std(valid_df):
    pipeline = build_pipeline("dummy", "raw")
    x, y = valid_df[FEATURE_SETS["raw"]], valid_df[TARGET]
    first = train.cross_validate_model(pipeline, x, y)
    assert first == train.cross_validate_model(pipeline, x, y)
    assert first["summary"]["roc_auc"] == {"mean": 0.5, "std": 0.0}
    assert first["summary"]["ap"]["mean"] == pytest.approx(y.mean(), abs=0.02)
    for name, summary in first["summary"].items():
        values = [fold["metrics"][name] for fold in first["folds"]]
        assert summary["std"] == np.std(values, ddof=1)
    assert not hasattr(pipeline.named_steps["model"], "classes_")


def test_folds_identical_for_models_and_match_protocol(valid_df):
    x, y = valid_df[FEATURE_SETS["raw"]], valid_df[TARGET]
    first = train.cross_validate_model(build_pipeline("dummy", "raw"), x, y)
    second = train.cross_validate_model(build_pipeline("logreg", "eda"), x, y)
    expected = StratifiedKFold(5, shuffle=True, random_state=RANDOM_SEED).split(x, y)
    for a, b, (fitting, scoring) in zip(first["folds"], second["folds"], expected, strict=True):
        assert a["fit_indices_sha256"] == b["fit_indices_sha256"] == train._indices_hash(fitting)
        assert (
            a["score_indices_sha256"] == b["score_indices_sha256"] == train._indices_hash(scoring)
        )


def test_training_loader_excludes_validation_and_reserved_customers(valid_df, monkeypatch):
    split = make_split(valid_df)
    exploration = valid_df.iloc[split["train"] + split["validation"]].copy()
    exploration["partition"] = ["train"] * len(split["train"]) + ["validation"] * len(
        split["validation"]
    )
    monkeypatch.setattr(train, "load_exploration", lambda: exploration)
    loaded = train.load_training()
    assert set(loaded["CustomerId"]) == set(valid_df.iloc[split["train"]]["CustomerId"])
    excluded = valid_df.iloc[split["validation"] + split["test"]]["CustomerId"]
    assert not set(loaded["CustomerId"]) & set(excluded)
    assert set(loaded["partition"]) == {"train"}
    assert not hasattr(train, "load_test") and not hasattr(train, "load_validation")


@pytest.mark.parametrize(
    ("model", "feature_set", "eligible"), [("dummy", "raw", "false"), ("logreg", "eda", "true")]
)
def test_mlflow_required_fields(
    valid_df, temporary_tracking, provenance, model, feature_set, eligible
):
    pipeline = build_pipeline(model, feature_set)
    metrics = train.cross_validate_model(
        pipeline, valid_df[FEATURE_SETS[feature_set]], valid_df[TARGET]
    )
    run_id = train.log_run(model, feature_set, pipeline, metrics, provenance)
    run = temporary_tracking.get_run(run_id)
    assert run.info.status == "FINISHED"
    assert run.data.params["model"] == model
    assert run.data.params["feature_set"] == feature_set
    assert run.data.params["n_folds"] == "5" and run.data.params["seed"] == "42"
    for name, value in pipeline.named_steps["model"].get_params(deep=False).items():
        assert run.data.params[name] == str(value)
    for key, value in provenance.items():
        assert run.data.tags[key] == value
    assert run.data.tags["stage"] == "baseline"
    assert run.data.tags["eligible"] == eligible and run.data.tags["final"] == "false"
    for name, summary in metrics["summary"].items():
        assert run.data.metrics[f"{name}_mean"] == summary["mean"]
        assert run.data.metrics[f"{name}_std"] == summary["std"]
        history = sorted(
            temporary_tracking.get_metric_history(run_id, name), key=lambda point: point.step
        )
        assert [point.step for point in history] == [1, 2, 3, 4, 5]
        assert [point.value for point in history] == [
            fold["metrics"][name] for fold in metrics["folds"]
        ]
    # Reutilizar el experimento también está cubierto, siempre dentro de tmp_path.
    assert train.log_run(model, feature_set, pipeline, metrics, provenance) != run_id


def test_cli_runs_exactly_three_baselines(valid_df, temporary_tracking, monkeypatch, tmp_path):
    data = valid_df.assign(partition="train")
    monkeypatch.setattr(train, "load_training", lambda: data)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"csv_sha256": "b" * 64}), encoding="utf-8")
    monkeypatch.setattr(train, "MANIFEST_FILE", manifest)
    monkeypatch.setattr(train, "BASELINES_FILE", tmp_path / "baselines.json")
    monkeypatch.setattr(train, "_git_commit", lambda: "a" * 40)
    assert train.main() == 0
    report = json.loads(train.BASELINES_FILE.read_text(encoding="utf-8"))
    assert report["n_training"] == len(data)
    assert [run["name"] for run in report["runs"]] == ["dummy-raw", "logreg-raw", "logreg-eda"]
    assert all(len(run["folds"]) == 5 and run["final"] is False for run in report["runs"])
    assert all(
        temporary_tracking.get_run(run["run_id"]).info.status == "FINISHED"
        for run in report["runs"]
    )
