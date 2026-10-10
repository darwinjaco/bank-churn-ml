"""Funciones puras del dashboard y cliente HTTP con transporte simulado."""

import csv
import io
import json

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
    with pytest.raises(ui.ApiError, match="500"):
        failing.health()


def test_api_errors_are_readable_and_monitoring_404():
    detail = [
        {"loc": ["body", "customers", 2, "Age"], "msg": "Input should be >= 18"},
        {"loc": ["body", "customers", 0, "Geography"], "msg": "Input should be 'France'"},
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/monitoring":
            return httpx.Response(404, json={"detail": "no"})
        return httpx.Response(422, json={"detail": detail})

    client = ui.ApiClient("http://x", httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(ui.ApiError) as error:
        client.batch([ROW])
    assert "fila 3, Age: Input should be >= 18" in str(error.value)
    assert "fila 1, Geography" in str(error.value)
    assert client.monitoring() is None
    many = [{"loc": ["body", "customers", i, "Age"], "msg": "x"} for i in range(8)]
    assert "3 errores más" in ui.describe_errors(many)
    assert ui.describe_errors("texto") == "texto"
    plain = ui.ApiClient(
        "http://x", httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(502)))
    )
    with pytest.raises(ui.ApiError, match="502"):
        plain.model()


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"Balance": None}, "celdas vacías en: Balance"),
        ({"Age": 52.7}, "Age debe contener enteros"),
        ({"CreditScore": "alto"}, "CreditScore debe ser numérica"),
    ],
)
def test_prepare_batch_rejects_bad_values(change, message):
    frame = pd.DataFrame([ROW, {**ROW, **change}])
    with pytest.raises(ValueError, match=message):
        ui.prepare_batch(frame)


def test_prepare_batch_accepts_float_encoded_integers():
    frame = pd.DataFrame([{**ROW, "Age": 52.0, "HasCrCard": 1.0}])
    assert ui.prepare_batch(frame) == [ROW]


def test_monitoring_tables_from_versioned_report():

    from churn.config import PROJECT_ROOT

    report = json.loads((PROJECT_ROOT / "reports" / "monitoring.json").read_text("utf-8"))
    psi = ui.psi_table(report)
    assert list(psi.columns) == ["S0", "S1", "S2", "S3", "S4"]
    assert "Probabilidad predicha" in psi.index and "Age" in psi.index
    metrics = ui.monitoring_metrics(report)
    assert metrics.loc["Alarma de PSI (> 0,25)", "S1"] in {"sí", "no"}
    assert all(isinstance(v, str) for v in metrics.to_numpy().ravel())  # serializable a Arrow
    import pyarrow as pa

    pa.Table.from_pandas(metrics)
    pa.Table.from_pandas(psi)
    rows = ui.expectation_rows(report)
    assert [row["Expectativa"][:2] for row in rows] == ["E1", "E2", "E3", "E4"]


def test_download_drops_identifiers_and_untrusted_columns():
    frame = pd.DataFrame([{**ROW, "CustomerId": "privado", "Gender": "privado", "nota": "=1+1"}])
    response = {
        "predictions": [{"churn_probability": 0.1, "contact": False, "expected_benefit_eur": -20.0}]
    }
    table = ui.results_table(frame, response)
    assert set(table.columns) == set(ui.CONTRACT_COLUMNS) | {
        "probabilidad_abandono",
        "contactar",
        "beneficio_esperado_eur",
    }
    exported = ui.results_csv(table)
    assert "privado" not in exported and "=1+1" not in exported
    assert pd.read_csv(io.StringIO(exported))["beneficio_esperado_eur"].iloc[0] == -20


@pytest.mark.parametrize("text", ["=1+1", "+1+1", "-1+1", "@SUM(1)", "\t =1", "\uff20SUM(1)"])
def test_csv_formula_text_is_neutralized_without_creating_new_cells(text):
    table = pd.DataFrame({"texto": [text + '",otra'], "numero": [-20.0]})
    rows = list(csv.reader(io.StringIO(ui.results_csv(table))))
    assert len(rows[1]) == 2
    assert rows[1][0].startswith("'")
    assert float(rows[1][1]) == -20


def test_csv_reader_is_bounded_and_discards_extra_columns():
    frame = pd.DataFrame([{**ROW, "Surname": "privado", "nota": "=1+1"}])
    data = frame.to_csv(index=False).encode()
    upload = io.BytesIO(data)
    parsed = ui.read_batch_csv(upload)
    assert ui.read_batch_csv(upload).equals(parsed)
    assert set(parsed.columns) == set(ui.CONTRACT_COLUMNS)
    assert ui.prepare_batch(parsed) == [ROW]
    oversized = io.BytesIO(b"x" * (ui.MAX_CSV_BYTES + 1))
    with pytest.raises(ValueError, match="1 MiB"):
        ui.read_batch_csv(oversized)
    assert oversized.tell() == ui.MAX_CSV_BYTES + 1
    many = pd.DataFrame([ROW] * (ui.MAX_BATCH + 1)).to_csv(index=False).encode()
    with pytest.raises(ValueError, match="1 y 1000"):
        ui.read_batch_csv(io.BytesIO(many))


@pytest.mark.parametrize("data", [b"", b"\xff", b"Age,Age\n52,52\n", b"Age\n"])
def test_csv_reader_rejects_invalid_or_duplicate_headers(data):
    with pytest.raises(ValueError):
        ui.read_batch_csv(io.BytesIO(data))


def test_prepare_batch_rejects_infinity_before_json_serialization():
    with pytest.raises(ValueError, match="finitos"):
        ui.prepare_batch(pd.DataFrame([{**ROW, "Balance": float("inf")}]))
