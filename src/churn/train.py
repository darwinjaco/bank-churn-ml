"""CV exclusiva de entrenamiento y trazabilidad de baselines (spec 002 v1.1)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess

import numpy as np
import pandas as pd
from mlflow.tracking import MlflowClient
from sklearn.base import clone
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold

from churn.config import FEATURE_SETS, PROJECT_ROOT, RANDOM_SEED, TARGET
from churn.pipeline import build_pipeline
from churn.split import MANIFEST_FILE, load_exploration

N_FOLDS = 5
EXPERIMENT = "bank-churn"
DEFAULT_TRACKING_URI = "sqlite:///mlruns/mlflow.db"
BASELINE_RUNS = (("dummy", "raw"), ("logreg", "raw"), ("logreg", "eda"))
BASELINES_FILE = PROJECT_ROOT / "reports" / "baselines.json"


def load_training() -> pd.DataFrame:
    """Filtra inmediatamente exploración: solo filas de entrenamiento."""
    exploration = load_exploration()
    return exploration.loc[exploration["partition"] == "train"].copy()


def _indices_hash(indices) -> str:
    payload = json.dumps(indices.tolist(), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def cross_validate_model(pipeline, x: pd.DataFrame, y) -> dict:
    """Ajusta clones independientes por pliegue; no modifica el pipeline recibido."""
    labels = pd.Series(y).reset_index(drop=True)
    splitter = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    folds = []
    for number, (fitting, scoring) in enumerate(splitter.split(x, labels), start=1):
        fitted = clone(pipeline).fit(x.iloc[fitting], labels.iloc[fitting])
        probability = fitted.predict_proba(x.iloc[scoring])[:, 1]
        actual = labels.iloc[scoring]
        folds.append(
            {
                "fold": number,
                "fit_indices_sha256": _indices_hash(fitting),
                "score_indices_sha256": _indices_hash(scoring),
                "metrics": {
                    "ap": float(average_precision_score(actual, probability)),
                    "roc_auc": float(roc_auc_score(actual, probability)),
                    "brier": float(brier_score_loss(actual, probability)),
                    "log_loss": float(log_loss(actual, probability, labels=[0, 1])),
                },
            }
        )
    summary = {}
    for name in folds[0]["metrics"]:
        values = [fold["metrics"][name] for fold in folds]
        summary[name] = {"mean": float(np.mean(values)), "std": float(np.std(values, ddof=1))}
    return {"folds": folds, "summary": summary}


def _git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def log_run(model: str, feature_set: str, pipeline, metrics: dict, provenance: dict) -> str:
    """Registra parámetros, métricas, pliegues y etiquetas mediante el URI configurado."""
    uri = os.getenv("MLFLOW_TRACKING_URI") or DEFAULT_TRACKING_URI
    if uri == DEFAULT_TRACKING_URI:
        (PROJECT_ROOT / "mlruns").mkdir(parents=True, exist_ok=True)
    client = MlflowClient(tracking_uri=uri)
    experiment = client.get_experiment_by_name(EXPERIMENT)
    experiment_id = experiment.experiment_id if experiment else client.create_experiment(EXPERIMENT)
    tags = {
        "mlflow.runName": f"{model}-{feature_set}",
        "stage": "baseline",
        "git_commit": provenance["git_commit"],
        "csv_sha256": provenance["csv_sha256"],
        "split_manifest_sha256": provenance["split_manifest_sha256"],
        "eligible": str(model != "dummy").lower(),
        "final": "false",
    }
    run = client.create_run(experiment_id, tags=tags)
    run_id = run.info.run_id
    params = {
        "model": model,
        "feature_set": feature_set,
        "n_folds": N_FOLDS,
        "seed": RANDOM_SEED,
        **pipeline.named_steps["model"].get_params(deep=False),
    }
    for name, value in params.items():
        client.log_param(run_id, name, str(value))
    for name, values in metrics["summary"].items():
        client.log_metric(run_id, f"{name}_mean", values["mean"])
        client.log_metric(run_id, f"{name}_std", values["std"])
    for fold in metrics["folds"]:
        for name, value in fold["metrics"].items():
            client.log_metric(run_id, name, value, step=fold["fold"])
    client.set_terminated(run_id)
    return run_id


def main() -> int:
    training = load_training()
    manifest_bytes = MANIFEST_FILE.read_bytes()
    manifest = json.loads(manifest_bytes)
    provenance = {
        "git_commit": _git_commit(),
        "csv_sha256": manifest["csv_sha256"],
        "split_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    }
    runs = []
    for model, feature_set in BASELINE_RUNS:
        pipeline = build_pipeline(model, feature_set)
        metrics = cross_validate_model(
            pipeline, training[FEATURE_SETS[feature_set]], training[TARGET]
        )
        run_id = log_run(model, feature_set, pipeline, metrics, provenance)
        runs.append(
            {
                "name": f"{model}-{feature_set}",
                "model": model,
                "feature_set": feature_set,
                "run_id": run_id,
                "eligible": model != "dummy",
                "final": False,
                "parameters": pipeline.named_steps["model"].get_params(deep=False),
                **metrics,
            }
        )
    payload = {
        "stage": "baseline",
        "n_training": len(training),
        "n_folds": N_FOLDS,
        "seed": RANDOM_SEED,
        **provenance,
        "runs": runs,
    }
    BASELINES_FILE.parent.mkdir(parents=True, exist_ok=True)
    BASELINES_FILE.write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, allow_nan=False))
    return 0
