"""Semana 5: calibrar el modelo final (E-04), aplicar la spec 004 y congelar el artefacto."""

from __future__ import annotations

import json
import platform

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.base import clone

from churn.calibration import (
    CalibratedModel,
    choose_calibrator,
    fit_calibrators,
    group_calibration,
    oof_predictions,
    reliability_table,
    variant_metrics,
)
from churn.config import PROJECT_ROOT, TARGET
from churn.decision import assumptions, evaluate_policies, threshold
from churn.experiments import HIGH_PRODUCTS, SELECTION_FILE, load_validation
from churn.pipeline import build_pipeline, input_columns
from churn.search_spaces import SEARCH_SPACES
from churn.tracking import jsonable, log_run, provenance

DECISION_FILE = PROJECT_ROOT / "reports" / "decision.json"
METADATA_COPY = PROJECT_ROOT / "reports" / "model_metadata.json"
MODELS_DIR = PROJECT_ROOT / "models"
FIGURE_FILE = PROJECT_ROOT / "reports" / "figures" / "reliability.png"


def final_configuration(selection: dict) -> dict:
    """Configuración congelada en la semana 4 (spec 002 §6 y E-03)."""
    family = selection["final_model"]
    if family is None:
        raise ValueError("La semana 4 no produjo un modelo final.")
    feature_set = SEARCH_SPACES[family]["feature_set"] if family != "dummy" else "raw"
    exclude = tuple(selection["final_exclude"])
    return {
        "family": family,
        "feature_set": feature_set,
        "exclude": exclude,
        "params": selection["chosen_params"],
        "columns": input_columns(feature_set, exclude),
    }


def run_decision(selection: dict, training: pd.DataFrame, validation: pd.DataFrame) -> dict:
    """E-04 con OOF de entrenamiento y comparación en validación; luego la regla de la spec 004."""
    config = final_configuration(selection)
    columns = config["columns"]
    pipeline = build_pipeline(
        config["family"], config["feature_set"], exclude=config["exclude"], params=config["params"]
    )
    y_train = training[TARGET].to_numpy()
    y_val = validation[TARGET].to_numpy()

    oof = oof_predictions(pipeline, training[columns], training[TARGET])
    calibrators = fit_calibrators(oof, y_train)
    fitted = clone(pipeline).fit(training[columns], training[TARGET])
    raw = fitted.predict_proba(validation[columns])[:, 1]
    variants = {name: np.clip(cal.transform(raw), 0, 1) for name, cal in calibrators.items()}
    metrics = {name: variant_metrics(values, y_val) for name, values in variants.items()}
    chosen = choose_calibrator({name: values["brier"] for name, values in metrics.items()})
    high = validation["NumOfProducts"].to_numpy() >= HIGH_PRODUCTS

    return {
        "config": config,
        "calibration": {
            "oof_train_metrics": variant_metrics(oof, y_train),
            "validation_metrics": metrics,
            "chosen": chosen,
            "reliability": {name: reliability_table(v, y_val) for name, v in variants.items()},
            "group_3_4": {name: group_calibration(v, y_val, high) for name, v in variants.items()},
        },
        "decision": evaluate_policies(variants[chosen], y_val),
        "model": CalibratedModel(fitted, calibrators[chosen], columns),
        "n_training": len(training),
        "n_validation": len(validation),
    }


def build_metadata(result: dict, origin: dict) -> dict:
    config = result["config"]
    return {
        "model_family": config["family"],
        "feature_set": config["feature_set"],
        "input_columns": config["columns"],
        "excluded_columns": list(config["exclude"]),
        "hyperparameters": config["params"],
        "calibrator": result["calibration"]["chosen"],
        "decision_rule": "contactar si p_calibrada > t* = c / (s * V) (spec 004)",
        "threshold": threshold(),
        "assumptions": assumptions(),
        "trained_on": {"partition": "train", "n_rows": result["n_training"]},
        "versions": {
            "python": platform.python_version(),
            "scikit-learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        **origin,
        "specs": {"002": "v1.5", "004": "v1.0"},
        "final_test_evaluation": "pendiente",
    }


def main() -> int:
    from churn.plots import reliability_figure
    from churn.train import load_training

    selection = json.loads(SELECTION_FILE.read_text(encoding="utf-8"))
    result = run_decision(selection, load_training(), load_validation())
    origin = provenance()
    metadata = build_metadata(result, origin)
    calibration_info, decision_info = result["calibration"], result["decision"]

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(result["model"], MODELS_DIR / "model.joblib")
    for path in (MODELS_DIR / "metadata.json", METADATA_COPY):
        path.write_text(json.dumps(jsonable(metadata), indent=2) + "\n", encoding="utf-8")
    reliability_figure(calibration_info["reliability"], calibration_info["chosen"], FIGURE_FILE)

    base = {"model": result["config"]["family"], **result["config"]["params"]}
    run_ids = {
        "calibration": log_run(
            "e04-calibration",
            "calibration",
            {**base, "chosen_calibrator": calibration_info["chosen"]},
            None,
            None,
            origin,
            tags={"experiment": "E-04"},
            extra_metrics={
                f"val_{metric}_{name}": value
                for name, values in calibration_info["validation_metrics"].items()
                for metric, value in values.items()
            },
        ),
        "decision": log_run(
            "decision-option-a",
            "decision",
            {**base, **assumptions(), "threshold": threshold()},
            None,
            None,
            origin,
            extra_metrics={
                f"benefit_{name}": policy["benefit_eur"]
                for name, policy in decision_info["policies"].items()
            },
        ),
    }
    payload = {
        "stage": "decision",
        **origin,
        "n_training": result["n_training"],
        "n_validation": result["n_validation"],
        "config": {k: v for k, v in result["config"].items() if k != "columns"},
        "calibration": calibration_info,
        "decision": decision_info,
        "run_ids": run_ids,
    }
    DECISION_FILE.write_text(
        json.dumps(jsonable(payload), indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        f"Calibrador: {calibration_info['chosen']}; contactados: "
        f"{decision_info['policies']['model']['contacted']}; beneficio modelo: "
        f"{decision_info['policies']['model']['benefit_eur']:.0f} EUR"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
