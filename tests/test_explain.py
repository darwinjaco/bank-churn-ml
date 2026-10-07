"""SHAP: aditividad, agrupaciones R4 y explicaciones locales con un modelo pequeño."""

import numpy as np
import pytest

from churn import explain
from churn.calibration import CalibratedModel, SigmoidCalibrator, oof_predictions
from churn.config import FEATURE_SETS, TARGET
from churn.pipeline import build_pipeline


@pytest.fixture
def small_model(valid_df):
    columns = [c for c in FEATURE_SETS["tree"] if c != "EstimatedSalary"]
    pipeline = build_pipeline(
        "rf", "tree", exclude=("EstimatedSalary",), params={"n_estimators": 20, "max_depth": 4}
    )
    oof = oof_predictions(pipeline, valid_df[columns], valid_df[TARGET])
    pipeline.fit(valid_df[columns], valid_df[TARGET])
    calibrator = SigmoidCalibrator().fit(oof, valid_df[TARGET])
    return CalibratedModel(pipeline, calibrator, columns)


def test_display_names_and_groups():
    names = [
        "numeric__Balance",
        "has_balance__has_balance",
        "geography__Geography_France",
        "geography__Geography_Germany",
        "numeric__Age",
    ]
    assert explain.display_name(names[3]) == "Geography=Germany"
    assert explain.display_name(names[4]) == "Age"
    groups = explain.feature_groups(names)
    assert groups["Geography"] == names[2:4]
    assert groups["saldo (Balance + has_balance)"] == names[:2]
    assert groups["saldo y geografía (R4)"] == names[:4]


def test_shap_is_additive_and_importance_is_sorted(small_model, valid_df):
    result = explain.compute_shap(small_model, valid_df)
    assert result["values"].shape == (len(valid_df), len(result["names"]))
    assert result["additivity_max_gap"] <= explain.ADDITIVITY_TOLERANCE
    importance = explain.global_importance(result["values"], result["names"])
    scores = [row["mean_abs_shap"] for row in importance["per_feature"]]
    assert scores == sorted(scores, reverse=True)
    groups = importance["groups"]
    assert groups["saldo y geografía (R4)"] <= (
        groups["Geography"] + groups["saldo (Balance + has_balance)"] + 1e-12
    )
    assert all("Gender" not in row["feature"] for row in importance["per_feature"])


def test_local_explanations_pick_expected_customers(small_model, valid_df):
    result = explain.compute_shap(small_model, valid_df)
    calibrated = small_model.predict_proba(valid_df)
    cases = explain.local_explanations(result, calibrated, valid_df["CustomerId"], 1 / 6)
    by_case = {case["case"]: case for case in cases}
    assert by_case["mayor_probabilidad"]["p_calibrated"] == pytest.approx(calibrated.max())
    assert by_case["menor_probabilidad"]["p_calibrated"] == pytest.approx(calibrated.min())
    near = by_case["cerca_del_umbral"]["p_calibrated"]
    assert near > 1 / 6 and near == pytest.approx(calibrated[calibrated > 1 / 6].min())
    for case in cases:
        assert len(case["top_contributions"]) == explain.N_LOCAL_TOP
        magnitudes = [abs(c["shap"]) for c in case["top_contributions"]]
        assert magnitudes == sorted(magnitudes, reverse=True)


def test_local_explanations_without_customers_above_threshold(small_model, valid_df):
    result = explain.compute_shap(small_model, valid_df)
    calibrated = np.zeros(len(valid_df))
    cases = explain.local_explanations(result, calibrated, valid_df["CustomerId"], 0.5)
    assert {case["case"] for case in cases} == {"mayor_probabilidad", "menor_probabilidad"}
