"""Generador sintético existente, compartido por CLI y dashboard (spec 005 v1.3)."""

from __future__ import annotations

import csv
import io

import numpy as np

SEED = 20_261_123
N_CUSTOMERS = 20
COLUMNS = [
    "ClienteEjemplo",
    "CreditScore",
    "Age",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "HasCrCard",
    "IsActiveMember",
    "Geography",
]


def generate(seed: int = SEED, n: int = N_CUSTOMERS) -> str:
    """Mismo CSV determinista; ninguna fila procede del dataset real."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        geography = str(rng.choice(["France", "Germany", "Spain"], p=[0.5, 0.25, 0.25]))
        zero = geography != "Germany" and rng.random() < 0.45
        balance = 0.0 if zero else round(float(rng.uniform(20_000, 220_000)), 2)
        rows.append(
            [
                f"EJ-{i + 1:02d}",
                int(np.clip(rng.normal(650, 90), 350, 850)),
                int(np.clip(rng.normal(40, 11), 18, 85)),
                int(rng.integers(0, 11)),
                f"{balance:.2f}",
                int(rng.choice([1, 2, 3, 4], p=[0.5, 0.44, 0.05, 0.01])),
                int(rng.random() < 0.7),
                int(rng.random() < 0.5),
                geography,
            ]
        )
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)
    writer.writerows(rows)
    return buffer.getvalue()
