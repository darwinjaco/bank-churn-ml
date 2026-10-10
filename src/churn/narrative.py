"""Explicación en lenguaje natural (spec 005 §6): LLM opcional con plantilla determinista.

El número de llamadas al LLM está limitado por hora (spec 006 §3).
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from collections import deque
from collections.abc import Callable
from pathlib import Path

from churn.config import PROJECT_ROOT
from churn.security import SQLiteHourlyLimiter

LLM_TIMEOUT_S = 10.0
DEFAULT_MAX_CALLS_PER_HOUR = 30
WINDOW_S = 3_600.0
RATE_LIMIT_REASON = "límite de llamadas por hora"
SYSTEM_PROMPT = (
    "Eres analista de retención de un banco. Redacta en español, en 2 o 3 frases, una "
    "recomendación para el equipo comercial a partir de los datos JSON. Usa solo esos datos; "
    "no inventes cifras. Presenta las razones como factores del modelo, no como causas, y no "
    "menciones datos personales distintos de los recibidos."
)


def build_facts(customer: dict, prediction: dict) -> dict:
    """Datos que puede ver el LLM: variables del contrato, probabilidad, decisión y razones."""
    allowed = {
        "CreditScore",
        "Age",
        "Tenure",
        "Balance",
        "NumOfProducts",
        "HasCrCard",
        "IsActiveMember",
        "Geography",
    }
    return {
        "cliente": {k: v for k, v in customer.items() if k in allowed},
        "probabilidad_abandono": round(prediction["churn_probability"], 3),
        "contactar": prediction["contact"],
        "beneficio_esperado_eur": round(prediction["expected_benefit_eur"], 2),
        "umbral": round(prediction["threshold"], 4),
        "razones": [
            {"variable": r["feature"], "efecto": r["direction"]}
            for r in prediction.get("top_reasons", [])
        ],
    }


def template_text(facts: dict) -> str:
    p = facts["probabilidad_abandono"]
    decision = "Se recomienda contactarlo" if facts["contactar"] else "No se recomienda contactarlo"
    reasons = ", ".join(f"{r['variable']} ({r['efecto']})" for r in facts["razones"])
    text = (
        f"Probabilidad estimada de abandono: {p:.0%}. {decision}: el beneficio esperado de la "
        f"campaña es {facts['beneficio_esperado_eur']:.2f} EUR (umbral {facts['umbral']:.3f})."
    )
    if reasons:
        text += f" Factores del modelo con más peso: {reasons}."
    return text


def llm_config() -> dict | None:
    """Configuración compatible con OpenAI (NVIDIA NIM, OpenRouter...). None si falta algo."""
    config = {
        "base_url": os.getenv("LLM_BASE_URL"),
        "api_key": os.getenv("LLM_API_KEY"),
        "model": os.getenv("LLM_MODEL"),
    }
    return config if all(config.values()) else None


def max_calls_per_hour() -> int:
    """LLM_MAX_CALLS_PER_HOUR: entero ≥ 0 (0 desactiva el LLM); otro valor → 30."""
    raw = os.getenv("LLM_MAX_CALLS_PER_HOUR", "").strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_MAX_CALLS_PER_HOUR
    return value if value >= 0 else DEFAULT_MAX_CALLS_PER_HOUR


class HourlyLimiter:
    """Ventana deslizante de una hora, en memoria y segura entre hilos (sin estado en disco)."""

    def __init__(self, clock: Callable[[], float] = time.monotonic, window: float = WINDOW_S):
        self._clock = clock
        self._window = window
        self._calls: deque[float] = deque()
        self._lock = threading.Lock()

    def try_acquire(self, limit: int) -> bool:
        """Registra un intento si cabe en la ventana; False si se alcanzó el límite."""
        with self._lock:
            now = self._clock()
            while self._calls and now - self._calls[0] >= self._window:
                self._calls.popleft()
            if len(self._calls) >= limit:
                return False
            self._calls.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._calls.clear()


def persistent_limiter() -> SQLiteHourlyLimiter:
    path = Path(os.getenv("LLM_RATE_LIMIT_DB") or PROJECT_ROOT / ".runtime" / "llm-quota.sqlite3")
    return SQLiteHourlyLimiter(path)


def _openai_client(base_url: str, api_key: str):
    from openai import OpenAI

    return OpenAI(base_url=base_url, api_key=api_key, timeout=LLM_TIMEOUT_S, max_retries=0)


def explain(
    customer: dict,
    prediction: dict,
    client_factory: Callable = _openai_client,
    limiter: HourlyLimiter | SQLiteHourlyLimiter | None = None,
) -> dict:
    """Texto del LLM si está configurado, dentro del límite y responde; si no, la plantilla."""
    facts = build_facts(customer, prediction)
    fallback = template_text(facts)
    config = llm_config()
    if config is None:
        return {"text": fallback, "source": "template", "reason": "LLM no configurado"}
    limiter = limiter or persistent_limiter()
    try:
        allowed = limiter.try_acquire(max_calls_per_hour())
    except (OSError, sqlite3.Error):
        return {"text": fallback, "source": "template", "reason": "presupuesto LLM no disponible"}
    if not allowed:  # Cuenta intentos, también los fallidos.
        return {"text": fallback, "source": "template", "reason": RATE_LIMIT_REASON}
    try:
        client = client_factory(config["base_url"], config["api_key"])
        response = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
            ],
            temperature=0.2,
            max_tokens=200,
        )
        text = (response.choices[0].message.content or "").strip()
    except Exception as error:  # Red, cuota, credenciales o formato: siempre hay plantilla.
        return {"text": fallback, "source": "template", "reason": type(error).__name__}
    if not text:
        return {"text": fallback, "source": "template", "reason": "respuesta vacía"}
    return {"text": text, "source": "llm", "model": config["model"]}
