"""Lanzadores reales en raíces temporales: outputs y rechazos, sin datos/modelo del proyecto."""

import json
import runpy
import sys
from pathlib import Path

import pytest

from churn import config, experiments, hypotheses, split, tune

ROOT = Path(__file__).parents[1]
SOURCES = ROOT / "src" / "churn"


@pytest.fixture
def isolated_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    raw = tmp_path / "data" / "raw" / "absent.csv"
    processed = tmp_path / "data" / "processed"
    monkeypatch.setattr(config, "RAW_FILE", raw)
    monkeypatch.setattr(config, "DATA_PROCESSED", processed)
    monkeypatch.setattr(split, "RAW_FILE", raw)
    monkeypatch.setattr(split, "SPLIT_FILE", processed / "split.json")
    monkeypatch.setattr(split, "MANIFEST_FILE", tmp_path / "reports" / "split_manifest.json")
    monkeypatch.setattr(hypotheses, "HYPOTHESES_FILE", tmp_path / "reports" / "hypotheses.json")
    monkeypatch.setattr(
        experiments, "SELECTION_FILE", tmp_path / "reports" / "model_selection.json"
    )
    monkeypatch.setattr(tune, "TUNING_FILE", tmp_path / "reports" / "tuning.json")
    monkeypatch.setattr(tune, "OOF_FILE", processed / "oof.parquet")
    monkeypatch.setenv("MODEL_PATH", str(tmp_path / "models" / "model.joblib"))
    monkeypatch.setenv("MODEL_URL", "https://artifact.invalid/model.joblib")
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{(tmp_path / 'tracking.db').as_posix()}")
    monkeypatch.setattr(sys, "argv", ["synthetic-cli"])
    return tmp_path


def execute(module):
    # run_path ejecuta también el guard __main__, sin reemplazar main ni manipular cobertura.
    return runpy.run_path(str(SOURCES / f"{module}.py"), run_name="__main__")


@pytest.mark.parametrize(
    "module,inputs,output,expected",
    [
        ("reports", ["baselines.json"], "baselines.md", "dummy-raw"),
        ("decision_report", ["decision.json"], "decision.md", "61.950"),
        (
            "selection_report",
            ["tuning.json", "model_selection.json"],
            "model_selection.md",
            "Random Forest",
        ),
        (
            "model_card",
            [
                "audit.json",
                "decision.json",
                "model_selection.json",
                "tuning.json",
                "model_metadata.json",
            ],
            "model_card.md",
            "la prueba sigue reservada",
        ),
    ],
)
def test_report_launchers_generate_documents_in_isolated_root(
    isolated_root, module, inputs, output, expected
):
    reports = isolated_root / "reports"
    reports.mkdir()
    for name in inputs:
        (reports / name).write_bytes((ROOT / "reports" / name).read_bytes())
    with pytest.raises(SystemExit) as exit_info:
        execute(module)
    assert exit_info.value.code == 0
    assert expected in (reports / output).read_text(encoding="utf-8")
    assert not (reports / "final_test.json").exists()
    assert not (isolated_root / "models").exists()


@pytest.mark.parametrize(
    "module,missing",
    [
        ("decide", "model_selection.json"),
        ("experiments", "tuning.json"),
        ("tune", "split.json"),
        ("monitoring", "split.json"),
        ("plots", "hypotheses.json"),
    ],
)
def test_analysis_launchers_stop_at_missing_prerequisite(isolated_root, module, missing):
    with pytest.raises(FileNotFoundError) as error:
        execute(module)
    assert Path(error.value.filename).name == missing
    assert Path(error.value.filename).is_relative_to(isolated_root)
    assert list(isolated_root.iterdir()) == []


def test_audit_launcher_requires_local_model(isolated_root, monkeypatch):
    from churn import artifact

    monkeypatch.setattr(artifact, "_download", lambda *args: pytest.fail("No descargar modelo"))
    with pytest.raises(FileNotFoundError, match="artefacto local congelado"):
        execute("run_audit")
    assert list(isolated_root.iterdir()) == []


def test_final_launcher_refuses_completed_synthetic_metadata(isolated_root, monkeypatch):
    from churn import artifact

    models = isolated_root / "models"
    models.mkdir()
    metadata = models / "metadata.json"
    metadata.write_text(json.dumps({"final_test_evaluation": "completada (sintético)"}))
    monkeypatch.setattr(artifact, "load_local_model", lambda *args: pytest.fail("No cargar modelo"))
    with pytest.raises(RuntimeError, match="metadata indica que la prueba ya se evaluó"):
        execute("final_eval")
    assert list(models.iterdir()) == [metadata]
    assert not (isolated_root / "reports").exists()
    assert not (isolated_root / "data").exists()


def test_artifact_launcher_rejects_corrupt_local_file_without_network(isolated_root, monkeypatch):
    import urllib.request

    model = isolated_root / "models" / "model.joblib"
    model.parent.mkdir()
    model.write_bytes(b"modelo sintetico corrupto")
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: pytest.fail("No red"))
    with pytest.raises(RuntimeError, match=r"SHA-256.*!= esperado"):
        execute("artifact")
    assert model.read_bytes() == b"modelo sintetico corrupto"


@pytest.mark.parametrize("valid,code", [(True, 0), (False, 1)])
def test_validation_launcher_exit_code_and_report(
    isolated_root, valid_df, monkeypatch, capsys, valid, code
):
    source = isolated_root / "sample.csv"
    output = isolated_root / "quality.json"
    frame = valid_df if valid else valid_df.assign(Age=0)
    frame.to_csv(source, index=False)
    monkeypatch.setattr(sys, "argv", ["validation", "--path", str(source), "--out", str(output)])
    with pytest.raises(SystemExit) as exit_info:
        execute("validation")
    assert exit_info.value.code == code
    if valid:
        assert json.loads(output.read_text(encoding="utf-8"))["n_rows"] == len(frame)
    else:
        assert not output.exists()
        assert "SCHEMA VALIDATION FAILED" in capsys.readouterr().err
