"""Pipelines de la spec 002 v1.3 y defensa explícita de columnas de auditoría."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.validation import check_is_fitted
from xgboost import XGBClassifier

from churn.config import (
    ABLATION_COLUMNS,
    AUDIT_COLUMNS,
    BINARY_FEATURES,
    FEATURE_SETS,
    NUMERIC_FEATURES,
    RANDOM_SEED,
)
from churn.features import HasBalance, ProductsGroup, build_age_transformer

# Combinaciones permitidas: modelos lineales con FS-RAW/FS-EDA, árboles con FS-TREE (§3).
VALID_COMBINATIONS = {
    "dummy": {"raw", "eda"},
    "logreg": {"raw", "eda"},
    "rf": {"tree"},
    "xgb": {"tree"},
}


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


def input_columns(feature_set: str, exclude: tuple[str, ...] = ()) -> list[str]:
    """Columnas de entrada del conjunto, sin las excluidas por una ablación."""
    return [column for column in FEATURE_SETS[feature_set] if column not in exclude]


def _estimator(model: str):
    if model == "dummy":
        return DummyClassifier(strategy="prior")
    if model == "logreg":
        return LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", max_iter=1000)
    if model == "rf":
        # R3: sin class_weight.
        return RandomForestClassifier(
            n_estimators=500, class_weight=None, random_state=RANDOM_SEED, n_jobs=-1
        )
    # R3: scale_pos_weight=1; sin early stopping.
    return XGBClassifier(
        tree_method="hist",
        scale_pos_weight=1,
        eval_metric="logloss",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )


def _linear_transformers(model: str, feature_set: str, exclude: tuple[str, ...]) -> list:
    numeric = [column for column in NUMERIC_FEATURES if column not in exclude]
    numeric_transform = StandardScaler() if model == "logreg" else "passthrough"
    transformers = []
    if feature_set == "eda":
        numeric.remove("Age")
        transformers.append(("age", build_age_transformer(), ["Age"]))
        if "NumOfProducts" not in exclude:
            transformers.append(
                (
                    "products",
                    Pipeline(
                        [
                            ("group", ProductsGroup()),
                            ("encode", OneHotEncoder(handle_unknown="error")),
                        ]
                    ),
                    ["NumOfProducts"],
                )
            )
        transformers.append(("has_balance", HasBalance(), ["Balance"]))
    elif "NumOfProducts" not in exclude:
        transformers.append(("products", "passthrough", ["NumOfProducts"]))
    transformers.append(("numeric", numeric_transform, numeric))
    return transformers


def _tree_transformers(exclude: tuple[str, ...]) -> list:
    # FS-TREE: valores originales sin escalar; NumOfProducts entero sin agrupar.
    numeric = [column for column in NUMERIC_FEATURES if column not in exclude]
    transformers = [("numeric", "passthrough", numeric)]
    if "NumOfProducts" not in exclude:
        transformers.append(("products", "passthrough", ["NumOfProducts"]))
    transformers.append(("has_balance", HasBalance(), ["Balance"]))
    return transformers


def build_pipeline(
    model: str,
    feature_set: str,
    exclude: tuple[str, ...] = (),
    params: dict | None = None,
) -> Pipeline:
    """Construye guard, ColumnTransformer y clasificador; no ajusta ningún dato.

    ``exclude`` solo admite columnas de ablación preregistradas (E-02, E-03).
    ``params`` fija hiperparámetros del clasificador (sin prefijo).
    """
    if feature_set not in VALID_COMBINATIONS.get(model, set()):
        raise ValueError(
            "Combinación no permitida. Válidas: dummy|logreg con raw|eda; rf|xgb con tree."
        )
    exclude = tuple(exclude)
    invalid = set(exclude) - set(ABLATION_COLUMNS)
    if invalid:
        raise ValueError(f"Solo se pueden excluir {ABLATION_COLUMNS}; recibido: {sorted(invalid)}")
    if model in {"rf", "xgb"}:
        transformers = _tree_transformers(exclude)
    else:
        transformers = _linear_transformers(model, feature_set, exclude)
    transformers.extend(
        [
            ("binary", "passthrough", BINARY_FEATURES),
            ("geography", OneHotEncoder(handle_unknown="error"), ["Geography"]),
        ]
    )
    estimator = _estimator(model)
    if params:
        estimator.set_params(**params)
    return Pipeline(
        [
            ("guard", InputGuard()),
            ("preprocess", ColumnTransformer(transformers, remainder="drop")),
            ("model", estimator),
        ]
    )
