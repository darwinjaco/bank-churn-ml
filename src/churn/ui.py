"""Funciones puras del dashboard (spec 005 §7): cliente HTTP y formato. Sin Streamlit."""

from __future__ import annotations

import csv
import io
import math
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
MAX_CSV_BYTES = 1024 * 1024
INTEGER_COLUMNS = ("CreditScore", "Age", "Tenure", "NumOfProducts", "HasCrCard", "IsActiveMember")
MAX_ERRORS_SHOWN = 5


class ApiError(RuntimeError):
    """Respuesta de error de la API con un mensaje legible para el dashboard."""


def describe_errors(detail) -> str:
    """Errores 422 de FastAPI → 'fila 3, Age: ...' (las filas empiezan en 1)."""
    if not isinstance(detail, list):
        return str(detail)
    messages = []
    for error in detail[:MAX_ERRORS_SHOWN]:
        loc = [part for part in error.get("loc", []) if part not in ("body", "customers")]
        where = ", ".join(
            f"fila {part + 1}" if isinstance(part, int) else str(part) for part in loc
        )
        messages.append(f"{where}: {error.get('msg', 'valor no válido')}")
    if len(detail) > MAX_ERRORS_SHOWN:
        messages.append(f"… y {len(detail) - MAX_ERRORS_SHOWN} errores más")
    return "; ".join(messages)


def api_url() -> str:
    return os.getenv("API_URL", "http://localhost:8000").rstrip("/")


class ApiClient:
    def __init__(self, base_url: str | None = None, client: httpx.Client | None = None):
        self.base_url = (base_url or api_url()).rstrip("/")
        self.client = client or httpx.Client(timeout=30.0)

    @staticmethod
    def _check(response: httpx.Response) -> dict:
        if response.is_success:
            return response.json()
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise ApiError(f"La API respondió {response.status_code}: {describe_errors(detail)}")

    def _get(self, path: str) -> dict:
        return self._check(self.client.get(f"{self.base_url}{path}"))

    def _post(self, path: str, payload: dict) -> dict:
        return self._check(self.client.post(f"{self.base_url}{path}", json=payload))

    def health(self) -> dict:
        return self._get("/health")

    def model(self) -> dict:
        return self._get("/model")

    def explain(self, customer: dict) -> dict:
        return self._post("/explain", customer)

    def batch(self, customers: list[dict]) -> dict:
        return self._post("/predict/batch", {"customers": customers})

    def monitoring(self) -> dict | None:
        """Reporte de monitoreo simulado; None si la API no lo tiene (404)."""
        response = self.client.get(f"{self.base_url}/monitoring")
        return None if response.status_code == 404 else self._check(response)


def read_batch_csv(upload) -> pd.DataFrame:
    """CSV acotado antes de pandas; no materializa columnas fuera del contrato."""
    upload.seek(0)  # Streamlit puede reutilizar el mismo archivo durante una re-ejecución.
    raw = upload.read(MAX_CSV_BYTES + 1)
    if len(raw) > MAX_CSV_BYTES:
        raise ValueError("El CSV supera el máximo de 1 MiB.")
    try:
        header = next(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    except (UnicodeError, csv.Error, StopIteration) as error:
        raise ValueError("El CSV está vacío o no tiene formato UTF-8 válido.") from error
    if len(header) != len(set(header)):
        raise ValueError("El CSV contiene columnas duplicadas.")
    try:
        frame = pd.read_csv(
            io.BytesIO(raw), usecols=lambda column: column in CONTRACT_COLUMNS, nrows=MAX_BATCH + 1
        )
    except (ValueError, pd.errors.ParserError) as error:
        raise ValueError("El CSV no tiene un formato válido.") from error
    if not 1 <= len(frame) <= MAX_BATCH:
        raise ValueError(f"El archivo debe tener entre 1 y {MAX_BATCH} filas.")
    return frame


def prepare_batch(frame: pd.DataFrame) -> list[dict]:
    """Toma solo las columnas del contrato (descarta Gender, IDs, salario) y valida tamaño."""
    missing = [c for c in CONTRACT_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"Faltan columnas: {', '.join(missing)}")
    if not 1 <= len(frame) <= MAX_BATCH:
        raise ValueError(f"El archivo debe tener entre 1 y {MAX_BATCH} filas.")
    data = frame[CONTRACT_COLUMNS].copy()
    empty = [c for c in CONTRACT_COLUMNS if data[c].isna().any()]
    if empty:
        raise ValueError(f"Hay celdas vacías en: {', '.join(empty)}")
    for column in (*INTEGER_COLUMNS, "Balance"):
        values = pd.to_numeric(data[column], errors="coerce")
        if values.isna().any():
            raise ValueError(f"{column} debe ser numérica")
        if not values.map(math.isfinite).all():
            raise ValueError(f"{column} debe contener números finitos")
        if column in INTEGER_COLUMNS and not (values % 1 == 0).all():
            raise ValueError(f"{column} debe contener enteros")
        data[column] = values.astype(int) if column in INTEGER_COLUMNS else values.astype(float)
    data["Geography"] = data["Geography"].astype(str)
    return data.to_dict(orient="records")


def results_table(frame: pd.DataFrame, response: dict) -> pd.DataFrame:
    """Solo entradas normalizadas del contrato y predicciones; sin IDs ni columnas extra."""
    predictions = pd.DataFrame(response["predictions"])
    out = pd.DataFrame(prepare_batch(frame))
    out["probabilidad_abandono"] = predictions["churn_probability"].round(4)
    out["contactar"] = predictions["contact"].map({True: "sí", False: "no"})
    out["beneficio_esperado_eur"] = predictions["expected_benefit_eur"].round(2)
    return out.sort_values("probabilidad_abandono", ascending=False).reset_index(drop=True)


def results_csv(table: pd.DataFrame) -> str:
    """Protección adicional de texto para hojas de cálculo; los números se conservan."""

    def safe(value):
        if isinstance(value, str):
            start = value.lstrip()
            if start.startswith(("=", "+", "-", "@", "\uff1d", "\uff0b", "\uff0d", "\uff20")):
                return "'" + value
        return value

    return table.map(safe).to_csv(index=False, quoting=csv.QUOTE_ALL)


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


def psi_table(report: dict) -> pd.DataFrame:
    """PSI por variable (filas) y escenario (columnas)."""
    scenarios = report["scenarios"]
    table = {
        name: {
            **{column: row["psi"] for column, row in scenario["variables"].items()},
            "Probabilidad predicha": scenario["probability"]["psi"],
        }
        for name, scenario in scenarios.items()
    }
    return pd.DataFrame(table).round(3)


def monitoring_metrics(report: dict) -> pd.DataFrame:
    """Texto ya formateado: una columna con números y "sí"/"no" no se serializa a Arrow."""
    rows = {
        "Alarma de PSI (> 0,25)": lambda s: "sí" if s["alarm"] else "no",
        "Tasa de contacto": lambda s: f"{100 * s['unlabeled']['contact_rate']:.1f} %",
        "Abandono observado": lambda s: f"{100 * s['labeled']['churn_rate']:.1f} %",
        "Calibración global": lambda s: f"{100 * s['labeled']['calibration_gap']:+.1f} pp",
        "Brier": lambda s: f"{s['labeled']['brier']:.4f}",
        "Beneficio realizado": lambda s: eur(s["labeled"]["benefit_model_eur"]),
        "Degradación": lambda s: "sí" if s["degradation"]["degraded"] else "no",
    }
    scenarios = report["scenarios"]
    return pd.DataFrame(
        {name: {label: get(s) for label, get in rows.items()} for name, s in scenarios.items()}
    )


def expectation_rows(report: dict) -> list[dict]:
    return [
        {
            "Expectativa": f"{key} — {row['description']}",
            "Resultado": "cumplida" if row["met"] else "no cumplida",
        }
        for key, row in report["expectations"].items()
    ]
