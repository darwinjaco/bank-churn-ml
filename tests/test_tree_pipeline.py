"""Pipelines de árboles, ablaciones y espacios de búsqueda preregistrados (spec 002 v1.3)."""

import numpy as np
import pytest
from sklearn.preprocessing import StandardScaler

from churn.config import AUDIT_COLUMNS, FEATURE_SETS, ID_COLUMNS, RANDOM_SEED, TARGET
from churn.pipeline import build_pipeline, input_columns
from churn.search_spaces import (
    N_REPEATS,
    N_SPLITS,
    REEVALUATION_SEED,
    SEARCH_SPACES,
    TUNING_SEED,
)

FAST = {"rf": {"n_estimators": 20}, "xgb": {"n_estimators": 20}}


@pytest.mark.parametrize("model", ["rf", "xgb"])
def test_tree_pipeline_probabilities_names_and_no_scaling(valid_df, model):
    x = valid_df[FEATURE_SETS["tree"]]
    pipeline = build_pipeline(model, "tree", params=FAST[model]).fit(x, valid_df[TARGET])
    probabilities = pipeline.predict_proba(x)[:, 1]
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
    names = list(pipeline[:-1].get_feature_names_out())
    assert any("has_balance" in name for name in names)
    assert any(name.endswith("NumOfProducts") for name in names)
    assert any(name.endswith("__Age") for name in names)
    assert not any("Age^2" in name for name in names)
    assert all(not any(column in name for column in AUDIT_COLUMNS + ID_COLUMNS) for name in names)
    transformers = pipeline.named_steps["preprocess"].transformers_
    assert not any(isinstance(step, StandardScaler) for _, step, _ in transformers)


def test_r3_no_class_reweighting():
    rf = build_pipeline("rf", "tree").named_steps["model"].get_params()
    xgb = build_pipeline("xgb", "tree").named_steps["model"].get_params()
    assert rf["class_weight"] is None and rf["n_estimators"] == 500
    assert rf["random_state"] == RANDOM_SEED
    assert xgb["scale_pos_weight"] == 1 and xgb["tree_method"] == "hist"
    assert xgb["eval_metric"] == "logloss" and xgb["random_state"] == RANDOM_SEED
    assert xgb.get("early_stopping_rounds") is None


@pytest.mark.parametrize("model", ["rf", "xgb"])
def test_tree_pipelines_reject_gender_and_are_deterministic(valid_df, model):
    x = valid_df[FEATURE_SETS["tree"]]
    with pytest.raises(ValueError, match=AUDIT_COLUMNS[0]):
        build_pipeline(model, "tree", params=FAST[model]).fit(valid_df, valid_df[TARGET])
    first = build_pipeline(model, "tree", params=FAST[model]).fit(x, valid_df[TARGET])
    second = build_pipeline(model, "tree", params=FAST[model]).fit(x, valid_df[TARGET])
    np.testing.assert_array_equal(first.predict_proba(x), second.predict_proba(x))


@pytest.mark.parametrize(
    ("model", "feature_set"), [("logreg", "eda"), ("rf", "tree"), ("xgb", "tree")]
)
@pytest.mark.parametrize("column", ["EstimatedSalary", "NumOfProducts"])
def test_ablation_excludes_column(valid_df, model, feature_set, column):
    params = FAST.get(model)
    columns = input_columns(feature_set, (column,))
    assert column not in columns
    pipeline = build_pipeline(model, feature_set, exclude=(column,), params=params)
    pipeline.fit(valid_df[columns], valid_df[TARGET])
    names = pipeline[:-1].get_feature_names_out()
    assert not any(column in name for name in names)


def test_invalid_combinations_and_exclusions():
    invalid = [("rf", "eda"), ("xgb", "raw"), ("logreg", "tree"), ("dummy", "tree")]
    for model, feature_set in invalid:
        with pytest.raises(ValueError, match="Combinación"):
            build_pipeline(model, feature_set)
    with pytest.raises(ValueError, match="Solo se pueden excluir"):
        build_pipeline("rf", "tree", exclude=("Age",))


def test_search_spaces_match_spec_exactly():
    assert (TUNING_SEED, REEVALUATION_SEED, N_SPLITS, N_REPEATS) == (42, 2027, 5, 2)
    logreg, rf, xgb = (SEARCH_SPACES[name] for name in ("logreg", "rf", "xgb"))
    assert (logreg["feature_set"], rf["feature_set"], xgb["feature_set"]) == ("eda", "tree", "tree")
    assert (logreg["n_iter"], rf["n_iter"], xgb["n_iter"]) == (20, 40, 40)
    assert logreg["fixed"] == {"penalty": "l2", "solver": "lbfgs", "max_iter": 2000}

    def dist(value):
        return value.dist.name, value.args

    assert dist(logreg["distributions"]["C"]) == ("loguniform", (1e-3, 1e2))
    assert rf["fixed"] == {"n_estimators": 500, "random_state": 42, "n_jobs": -1}
    assert rf["distributions"] == {
        "max_depth": [None, 4, 6, 8, 10, 12, 16],
        "min_samples_leaf": [1, 2, 5, 10, 20, 50],
        "max_features": ["sqrt", 0.3, 0.5, 0.8],
    }
    assert xgb["fixed"] == {
        "tree_method": "hist",
        "scale_pos_weight": 1,
        "eval_metric": "logloss",
        "random_state": 42,
        "n_jobs": -1,
    }
    space = xgb["distributions"]
    assert space["n_estimators"] == [100, 200, 400, 800]
    assert space["max_depth"] == [2, 3, 4, 5, 6]
    assert space["min_child_weight"] == [1, 3, 5, 10]
    assert dist(space["learning_rate"]) == ("loguniform", (0.01, 0.3))
    assert dist(space["subsample"]) == ("uniform", (0.6, 0.4))
    assert dist(space["colsample_bytree"]) == ("uniform", (0.6, 0.4))
    assert dist(space["reg_lambda"]) == ("loguniform", (0.1, 10))
    assert set(space) == {
        "n_estimators",
        "learning_rate",
        "max_depth",
        "min_child_weight",
        "subsample",
        "colsample_bytree",
        "reg_lambda",
    }
