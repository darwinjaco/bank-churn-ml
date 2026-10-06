"""Reporte legible de la semana 4, generado solo desde tuning.json y model_selection.json."""

from __future__ import annotations

import json

from churn.config import PROJECT_ROOT
from churn.search_spaces import SIMPLICITY_ORDER

TUNING_JSON = PROJECT_ROOT / "reports" / "tuning.json"
SELECTION_JSON = PROJECT_ROOT / "reports" / "model_selection.json"
SELECTION_MD = PROJECT_ROOT / "reports" / "model_selection.md"
NAMES = {"logreg": "LogReg (FS-EDA)", "rf": "Random Forest (FS-TREE)", "xgb": "XGBoost (FS-TREE)"}


def _ms(summary: dict) -> str:
    return f"{summary['mean']:.3f} ± {summary['std']:.3f}"


def _deltas(deltas: dict) -> str:
    total = len(deltas["by_fold"])
    return (
        f"{deltas['mean']:+.3f} ± {deltas['std']:.3f} "
        f"({deltas['positive']}/{total} pliegues positivos, {deltas['negative']}/{total} negativos)"
    )


def _phase_b_table(tuning: dict, selection: dict) -> str:
    rows = [
        "| Familia | AP búsqueda (optimista) | AP FASE B | ROC-AUC | Brier | Log loss |",
        "|---|---|---|---|---|---|",
    ]
    for family in SIMPLICITY_ORDER:
        entry = tuning["families"][family]
        summary = entry["phase_b"]["summary"]
        rows.append(
            f"| {NAMES[family]} | {entry['phase_a']['search_ap_optimistic']:.3f} | "
            f"{_ms(summary['ap'])} | {_ms(summary['roc_auc'])} | {_ms(summary['brier'])} | "
            f"{_ms(summary['log_loss'])} |"
        )
    informative = selection["paired_vs_best_informative"]
    best = selection["steps_1_2"]["best"]
    lines = [
        f"- {NAMES[family]} - {NAMES[best]}: {_deltas(deltas)}"
        for family, deltas in informative.items()
    ]
    return (
        "\n".join(rows)
        + "\n\nDiferencias pareadas frente al mejor (informativas):\n\n"
        + ("\n".join(lines))
    )


def _rule(selection: dict) -> str:
    steps = selection["steps_1_2"]
    best, chosen = steps["best"], steps["chosen"]
    close = ", ".join(NAMES[name] for name in steps["close"])
    validation = selection["validation_ap"]
    val_rows = "\n".join(
        f"| {NAMES.get(name, 'Dummy (FS-RAW)')} | {value:.3f} |"
        for name, value in validation.items()
    )
    outcome = selection["steps_3_5"]
    return "\n".join(
        [
            f"1. **Mejor AP media de FASE B:** {NAMES[best]}, {steps['best_mean']:.3f} "
            f"(std {steps['best_std']:.3f}).",
            "2. **Cercanos** (diferencia < std del mejor o media igual): "
            + close
            + ". Diferencias: "
            + "; ".join(
                f"{NAMES[name]} {value:.3f}" for name, value in steps["differences_to_best"].items()
            )
            + f". Por parsimonia se elige **{NAMES[chosen]}**.",
            f"3-5. **Validación** (primer uso; ajuste con las {selection['n_training']:,} filas "
            f"de entrenamiento, AP en {selection['n_validation']:,} filas):",
            "",
            "| Modelo | AP validación |",
            "|---|---|",
            val_rows,
            "",
            f"Resultado del paso {outcome['step']}: `{outcome['status']}`. {outcome['detail']}",
            "",
            f"**Modelo final de la semana 4: {NAMES.get(selection['final_model'], 'ninguno')}"
            f"**, sin {', '.join(selection['final_exclude']) or 'exclusiones'}.",
        ]
    )


def _experiments(selection: dict) -> str:
    e03, e02 = selection["e03"], selection["e02"]
    decision = "se **elimina**" if e03["drop_salary"] else "se **conserva**"
    group = e02["c_group_3_4"]
    by_repeat = lambda part: " / ".join(  # noqa: E731
        f"{value:.3f}" for value in part["by_repeat"].values()
    )
    return "\n".join(
        [
            "### E-03: salario",
            "",
            f"Δ AP (sin - con `EstimatedSalary`): {_deltas(e03['deltas'])}. Umbral "
            f"preregistrado: Δ ≥ {e03['threshold']:.3f} → eliminar. Decisión: {decision} "
            "`EstimatedSalary`.",
            "",
            "### E-02: dependencia de `NumOfProducts` (auditoría, no elimina la variable)",
            "",
            f"- (a) Δ AP (sin - con `NumOfProducts`, configuración final): "
            f"{_deltas(e02['a_deltas'])}.",
            f"- (b) AP por repetición, todos los clientes (n = {e02['n_all']:,}): "
            f"{by_repeat(e02['b_ap_all'])}, media {e02['b_ap_all']['mean']:.3f}. "
            f"Sin el grupo de 3-4 productos (n = {e02['n_without_3_4']:,}): "
            f"{by_repeat(e02['b_ap_without_3_4'])}, media {e02['b_ap_without_3_4']['mean']:.3f}.",
            f"- (c) Grupo de 3-4 productos (n = {group['n']}): tasa observada "
            f"{group['observed_rate']:.1%}; probabilidad media predicha "
            f"{group['mean_predicted']:.1%} (por repetición: "
            + " / ".join(f"{v:.1%}" for v in group["mean_predicted_by_repeat"].values())
            + ").",
        ]
    )


def _reading(selection: dict) -> str:
    steps, e02 = selection["steps_1_2"], selection["e02"]
    group = e02["c_group_3_4"]
    gap = e02["b_ap_all"]["mean"] - e02["b_ap_without_3_4"]["mean"]
    share = group["n"] / e02["n_all"]
    calibration_gap = group["observed_rate"] - group["mean_predicted"]
    return "\n".join(
        [
            f"- La diferencia entre {NAMES[steps['best']]} y el elegido es menor que la "
            "desviación del mejor; la regla prefiere el modelo más simple entre los cercanos.",
            "- La re-evaluación en pliegues nuevos (FASE B) da AP ligeramente menores que la "
            "búsqueda, como se esperaba del sesgo optimista; el orden de las familias se mantiene.",
            f"- E-02 (b): el {share:.1%} de clientes con 3-4 productos aporta {gap:.3f} de AP. "
            "La AP sin ese grupo es la referencia más honesta del rendimiento sobre el resto.",
            f"- E-02 (c): en ese grupo la probabilidad media predicha queda {calibration_gap:.1%} "
            "por debajo de la tasa observada. Es un insumo para la calibración (E-04, semana 5) y "
            "la ficha del modelo (semana 6).",
            "- Todas las métricas son de desarrollo: la validación se usó para elegir; la "
            "estimación independiente corresponde a la evaluación final en prueba.",
        ]
    )


def render(tuning: dict, selection: dict) -> str:
    params = ", ".join(f"`{k}={v}`" for k, v in selection["chosen_params"].items())
    run_ids = [
        f"| {family}-{stage} | `{tuning['families'][family][phase]['run_id']}` |"
        for family in SIMPLICITY_ORDER
        for stage, phase in (("tuning", "phase_a"), ("reevaluation", "phase_b"))
    ] + [f"| {name} | `{run}` |" for name, run in selection.get("run_ids", {}).items()]
    sections = [
        "# Selección de modelo — Semana 4",
        "Generado con `uv run python -m churn.selection_report` desde "
        "[tuning.json](tuning.json) y [model_selection.json](model_selection.json) "
        "(spec 002 v1.4). Tres decimales; media ± desviación estándar muestral (ddof=1).",
        "## Protocolo",
        f"FASE A: `RandomizedSearchCV` (20/40/40 iteraciones), 5 pliegues, semilla "
        f"{tuning['phase_a']['seed']}, AP. FASE B: mejores configuraciones en "
        f"`RepeatedStratifiedKFold` 5x2, semilla {tuning['phase_b']['seed']}, idénticos para "
        f"todas las familias. Entrenamiento: {tuning['n_training']:,} filas. La prueba no se usa.",
        "## FASE B",
        _phase_b_table(tuning, selection),
        "## Regla de selección (§6), paso a paso",
        _rule(selection),
        "## Experimentos",
        _experiments(selection),
        "## Lectura descriptiva",
        _reading(selection),
        "## Hiperparámetros del modelo elegido",
        params,
        "## Trazabilidad",
        f"Código de FASE A/B: `{tuning['git_commit']}`; selección y experimentos: "
        f"`{selection['git_commit']}`. CSV SHA-256: `{selection['csv_sha256']}`. Manifiesto "
        f"SHA-256: `{selection['split_manifest_sha256']}`. MLflow: `sqlite:///mlruns/mlflow.db`, "
        "experimento `bank-churn`.",
        "| Corrida | Run ID |\n|---|---|\n" + "\n".join(run_ids),
    ]
    return "\n\n".join(sections) + "\n"


def main() -> int:
    tuning = json.loads(TUNING_JSON.read_text(encoding="utf-8"))
    selection = json.loads(SELECTION_JSON.read_text(encoding="utf-8"))
    SELECTION_MD.write_text(render(tuning, selection), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
