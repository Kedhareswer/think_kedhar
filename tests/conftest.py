"""Shared pytest helpers.

Provides ``setup_tmp_root`` which routes all medbrain runtime paths
(student/, brain/, dream/, exports/) under a single temp directory.
Reloads ``medbrain.config`` and ``medbrain.db`` so they pick up the new
environment.

Existing tests that historically only set ``BRAIN_DIR`` should call this
helper instead so the sibling student/, dream/, exports/ dirs also land
under the temp root rather than polluting the working tree.
"""
from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _disable_citation_gate_in_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mocked LLM bodies in regen tests do not include `[c:<id>]` citations.
    Force the gate off so the existing fixtures keep working. Real prod runs
    leave MEDBRAIN_REGEN_GATE_DISABLE unset and get the full safety check.
    Citation-gate behavior itself is tested directly in test_citation_gate.py
    (which clears this env via monkeypatch.delenv)."""
    monkeypatch.setenv("MEDBRAIN_REGEN_GATE_DISABLE", "1")


def setup_tmp_root(monkeypatch: pytest.MonkeyPatch, tmp: Path) -> Path:
    monkeypatch.setenv("MEDBRAIN_ROOT", str(tmp))
    monkeypatch.setenv("STUDENT_DIR", str(tmp / "student"))
    monkeypatch.setenv("BRAIN_DIR", str(tmp / "brain"))
    monkeypatch.setenv("DREAM_DIR", str(tmp / "dream"))
    monkeypatch.setenv("EXPORTS_DIR", str(tmp / "exports"))

    import medbrain.config as config_mod
    import medbrain.db as db_mod

    importlib.reload(config_mod)
    importlib.reload(db_mod)
    return tmp
