"""CSV de ejemplo sintético (spec 006 §5): reproducible y válido para la API."""

import importlib.util
import io
from pathlib import Path

import pandas as pd

from churn.api import Customer
from churn.ui import CONTRACT_COLUMNS, prepare_batch

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "make_example_csv", ROOT / "scripts" / "make_example_csv.py"
)
make_example_csv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make_example_csv)


def test_example_matches_generator():
    content = make_example_csv.OUTPUT.read_text(encoding="utf-8")
    assert content == make_example_csv.generate()


def test_example_rows_pass_contract_and_batch():
    frame = pd.read_csv(io.StringIO(make_example_csv.generate()))
    assert len(frame) == make_example_csv.N_CUSTOMERS
    assert frame["ClienteEjemplo"].str.fullmatch(r"EJ-\d{2}").all()
    for record in frame[CONTRACT_COLUMNS].to_dict(orient="records"):
        Customer(**record)
    assert len(prepare_batch(frame)) == len(frame)
    germany = frame["Geography"].eq("Germany")
    assert (frame.loc[germany, "Balance"] > 0).all()


def test_generator_is_seeded():
    assert make_example_csv.generate(seed=1) != make_example_csv.generate()
    assert make_example_csv.generate(seed=1) == make_example_csv.generate(seed=1)
