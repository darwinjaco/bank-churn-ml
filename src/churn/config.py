"""Single source of truth for paths and the column contract (see specs/001)."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
RAW_FILE = DATA_RAW / "Churn_Modelling.csv"

RANDOM_SEED = 42

TARGET = "Exited"

# Identifiers: never model inputs.
ID_COLUMNS = ["RowNumber", "CustomerId", "Surname"]

# Kept for fairness/segment audits only, excluded from model features (spec 001, D-02).
AUDIT_COLUMNS = ["Gender"]

NUMERIC_FEATURES = ["CreditScore", "Age", "Tenure", "Balance", "EstimatedSalary"]
ORDINAL_FEATURES = ["NumOfProducts"]
BINARY_FEATURES = ["HasCrCard", "IsActiveMember"]
CATEGORICAL_FEATURES = ["Geography"]

MODEL_FEATURES = NUMERIC_FEATURES + ORDINAL_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES

EXPECTED_COLUMNS = [
    "RowNumber",
    "CustomerId",
    "Surname",
    "CreditScore",
    "Geography",
    "Gender",
    "Age",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "HasCrCard",
    "IsActiveMember",
    "EstimatedSalary",
    "Exited",
]

GEOGRAPHIES = ["France", "Germany", "Spain"]
GENDERS = ["Female", "Male"]
