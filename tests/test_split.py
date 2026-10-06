"""Separación reproducible y protección estructural de la exploración."""

import hashlib
import json

import numpy as np
import pandas as pd
import pytest
import sklearn
from sklearn.model_selection import train_test_split

from churn import split as splitting
from churn.config import AUDIT_COLUMNS, RANDOM_SEED, TARGET


@pytest.fixture
def local_split(monkeypatch, csv_path, tmp_path, valid_df):
    monkeypatch.setattr(splitting, "RAW_FILE", csv_path)
    monkeypatch.setattr(splitting, "SPLIT_FILE", tmp_path / "processed" / "split.json")
    monkeypatch.setattr(splitting, "MANIFEST_FILE", tmp_path / "reports" / "manifest.json")
    result = splitting.make_split(valid_df)
    splitting.SPLIT_FILE.parent.mkdir()
    splitting.SPLIT_FILE.write_text(json.dumps(result), encoding="utf-8")
    return result


def test_disjoint_complete_and_stratified(valid_df):
    result = splitting.make_split(valid_df)
    train, validation, test = (set(result[name]) for name in ("train", "validation", "test"))
    assert not train & validation
    assert not train & test
    assert not validation & test
    assert train | validation | test == set(range(len(valid_df)))
    for name, fraction in (("train", 0.6), ("validation", 0.2), ("test", 0.2)):
        assert abs(len(result[name]) - len(valid_df) * fraction) <= 1
        assert abs(valid_df.iloc[result[name]][TARGET].mean() - valid_df[TARGET].mean()) <= 0.01


def test_seed_and_two_stage_protocol(valid_df):
    expected_development, expected_test = train_test_split(
        np.arange(len(valid_df)),
        test_size=0.2,
        stratify=valid_df[TARGET],
        random_state=RANDOM_SEED,
    )
    expected_train, expected_validation = train_test_split(
        expected_development,
        test_size=0.25,
        stratify=valid_df.iloc[expected_development][TARGET],
        random_state=RANDOM_SEED,
    )
    actual = splitting.make_split(valid_df)
    assert actual["test"] == sorted(expected_test.tolist())
    assert actual["train"] == sorted(expected_train.tolist())
    assert actual["validation"] == sorted(expected_validation.tolist())
    assert actual == splitting.make_split(valid_df)


def test_manifest_records_source_and_partition_hashes(valid_df, local_split):
    manifest = splitting.build_manifest(valid_df, local_split)
    assert manifest["seed"] == RANDOM_SEED
    assert manifest["sklearn_version"] == sklearn.__version__
    assert manifest["csv_sha256"] == hashlib.sha256(splitting.RAW_FILE.read_bytes()).hexdigest()
    for name, indices in local_split.items():
        ids = sorted(valid_df.iloc[indices]["CustomerId"].tolist())
        digest = hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode()).hexdigest()
        assert manifest["partitions"][name] == {
            "n_rows": len(indices),
            "churn_rate": valid_df.iloc[indices][TARGET].mean(),
            "customer_ids_sha256": digest,
        }


def test_exploration_excludes_reserved_customers(valid_df, local_split):
    df = splitting.load_exploration()
    reserved_ids = set(valid_df.iloc[local_split["test"]]["CustomerId"])
    assert not set(df["CustomerId"]) & reserved_ids
    assert set(df["partition"]) == {"train", "validation"}
    assert len(df) == len(local_split["train"]) + len(local_split["validation"])
    assert not set(AUDIT_COLUMNS) & set(df.columns)
    assert not hasattr(splitting, "load_test")
    assert set(df.loc[df["partition"] == "train", "CustomerId"]) == set(
        valid_df.iloc[local_split["train"]]["CustomerId"]
    )


def test_exploration_does_not_parse_reserved_values(valid_df, local_split):
    # Un valor no convertible en una fila reservada no afecta a la exploración.
    poisoned = valid_df.assign(Age=valid_df["Age"].astype("string"))
    poisoned.loc[local_split["test"], "Age"] = "reserved"
    poisoned.to_csv(splitting.RAW_FILE, index=False)
    exploration = splitting.load_exploration()
    assert pd.api.types.is_integer_dtype(exploration["Age"])


def test_cli_writes_both_outputs(valid_df, local_split, capsys):
    assert splitting.main() == 0
    assert json.loads(splitting.SPLIT_FILE.read_text()) == local_split
    manifest = json.loads(splitting.MANIFEST_FILE.read_text())
    assert manifest == splitting.build_manifest(valid_df, local_split)
    assert json.loads(capsys.readouterr().out) == manifest


@pytest.mark.realdata
def test_real_split_matches_versioned_manifest(real_df):
    if not splitting.MANIFEST_FILE.exists():
        pytest.skip("El manifiesto real se generará en T5.")
    manifest = json.loads(splitting.MANIFEST_FILE.read_text(encoding="utf-8"))
    assert splitting.build_manifest(real_df, splitting.make_split(real_df)) == manifest
