"""Valores de referencia y límites del protocolo estadístico."""

import numpy as np
import pytest
from scipy.stats import norm

from churn.stats import auc_bootstrap, cramers_v, holm, odds_ratio, risk_difference, wilson_ci


@pytest.mark.parametrize(
    ("k", "n", "expected"), [(50, 100, [0.4038, 0.5962]), (0, 20, [0.0, 0.1611])]
)
def test_wilson_reference(k, n, expected):
    assert wilson_ci(k, n) == pytest.approx(expected, abs=1e-4)


@pytest.mark.parametrize(("k", "n"), [(0, 0), (-1, 10), (11, 10)])
def test_wilson_rejects_invalid_counts(k, n):
    with pytest.raises(ValueError):
        wilson_ci(k, n)


def test_risk_difference_newcombe_method_10():
    p1, p2 = 0.2, 0.1
    l1, u1 = wilson_ci(20, 100)
    l2, u2 = wilson_ci(10, 100)
    expected = (
        p1 - p2,
        p1 - p2 - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
        p1 - p2 + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2),
    )
    assert risk_difference(20, 100, 10, 100) == pytest.approx(expected, abs=1e-4)
    estimate, low, high = risk_difference(0, 20, 0, 20)
    assert estimate == 0
    assert low < 0 < high
    with pytest.raises(ValueError):
        risk_difference(0, 0, 1, 20)


def test_odds_ratio_woolf_reference():
    assert odds_ratio([[20, 80], [10, 90]]) == pytest.approx([2.25, 0.9943, 5.0915], abs=1e-4)


@pytest.mark.parametrize(
    "table",
    [[], [[1, 2, 3]], [[1, 2, 3], [4, 5, 6]], [[0, 80], [10, 90]], [[-1, 2], [3, 4]]],
)
def test_odds_ratio_invalid_or_zero_cells(table):
    with pytest.raises(ValueError):
        odds_ratio(table)


def test_cramers_v_reference_and_independence():
    assert cramers_v([[50, 0], [0, 50]]) == pytest.approx(1.0, abs=1e-4)
    assert cramers_v([[25, 25], [25, 25]]) == pytest.approx(0.0, abs=1e-4)
    with pytest.raises(ValueError):
        cramers_v([[0, 0], [0, 0]])


def test_holm_reference_order_and_empty():
    assert holm([0.01, 0.04, 0.03, 0.005]) == pytest.approx([0.03, 0.06, 0.06, 0.02], abs=1e-4)
    assert holm([]).size == 0
    with pytest.raises(ValueError):
        holm([0.1, 1.1])


def test_auc_bootstrap_known_auc_and_determinism():
    labels = np.tile([0, 1], 20)
    assert auc_bootstrap(labels, labels, n_boot=100) == (1.0, 1.0, 1.0)
    rng = np.random.default_rng(42)
    labels = np.tile([0, 1], 100)
    scores = rng.normal(size=len(labels)) + labels
    expected = norm.cdf(1 / np.sqrt(2))
    first = auc_bootstrap(scores, labels, n_boot=100)
    assert first == auc_bootstrap(scores, labels, n_boot=100)
    assert abs(first[0] - expected) < 0.1
    assert first[1] < first[0] < first[2]


@pytest.mark.parametrize(
    ("scores", "labels", "n_boot"),
    [([1, 2], [0], 10), ([1, 2], [0, 0], 10), ([0, 1], [0, 1], 0), ([np.nan, 1], [0, 1], 10)],
)
def test_auc_bootstrap_rejects_undefined_inputs(scores, labels, n_boot):
    with pytest.raises(ValueError):
        auc_bootstrap(scores, labels, n_boot=n_boot)
