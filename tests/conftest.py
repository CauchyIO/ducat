"""Shared fixtures: the two scripts loaded as modules, and a fixed date."""

from datetime import date
from pathlib import Path
from types import ModuleType

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"


def _load(name: str) -> ModuleType:
    """The scripts have hyphenated names, so they cannot be imported the normal way.

    Compiled from source rather than through a loader so no bytecode cache is
    written or trusted: the scripts are tiny, and a stale cache is one more way for
    a test to pass against code that no longer exists.
    """
    path = TOOLS / f"{name}.py"
    module = ModuleType(name)
    module.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), module.__dict__)
    return module


@pytest.fixture(scope="session")
def check_package() -> ModuleType:
    """The credential and identifier scanner, loaded once for the whole run."""
    return _load("check-package")


@pytest.fixture(scope="session")
def check_consistency() -> ModuleType:
    """The review-date, price, link and routing checker, loaded once for the whole run."""
    return _load("check-consistency")


@pytest.fixture
def today(check_consistency: ModuleType, monkeypatch: pytest.MonkeyPatch) -> date:
    """Pin the script's notion of today so date arithmetic is stable."""
    fixed = date(2026, 9, 4)
    monkeypatch.setattr(check_consistency, "TODAY", fixed)
    return fixed
