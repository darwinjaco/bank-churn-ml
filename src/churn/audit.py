"""Errores en t*, segmentos y auditoría E-01 por género (spec 002 v1.6 §11.2-11.4)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from churn.config import RANDOM_SEED, age_band
from churn.decision import realized_benefit

NEAR_THRESHOLD_BAND = 0.05
N_BOOTSTRAP = 2_000
ALERT_MIN_ABS_DIFF = 0.05
PROFILE_COLUMNS = (
    "CreditScore",
    "Age",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "HasCrCard",
    "IsActiveMember",
)


def segment_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Segmentos de §11.3 (Gender solo como auditoría)."""
    return pd.DataFrame(
        {
            "Geography": frame["Geography"].astype(str).to_numpy(),
            "tramo_edad": age_band(frame["Age"]).astype(str).to_numpy(),
            "productos": np.where(
                frame["NumOfProducts"] >= 3, "3-4", frame["NumOfProducts"].astype(str)
            ),
            "IsActiveMember": frame["IsActiveMember"].astype(str).to_numpy(),
            "has_balance": (frame["Balance"] > 0).astype(int).astype(str).to_numpy(),
            "Gender": frame["Gender"].astype(str).to_numpy(),
        }
    )


def rates(y, p, contact) -> dict:
    """Métricas de un grupo; None cuando el denominador es cero."""
    y, p, contact = np.asarray(y), np.asarray(p, dtype=float), np.asarray(contact, dtype=bool)
    positives, contacted = int(y.sum()), int(contact.sum())
    true_positive = int((contact & (y == 1)).sum())
    observed = float(y.mean())
    predicted = float(p.mean())
    return {
        "n": len(y),
        "churners": positives,
        "observed_rate": observed,
        "mean_predicted": predicted,
        "calibration_gap": predicted - observed,
        "contact_rate": float(contact.mean()),
        "recall": true_positive / positives if positives else None,
        "precision": true_positive / contacted if contacted else None,
        "missed_churn_share": (positives - true_positive) / positives if positives else None,
    }


def segment_metrics(segments: pd.DataFrame, y, p, contact) -> dict:
    y, p, contact = np.asarray(y), np.asarray(p, dtype=float), np.asarray(contact, dtype=bool)
    out = {}
    for column in segments.columns:
        out[column] = {}
        for level in sorted(segments[column].unique()):
            mask = (segments[column] == level).to_numpy()
            metrics = rates(y[mask], p[mask], contact[mask])
            benefit = realized_benefit(contact[mask], y[mask])
            out[column][level] = {
                **metrics,
                "benefit_eur": benefit,
                "benefit_per_customer_eur": benefit / metrics["n"],
            }
    return out


def worst_missed_segment(metrics: dict) -> dict:
    """Segmento con mayor proporción de abandonos no contactados (FN / abandonos), §11.2."""
    candidates = [
        (values["missed_churn_share"], column, level, values["churners"])
        for column, levels in metrics.items()
        for level, values in levels.items()
        if values["missed_churn_share"] is not None
    ]
    share, column, level, churners = max(candidates)
    return {"segment": column, "level": level, "missed_churn_share": share, "churners": churners}


def error_profiles(frame: pd.DataFrame, y, contact) -> dict:
    """Perfil medio de variables del modelo para VP, FP, FN y VN en t*."""
    y, contact = np.asarray(y), np.asarray(contact, dtype=bool)
    groups = {
        "VP": contact & (y == 1),
        "FP": contact & (y == 0),
        "FN": ~contact & (y == 1),
        "VN": ~contact & (y == 0),
    }
    out = {}
    for name, mask in groups.items():
        part = frame.loc[mask]
        if part.empty:
            out[name] = {"n": 0, "means": None}
            continue
        profile = {column: float(part[column].mean()) for column in PROFILE_COLUMNS}
        profile["Germany_share"] = float((part["Geography"] == "Germany").mean())
        profile["zero_balance_share"] = float((part["Balance"] == 0).mean())
        out[name] = {"n": int(mask.sum()), "means": profile}
    return out


def near_threshold(y, p, threshold: float, band: float = NEAR_THRESHOLD_BAND) -> dict:
    p, y = np.asarray(p, dtype=float), np.asarray(y)
    mask = np.abs(p - threshold) < band
    return {
        "band": band,
        "n": int(mask.sum()),
        "observed_rate": float(y[mask].mean()) if mask.any() else None,
        "contacted": int((p[mask] > threshold).sum()),
    }


def alert(diff: float, low: float, high: float) -> bool:
    """Señal preregistrada: el IC excluye 0 y |diferencia| >= 0,05."""
    return (low > 0 or high < 0) and abs(diff) >= ALERT_MIN_ABS_DIFF


def e01_gender(y, p, contact, gender, n_boot: int = N_BOOTSTRAP, seed: int = RANDOM_SEED) -> dict:
    """Diferencias Female - Male con IC 95 % por bootstrap estratificado por género."""
    y, p = np.asarray(y), np.asarray(p, dtype=float)
    contact, gender = np.asarray(contact, dtype=bool), np.asarray(gender).astype(str)
    index = {g: np.flatnonzero(gender == g) for g in ("Female", "Male")}
    metrics = ("contact_rate", "recall", "precision", "calibration_gap")

    def compute(female_rows, male_rows):
        f = rates(y[female_rows], p[female_rows], contact[female_rows])
        m = rates(y[male_rows], p[male_rows], contact[male_rows])
        return f, m

    female, male = compute(index["Female"], index["Male"])
    rng = np.random.default_rng(seed)
    samples = {metric: [] for metric in metrics}
    for _ in range(n_boot):
        f_rows = rng.choice(index["Female"], size=index["Female"].size, replace=True)
        m_rows = rng.choice(index["Male"], size=index["Male"].size, replace=True)
        f, m = compute(f_rows, m_rows)
        for metric in metrics:
            if f[metric] is not None and m[metric] is not None:
                samples[metric].append(f[metric] - m[metric])
    out = {"n": {"Female": int(index["Female"].size), "Male": int(index["Male"].size)}}
    for metric in metrics:
        diff = female[metric] - male[metric]
        low, high = np.percentile(samples[metric], [2.5, 97.5])
        out[metric] = {
            "Female": female[metric],
            "Male": male[metric],
            "difference": float(diff),
            "ci_low": float(low),
            "ci_high": float(high),
            "alert": bool(alert(diff, low, high)),
        }
    out["observed_rate"] = {"Female": female["observed_rate"], "Male": male["observed_rate"]}
    return out
