"""Shared fixtures for site tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def index_html(repo_root: Path) -> str:
    return (repo_root / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def centros_html(repo_root: Path) -> str:
    return (repo_root / "centros" / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def axed_html(repo_root: Path) -> str:
    path = repo_root / "axed" / "index.html"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def references_html(repo_root: Path) -> str:
    path = repo_root / "references" / "index.html"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
