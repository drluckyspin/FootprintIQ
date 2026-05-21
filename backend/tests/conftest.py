"""Shared pytest fixtures.

`fixtures_dir` always points at the repo's tests/fixtures/ regardless of cwd.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def sample_addresses_csv(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_addresses.csv"
