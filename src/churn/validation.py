"""Data validation (spec 001).

Two levels:
- **Hard checks** (pandera schema): contract violations. Pipeline must stop.
- **Soft checks** (quality report): legal but suspicious patterns. Logged, documented,
  and handled explicitly downstream; they never stop the pipeline.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaErrors

from churn.config import GENDERS, GEOGRAPHIES, RAW_FILE, TARGET
from churn.data import load_raw

# --------------------------------------------------------------------- hard checks
RAW_SCHEMA = pa.DataFrameSchema(
    columns={
        "RowNumber": pa.Column(int, pa.Check.ge(1), unique=True),
        "CustomerId": pa.Column(int, unique=True),
        "Surname": pa.Column("string", pa.Check.str_length(min_value=1)),
        "CreditScore": pa.Column(int, pa.Check.in_range(300, 900)),
        "Geography": pa.Column("string", pa.Check.isin(GEOGRAPHIES)),
        "Gender": pa.Column("string", pa.Check.isin(GENDERS)),
        "Age": pa.Column(int, pa.Check.in_range(18, 100)),
        "Tenure": pa.Column(int, pa.Check.in_range(0, 10)),
        "Balance": pa.Column(float, pa.Check.ge(0)),
        "NumOfProducts": pa.Column(int, pa.Check.in_range(1, 4)),
        "HasCrCard": pa.Column(int, pa.Check.isin([0, 1])),
        "IsActiveMember": pa.Column(int, pa.Check.isin([0, 1])),
        "EstimatedSalary": pa.Column(float, pa.Check.gt(0)),
        TARGET: pa.Column(int, pa.Check.isin([0, 1])),
    },
    strict=True,
    coerce=False,
    unique=None,
)


def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Validate against the data contract, collecting *all* failures (lazy)."""
    return RAW_SCHEMA.validate(df, lazy=True)


# --------------------------------------------------------------------- soft checks
LEAKAGE_AUC_THRESHOLD = 0.90
MIN_REASONABLE_SALARY = 1_000.0


@dataclass
class QualityReport:
    n_rows: int
    n_duplicated_rows: int
    churn_rate: float
    balance_zero_share: float
    churn_by_products: dict[int, dict[str, float]]
    low_salary_rows: int
    surname_cardinality: int
    single_feature_auc: dict[str, float]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _auc(score: pd.Series, y: pd.Series) -> float:
    """ROC-AUC of a single feature via Mann-Whitney U (no sklearn needed)."""
    ranks = score.rank(method="average")
    n_pos = int((y == 1).sum())
    n_neg = len(y) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    u = ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2
    return float(u / (n_pos * n_neg))


def quality_report(df: pd.DataFrame) -> QualityReport:
    """Compute soft quality checks. Assumes ``validate_schema`` already passed."""
    y = df[TARGET]
    numeric = df.select_dtypes("number").columns.difference([TARGET, "RowNumber", "CustomerId"])
    aucs = {col: round(_auc(df[col], y), 4) for col in sorted(numeric)}

    by_products = (
        df.groupby("NumOfProducts")[TARGET]
        .agg(churn_rate="mean", n="size")
        .round(4)
        .to_dict(orient="index")
    )

    report = QualityReport(
        n_rows=len(df),
        n_duplicated_rows=int(df.drop(columns=["RowNumber"]).duplicated().sum()),
        churn_rate=round(float(y.mean()), 4),
        balance_zero_share=round(float((df["Balance"] == 0).mean()), 4),
        churn_by_products={int(k): v for k, v in by_products.items()},
        low_salary_rows=int((df["EstimatedSalary"] < MIN_REASONABLE_SALARY).sum()),
        surname_cardinality=int(df["Surname"].nunique()),
        single_feature_auc=aucs,
    )

    w = report.warnings
    if report.n_duplicated_rows:
        w.append(f"{report.n_duplicated_rows} duplicated rows (ignoring RowNumber).")
    for col, auc in aucs.items():
        if max(auc, 1 - auc) >= LEAKAGE_AUC_THRESHOLD:
            w.append(f"Possible leakage: '{col}' alone reaches AUC={auc:.3f}.")
    if report.balance_zero_share > 0.2:
        w.append(
            f"Balance has a point mass at 0 ({report.balance_zero_share:.1%}); "
            "add an explicit 'has_balance' flag instead of treating it as continuous."
        )
    for k, stats in report.churn_by_products.items():
        if k >= 3 and stats["churn_rate"] > 0.8:
            w.append(
                f"NumOfProducts={k}: churn {stats['churn_rate']:.0%} on only "
                f"{int(stats['n'])} rows; likely synthetic artefact, audit model reliance."
            )
    if report.low_salary_rows:
        w.append(
            f"{report.low_salary_rows} rows with EstimatedSalary < {MIN_REASONABLE_SALARY:,.0f}; "
            "implausible values, salary is likely synthetic (check for uniform distribution)."
        )
    return report


# --------------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the raw churn dataset.")
    parser.add_argument("--path", type=Path, default=RAW_FILE)
    parser.add_argument("--out", type=Path, default=None, help="Write report as JSON.")
    args = parser.parse_args(argv)

    df = load_raw(args.path)
    try:
        validate_schema(df)
    except SchemaErrors as exc:
        print("SCHEMA VALIDATION FAILED", file=sys.stderr)
        print(f"Fallos detectados: {len(exc.failure_cases)}. Valores omitidos.", file=sys.stderr)
        return 1

    report = quality_report(df)
    payload = json.dumps(report.to_dict(), indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
