"""Procedencia y registro genérico en MLflow para la semana 4 (spec 002 §5.4)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess

import numpy as np
from mlflow.tracking import MlflowClient

from churn.config import PROJECT_ROOT
from churn.split import MANIFEST_FILE

EXPERIMENT = "bank-churn"
DEFAULT_TRACKING_URI = "sqlite:///mlruns/mlflow.db"


def manifest_sha256(path=MANIFEST_FILE) -> str:
    """SHA-256 del manifiesto canónico (spec 002 v1.5): independiente del fin de línea."""
    content = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def provenance() -> dict:
    """Commit de Git, hash del CSV y hash canónico del manifiesto de división."""
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    return {
        "git_commit": commit,
        "csv_sha256": json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))["csv_sha256"],
        "split_manifest_sha256": manifest_sha256(),
    }


def jsonable(value):
    """Convierte tipos de NumPy a tipos nativos serializables en JSON."""
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def log_run(
    name: str,
    stage: str,
    params: dict,
    summary: dict | None,
    folds: list[dict] | None,
    origin: dict,
    tags: dict | None = None,
    extra_metrics: dict | None = None,
) -> str:
    """Registra una corrida con las etiquetas obligatorias y devuelve su run ID."""
    uri = os.getenv("MLFLOW_TRACKING_URI") or DEFAULT_TRACKING_URI
    if uri == DEFAULT_TRACKING_URI:
        (PROJECT_ROOT / "mlruns").mkdir(parents=True, exist_ok=True)
    client = MlflowClient(tracking_uri=uri)
    experiment = client.get_experiment_by_name(EXPERIMENT)
    experiment_id = experiment.experiment_id if experiment else client.create_experiment(EXPERIMENT)
    all_tags = {
        "mlflow.runName": name,
        "stage": stage,
        "git_commit": origin["git_commit"],
        "csv_sha256": origin["csv_sha256"],
        "split_manifest_sha256": origin["split_manifest_sha256"],
        "eligible": "true",
        "final": "false",
        **(tags or {}),
    }
    run_id = client.create_run(experiment_id, tags=all_tags).info.run_id
    for key, value in params.items():
        client.log_param(run_id, key, str(value))
    for metric, values in (summary or {}).items():
        client.log_metric(run_id, f"{metric}_mean", values["mean"])
        client.log_metric(run_id, f"{metric}_std", values["std"])
    for step, fold in enumerate(folds or [], start=1):
        for metric, value in fold["metrics"].items():
            client.log_metric(run_id, metric, value, step=step)
    for metric, value in (extra_metrics or {}).items():
        client.log_metric(run_id, metric, float(value))
    client.set_terminated(run_id)
    return run_id
