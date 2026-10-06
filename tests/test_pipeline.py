"""Defensa explícita de auditoría, contrato categórico y pipelines ajustables."""

import numpy as np
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from churn.config import AUDIT_COLUMNS, FEATURE_SETS, ID_COLUMNS, TARGET
from churn.pipeline import InputGuard, build_pipeline


@pytest.mark.parametrize("model", ["dummy", "logreg"])
@pytest.mark.parametrize("feature_set", ["raw", "eda"])
def test_pipeline_probabilities_and_names(valid_df, model, feature_set):
    x = valid_df[FEATURE_SETS[feature_set]]
    pipeline = build_pipeline(model, feature_set).fit(x, valid_df[TARGET])
    assert isinstance(pipeline, Pipeline)
    assert isinstance(pipeline.named_steps["preprocess"], ColumnTransformer)
    probabilities = pipeline.predict_proba(x)
    assert probabilities.shape == (len(x), 2)
    assert np.isfinite(probabilities).all()
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
    np.testing.assert_allclose(probabilities.sum(axis=1), 1)
    names = pipeline[:-1].get_feature_names_out()
    assert all(not any(column in name for column in AUDIT_COLUMNS + ID_COLUMNS) for name in names)
    if model == "logreg":
        params = pipeline.named_steps["model"].get_params()
        assert params["penalty"] == "l2" and params["C"] == 1
        assert params["solver"] == "lbfgs" and params["max_iter"] == 1000
        assert params["class_weight"] is None
    if feature_set == "eda":
        assert any("Age^2" in name for name in names)
        assert any("has_balance" in name for name in names)


def test_audit_column_rejected_during_fit_and_prediction(valid_df):
    pipeline = build_pipeline("logreg", "eda")
    with pytest.raises(ValueError, match=AUDIT_COLUMNS[0]):
        pipeline.fit(valid_df, valid_df[TARGET])
    pipeline.fit(valid_df[FEATURE_SETS["eda"]], valid_df[TARGET])
    with pytest.raises(ValueError, match=AUDIT_COLUMNS[0]):
        pipeline.predict_proba(valid_df)


def test_unknown_geography_rejected(valid_df):
    x = valid_df[FEATURE_SETS["raw"]].copy()
    pipeline = build_pipeline("logreg", "raw").fit(x, valid_df[TARGET])
    x.loc[0, "Geography"] = "Italy"
    with pytest.raises(ValueError, match="unknown categories"):
        pipeline.predict_proba(x)


def test_invalid_configuration_or_unnamed_input():
    with pytest.raises(ValueError):
        build_pipeline("xgboost", "raw")
    with pytest.raises(ValueError):
        build_pipeline("logreg", "unknown")
    with pytest.raises(ValueError, match="DataFrame"):
        InputGuard().fit(np.ones((4, 2)))
