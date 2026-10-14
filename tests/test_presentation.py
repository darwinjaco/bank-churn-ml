"""Regresión de unidades, límites e integridad de los datos mostrados (spec 005 v1.3)."""

import json

import pandas as pd
import pytest

from churn import presentation as visual
from churn import ui
from churn.config import PROJECT_ROOT


def test_spanish_numbers_and_feature_labels():
    assert visual.number(1234.56, 2) == "1.234,56"
    assert visual.number(-0.025 * 100, 1, signed=True) == "-2,5"
    assert visual.percent(1 / 6) == "16,7 %"
    assert visual.feature_label("Geography=Germany") == "País: Alemania"
    assert visual.feature_label("unknown") == "unknown"


def test_risk_threshold_and_shap_use_different_scales():
    risk = visual.risk_chart(0.947, 1 / 6)
    assert risk["data"]["values"][0]["risk"] == pytest.approx(94.7)
    assert risk["data"]["values"][0]["threshold"] == pytest.approx(100 / 6)
    prediction = {
        "top_reasons": [
            {"feature": "Age", "shap": 0.23, "direction": "aumenta el riesgo"},
            {"feature": "IsActiveMember", "shap": -0.08, "direction": "reduce el riesgo"},
        ]
    }
    rows = visual.reason_data(prediction)
    assert [row["contribution_pp"] for row in rows] == pytest.approx([23, -8])
    assert rows[1]["label"] == "-8,0 pp"
    assert "sin calibrar" in visual.reasons_chart(prediction)["encoding"]["x"]["title"]


def test_histogram_keeps_extreme_probabilities_and_api_decisions():
    predictions = [{"churn_probability": p, "contact": p > 1 / 6} for p in [0, 0.1, 1 / 6, 0.9, 1]]
    bins = visual.probability_bins(predictions)
    assert sum(row["customers"] for row in bins) == 5
    assert [row["customers"] for row in bins] == [1, 2, 0, 0, 0, 0, 0, 0, 0, 2]
    assert visual.decision_counts(predictions) == [
        {"decision": "Contactar", "customers": 2},
        {"decision": "No contactar", "customers": 3},
    ]
    assert visual.histogram_chart(predictions, 1 / 6)["layer"][1]["encoding"]["x"][
        "datum"
    ] == pytest.approx(100 / 6)
    assert visual.decisions_chart(predictions)["data"]["values"] == visual.decision_counts(
        predictions
    )


def test_final_policies_are_frozen_aggregates_and_absences_are_not_fabricated():
    final = json.loads((PROJECT_ROOT / "reports" / "final_test.json").read_text("utf-8"))
    info = {"policies": final["decision"]["policies"]}
    rows = visual.policy_data(info)
    assert [row["benefit_eur"] for row in rows] == [61600, 22100, 0]
    assert [row["contacted"] for row in rows] == [634, 2000, 0]
    assert len(visual.policies_chart(info)["data"]["values"]) == 3
    assert visual.policy_data({}) == []
    assert visual.policy_data({"policies": {"model": {"benefit_eur": 1}}}) == []


def test_monitoring_keeps_report_limits_and_percentage_points():
    report = json.loads((PROJECT_ROOT / "reports" / "monitoring.json").read_text("utf-8"))
    rows = visual.calibration_data(report)
    assert rows[-1]["gap_pp"] == pytest.approx(
        report["scenarios"]["S4"]["labeled"]["calibration_gap"] * 100
    )
    psi = visual.psi_chart(report["scenarios"]["S3"], {"stable_below": 0.2, "alert_above": 0.4})
    assert [layer["encoding"]["x"]["datum"] for layer in psi["layer"][1:]] == [0.2, 0.4]
    assert len(psi["data"]["values"]) == 9
    report["config"]["degradation"]["calibration_tolerance"] = 0.05
    band = visual.calibration_chart(report)["layer"][0]["encoding"]
    assert band == {"y": {"datum": -5.0}, "y2": {"datum": 5.0}}
    json.dumps(psi, allow_nan=False)


def test_batch_identity_uses_only_normalized_contract_and_detects_change():
    row = {
        "CreditScore": 600,
        "Age": 52,
        "Tenure": 3,
        "Balance": 120000.0,
        "NumOfProducts": 1,
        "HasCrCard": 1,
        "IsActiveMember": 0,
        "Geography": "Germany",
    }
    clean = ui.prepare_batch(pd.DataFrame([row]))
    extras = ui.prepare_batch(pd.DataFrame([{**row, "Gender": "Female", "CustomerId": "privado"}]))
    assert visual.batch_identity(clean) == visual.batch_identity(extras)
    changed = [{**row, "Age": 25}]
    assert visual.batch_identity(clean) != visual.batch_identity(changed)
