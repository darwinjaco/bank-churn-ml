"""Reporte legible de la semana 5, generado solo desde reports/decision.json."""

from __future__ import annotations

import json

from churn.config import PROJECT_ROOT

DECISION_JSON = PROJECT_ROOT / "reports" / "decision.json"
DECISION_MD = PROJECT_ROOT / "reports" / "decision.md"
VARIANTS = {"none": "Sin calibrar", "sigmoid": "Sigmoide", "isotonic": "Isotónica"}
POLICIES = {
    "nobody": "Nadie",
    "everyone": "Todos",
    "random_20": "Aleatoria 20 % (valor esperado)",
    "model": "**Modelo (p calibrada > t\\*)**",
    "oracle": "Oráculo (cota superior)",
}


def _int(value: float) -> str:
    """Entero con separador de miles español (punto)."""
    return f"{value:,.0f}".replace(",", ".")


def _eur(value: float) -> str:
    return f"{_int(value)} €"


def render(data: dict) -> str:
    calibration, decision = data["calibration"], data["decision"]
    chosen = calibration["chosen"]
    assumptions = decision["assumptions"]
    variant_rows = []
    for name, m in calibration["validation_metrics"].items():
        label = VARIANTS[name] + (" (elegida)" if name == chosen else "")
        predicted = calibration["group_3_4"][name]["mean_predicted"]
        variant_rows.append(
            f"| {label} | {m['brier']:.4f} | {m['log_loss']:.4f} | {m['ap']:.3f} | "
            f"{predicted:.1%} |"
        )
    group = calibration["group_3_4"][chosen]
    policy_rows = [
        f"| {POLICIES[name]} | {_int(p['contacted'])} | {_int(p['churners_captured'])} | "
        f"{_eur(p['benefit_eur'])} |"
        for name, p in decision["policies"].items()
    ]
    cls = decision["classification_at_threshold"]
    cm = cls["confusion_matrix"]
    model = decision["policies"]["model"]
    sections = [
        "# Calibración y decisión — Semana 5",
        "Generado con `uv run python -m churn.decision_report` desde "
        "[decision.json](decision.json) (spec 002 v1.5 §5.3.1 y spec 004 v1.0, opción A). "
        f"Todas las cifras son de validación ({_int(data['n_validation'])} clientes) y de "
        "**desarrollo**: la validación ya se usó para elegir modelo y calibrador. La prueba "
        "sigue sin usarse.",
        "## E-04: calibración",
        f"Calibradores ajustados con predicciones OOF de las {_int(data['n_training'])} filas "
        "de entrenamiento (5 pliegues, semilla 42) y comparados en validación por Brier; "
        "empate si la diferencia es < 1e-4.",
        "| Variante | Brier | Log loss | AP | Predicho grupo 3-4 |\n|---|---|---|---|---|\n"
        + "\n".join(variant_rows),
        f"Grupo de 3-4 productos en validación: n = {group['n']}, tasa observada "
        f"{group['observed_rate']:.1%}. Figura: [reliability.png](figures/reliability.png).",
        "## Regla de decisión (opción A)",
        f"Supuestos ilustrativos: V = {_eur(assumptions['customer_value_eur'])}, "
        f"c = {_eur(assumptions['contact_cost_eur'])}, "
        f"s = {assumptions['retention_success_rate']:.0%}. Contactar si p > t\\* = c / (s·V) = "
        f"{decision['threshold']:.4f}. El umbral es analítico: no se ajustó con datos.",
        "## Beneficio en validación",
        f"{_int(decision['n'])} clientes, {_int(decision['churners'])} abandonos. "
        "Beneficio = suma sobre contactados de (y·s·V - c).",
        "| Política | Contactados | Abandonos captados | Beneficio |\n|---|---|---|---|\n"
        + "\n".join(policy_rows),
        f"- Mejor referencia sin modelo: **{POLICIES[decision['best_reference']]}**; el modelo "
        f"aporta {_eur(decision['model_minus_best_reference_eur'])} más.",
        f"- El modelo captura el {decision['oracle_share_captured']:.1%} del beneficio del oráculo "
        f"contactando al {model['contacted_share']:.1%} de los clientes.",
        f"- En t\\*: precisión {cls['precision']:.3f}, sensibilidad {cls['recall']:.3f}, "
        f"F1 {cls['f1']:.3f}. Matriz de confusión: VN {cm['tn']}, FP {cm['fp']}, FN {cm['fn']}, "
        f"VP {cm['tp']}.",
        "## Límites (spec 004 §4)",
        "- Los supuestos económicos son ilustrativos; con otros valores cambian t\\* y el "
        "beneficio. Deciles y sensibilidad quedaron fuera del alcance por decisión del "
        "responsable.\n"
        "- La campaña se supone efectiva solo en quienes iban a irse, con la misma tasa s para "
        "todos y sin efectos negativos; no hay datos de tratamiento para estimar *uplift*.\n"
        "- V es igual para todos: el dataset no tiene ingresos por cliente.\n"
        "- Cifras de desarrollo; la estimación independiente corresponde a la evaluación final en "
        "prueba.",
        "## Trazabilidad",
        f"Commit: `{data['git_commit']}`. CSV SHA-256: `{data['csv_sha256']}`. Manifiesto "
        f"(canónico): `{data['split_manifest_sha256']}`. MLflow: calibración "
        f"`{data['run_ids']['calibration']}`, decisión `{data['run_ids']['decision']}`. "
        "Artefacto en `models/` (fuera de Git); metadata en "
        "[model_metadata.json](model_metadata.json).",
    ]
    return "\n\n".join(sections) + "\n"


def main() -> int:
    data = json.loads(DECISION_JSON.read_text(encoding="utf-8"))
    DECISION_MD.write_text(render(data), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
