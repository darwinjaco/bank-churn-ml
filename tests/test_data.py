import pandas as pd
import pytest

from churn.config import EXPECTED_COLUMNS
from churn.data import DataFileNotFoundError, load_raw


def test_load_raw_returns_contract_columns(csv_path):
    df = load_raw(csv_path)
    assert list(df.columns) == EXPECTED_COLUMNS
    assert df["Geography"].dtype == "string"


def test_missing_file_raises_with_instructions(tmp_path):
    with pytest.raises(DataFileNotFoundError, match="data/raw"):
        load_raw(tmp_path / "nope.csv")


def test_missing_column_is_rejected(tmp_path, valid_df):
    path = tmp_path / "bad.csv"
    valid_df.drop(columns=["Age"]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Missing: \\['Age'\\]"):
        load_raw(path)


def test_unexpected_column_is_rejected(tmp_path, valid_df):
    path = tmp_path / "bad.csv"
    valid_df.assign(Complain=0).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Unexpected: \\['Complain'\\]"):
        load_raw(path)


def test_load_does_not_modify_file(csv_path):
    before = csv_path.read_bytes()
    load_raw(csv_path)
    assert csv_path.read_bytes() == before
    assert isinstance(pd.read_csv(csv_path), pd.DataFrame)
