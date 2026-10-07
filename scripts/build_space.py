"""Arma el directorio que se sincroniza con el Space de Hugging Face (spec 006 §2.2-2.3).

Uso: python scripts/build_space.py --out <directorio vacío>

Copia solo lo que necesita el Dockerfile, deriva un Dockerfile con la variante "release"
del modelo y falla si el resultado contiene binarios, datos, modelos o secretos.
Solo usa la biblioteca estándar (se ejecuta en el workflow sin instalar el proyecto).
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPACE_README = Path("deploy/space/README.md")
STATIC_FILES = (
    "pyproject.toml",
    "uv.lock",
    "docker/start.sh",
    "reports/model_metadata.json",
    "reports/final_test.json",
    "reports/monitoring.json",
)
PY_GLOBS = ("src/churn/*.py", "dashboard/*.py")
FORBIDDEN_DIRS = {"data", "models", "mlruns", ".git", ".venv"}
FORBIDDEN_SUFFIXES = {".csv", ".joblib", ".parquet", ".pkl", ".db", ".png", ".gif"}
SPACE_HEADER = (
    "# Generado por scripts/build_space.py para Hugging Face Spaces (spec 006 §2.3).\n"
    "# Solo variante release: el modelo se descarga del GitHub Release y se verifica\n"
    "# por SHA-256 durante el build. No editar aquí: el original es ./Dockerfile.\n"
)


class SpaceBuildError(RuntimeError):
    """El contenido del Space no cumple la spec 006."""


def _replace_once(text: str, pattern: str, replacement: str, flags: int = 0) -> str:
    new, count = re.subn(pattern, replacement, text, flags=flags)
    if count != 1:
        raise SpaceBuildError(f"Dockerfile: se esperaba 1 coincidencia de {pattern!r}, hay {count}")
    return new


def space_dockerfile(text: str) -> str:
    """Dockerfile del repositorio → solo variante release (sin contexto 'localmodel')."""
    body = text.split("\n")
    first_code = next(i for i, line in enumerate(body) if line.strip() and not line.startswith("#"))
    text = "\n".join(body[first_code:])
    text = _replace_once(text, r"^ARG MODEL_SOURCE=release\n\n?", "", flags=re.M)
    text = _replace_once(text, r"^FROM base AS model-local\n.*?(?=^FROM )", "", flags=re.M | re.S)
    text = _replace_once(
        text, r"^FROM model-\$\{MODEL_SOURCE\} AS final$", "FROM model-release AS final", re.M
    )
    for leftover in ("MODEL_SOURCE", "localmodel", "model-local"):
        if leftover in text:
            raise SpaceBuildError(f"Dockerfile del Space conserva '{leftover}'")
    return SPACE_HEADER + "\n" + text


def sources(root: Path = ROOT) -> dict[str, Path]:
    """Destino relativo → archivo de origen."""
    files = {name: root / name for name in STATIC_FILES}
    for pattern in PY_GLOBS:
        for path in sorted(root.glob(pattern)):
            files[path.relative_to(root).as_posix()] = path
    files["README.md"] = root / SPACE_README
    missing = sorted(name for name, path in files.items() if not path.is_file())
    if missing:
        raise SpaceBuildError(f"Faltan archivos para el Space: {', '.join(missing)}")
    return files


def check_tree(directory: Path) -> list[str]:
    """Falla si hay binarios, datos, modelos o secretos. Devuelve la lista de archivos."""
    problems, listing = [], []
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        rel = path.relative_to(directory)
        name = rel.as_posix()
        listing.append(name)
        if FORBIDDEN_DIRS & set(rel.parts[:-1]):
            problems.append(f"{name}: directorio prohibido")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            problems.append(f"{name}: extensión prohibida")
        if path.name == ".env" or path.name.startswith(".env."):
            problems.append(f"{name}: archivo de entorno")
        data = path.read_bytes()
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"{name}: binario (no UTF-8)")
        else:
            if b"\0" in data:
                problems.append(f"{name}: binario (bytes nulos)")
    if problems:
        raise SpaceBuildError("Contenido no permitido en el Space:\n  " + "\n  ".join(problems))
    return listing


def build(out: Path, root: Path = ROOT) -> list[str]:
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise SpaceBuildError(f"{out} no está vacío")
    files = sources(root)
    for name, source in files.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    dockerfile = space_dockerfile((root / "Dockerfile").read_text(encoding="utf-8"))
    (out / "Dockerfile").write_text(dockerfile, encoding="utf-8")
    return check_tree(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, help="Directorio de salida (vacío o inexistente)")
    args = parser.parse_args(argv)
    out = args.out or Path(tempfile.mkdtemp(prefix="space-"))
    try:
        listing = build(out)
    except SpaceBuildError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Space armado en {out} ({len(listing)} archivos):")
    print("\n".join(f"  {name}" for name in listing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
