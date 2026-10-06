"""Espacios de búsqueda preregistrados (spec 002 v1.3 §4 y §5.1). No modificar sin enmienda."""

from __future__ import annotations

from scipy.stats import loguniform, uniform

from churn.config import RANDOM_SEED

TUNING_SEED = RANDOM_SEED
REEVALUATION_SEED = 2027
N_SPLITS = 5
N_REPEATS = 2
SIMPLICITY_ORDER = ("logreg", "rf", "xgb")

SEARCH_SPACES = {
    "logreg": {
        "feature_set": "eda",
        "n_iter": 20,
        "fixed": {"penalty": "l2", "solver": "lbfgs", "max_iter": 2000},
        "distributions": {"C": loguniform(1e-3, 1e2)},
    },
    "rf": {
        "feature_set": "tree",
        "n_iter": 40,
        "fixed": {"n_estimators": 500, "random_state": RANDOM_SEED, "n_jobs": -1},
        "distributions": {
            "max_depth": [None, 4, 6, 8, 10, 12, 16],
            "min_samples_leaf": [1, 2, 5, 10, 20, 50],
            "max_features": ["sqrt", 0.3, 0.5, 0.8],
        },
    },
    "xgb": {
        "feature_set": "tree",
        "n_iter": 40,
        "fixed": {
            "tree_method": "hist",
            "scale_pos_weight": 1,
            "eval_metric": "logloss",
            "random_state": RANDOM_SEED,
            "n_jobs": -1,
        },
        "distributions": {
            "n_estimators": [100, 200, 400, 800],
            "learning_rate": loguniform(0.01, 0.3),
            "max_depth": [2, 3, 4, 5, 6],
            "min_child_weight": [1, 3, 5, 10],
            "subsample": uniform(0.6, 0.4),
            "colsample_bytree": uniform(0.6, 0.4),
            "reg_lambda": loguniform(0.1, 10),
        },
    },
}
