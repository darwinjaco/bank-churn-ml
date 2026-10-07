"""Evaluación final: una sola vez y con verificación del manifiesto (datos sintéticos)."""

import json

import joblib
import pytest

from churn import final_eval
from churn.calibration import CalibratedModel, IdentityCalibrator
from churn.config import FEATURE_SETS, TARGET
from churn.pipeline import build_pipeline
from churn.split import build_manifest, make_split


@pytest.fixture
def setup(valid_df, csv_path, tmp_path, monkeypatch):
    split = make_split(valid_df)
    (tmp_path / "split.json").write_text(json.dumps(split), encoding="utf-8")
    monkeypatch.setattr("churn.split.RAW_FILE", csv_path)
    manifest = build_manifest(valid_df, split)
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return {
        "split": tmp_path / "split.json",
        "manifest": tmp_path / "manifest.json",
        "csv": csv_path,
    }


def test_load_test_once_checks_manifest_and_refuses_reuse(setup, tmp_path, valid_df):
    final = tmp_path / "final.json"
    test = final_eval.load_test_once(final, setup["split"], setup["manifest"], setup["csv"])
    assert len(test) == len(make_split(valid_df)["test"]) and "Gender" not in test.columns
    final.write_text("{}", encoding="utf-8")
    with pytest.raises(final_eval.FinalEvaluationDoneError):
        final_eval.load_test_once(final, setup["split"], setup["manifest"], setup["csv"])
    manifest = json.loads(setup["manifest"].read_text(encoding="utf-8"))
    manifest["partitions"]["test"]["customer_ids_sha256"] = "0" * 64
    setup["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="manifiesto"):
        final_eval.load_test_once(
            tmp_path / "x.json", setup["split"], setup["manifest"], setup["csv"]
        )


def test_main_runs_once_and_updates_metadata(setup, valid_df, tmp_path, monkeypatch):
    columns = [c for c in FEATURE_SETS["tree"] if c != "EstimatedSalary"]
    pipeline = build_pipeline(
        "rf", "tree", exclude=("EstimatedSalary",), params={"n_estimators": 10, "max_depth": 3}
    ).fit(valid_df[columns], valid_df[TARGET])
    joblib.dump(CalibratedModel(pipeline, IdentityCalibrator(), columns), tmp_path / "m.joblib")
    metadata = {
        "model_family": "rf",
        "git_commit": "d" * 40,
        "threshold": 1 / 6,
        "final_test_evaluation": "pendiente",
    }
    (tmp_path / "meta.json").write_text(json.dumps(metadata), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{(tmp_path / 't.db').as_posix()}")
    origin = {"git_commit": "a" * 40, "csv_sha256": "b" * 64, "split_manifest_sha256": "c" * 64}
    monkeypatch.setattr(final_eval, "provenance", lambda: origin)
    for name, value in {
        "MODEL_FILE": tmp_path / "m.joblib",
        "METADATA_FILE": tmp_path / "meta.json",
        "METADATA_COPY": tmp_path / "meta_copy.json",
        "FINAL_FILE": tmp_path / "final.json",
        "SPLIT_FILE": setup["split"],
        "MANIFEST_FILE": setup["manifest"],
        "RAW_FILE": setup["csv"],
    }.items():
        monkeypatch.setattr(final_eval, name, value)
    assert final_eval.main() == 0
    payload = json.loads((tmp_path / "final.json").read_text(encoding="utf-8"))
    assert payload["final"] is True and payload["run_id"]
    assert set(payload["metrics"]) == {"ap", "roc_auc", "brier", "log_loss"}
    updated = json.loads((tmp_path / "meta.json").read_text(encoding="utf-8"))
    assert updated["final_test_evaluation"].startswith("completada")
    assert updated == json.loads((tmp_path / "meta_copy.json").read_text(encoding="utf-8"))
    with pytest.raises(final_eval.FinalEvaluationDoneError):
        final_eval.main()
    (tmp_path / "final.json").unlink()
    with pytest.raises(final_eval.FinalEvaluationDoneError, match="metadata"):
        final_eval.main()
