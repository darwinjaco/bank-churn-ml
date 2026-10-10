"""Semana 6: SHAP, errores, segmentos y E-01 sobre validación con el artefacto congelado."""

from __future__ import annotations

import json

import pandas as pd

from churn import audit, explain
from churn.artifact import load_local_model
from churn.config import PROJECT_ROOT, RAW_FILE, TARGET
from churn.decision import decide, threshold
from churn.experiments import load_validation
from churn.tracking import jsonable, log_run, provenance

MODEL_FILE = PROJECT_ROOT / "models" / "model.joblib"
METADATA_FILE = PROJECT_ROOT / "models" / "metadata.json"
DECISION_FILE = PROJECT_ROOT / "reports" / "decision.json"
AUDIT_FILE = PROJECT_ROOT / "reports" / "audit.json"
FIGURE_FILE = PROJECT_ROOT / "reports" / "figures" / "shap_importance.png"


def attach_gender(validation: pd.DataFrame, raw_file=RAW_FILE) -> pd.DataFrame:
    """Añade Gender (solo auditoría) por CustomerId; el modelo nunca recibe esta columna."""
    gender = pd.read_csv(raw_file, usecols=["CustomerId", "Gender"])
    merged = validation.merge(gender, on="CustomerId", how="left", validate="one_to_one")
    if merged["Gender"].isna().any():
        raise ValueError("Clientes de validación sin Gender.")
    return merged


def run_audit(model, validation: pd.DataFrame) -> dict:
    t = threshold()
    probability = model.predict_proba(validation)
    contact = decide(probability, t)
    y = validation[TARGET].to_numpy()
    shap_result = explain.compute_shap(model, validation)
    segments = audit.segment_columns(validation)
    metrics = audit.segment_metrics(segments, y, probability, contact)
    return {
        "threshold": t,
        "n_validation": len(validation),
        "contacted": int(contact.sum()),
        "shap": {
            "base_value": shap_result["base"],
            "additivity_max_gap": shap_result["additivity_max_gap"],
            "explains": "probabilidad sin calibrar del Random Forest base",
            **explain.global_importance(shap_result["values"], shap_result["names"]),
            "local": explain.local_explanations(shap_result, probability, t),
        },
        "errors": {
            "profiles": audit.error_profiles(validation, y, contact),
            "near_threshold": audit.near_threshold(y, probability, t),
            "worst_missed_segment": audit.worst_missed_segment(metrics),
        },
        "segments": metrics,
        "e01_gender": audit.e01_gender(y, probability, contact, validation["Gender"]),
    }


def main() -> int:
    from churn.plots import shap_importance_figure

    model = load_local_model(MODEL_FILE)
    metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    validation = attach_gender(load_validation())
    result = run_audit(model, validation)
    expected = json.loads(DECISION_FILE.read_text(encoding="utf-8"))
    if result["contacted"] != expected["decision"]["policies"]["model"]["contacted"]:
        raise RuntimeError("El artefacto no reproduce los contactados de decision.json.")
    origin = provenance()
    e01 = result["e01_gender"]
    result["run_id"] = log_run(
        "audit-e01-shap",
        "audit",
        {"model": metadata["model_family"], "artifact_commit": metadata["git_commit"]},
        None,
        None,
        origin,
        tags={"experiment": "E-01"},
        extra_metrics={
            f"e01_{metric}_diff": e01[metric]["difference"]
            for metric in ("contact_rate", "recall", "precision", "calibration_gap")
        },
    )
    payload = {"stage": "audit", **origin, "artifact_commit": metadata["git_commit"], **result}
    AUDIT_FILE.write_text(
        json.dumps(jsonable(payload), indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    shap_importance_figure(result["shap"], FIGURE_FILE)
    alerts = [
        m for m in ("contact_rate", "recall", "precision", "calibration_gap") if e01[m]["alert"]
    ]
    print(f"Contactados {result['contacted']}; alertas E-01: {alerts or 'ninguna'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
