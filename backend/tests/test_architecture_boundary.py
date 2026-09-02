import ast
from pathlib import Path


FORBIDDEN = {"cubeai.api", "cubeai.adapters", "fastapi", "sqlite3", "httpx", "requests"}
DOMAIN_ROOT = Path(__file__).parents[1] / "src" / "cubeai" / "lab" / "domain"


def forbidden_imports(source: str) -> set[str]:
    tree = ast.parse(source)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names if alias.name in FORBIDDEN)
        elif isinstance(node, ast.ImportFrom) and node.module in FORBIDDEN:
            found.add(node.module)
    return found


def test_domain_has_no_forbidden_outer_imports() -> None:
    found = set()
    for path in DOMAIN_ROOT.rglob("*.py"):
        found.update(forbidden_imports(path.read_text(encoding="utf-8")))
    assert found == set()


def test_controlled_forbidden_probe_is_detected() -> None:
    assert forbidden_imports("import sqlite3\nfrom fastapi import FastAPI\n") == {
        "sqlite3",
        "fastapi",
    }
