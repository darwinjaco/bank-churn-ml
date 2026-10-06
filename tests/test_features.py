"""Contratos sin estado y aprendizaje de medias solo en el conjunto de ajuste."""

from copy import deepcopy

import numpy as np
import pandas as pd
import pytest
from sklearn.base import BaseEstimator, TransformerMixin

from churn import config
from churn.features import HasBalance, ProductsGroup, build_age_transformer


def test_feature_sets_exclude_audit_identifiers_and_target():
    forbidden = set(config.AUDIT_COLUMNS + config.ID_COLUMNS + [config.TARGET])
    assert set(config.FEATURE_SETS) == {"raw", "eda"}
    for columns in config.FEATURE_SETS.values():
        assert not forbidden & set(columns)
        assert set(columns) == set(config.MODEL_FEATURES)


@pytest.mark.parametrize(
    ("transformer", "values", "expected", "name"),
    [
        (HasBalance(), [0, 100, 0, 0.1], [0, 1, 0, 1], "has_balance"),
        (ProductsGroup(), [1, 2, 3, 4], [1, 2, 3, 3], "NumOfProducts"),
    ],
)
def test_transformers_are_stateless_deterministic_and_named(transformer, values, expected, name):
    assert isinstance(transformer, (BaseEstimator, TransformerMixin))
    before = deepcopy(transformer.__dict__)
    assert transformer.fit(np.asarray(values)) is transformer
    assert transformer.__dict__ == before
    first = transformer.transform(values)
    np.testing.assert_array_equal(first[:, 0], expected)
    np.testing.assert_array_equal(first, transformer.transform(pd.DataFrame({name: values})))
    assert transformer.get_feature_names_out().tolist() == [name]
    assert transformer.__dict__ == before


@pytest.mark.parametrize("transformer", [HasBalance(), ProductsGroup()])
def test_transformers_reject_multiple_columns(transformer):
    with pytest.raises(ValueError, match="única columna"):
        transformer.transform([[1, 2], [3, 4]])


def test_age_scaler_uses_fitting_mean_not_transformation_mean(monkeypatch):
    def forbidden_centering(age):
        raise AssertionError("La función inferencial no puede usarse para modelar.")

    monkeypatch.setattr(config, "centered_age", forbidden_centering)
    fitting = pd.DataFrame({"Age": [20, 40]})
    held_out = pd.DataFrame({"Age": [70, 80]})
    transformer = build_age_transformer().fit(fitting)
    np.testing.assert_array_equal(transformer.named_steps["scale"].mean_, [30])
    np.testing.assert_allclose(transformer.transform(held_out), [[4, 16], [5, 25]])
    np.testing.assert_array_equal(transformer.named_steps["scale"].mean_, [30])
    assert transformer.get_feature_names_out().tolist() == ["Age", "Age^2"]
