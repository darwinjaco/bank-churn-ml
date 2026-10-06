"""Semana 5 de extremo a extremo con datos sintéticos: E-04, decisión y artefacto."""

import json

import joblib
import numpy as np
import pytest

from churn import decide
from churn.split import make_split

SELECTION = {
    "final_model": "rf",
    "chosen_params": {"n_estimators": 10, "random_state": 42, "n_jobs": -1, "max_depth": 4},
    "final_exclude": ["EstimatedSalary"],
}


@pytest.fixture
def partitions(valid_df):
    split = make_split(valid_df)
    return (
        valid_df.iloc[split["train"]].reset_index(drop=True),
        valid_df.iloc[split["validation"]].reset_index(drop=True),
    )


def test_final_configuration_and_missing_model():
    config = decide.final_configuration(SELECTION)
    assert config["feature_set"] == "tree" and "EstimatedSalary" not in config["columns"]
    with pytest.raises(ValueError):
        decide.final_configuration({**SELECTION, "final_model": None})


def test_run_decision_chooses_calibrator_and_applies_threshold(partitions):
    training, validation = partitions
    result = decide.run_decision(SELECTION, training, validation)
    calibration = result["calibration"]
    assert calibration["chosen"] in {"none", "sigmoid", "isotonic"}
    assert set(calibration["validation_metrics"]) == {"none", "sigmoid", "isotonic"}
    assert result["decision"]["threshold"] == pytest.approx(1 / 6)
    probability = result["model"].predict_proba(validation)
    contacted = int((probability > 1 / 6).sum())
    assert result["decision"]["policies"]["model"]["contacted"] == contacted
    assert all(len(rows) == 10 for rows in calibration["reliability"].values())


def test_main_writes_reports_artifact_and_metadata(partitions, monkeypatch, tmp_path):
    training, validation = partitions
    import churn.train as train_module

    (tmp_path / "selection.json").write_text(json.dumps(SELECTION), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{(tmp_path / 't.db').as_posix()}")
    origin = {"git_commit": "a" * 40, "csv_sha256": "b" * 64, "split_manifest_sha256": "c" * 64}
    monkeypatch.setattr(decide, "provenance", lambda: origin)
    monkeypatch.setattr(decide, "SELECTION_FILE", tmp_path / "selection.json")
    monkeypatch.setattr(decide, "DECISION_FILE", tmp_path / "decision.json")
    monkeypatch.setattr(decide, "METADATA_COPY", tmp_path / "model_metadata.json")
    monkeypatch.setattr(decide, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(decide, "FIGURE_FILE", tmp_path / "reliability.png")
    monkeypatch.setattr(train_module, "load_training", lambda: training)
    monkeypatch.setattr(decide, "load_validation", lambda: validation)
    assert decide.main() == 0
    payload = json.loads((tmp_path / "decision.json").read_text(encoding="utf-8"))
    metadata = json.loads((tmp_path / "models" / "metadata.json").read_text(encoding="utf-8"))
    assert metadata == json.loads((tmp_path / "model_metadata.json").read_text(encoding="utf-8"))
    assert metadata["threshold"] == pytest.approx(1 / 6)
    assert metadata["excluded_columns"] == ["EstimatedSalary"]
    assert metadata["calibrator"] == payload["calibration"]["chosen"]
    assert set(payload["run_ids"]) == {"calibration", "decision"}
    assert (tmp_path / "reliability.png").stat().st_size > 0
    model = joblib.load(tmp_path / "models" / "model.joblib")
    probability = model.predict_proba(validation)
    assert ((probability >= 0) & (probability <= 1)).all()
    expected = payload["decision"]["policies"]["model"]["contacted"]
    assert int(np.sum(probability > metadata["threshold"])) == expected
