"""Funciones puras del dashboard (spec 005 §7): cliente HTTP y formato. Sin Streamlit."""

from __future__ import annotations

import os

import httpx
import pandas as pd

CONTRACT_COLUMNS = [
    "CreditScore",
    "Age",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "HasCrCard",
    "IsActiveMember",
    "Geography",
]
MAX_BATCH = 1_000


def api_url() -> str:
    return os.getenv("API_URL", "http://localhost:8000").rstrip("/")


class ApiClient:
    def __init__(self, base_url: str | None = None, client: httpx.Client | None = None):
        self.base_url = (base_url or api_url()).rstrip("/")
        self.client = client or httpx.Client(timeout=30.0)

    def _get(self, path: str) -> dict:
        response = self.client.get(f"{self.base_url}{path}")
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload: dict) -> dict:
        response = self.client.post(f"{self.base_url}{path}", json=payload)
        response.raise_for_status()
        return response.json()

    def health(self) -> dict:
        return self._get("/health")

    def model(self) -> dict:
        return self._get("/model")

    def explain(self, customer: dict) -> dict:
        return self._post("/explain", customer)

    def batch(self, customers: list[dict]) -> dict:
        return self._post("/predict/batch", {"customers": customers})


def prepare_batch(frame: pd.DataFrame) -> list[dict]:
    """Toma solo las columnas del contrato (descarta Gender, IDs, salario) y valida tamaño."""
    missing = [c for c in CONTRACT_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"Faltan columnas: {', '.join(missing)}")
    if not 1 <= len(frame) <= MAX_BATCH:
        raise ValueError(f"El archivo debe tener entre 1 y {MAX_BATCH} filas.")
    data = frame[CONTRACT_COLUMNS].copy()
    for column in ("CreditScore", "Age", "Tenure", "NumOfProducts", "HasCrCard", "IsActiveMember"):
        data[column] = data[column].astype(int)
    data["Balance"] = data["Balance"].astype(float)
    data["Geography"] = data["Geography"].astype(str)
    return data.to_dict(orient="records")


def results_table(frame: pd.DataFrame, response: dict) -> pd.DataFrame:
    """Une el CSV original con las predicciones, ordenado por probabilidad descendente."""
    predictions = pd.DataFrame(response["predictions"])
    out = frame.reset_index(drop=True).copy()
    out["probabilidad_abandono"] = predictions["churn_probability"].round(4)
    out["contactar"] = predictions["contact"].map({True: "sí", False: "no"})
    out["beneficio_esperado_eur"] = predictions["expected_benefit_eur"].round(2)
    return out.sort_values("probabilidad_abandono", ascending=False).reset_index(drop=True)


def reason_rows(prediction: dict) -> list[dict]:
    return [
        {
            "Factor del modelo": reason["feature"],
            "Valor": reason["value"],
            "Efecto": reason["direction"],
            "Contribución (pp)": round(100 * reason["shap"], 1),
        }
        for reason in prediction.get("top_reasons", [])
    ]


def eur(value: float) -> str:
    return f"{value:,.0f} €".replace(",", ".")
