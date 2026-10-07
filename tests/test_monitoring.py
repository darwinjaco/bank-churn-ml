"""Monitoreo simulado (spec 006 §4): PSI, escenarios deterministas y sin partición de prueba."""

import inspect
import json
import math

import numpy as np
import pandas as pd
import pytest

from churn import monitoring, split
from churn.config import TARGET


def synthetic(n: int = 2_000, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(
        {
            "CustomerId": np.arange(n),
            "CreditScore": rng.integers(350, 851, n),
            "Geography": rng.choice(["France", "Germany", "Spain"], n, p=[0.5, 0.25, 0.25]),
            "Age": rng.integers(18, 93, n),
            "Tenure": rng.integers(0, 11, n),
            "Balance": np.where(rng.random(n) < 0.36, 0.0, rng.uniform(1e4, 2.5e5, n)),
            "NumOfProducts": rng.choice([1, 2, 3, 4], n, p=[0.5, 0.45, 0.04, 0.01]),
            "HasCrCard": rng.integers(0, 2, n),
            "IsActiveMember": rng.integers(0, 2, n),
            "EstimatedSalary": rng.uniform(1e3, 2e5, n),
        }
    )
    logit = (
        -5.0 + 0.06 * df["Age"] - 0.8 * df["IsActiveMember"] + 0.7 * df["Geography"].eq("Germany")
    )
    df[TARGET] = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    return df


class FakeModel:
    """Probabilidad = verdadera P(y|X) del generador sintético."""

    def predict_proba(self, x: pd.DataFrame) -> np.ndarray:
        logit = (
            -5.0 + 0.06 * x["Age"] - 0.8 * x["IsActiveMember"] + 0.7 * x["Geography"].eq("Germany")
        )
        return (1 / (1 + np.exp(-logit))).to_numpy()


def test_psi_zero_for_identical_distributions():
    values = np.random.default_rng(1).normal(size=1_000)
    assert monitoring.psi(values, values, "continuous") == pytest.approx(0.0)
    levels = ["a", "b", "c"] * 50
    assert monitoring.psi(levels, levels, "discrete") == pytest.approx(0.0)


def test_psi_hand_computed():
    expected = 0.2 * math.log(0.7 / 0.5) + (-0.2) * math.log(0.3 / 0.5)  # 0,16946
    assert monitoring.psi_from_proportions([0.5, 0.5], [0.7, 0.3]) == pytest.approx(expected)
    reference = ["a"] * 50 + ["b"] * 50
    current = ["a"] * 70 + ["b"] * 30
    assert monitoring.psi(reference, current, "discrete") == pytest.approx(expected)


def test_empty_bins_use_documented_epsilon():
    eps = monitoring.EPSILON
    expected = (0.1 - eps) * math.log(0.1 / eps) + (0.4 - 0.5) * math.log(0.4 / 0.5)
    value = monitoring.psi_from_proportions([0.5, 0.5, 0.0], [0.5, 0.4, 0.1])
    assert value == pytest.approx(expected)
    assert math.isfinite(monitoring.psi(["a"] * 10, ["b"] * 10, "discrete"))


def test_decile_edges_with_point_mass_and_right_closed_bins():
    reference = np.r_[np.zeros(40), np.arange(1, 61)]
    edges = monitoring.decile_edges(reference)
    assert len(edges) == len(np.unique(edges)) < 9 and edges[0] == 0.0
    proportions = monitoring.binned_proportions([0.0, edges[1], edges[1] + 0.5], edges)
    assert proportions[0] == pytest.approx(1 / 3)  # 0 cae en (-inf, 0]
    assert proportions[1] == pytest.approx(1 / 3)  # el borde cae en su intervalo izquierdo


def test_psi_levels_and_invalid_kind():
    assert [monitoring.psi_level(v) for v in (0.05, 0.10, 0.25, 0.26)] == [
        "estable",
        "moderado",
        "moderado",
        "alerta",
    ]
    with pytest.raises(ValueError, match="desconocido"):
        monitoring.psi([1], [1], "otro")


def test_scenarios_are_deterministic_and_hit_targets():
    validation = synthetic()
    first, second = monitoring.build_scenarios(validation), monitoring.build_scenarios(validation)
    for name in first:
        pd.testing.assert_frame_equal(first[name], second[name])
        assert len(first[name]) == len(validation)
    pd.testing.assert_frame_equal(first["S0"], validation.reset_index(drop=True))
    germany = validation["Geography"].eq("Germany").mean()
    assert first["S2"]["Geography"].eq("Germany").mean() == pytest.approx(2 * germany, abs=1e-3)
    assert first["S3"]["IsActiveMember"].eq(0).mean() == pytest.approx(0.70, abs=1e-3)
    assert first["S4"][TARGET].mean() == pytest.approx(0.35, abs=0.01)
    assert first["S1"]["Age"].mean() > validation["Age"].mean() + 3


def test_exact_composition_rejects_invalid_groups():
    frame = synthetic(100)
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError):
        monitoring.exact_composition(frame, np.ones(100, dtype=bool), 0.5, rng)
    with pytest.raises(ValueError):
        monitoring.exact_composition(frame, frame["HasCrCard"].eq(1), 1.0, rng)


def test_run_monitoring_detects_prevalence_shift_only_with_labels():
    data = synthetic(8_000, seed=3)
    training, validation = data.iloc[:6_000], data.iloc[6_000:]
    result = monitoring.run_monitoring(FakeModel(), training, validation)
    scenarios, expectations = result["scenarios"], result["expectations"]
    assert set(scenarios) == {"S0", "S1", "S2", "S3", "S4"}
    assert scenarios["S0"]["probability"]["psi"] == pytest.approx(0.0)
    assert scenarios["S0"]["degradation"]["brier_ratio"] == pytest.approx(1.0)
    assert expectations["E1"]["met"]
    assert scenarios["S1"]["variables"]["Age"]["psi"] > monitoring.PSI_ALERT
    assert scenarios["S2"]["variables"]["Geography"]["psi"] > 0.2
    assert expectations["E3"]["met"]  # PSI bajo, pero calibración fuera de ±3 pp
    for row in scenarios["S1"]["variables"].values():
        assert {"psi", "level", "method", "p_value", "p_holm", "significant"} <= set(row)
    text = monitoring.render_markdown(result)
    assert "E1" in text and "E4" in text and "| Age |" in text
    json.dumps(result, allow_nan=False, default=float)


def test_module_never_reads_test_partition():
    source = inspect.getsource(monitoring)
    for forbidden in ('"test"', "'test'", "load_test", "final_eval"):
        assert forbidden not in source


def test_load_partitions_excludes_test_rows(tmp_path, monkeypatch, valid_df):
    raw = tmp_path / "raw.csv"
    valid_df.to_csv(raw, index=False)
    positions = list(range(len(valid_df)))
    assignment = {"train": positions[:120], "validation": positions[120:160]}
    assignment["test"] = positions[160:]
    split_file = tmp_path / "split.json"
    split_file.write_text(json.dumps(assignment), encoding="utf-8")
    monkeypatch.setattr(split, "RAW_FILE", raw)
    monkeypatch.setattr(split, "SPLIT_FILE", split_file)
    training, validation = monitoring.load_partitions()
    test_ids = set(valid_df.iloc[160:]["CustomerId"])
    assert len(training) == 120 and len(validation) == 40
    assert not test_ids & (set(training["CustomerId"]) | set(validation["CustomerId"]))


def test_main_writes_reports(tmp_path, monkeypatch):
    data = synthetic(3_000, seed=5)
    monkeypatch.setattr(
        monitoring, "load_partitions", lambda: (data.iloc[:2_000], data.iloc[2_000:])
    )
    monkeypatch.setattr("churn.artifact.load_model", lambda: FakeModel())
    monkeypatch.setattr("churn.tracking.provenance", lambda: {"git_commit": "x"})
    for name, file in (
        ("MONITORING_FILE", "m.json"),
        ("MONITORING_MD", "m.md"),
        ("FIGURE_FILE", "m.png"),
    ):
        monkeypatch.setattr(monitoring, name, tmp_path / file)
    assert monitoring.main() == 0
    payload = json.loads((tmp_path / "m.json").read_text(encoding="utf-8"))
    assert payload["stage"] == "monitoring" and "expectations" in payload
    assert (tmp_path / "m.png").stat().st_size < 500_000
