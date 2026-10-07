"""Orquestación de la semana 6 con datos sintéticos y artefacto pequeño."""

import json

import joblib
import pytest

from churn import run_audit
from churn.calibration import CalibratedModel, SigmoidCalibrator, oof_predictions
from churn.config import FEATURE_SETS, TARGET
from churn.decision import decide
from churn.pipeline import build_pipeline


@pytest.fixture
def artifact(valid_df):
    columns = [c for c in FEATURE_SETS["tree"] if c != "EstimatedSalary"]
    pipeline = build_pipeline(
        "rf", "tree", exclude=("EstimatedSalary",), params={"n_estimators": 20, "max_depth": 4}
    )
    oof = oof_predictions(pipeline, valid_df[columns], valid_df[TARGET])
    pipeline.fit(valid_df[columns], valid_df[TARGET])
    return CalibratedModel(pipeline, SigmoidCalibrator().fit(oof, valid_df[TARGET]), columns)


def test_attach_gender_and_missing(valid_df, csv_path):
    validation = valid_df.drop(columns="Gender").iloc[:50]
    merged = run_audit.attach_gender(validation, csv_path)
    assert merged["Gender"].notna().all() and len(merged) == 50
    other = validation.assign(CustomerId=validation["CustomerId"] + 10**9)
    with pytest.raises(ValueError):
        run_audit.attach_gender(other, csv_path)


def test_run_audit_structure(artifact, valid_df):
    result = run_audit.run_audit(artifact, valid_df)
    assert result["contacted"] == int(decide(artifact.predict_proba(valid_df)).sum())
    assert set(result["segments"]) >= {"Gender", "productos", "Geography"}
    assert set(result["e01_gender"]) >= {"contact_rate", "recall", "precision", "calibration_gap"}
    assert result["shap"]["additivity_max_gap"] <= 1e-6


def test_main_writes_audit_and_checks_decision(artifact, valid_df, monkeypatch, tmp_path):
    joblib.dump(artifact, tmp_path / "model.joblib")
    (tmp_path / "metadata.json").write_text(
        json.dumps({"model_family": "rf", "git_commit": "d" * 40}), encoding="utf-8"
    )
    contacted = int(decide(artifact.predict_proba(valid_df)).sum())
    decision = {"decision": {"policies": {"model": {"contacted": contacted}}}}
    (tmp_path / "decision.json").write_text(json.dumps(decision), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{(tmp_path / 't.db').as_posix()}")
    origin = {"git_commit": "a" * 40, "csv_sha256": "b" * 64, "split_manifest_sha256": "c" * 64}
    monkeypatch.setattr(run_audit, "provenance", lambda: origin)
    for name, value in {
        "MODEL_FILE": tmp_path / "model.joblib",
        "METADATA_FILE": tmp_path / "metadata.json",
        "DECISION_FILE": tmp_path / "decision.json",
        "AUDIT_FILE": tmp_path / "audit.json",
        "FIGURE_FILE": tmp_path / "shap.png",
    }.items():
        monkeypatch.setattr(run_audit, name, value)
    monkeypatch.setattr(run_audit, "load_validation", lambda: valid_df.drop(columns="Gender"))
    monkeypatch.setattr(run_audit, "attach_gender", lambda frame: valid_df)
    assert run_audit.main() == 0
    payload = json.loads((tmp_path / "audit.json").read_text(encoding="utf-8"))
    assert payload["artifact_commit"] == "d" * 40 and payload["run_id"]
    assert (tmp_path / "shap.png").exists()
    decision["decision"]["policies"]["model"]["contacted"] = contacted + 1
    (tmp_path / "decision.json").write_text(json.dumps(decision), encoding="utf-8")
    with pytest.raises(RuntimeError):
        run_audit.main()
