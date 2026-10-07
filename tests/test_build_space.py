"""Contenido del Space de Hugging Face (spec 006 §2.2-2.3)."""

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("build_space", ROOT / "scripts" / "build_space.py")
build_space = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_space)

EXPECTED_STATIC = {
    "Dockerfile",
    "README.md",
    "pyproject.toml",
    "uv.lock",
    "docker/start.sh",
    "dashboard/app.py",
    "reports/model_metadata.json",
    "reports/final_test.json",
    "reports/monitoring.json",
}


@pytest.fixture(scope="module")
def space(tmp_path_factory):
    out = tmp_path_factory.mktemp("space")
    return out, build_space.build(out)


def front_matter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    assert lines[0] == "---"
    end = lines.index("---", 1)
    pairs = (line.split(":", 1) for line in lines[1:end])
    return {key.strip(): value.strip() for key, value in pairs}


def test_exact_file_list(space):
    _, listing = space
    python = {p.relative_to(ROOT).as_posix() for p in (ROOT / "src" / "churn").glob("*.py")}
    assert set(listing) == EXPECTED_STATIC | python
    forbidden = ("data/", "models/", "tests/", "notebooks/")
    assert not any(name.startswith(forbidden) for name in listing)


def test_space_readme_header(space):
    out, _ = space
    header = front_matter((out / "README.md").read_text(encoding="utf-8"))
    assert header["sdk"] == "docker"
    assert header["app_port"] == "7860"
    assert header["license"] == "mit"


def test_dockerfile_release_only(space):
    out, _ = space
    text = (out / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM model-release AS final" in text
    assert text.count("AS model-release") == 1
    for leftover in ("MODEL_SOURCE", "localmodel", "model-local"):
        assert leftover not in text
    assert "python -m churn.artifact" in text


def test_dockerfile_copy_sources_exist(space):
    """Cada COPY del contexto apunta a un archivo presente en el Space."""
    out, _ = space
    text = (out / "Dockerfile").read_text(encoding="utf-8")
    copies = [line.split()[1:-1] for line in text.splitlines() if line.startswith("COPY ")]
    paths = [p for args in copies if not any(a.startswith("--from") for a in args) for p in args]
    assert paths
    for path in paths:
        assert (out / path).exists(), path


def test_dockerfile_change_is_detected():
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    with pytest.raises(build_space.SpaceBuildError, match="coincidencia"):
        build_space.space_dockerfile(text.replace("FROM base AS model-local", "FROM base AS other"))


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("data/raw/x.txt", b"a"),
        ("models/model.txt", b"a"),
        ("ejemplo.csv", b"a,b\n1,2\n"),
        (".env", b"LLM_API_KEY=x\n"),
        ("figura.bin", b"\x89PNG\x00\x01"),
        ("latin.txt", "año".encode("latin-1")),
    ],
)
def test_check_tree_rejects(tmp_path, name, content):
    target = tmp_path / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    with pytest.raises(build_space.SpaceBuildError, match=re.escape(name)):
        build_space.check_tree(tmp_path)


def test_build_refuses_non_empty_output(tmp_path):
    (tmp_path / "existing.txt").write_text("x")
    with pytest.raises(build_space.SpaceBuildError, match="no está vacío"):
        build_space.build(tmp_path)


def test_main_reports_errors(tmp_path, capsys):
    (tmp_path / "existing.txt").write_text("x")
    assert build_space.main(["--out", str(tmp_path)]) == 1
    assert "ERROR" in capsys.readouterr().err
