"""Transformaciones de modelado de la spec 002 v1.1, sin estadísticas externas."""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from churn.config import BALANCE_POSITIVE_THRESHOLD, PRODUCTS_GROUP_MAX


def _single_column(x) -> np.ndarray:
    values = np.asarray(x, dtype=float)
    if values.ndim == 1:
        values = values.reshape(-1, 1)
    if values.ndim != 2 or values.shape[1] != 1:
        raise ValueError("El transformador requiere una única columna.")
    return values


class HasBalance(TransformerMixin, BaseEstimator):
    """Indicador de saldo positivo, determinista y sin estado aprendido."""

    def fit(self, x, y=None):
        return self

    def transform(self, x) -> np.ndarray:
        return (_single_column(x) > BALANCE_POSITIVE_THRESHOLD).astype(int)

    def get_feature_names_out(self, input_features=None) -> np.ndarray:
        return np.asarray(["has_balance"], dtype=object)


class ProductsGroup(TransformerMixin, BaseEstimator):
    """Clip sin estado; 3 representa los grupos originales de 3 y 4 productos."""

    def fit(self, x, y=None):
        return self

    def transform(self, x) -> np.ndarray:
        return np.minimum(_single_column(x), PRODUCTS_GROUP_MAX)

    def get_feature_names_out(self, input_features=None) -> np.ndarray:
        return np.asarray(["NumOfProducts"], dtype=object)


def build_age_transformer() -> Pipeline:
    """Media y escala aprendidas al ajustar; dos términos de edad sin intercepto."""
    return Pipeline(
        [
            ("scale", StandardScaler()),
            ("quadratic", PolynomialFeatures(degree=2, include_bias=False)),
        ]
    )
