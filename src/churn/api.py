"""API de predicción y decisión de retención (spec 005 §4-6)."""

from __future__ import annotations

import json
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, Request
from pydantic import BaseModel, ConfigDict, Field

from churn import explain, narrative
from churn.config import PROJECT_ROOT

METADATA_FILE = PROJECT_ROOT / "reports" / "model_metadata.json"
FINAL_FILE = PROJECT_ROOT / "reports" / "final_test.json"
MAX_BATCH = 1_000
N_REASONS = 3


class Customer(BaseModel):
    """Contrato de entrada (spec 001); campos extra como Gender o identificadores dan 422."""

    model_config = ConfigDict(extra="forbid")

    CreditScore: int = Field(ge=300, le=900)
    Age: int = Field(ge=18, le=100)
    Tenure: int = Field(ge=0, le=10)
    Balance: float = Field(ge=0)
    NumOfProducts: int = Field(ge=1, le=4)
    HasCrCard: Literal[0, 1]
    IsActiveMember: Literal[0, 1]
    Geography: Literal["France", "Germany", "Spain"]
    EstimatedSalary: float | None = Field(default=None, gt=0, description="Se ignora (E-03).")


class Batch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customers: list[Customer] = Field(min_length=1, max_length=MAX_BATCH)


@dataclass
class Service:
    """Modelo, metadata y SHA-256 cargados una sola vez al arrancar."""

    model: object
    metadata: dict
    artifact_sha256: str
    final_test: dict | None = None

    @property
    def threshold(self) -> float:
        return float(self.metadata["threshold"])

    def _frame(self, customers: list[Customer]) -> pd.DataFrame:
        return pd.DataFrame([c.model_dump(exclude={"EstimatedSalary"}) for c in customers])

    def predict(self, customers: list[Customer], reasons: bool = False) -> list[dict]:
        frame = self._frame(customers)
        probability = self.model.predict_proba(frame)
        assumptions = self.metadata["assumptions"]
        benefit = (
            probability * assumptions["retention_success_rate"] * assumptions["customer_value_eur"]
            - assumptions["contact_cost_eur"]
        )
        out = [
            {
                "churn_probability": float(p),
                "contact": bool(p > self.threshold),
                "expected_benefit_eur": float(b),
                "threshold": self.threshold,
            }
            for p, b in zip(probability, benefit, strict=True)
        ]
        if reasons:
            shap_result = explain.compute_shap(self.model, frame)
            for row, item in enumerate(out):
                order = np.argsort(-np.abs(shap_result["values"][row]))[:N_REASONS]
                item["top_reasons"] = [
                    {
                        "feature": explain.display_name(shap_result["names"][j]),
                        "value": float(shap_result["matrix"][row, j]),
                        "shap": float(shap_result["values"][row, j]),
                        "direction": "aumenta el riesgo"
                        if shap_result["values"][row, j] > 0
                        else "reduce el riesgo",
                    }
                    for j in order
                ]
        return out


def load_service() -> Service:
    from churn.artifact import MODEL_SHA256, load_model

    metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    final = json.loads(FINAL_FILE.read_text(encoding="utf-8")) if FINAL_FILE.exists() else None
    return Service(load_model(), metadata, MODEL_SHA256, final)


def create_app(service_factory: Callable[[], Service] = load_service) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.service = service_factory()
        yield

    app = FastAPI(
        title="Bank churn → retention decisions",
        version="1.0",
        description="Probabilidad calibrada de abandono y decisión de contacto (specs 004 y 005).",
        lifespan=lifespan,
    )

    def service(request: Request) -> Service:
        return request.app.state.service

    @app.get("/health")
    def health(request: Request) -> dict:
        svc = service(request)
        return {
            "status": "ok",
            "artifact_sha256": svc.artifact_sha256,
            "model_commit": svc.metadata.get("git_commit"),
        }

    @app.get("/model")
    def model_info(request: Request) -> dict:
        svc = service(request)
        keys = (
            "model_family",
            "input_columns",
            "excluded_columns",
            "calibrator",
            "threshold",
            "assumptions",
            "decision_rule",
            "final_test_evaluation",
        )
        info = {key: svc.metadata.get(key) for key in keys}
        if svc.final_test:
            info["final_test"] = {
                "metrics": svc.final_test["metrics"],
                "benefit_model_eur": svc.final_test["decision"]["policies"]["model"]["benefit_eur"],
                "n": svc.final_test["n"],
            }
        return info

    @app.post("/predict")
    def predict(customer: Customer, request: Request) -> dict:
        return service(request).predict([customer], reasons=True)[0]

    @app.post("/explain")
    def explain_customer(customer: Customer, request: Request) -> dict:
        prediction = service(request).predict([customer], reasons=True)[0]
        return {
            **narrative.explain(customer.model_dump(exclude={"EstimatedSalary"}), prediction),
            "prediction": prediction,
        }

    @app.post("/predict/batch")
    def predict_batch(batch: Batch, request: Request) -> dict:
        predictions = service(request).predict(batch.customers)
        contacted = [p for p in predictions if p["contact"]]
        return {
            "predictions": predictions,
            "summary": {
                "n": len(predictions),
                "contacted": len(contacted),
                "expected_benefit_eur": float(sum(p["expected_benefit_eur"] for p in contacted)),
            },
        }

    return app


app = create_app()
