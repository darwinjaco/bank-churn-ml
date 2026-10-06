# Bank Churn → Retention Decisions

[![CI](https://github.com/<your-user>/bank-churn-ml/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-user>/bank-churn-ml/actions/workflows/ci.yml)

End-to-end ML system that predicts customer churn **and decides who is worth contacting**, by turning calibrated probabilities into expected profit.

> 🚧 Work in progress. Week 1 of 8: repository, data contract and validation.

## Why this project is different

Most churn projects stop at "XGBoost got 0.86 AUC". This one answers the business question:
*given a retention budget, which customers should we call, and how much money does that save compared with calling nobody or everyone?*

## Quickstart

Requirements: Python 3.11, [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/<your-user>/bank-churn-ml.git
cd bank-churn-ml
uv sync                      # creates .venv and installs locked dependencies
uv run pre-commit install    # lint/format hooks on every commit
uv run pytest                # runs on synthetic data, no dataset needed
```

## Data

The dataset is **not** included in this repository.

1. Download *Churn Modelling* from Kaggle (`shrutimechlearn/churn-modelling`), for example:
   ```bash
   kaggle datasets download -d shrutimechlearn/churn-modelling -p data/raw --unzip
   ```
2. Check that the file is at `data/raw/Churn_Modelling.csv`.
3. Validate it:
   ```bash
   uv run churn-validate --out reports/data_quality.json
   ```

The data contract (columns, types, ranges, roles) is defined in [`specs/001`](specs/001-overview-and-data-contract.md).

## Week 1 findings

| Check | Result |
|---|---|
| Rows / duplicates / nulls | 10,000 / 0 / 0 |
| Churn rate | 20.4 % (imbalanced) |
| `Balance = 0` | 36.2 % of customers (point mass) |
| Churn with 3–4 products | 83–100 % on only 326 customers (likely synthetic artefact) |
| Leakage scan | No single feature above AUC 0.90 (max: Age, 0.73) |

## Project structure

```text
specs/        Design specs, written before code (SDD)
src/churn/    Package: config, data loading, validation
tests/        Pytest suite (synthetic fixtures + optional real-data tests)
data/         raw/ and processed/ (git-ignored)
reports/      Generated reports
notebooks/    Exploration only, no business logic
```

## Roadmap

- [x] Week 1: repo, CI, data contract, validation
- [ ] Week 2: EDA and hypotheses
- [ ] Week 3: pipeline, split, baselines, MLflow
- [ ] Week 4: RF / XGBoost, CV, tuning
- [ ] Week 5: calibration and profit-based decision layer
- [ ] Week 6: SHAP, error and segment analysis, model card
- [ ] Week 7: FastAPI + Streamlit + Docker
- [ ] Week 8: drift monitoring, deployment, final README

## License

MIT. The dataset keeps its original Kaggle licence and is not redistributed here.
