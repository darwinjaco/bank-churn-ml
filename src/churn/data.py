"""Data ingestion: load the raw CSV without touching it on disk."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from churn.config import EXPECTED_COLUMNS, RAW_FILE

DTYPES = {
    "RowNumber": "int64",
    "CustomerId": "int64",
    "Surname": "string",
    "CreditScore": "int64",
    "Geography": "string",
    "Gender": "string",
    "Age": "int64",
    "Tenure": "int64",
    "Balance": "float64",
    "NumOfProducts": "int64",
    "HasCrCard": "int64",
    "IsActiveMember": "int64",
    "EstimatedSalary": "float64",
    "Exited": "int64",
}


class DataFileNotFoundError(FileNotFoundError):
    """Raised when the raw dataset is missing, with instructions to obtain it."""


def load_raw(path: str | Path = RAW_FILE) -> pd.DataFrame:
    """Load the raw churn dataset with explicit dtypes.

    Fails fast if the file is missing or the header does not match the contract.
    Value-level checks live in ``churn.validation``.
    """
    path = Path(path)
    if not path.exists():
        raise DataFileNotFoundError(
            f"{path} not found. Download Churn_Modelling.csv (see README > Data) "
            "and place it in data/raw/."
        )

    header = pd.read_csv(path, nrows=0).columns.tolist()
    missing = sorted(set(EXPECTED_COLUMNS) - set(header))
    extra = sorted(set(header) - set(EXPECTED_COLUMNS))
    if missing or extra:
        raise ValueError(f"Column mismatch. Missing: {missing}. Unexpected: {extra}.")

    return pd.read_csv(path, dtype=DTYPES)
