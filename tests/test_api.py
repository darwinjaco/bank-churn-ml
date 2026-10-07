"""API con un modelo sintético pequeño (sin artefacto real ni red)."""

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from churn import api
from churn.calibration import CalibratedModel, SigmoidCalibrator, oof_predictions
from churn.config import FEATURE_SETS, TARGET
from churn.pipeline import build_pipeline

METADATA = {
    "model_family": "rf",
    "git_commit": "a" * 40,
    "input_columns": [c for c in FEATURE_SETS["tree"] if c != "EstimatedSalary"],
    "excluded_columns": ["EstimatedSalary"],
    "calibrator": "sigmoid",
    "threshold": 1 / 6,
    "assumptions": {
        "customer_value_eur": 1000.0,
        "contact_cost_eur": 50.0,
        "retention_success_rate": 0.3,
    },
    "decision_rule": "p > t*",
    "final_test_evaluation": "completada",
}
CUSTOMER = {
    "CreditScore": 600,
    "Age": 52,
    "Tenure": 3,
    "Balance": 120000.0,
    "NumOfProducts": 1,
    "HasCrCard": 1,
    "IsActiveMember": 0,
    "Geography": "Germany",
}


@pytest.fixture(scope="module")
def model():

    rng = np.random.default_rng(0)
    n = 300
    df = pd.DataFrame(
        {
            "CreditScore": rng.integers(350, 851, n),
            "Geography": rng.choice(["France", "Germany", "Spain"], n),
            "Age": rng.integers(18, 93, n),
            "Tenure": rng.integers(0, 11, n),
            "Balance": np.where(rng.random(n) < 0.35, 0.0, rng.uniform(1e4, 2.5e5, n)),
            "NumOfProducts": rng.choice([1, 2, 3, 4], n, p=[0.5, 0.42, 0.06, 0.02]),
            "HasCrCard": rng.integers(0, 2, n),
            "IsActiveMember": rng.integers(0, 2, n),
            "EstimatedSalary": rng.uniform(1e3, 2e5, n),
        }
    )
    y = pd.Series((rng.random(n) < 0.15 + 0.3 * (df["Age"] > 45)).astype(int), name=TARGET)
    columns = METADATA["input_columns"]
    pipeline = build_pipeline(
        "rf", "tree", exclude=("EstimatedSalary",), params={"n_estimators": 20, "max_depth": 4}
    )
    oof = oof_predictions(pipeline, df[columns], y)
    pipeline.fit(df[columns], y)
    return CalibratedModel(pipeline, SigmoidCalibrator().fit(oof, y), columns)


@pytest.fixture
def client(model):
    final = {
        "metrics": {"ap": 0.7},
        "decision": {"policies": {"model": {"benefit_eur": 1.0}}},
        "n": 2000,
    }
    service = api.Service(model, METADATA, "b" * 64, final)
    with TestClient(api.create_app(lambda: service)) as test_client:
        yield test_client


def test_health_and_model(client):
    health = client.get("/health").json()
    assert health == {"status": "ok", "artifact_sha256": "b" * 64, "model_commit": "a" * 40}
    info = client.get("/model").json()
    assert info["threshold"] == pytest.approx(1 / 6) and info["final_test"]["n"] == 2000


def test_predict_matches_model_and_rule(client, model):
    body = client.post("/predict", json=CUSTOMER).json()
    expected = model.predict_proba(pd.DataFrame([CUSTOMER]))[0]
    assert body["churn_probability"] == pytest.approx(expected)
    assert body["contact"] == (expected > 1 / 6)
    assert body["expected_benefit_eur"] == pytest.approx(expected * 300 - 50)
    assert len(body["top_reasons"]) == 3
    assert all(
        r["direction"] in {"aumenta el riesgo", "reduce el riesgo"} for r in body["top_reasons"]
    )


def test_salary_is_accepted_and_ignored(client):
    with_salary = client.post("/predict", json={**CUSTOMER, "EstimatedSalary": 5e4}).json()
    without = client.post("/predict", json=CUSTOMER).json()
    assert with_salary["churn_probability"] == pytest.approx(without["churn_probability"])


@pytest.mark.parametrize(
    "change",
    [
        {"Age": 12},
        {"CreditScore": 1000},
        {"Balance": -1},
        {"NumOfProducts": 5},
        {"HasCrCard": 2},
        {"Geography": "Italy"},
        {"Gender": "Female"},
        {"CustomerId": 15600000},
    ],
)
def test_invalid_input_returns_422(client, change):
    assert client.post("/predict", json={**CUSTOMER, **change}).status_code == 422


def test_missing_field_returns_422(client):
    payload = dict(CUSTOMER)
    payload.pop("Age")
    assert client.post("/predict", json=payload).status_code == 422


def test_batch_summary_and_limits(client, model):
    customers = [CUSTOMER, {**CUSTOMER, "Age": 25, "IsActiveMember": 1, "NumOfProducts": 2}]
    body = client.post("/predict/batch", json={"customers": customers}).json()
    probabilities = model.predict_proba(pd.DataFrame(customers))
    assert [p["churn_probability"] for p in body["predictions"]] == pytest.approx(probabilities)
    contacted = probabilities > 1 / 6
    assert body["summary"]["contacted"] == int(contacted.sum())
    assert body["summary"]["expected_benefit_eur"] == pytest.approx(
        float((probabilities[contacted] * 300 - 50).sum())
    )
    assert client.post("/predict/batch", json={"customers": []}).status_code == 422
    too_many = {"customers": [CUSTOMER] * (api.MAX_BATCH + 1)}
    assert client.post("/predict/batch", json=too_many).status_code == 422


def test_load_service_reads_metadata_and_final(model, monkeypatch, tmp_path):
    import json

    import churn.artifact as artifact_module

    (tmp_path / "meta.json").write_text(json.dumps(METADATA), encoding="utf-8")
    monkeypatch.setattr(api, "METADATA_FILE", tmp_path / "meta.json")
    monkeypatch.setattr(api, "FINAL_FILE", tmp_path / "missing.json")
    monkeypatch.setattr(artifact_module, "load_model", lambda: model)
    service = api.load_service()
    assert service.final_test is None and service.artifact_sha256 == artifact_module.MODEL_SHA256
    assert service.threshold == pytest.approx(1 / 6)


def test_explain_endpoint_uses_template_without_key(client, monkeypatch):
    for name in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    body = client.post("/explain", json=CUSTOMER).json()
    assert body["source"] == "template" and body["prediction"]["top_reasons"]
    assert client.post("/explain", json={**CUSTOMER, "Gender": "Male"}).status_code == 422


@pytest.mark.parametrize(
    "change",
    [{"Balance": float("nan")}, {"Balance": float("inf")}, {"EstimatedSalary": float("nan")}],
)
def test_non_finite_numbers_return_422_not_500(client, change):
    import json

    payload = json.dumps({**CUSTOMER, **change})  # Python serializa NaN/Infinity sin error.
    headers = {"content-type": "application/json"}
    response = client.post("/predict", content=payload, headers=headers)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] in change
    batch = json.dumps({"customers": [{**CUSTOMER, **change}]})
    assert client.post("/predict/batch", content=batch, headers=headers).status_code == 422


def test_shap_explainer_is_created_once(client):
    service = client.app.state.service
    client.post("/predict", json=CUSTOMER)
    first = service.explainer
    client.post("/predict", json=CUSTOMER)
    assert service.explainer is first


def test_monitoring_endpoint(model):
    service = api.Service(model, METADATA, "b" * 64, None, {"expectations": {"E1": {"met": True}}})
    with TestClient(api.create_app(lambda: service)) as test_client:
        assert test_client.get("/monitoring").json()["expectations"]["E1"]["met"]
    empty = api.Service(model, METADATA, "b" * 64)
    with TestClient(api.create_app(lambda: empty)) as test_client:
        assert test_client.get("/monitoring").status_code == 404
