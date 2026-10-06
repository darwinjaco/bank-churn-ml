"""Contrastes preregistrados H1-H6 y reporte de exploración (spec 003 v1.1)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from math import comb, prod

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import chi2, chi2_contingency, fisher_exact, kstest, mannwhitneyu

from churn.config import (
    AGE_LABELS,
    AGE_PEAK_RANGE,
    ALPHA,
    AUC_BOOTSTRAP_REPLICATES,
    GERMANY_OR_THRESHOLD,
    PROJECT_ROOT,
    RANDOM_SEED,
    RISK_DIFFERENCE_THRESHOLD,
    SALARY_AUC_EQUIVALENCE,
    TARGET,
    age_band,
    balance_10k,
    centered_age,
    has_balance,
    is_germany,
)
from churn.split import load_exploration
from churn.stats import (
    auc_bootstrap,
    cramers_v,
    holm,
    independence_test,
    odds_ratio,
    risk_difference,
    wilson_ci,
)

HYPOTHESES_FILE = PROJECT_ROOT / "reports" / "hypotheses.json"


@dataclass
class HypothesisResult:
    id: str
    prueba: str
    prueba_usada: str
    estadistico: float | None
    p_raw: float | None
    p_holm: float | None
    efecto: float
    ic_low: float | None
    ic_high: float | None
    umbral: str
    direccion_ok: bool
    veredicto: str
    detalles: dict


def _rates(y: pd.Series, groups: pd.Series, levels) -> dict:
    rates = {}
    for level in levels:
        selected = y[groups == level]
        k, n = int(selected.sum()), len(selected)
        low, high = wilson_ci(k, n)
        rates[str(level)] = {"n": n, "k": k, "rate": k / n, "ic_low": low, "ic_high": high}
    return rates


def _counts(rates: dict, levels) -> np.ndarray:
    return np.asarray(
        [[rates[level]["k"], rates[level]["n"] - rates[level]["k"]] for level in levels]
    )


def _association(table: np.ndarray) -> tuple[float, str, float | None]:
    pvalue, method = independence_test(table)
    if method == "chi2_pearson":
        statistic = float(chi2_contingency(table, correction=False).statistic)
    elif method == "fisher_exact":
        statistic = float(fisher_exact(table, alternative="two-sided").statistic)
        if not np.isfinite(statistic):
            statistic = None
    else:
        # Probabilidad de la tabla observada, estadístico del test condicional exacto.
        rows = table.sum(axis=1)
        numerator = prod(comb(int(n), int(k)) for n, k in zip(rows, table[:, 0], strict=True))
        statistic = numerator / comb(int(table.sum()), int(table[:, 0].sum()))
    return pvalue, method, statistic


def _or_details(table: np.ndarray) -> dict:
    if (table == 0).any():
        return {
            "estimate": None,
            "ic_low": None,
            "ic_high": None,
            "nota": "Woolf indefinido: celdas cero",
        }
    estimate, low, high = odds_ratio(table)
    return {"estimate": estimate, "ic_low": low, "ic_high": high}


def test_h1(df: pd.DataFrame) -> HypothesisResult:
    rates = _rates(df[TARGET], df["IsActiveMember"], (0, 1))
    table = _counts(rates, ("0", "1"))
    first, second = rates["0"], rates["1"]
    effect, low, high = risk_difference(first["k"], first["n"], second["k"], second["n"])
    pvalue, method, statistic = _association(table)
    return HypothesisResult(
        "H1",
        "independencia_2x2",
        method,
        statistic,
        pvalue,
        None,
        effect,
        low,
        high,
        "DR >= 0.05",
        effect > 0,
        "no confirmada",
        {"rates": rates, "or": _or_details(table), "practico_ok": low >= RISK_DIFFERENCE_THRESHOLD},
    )


def test_h2(df: pd.DataFrame) -> HypothesisResult:
    groups = df["NumOfProducts"].map({1: "1", 2: "2", 3: "3-4", 4: "3-4"})
    rates = _rates(df[TARGET], groups, ("1", "2", "3-4"))
    table = _counts(rates, ("1", "2", "3-4"))
    pvalue, method, statistic = _association(table)
    direction = rates["2"]["rate"] < rates["1"]["rate"] < rates["3-4"]["rate"]
    practical = (
        rates["2"]["ic_high"] < rates["1"]["ic_low"]
        and rates["1"]["ic_high"] < rates["3-4"]["ic_low"]
    )
    return HypothesisResult(
        "H2",
        "independencia_3x2",
        method,
        statistic,
        pvalue,
        None,
        cramers_v(table),
        None,
        None,
        "IC Wilson no solapados: tasa(2) < tasa(1) < tasa(3-4)",
        direction,
        "no confirmada",
        {
            "rates": rates,
            "practico_ok": practical,
            "nota_ic": "IC por nivel; V sin IC preregistrado",
        },
    )


def test_h3(df: pd.DataFrame) -> HypothesisResult:
    germany = is_germany(df["Geography"])
    rates = _rates(df[TARGET], germany, (1, 0))
    crude = _or_details(_counts(rates, ("1", "0")))
    features = pd.DataFrame(
        {
            "is_germany": germany,
            "has_balance": has_balance(df["Balance"]),
            "balance_10k": balance_10k(df["Balance"]),
        }
    )
    fitted = sm.Logit(df[TARGET], sm.add_constant(features.astype(float))).fit(disp=False)
    beta = float(fitted.params["is_germany"])
    ci = fitted.conf_int(alpha=ALPHA).loc["is_germany"].to_numpy()
    effect, low, high = float(np.exp(beta)), float(np.exp(ci[0])), float(np.exp(ci[1]))
    log_crude = np.log(crude["estimate"]) if crude["estimate"] is not None else None
    attenuation = (
        float(100 * (log_crude - beta) / log_crude) if log_crude not in (None, 0) else None
    )
    return HypothesisResult(
        "H3",
        "wald_is_germany",
        "wald_logit",
        float(fitted.tvalues["is_germany"]),
        float(fitted.pvalues["is_germany"]),
        None,
        effect,
        low,
        high,
        "OR ajustado >= 1.5",
        effect > 1,
        "no confirmada",
        {
            "rates": rates,
            "or_crudo": crude,
            "or_ajustado": {"estimate": effect, "ic_low": low, "ic_high": high},
            "atenuacion_log_or_pct": attenuation,
            "coeficientes": fitted.params.to_dict(),
            "practico_ok": low >= GERMANY_OR_THRESHOLD,
        },
    )


def test_h4(df: pd.DataFrame) -> HypothesisResult:
    age = centered_age(df["Age"])
    features = pd.DataFrame({"age_c": age})
    linear = sm.Logit(df[TARGET], sm.add_constant(features)).fit(disp=False)
    quadratic = sm.Logit(df[TARGET], sm.add_constant(features.assign(age_c2=age**2))).fit(
        disp=False
    )
    statistic = float(2 * (quadratic.llf - linear.llf))
    beta1, beta2 = float(quadratic.params["age_c"]), float(quadratic.params["age_c2"])
    low, high = quadratic.conf_int(alpha=ALPHA).loc["age_c2"].to_numpy()
    peak = float(-beta1 / (2 * beta2) + df["Age"].mean()) if beta2 != 0 else None
    practical = bool(
        high < 0 and peak is not None and AGE_PEAK_RANGE[0] <= peak <= AGE_PEAK_RANGE[1]
    )
    return HypothesisResult(
        "H4",
        "razon_verosimilitud",
        "likelihood_ratio_logit",
        statistic,
        float(chi2.sf(statistic, 1)),
        None,
        beta2,
        float(low),
        float(high),
        "coeficiente cuadratico < 0 y pico entre 18 y 92",
        beta2 < 0,
        "no confirmada",
        {
            "rates": _rates(df[TARGET], age_band(df["Age"]), AGE_LABELS),
            "peak_age": peak,
            "mean_age": float(df["Age"].mean()),
            "coeficientes": quadratic.params.to_dict(),
            "practico_ok": practical,
        },
    )


def test_h5(df: pd.DataFrame) -> HypothesisResult:
    positive = has_balance(df["Balance"])
    rates = _rates(df[TARGET], positive, (0, 1))
    first, second = rates["0"], rates["1"]
    effect, low, high = risk_difference(first["k"], first["n"], second["k"], second["n"])
    pvalue, method, statistic = _association(_counts(rates, ("0", "1")))
    balances = df.loc[positive == 1, ["Balance", TARGET]]
    churned = balances.loc[balances[TARGET] == 1, "Balance"]
    retained = balances.loc[balances[TARGET] == 0, "Balance"]
    secondary = None
    if len(churned) and len(retained):
        mw = mannwhitneyu(churned, retained, alternative="two-sided")
        secondary = {
            "u": float(mw.statistic),
            "p_raw": float(mw.pvalue),
            "auc": float(mw.statistic / (len(churned) * len(retained))),
            "n_churn": len(churned),
            "n_retained": len(retained),
            "confirmatorio": False,
        }
    return HypothesisResult(
        "H5",
        "independencia_2x2",
        method,
        statistic,
        pvalue,
        None,
        effect,
        low,
        high,
        "DR <= -0.05",
        effect < 0,
        "no confirmada",
        {
            "rates": rates,
            "mann_whitney_saldo_positivo": secondary,
            "practico_ok": high <= -RISK_DIFFERENCE_THRESHOLD,
        },
    )


def test_h6(df: pd.DataFrame) -> HypothesisResult:
    salary = df["EstimatedSalary"]
    effect, low, high = auc_bootstrap(
        salary, df[TARGET], n_boot=AUC_BOOTSTRAP_REPLICATES, seed=RANDOM_SEED
    )
    equivalent = SALARY_AUC_EQUIVALENCE[0] <= low <= high <= SALARY_AUC_EQUIVALENCE[1]
    minimum, maximum = float(salary.min()), float(salary.max())
    secondary = None
    if maximum > minimum:
        ks = kstest(salary, "uniform", args=(minimum, maximum - minimum))
        secondary = {
            "statistic": float(ks.statistic),
            "p_raw": float(ks.pvalue),
            "minimum": minimum,
            "maximum": maximum,
            "confirmatorio": False,
        }
    return HypothesisResult(
        "H6",
        "equivalencia_auc",
        "bootstrap_percentil",
        effect,
        None,
        None,
        effect,
        low,
        high,
        "IC AUC dentro de [0.45, 0.55]",
        True,
        "confirmada" if equivalent else "no confirmada",
        {
            "ks_uniforme": secondary,
            "practico_ok": equivalent,
            "n_boot": AUC_BOOTSTRAP_REPLICATES,
            "seed": RANDOM_SEED,
        },
    )


def run_all(df: pd.DataFrame) -> list[HypothesisResult]:
    results = [function(df) for function in (test_h1, test_h2, test_h3, test_h4, test_h5, test_h6)]
    adjusted = holm([result.p_raw for result in results[:5]])
    for result, pvalue in zip(results[:5], adjusted, strict=True):
        result.p_holm = float(pvalue)
        significant = pvalue < ALPHA
        practical = result.detalles["practico_ok"]
        if significant and result.direccion_ok and practical:
            result.veredicto = "confirmada"
        elif significant and not practical:
            result.veredicto = "detectable sin relevancia"
        else:
            result.veredicto = "no confirmada"
    return results


def main() -> int:
    results = run_all(load_exploration())
    payload = json.dumps(
        [asdict(result) for result in results], indent=2, ensure_ascii=False, allow_nan=False
    )
    HYPOTHESES_FILE.parent.mkdir(parents=True, exist_ok=True)
    HYPOTHESES_FILE.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0
