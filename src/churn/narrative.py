"""Explicación en lenguaje natural (spec 005 §6): LLM opcional con plantilla determinista."""

from __future__ import annotations

import json
import os
from collections.abc import Callable

LLM_TIMEOUT_S = 10.0
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


def _openai_client(base_url: str, api_key: str):
    from openai import OpenAI

    return OpenAI(base_url=base_url, api_key=api_key, timeout=LLM_TIMEOUT_S, max_retries=0)


def explain(
    customer: dict,
    prediction: dict,
    client_factory: Callable = _openai_client,
) -> dict:
    """Texto del LLM si está configurado y responde; si no, la plantilla."""
    facts = build_facts(customer, prediction)
    fallback = template_text(facts)
    config = llm_config()
    if config is None:
        return {"text": fallback, "source": "template", "reason": "LLM no configurado"}
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
