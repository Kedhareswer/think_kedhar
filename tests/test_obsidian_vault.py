"""Tests for medbrain.exporters.obsidian_vault."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


def _setup(monkeypatch: pytest.MonkeyPatch) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="medbrain-vault-"))
    from tests.conftest import setup_tmp_root
    return setup_tmp_root(monkeypatch, tmp)


def test_publish_to_vault_writes_brain_artifacts(monkeypatch: pytest.MonkeyPatch):
    root = _setup(monkeypatch)
    from medbrain import config
    from medbrain.exporters.obsidian_vault import publish_to_vault

    config.ensure_brain_dirs()
    config.MEMORY_FILE.write_text("# brain memory\n", encoding="utf-8")
    config.QUESTIONS_FILE.write_text(
        "# Questions\n\n## Q-2026-05-13-001\n- priority: 1\n- status: open\n- created: 2026-05-13T00:00:00+00:00\n- topic: t\n\nbody?\n",
        encoding="utf-8",
    )

    res = publish_to_vault()
    assert res.errors == []
    vault_brain = config.STUDENT_DIR / "_brain"
    assert (vault_brain / "memory.md").read_text() == "# brain memory\n"
    assert (vault_brain / "questions.md").exists()


def test_publish_to_vault_skips_missing_sources(monkeypatch: pytest.MonkeyPatch):
    """Cold start (no brain artifacts yet) reports skipped, not errored."""
    root = _setup(monkeypatch)
    from medbrain import config
    from medbrain.exporters.obsidian_vault import publish_to_vault

    config.ensure_brain_dirs()
    res = publish_to_vault()
    assert res.errors == []
    # Memory and questions are missing on cold start
    assert any("memory.md" in s for s in res.files_skipped)
    assert any("questions.md" in s for s in res.files_skipped)


def test_publish_to_vault_handles_dream_artifacts(monkeypatch: pytest.MonkeyPatch):
    root = _setup(monkeypatch)
    from medbrain import config
    from medbrain.exporters.obsidian_vault import publish_to_vault

    config.ensure_brain_dirs()
    (config.MNEMONICS_DIR / "artemisinin.md").write_text("# mnemonic\n", encoding="utf-8")
    (config.ANALOGIES_DIR / "k13.md").write_text("# analogy\n", encoding="utf-8")
    (config.GAPS_DIR / "vivax.md").write_text("# gap\n", encoding="utf-8")

    res = publish_to_vault()
    vault_dream = config.STUDENT_DIR / "_dream"
    assert (vault_dream / "mnemonics" / "artemisinin.md").exists()
    assert (vault_dream / "analogies" / "k13.md").exists()
    assert (vault_dream / "gaps" / "vivax.md").exists()


def test_write_vault_index(monkeypatch: pytest.MonkeyPatch):
    root = _setup(monkeypatch)
    from medbrain import config
    from medbrain.exporters.obsidian_vault import write_vault_index

    config.ensure_brain_dirs()
    idx = write_vault_index()
    assert idx.exists()
    body = idx.read_text(encoding="utf-8")
    assert "type: index" in body
    assert "[[_brain/memory" in body
    assert "_dream/" in body
