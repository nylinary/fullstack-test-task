"""Executable version of the dependency rule.

Clean architecture is only worth something if it is enforced, so the layering
is asserted rather than described: inner layers must not import outer ones.
"""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"

FRAMEWORKS = ("sqlalchemy", "fastapi", "starlette", "celery", "anyio")

# layer package -> module prefixes it must never import
FORBIDDEN_IMPORTS = {
    "domain": (*FRAMEWORKS, "pydantic", "src.application", "src.infrastructure", "src.presentation"),
    "application": (*FRAMEWORKS, "src.infrastructure", "src.presentation"),
    "infrastructure": ("fastapi", "src.presentation"),
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
    return modules


def layer_modules(layer: str) -> list[Path]:
    return sorted((SRC / layer).rglob("*.py"))


@pytest.mark.parametrize("layer", sorted(FORBIDDEN_IMPORTS))
def test_layer_does_not_depend_on_outer_layers(layer: str) -> None:
    forbidden = FORBIDDEN_IMPORTS[layer]
    violations = [
        f"{path.relative_to(SRC)} imports {module}"
        for path in layer_modules(layer)
        for module in imported_modules(path)
        if module.startswith(forbidden)
    ]

    assert violations == []


def test_every_layer_is_covered() -> None:
    packages = {path.name for path in SRC.iterdir() if path.is_dir() and not path.name.startswith("__")}

    assert packages == set(FORBIDDEN_IMPORTS) | {"presentation"}
