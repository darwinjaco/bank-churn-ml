"""Regresión de navegación, privacidad y estados del dashboard (spec 005 v1.3)."""

import copy
import sys
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from churn import presentation, ui

TEXT = "![imagen](https://example.invalid/tracker) [enlace](https://example.invalid)"
CUSTOMER = {
    "CreditScore": 600,
    "Age": 52,
    "Tenure": 3,
    "Balance": 120000.0,
    "NumOfProducts": 1,
    "Geography": "Germany",
    "HasCrCard": 1,
    "IsActiveMember": 0,
}
MODEL = {
    "threshold": 1 / 6,
    "assumptions": {
        "customer_value_eur": 1000,
        "contact_cost_eur": 50,
        "retention_success_rate": 0.3,
    },
    "model_family": "rf",
    "calibrator": "sigmoid",
    "input_columns": ui.CONTRACT_COLUMNS,
    "final_test": {
        "n": 2000,
        "metrics": {"ap": 0.705, "roc_auc": 0.862, "brier": 0.1017},
        "benefit_model_eur": 61600.0,
        "policies": {
            "model": {"contacted": 634, "benefit_eur": 61600.0},
            "everyone": {"contacted": 2000, "benefit_eur": 22100.0},
            "nobody": {"contacted": 0, "benefit_eur": 0.0},
        },
    },
}


class FakeApi:
    def __init__(self):
        self.calls = {"model": 0, "monitoring": 0, "explain": 0, "batch": 0}
        self.probability = 0.947001474187885
        self.fail = False

    def model(self):
        self.calls["model"] += 1
        if self.fail:
            raise ui.ApiError("La API respondió 503")
        return copy.deepcopy(MODEL)

    def monitoring(self):
        self.calls["monitoring"] += 1
        return None

    def explain(self, customer):
        self.calls["explain"] += 1
        assert set(customer) == set(ui.CONTRACT_COLUMNS)
        if self.fail:
            raise ui.ApiError("La API respondió 429")
        return {
            "source": "llm",
            "text": TEXT,
            "prediction": {
                "churn_probability": self.probability,
                "contact": self.probability > 1 / 6,
                "expected_benefit_eur": self.probability * 300 - 50,
                "threshold": 1 / 6,
                "top_reasons": [
                    {"feature": "Age", "value": 52, "shap": 0.2, "direction": "aumenta el riesgo"}
                ],
            },
        }

    def batch(self, customers):
        self.calls["batch"] += 1
        assert all(set(row) == set(ui.CONTRACT_COLUMNS) for row in customers)
        return {
            "predictions": [
                {"churn_probability": 0.9, "contact": True, "expected_benefit_eur": 220.0},
                {"churn_probability": 1 / 6, "contact": False, "expected_benefit_eur": 0.0},
            ],
            "summary": {"n": 2, "contacted": 1, "expected_benefit_eur": 220.0},
        }


@pytest.fixture
def dashboard(monkeypatch):
    api = FakeApi()
    monkeypatch.setattr(ui, "ApiClient", lambda: api)
    original_main = sys.modules["__main__"]
    st.cache_resource.clear()
    try:
        app = AppTest.from_file(
            str(Path(__file__).parents[1] / "dashboard" / "app.py"), default_timeout=30
        )
        yield app, api
    finally:
        sys.modules["__main__"] = original_main
        st.cache_resource.clear()


def click(app, label):
    return next(button for button in app.button if button.label == label).click().run()


def test_dashboard_displays_llm_as_literal_text_and_preserves_result(dashboard):
    app, api = dashboard
    app.run()
    assert not app.exception and api.calls == {
        "model": 1,
        "monitoring": 0,
        "explain": 0,
        "batch": 0,
    }
    click(app, "Cargar ejemplo")
    click(app, "Analizar cliente")
    assert not app.exception
    assert app.text[0].value == TEXT
    assert app.metric[0].value == "94,7 %" and app.metric[1].value == "Contactar"
    assert not any(TEXT in element.value for element in app.markdown)
    app.radio(key="view").set_value("Modelo").run()
    assert not app.exception and app.metric[0].value == "0,705"
    app.radio(key="view").set_value("Cliente").run()
    assert not app.exception and app.metric[1].value == "Contactar"
    assert api.calls["explain"] == 1 and api.calls["model"] == 1


def test_dashboard_respects_strict_threshold_and_recovers_error(dashboard):
    app, api = dashboard
    api.probability = 1 / 6
    app.run()
    click(app, "Analizar cliente")
    assert not app.exception and app.metric[1].value == "No contactar"
    api.fail = True
    click(app, "Analizar cliente")
    assert not app.exception and app.error and not app.metric
    api.fail = False
    click(app, "Analizar cliente")
    assert not app.exception and app.metric[1].value == "No contactar"


def test_batch_requires_action_and_read_interactions_do_not_predict_again(dashboard):
    app, api = dashboard
    customers = [CUSTOMER, {**CUSTOMER, "Age": 25}]
    app.session_state["batch_payload"] = {
        "customers": customers,
        "identity": presentation.batch_identity(customers),
    }
    app.run()
    app.radio(key="view").set_value("Lote").run()
    assert not app.exception and api.calls["batch"] == 0 and not app.metric
    click(app, "Procesar lote")
    assert not app.exception and api.calls["batch"] == 1 and app.metric[1].value == "1"
    app.checkbox(key="only_contacts").check().run()
    assert not app.exception and api.calls["batch"] == 1
    app.radio(key="view").set_value("Modelo").run()
    app.radio(key="view").set_value("Lote").run()
    assert not app.exception and api.calls["batch"] == 1 and app.metric[0].value == "2"
    click(app, "Vaciar lote")
    assert not app.exception and not app.metric and api.calls["batch"] == 1


def test_missing_monitoring_is_lazy_and_can_be_retried(dashboard):
    app, api = dashboard
    app.run()
    assert api.calls["monitoring"] == 0
    app.radio(key="view").set_value("Monitoreo").run()
    assert not app.exception and app.info and api.calls["monitoring"] == 1
    click(app, "Reintentar informe")
    assert not app.exception and api.calls["monitoring"] == 2


def test_initial_connection_failure_can_be_retried(dashboard):
    app, api = dashboard
    api.fail = True
    app.run()
    assert not app.exception and app.error
    api.fail = False
    click(app, "Reintentar conexión")
    assert not app.exception and len(app.radio) == 1 and api.calls["model"] == 2
