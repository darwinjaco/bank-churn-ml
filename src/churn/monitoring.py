"""Monitoreo simulado de cambios de distribución (spec 006 §4).

Referencia: entrenamiento. Actual: validación remuestreada (semilla 2028). La partición de
prueba nunca se usa: los datos llegan solo por ``load_exploration`` (entrenamiento y validación).
Umbrales, escenarios y expectativas E1-E4 están preregistrados en la spec 006 §4.5-4.6.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import average_precision_score, brier_score_loss
from statsmodels.stats.multitest import multipletests

from churn.config import PROJECT_ROOT, TARGET
from churn.decision import decide, expected_benefit, realized_benefit, threshold
from churn.split import load_exploration

MONITORING_FILE = PROJECT_ROOT / "reports" / "monitoring.json"
MONITORING_MD = PROJECT_ROOT / "reports" / "monitoring.md"
FIGURE_FILE = PROJECT_ROOT / "reports" / "figures" / "monitoring_psi.png"

MONITOR_SEED = 2028
EPSILON = 1e-4  # Sustituye proporciones nulas en el PSI (evita ln(0)).
PSI_STABLE = 0.10
PSI_ALERT = 0.25
CALIBRATION_TOLERANCE = 0.03
BRIER_FACTOR = 1.15
CONTACT_SHIFT = 0.02  # E4: cambio de la tasa de contacto frente a S0.
ALPHA = 0.05

CONTINUOUS = ("CreditScore", "Age", "Balance")
DISCRETE = ("Tenure", "NumOfProducts", "HasCrCard", "IsActiveMember", "Geography")
MONITORED = CONTINUOUS + DISCRETE

AGE_TILT = 0.05
GERMANY_FACTOR = 2.0
INACTIVE_SHARE = 0.70
PREVALENCE_SHARE = 0.35

SCENARIOS = {
    "S0": "Validación sin remuestrear (control de falsas alarmas)",
    "S1": "Envejecimiento: pesos ∝ exp(0,05·(Age - mediana))",
    "S2": "Proporción de Germany x 2 (composición exacta)",
    "S3": "IsActiveMember = 0 en el 70 % (composición exacta)",
    "S4": "Tasa de abandono del 35 % por etiqueta (composición exacta)",
}
SHIFTED_VARIABLE = {"S1": "Age", "S2": "Geography", "S3": "IsActiveMember"}


# ---------------------------------------------------------------- PSI
def psi_from_proportions(expected, actual, eps: float = EPSILON) -> float:
    """PSI = Σ (a - e)·ln(a/e), con proporciones nulas reemplazadas por ``eps``."""
    e = np.clip(np.asarray(expected, dtype=float), eps, None)
    a = np.clip(np.asarray(actual, dtype=float), eps, None)
    return float(np.sum((a - e) * np.log(a / e)))


def decile_edges(reference) -> np.ndarray:
    """Bordes interiores únicos de los deciles de la referencia."""
    quantiles = np.quantile(np.asarray(reference, dtype=float), np.linspace(0, 1, 11))
    return np.unique(quantiles[1:-1])


def binned_proportions(values, edges: np.ndarray) -> np.ndarray:
    """Intervalos cerrados por la derecha: (-inf, e1], (e1, e2], ..., (ek, +inf)."""
    index = np.searchsorted(edges, np.asarray(values, dtype=float), side="left")
    counts = np.bincount(index, minlength=len(edges) + 1)
    return counts / counts.sum()


def level_proportions(reference, current) -> tuple[np.ndarray, np.ndarray, list]:
    reference, current = pd.Series(reference), pd.Series(current)
    levels = sorted(set(reference.unique()) | set(current.unique()), key=str)
    ref = reference.value_counts(normalize=True).reindex(levels, fill_value=0.0)
    cur = current.value_counts(normalize=True).reindex(levels, fill_value=0.0)
    return ref.to_numpy(), cur.to_numpy(), levels


def psi(reference, current, kind: str = "continuous") -> float:
    if kind == "continuous":
        edges = decile_edges(reference)
        return psi_from_proportions(
            binned_proportions(reference, edges), binned_proportions(current, edges)
        )
    if kind == "discrete":
        ref, cur, _ = level_proportions(reference, current)
        return psi_from_proportions(ref, cur)
    raise ValueError(f"Tipo desconocido: {kind}")


def psi_level(value: float) -> str:
    if value > PSI_ALERT:
        return "alerta"
    return "moderado" if value >= PSI_STABLE else "estable"


# ---------------------------------------------------------------- escenarios
def exact_composition(frame: pd.DataFrame, mask, share: float, rng) -> pd.DataFrame:
    """round(share·n) filas del grupo y el resto fuera de él, con reemplazo en cada grupo."""
    mask = np.asarray(mask, dtype=bool)
    if not 0 < share < 1 or mask.all() or not mask.any():
        raise ValueError("Proporción o grupo no válidos para la composición exacta.")
    n = len(frame)
    k = round(share * n)
    inside = rng.choice(np.flatnonzero(mask), size=k, replace=True)
    outside = rng.choice(np.flatnonzero(~mask), size=n - k, replace=True)
    order = rng.permutation(np.concatenate([inside, outside]))
    return frame.iloc[order].reset_index(drop=True)


def weighted_resample(frame: pd.DataFrame, weights, rng) -> pd.DataFrame:
    weights = np.asarray(weights, dtype=float)
    rows = rng.choice(len(frame), size=len(frame), replace=True, p=weights / weights.sum())
    return frame.iloc[rows].reset_index(drop=True)


def build_scenarios(validation: pd.DataFrame, seed: int = MONITOR_SEED) -> dict:
    """S0-S4 de la spec 006 §4.3; un generador nuevo con la misma semilla por escenario."""
    base = validation.reset_index(drop=True)
    age = base["Age"].to_numpy(dtype=float)
    germany = base["Geography"].eq("Germany").to_numpy()
    return {
        "S0": base.copy(),
        "S1": weighted_resample(
            base, np.exp(AGE_TILT * (age - np.median(age))), np.random.default_rng(seed)
        ),
        "S2": exact_composition(
            base, germany, GERMANY_FACTOR * germany.mean(), np.random.default_rng(seed)
        ),
        "S3": exact_composition(
            base, base["IsActiveMember"].eq(0), INACTIVE_SHARE, np.random.default_rng(seed)
        ),
        "S4": exact_composition(
            base, base[TARGET].eq(1), PREVALENCE_SHARE, np.random.default_rng(seed)
        ),
    }


# ---------------------------------------------------------------- evaluación
def drift_tests(reference: pd.DataFrame, current: pd.DataFrame) -> dict:
    """KS (continuas) o chi² (discretas) con Holm sobre las variables monitoreadas."""
    rows = {}
    for column in MONITORED:
        if column in CONTINUOUS:
            result = stats.ks_2samp(reference[column], current[column])
            rows[column] = {"method": "ks", "statistic": float(result.statistic)}
            p_value = float(result.pvalue)
        else:
            levels = sorted(
                set(reference[column].unique()) | set(current[column].unique()), key=str
            )
            table = np.vstack(
                [
                    reference[column].value_counts().reindex(levels, fill_value=0).to_numpy(),
                    current[column].value_counts().reindex(levels, fill_value=0).to_numpy(),
                ]
            )
            result = stats.chi2_contingency(table)
            rows[column] = {"method": "chi2", "statistic": float(result.statistic)}
            p_value = float(result.pvalue)
        rows[column]["p_value"] = p_value
    reject, adjusted, _, _ = multipletests([r["p_value"] for r in rows.values()], ALPHA, "holm")
    for row, significant, p_holm in zip(rows.values(), reject, adjusted, strict=True):
        row["p_holm"] = float(p_holm)
        row["significant"] = bool(significant)
    return rows


def evaluate_scenario(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    p_reference,
    p_current,
    t: float | None = None,
) -> dict:
    """PSI, pruebas de apoyo, señales sin etiquetas y métricas con etiquetas."""
    t = threshold() if t is None else t
    p_current = np.asarray(p_current, dtype=float)
    y = current[TARGET].to_numpy()
    tests = drift_tests(reference, current)
    variables = {}
    for column in MONITORED:
        kind = "continuous" if column in CONTINUOUS else "discrete"
        value = psi(reference[column], current[column], kind)
        variables[column] = {"psi": value, "level": psi_level(value), **tests[column]}
    probability_psi = psi(p_reference, p_current, "continuous")
    alarms = [c for c, row in variables.items() if row["psi"] > PSI_ALERT]
    if probability_psi > PSI_ALERT:
        alarms.append("probabilidad")
    contact = decide(p_current, t)
    benefit = expected_benefit(p_current)
    return {
        "n": len(current),
        "variables": variables,
        "probability": {"psi": probability_psi, "level": psi_level(probability_psi)},
        "alarm": bool(alarms),
        "alarm_on": alarms,
        "unlabeled": {
            "contact_rate": float(contact.mean()),
            "mean_predicted": float(p_current.mean()),
            "expected_benefit_eur": float(benefit[contact].sum()),
        },
        "labeled": {
            "churn_rate": float(y.mean()),
            "ap": float(average_precision_score(y, p_current)),
            "brier": float(brier_score_loss(y, p_current)),
            "calibration_gap": float(p_current.mean() - y.mean()),
            "benefit_model_eur": realized_benefit(contact, y),
            "benefit_everyone_eur": realized_benefit(np.ones_like(contact), y),
            "benefit_nobody_eur": 0.0,
        },
    }


def add_degradation(results: dict) -> None:
    """Degradación: calibración global fuera de ±3 pp o Brier > 1,15 x Brier(S0)."""
    brier_s0 = results["S0"]["labeled"]["brier"]
    for result in results.values():
        labeled = result["labeled"]
        calibration_out = abs(labeled["calibration_gap"]) > CALIBRATION_TOLERANCE
        brier_out = labeled["brier"] > BRIER_FACTOR * brier_s0
        result["degradation"] = {
            "calibration_out": bool(calibration_out),
            "brier_ratio": labeled["brier"] / brier_s0,
            "brier_out": bool(brier_out),
            "degraded": bool(calibration_out or brier_out),
        }


def check_expectations(results: dict) -> dict:
    """E1-E4 tal como están preregistradas (spec 006 §4.6)."""
    s0 = results["S0"]
    e2 = {}
    for name, column in SHIFTED_VARIABLE.items():
        result = results[name]
        alarm_on_variable = result["variables"][column]["psi"] > PSI_ALERT
        calibrated = not result["degradation"]["calibration_out"]
        e2[name] = {
            "variable": column,
            "alarm_on_variable": alarm_on_variable,
            "calibration_within": calibrated,
            "met": alarm_on_variable and calibrated,
        }
    s4 = results["S4"]
    variables_quiet = all(row["psi"] <= PSI_ALERT for row in s4["variables"].values())
    base_rate = s0["unlabeled"]["contact_rate"]
    e4 = {
        name: {
            "contact_rate_change": results[name]["unlabeled"]["contact_rate"] - base_rate,
            "met": abs(results[name]["unlabeled"]["contact_rate"] - base_rate) > CONTACT_SHIFT,
        }
        for name in ("S1", "S2", "S3", "S4")
    }
    return {
        "E1": {
            "description": "S0 sin alarma y sin degradación",
            "met": not s0["alarm"] and not s0["degradation"]["degraded"],
        },
        "E2": {
            "description": "S1-S3: alarma en la variable desplazada y calibración dentro de ±3 pp",
            "by_scenario": e2,
            "met": all(row["met"] for row in e2.values()),
        },
        "E3": {
            "description": "S4: PSI de variables ≤ 0,25 y calibración fuera de ±3 pp",
            "variables_quiet": variables_quiet,
            "calibration_out": s4["degradation"]["calibration_out"],
            "met": variables_quiet and s4["degradation"]["calibration_out"],
        },
        "E4": {
            "description": "La tasa de contacto se aleja más de 2 pp de S0 en S1-S4",
            "by_scenario": e4,
            "met": all(row["met"] for row in e4.values()),
        },
    }


def run_monitoring(model, training: pd.DataFrame, validation: pd.DataFrame) -> dict:
    """Evalúa S0-S4 con el modelo congelado; referencia de la probabilidad = validación (S0)."""
    t = threshold()
    reference = training.reset_index(drop=True)
    p_reference = model.predict_proba(validation)
    results = {}
    for name, current in build_scenarios(validation).items():
        results[name] = {
            "description": SCENARIOS[name],
            **evaluate_scenario(reference, current, p_reference, model.predict_proba(current), t),
        }
    add_degradation(results)
    return {
        "config": {
            "seed": MONITOR_SEED,
            "reference": f"entrenamiento ({len(training)} filas)",
            "current": f"validación remuestreada ({len(validation)} filas por escenario)",
            "probability_reference": "probabilidad del modelo en validación sin remuestrear (S0)",
            "threshold": t,
            "psi": {"stable_below": PSI_STABLE, "alert_above": PSI_ALERT, "epsilon": EPSILON},
            "degradation": {
                "calibration_tolerance": CALIBRATION_TOLERANCE,
                "brier_factor": BRIER_FACTOR,
            },
            "contact_shift": CONTACT_SHIFT,
            "alpha_holm": ALPHA,
        },
        "scenarios": results,
        "expectations": check_expectations(results),
    }


def load_partitions() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Entrenamiento y validación; ``load_exploration`` no lee la partición de prueba."""
    exploration = load_exploration()
    training = exploration.loc[exploration["partition"] == "train"].copy()
    validation = exploration.loc[exploration["partition"] == "validation"].copy()
    return training, validation


# ---------------------------------------------------------------- reporte
def _pct(value: float) -> str:
    return f"{100 * value:.1f} %"


def _yes(flag: bool) -> str:
    return "sí" if flag else "no"


def render_markdown(result: dict) -> str:
    scenarios = result["scenarios"]
    names = list(scenarios)
    lines = [
        "# Monitoreo simulado de cambios de distribución",
        "",
        "Generado por `churn-monitor` (spec 006 §4). Referencia: entrenamiento; actual: "
        "validación remuestreada con semilla "
        f"{result['config']['seed']}. La partición de prueba no se usa. Umbrales y "
        "expectativas preregistrados antes de ejecutar.",
        "",
        "## Escenarios",
        "",
        "| Escenario | Definición |",
        "|---|---|",
        *(f"| {name} | {scenarios[name]['description']} |" for name in names),
        "",
        "## PSI por variable",
        "",
        "Estable < 0,10 · moderado 0,10-0,25 · **alerta > 0,25**. ✱ = diferencia "
        "significativa en KS/chi² con corrección de Holm (solo apoyo).",
        "",
        "| Variable | " + " | ".join(names) + " |",
        "|---|" + "---|" * len(names),
    ]
    for column in MONITORED:
        cells = []
        for name in names:
            row = scenarios[name]["variables"][column]
            mark = "**" if row["psi"] > PSI_ALERT else ""
            star = " ✱" if row["significant"] else ""
            cells.append(f"{mark}{row['psi']:.3f}{mark}{star}")
        lines.append(f"| {column} | " + " | ".join(cells) + " |")
    probability = []
    for name in names:
        value = scenarios[name]["probability"]["psi"]
        mark = "**" if value > PSI_ALERT else ""
        probability.append(f"{mark}{value:.3f}{mark}")
    lines += [
        "| Probabilidad predicha | " + " | ".join(probability) + " |",
        "| **Alarma** | " + " | ".join(_yes(scenarios[name]["alarm"]) for name in names) + " |",
        "",
        "## Señales sin etiquetas y métricas con etiquetas",
        "",
        "| Métrica | " + " | ".join(names) + " |",
        "|---|" + "---|" * len(names),
    ]
    rows = [
        ("Tasa de contacto", lambda s: _pct(s["unlabeled"]["contact_rate"])),
        ("Probabilidad media", lambda s: _pct(s["unlabeled"]["mean_predicted"])),
        ("Beneficio esperado (€)", lambda s: f"{s['unlabeled']['expected_benefit_eur']:,.0f}"),
        ("Tasa de abandono observada", lambda s: _pct(s["labeled"]["churn_rate"])),
        ("Calibración global (pp)", lambda s: f"{100 * s['labeled']['calibration_gap']:+.1f}"),
        ("AP", lambda s: f"{s['labeled']['ap']:.3f}"),
        (
            "Brier (x S0)",
            lambda s: f"{s['labeled']['brier']:.4f} ({s['degradation']['brier_ratio']:.2f})",
        ),
        ("Beneficio realizado modelo (€)", lambda s: f"{s['labeled']['benefit_model_eur']:,.0f}"),
        (
            "Beneficio contactar a todos (€)",
            lambda s: f"{s['labeled']['benefit_everyone_eur']:,.0f}",
        ),
        ("**Degradación**", lambda s: _yes(s["degradation"]["degraded"])),
    ]
    for label, getter in rows:
        lines.append(f"| {label} | " + " | ".join(getter(scenarios[n]) for n in names) + " |")
    expectations = result["expectations"]
    lines += [
        "",
        "Contactar a nadie rinde 0 € en todos los escenarios. Degradación: calibración global "
        "fuera de ±3 pp o Brier > 1,15 x S0.",
        "",
        "## Expectativas preregistradas",
        "",
        "| Expectativa | Resultado | Detalle |",
        "|---|---|---|",
        f"| E1 — {expectations['E1']['description']} | "
        f"{'cumplida' if expectations['E1']['met'] else '**no cumplida**'} | "
        f"alarma {_yes(scenarios['S0']['alarm'])}, degradación "
        f"{_yes(scenarios['S0']['degradation']['degraded'])} |",
    ]
    e2 = expectations["E2"]["by_scenario"]
    detail = "; ".join(
        f"{n}: PSI {row['variable']} "
        f"{scenarios[n]['variables'][row['variable']]['psi']:.3f}, "
        f"calibración {'dentro' if row['calibration_within'] else 'fuera'}"
        for n, row in e2.items()
    )
    lines.append(
        f"| E2 — {expectations['E2']['description']} | "
        f"{'cumplida' if expectations['E2']['met'] else '**no cumplida**'} | {detail} |"
    )
    e3 = expectations["E3"]
    s4_max = max(scenarios["S4"]["variables"].items(), key=lambda item: item[1]["psi"])
    lines.append(
        f"| E3 — {e3['description']} | {'cumplida' if e3['met'] else '**no cumplida**'} | "
        f"PSI máximo {s4_max[0]} {s4_max[1]['psi']:.3f}; calibración "
        f"{100 * scenarios['S4']['labeled']['calibration_gap']:+.1f} pp |"
    )
    e4 = expectations["E4"]["by_scenario"]
    detail = "; ".join(f"{n}: {100 * row['contact_rate_change']:+.1f} pp" for n, row in e4.items())
    lines.append(
        f"| E4 — {expectations['E4']['description']} | "
        f"{'cumplida' if expectations['E4']['met'] else '**no cumplida**'} | {detail} |"
    )
    lines += [
        "",
        "## Lectura",
        "",
        "- Las alarmas de PSI miden cambios en las entradas, no en el error del modelo. Solo las "
        "métricas con etiquetas (calibración, Brier, beneficio realizado) muestran degradación.",
        "- El Brier depende de la mezcla de clientes: si aumenta la proporción de grupos con más "
        "abandono puede subir sin que el modelo empeore (spec 006 §4.7).",
        "- Datos remuestreados de validación (ya usada para seleccionar y calibrar): es una "
        "simulación de mecanismos, no una estimación del comportamiento en producción.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    from churn.artifact import load_model
    from churn.plots import monitoring_psi_figure
    from churn.tracking import jsonable, provenance

    training, validation = load_partitions()
    result = run_monitoring(load_model(), training, validation)
    payload = {"stage": "monitoring", **provenance(), **result}
    MONITORING_FILE.write_text(
        json.dumps(jsonable(payload), indent=2, allow_nan=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    MONITORING_MD.write_text(render_markdown(result), encoding="utf-8")
    monitoring_psi_figure(result, FIGURE_FILE)
    summary = {name: row["met"] for name, row in result["expectations"].items()}
    print(f"Expectativas: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
