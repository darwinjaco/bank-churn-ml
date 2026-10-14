"""Presentación y gráficos del dashboard (spec 005 v1.3). Solo datos ya calculados."""

from __future__ import annotations

import hashlib
import json

BLUE = "#1D4ED8"
TEAL = "#0F766E"
AMBER = "#B45309"
NEUTRAL = "#DCE3ED"
FEATURE_LABELS = {
    "CreditScore": "Puntuación crediticia",
    "Age": "Edad",
    "Tenure": "Antigüedad",
    "Balance": "Saldo",
    "NumOfProducts": "Productos",
    "HasCrCard": "Tarjeta de crédito",
    "IsActiveMember": "Actividad del cliente",
    "Geography": "País",
    "has_balance": "Saldo positivo",
}
COUNTRIES = {"France": "Francia", "Germany": "Alemania", "Spain": "España"}


def number(value: float, decimals: int = 0, *, signed: bool = False) -> str:
    """Formato español consistente, también para valores negativos."""
    sign = "+" if signed else ""
    return f"{value:{sign},.{decimals}f}".translate(str.maketrans(",.", ".,"))


def percent(value: float) -> str:
    return f"{number(100 * value, 1)} %"


def feature_label(name: str) -> str:
    if name.startswith("Geography="):
        country = name.removeprefix("Geography=")
        return f"País: {COUNTRIES.get(country, country)}"
    return FEATURE_LABELS.get(name, name)


def batch_identity(customers: list[dict]) -> str:
    """Identidad solo del contrato normalizado; llamar después de prepare_batch."""
    raw = json.dumps(customers, sort_keys=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def chart(rows: list[dict], *, height: int, **spec) -> dict:
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "data": {"values": rows},
        "height": height,
        "autosize": {"type": "fit-x", "contains": "padding"},
        "config": {
            "view": {"stroke": None},
            "axis": {"labelFontSize": 12, "titleFontSize": 12, "labelLimit": 230},
        },
        **spec,
    }


def risk_chart(probability: float, threshold: float) -> dict:
    rows = [
        {"risk": probability * 100, "threshold": threshold * 100, "label": percent(probability)}
    ]
    axis = {"scale": {"domain": [0, 100]}, "axis": {"title": "Probabilidad calibrada (%)"}}
    return chart(
        rows,
        height=70,
        layer=[
            {
                "mark": {"type": "bar", "color": NEUTRAL, "size": 20},
                "encoding": {"x": {"datum": 100, **axis}},
            },
            {
                "mark": {"type": "bar", "color": BLUE, "size": 20},
                "encoding": {
                    "x": {"field": "risk", "type": "quantitative", **axis},
                    "tooltip": [{"field": "label", "title": "Probabilidad"}],
                },
            },
            {
                "mark": {"type": "rule", "color": AMBER, "strokeDash": [5, 4], "strokeWidth": 2},
                "encoding": {"x": {"field": "threshold", "type": "quantitative", **axis}},
            },
        ],
    )


def reason_data(prediction: dict) -> list[dict]:
    return [
        {
            "factor": feature_label(reason["feature"]),
            "contribution_pp": reason["shap"] * 100,
            "direction": reason["direction"],
            "label": f"{number(reason['shap'] * 100, 1, signed=True)} pp",
        }
        for reason in prediction.get("top_reasons", [])
    ]


def reasons_chart(prediction: dict) -> dict:
    return chart(
        reason_data(prediction),
        height=140,
        mark={"type": "bar", "cornerRadiusEnd": 3},
        encoding={
            "x": {
                "field": "contribution_pp",
                "type": "quantitative",
                "title": "Contribución sin calibrar (pp)",
            },
            "y": {"field": "factor", "type": "nominal", "sort": None, "title": None},
            "color": {
                "field": "direction",
                "type": "nominal",
                "title": None,
                "scale": {
                    "domain": ["aumenta el riesgo", "reduce el riesgo"],
                    "range": [AMBER, TEAL],
                },
                "legend": {"orient": "bottom"},
            },
            "tooltip": [
                {"field": "factor", "title": "Factor"},
                {"field": "label", "title": "Contribución"},
                {"field": "direction", "title": "Efecto"},
            ],
        },
    )


def probability_bins(predictions: list[dict]) -> list[dict]:
    counts = [0] * 10
    for row in predictions:
        counts[min(int(row["churn_probability"] * 10), 9)] += 1
    return [
        {
            "lower": i * 10,
            "upper": (i + 1) * 10,
            "customers": count,
            "interval": f"{i * 10} a {(i + 1) * 10} %",
        }
        for i, count in enumerate(counts)
    ]


def histogram_chart(predictions: list[dict], threshold: float) -> dict:
    return chart(
        probability_bins(predictions),
        height=220,
        layer=[
            {
                "mark": {"type": "bar", "color": BLUE, "binSpacing": 3},
                "encoding": {
                    "x": {
                        "field": "lower",
                        "type": "quantitative",
                        "bin": "binned",
                        "scale": {"domain": [0, 100]},
                        "title": "Probabilidad calibrada (%)",
                    },
                    "x2": {"field": "upper"},
                    "y": {
                        "field": "customers",
                        "type": "quantitative",
                        "title": "Clientes",
                        "axis": {"tickMinStep": 1},
                    },
                    "tooltip": [
                        {"field": "interval", "title": "Intervalo"},
                        {"field": "customers", "title": "Clientes"},
                    ],
                },
            },
            {
                "mark": {"type": "rule", "color": AMBER, "strokeDash": [5, 4]},
                "encoding": {"x": {"datum": threshold * 100}},
            },
        ],
    )


def decision_counts(predictions: list[dict]) -> list[dict]:
    contacted = sum(bool(row["contact"]) for row in predictions)
    return [
        {"decision": "Contactar", "customers": contacted},
        {"decision": "No contactar", "customers": len(predictions) - contacted},
    ]


def decisions_chart(predictions: list[dict]) -> dict:
    return chart(
        decision_counts(predictions),
        height=160,
        mark={"type": "bar", "color": TEAL, "size": 32},
        encoding={
            "x": {
                "field": "customers",
                "type": "quantitative",
                "title": "Clientes",
                "axis": {"tickMinStep": 1},
            },
            "y": {"field": "decision", "type": "nominal", "sort": None, "title": None},
            "tooltip": [
                {"field": "decision", "title": "Decisión"},
                {"field": "customers", "title": "Clientes"},
            ],
        },
    )


def policy_data(final: dict) -> list[dict]:
    names = {
        "model": "Modelo de retención",
        "everyone": "Contactar a todos",
        "nobody": "No contactar",
    }
    return [
        {
            "policy": label,
            "benefit_eur": final["policies"][key]["benefit_eur"],
            "contacted": final["policies"][key]["contacted"],
            "label": f"{number(final['policies'][key]['benefit_eur'])} €",
        }
        for key, label in names.items()
        if key in final.get("policies", {})
        and {"contacted", "benefit_eur"} <= final["policies"][key].keys()
    ]


def policies_chart(final: dict) -> dict:
    rows = policy_data(final)
    maximum = max([1.0, *(row["benefit_eur"] for row in rows)])
    return chart(
        rows,
        height=200,
        layer=[
            {
                "mark": {"type": "bar", "color": BLUE, "size": 30},
                "encoding": {
                    "x": {
                        "field": "benefit_eur",
                        "type": "quantitative",
                        "title": "Beneficio bajo los supuestos (€)",
                        "scale": {"domainMax": maximum * 1.15},
                        "axis": {
                            "tickCount": 5,
                            "labelExpr": "replace(format(datum.value, ',.0f'), /,/g, '.')",
                        },
                    },
                    "y": {"field": "policy", "type": "nominal", "sort": None, "title": None},
                    "tooltip": [
                        {"field": "policy", "title": "Política"},
                        {"field": "label", "title": "Beneficio"},
                        {"field": "contacted", "title": "Contactados"},
                    ],
                },
            },
            {
                "mark": {"type": "text", "align": "left", "dx": 7, "color": "#14243B"},
                "encoding": {
                    "x": {"field": "benefit_eur", "type": "quantitative"},
                    "y": {"field": "policy", "type": "nominal", "sort": None},
                    "text": {"field": "label"},
                },
            },
        ],
    )


def psi_data(scenario: dict) -> list[dict]:
    rows = [
        {"variable": feature_label(name), "psi": row["psi"], "level": row["level"]}
        for name, row in scenario["variables"].items()
    ]
    rows.append(
        {
            "variable": "Probabilidad predicha",
            "psi": scenario["probability"]["psi"],
            "level": scenario["probability"]["level"],
        }
    )
    return rows


def psi_chart(scenario: dict, limits: dict) -> dict:
    return chart(
        psi_data(scenario),
        height=310,
        layer=[
            {
                "mark": {"type": "bar", "cornerRadiusEnd": 3},
                "encoding": {
                    "x": {
                        "field": "psi",
                        "type": "quantitative",
                        "title": "PSI · cambio de distribución",
                        "axis": {
                            "tickCount": 5,
                            "labelExpr": "replace(format(datum.value, '.2f'), '.', ',')",
                        },
                    },
                    "y": {"field": "variable", "type": "nominal", "sort": "-x", "title": None},
                    "color": {
                        "field": "level",
                        "type": "nominal",
                        "title": None,
                        "scale": {
                            "domain": ["estable", "moderado", "alerta"],
                            "range": [TEAL, "#8091A6", AMBER],
                        },
                        "legend": {"orient": "bottom"},
                    },
                    "tooltip": [
                        {"field": "variable", "title": "Variable"},
                        {"field": "psi", "title": "PSI", "format": ".3f"},
                        {"field": "level", "title": "Estado"},
                    ],
                },
            },
            *[
                {
                    "mark": {"type": "rule", "color": color, "strokeDash": [5, 4]},
                    "encoding": {"x": {"datum": value}},
                }
                for value, color in [
                    (limits["stable_below"], "#8091A6"),
                    (limits["alert_above"], AMBER),
                ]
            ],
        ],
    )


def calibration_data(report: dict) -> list[dict]:
    return [
        {
            "scenario": name,
            "description": row["description"],
            "gap_pp": row["labeled"]["calibration_gap"] * 100,
            "label": f"{number(row['labeled']['calibration_gap'] * 100, 1, signed=True)} pp",
        }
        for name, row in report["scenarios"].items()
    ]


def calibration_chart(report: dict) -> dict:
    tolerance = report["config"]["degradation"]["calibration_tolerance"] * 100
    return chart(
        calibration_data(report),
        height=230,
        layer=[
            {
                "data": {"values": [{}]},
                "mark": {"type": "rect", "color": TEAL, "opacity": 0.08},
                "encoding": {"y": {"datum": -tolerance}, "y2": {"datum": tolerance}},
            },
            {"mark": {"type": "rule", "color": "#8091A6"}, "encoding": {"y": {"datum": 0}}},
            {
                "mark": {"type": "bar", "color": BLUE, "size": 30},
                "encoding": {
                    "x": {
                        "field": "scenario",
                        "type": "ordinal",
                        "sort": None,
                        "title": "Escenario simulado",
                        "axis": {"labelAngle": 0},
                    },
                    "y": {
                        "field": "gap_pp",
                        "type": "quantitative",
                        "title": "Desviación de calibración (pp)",
                    },
                    "tooltip": [
                        {"field": "scenario", "title": "Escenario"},
                        {"field": "description", "title": "Cambio"},
                        {"field": "label", "title": "Desviación"},
                    ],
                },
            },
        ],
    )
