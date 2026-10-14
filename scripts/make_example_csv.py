"""Genera examples/clientes_ejemplo.csv: 20 clientes SINTÉTICOS (spec 006 §5).

Ninguna fila procede del CSV real: los valores se generan con semilla fija dentro de los
rangos del contrato de datos (spec 001). Uso: python scripts/make_example_csv.py
"""

from __future__ import annotations

from pathlib import Path

from churn.examples import COLUMNS as COLUMNS
from churn.examples import N_CUSTOMERS as N_CUSTOMERS
from churn.examples import SEED as SEED
from churn.examples import generate as generate

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "examples" / "clientes_ejemplo.csv"


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(generate(), encoding="utf-8")
    print(f"{OUTPUT.relative_to(ROOT)}: {N_CUSTOMERS} clientes sintéticos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
