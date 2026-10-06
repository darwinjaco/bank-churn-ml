"""Selección (§6), E-03 y E-02 (§7) y validación de la semana 4 (spec 002 v1.3)."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from churn.config import PROJECT_ROOT, TARGET
from churn.pipeline import build_pipeline, input_columns
from churn.search_spaces import SEARCH_SPACES
from churn.selection import COMPLEX, select_candidate, validate_choice
from churn.split import load_exploration
from churn.tracking import jsonable, log_run, provenance
from churn.tune import OOF_FILE, TUNING_FILE, reevaluate

SELECTION_FILE = PROJECT_ROOT / "reports" / "model_selection.json"
E03_THRESHOLD = -0.005  # §7: si media(delta) >= -0,005 se elimina EstimatedSalary.
SALARY = "EstimatedSalary"
PRODUCTS = "NumOfProducts"
HIGH_PRODUCTS = 3  # Grupo 3-4 del artefacto Q-03.


def load_validation() -> pd.DataFrame:
    """Primera lectura de validación (§6, pasos 3-4). No existe cargador de prueba."""
    exploration = load_exploration()
    return exploration.loc[exploration["partition"] == "validation"].copy()


def paired_deltas(with_folds: list[dict], without_folds: list[dict], metric: str = "ap") -> dict:
    """Delta = métrica(sin) - métrica(con), pareada por (repetición, pliegue)."""
    key = lambda fold: (fold["repeat"], fold["fold"])  # noqa: E731
    left, right = sorted(with_folds, key=key), sorted(without_folds, key=key)
    if [key(f) for f in left] != [key(f) for f in right]:
        raise ValueError("Los pliegues no coinciden.")
    deltas = [b["metrics"][metric] - a["metrics"][metric] for a, b in zip(left, right, strict=True)]
    return {
        "by_fold": deltas,
        "mean": float(np.mean(deltas)),
        "std": float(np.std(deltas, ddof=1)),
        "positive": int(sum(d > 0 for d in deltas)),
        "negative": int(sum(d < 0 for d in deltas)),
    }


def e03_decision(mean_delta: float) -> bool:
    """True = eliminar EstimatedSalary (umbral preregistrado de §7)."""
    return mean_delta >= E03_THRESHOLD


def ap_by_repeat(oof: pd.DataFrame) -> dict:
    """AP calculada dentro de cada repetición (unidad de cálculo de B-02) y su media."""
    values = {
        int(repeat): float(average_precision_score(part["y"], part["proba"]))
        for repeat, part in oof.groupby("repeat", sort=True)
    }
    return {"by_repeat": values, "mean": float(np.mean(list(values.values())))}


def e02_segments(oof: pd.DataFrame, products: pd.Series) -> dict:
    """E-02 (b) y (c) por repetición; ``products`` indexado por CustomerId."""
    frame = oof.assign(products=oof["CustomerId"].map(products))
    if frame["products"].isna().any():
        raise ValueError("Hay CustomerId de las OOF sin NumOfProducts.")
    for repeat, part in frame.groupby("repeat"):
        if not part["CustomerId"].is_unique:
            raise ValueError(f"Cliente repetido dentro de la repetición {repeat}.")
    high = frame["products"] >= HIGH_PRODUCTS
    unique = frame.drop_duplicates("CustomerId")
    calibration = {}
    for repeat, part in frame[high].groupby("repeat", sort=True):
        calibration[int(repeat)] = float(part["proba"].mean())
    observed = frame[high].drop_duplicates("CustomerId")["y"]
    return {
        "b_ap_all": ap_by_repeat(frame),
        "b_ap_without_3_4": ap_by_repeat(frame[~high]),
        "n_all": len(unique),
        "n_without_3_4": int((unique["products"] < HIGH_PRODUCTS).sum()),
        "c_group_3_4": {
            "n": len(observed),
            "observed_rate": float(observed.mean()),
            "mean_predicted_by_repeat": calibration,
            "mean_predicted": float(np.mean(list(calibration.values()))),
        },
    }


def validation_ap(
    family: str,
    params: dict,
    training: pd.DataFrame,
    validation: pd.DataFrame,
    exclude: tuple[str, ...] = (),
) -> float:
    """Ajusta con todo el entrenamiento y mide AP una vez en validación."""
    feature_set = SEARCH_SPACES[family]["feature_set"] if family != "dummy" else "raw"
    columns = input_columns(feature_set, exclude)
    pipeline = build_pipeline(family, feature_set, exclude=exclude, params=params)
    pipeline.fit(training[columns], training[TARGET])
    probability = pipeline.predict_proba(validation[columns])[:, 1]
    return float(average_precision_score(validation[TARGET], probability))


def run_selection(
    tuning: dict,
    phase_b_oof: pd.DataFrame,
    training: pd.DataFrame,
    validation: pd.DataFrame,
    log: bool = True,
) -> dict:
    """Orden fijo de §6: pasos 1-2 → E-03 → E-02 → ajuste final → validación (pasos 3-5)."""
    origin = provenance() if log else None
    families = tuning["families"]
    cv_summary = {name: entry["phase_b"]["summary"]["ap"] for name, entry in families.items()}
    step_1_2 = select_candidate(cv_summary)
    chosen = step_1_2["chosen"]
    params = families[chosen]["phase_a"]["best_params"]
    best = step_1_2["best"]
    informative = {
        name: paired_deltas(families[best]["phase_b"]["folds"], entry["phase_b"]["folds"])
        for name, entry in families.items()
        if name != best
    }

    # E-03: con y sin EstimatedSalary sobre los pliegues de FASE B, sin reajustar.
    with_salary = families[chosen]["phase_b"]
    without_salary = reevaluate(chosen, params, training, exclude=(SALARY,))
    e03_deltas = paired_deltas(with_salary["folds"], without_salary["folds"])
    drop_salary = e03_decision(e03_deltas["mean"])
    final_exclude = (SALARY,) if drop_salary else ()

    # E-02 sobre la configuración final (después de la decisión de E-03).
    if drop_salary:
        final_folds, final_oof = without_salary["folds"], without_salary["oof"]
    else:
        final_folds = with_salary["folds"]
        final_oof = phase_b_oof.loc[phase_b_oof["family"] == chosen].drop(columns="family")
    without_products = reevaluate(chosen, params, training, exclude=(*final_exclude, PRODUCTS))
    e02_a = paired_deltas(final_folds, without_products["folds"])
    products = training.set_index("CustomerId")[PRODUCTS]
    e02_bc = e02_segments(final_oof, products)

    # Validación (primera vez): candidato, Dummy y, si es complejo, LogReg con la misma decisión.
    val_scores = {
        "dummy": validation_ap("dummy", {}, training, validation),
        chosen: validation_ap(chosen, params, training, validation, final_exclude),
    }
    if chosen in COMPLEX:
        logreg_params = families["logreg"]["phase_a"]["best_params"]
        val_scores["logreg"] = validation_ap(
            "logreg", logreg_params, training, validation, final_exclude
        )
    step_3_5 = validate_choice(chosen, val_scores)

    result = {
        "stage": "selection",
        "n_training": len(training),
        "n_validation": len(validation),
        **(origin or {}),
        "phase_b_ap": cv_summary,
        "search_ap_optimistic": {
            name: entry["phase_a"]["search_ap_optimistic"] for name, entry in families.items()
        },
        "paired_vs_best_informative": informative,
        "steps_1_2": step_1_2,
        "chosen_params": params,
        "e03": {
            "deltas": e03_deltas,
            "threshold": E03_THRESHOLD,
            "drop_salary": drop_salary,
            "without_salary_summary": without_salary["summary"],
        },
        "final_exclude": list(final_exclude),
        "final_features": input_columns(SEARCH_SPACES[chosen]["feature_set"], final_exclude),
        "e02": {
            "a_deltas": e02_a,
            "a_without_products_summary": without_products["summary"],
            **e02_bc,
        },
        "validation_ap": val_scores,
        "steps_3_5": step_3_5,
        "final_model": step_3_5["final"],
    }
    if log:
        base = {"model": chosen, "feature_set": SEARCH_SPACES[chosen]["feature_set"], **params}
        result["run_ids"] = {
            "e03": log_run(
                f"{chosen}-E-03-sin-salario",
                "experiment",
                {**base, "exclude": SALARY},
                without_salary["summary"],
                without_salary["folds"],
                origin,
                tags={"experiment": "E-03", "decision": f"drop_salary={drop_salary}"},
                extra_metrics={"delta_ap_mean": e03_deltas["mean"]},
            ),
            "e02": log_run(
                f"{chosen}-E-02-sin-productos",
                "experiment",
                {**base, "exclude": ",".join((*final_exclude, PRODUCTS))},
                without_products["summary"],
                without_products["folds"],
                origin,
                tags={"experiment": "E-02"},
                extra_metrics={
                    "delta_ap_mean": e02_a["mean"],
                    "ap_without_3_4_mean": e02_bc["b_ap_without_3_4"]["mean"],
                    "ap_all_by_repeat_mean": e02_bc["b_ap_all"]["mean"],
                },
            ),
            "selection": log_run(
                "selection-rule",
                "selection",
                {**base, "final_exclude": ",".join(final_exclude) or "none"},
                None,
                None,
                origin,
                tags={
                    "chosen_cv": chosen,
                    "final_model": str(step_3_5["final"]),
                    "rule_status": step_3_5["status"],
                },
                extra_metrics={f"val_ap_{name}": value for name, value in val_scores.items()},
            ),
        }
    return result


def main() -> int:
    from churn.train import load_training

    tuning = json.loads(TUNING_FILE.read_text(encoding="utf-8"))
    result = run_selection(tuning, pd.read_parquet(OOF_FILE), load_training(), load_validation())
    SELECTION_FILE.write_text(
        json.dumps(jsonable(result), indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(jsonable({k: result[k] for k in ("steps_1_2", "steps_3_5")}), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
