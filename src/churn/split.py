"""División estratificada y carga exclusiva de exploración (especificación 003)."""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import train_test_split

from churn.config import (
    DATA_PROCESSED,
    ID_COLUMNS,
    MODEL_FEATURES,
    PROJECT_ROOT,
    RANDOM_SEED,
    RAW_FILE,
    TARGET,
)
from churn.data import DTYPES, load_raw
from churn.validation import validate_schema

SPLIT_FILE = DATA_PROCESSED / "split.json"
MANIFEST_FILE = PROJECT_ROOT / "reports" / "split_manifest.json"


def make_split(df: pd.DataFrame) -> dict[str, list[int]]:
    """Devuelve posiciones de filas: prueba primero, luego entrenamiento/validación."""
    positions = np.arange(len(df))
    development, test = train_test_split(
        positions, test_size=0.2, stratify=df[TARGET], random_state=RANDOM_SEED
    )
    train, validation = train_test_split(
        development,
        test_size=0.25,
        stratify=df.iloc[development][TARGET],
        random_state=RANDOM_SEED,
    )
    return {
        "train": sorted(train.tolist()),
        "validation": sorted(validation.tolist()),
        "test": sorted(test.tolist()),
    }


def build_manifest(df: pd.DataFrame, split: dict[str, list[int]]) -> dict:
    """Registra los agregados y hashes de la división del CSV original."""
    partitions = {}
    for name, positions in split.items():
        subset = df.iloc[positions]
        ids = sorted(int(value) for value in subset["CustomerId"])
        payload = json.dumps(ids, separators=(",", ":")).encode("utf-8")
        partitions[name] = {
            "n_rows": len(subset),
            "churn_rate": float(subset[TARGET].mean()),
            "customer_ids_sha256": hashlib.sha256(payload).hexdigest(),
        }
    return {
        "seed": RANDOM_SEED,
        "csv_sha256": hashlib.sha256(RAW_FILE.read_bytes()).hexdigest(),
        "sklearn_version": sklearn.__version__,
        "partitions": partitions,
    }


def load_exploration() -> pd.DataFrame:
    """Carga únicamente filas de entrenamiento y validación del CSV original."""
    split = json.loads(SPLIT_FILE.read_text(encoding="utf-8"))
    train = set(split["train"])
    positions = sorted(train | set(split["validation"]))
    selected = set(positions)
    columns = ID_COLUMNS + MODEL_FEATURES + [TARGET]
    df = pd.read_csv(
        RAW_FILE,
        dtype={column: DTYPES[column] for column in columns},
        usecols=columns,
        skiprows=lambda row: row > 0 and row - 1 not in selected,
    )
    df.index = positions
    df["partition"] = ["train" if position in train else "validation" for position in positions]
    return df


def main() -> int:
    """Escribe índices locales y el manifiesto versionable; no crea un lector de prueba."""
    df = load_raw(RAW_FILE)
    validate_schema(df)
    split = make_split(df)
    manifest = build_manifest(df, split)
    for path, payload in ((SPLIT_FILE, split), (MANIFEST_FILE, manifest)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0
