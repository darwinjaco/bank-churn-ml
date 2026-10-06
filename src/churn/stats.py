"""Funciones estadísticas puras del protocolo preregistrado (especificación 003)."""

from __future__ import annotations

from math import comb, prod

import numpy as np
from scipy.stats import chi2_contingency, fisher_exact
from sklearn.metrics import roc_auc_score
from statsmodels.stats.contingency_tables import Table2x2
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import confint_proportions_2indep, proportion_confint


def wilson_ci(k: int, n: int) -> tuple[float, float]:
    """IC de Wilson bilateral del 95 % para una proporción binomial."""
    if n <= 0 or not 0 <= k <= n:
        raise ValueError("Se requiere n > 0 y 0 <= k <= n.")
    low, high = proportion_confint(k, n, alpha=0.05, method="wilson")
    return float(low), float(high)


def risk_difference(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float, float]:
    """Diferencia p1 - p2 e IC Newcombe método 10, bilateral del 95 %."""
    wilson_ci(k1, n1)
    wilson_ci(k2, n2)
    low, high = confint_proportions_2indep(
        k1, n1, k2, n2, method="newcomb", compare="diff", alpha=0.05
    )
    return float(k1 / n1 - k2 / n2), float(low), float(high)


def _table(table, *, two_by_two: bool = False) -> np.ndarray:
    values = np.asarray(table, dtype=float)
    if values.ndim != 2 or min(values.shape) < 2:
        raise ValueError("Se requiere una tabla de al menos 2 por 2.")
    if two_by_two and values.shape != (2, 2):
        raise ValueError("El odds ratio requiere una tabla 2 por 2.")
    if not np.isfinite(values).all() or (values < 0).any() or values.sum() == 0:
        raise ValueError("Las frecuencias deben ser finitas, no negativas y sumar más de cero.")
    return values


def odds_ratio(table) -> tuple[float, float, float]:
    """OR ad/bc e IC de Woolf del 95 %, sin corrección de continuidad."""
    values = _table(table, two_by_two=True)
    if (values == 0).any():
        raise ValueError("El IC de Woolf no está definido con celdas cero.")
    estimate = Table2x2(values, shift_zeros=False)
    low, high = estimate.oddsratio_confint(alpha=0.05, method="normal")
    return float(estimate.oddsratio), float(low), float(high)


def cramers_v(table) -> float:
    """V de Cramér a partir de Pearson sin corrección de Yates."""
    values = _table(table)
    statistic = chi2_contingency(values, correction=False).statistic
    return float(np.sqrt(statistic / (values.sum() * (min(values.shape) - 1))))


def _integer_table(table) -> np.ndarray:
    values = _table(table)
    if values.shape[1] != 2 or (values != np.floor(values)).any():
        raise ValueError("Se requieren dos columnas y frecuencias enteras no negativas.")
    return values


def freeman_halton(table) -> float:
    """P bilateral exacto por enumeración completa con marginales fijos (v1.1)."""
    values = _integer_table(table)
    rows = [int(total) for total in values.sum(axis=1)]
    first_column = int(values[:, 0].sum())
    denominator = comb(sum(rows), first_column)
    observed_weight = prod(
        comb(total, int(value)) for total, value in zip(rows, values[:, 0], strict=True)
    )

    def weights(row: int, remaining: int, weight: int):
        if row == len(rows) - 1:
            if 0 <= remaining <= rows[row]:
                yield weight * comb(rows[row], remaining)
            return
        lower = max(0, remaining - sum(rows[row + 1 :]))
        upper = min(rows[row], remaining)
        for count in range(lower, upper + 1):
            yield from weights(row + 1, remaining - count, weight * comb(rows[row], count))

    # El denominador es común. Comparar enteros evita subdesbordamientos y redondeo.
    # 10_000_001 / 10_000_000 equivale exactamente a la tolerancia relativa 1 + 1e-7.
    extreme_weight = sum(
        weight
        for weight in weights(0, first_column, 1)
        if weight * 10_000_000 <= observed_weight * 10_000_001
    )
    return extreme_weight / denominator


def independence_test(table) -> tuple[float, str]:
    """Selecciona Pearson, Fisher 2x2 o Freeman-Halton según las esperadas."""
    values = _integer_table(table)
    expected = np.outer(values.sum(axis=1), values.sum(axis=0)) / values.sum()
    if (expected >= 5).all():
        return float(chi2_contingency(values, correction=False).pvalue), "chi2_pearson"
    if values.shape == (2, 2):
        return float(fisher_exact(values, alternative="two-sided").pvalue), "fisher_exact"
    return freeman_halton(values), "freeman_halton"


def holm(pvalues) -> np.ndarray:
    """Ajuste Holm, conservando el orden de entrada."""
    values = np.asarray(pvalues, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
        raise ValueError("Los p-valores deben ser un vector finito entre 0 y 1.")
    if values.size == 0:
        return values.copy()
    return multipletests(values, method="holm")[1]


def auc_bootstrap(score, y, n_boot: int = 2000, seed: int = 42) -> tuple[float, float, float]:
    """AUC e IC percentil del 95 % con remuestreo pareado de observaciones."""
    scores, labels = np.asarray(score, dtype=float), np.asarray(y)
    if scores.ndim != 1 or labels.ndim != 1 or scores.shape != labels.shape:
        raise ValueError("Score y objetivo deben ser vectores del mismo tamaño.")
    if not np.isfinite(scores).all() or set(np.unique(labels)) != {0, 1} or n_boot < 1:
        raise ValueError("Se requieren scores finitos, ambas clases binarias y réplicas positivas.")
    rng = np.random.default_rng(seed)
    estimates = []
    while len(estimates) < n_boot:
        indices = rng.integers(0, len(labels), size=len(labels))
        sampled_y = labels[indices]
        if np.unique(sampled_y).size == 2:
            estimates.append(roc_auc_score(sampled_y, scores[indices]))
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(roc_auc_score(labels, scores)), float(low), float(high)
