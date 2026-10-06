"""Regla de selección congelada (spec 002 §6), implementada literalmente como funciones puras."""

from __future__ import annotations

from churn.search_spaces import SIMPLICITY_ORDER

COMPLEX = ("rf", "xgb")


def select_candidate(cv_summary: dict[str, dict[str, float]]) -> dict:
    """Pasos 1-2: mayor AP media de FASE B y parsimonia entre candidatos cercanos.

    ``cv_summary`` = {familia: {"mean": AP media, "std": desviación estándar}}.
    Cercano: diferencia respecto al mejor < std del mejor, o media igual a la del mejor.
    """
    candidates = [family for family in SIMPLICITY_ORDER if family in cv_summary]
    if not candidates:
        raise ValueError("Se requiere al menos una familia candidata.")
    best_mean = max(cv_summary[family]["mean"] for family in candidates)
    # Ante igualdad exacta de medias, el mejor nominal es el primero en orden de simplicidad.
    best = next(family for family in candidates if cv_summary[family]["mean"] == best_mean)
    best_std = cv_summary[best]["std"]
    close = [
        family
        for family in candidates
        if cv_summary[family]["mean"] == best_mean
        or best_mean - cv_summary[family]["mean"] < best_std
    ]
    chosen = next(family for family in SIMPLICITY_ORDER if family in close)
    return {
        "best": best,
        "best_mean": best_mean,
        "best_std": best_std,
        "differences_to_best": {
            family: best_mean - cv_summary[family]["mean"] for family in candidates
        },
        "close": close,
        "chosen": chosen,
    }


def validate_choice(chosen: str, validation_ap: dict[str, float]) -> dict:
    """Pasos 3-5 en validación. "Superar" significa AP estrictamente mayor."""
    dummy = validation_ap["dummy"]
    if not validation_ap[chosen] > dummy:
        return {
            "step": 3,
            "final": None,
            "status": "criterio_fallido_dummy",
            "detail": f"{chosen} no supera a Dummy en validación; revisar desarrollo sin prueba.",
        }
    if chosen in COMPLEX:
        if validation_ap[chosen] > validation_ap["logreg"]:
            return {
                "step": 4,
                "final": chosen,
                "status": "complejo_supera_logreg",
                "detail": f"{chosen} supera a Dummy y a LogReg en validación.",
            }
        if validation_ap["logreg"] > dummy:
            return {
                "step": 4,
                "final": "logreg",
                "status": "logreg_conservada",
                "detail": f"{chosen} no supera a LogReg en validación; se conserva LogReg.",
            }
        # Inalcanzable en la práctica: si el candidato supera a Dummy y LogReg >= candidato,
        # LogReg también supera a Dummy. Se conserva por fidelidad literal a §6, paso 4.
        return {  # pragma: no cover
            "step": 4,
            "final": None,
            "status": "criterio_fallido",
            "detail": "Ni el candidato complejo ni LogReg cumplen el criterio de validación.",
        }
    return {
        "step": 5,
        "final": "logreg",
        "status": "logreg_supera_dummy",
        "detail": "LogReg supera a Dummy; no se exige que se supere a sí misma.",
    }


def select_model(
    cv_summary: dict[str, dict[str, float]], validation_ap: dict[str, float] | None = None
) -> dict:
    """Aplica §6 completa: pasos 1-2 con FASE B y, si hay AP de validación, pasos 3-5."""
    result = {"cv": select_candidate(cv_summary)}
    if validation_ap is not None:
        result["validation"] = validate_choice(result["cv"]["chosen"], validation_ap)
    return result
