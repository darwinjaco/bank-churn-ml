import numpy as np
import pandas as pd
import pytest
from pandera.errors import SchemaErrors

from churn.validation import _auc, main, quality_report, validate_schema


def test_valid_data_passes(valid_df):
    validate_schema(valid_df)


@pytest.mark.parametrize(
    ("column", "bad_value"),
    [
        ("Balance", -1.0),
        ("Age", 12),
        ("CreditScore", 1000),
        ("NumOfProducts", 5),
        ("Exited", 2),
        ("HasCrCard", 3),
        ("Geography", "Italy"),
        ("Gender", "Other"),
    ],
)
def test_contract_violations_fail(valid_df, column, bad_value):
    df = valid_df.copy()
    df.loc[0, column] = bad_value
    with pytest.raises(SchemaErrors):
        validate_schema(df)


def test_duplicate_customer_id_fails(valid_df):
    df = valid_df.copy()
    df.loc[1, "CustomerId"] = df.loc[0, "CustomerId"]
    with pytest.raises(SchemaErrors):
        validate_schema(df)


def test_lazy_validation_collects_all_errors(valid_df):
    df = valid_df.copy()
    df.loc[0, "Balance"] = -1.0
    df.loc[1, "Age"] = 5
    with pytest.raises(SchemaErrors) as exc:
        validate_schema(df)
    assert {"Balance", "Age"} <= set(exc.value.failure_cases["column"])


def test_auc_perfect_and_random():
    y = np.array([0, 0, 1, 1])
    assert _auc(pd.Series([1, 2, 3, 4]), pd.Series(y)) == 1.0
    assert _auc(pd.Series([4, 3, 2, 1]), pd.Series(y)) == 0.0


def test_leakage_is_flagged(valid_df):
    df = valid_df.copy()
    df["CreditScore"] = 400 + df["Exited"] * 400  # perfectly separates target
    report = quality_report(df)
    assert any("leakage" in w and "CreditScore" in w for w in report.warnings)


def test_balance_point_mass_is_flagged(valid_df):
    report = quality_report(valid_df)
    assert report.balance_zero_share > 0.2
    assert any("point mass" in w for w in report.warnings)


def test_cli_writes_report(csv_path, tmp_path):
    out = tmp_path / "report.json"
    assert main(["--path", str(csv_path), "--out", str(out)]) == 0
    assert out.exists()


def test_cli_returns_1_on_schema_failure(tmp_path, valid_df, capsys):
    path = tmp_path / "bad.csv"
    valid_df.assign(Balance=-1.0).to_csv(path, index=False)
    assert main(["--path", str(path)]) == 1
    captured = capsys.readouterr().err
    assert "Valores omitidos" in captured
    assert "failure_case" not in captured and "CustomerId" not in captured


@pytest.mark.realdata
def test_real_dataset_contract(real_df):
    validate_schema(real_df)
    report = quality_report(real_df)
    assert report.n_rows == 10_000
    assert report.n_duplicated_rows == 0
    assert not any("leakage" in w for w in report.warnings)
