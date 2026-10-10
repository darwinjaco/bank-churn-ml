"""Explicabilidad SHAP del modelo congelado (spec 002 v1.6 §11.1)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap

ADDITIVITY_TOLERANCE = 1e-6
N_LOCAL_TOP = 5


def display_name(name: str) -> str:
    """'numeric__Age' -> 'Age'; 'geography__Geography_Germany' -> 'Geography=Germany'."""
    base = name.split("__", 1)[-1]
    if base.startswith("Geography_"):
        return "Geography=" + base.removeprefix("Geography_")
    return base


def feature_groups(names: list[str]) -> dict[str, list[str]]:
    """Agrupaciones de §11.1: Geography, saldo y, por R4, saldo y geografía juntos."""
    geography = [n for n in names if display_name(n).startswith("Geography=")]
    balance = [n for n in names if display_name(n) in {"Balance", "has_balance"}]
    return {
        "Geography": geography,
        "saldo (Balance + has_balance)": balance,
        "saldo y geografía (R4)": balance + geography,
    }


def tree_explainer(model) -> shap.TreeExplainer:
    """Explicador del estimador base; se puede crear una vez y reutilizar (spec 005 §6)."""
    return shap.TreeExplainer(model.pipeline.named_steps["model"])


def compute_shap(model, x: pd.DataFrame, explainer: shap.TreeExplainer | None = None) -> dict:
    """SHAP de la clase 1 sobre la probabilidad sin calibrar, con comprobación de aditividad."""
    preprocess = model.pipeline[:-1]
    estimator = model.pipeline.named_steps["model"]
    matrix = preprocess.transform(x[model.columns])
    names = [str(n) for n in preprocess.get_feature_names_out()]
    explainer = explainer or tree_explainer(model)
    values = np.asarray(explainer.shap_values(matrix))
    if values.ndim == 3:  # (n, variables, clases)
        values = values[:, :, 1]
    base = float(np.ravel(explainer.expected_value)[-1])
    raw = estimator.predict_proba(matrix)[:, 1]
    gap = float(np.max(np.abs(base + values.sum(axis=1) - raw)))
    if gap > ADDITIVITY_TOLERANCE:
        raise ValueError(f"SHAP no es aditivo: diferencia máxima {gap:.2e}")
    return {
        "values": values,
        "base": base,
        "names": names,
        "matrix": np.asarray(matrix, dtype=float),
        "raw": raw,
        "additivity_max_gap": gap,
    }


def global_importance(values: np.ndarray, names: list[str]) -> dict:
    """Media de |SHAP| por variable y por grupo (suma de SHAP por fila dentro del grupo)."""
    per_feature = sorted(
        (
            {"feature": display_name(name), "mean_abs_shap": float(np.mean(np.abs(values[:, i])))}
            for i, name in enumerate(names)
        ),
        key=lambda row: row["mean_abs_shap"],
        reverse=True,
    )
    groups = {}
    for group, members in feature_groups(names).items():
        index = [names.index(member) for member in members]
        groups[group] = float(np.mean(np.abs(values[:, index].sum(axis=1))))
    return {"per_feature": per_feature, "groups": groups}


def local_explanations(shap_result: dict, calibrated: np.ndarray, threshold: float) -> list[dict]:
    """Tres clientes: mayor p, el más cercano a t* por encima y menor p (§11.1)."""
    calibrated = np.asarray(calibrated, dtype=float)
    above = np.flatnonzero(calibrated > threshold)
    cases = {
        "mayor_probabilidad": int(np.argmax(calibrated)),
        "cerca_del_umbral": int(above[np.argmin(calibrated[above])]) if above.size else None,
        "menor_probabilidad": int(np.argmin(calibrated)),
    }
    names, values, matrix = shap_result["names"], shap_result["values"], shap_result["matrix"]
    out = []
    for case, row in cases.items():
        if row is None:
            continue
        order = np.argsort(-np.abs(values[row]))[:N_LOCAL_TOP]
        out.append(
            {
                "case": case,
                "p_calibrated": float(calibrated[row]),
                "p_raw": float(shap_result["raw"][row]),
                "base_value": shap_result["base"],
                "top_contributions": [
                    {
                        "feature": display_name(names[j]),
                        "value": float(matrix[row, j]),
                        "shap": float(values[row, j]),
                    }
                    for j in order
                ],
            }
        )
    return out
