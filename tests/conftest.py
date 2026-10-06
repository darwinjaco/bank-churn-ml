"""Shared fixtures. CI never needs the real dataset: tests run on a synthetic sample."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from churn.config import RAW_FILE
from churn.data import DTYPES


@pytest.fixture
def valid_df() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    n = 200
    df = pd.DataFrame(
        {
            "RowNumber": np.arange(1, n + 1),
            "CustomerId": np.arange(15_000_000, 15_000_000 + n),
            "Surname": [f"Name{i % 50}" for i in range(n)],
            "CreditScore": rng.integers(350, 851, n),
            "Geography": rng.choice(["France", "Germany", "Spain"], n),
            "Gender": rng.choice(["Female", "Male"], n),
            "Age": rng.integers(18, 93, n),
            "Tenure": rng.integers(0, 11, n),
            "Balance": np.where(rng.random(n) < 0.35, 0.0, rng.uniform(1e4, 2.5e5, n)),
            "NumOfProducts": rng.choice([1, 2, 3, 4], n, p=[0.5, 0.45, 0.04, 0.01]),
            "HasCrCard": rng.integers(0, 2, n),
            "IsActiveMember": rng.integers(0, 2, n),
            "EstimatedSalary": rng.uniform(1e3, 2e5, n),
            "Exited": (rng.random(n) < 0.2).astype(int),
        }
    )
    return df.astype(DTYPES)


@pytest.fixture
def csv_path(tmp_path, valid_df):
    path = tmp_path / "Churn_Modelling.csv"
    valid_df.to_csv(path, index=False)
    return path


@pytest.fixture
def real_df():
    if not RAW_FILE.exists():
        pytest.skip("Real dataset not present (expected in CI).")
    from churn.data import load_raw

    return load_raw()
