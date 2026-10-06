"""El reporte de la semana 4 se genera desde los JSON versionados, sin cifras a mano."""

import json

from churn import selection_report


def test_render_contains_json_values_and_cli_matches(tmp_path, monkeypatch):
    tuning = json.loads(selection_report.TUNING_JSON.read_text(encoding="utf-8"))
    selection = json.loads(selection_report.SELECTION_JSON.read_text(encoding="utf-8"))
    text = selection_report.render(tuning, selection)
    chosen = selection["steps_1_2"]["chosen"]
    assert selection_report.NAMES[chosen] in text
    assert f"{selection['validation_ap'][chosen]:.3f}" in text
    assert f"{selection['e03']['deltas']['mean']:+.3f}" in text
    assert f"{selection['e02']['b_ap_without_3_4']['mean']:.3f}" in text
    assert selection["steps_3_5"]["status"] in text
    destination = tmp_path / "model_selection.md"
    monkeypatch.setattr(selection_report, "SELECTION_MD", destination)
    assert selection_report.main() == 0
    assert destination.read_text(encoding="utf-8") == text
