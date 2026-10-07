"""Auditoría de errores, segmentos y E-01 con valores conocidos."""

import numpy as np
import pandas as pd
import pytest

from churn import audit


def test_rates_known_case_and_empty_denominators():
    y = np.array([1, 1, 0, 0])
    p = np.array([0.9, 0.1, 0.4, 0.2])
    contact = np.array([True, False, True, False])
    r = audit.rates(y, p, contact)
    assert r["recall"] == 0.5 and r["precision"] == 0.5 and r["contact_rate"] == 0.5
    assert r["calibration_gap"] == pytest.approx(0.4 - 0.5)
    assert r["missed_churn_share"] == 0.5
    empty = audit.rates(np.zeros(3), np.zeros(3), np.zeros(3, dtype=bool))
    assert empty["recall"] is None and empty["precision"] is None


def test_segments_errors_and_worst_missed(valid_df):
    rng = np.random.default_rng(0)
    p = rng.random(len(valid_df))
    contact = p > 0.5
    y = valid_df["Exited"].to_numpy()
    segments = audit.segment_columns(valid_df)
    assert set(segments.columns) == {
        "Geography",
        "tramo_edad",
        "productos",
        "IsActiveMember",
        "has_balance",
        "Gender",
    }
    assert set(segments["productos"]) <= {"1", "2", "3-4"}
    metrics = audit.segment_metrics(segments, y, p, contact)
    assert sum(v["n"] for v in metrics["Gender"].values()) == len(valid_df)
    worst = audit.worst_missed_segment(metrics)
    shares = [
        v["missed_churn_share"]
        for levels in metrics.values()
        for v in levels.values()
        if v["missed_churn_share"] is not None
    ]
    assert worst["missed_churn_share"] == max(shares)
    profiles = audit.error_profiles(valid_df, y, contact)
    assert sum(g["n"] for g in profiles.values()) == len(valid_df)
    assert "Gender" not in profiles["VP"]["means"]
    empty = audit.error_profiles(valid_df, y, np.zeros(len(valid_df), dtype=bool))
    assert empty["VP"] == {"n": 0, "means": None} and empty["FP"]["n"] == 0
    near = audit.near_threshold(y, p, 0.5, band=0.1)
    assert near["n"] == int((np.abs(p - 0.5) < 0.1).sum())


def test_alert_rule():
    assert audit.alert(0.06, 0.01, 0.11) is True
    assert audit.alert(-0.06, -0.10, -0.02) is True
    assert audit.alert(0.06, -0.01, 0.11) is False  # El IC incluye 0.
    assert audit.alert(0.03, 0.01, 0.05) is False  # Diferencia < 0,05.


def test_e01_bootstrap_detects_planted_gap_and_is_deterministic():
    rng = np.random.default_rng(1)
    n = 2000
    gender = np.where(rng.random(n) < 0.5, "Female", "Male")
    y = (rng.random(n) < 0.3).astype(int)
    p = rng.random(n)
    contact = np.where(gender == "Female", (y == 1) | (rng.random(n) < 0.1), rng.random(n) < 0.2)
    first = audit.e01_gender(y, p, contact, gender, n_boot=300)
    second = audit.e01_gender(y, p, contact, gender, n_boot=300)
    assert first == second
    recall = first["recall"]
    assert (
        recall["difference"] > 0.5 and recall["ci_low"] <= recall["difference"] <= recall["ci_high"]
    )
    assert recall["alert"] is True
    assert first["n"]["Female"] + first["n"]["Male"] == n
    no_gap = audit.e01_gender(y, p, rng.random(n) < 0.3, gender, n_boot=300)
    assert no_gap["contact_rate"]["alert"] is False
    assert isinstance(pd.Series(first["observed_rate"]).sum(), float)
