"""Capa de decisión (spec 004): umbral analítico y beneficio con valores conocidos."""

import numpy as np
import pytest

from churn import decision


def test_threshold_from_config_is_one_sixth():
    assert decision.threshold() == pytest.approx(1 / 6)
    assert decision.threshold(value=2000, cost=50, success=0.25) == pytest.approx(0.1)
    for bad in ({"value": 0}, {"cost": -1}, {"success": 0}, {"success": 1.5}):
        with pytest.raises(ValueError):
            decision.threshold(**bad)


def test_expected_benefit_sign_matches_decision():
    p = np.array([0.0, 1 / 6, 0.2, 1.0])
    benefit = decision.expected_benefit(p)
    np.testing.assert_allclose(benefit, [-50.0, 0.0, 10.0, 250.0], atol=1e-9)
    # En la frontera el redondeo de coma flotante decide; se compara fuera de ella.
    np.testing.assert_array_equal(decision.decide(p), benefit > 1e-9)
    assert not decision.decide(np.array([1 / 6]))[0]  # En t* exacto no se contacta (EB = 0).


def test_realized_benefit_known_case():
    y = np.array([1, 0, 1, 0, 0])
    contact = np.array([True, True, False, False, True])
    # Contactados: un abandono (+300 - 50) y dos permanencias (-50 cada una) = 150.
    assert decision.realized_benefit(contact, y) == pytest.approx(150.0)


def test_evaluate_policies_known_case():
    y = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    p = np.array([0.9, 0.1, 0.5, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05])
    result = decision.evaluate_policies(p, y)
    policies = result["policies"]
    assert result["threshold"] == pytest.approx(1 / 6)
    assert policies["nobody"]["benefit_eur"] == 0
    assert policies["everyone"]["benefit_eur"] == pytest.approx(2 * 300 - 10 * 50)
    assert policies["random_20"]["benefit_eur"] == pytest.approx(0.2 * 100)
    assert policies["oracle"]["benefit_eur"] == pytest.approx(2 * 250)
    assert policies["model"]["contacted"] == 2 and policies["model"]["churners_captured"] == 1
    assert policies["model"]["benefit_eur"] == pytest.approx(250 - 50)
    assert result["best_reference"] == "everyone"
    assert result["model_minus_best_reference_eur"] == pytest.approx(200 - 100)
    assert result["oracle_share_captured"] == pytest.approx(200 / 500)
    cls = result["classification_at_threshold"]
    assert cls["confusion_matrix"] == {"tn": 7, "fp": 1, "fn": 1, "tp": 1}
    assert cls["precision"] == pytest.approx(0.5) and cls["recall"] == pytest.approx(0.5)
    assert result["assumptions"]["retention_success_rate"] == 0.30


def test_policy_report_without_contacts():
    report = decision.policy_report(np.zeros(3, dtype=bool), np.array([1, 0, 0]))
    assert report["benefit_per_contact_eur"] == 0.0 and report["contacted"] == 0
