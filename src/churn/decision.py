"""Capa de decisión por beneficio esperado, opción A (spec 004)."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

from churn.config import (
    CONTACT_COST_EUR,
    CUSTOMER_VALUE_EUR,
    RANDOM_POLICY_SHARE,
    RETENTION_SUCCESS_RATE,
)


def assumptions() -> dict:
    return {
        "customer_value_eur": CUSTOMER_VALUE_EUR,
        "contact_cost_eur": CONTACT_COST_EUR,
        "retention_success_rate": RETENTION_SUCCESS_RATE,
    }


def threshold(
    value: float = CUSTOMER_VALUE_EUR,
    cost: float = CONTACT_COST_EUR,
    success: float = RETENTION_SUCCESS_RATE,
) -> float:
    """t* = c / (s · V): contactar si p > t* (spec 004 §3)."""
    if value <= 0 or cost < 0 or not 0 < success <= 1:
        raise ValueError("Supuestos fuera de rango.")
    return cost / (success * value)


def expected_benefit(
    probability, value=CUSTOMER_VALUE_EUR, cost=CONTACT_COST_EUR, success=RETENTION_SUCCESS_RATE
) -> np.ndarray:
    """EB_i = p_i · s · V - c."""
    return np.asarray(probability, dtype=float) * success * value - cost


def decide(probability, t: float | None = None) -> np.ndarray:
    """Contactar si y solo si p > t* (desigualdad estricta, EB > 0)."""
    t = threshold() if t is None else t
    return np.asarray(probability, dtype=float) > t


def realized_benefit(
    contact, y, value=CUSTOMER_VALUE_EUR, cost=CONTACT_COST_EUR, success=RETENTION_SUCCESS_RATE
) -> float:
    """B(C) = Σ_{i ∈ C} (y_i · s · V - c), con etiquetas reales (spec 004 §6)."""
    contact = np.asarray(contact, dtype=bool)
    y = np.asarray(y)
    return float(np.sum(y[contact] * success * value - cost))


def policy_report(contact, y) -> dict:
    contact = np.asarray(contact, dtype=bool)
    y = np.asarray(y)
    n_contacted = int(contact.sum())
    benefit = realized_benefit(contact, y)
    return {
        "contacted": n_contacted,
        "contacted_share": float(contact.mean()),
        "churners_captured": int((contact & (y == 1)).sum()),
        "benefit_eur": benefit,
        "benefit_per_contact_eur": benefit / n_contacted if n_contacted else 0.0,
    }


def evaluate_policies(probability, y) -> dict:
    """Nadie, todos, aleatoria 20 % (valor esperado), modelo en t* y oráculo."""
    y = np.asarray(y)
    t = threshold()
    model_contact = decide(probability, t)
    everyone = policy_report(np.ones_like(y, dtype=bool), y)
    random_policy = {
        "contacted": RANDOM_POLICY_SHARE * len(y),
        "contacted_share": RANDOM_POLICY_SHARE,
        "churners_captured": RANDOM_POLICY_SHARE * int(y.sum()),
        "benefit_eur": RANDOM_POLICY_SHARE * everyone["benefit_eur"],
        "benefit_per_contact_eur": everyone["benefit_per_contact_eur"],
    }
    policies = {
        "nobody": policy_report(np.zeros_like(y, dtype=bool), y),
        "everyone": everyone,
        "random_20": random_policy,
        "model": policy_report(model_contact, y),
        "oracle": policy_report(y == 1, y),
    }
    best_reference = max(
        ("nobody", "everyone", "random_20"), key=lambda name: policies[name]["benefit_eur"]
    )
    model = policies["model"]
    tn, fp, fn, tp = confusion_matrix(y, model_contact, labels=[0, 1]).ravel()
    return {
        "threshold": t,
        "assumptions": assumptions(),
        "n": len(y),
        "churners": int(y.sum()),
        "policies": policies,
        "best_reference": best_reference,
        "model_minus_best_reference_eur": model["benefit_eur"]
        - policies[best_reference]["benefit_eur"],
        "oracle_share_captured": model["benefit_eur"] / policies["oracle"]["benefit_eur"],
        "classification_at_threshold": {
            "precision": float(precision_score(y, model_contact, zero_division=0)),
            "recall": float(recall_score(y, model_contact, zero_division=0)),
            "f1": float(f1_score(y, model_contact, zero_division=0)),
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        },
    }
