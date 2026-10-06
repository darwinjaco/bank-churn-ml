"""Single source of truth for paths and the column contract (see specs/001)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

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

# Definiciones congeladas de EDA: especificación 003, versiones 1.0 y 1.1.
ALPHA = 0.05
BALANCE_SCALE = 10_000.0
AGE_BINS = (18, 30, 40, 50, 60, float("inf"))
AGE_LABELS = ("18-29", "30-39", "40-49", "50-59", "60+")
AGE_PEAK_RANGE = (18.0, 92.0)
RISK_DIFFERENCE_THRESHOLD = 0.05
GERMANY_OR_THRESHOLD = 1.5
SALARY_AUC_EQUIVALENCE = (0.45, 0.55)
AUC_BOOTSTRAP_REPLICATES = 2_000


def has_balance(balance: pd.Series) -> pd.Series:
    """Indicador fijo de saldo positivo."""
    return (balance > 0).astype(int)


def balance_10k(balance: pd.Series) -> pd.Series:
    """Saldo en unidades de diez mil."""
    return balance / BALANCE_SCALE


def age_band(age: pd.Series) -> pd.Series:
    """Tramos preregistrados, con límite inferior incluido."""
    return pd.cut(age, bins=AGE_BINS, labels=AGE_LABELS, right=False)


def centered_age(age: pd.Series) -> pd.Series:
    """Edad centrada en la media de la muestra de trabajo."""
    return age - age.mean()


def is_germany(geography: pd.Series) -> pd.Series:
    """Alemania frente a Francia y España juntas."""
    return geography.eq("Germany").astype(int)
