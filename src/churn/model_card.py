"""Reporte de auditoría y ficha del modelo (spec 002 v1.6 §11.5), generados desde JSON."""

from __future__ import annotations

import json

from churn.config import PROJECT_ROOT

REPORTS = PROJECT_ROOT / "reports"
AUDIT_MD = REPORTS / "audit.md"
CARD_MD = REPORTS / "model_card.md"
METRICS = {
    "contact_rate": "Tasa de contacto",
    "recall": "Sensibilidad",
    "precision": "Precisión",
    "calibration_gap": "Brecha de calibración",
}


def _load(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def _int(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def _eur(value: float) -> str:
    return f"{_int(value)} €"


def _pct(value) -> str:
    return "—" if value is None else f"{value:.1%}"


def _e01_table(e01: dict) -> str:
    rows = [
        "| Métrica | Female | Male | Δ (F - M) | IC 95 % | Alerta |",
        "|---|---|---|---|---|---|",
    ]
    for key, label in METRICS.items():
        m = e01[key]
        rows.append(
            f"| {label} | {_pct(m['Female'])} | {_pct(m['Male'])} | {m['difference']:+.3f} | "
            f"[{m['ci_low']:+.3f}; {m['ci_high']:+.3f}] | {'**sí**' if m['alert'] else 'no'} |"
        )
    return "\n".join(rows)


def _segments_table(segments: dict) -> str:
    rows = [
        "| Segmento | Nivel | n | Abandono | Predicho | Brecha | Contacto | Sensibilidad "
        "| Precisión |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for segment, levels in segments.items():
        for level, m in levels.items():
            rows.append(
                f"| {segment} | {level} | {m['n']} | {_pct(m['observed_rate'])} | "
                f"{_pct(m['mean_predicted'])} | {m['calibration_gap']:+.3f} | "
                f"{_pct(m['contact_rate'])} | {_pct(m['recall'])} | {_pct(m['precision'])} |"
            )
    return "\n".join(rows)


def render_audit(audit: dict) -> str:
    shap_info, errors = audit["shap"], audit["errors"]
    features = "\n".join(
        f"| {row['feature']} | {row['mean_abs_shap']:.4f} |" for row in shap_info["per_feature"]
    )
    groups = "\n".join(f"| {name} | {value:.4f} |" for name, value in shap_info["groups"].items())
    local = []
    for case in shap_info["local"]:
        contributions = "; ".join(
            f"{c['feature']} = {c['value']:g} ({c['shap']:+.3f})" for c in case["top_contributions"]
        )
        local.append(
            f"- **{case['case'].replace('_', ' ')}** (cliente {case['customer_id']}, p calibrada "
            f"{case['p_calibrated']:.3f}): {contributions}."
        )
    profiles = errors["profiles"]
    profile_rows = [
        "| Grupo | n | Edad | Productos | Activo | Alemania | Saldo cero |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, group in profiles.items():
        m = group["means"]
        if m is None:
            continue
        profile_rows.append(
            f"| {name} | {group['n']} | {m['Age']:.1f} | {m['NumOfProducts']:.2f} | "
            f"{_pct(m['IsActiveMember'])} | {_pct(m['Germany_share'])} | "
            f"{_pct(m['zero_balance_share'])} |"
        )
    near, worst, e01 = errors["near_threshold"], errors["worst_missed_segment"], audit["e01_gender"]
    sections = [
        "# Explicabilidad y auditoría — Semana 6",
        "Generado con `uv run python -m churn.model_card` desde [audit.json](audit.json) "
        "(spec 002 v1.6 §11). Validación, artefacto congelado de la semana 5 y t* = 1/6. "
        "Análisis de **desarrollo**: no cambia el modelo.",
        "## SHAP",
        f"Explica la {shap_info['explains']}; aditividad comprobada (error máximo "
        f"{shap_info['additivity_max_gap']:.1e}). Importancia predictiva, no causal.",
        "| Variable | Media de abs(SHAP) |\n|---|---|\n" + features,
        "| Grupo (R4) | Media de abs(SHAP) del grupo |\n|---|---|\n" + groups,
        "Explicaciones locales (cinco mayores contribuciones; valores de las variables tal como "
        "las recibe el modelo):",
        "\n".join(local),
        "Figura: [shap_importance.png](figures/shap_importance.png).",
        "## Errores en t*",
        "\n".join(profile_rows),
        f"- Banda ±{near['band']} alrededor de t*: {near['n']} clientes, abandono "
        f"{_pct(near['observed_rate'])}; {near['contacted']} contactados. Pequeños cambios de "
        "supuestos moverían a estos clientes de lado.",
        f"- Mayor proporción de abandonos no contactados: {worst['segment']} = {worst['level']} "
        f"({_pct(worst['missed_churn_share'])} de {worst['churners']} abandonos).",
        "## Segmentos",
        _segments_table(audit["segments"]),
        "## E-01: auditoría por género",
        f"n: Female {e01['n']['Female']}, Male {e01['n']['Male']}. Tasa observada de abandono: "
        f"Female {_pct(e01['observed_rate']['Female'])}, "
        f"Male {_pct(e01['observed_rate']['Male'])}. "
        "IC 95 % por bootstrap estratificado (2.000 réplicas, semilla 42). Alerta = IC sin 0 y "
        "abs(Δ) ≥ 0,05.",
        _e01_table(e01),
        "- La tasa de contacto y la sensibilidad no muestran diferencias detectables.\n"
        "- La alerta de precisión es coherente con tasas base distintas: con igual tasa de "
        "contacto, el grupo con más abandono obtiene mayor precisión; contactar a un hombre "
        "tiene, en promedio, menor probabilidad de evitar un abandono.\n"
        "- Al excluir `Gender`, el modelo subestima levemente a las mujeres y sobrestima a los "
        "hombres (Δ de calibración con IC sin 0, por debajo del umbral de alerta).\n"
        "- Según §11.4 solo se reporta; cualquier mitigación requiere enmienda.",
        "## Trazabilidad",
        f"Commit: `{audit['git_commit']}`; artefacto: `{audit['artifact_commit']}`; "
        f"MLflow: `{audit['run_id']}`.",
    ]
    return "\n\n".join(sections) + "\n"


def _final_section(final: dict | None, validation_decision: dict, phase_b: dict) -> str:
    if final is None:
        return "Pendiente: la prueba sigue reservada (spec 002 §11.6)."
    m, d = final["metrics"], final["decision"]
    pol = d["policies"]
    return (
        f"Única evaluación, el {final['evaluated_on']}, sobre {_int(final['n'])} clientes nunca "
        f"usados (abandono {final['churn_rate']:.1%}), con modelo, calibrador y umbral "
        "congelados. Es la estimación independiente del rendimiento.\n\n"
        "| Métrica | Prueba | Validación (desarrollo) |\n|---|---|---|\n"
        f"| AP | {m['ap']:.3f} | {validation_decision['_val_ap']:.3f} |\n"
        f"| ROC-AUC | {m['roc_auc']:.3f} | — |\n"
        f"| Brier | {m['brier']:.4f} | {validation_decision['_val_brier']:.4f} |\n"
        f"| Contactados | {_int(pol['model']['contacted'])} | "
        f"{_int(validation_decision['policies']['model']['contacted'])} |\n"
        f"| Beneficio del modelo | {_eur(pol['model']['benefit_eur'])} | "
        f"{_eur(validation_decision['policies']['model']['benefit_eur'])} |\n"
        f"| Beneficio contactando a todos | {_eur(pol['everyone']['benefit_eur'])} | "
        f"{_eur(validation_decision['policies']['everyone']['benefit_eur'])} |\n"
        f"| Fracción del oráculo | {d['oracle_share_captured']:.1%} | "
        f"{validation_decision['oracle_share_captured']:.1%} |\n\n"
        f"En t*: precisión {d['classification_at_threshold']['precision']:.3f}, sensibilidad "
        f"{d['classification_at_threshold']['recall']:.3f}. AP de FASE B (CV de entrenamiento): "
        f"{phase_b['ap']['mean']:.3f} ± {phase_b['ap']['std']:.3f}."
    )


def render_card(
    audit: dict,
    decision: dict,
    selection: dict,
    tuning: dict,
    metadata: dict,
    final: dict | None = None,
) -> str:
    rf = tuning["families"]["rf"]["phase_b"]["summary"]
    cal = decision["calibration"]
    dec = {
        **decision["decision"],
        "_val_ap": cal["validation_metrics"][metadata["calibrator"]]["ap"],
        "_val_brier": cal["validation_metrics"][metadata["calibrator"]]["brier"],
    }
    pol = dec["policies"]
    e01 = audit["e01_gender"]
    alerts = [METRICS[key] for key in METRICS if e01[key]["alert"]] or ["ninguna"]
    sections = [
        "# Ficha del modelo — Abandono bancario → decisiones de retención",
        "Generada con `uv run python -m churn.model_card` desde los JSON de `reports/`.",
        "## Resumen",
        f"Random Forest calibrado ({metadata['calibrator']}) que estima la probabilidad de "
        "abandono de un cliente y recomienda contactarlo si el beneficio esperado de la campaña "
        f"es positivo (p > {metadata['threshold']:.4f}).",
        "## Uso previsto y no previsto",
        "- **Previsto:** priorizar contactos de retención en un ejercicio de portafolio con datos "
        "públicos; demostrar un flujo reproducible de modelado y decisión.\n"
        "- **No previsto:** decisiones reales sobre clientes, crédito o precios; cualquier uso "
        "con datos de una institución sin revalidar, recalibrar y revisar supuestos; "
        "interpretaciones causales.",
        "## Datos",
        "Churn Modelling (Kaggle), 10.000 clientes, probablemente sintético. División "
        "estratificada 60/20/20 (semilla 42) con manifiesto versionado. Entrenamiento 6.000; "
        "validación 2.000 (usada para seleccionar y calibrar); prueba 2.000 reservada.",
        "## Variables",
        f"- Entradas: {', '.join(metadata['input_columns'])} (+ `has_balance` derivada).\n"
        f"- Excluidas: identificadores; `Gender` (solo auditoría, D-02); "
        f"{', '.join(metadata['excluded_columns'])} (E-03).",
        "## Entrenamiento y selección",
        f"Búsqueda en dos fases (spec 002 §5.1) entre LogReg, Random Forest y XGBoost; regla de "
        f"parsimonia de §6. Random Forest: AP en FASE B {rf['ap']['mean']:.3f} ± "
        f"{rf['ap']['std']:.3f}; AP en validación {selection['validation_ap']['rf']:.3f}. "
        "Hiperparámetros: "
        + ", ".join(f"{k}={v}" for k, v in metadata["hyperparameters"].items())
        + ".",
        "## Calibración y decisión",
        f"- Brier en validación: sin calibrar {cal['validation_metrics']['none']['brier']:.4f}, "
        f"{metadata['calibrator']} "
        f"{cal['validation_metrics'][metadata['calibrator']]['brier']:.4f}.\n"
        "- Regla: contactar si p > c / (s·V) con V = "
        f"{_eur(metadata['assumptions']['customer_value_eur'])}, "
        f"c = {_eur(metadata['assumptions']['contact_cost_eur'])}, "
        f"s = {metadata['assumptions']['retention_success_rate']:.0%} (supuestos ilustrativos).\n"
        f"- Validación: el modelo contacta a {_int(pol['model']['contacted'])} de {_int(dec['n'])} "
        f"clientes y obtiene {_eur(pol['model']['benefit_eur'])}, frente a "
        f"{_eur(pol['everyone']['benefit_eur'])} contactando a todos; "
        f"{dec['oracle_share_captured']:.1%} del oráculo.",
        "## Explicabilidad y equidad",
        "- Variables más influyentes (SHAP): "
        + ", ".join(row["feature"] for row in audit["shap"]["per_feature"][:4])
        + ".\n"
        f"- E-01 (género): alertas preregistradas: {', '.join(alerts)}. Tasa de contacto "
        f"{_pct(e01['contact_rate']['Female'])} frente a {_pct(e01['contact_rate']['Male'])}; "
        f"sensibilidad {_pct(e01['recall']['Female'])} frente a {_pct(e01['recall']['Male'])}. "
        "Detalle en [audit.md](audit.md).",
        "## Limitaciones",
        "- Datos probablemente sintéticos: los resultados no son evidencia bancaria real.\n"
        f"- El grupo de 3-4 productos (≈3 % de clientes) aporta una parte importante de la AP "
        f"(E-02: AP {selection['e02']['b_ap_all']['mean']:.3f} con todos frente a "
        f"{selection['e02']['b_ap_without_3_4']['mean']:.3f} sin ese grupo).\n"
        "- Alemania no tiene clientes con saldo cero (Q-10): saldo y geografía comparten señal.\n"
        "- Los abandonos de clientes jóvenes y activos son los más difíciles de detectar.\n"
        "- Supuestos económicos ilustrativos e iguales para todos; sin datos de tratamiento "
        "(*uplift*); sin análisis de sensibilidad (fuera de alcance por decisión del "
        "responsable).\n"
        "- Las métricas de validación son de desarrollo.",
        "## Evaluación final en prueba",
        _final_section(final, dec, rf),
        "## Trazabilidad",
        f"Artefacto: commit `{metadata['git_commit']}`; CSV `{metadata['csv_sha256'][:12]}…`; "
        f"manifiesto `{metadata['split_manifest_sha256'][:12]}…`; versiones "
        + ", ".join(f"{k} {v}" for k, v in metadata["versions"].items())
        + ".",
    ]
    return "\n\n".join(sections) + "\n"


def main() -> int:
    audit = _load("audit.json")
    AUDIT_MD.write_text(render_audit(audit), encoding="utf-8")
    CARD_MD.write_text(
        render_card(
            audit,
            _load("decision.json"),
            _load("model_selection.json"),
            _load("tuning.json"),
            _load("model_metadata.json"),
            _load("final_test.json") if (REPORTS / "final_test.json").exists() else None,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
