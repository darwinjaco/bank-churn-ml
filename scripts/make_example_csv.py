"""Genera examples/clientes_ejemplo.csv: 20 clientes SINTÉTICOS (spec 006 §5).

Ninguna fila procede del CSV real: los valores se generan con semilla fija dentro de los
rangos del contrato de datos (spec 001). Uso: python scripts/make_example_csv.py
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "examples" / "clientes_ejemplo.csv"
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
    """Contenido CSV determinista; identificadores ficticios EJ-01, EJ-02..."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        geography = str(rng.choice(["France", "Germany", "Spain"], p=[0.5, 0.25, 0.25]))
        # Como en los datos (EDA, H5): ningún cliente de Alemania tiene saldo cero.
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


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(generate(), encoding="utf-8")
    print(f"{OUTPUT.relative_to(ROOT)}: {N_CUSTOMERS} clientes sintéticos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
