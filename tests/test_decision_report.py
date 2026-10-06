"""El reporte de la semana 5 se genera desde decision.json, sin cifras a mano."""

import json

from churn import decision_report


def test_render_matches_json_and_cli(tmp_path, monkeypatch):
    data = json.loads(decision_report.DECISION_JSON.read_text(encoding="utf-8"))
    text = decision_report.render(data)
    model = data["decision"]["policies"]["model"]
    assert decision_report._eur(model["benefit_eur"]) in text
    assert f"{data['decision']['threshold']:.4f}" in text
    chosen = data["calibration"]["chosen"]
    assert f"{data['calibration']['validation_metrics'][chosen]['brier']:.4f}" in text
    assert "(elegida)" in text
    destination = tmp_path / "decision.md"
    monkeypatch.setattr(decision_report, "DECISION_MD", destination)
    assert decision_report.main() == 0
    assert destination.read_text(encoding="utf-8") == text


def test_eur_format_uses_dot_thousands():
    assert decision_report._eur(61950.0) == "61.950 €"
