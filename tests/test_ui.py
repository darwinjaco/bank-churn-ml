"""Funciones puras del dashboard y cliente HTTP con transporte simulado."""

import httpx
import pandas as pd
import pytest

from churn import ui

ROW = {
    "CreditScore": 600,
    "Age": 52,
    "Tenure": 3,
    "Balance": 120000.0,
    "NumOfProducts": 1,
    "HasCrCard": 1,
    "IsActiveMember": 0,
    "Geography": "Germany",
}


def test_prepare_batch_drops_extra_columns_and_validates():
    frame = pd.DataFrame([{**ROW, "Gender": "Male", "CustomerId": 1, "EstimatedSalary": 1.0}])
    records = ui.prepare_batch(frame)
    assert records == [ROW]
    with pytest.raises(ValueError, match="Faltan columnas: Age"):
        ui.prepare_batch(frame.drop(columns="Age"))
    with pytest.raises(ValueError, match="entre 1"):
        ui.prepare_batch(frame.iloc[:0])
    with pytest.raises(ValueError, match="entre 1"):
        ui.prepare_batch(pd.concat([frame] * (ui.MAX_BATCH + 1)))


def test_results_table_sorted_and_labelled():
    frame = pd.DataFrame([ROW, {**ROW, "Age": 25}])
    response = {
        "predictions": [
            {"churn_probability": 0.1, "contact": False, "expected_benefit_eur": -20.0},
            {"churn_probability": 0.9, "contact": True, "expected_benefit_eur": 220.0},
        ]
    }
    table = ui.results_table(frame, response)
    assert table["probabilidad_abandono"].tolist() == [0.9, 0.1]
    assert table["contactar"].tolist() == ["sí", "no"] and table.loc[0, "Age"] == 25


def test_reason_rows_and_eur():
    rows = ui.reason_rows(
        {
            "top_reasons": [
                {"feature": "Age", "value": 52.0, "direction": "aumenta el riesgo", "shap": 0.234}
            ]
        }
    )
    assert rows == [
        {
            "Factor del modelo": "Age",
            "Valor": 52.0,
            "Efecto": "aumenta el riesgo",
            "Contribución (pp)": 23.4,
        }
    ]
    assert ui.eur(61600) == "61.600 €"


def test_api_client_with_mock_transport(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        routes = {
            ("GET", "/health"): {"status": "ok"},
            ("GET", "/model"): {"threshold": 0.1667},
            ("POST", "/explain"): {"source": "template"},
            ("POST", "/predict/batch"): {"summary": {"n": 1}},
        }
        return httpx.Response(200, json=routes[(request.method, request.url.path)])

    monkeypatch.setenv("API_URL", "http://api:8000/")
    client = ui.ApiClient(client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert client.base_url == "http://api:8000"
    assert client.health() == {"status": "ok"} and client.model()["threshold"] == 0.1667
    assert client.explain(ROW)["source"] == "template"
    assert client.batch([ROW])["summary"]["n"] == 1
    failing = ui.ApiClient(
        "http://x", httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    )
    with pytest.raises(httpx.HTTPStatusError):
        failing.health()
