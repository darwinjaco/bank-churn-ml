"""Regresión de la interfaz: respuesta LLM literal, sin llamar a servicios externos."""

import sys
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

from churn import ui


def test_dashboard_displays_llm_as_literal_text(monkeypatch):
    text = "![imagen](https://example.invalid/tracker) [enlace](https://example.invalid)"

    class FakeApi:
        def model(self):
            return {
                "threshold": 1 / 6,
                "assumptions": {
                    "customer_value_eur": 1000,
                    "contact_cost_eur": 50,
                    "retention_success_rate": 0.3,
                },
                "model_family": "rf",
                "calibrator": "sigmoid",
                "input_columns": ui.CONTRACT_COLUMNS,
            }

        def monitoring(self):
            return None

        def explain(self, customer):
            return {
                "source": "llm",
                "text": text,
                "prediction": {
                    "churn_probability": 0.947001474187885,
                    "contact": True,
                    "expected_benefit_eur": 234.1004422563655,
                    "top_reasons": [],
                },
            }

    monkeypatch.setattr(ui, "ApiClient", FakeApi)
    original_main = sys.modules["__main__"]
    st.cache_resource.clear()
    try:
        app = AppTest.from_file(str(Path(__file__).parents[1] / "dashboard" / "app.py"))
        app.run()
        assert not app.exception and len(app.tabs) == 4
        app.button[0].click().run()
        assert not app.exception
        assert app.text[0].value == text
        assert app.metric[0].value == "94.7%" and app.metric[1].value == "Contactar"
        assert not any(text in element.value for element in app.markdown)
    finally:
        # AppTest instala el script como __main__; spawn necesita el módulo original.
        sys.modules["__main__"] = original_main
        st.cache_resource.clear()
