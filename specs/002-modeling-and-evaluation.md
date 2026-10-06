# Spec 002 — Modelling & evaluation

| Field  | Value |
|--------|-------|
| Status | Accepted (implementation weeks 3–4) |
| Owner  | Darwin Jacome Cuenca |
| Depends on | 001 |

## 1. Objective

Select a model that produces **well-ranked and calibrated** churn probabilities, as input for the profit-based decision layer (spec 003). The best model is not the one with the highest accuracy.

## 2. Data split

| Set | Share | Use |
|---|---|---|
| Train | 60 % | Fit pipelines, cross-validation, tuning |
| Validation | 20 % | Calibration fitting, threshold choice (spec 003) |
| Test | 20 % | **Touched once**, final report only |

- Stratified by `Exited`, `random_state = 42`.
- Split is saved as indices in `data/processed/` and checked in a test (no row in two sets).
- All preprocessing lives inside a `sklearn.Pipeline` and is fitted on train only.

## 3. Preprocessing & features

| Group | Columns | Transform |
|---|---|---|
| Numeric | CreditScore, Age, Tenure, Balance, EstimatedSalary | `StandardScaler` (linear models only) |
| Ordinal | NumOfProducts | As integer |
| Binary | HasCrCard, IsActiveMember | Passthrough |
| Categorical | Geography | `OneHotEncoder(handle_unknown="error")` |
| Engineered | `has_balance`, `balance_to_salary`, `age_band` | Documented in code; each must justify itself in CV |

## 4. Models

| Order | Model | Purpose |
|---|---|---|
| 0 | `DummyClassifier(strategy="prior")` | Floor reference |
| 1 | Logistic Regression | Interpretable baseline |
| 2 | Random Forest | Non-linear reference |
| 3 | XGBoost | Main candidate |

A neural network is **out of scope**: on 10k tabular rows it is not expected to beat gradient boosting, and adding it only to list the technology would weaken the project.

## 5. Evaluation protocol

- 5-fold `StratifiedKFold` on train. Report **mean ± std** for every metric.
- Tuning: `RandomizedSearchCV`, ≤ 50 iterations, small and documented search space, scoring = PR-AUC.
- Every run tracked in MLflow: params, metrics, git commit, data hash.

**Metrics**

| Role | Metric | Why |
|---|---|---|
| Primary | PR-AUC (average precision) | Imbalanced target; ranking quality on the positive class |
| Secondary | ROC-AUC | Global ranking |
| Calibration | Brier score, reliability curve | Probabilities are used for money decisions |
| Reported | Precision, Recall, F1 at chosen threshold, confusion matrix | Readability |

## 6. Selection rule (fixed before training)

1. Highest mean CV PR-AUC.
2. If two models differ by less than 1 std, choose the **simpler** one (LogReg > RF > XGBoost).
3. Final model must beat the Dummy and LogReg baselines on PR-AUC on the validation set.

## 7. Required experiments

| ID | Experiment | Question |
|---|---|---|
| E-01 | With vs. without `Gender` | What is the cost of decision D-02? |
| E-02 | With vs. without `NumOfProducts ≥ 3` signal | How much does the model depend on the artefact Q-03? |
| E-03 | With vs. without `EstimatedSalary` | Does a no-signal feature add noise? |
| E-04 | Raw vs. calibrated (isotonic / sigmoid) | Does calibration lower the Brier score on validation? |

## 8. Acceptance criteria

- [ ] Comparison table with mean ± std for all models in the README.
- [ ] E-01 to E-04 results documented with a one-line conclusion each.
- [ ] Test set used only once, logged in MLflow with tag `final=true`.
- [ ] Saved artefact = full pipeline (preprocessing + model + calibrator) + `metadata.json`.

## 9. Definition of Done

Selected model justified with this rule, experiments documented, artefact loadable by `predict.py` with a passing test.
