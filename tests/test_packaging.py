"""Las dependencias de runtime cubren todo lo que importan la API y el dashboard.

La imagen Docker instala solo [project].dependencies (`uv sync --no-dev`); un import
satisfecho por un grupo de desarrollo pasa los tests pero rompe el contenedor.
"""

from __future__ import annotations

import ast
import sys
import tomllib
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = [ROOT / "src/churn/api.py", ROOT / "dashboard/app.py", ROOT / "src/churn/artifact.py"]


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
            if node.module == "churn":
                names.update(f"churn.{alias.name}" for alias in node.names)
    return names


def _serving_third_party() -> set[str]:
    """Módulos de terceros alcanzables desde los puntos de entrada de serving."""
    pending, seen, external = list(ENTRYPOINTS), set(), set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        for name in _imports(path):
            top = name.split(".")[0]
            if top == "churn":
                module = ROOT / "src" / (name.replace(".", "/") + ".py")
                if module.exists():
                    pending.append(module)
            elif top not in sys.stdlib_module_names and top != "__future__":
                external.add(top)
    return external


def _runtime_closure() -> set[str]:
    """Distribuciones instaladas por [project].dependencies, transitivamente."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    pending = [Requirement(spec) for spec in project["dependencies"]]
    closure: set[str] = set()
    while pending:
        req = pending.pop()
        name = canonicalize_name(req.name)
        if name in closure:
            continue
        closure.add(name)
        try:
            requires = metadata.requires(req.name) or []
        except metadata.PackageNotFoundError:
            continue
        for spec in requires:
            child = Requirement(spec)
            extras = req.extras or {""}
            if child.marker is None or any(child.marker.evaluate({"extra": e}) for e in extras):
                pending.append(child)
    return closure


def test_serving_imports_are_runtime_dependencies():
    providers = metadata.packages_distributions()
    closure = _runtime_closure()
    missing = {
        module: providers.get(module, [module])
        for module in _serving_third_party()
        if not any(canonicalize_name(d) in closure for d in providers.get(module, [module]))
    }
    assert not missing, f"Importados en serving pero fuera de [project].dependencies: {missing}"
