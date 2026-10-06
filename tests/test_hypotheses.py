"""Efectos sintéticos, protocolo preregistrado y aislamiento de la exploración."""

import ast
import json
from dataclasses import asdict
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from scipy.special import expit

from churn import hypotheses as h
from churn.config import AUC_BOOTSTRAP_REPLICATES, AUDIT_COLUMNS, RANDOM_SEED
from churn.stats import holm


@pytest.fixture
def synthetic():
    rng = np.random.default_rng(42)
    n = 4_000
    return pd.DataFrame(
        {
            "IsActiveMember": rng.integers(0, 2, n),
            "NumOfProducts": rng.choice([1, 2, 3, 4], n, p=[0.49, 0.46, 0.04, 0.01]),
            "Geography": rng.choice(["France", "Germany", "Spain"], n),
            "Balance": np.where(rng.random(n) < 0.36, 0.0, rng.uniform(1e4, 2e5, n)),
            "Age": rng.integers(18, 93, n),
            "EstimatedSalary": rng.uniform(1e3, 2e5, n),
            "Exited": (rng.random(n) < 0.2).astype(int),
        }
    )


@pytest.fixture
def quick_bootstrap(monkeypatch):
    # El protocolo de producción sigue siendo 2.000; aquí se prueba la orquestación.
    mock = Mock(return_value=(0.5, 0.48, 0.52))
    monkeypatch.setattr(h, "auc_bootstrap", mock)
    return mock


def test_seeded_h1_confirmed(synthetic, quick_bootstrap):
    rng = np.random.default_rng(43)
    probabilities = np.where(synthetic["IsActiveMember"] == 0, 0.45, 0.1)
    synthetic["Exited"] = (rng.random(len(synthetic)) < probabilities).astype(int)
    result = h.run_all(synthetic)[0]
    assert result.veredicto == "confirmada"
    assert result.ic_low > 0.05
    assert result.direccion_ok


def test_h1_without_effect_not_confirmed(synthetic, quick_bootstrap):
    synthetic["Exited"] = 0
    for active in (0, 1):
        positions = synthetic.index[synthetic["IsActiveMember"] == active]
        synthetic.loc[positions[: round(len(positions) * 0.2)], "Exited"] = 1
    assert h.run_all(synthetic)[0].veredicto == "no confirmada"


def test_h3_recovers_known_adjusted_coefficient():
    rng = np.random.default_rng(45)
    n = 12_000
    germany = rng.integers(0, 2, n)
    positive = rng.integers(0, 2, n)
    balance = positive * rng.uniform(1, 20, n)
    y = rng.random(n) < expit(-2 + 0.9 * germany + 0.4 * positive + 0.025 * balance)
    df = pd.DataFrame(
        {
            "Geography": np.where(germany, "Germany", "France"),
            "Balance": balance * 10000,
            "Exited": y.astype(int),
        }
    )
    result = h.test_h3(df)
    assert result.detalles["coeficientes"]["is_germany"] == pytest.approx(0.9, abs=0.15)
    assert result.ic_low < np.exp(0.9) < result.ic_high
    assert result.direccion_ok


def test_h4_recovers_known_quadratic_coefficient_and_peak():
    rng = np.random.default_rng(46)
    age = rng.integers(18, 93, 12_000)
    centered = age - age.mean()
    y = rng.random(len(age)) < expit(-0.5 + 0.025 * centered - 0.003 * centered**2)
    result = h.test_h4(pd.DataFrame({"Age": age, "Exited": y.astype(int)}))
    assert result.efecto == pytest.approx(-0.003, abs=0.0005)
    assert result.ic_high < 0
    assert result.detalles["peak_age"] == pytest.approx(age.mean() + 0.025 / 0.006, abs=3)
    assert result.detalles["practico_ok"]


def test_exact_selectors_are_reported_by_h1_and_h2():
    h1 = h.test_h1(
        pd.DataFrame({"IsActiveMember": [0] * 4 + [1] * 4, "Exited": [1, 1, 1, 0, 1, 0, 0, 0]})
    )
    assert h1.prueba_usada == "fisher_exact"
    df = pd.DataFrame(
        {
            "NumOfProducts": [1] * 10 + [2] * 6 + [3] * 4,
            "Exited": [1] * 8 + [0] * 2 + [1] + [0] * 5 + [0] * 4,
        }
    )
    h2 = h.test_h2(df)
    assert h2.prueba_usada == "freeman_halton"
    assert h2.p_raw == pytest.approx(0.008764, abs=1e-6)


def test_h6_equivalence_and_bootstrap_configuration(synthetic, quick_bootstrap):
    result = h.test_h6(synthetic)
    assert result.veredicto == "confirmada"
    assert result.p_raw is None and result.p_holm is None
    assert quick_bootstrap.call_args.kwargs == {
        "n_boot": AUC_BOOTSTRAP_REPLICATES,
        "seed": RANDOM_SEED,
    }
    quick_bootstrap.return_value = (0.54, 0.49, 0.57)
    assert h.test_h6(synthetic).veredicto == "no confirmada"


@pytest.mark.parametrize(
    ("direction", "practical", "pvalue", "expected"),
    [
        (True, True, 0.001, "confirmada"),
        (True, False, 0.001, "detectable sin relevancia"),
        (False, True, 0.001, "no confirmada"),
        (True, True, 0.04, "no confirmada"),
    ],
)
def test_holm_family_and_verdicts(monkeypatch, direction, practical, pvalue, expected):
    raw = [pvalue] * 5
    for index in range(1, 7):
        result = h.HypothesisResult(
            f"H{index}",
            "test",
            "test",
            1.0,
            pvalue if index < 6 else None,
            None,
            0.1,
            0.06,
            0.14,
            "referencia",
            direction,
            "no confirmada",
            {"practico_ok": practical},
        )
        monkeypatch.setattr(h, f"test_h{index}", lambda df, result=result: result)
    results = h.run_all(pd.DataFrame())
    assert [result.p_holm for result in results[:5]] == pytest.approx(holm(raw))
    assert results[0].veredicto == expected
    assert results[5].p_holm is None


def test_cli_serializes_all_required_fields(synthetic, quick_bootstrap, monkeypatch, tmp_path):
    monkeypatch.setattr(h, "load_exploration", lambda: synthetic)
    monkeypatch.setattr(h, "HYPOTHESES_FILE", tmp_path / "hypotheses.json")
    assert h.main() == 0
    results = json.loads(h.HYPOTHESES_FILE.read_text(encoding="utf-8"))
    assert len(results) == 6
    assert set(results[0]) == set(asdict(h.test_h1(synthetic)))
    assert results[5]["p_holm"] is None


def test_new_modules_do_not_access_audit_column_or_define_test_loader():
    root = Path(h.__file__).parent
    for name in ("split", "stats", "hypotheses", "plots"):
        path = root / f"{name}.py"
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8")
        assert all(column not in source for column in AUDIT_COLUMNS)
        tree = ast.parse(source)
        assert not any(
            isinstance(node, ast.FunctionDef) and node.name == "load_test"
            for node in ast.walk(tree)
        )
