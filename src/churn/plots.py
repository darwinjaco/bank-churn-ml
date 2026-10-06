"""Seis figuras de EDA; los efectos e intervalos proceden de hypotheses.json."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from churn.config import AGE_LABELS, PROJECT_ROOT, has_balance
from churn.hypotheses import HYPOTHESES_FILE
from churn.split import load_exploration

FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    if path.stat().st_size >= 200_000:
        raise ValueError(f"La figura supera el límite de 200 KB: {path.name}")
    return path


def _rates_plot(rates, levels, labels, title, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6, 4))
    values = [rates[level]["rate"] for level in levels]
    errors = [
        [rates[level]["rate"] - rates[level]["ic_low"] for level in levels],
        [rates[level]["ic_high"] - rates[level]["rate"] for level in levels],
    ]
    ax.bar(labels, values, yerr=errors, capsize=5, color="#287a9e")
    ax.set(title=title, ylabel="Tasa de abandono (IC 95 % Wilson)", ylim=(0, 1))
    return _save(fig, path)


def generate_figures(df: pd.DataFrame, results: list[dict], out_dir: Path) -> list[Path]:
    """Dibuja resultados ya calculados y distribuciones descriptivas del EDA."""
    indexed = {result["id"]: result for result in results}
    paths = [
        _rates_plot(
            indexed["H2"]["detalles"]["rates"],
            ("1", "2", "3-4"),
            ("1", "2", "3-4"),
            "Abandono por número de productos (H2)",
            out_dir / "churn_products.png",
        ),
        _rates_plot(
            indexed["H4"]["detalles"]["rates"],
            AGE_LABELS,
            AGE_LABELS,
            "Abandono por tramo de edad",
            out_dir / "churn_age.png",
        ),
    ]
    germany = indexed["H3"]["detalles"]
    estimates = [germany["or_crudo"], germany["or_ajustado"]]
    fig, ax = plt.subplots(figsize=(6, 4))
    values = [estimate["estimate"] for estimate in estimates]
    errors = [
        [value - estimate["ic_low"] for value, estimate in zip(values, estimates, strict=True)],
        [estimate["ic_high"] - value for value, estimate in zip(values, estimates, strict=True)],
    ]
    ax.errorbar(values, [0, 1], xerr=errors, fmt="o", capsize=5)
    ax.axvline(1, color="gray", linestyle="--")
    ax.set(
        yticks=[0, 1],
        yticklabels=["Crudo", "Ajustado por saldo"],
        xlabel="Odds ratio (IC 95 %)",
        title="Alemania frente a Francia y España",
    )
    paths.append(_save(fig, out_dir / "germany_or.png"))

    rates = indexed["H5"]["detalles"]["rates"]
    fig, axes = plt.subplots(1, 2, figsize=(8, 4))
    axes[0].bar(["Saldo cero", "Saldo positivo"], [rates["0"]["n"], rates["1"]["n"]])
    axes[0].set(title="Masa puntual en cero", ylabel="Clientes")
    axes[1].hist(df.loc[has_balance(df["Balance"]) == 1, "Balance"], bins=40)
    axes[1].set(title="Distribución del saldo positivo", xlabel="Balance", ylabel="Clientes")
    paths.append(_save(fig, out_dir / "balance_distribution.png"))

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(df["EstimatedSalary"], bins=40, color="#287a9e")
    ax.set(title="Distribución de EstimatedSalary", xlabel="EstimatedSalary", ylabel="Clientes")
    paths.append(_save(fig, out_dir / "salary_distribution.png"))
    paths.append(
        _rates_plot(
            indexed["H1"]["detalles"]["rates"],
            ("0", "1"),
            ("Inactivo", "Activo"),
            "Abandono por actividad",
            out_dir / "churn_activity.png",
        )
    )
    return paths


def main() -> int:
    results = json.loads(HYPOTHESES_FILE.read_text(encoding="utf-8"))
    for path in generate_figures(load_exploration(), results, FIGURES_DIR):
        print(f"{path.name}: {path.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
