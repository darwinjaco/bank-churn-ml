# Spec 001 — Project overview & data contract

| Field  | Value |
|--------|-------|
| Status | Accepted |
| Owner  | Darwin Jacome Cuenca |
| Week   | 1 |

## 1. Objective

Build a **retention decision system**, not only a churn classifier. For each customer, the system must answer:

1. What is the probability that this customer leaves? (calibrated probability)
2. Is it worth contacting them, given campaign cost and customer value? (expected profit)
3. Why did the model score them this way? (local explanation)

Success is measured in **expected profit vs. baseline policies** ("contact nobody", "contact everyone", "contact random 20 %"), not by accuracy or F1 alone.

## 2. Context

- Dataset: *Churn Modelling* (Kaggle), 10,000 customers of a European bank, 14 columns.
- Public, anonymised and partly **synthetic** (see §6). Results must not be presented as real banking evidence.
- The dataset has no revenue or cost data. All monetary values are **explicit assumptions** with sensitivity analysis (spec 003).

## 3. Scope

| In scope | Out of scope |
|---|---|
| Binary churn prediction, calibration, profit-based threshold | Survival / time-to-churn modelling |
| Global and local explainability (SHAP) | Causal / uplift claims (no treatment data) |
| Segment and fairness audit | Real customer data of any institution |
| API, dashboard, Docker, CI, drift simulation | Production-grade auth, scaling, SLAs |

## 4. Data contract

**Source file:** `data/raw/Churn_Modelling.csv` (not committed, see README > Data).
**Grain:** one row = one customer. **Primary key:** `CustomerId`.

| Column | Type | Allowed values | Role | Description |
|---|---|---|---|---|
| RowNumber | int | ≥ 1, unique | ID (dropped) | File row index |
| CustomerId | int | unique | ID (dropped) | Customer key |
| Surname | string | non-empty | ID (dropped) | Last name |
| CreditScore | int | 300–900 | Feature | Credit score |
| Geography | string | France, Germany, Spain | Feature | Country |
| Gender | string | Female, Male | **Audit only** | Used for fairness checks, not as input |
| Age | int | 18–100 | Feature | Age in years |
| Tenure | int | 0–10 | Feature | Years as customer |
| Balance | float | ≥ 0 | Feature | Account balance |
| NumOfProducts | int | 1–4 | Feature | Number of bank products |
| HasCrCard | int | {0, 1} | Feature | Has credit card |
| IsActiveMember | int | {0, 1} | Feature | Active member flag |
| EstimatedSalary | float | > 0 | Feature | Estimated salary |
| **Exited** | int | {0, 1} | **Target** | 1 = customer left the bank |

**Model input:** the 9 *Feature* columns. **Model output:** `churn_probability ∈ [0, 1]`, `contact: bool`, `expected_profit`, `top_reasons`.

## 5. Validation rules

Implemented in `src/churn/validation.py`.

- **Hard checks (pipeline stops):** exact column set, dtypes, ranges and categories in §4, unique `CustomerId`, binary target. Errors are collected lazily, so all violations are reported at once.
- **Soft checks (logged in `reports/data_quality.json`):** duplicated rows, class balance, `Balance = 0` share, churn by `NumOfProducts`, implausible salaries, and **single-feature AUC ≥ 0.90 as a leakage alarm**.

## 6. Known data issues (week 1 findings)

| ID | Finding | Evidence | Handling |
|---|---|---|---|
| Q-01 | Class imbalance | churn rate 20.4 % | Stratified splits; PR-AUC as primary metric |
| Q-02 | Point mass at `Balance = 0` | 36.2 % of rows | Add `has_balance` flag (week 3) |
| Q-03 | `NumOfProducts ≥ 3` churn 83–100 % on 326 rows | report | Likely synthetic. Audit model reliance; run ablation without this signal |
| Q-04 | `EstimatedSalary` has no signal | single-feature AUC 0.509; 59 rows < 1,000 | Test for uniform distribution in EDA; candidate to drop |
| Q-05 | No leakage detected | max single-feature AUC = Age 0.732 | Re-check after feature engineering |

## 7. Technical decisions

| ID | Decision | Rationale |
|---|---|---|
| D-01 | Drop `RowNumber`, `CustomerId`, `Surname` | Identifiers. `Surname` (2,932 values) overfits and can proxy nationality/ethnicity |
| D-02 | `Gender` excluded from model inputs, kept for audit | Avoid direct use of a protected attribute. Cost of exclusion is measured in week 4 and reported |
| D-03 | Raw data never committed nor edited | Licence not verified for redistribution; reproducibility via `load_raw()` |
| D-04 | CI runs on synthetic fixtures | CI must not depend on the dataset. Real-data tests are marked `realdata` and skip if absent |
| D-05 | `pandera` for schema validation | Declarative, readable contract; lazy mode reports all errors |

## 8. Acceptance criteria

- [ ] `uv sync && uv run pytest` passes on a clean clone (real-data tests skipped).
- [ ] `uv run churn-validate` passes on the real file and writes `reports/data_quality.json`.
- [ ] Any contract violation (bad range, unknown category, missing or extra column) makes validation fail, with tests for each case.
- [ ] CI is green on `main`.

## 9. Definition of Done

Code merged, tests and lint green in CI, this spec updated with real findings, README explains how to get the data.
