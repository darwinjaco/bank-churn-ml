"""LLM opcional: plantilla sin clave, con fallo o sobre el límite; datos sin identificadores."""

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


@pytest.fixture(autouse=True)
def fresh_limiter(monkeypatch):
    narrative.LIMITER.reset()
    monkeypatch.delenv("LLM_MAX_CALLS_PER_HOUR", raising=False)
    yield
    narrative.LIMITER.reset()


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


class FakeClock:
    def __init__(self):
        self.now = 1_000.0

    def __call__(self):
        return self.now


def test_rate_limit_falls_back_to_template(configured, monkeypatch):
    monkeypatch.setenv("LLM_MAX_CALLS_PER_HOUR", "2")
    limiter = narrative.HourlyLimiter(clock=FakeClock())
    fake = FakeClient("Texto del LLM.")
    results = [
        narrative.explain(CUSTOMER, PREDICTION, lambda url, key: fake, limiter=limiter)
        for _ in range(3)
    ]
    assert [r["source"] for r in results] == ["llm", "llm", "template"]
    assert results[-1]["reason"] == narrative.RATE_LIMIT_REASON


def test_failed_attempts_also_count(configured, monkeypatch):
    monkeypatch.setenv("LLM_MAX_CALLS_PER_HOUR", "1")
    limiter = narrative.HourlyLimiter(clock=FakeClock())
    failing = FakeClient(error=TimeoutError())
    first = narrative.explain(CUSTOMER, PREDICTION, lambda url, key: failing, limiter=limiter)
    second = narrative.explain(CUSTOMER, PREDICTION, lambda url, key: failing, limiter=limiter)
    assert first["reason"] == "TimeoutError"
    assert second["reason"] == narrative.RATE_LIMIT_REASON


def test_window_slides_after_one_hour():
    clock = FakeClock()
    limiter = narrative.HourlyLimiter(clock=clock)
    assert limiter.try_acquire(2)  # t = 0 s
    clock.now += 600
    assert limiter.try_acquire(2)  # t = 600 s
    assert not limiter.try_acquire(2)
    clock.now += narrative.WINDOW_S - 600 - 1
    assert not limiter.try_acquire(2)  # t = 3.599 s: las dos siguen en la ventana
    clock.now += 1
    assert limiter.try_acquire(2)  # t = 3.600 s: sale la primera
    assert not limiter.try_acquire(2)


def test_zero_disables_llm(configured, monkeypatch):
    monkeypatch.setenv("LLM_MAX_CALLS_PER_HOUR", "0")
    fake = FakeClient("No debería llamarse.")
    result = narrative.explain(CUSTOMER, PREDICTION, lambda url, key: fake)
    assert result["source"] == "template" and fake.sent is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, 30), ("", 30), ("abc", 30), ("-5", 30), ("2.5", 30), (" 12 ", 12), ("0", 0)],
)
def test_max_calls_per_hour_parsing(monkeypatch, raw, expected):
    if raw is None:
        monkeypatch.delenv("LLM_MAX_CALLS_PER_HOUR", raising=False)
    else:
        monkeypatch.setenv("LLM_MAX_CALLS_PER_HOUR", raw)
    assert narrative.max_calls_per_hour() == expected
