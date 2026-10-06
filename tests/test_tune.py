"""Ajuste en dos fases con presupuesto reducido sobre datos sintéticos."""

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import StratifiedKFold

from churn import tune
from churn.config import TARGET

FAST = {"rf": {"n_estimators": 10}, "xgb": {"n_estimators": 10}}


@pytest.fixture
def training(valid_df):
    return valid_df.reset_index(drop=True)


@pytest.fixture
def tracking(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{(tmp_path / 't.db').as_posix()}")
    monkeypatch.setattr(
        tune,
        "provenance",
        lambda: {"git_commit": "a" * 40, "csv_sha256": "b" * 64, "split_manifest_sha256": "c" * 64},
    )


def test_phase_b_folds_are_identical_and_differ_from_phase_a(training):
    x, y = training, training[TARGET]
    first = tune.phase_b_splits(x, y)
    second = tune.phase_b_splits(x, y)
    assert len(first) == 10
    assert [(r, f) for r, f, _, _ in first] == [(r, f) for r in (0, 1) for f in range(1, 6)]
    for a, b in zip(first, second, strict=True):
        np.testing.assert_array_equal(a[3], b[3])
    phase_a = [set(s) for _, s in StratifiedKFold(5, shuffle=True, random_state=42).split(x, y)]
    assert any(set(scoring) not in phase_a for _, _, _, scoring in first)
    for repeat in (0, 1):
        scored = np.concatenate([s for r, _, _, s in first if r == repeat])
        assert sorted(scored) == list(range(len(training)))


@pytest.mark.parametrize("family", ["logreg", "rf", "xgb"])
def test_tune_family_returns_fixed_and_sampled_params(training, family):
    result = tune.tune_family(family, training, n_iter=2, fixed_override=FAST.get(family))
    assert result["family"] == family and result["n_iter"] == 2
    assert 0 <= result["search_ap_optimistic"] <= 1
    fixed = tune.SEARCH_SPACES[family]["fixed"]
    for key in fixed:
        assert key in result["best_params"]
    for key in tune.SEARCH_SPACES[family]["distributions"]:
        assert key in result["best_params"]


def test_reevaluate_oof_one_prediction_per_customer_and_repeat(training):
    params = {**tune.SEARCH_SPACES["xgb"]["fixed"], "n_estimators": 10}
    result = tune.reevaluate("xgb", params, training)
    oof = result["oof"]
    assert list(oof.columns) == ["CustomerId", "repeat", "fold", "y", "proba"]
    assert len(result["folds"]) == 10
    for repeat in (0, 1):
        part = oof[oof["repeat"] == repeat]
        assert part["CustomerId"].is_unique and len(part) == len(training)
    assert result["summary"]["ap"]["std"] == pytest.approx(
        np.std([f["metrics"]["ap"] for f in result["folds"]], ddof=1)
    )
    again = tune.reevaluate("xgb", params, training)
    pd.testing.assert_frame_equal(oof, again["oof"])


def test_reevaluate_with_exclusion(training):
    params = {**tune.SEARCH_SPACES["rf"]["fixed"], "n_estimators": 10}
    result = tune.reevaluate("rf", params, training, exclude=("EstimatedSalary",))
    assert result["exclude"] == ["EstimatedSalary"]


def test_run_tuning_logs_and_returns_all_families(training, tracking):
    payload, oof = tune.run_tuning(training, n_iter=2, fixed_override=FAST)
    assert list(payload["families"]) == ["logreg", "rf", "xgb"]
    assert set(oof["family"]) == {"logreg", "rf", "xgb"}
    assert payload["phase_b"]["seed"] == 2027 and payload["phase_a"]["seed"] == 42
    for entry in payload["families"].values():
        assert entry["phase_a"]["run_id"] and entry["phase_b"]["run_id"]


def test_main_writes_json_and_oof(training, tracking, monkeypatch, tmp_path):
    import churn.train as train_module

    monkeypatch.setattr(train_module, "load_training", lambda: training)
    monkeypatch.setattr(tune, "TUNING_FILE", tmp_path / "tuning.json")
    monkeypatch.setattr(tune, "OOF_FILE", tmp_path / "oof.parquet")
    original = tune.run_tuning
    monkeypatch.setattr(
        tune, "run_tuning", lambda data: original(data, n_iter=1, fixed_override=FAST)
    )
    assert tune.main() == 0
    assert (tmp_path / "tuning.json").exists()
    assert len(pd.read_parquet(tmp_path / "oof.parquet")) == 3 * 2 * len(training)
