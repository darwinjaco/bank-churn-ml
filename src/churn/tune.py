"""Ajuste en dos fases (spec 002 v1.3 §5.1): FASE A búsqueda, FASE B re-evaluación."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import RandomizedSearchCV, RepeatedStratifiedKFold, StratifiedKFold

from churn.config import DATA_PROCESSED, PROJECT_ROOT, TARGET
from churn.pipeline import build_pipeline, input_columns
from churn.search_spaces import (
    N_REPEATS,
    N_SPLITS,
    REEVALUATION_SEED,
    SEARCH_SPACES,
    SIMPLICITY_ORDER,
    TUNING_SEED,
)
from churn.tracking import jsonable, log_run, provenance

TUNING_FILE = PROJECT_ROOT / "reports" / "tuning.json"
OOF_FILE = DATA_PROCESSED / "oof_phaseB.parquet"
METRICS = ("ap", "roc_auc", "brier", "log_loss")


def fold_metrics(actual, probability) -> dict:
    return {
        "ap": float(average_precision_score(actual, probability)),
        "roc_auc": float(roc_auc_score(actual, probability)),
        "brier": float(brier_score_loss(actual, probability)),
        "log_loss": float(log_loss(actual, probability, labels=[0, 1])),
    }


def summarize(folds: list[dict]) -> dict:
    summary = {}
    for name in METRICS:
        values = [fold["metrics"][name] for fold in folds]
        summary[name] = {"mean": float(np.mean(values)), "std": float(np.std(values, ddof=1))}
    return summary


def phase_a_splitter() -> StratifiedKFold:
    return StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=TUNING_SEED)


def phase_b_splits(x: pd.DataFrame, y: pd.Series) -> list[tuple[int, int, np.ndarray, np.ndarray]]:
    """(repetición, pliegue, índices de ajuste, índices de evaluación), idénticos entre familias."""
    splitter = RepeatedStratifiedKFold(
        n_splits=N_SPLITS, n_repeats=N_REPEATS, random_state=REEVALUATION_SEED
    )
    return [
        (number // N_SPLITS, number % N_SPLITS + 1, fitting, scoring)
        for number, (fitting, scoring) in enumerate(splitter.split(x, y))
    ]


def tune_family(
    family: str,
    training: pd.DataFrame,
    n_iter: int | None = None,
    fixed_override: dict | None = None,
) -> dict:
    """FASE A: RandomizedSearchCV sin refit; el mejor puntaje es optimista por construcción."""
    space = SEARCH_SPACES[family]
    fixed = {**space["fixed"], **(fixed_override or {})}
    columns = input_columns(space["feature_set"])
    search = RandomizedSearchCV(
        build_pipeline(family, space["feature_set"], params=fixed),
        param_distributions={f"model__{k}": v for k, v in space["distributions"].items()},
        n_iter=n_iter or space["n_iter"],
        scoring="average_precision",
        cv=phase_a_splitter(),
        refit=False,
        random_state=TUNING_SEED,
        n_jobs=1,
    )
    search.fit(training[columns], training[TARGET].reset_index(drop=True))
    best = {key.removeprefix("model__"): value for key, value in search.best_params_.items()}
    return {
        "family": family,
        "feature_set": space["feature_set"],
        "n_iter": int(n_iter or space["n_iter"]),
        "best_params": jsonable({**fixed, **best}),
        "search_ap_optimistic": float(search.best_score_),
        "search_ap_std": float(search.cv_results_["std_test_score"][search.best_index_]),
    }


def reevaluate(
    family: str,
    params: dict,
    training: pd.DataFrame,
    exclude: tuple[str, ...] = (),
) -> dict:
    """FASE B: pliegues nuevos 5x2 (semilla 2027); métricas por pliegue y OOF por repetición."""
    feature_set = SEARCH_SPACES[family]["feature_set"]
    columns = input_columns(feature_set, exclude)
    x = training[columns].reset_index(drop=True)
    y = training[TARGET].reset_index(drop=True)
    ids = training["CustomerId"].reset_index(drop=True)
    base = build_pipeline(family, feature_set, exclude=exclude, params=params)
    folds, oof = [], []
    for repeat, fold, fitting, scoring in phase_b_splits(x, y):
        fitted = clone(base).fit(x.iloc[fitting], y.iloc[fitting])
        probability = fitted.predict_proba(x.iloc[scoring])[:, 1]
        folds.append(
            {
                "repeat": repeat,
                "fold": fold,
                "metrics": fold_metrics(y.iloc[scoring], probability),
            }
        )
        oof.append(
            pd.DataFrame(
                {
                    "CustomerId": ids.iloc[scoring].to_numpy(),
                    "repeat": repeat,
                    "fold": fold,
                    "y": y.iloc[scoring].to_numpy(),
                    "proba": probability,
                }
            )
        )
    return {
        "family": family,
        "exclude": list(exclude),
        "folds": folds,
        "summary": summarize(folds),
        "oof": pd.concat(oof, ignore_index=True),
    }


def run_tuning(
    training: pd.DataFrame,
    n_iter: int | None = None,
    fixed_override: dict | None = None,
    log: bool = True,
) -> tuple[dict, pd.DataFrame]:
    """FASE A + FASE B para las tres familias; devuelve el JSON y las OOF de FASE B."""
    origin = provenance() if log else None
    families, oof_frames = {}, []
    for family in SIMPLICITY_ORDER:
        override = (fixed_override or {}).get(family)
        phase_a = tune_family(family, training, n_iter=n_iter, fixed_override=override)
        phase_b = reevaluate(family, phase_a["best_params"], training)
        oof_frames.append(phase_b["oof"].assign(family=family))
        entry = {
            "phase_a": phase_a,
            "phase_b": {"folds": phase_b["folds"], "summary": phase_b["summary"]},
        }
        if log:
            entry["phase_a"]["run_id"] = log_run(
                f"{family}-tuning",
                "tuning",
                {"model": family, "feature_set": phase_a["feature_set"], **phase_a["best_params"]},
                None,
                None,
                origin,
                tags={"search_score": "optimistic"},
                extra_metrics={"search_ap_optimistic": phase_a["search_ap_optimistic"]},
            )
            entry["phase_b"]["run_id"] = log_run(
                f"{family}-reevaluation",
                "reevaluation",
                {"model": family, "feature_set": phase_a["feature_set"], **phase_a["best_params"]},
                phase_b["summary"],
                phase_b["folds"],
                origin,
            )
        families[family] = entry
    payload = {
        "stage": "tuning",
        "n_training": len(training),
        "phase_a": {"cv": "StratifiedKFold", "n_splits": N_SPLITS, "seed": TUNING_SEED},
        "phase_b": {
            "cv": "RepeatedStratifiedKFold",
            "n_splits": N_SPLITS,
            "n_repeats": N_REPEATS,
            "seed": REEVALUATION_SEED,
        },
        **(origin or {}),
        "families": families,
    }
    return payload, pd.concat(oof_frames, ignore_index=True)


def main() -> int:
    from churn.train import load_training

    payload, oof = run_tuning(load_training())
    TUNING_FILE.parent.mkdir(parents=True, exist_ok=True)
    TUNING_FILE.write_text(
        json.dumps(jsonable(payload), indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    OOF_FILE.parent.mkdir(parents=True, exist_ok=True)
    oof.to_parquet(OOF_FILE, index=False)
    for family, entry in payload["families"].items():
        summary = entry["phase_b"]["summary"]["ap"]
        print(f"{family}: FASE B AP {summary['mean']:.4f} ± {summary['std']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
