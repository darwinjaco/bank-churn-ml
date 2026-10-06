"""Una prueba por rama de la regla de selección de la spec 002 §6."""

import pytest

from churn.selection import select_candidate, select_model, validate_choice


def summary(**values):
    return {name: {"mean": mean, "std": std} for name, (mean, std) in values.items()}


def test_clearly_better_candidate_is_chosen():
    result = select_candidate(summary(logreg=(0.60, 0.02), rf=(0.62, 0.02), xgb=(0.70, 0.02)))
    assert result["best"] == "xgb" and result["close"] == ["xgb"] and result["chosen"] == "xgb"


def test_close_candidates_choose_simplest():
    result = select_candidate(summary(logreg=(0.64, 0.02), rf=(0.655, 0.02), xgb=(0.66, 0.025)))
    assert result["best"] == "xgb"
    assert result["close"] == ["logreg", "rf", "xgb"]
    assert result["chosen"] == "logreg"


def test_closeness_uses_std_of_best_and_strict_inequality():
    # Diferencia exactamente igual a la std del mejor: NO es cercano (estrictamente menor).
    result = select_candidate(summary(logreg=(0.50, 0.01), rf=(0.625, 0.01), xgb=(0.75, 0.125)))
    assert result["close"] == ["xgb"] and result["chosen"] == "xgb"


def test_equal_means_are_close():
    result = select_candidate(summary(logreg=(0.5, 0.01), rf=(0.7, 0.0), xgb=(0.7, 0.0)))
    assert result["best"] == "rf" and result["close"] == ["rf", "xgb"]
    assert result["chosen"] == "rf"


def test_chosen_fails_against_dummy():
    result = validate_choice("xgb", {"dummy": 0.2, "logreg": 0.6, "xgb": 0.2})
    assert result["status"] == "criterio_fallido_dummy" and result["final"] is None


def test_complex_beats_logreg():
    result = validate_choice("xgb", {"dummy": 0.2, "logreg": 0.6, "xgb": 0.65})
    assert result["final"] == "xgb" and result["status"] == "complejo_supera_logreg"


def test_complex_does_not_beat_logreg_keeps_logreg():
    result = validate_choice("rf", {"dummy": 0.2, "logreg": 0.6, "rf": 0.6})
    assert result["final"] == "logreg" and result["status"] == "logreg_conservada"


def test_ties_on_validation_are_not_superation():
    # "Superar" es estrictamente mayor: empatar con Dummy falla el paso 3.
    result = validate_choice("rf", {"dummy": 0.2, "logreg": 0.6, "rf": 0.2})
    assert result["status"] == "criterio_fallido_dummy"
    # Empatar con LogReg (ambos por encima de Dummy) conserva LogReg en el paso 4.
    result = validate_choice("xgb", {"dummy": 0.2, "logreg": 0.5, "xgb": 0.5})
    assert result["final"] == "logreg" and result["status"] == "logreg_conservada"


def test_logreg_branch_only_compares_with_dummy():
    result = validate_choice("logreg", {"dummy": 0.2, "logreg": 0.6})
    assert result["final"] == "logreg" and result["step"] == 5


def test_select_model_combines_steps_and_requires_candidates():
    result = select_model(
        summary(logreg=(0.64, 0.02), xgb=(0.66, 0.03)), {"dummy": 0.2, "logreg": 0.6}
    )
    assert result["cv"]["chosen"] == "logreg" and result["validation"]["final"] == "logreg"
    assert "validation" not in select_model(summary(logreg=(0.6, 0.01)))
    with pytest.raises(ValueError):
        select_candidate({})
