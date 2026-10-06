"""Calibración E-04 (spec 002 v1.5 §5.3.1): OOF, sigmoide, isotónica y elección por Brier."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss
from sklearn.model_selection import StratifiedKFold

from churn.config import RANDOM_SEED

N_FOLDS = 5
BRIER_TIE = 1e-4
PREFERENCE = ("none", "sigmoid", "isotonic")  # Ante empate: sin calibrar > sigmoide > isotónica.


class IdentityCalibrator:
    """Variante sin calibración adicional."""

    name = "none"

    def fit(self, probability, y):
        return self

    def transform(self, probability) -> np.ndarray:
        return np.asarray(probability, dtype=float)


class SigmoidCalibrator:
    """Platt: regresión logística sin penalización sobre la probabilidad OOF."""

    name = "sigmoid"

    def fit(self, probability, y):
        self.model_ = LogisticRegression(C=np.inf, max_iter=1000)
        self.model_.fit(np.asarray(probability, dtype=float).reshape(-1, 1), np.asarray(y))
        return self

    def transform(self, probability) -> np.ndarray:
        values = np.asarray(probability, dtype=float).reshape(-1, 1)
        return self.model_.predict_proba(values)[:, 1]


class IsotonicCalibrator:
    """Regresión isotónica creciente, acotada a [0, 1] y recortada fuera de rango."""

    name = "isotonic"

    def fit(self, probability, y):
        self.model_ = IsotonicRegression(
            y_min=0.0, y_max=1.0, increasing=True, out_of_bounds="clip"
        )
        self.model_.fit(np.asarray(probability, dtype=float), np.asarray(y, dtype=float))
        return self

    def transform(self, probability) -> np.ndarray:
        return self.model_.predict(np.asarray(probability, dtype=float))


CALIBRATORS = {
    "none": IdentityCalibrator,
    "sigmoid": SigmoidCalibrator,
    "isotonic": IsotonicCalibrator,
}


class CalibratedModel:
    """Pipeline ajustado + calibrador elegido; devuelve la probabilidad calibrada de abandono."""

    def __init__(self, pipeline, calibrator, columns: list[str]):
        self.pipeline = pipeline
        self.calibrator = calibrator
        self.columns = list(columns)

    def predict_proba(self, x: pd.DataFrame) -> np.ndarray:
        raw = self.pipeline.predict_proba(x[self.columns])[:, 1]
        return np.clip(self.calibrator.transform(raw), 0.0, 1.0)


def oof_predictions(pipeline, x: pd.DataFrame, y: pd.Series) -> np.ndarray:
    """Predicción fuera de muestra: cada fila la predice un pipeline que no la vio."""
    labels = pd.Series(y).reset_index(drop=True)
    features = x.reset_index(drop=True)
    oof = np.full(len(features), np.nan)
    splitter = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    for fitting, scoring in splitter.split(features, labels):
        fitted = clone(pipeline).fit(features.iloc[fitting], labels.iloc[fitting])
        oof[scoring] = fitted.predict_proba(features.iloc[scoring])[:, 1]
    if np.isnan(oof).any():
        raise RuntimeError("Hay filas sin predicción OOF.")
    return oof


def fit_calibrators(oof: np.ndarray, y) -> dict:
    """Ajusta las tres variantes con OOF y etiquetas de entrenamiento únicamente."""
    return {name: factory().fit(oof, y) for name, factory in CALIBRATORS.items()}


def variant_metrics(probability, y) -> dict:
    probability = np.clip(np.asarray(probability, dtype=float), 0.0, 1.0)
    return {
        "brier": float(brier_score_loss(y, probability)),
        "log_loss": float(log_loss(y, probability, labels=[0, 1])),
        "ap": float(average_precision_score(y, probability)),
    }


def choose_calibrator(brier: dict[str, float]) -> str:
    """Menor Brier; diferencias < 1e-4 son empate y se resuelven por PREFERENCE."""
    best = min(brier.values())
    tied = [name for name in PREFERENCE if name in brier and brier[name] - best < BRIER_TIE]
    return tied[0]


def reliability_table(probability, y, n_bins: int = 10) -> list[dict]:
    """Intervalos por cuantiles: probabilidad media predicha frente a tasa observada."""
    frame = pd.DataFrame({"p": np.asarray(probability, dtype=float), "y": np.asarray(y)})
    frame["bin"] = pd.qcut(frame["p"].rank(method="first"), q=n_bins, labels=False)
    grouped = frame.groupby("bin", sort=True).agg(
        predicted=("p", "mean"), observed=("y", "mean"), n=("y", "size")
    )
    return [
        {
            "bin": int(index) + 1,
            **{k: float(v) for k, v in row.items() if k != "n"},
            "n": int(row["n"]),
        }
        for index, row in grouped.iterrows()
    ]


def group_calibration(probability, y, mask) -> dict:
    """Probabilidad media predicha frente a tasa observada en un segmento."""
    mask = np.asarray(mask, dtype=bool)
    return {
        "n": int(mask.sum()),
        "observed_rate": float(np.asarray(y)[mask].mean()),
        "mean_predicted": float(np.asarray(probability, dtype=float)[mask].mean()),
    }
