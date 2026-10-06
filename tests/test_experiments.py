"""E-03, E-02 por repetición (B-02) y orquestación de la selección con datos sintéticos."""

import numpy as np
import pandas as pd
import pytest

from churn import experiments, tune
from churn.split import make_split

FAST = {"rf": {"n_estimators": 10}, "xgb": {"n_estimators": 10}}


def folds(values):
    return [
        {"repeat": i // 5, "fold": i % 5 + 1, "metrics": {"ap": value}}
        for i, value in enumerate(values)
    ]


def test_paired_deltas_and_mismatch():
    result = experiments.paired_deltas(folds([0.5] * 10), folds([0.49] * 5 + [0.52] * 5))
    assert result["mean"] == pytest.approx(0.005)
    assert (result["positive"], result["negative"]) == (5, 5)
    with pytest.raises(ValueError):
        experiments.paired_deltas(folds([0.5] * 10), folds([0.5] * 9))


def test_e03_threshold_is_inclusive():
    assert experiments.e03_decision(-0.005) is True
    assert experiments.e03_decision(0.01) is True
    assert experiments.e03_decision(-0.0051) is False


def test_ap_by_repeat_matches_b02_reference():
    oof = pd.DataFrame(
        {
            "CustomerId": [1, 2, 3, 4] * 2,
            "repeat": [0] * 4 + [1] * 4,
            "y": [0, 1, 0, 1] * 2,
            "proba": [0.1, 0.9, 0.7, 0.6, 0.8, 0.7, 0.2, 0.5],
        }
    )
    result = experiments.ap_by_repeat(oof)
    assert result["by_repeat"] == pytest.approx({0: 0.833333, 1: 0.583333}, abs=1e-6)
    assert result["mean"] == pytest.approx(0.708333, abs=1e-6)


def test_e02_segments_by_repeat():
    ids = list(range(1, 9))
    products = pd.Series([1, 2, 1, 2, 3, 4, 3, 1], index=ids)
    y = [0, 1, 0, 1, 1, 1, 0, 0]
    oof = pd.DataFrame(
        {
            "CustomerId": ids * 2,
            "repeat": [0] * 8 + [1] * 8,
            "y": y * 2,
            "proba": [
                *[0.1, 0.8, 0.2, 0.7, 0.9, 0.95, 0.6, 0.3],
                *[0.2, 0.7, 0.1, 0.6, 0.8, 0.9, 0.7, 0.4],
            ],
        }
    )
    result = experiments.e02_segments(oof, products)
    assert result["n_all"] == 8 and result["n_without_3_4"] == 5
    group = result["c_group_3_4"]
    assert group["n"] == 3 and group["observed_rate"] == pytest.approx(2 / 3)
    assert group["mean_predicted_by_repeat"] == pytest.approx({0: 0.816667, 1: 0.8}, abs=1e-6)
    assert result["b_ap_without_3_4"]["by_repeat"][0] == pytest.approx(1.0)
    with pytest.raises(ValueError, match="repetido"):
        experiments.e02_segments(pd.concat([oof, oof.iloc[:1]]), products)
    with pytest.raises(ValueError, match="sin NumOfProducts"):
        experiments.e02_segments(oof, products.drop(8))


@pytest.fixture
def partitions(valid_df):
    split = make_split(valid_df)
    training = valid_df.iloc[split["train"]].reset_index(drop=True)
    validation = valid_df.iloc[split["validation"]].reset_index(drop=True)
    return training, validation


def test_run_selection_end_to_end(partitions, monkeypatch, tmp_path):
    training, validation = partitions
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{(tmp_path / 't.db').as_posix()}")
    origin = {"git_commit": "a" * 40, "csv_sha256": "b" * 64, "split_manifest_sha256": "c" * 64}
    monkeypatch.setattr(experiments, "provenance", lambda: origin)
    tuning, oof = tune.run_tuning(training, n_iter=1, fixed_override=FAST, log=False)
    result = experiments.run_selection(tuning, oof, training, validation)
    chosen = result["steps_1_2"]["chosen"]
    assert chosen in {"logreg", "rf", "xgb"}
    assert set(result["validation_ap"]) >= {"dummy", chosen}
    assert result["final_model"] in {None, "logreg", chosen}
    assert result["e03"]["drop_salary"] == (result["e03"]["deltas"]["mean"] >= -0.005)
    assert ("EstimatedSalary" in result["final_exclude"]) == result["e03"]["drop_salary"]
    assert "NumOfProducts" in result["final_features"]
    assert np.isclose(
        result["e02"]["b_ap_all"]["mean"],
        np.mean(list(result["e02"]["b_ap_all"]["by_repeat"].values())),
    )
    assert set(result["run_ids"]) == {"e03", "e02", "selection"}


def test_load_validation_filters_partition(valid_df, monkeypatch):
    frame = valid_df.assign(partition=["train", "validation"] * (len(valid_df) // 2))
    monkeypatch.setattr(experiments, "load_exploration", lambda: frame)
    assert set(experiments.load_validation()["partition"]) == {"validation"}


def test_main_writes_selection(monkeypatch, tmp_path, partitions):
    training, validation = partitions
    tuning, oof = tune.run_tuning(training, n_iter=1, fixed_override=FAST, log=False)
    import json

    import churn.train as train_module

    (tmp_path / "tuning.json").write_text(json.dumps(tune.jsonable(tuning)), encoding="utf-8")
    oof.to_parquet(tmp_path / "oof.parquet")
    monkeypatch.setattr(experiments, "TUNING_FILE", tmp_path / "tuning.json")
    monkeypatch.setattr(experiments, "OOF_FILE", tmp_path / "oof.parquet")
    monkeypatch.setattr(experiments, "SELECTION_FILE", tmp_path / "selection.json")
    monkeypatch.setattr(train_module, "load_training", lambda: training)
    monkeypatch.setattr(experiments, "load_validation", lambda: validation)
    original = experiments.run_selection
    monkeypatch.setattr(experiments, "run_selection", lambda *args: original(*args, log=False))
    assert experiments.main() == 0
    assert (tmp_path / "selection.json").exists()
