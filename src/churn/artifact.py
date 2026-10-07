"""Distribución del modelo congelado vía GitHub Release con verificación SHA-256 (spec 005 §3)."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import urllib.request
from collections.abc import Callable
from pathlib import Path

import joblib

from churn.config import PROJECT_ROOT

MODEL_RELEASE_TAG = "model-v1.0"
MODEL_URL = (
    "https://github.com/darwinjaco/bank-churn-ml/releases/download/"
    f"{MODEL_RELEASE_TAG}/model.joblib"
)
MODEL_SHA256 = "579b7fe349dc035c3171582cbfba1bfaed4599a795da4b149d7664ed21dc095a"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "model.joblib"


class ArtifactIntegrityError(RuntimeError):
    """El archivo del modelo no coincide con el SHA-256 publicado."""


def model_path() -> Path:
    return Path(os.getenv("MODEL_PATH") or DEFAULT_MODEL_PATH)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url, timeout=120) as response, destination.open("wb") as out:
        shutil.copyfileobj(response, out)


def ensure_model(
    path: Path | None = None,
    url: str | None = None,
    expected: str = MODEL_SHA256,
    downloader: Callable[[str, Path], None] = _download,
) -> Path:
    """Ruta del modelo verificado; lo descarga si falta y falla si el hash no coincide."""
    path = Path(path or model_path())
    url = url or os.getenv("MODEL_URL") or MODEL_URL
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False, suffix=".part") as tmp:
            temporary = Path(tmp.name)
        try:
            downloader(url, temporary)
            actual = sha256_file(temporary)
            if actual != expected:
                raise ArtifactIntegrityError(f"SHA-256 descargado {actual} != esperado {expected}")
            temporary.replace(path)
            path.chmod(0o644)  # El temporal nace con 0600; la imagen corre con otro usuario.
        finally:
            temporary.unlink(missing_ok=True)
    actual = sha256_file(path)
    if actual != expected:
        raise ArtifactIntegrityError(f"SHA-256 de {path.name} {actual} != esperado {expected}")
    return path


def load_model(path: Path | None = None, expected: str = MODEL_SHA256):
    """Carga el modelo solo después de verificar su hash."""
    return joblib.load(ensure_model(path, expected=expected))


def main() -> int:
    path = ensure_model()
    print(f"Modelo verificado: {path} ({MODEL_SHA256[:12]}…)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
