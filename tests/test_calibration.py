"""Calibración E-04 con datos sintéticos de calibración conocida."""

import numpy as np
import pandas as pd
import pytest

from churn import calibration
from churn.config import FEATURE_SETS, TARGET
from churn.pipeline import build_pipeline


@pytest.fixture
def miscalibrated():
    rng = np.random.default_rng(0)
    true = rng.uniform(0.02, 0.9, 4000)
    y = (rng.random(4000) < true).astype(int)
    score = true**2  # Subestima el riesgo: ordena bien, pero mal calibrada.
    return score, y, true


def test_sigmoid_and_isotonic_improve_brier_and_stay_in_range(miscalibrated):
    score, y, _ = miscalibrated
    fit, holdout = slice(0, 2000), slice(2000, None)
    calibrators = calibration.fit_calibrators(score[fit], y[fit])
    raw = calibration.variant_metrics(score[holdout], y[holdout])["brier"]
    for name in ("sigmoid", "isotonic"):
        values = calibrators[name].transform(score[holdout])
        assert ((values >= 0) & (values <= 1)).all()
        assert calibration.variant_metrics(values, y[holdout])["brier"] < raw
    np.testing.assert_array_equal(calibrators["none"].transform(score), score)
    sigmoid = calibrators["sigmoid"].transform(np.sort(score))
    assert (np.diff(sigmoid) >= 0).all()
    assert calibrators["isotonic"].transform(np.array([-1.0, 2.0])).tolist() == pytest.approx(
        calibrators["isotonic"].transform(np.array([score.min(), score.max()])).tolist()
    )


def test_choose_calibrator_rules():
    assert calibration.choose_calibrator({"none": 0.12, "sigmoid": 0.10, "isotonic": 0.11}) == (
        "sigmoid"
    )
    assert calibration.choose_calibrator({"none": 0.10005, "sigmoid": 0.1, "isotonic": 0.2}) == (
        "none"
    )
    assert calibration.choose_calibrator({"none": 0.2, "sigmoid": 0.10009, "isotonic": 0.1}) == (
        "sigmoid"
    )
    assert calibration.choose_calibrator({"none": 0.2, "sigmoid": 0.1002, "isotonic": 0.1}) == (
        "isotonic"
    )


def test_reliability_and_group_calibration(miscalibrated):
    score, y, _ = miscalibrated
    table = calibration.reliability_table(score, y)
    assert len(table) == 10 and sum(row["n"] for row in table) == len(score)
    assert all(row["predicted"] <= row["observed"] + 0.05 for row in table)
    group = calibration.group_calibration(score, y, score > 0.5)
    assert group["n"] == int((score > 0.5).sum())
    assert group["observed_rate"] == pytest.approx(y[score > 0.5].mean())


def test_oof_predictions_cover_every_row_once_and_are_deterministic(valid_df):
    x = valid_df[FEATURE_SETS["tree"]]
    pipeline = build_pipeline("rf", "tree", params={"n_estimators": 10})
    first = calibration.oof_predictions(pipeline, x, valid_df[TARGET])
    second = calibration.oof_predictions(pipeline, x, valid_df[TARGET])
    assert first.shape == (len(x),) and not np.isnan(first).any()
    np.testing.assert_array_equal(first, second)


def test_calibrated_model_selects_columns_and_clips(valid_df):
    columns = [c for c in FEATURE_SETS["tree"] if c != "EstimatedSalary"]
    pipeline = build_pipeline(
        "rf", "tree", exclude=("EstimatedSalary",), params={"n_estimators": 10}
    )
    pipeline.fit(valid_df[columns], valid_df[TARGET])
    oof = calibration.oof_predictions(pipeline, valid_df[columns], valid_df[TARGET])
    calibrator = calibration.fit_calibrators(oof, valid_df[TARGET])["sigmoid"]
    model = calibration.CalibratedModel(pipeline, calibrator, columns)
    probability = model.predict_proba(pd.DataFrame(valid_df))
    assert probability.shape == (len(valid_df),)
    assert ((probability >= 0) & (probability <= 1)).all()
