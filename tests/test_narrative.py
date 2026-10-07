"""LLM opcional: plantilla sin clave o con fallo; datos enviados sin identificadores."""

import json
from types import SimpleNamespace

import pytest

from churn import narrative

CUSTOMER = {
    "CreditScore": 600,
    "Age": 52,
    "Tenure": 3,
    "Balance": 120000.0,
    "NumOfProducts": 1,
    "HasCrCard": 1,
    "IsActiveMember": 0,
    "Geography": "Germany",
    "CustomerId": 15600000,
    "Surname": "Pérez",
    "Gender": "Female",
}
PREDICTION = {
    "churn_probability": 0.62,
    "contact": True,
    "expected_benefit_eur": 136.0,
    "threshold": 1 / 6,
    "top_reasons": [{"feature": "Age", "direction": "aumenta el riesgo", "shap": 0.2}],
}


class FakeClient:
    def __init__(self, content=None, error=None):
        self.content, self.error, self.sent = content, error, None
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.sent = kwargs
        if self.error:
            raise self.error
        message = SimpleNamespace(content=self.content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("LLM_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("LLM_MODEL", "modelo-de-prueba")


def test_template_without_configuration(monkeypatch):
    for name in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    result = narrative.explain(CUSTOMER, PREDICTION)
    assert result["source"] == "template" and "62%" in result["text"]
    assert "Se recomienda contactarlo" in result["text"] and "Age" in result["text"]


def test_llm_response_and_no_identifiers_sent(configured):
    fake = FakeClient("Recomendación generada.")
    result = narrative.explain(CUSTOMER, PREDICTION, client_factory=lambda url, key: fake)
    assert result == {
        "text": "Recomendación generada.",
        "source": "llm",
        "model": "modelo-de-prueba",
    }
    payload = json.loads(fake.sent["messages"][1]["content"])
    sent = json.dumps(payload, ensure_ascii=False)
    for forbidden in ("CustomerId", "Surname", "Gender", "Pérez", "15600000"):
        assert forbidden not in sent
    assert payload["cliente"]["Age"] == 52 and fake.sent["model"] == "modelo-de-prueba"


@pytest.mark.parametrize("fake", [FakeClient(error=TimeoutError()), FakeClient(content="  ")])
def test_failures_fall_back_to_template(configured, fake):
    result = narrative.explain(CUSTOMER, PREDICTION, client_factory=lambda url, key: fake)
    assert result["source"] == "template" and result["text"].startswith("Probabilidad estimada")


def test_no_contact_template_and_no_reasons():
    facts = narrative.build_facts(CUSTOMER, {**PREDICTION, "contact": False, "top_reasons": []})
    text = narrative.template_text(facts)
    assert "No se recomienda" in text and "Factores" not in text
