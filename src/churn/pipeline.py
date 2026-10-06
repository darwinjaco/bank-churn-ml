"""Pipelines fijos de baselines (spec 002 v1.1) y defensa de columnas de auditoría."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.validation import check_is_fitted

from churn.config import AUDIT_COLUMNS, BINARY_FEATURES, FEATURE_SETS, NUMERIC_FEATURES
from churn.features import HasBalance, ProductsGroup, build_age_transformer


class InputGuard(TransformerMixin, BaseEstimator):
    """Rechaza explícitamente auditoría antes de cualquier transformación aprendida."""

    @staticmethod
    def _check(x):
        if not isinstance(x, pd.DataFrame):
            raise ValueError("El pipeline requiere un DataFrame con columnas nombradas.")
        forbidden = set(AUDIT_COLUMNS) & set(x.columns)
        if forbidden:
            raise ValueError(f"Columnas de auditoría prohibidas: {sorted(forbidden)}")

    def fit(self, x, y=None):
        self._check(x)
        self.feature_names_in_ = np.asarray(x.columns, dtype=object)
        self.n_features_in_ = len(x.columns)
        return self

    def transform(self, x):
        self._check(x)
        return x

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self, "feature_names_in_")
        return self.feature_names_in_ if input_features is None else np.asarray(input_features)


def build_pipeline(model: str, feature_set: str) -> Pipeline:
    """Construye guard, ColumnTransformer y clasificador; no ajusta ningún dato."""
    if model not in {"dummy", "logreg"} or feature_set not in FEATURE_SETS:
        raise ValueError("Se requiere model en {dummy, logreg} y feature_set en {raw, eda}.")
    numeric = NUMERIC_FEATURES.copy()
    numeric_transform = StandardScaler() if model == "logreg" else "passthrough"
    transformers = []
    if feature_set == "eda":
        numeric.remove("Age")
        transformers.extend(
            [
                ("age", build_age_transformer(), ["Age"]),
                (
                    "products",
                    Pipeline(
                        [
                            ("group", ProductsGroup()),
                            ("encode", OneHotEncoder(handle_unknown="error")),
                        ]
                    ),
                    ["NumOfProducts"],
                ),
                ("has_balance", HasBalance(), ["Balance"]),
            ]
        )
    else:
        transformers.append(("products", "passthrough", ["NumOfProducts"]))
    transformers.extend(
        [
            ("numeric", numeric_transform, numeric),
            ("binary", "passthrough", BINARY_FEATURES),
            ("geography", OneHotEncoder(handle_unknown="error"), ["Geography"]),
        ]
    )
    estimator = (
        DummyClassifier(strategy="prior")
        if model == "dummy"
        else LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", max_iter=1000)
    )
    return Pipeline(
        [
            ("guard", InputGuard()),
            ("preprocess", ColumnTransformer(transformers, remainder="drop")),
            ("model", estimator),
        ]
    )
