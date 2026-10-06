"""Precisión legible y diferencias calculadas a partir del JSON de pliegues."""

import json

import numpy as np
import pytest

from churn import reports


def test_paired_differences_from_synthetic_json():
    data = json.loads('{"raw":[0.2,0.4,0.3],"eda":[0.3,0.35,0.3]}')
    raw = [{"fold": i, "metrics": {"ap": value}} for i, value in enumerate(data["raw"], 1)]
    eda = [{"fold": i, "metrics": {"ap": value}} for i, value in enumerate(data["eda"], 1)]
    actual = reports.paired_differences(raw, eda)
    differences = np.array([0.1, -0.05, 0])
    assert actual["by_fold"] == pytest.approx(differences)
    assert actual["mean"] == pytest.approx(differences.mean())
    assert actual["std"] == pytest.approx(differences.std(ddof=1))
    assert (actual["positive"], actual["negative"], actual["zero"]) == (1, 1, 1)
    with pytest.raises(ValueError):
        reports.paired_differences(raw[:1], eda)
    eda[0]["fold"] = 99
    with pytest.raises(ValueError):
        reports.paired_differences(raw, eda)


def test_renderer_and_cli_preserve_json(tmp_path, monkeypatch):
    data = json.loads(reports.BASELINES_JSON.read_text(encoding="utf-8"))
    text = reports.render_baselines(data)
    assert "+0.198 ± 0.019" in text and "5/5 positivos" in text
    assert "0.657 ± 0.028" in text
    destination = tmp_path / "baselines.md"
    monkeypatch.setattr(reports, "BASELINES_MD", destination)
    assert reports.main() == 0
    assert destination.read_text(encoding="utf-8") == text
