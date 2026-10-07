"""Reporte de auditoría y ficha del modelo generados desde los JSON versionados."""

from churn import model_card


def test_reports_contain_json_values_and_cli(tmp_path, monkeypatch):
    audit = model_card._load("audit.json")
    text = model_card.render_audit(audit)
    assert f"{audit['e01_gender']['precision']['difference']:+.3f}" in text
    assert audit["shap"]["per_feature"][0]["feature"] in text
    card = model_card.render_card(
        audit,
        model_card._load("decision.json"),
        model_card._load("model_selection.json"),
        model_card._load("tuning.json"),
        model_card._load("model_metadata.json"),
        model_card._load("final_test.json")
        if (model_card.REPORTS / "final_test.json").exists()
        else None,
    )
    assert "Uso previsto" in card and "Limitaciones" in card and "Gender" in card
    monkeypatch.setattr(model_card, "AUDIT_MD", tmp_path / "audit.md")
    monkeypatch.setattr(model_card, "CARD_MD", tmp_path / "card.md")
    assert model_card.main() == 0
    assert (tmp_path / "audit.md").read_text(encoding="utf-8") == text
    assert (tmp_path / "card.md").read_text(encoding="utf-8") == card


def test_formatters():
    assert model_card._pct(None) == "—" and model_card._pct(0.5) == "50.0%"
    assert model_card._eur(61950) == "61.950 €"


def test_card_with_final_section():
    decision = model_card._load("decision.json")
    final = {
        "evaluated_on": "2026-01-01",
        "n": 2000,
        "churn_rate": 0.2,
        "metrics": {"ap": 0.7, "roc_auc": 0.86, "brier": 0.1, "log_loss": 0.33},
        "decision": decision["decision"],
    }
    card = model_card.render_card(
        model_card._load("audit.json"),
        decision,
        model_card._load("model_selection.json"),
        model_card._load("tuning.json"),
        model_card._load("model_metadata.json"),
        final,
    )
    assert "Única evaluación, el 2026-01-01" in card and "| AP | 0.700 |" in card
