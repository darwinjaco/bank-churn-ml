"""Evaluación final única en prueba (spec 002 v1.6 §11.6; AGENTS.md regla 7)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

from churn.config import ID_COLUMNS, MODEL_FEATURES, PROJECT_ROOT, RAW_FILE, TARGET
from churn.data import DTYPES
from churn.decision import evaluate_policies, threshold
from churn.split import MANIFEST_FILE, SPLIT_FILE
from churn.tracking import jsonable, log_run, provenance

MODEL_FILE = PROJECT_ROOT / "models" / "model.joblib"
METADATA_FILE = PROJECT_ROOT / "models" / "metadata.json"
METADATA_COPY = PROJECT_ROOT / "reports" / "model_metadata.json"
FINAL_FILE = PROJECT_ROOT / "reports" / "final_test.json"


class FinalEvaluationDoneError(RuntimeError):
    """La prueba solo puede usarse una vez."""


def _ids_sha256(frame: pd.DataFrame) -> str:
    ids = sorted(int(value) for value in frame["CustomerId"])
    return hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode("utf-8")).hexdigest()


def load_test_once(final_file=None, split_file=None, manifest_file=None, raw_file=None):
    """Única función que carga la prueba: se niega si ya existe una evaluación final y
    comprueba que los clientes coinciden con el manifiesto versionado."""
    final_file = final_file or FINAL_FILE
    split_file = split_file or SPLIT_FILE
    manifest_file = manifest_file or MANIFEST_FILE
    raw_file = raw_file or RAW_FILE
    if final_file.exists():
        raise FinalEvaluationDoneError(f"Ya existe {final_file.name}: la prueba se usó una vez.")
    positions = json.loads(split_file.read_text(encoding="utf-8"))["test"]
    columns = ID_COLUMNS + MODEL_FEATURES + [TARGET]
    frame = pd.read_csv(raw_file, dtype={c: DTYPES[c] for c in columns}, usecols=columns)
    test = frame.iloc[sorted(positions)].reset_index(drop=True)
    expected = json.loads(manifest_file.read_text(encoding="utf-8"))["partitions"]["test"]
    if _ids_sha256(test) != expected["customer_ids_sha256"] or len(test) != expected["n_rows"]:
        raise ValueError("La partición de prueba no coincide con el manifiesto versionado.")
    return test


def evaluate(model, test: pd.DataFrame) -> dict:
    y = test[TARGET].to_numpy()
    probability = model.predict_proba(test)
    return {
        "n": len(test),
        "churn_rate": float(y.mean()),
        "metrics": {
            "ap": float(average_precision_score(y, probability)),
            "roc_auc": float(roc_auc_score(y, probability)),
            "brier": float(brier_score_loss(y, probability)),
            "log_loss": float(log_loss(y, probability, labels=[0, 1])),
        },
        "mean_predicted": float(np.mean(probability)),
        "decision": evaluate_policies(probability, y),
    }


def main() -> int:
    metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    if metadata.get("final_test_evaluation") != "pendiente":
        raise FinalEvaluationDoneError("La metadata indica que la prueba ya se evaluó.")
    if abs(metadata["threshold"] - threshold()) > 1e-12:
        raise ValueError("El umbral de la metadata no coincide con la spec 004.")
    model = joblib.load(MODEL_FILE)
    test = load_test_once()
    result = evaluate(model, test)
    origin = provenance()
    run_id = log_run(
        "final-test-evaluation",
        "final",
        {"model": metadata["model_family"], "artifact_commit": metadata["git_commit"]},
        None,
        None,
        origin,
        tags={"final": "true"},
        extra_metrics={
            **{f"test_{k}": v for k, v in result["metrics"].items()},
            "test_benefit_model": result["decision"]["policies"]["model"]["benefit_eur"],
        },
    )
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    payload = {
        "stage": "final",
        "final": True,
        "evaluated_on": stamp,
        **origin,
        "artifact_commit": metadata["git_commit"],
        "run_id": run_id,
        **result,
    }
    FINAL_FILE.write_text(
        json.dumps(jsonable(payload), indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    metadata["final_test_evaluation"] = f"completada el {stamp} (reports/final_test.json)"
    for path in (METADATA_FILE, METADATA_COPY):
        path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    m = result["metrics"]
    print(f"Prueba: AP {m['ap']:.3f}, ROC-AUC {m['roc_auc']:.3f}, Brier {m['brier']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
