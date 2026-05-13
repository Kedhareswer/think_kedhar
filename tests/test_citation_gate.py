"""Tests for medbrain.regen.citation_gate."""

from __future__ import annotations

import pytest

from medbrain.regen.citation_gate import check, extract_citations


def _enable_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Counter the autouse conftest fixture that disables the gate by default."""
    monkeypatch.delenv("MEDBRAIN_REGEN_GATE_DISABLE", raising=False)


def test_extract_citations_finds_8char_ids():
    body = "Foo [c:abcdef12] and bar [c:DEADBEEF]. No cite here."
    assert extract_citations(body) == {"abcdef12", "deadbeef"}


def test_extract_citations_handles_longer_prefixes():
    """Tolerant — accepts 6-16 hex; truncates to 8 for comparison."""
    body = "Long [c:abcdef1234567890] mention."
    assert extract_citations(body) == {"abcdef12"}


def test_gate_passes_when_all_inputs_cited(monkeypatch: pytest.MonkeyPatch):
    _enable_gate(monkeypatch)
    body = "Statement [c:abcdef12]. Another [c:11223344]."
    res = check(body=body, input_claim_ids=["abcdef1234", "1122334455"])
    assert res.passed
    assert res.coverage == 1.0


def test_gate_rejects_fabricated_citation(monkeypatch: pytest.MonkeyPatch):
    _enable_gate(monkeypatch)
    body = "Real [c:abcdef12]. Fake [c:ffffffff]."
    res = check(body=body, input_claim_ids=["abcdef12aa"])
    assert not res.passed
    assert "fabricated" in res.reason
    assert "ffffffff" in res.fabricated_ids


def test_gate_rejects_zero_citations_when_inputs_exist(monkeypatch: pytest.MonkeyPatch):
    _enable_gate(monkeypatch)
    body = "No citations at all."
    res = check(body=body, input_claim_ids=["abcdef12aa", "1122334455"])
    assert not res.passed
    assert "no input citations" in res.reason


def test_gate_rejects_low_coverage(monkeypatch: pytest.MonkeyPatch):
    _enable_gate(monkeypatch)
    body = "Only one [c:aaaaaaaa]."
    res = check(
        body=body,
        input_claim_ids=["aaaaaaaa11", "bbbbbbbb22", "cccccccc33", "dddddddd44"],
        min_coverage=0.5,
    )
    assert not res.passed
    assert "coverage" in res.reason
    assert res.coverage == pytest.approx(0.25)


def test_gate_passes_with_empty_input(monkeypatch: pytest.MonkeyPatch):
    _enable_gate(monkeypatch)
    res = check(body="Anything", input_claim_ids=[])
    assert res.passed
    assert res.input_count == 0


def test_gate_env_disable_short_circuits(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEDBRAIN_REGEN_GATE_DISABLE", "1")
    res = check(
        body="No citations.",
        input_claim_ids=["aaaaaaaa11", "bbbbbbbb22"],
    )
    assert res.passed
    assert "disabled" in res.reason


def test_gate_case_insensitive_ids(monkeypatch: pytest.MonkeyPatch):
    _enable_gate(monkeypatch)
    body = "Cite [c:ABCDEF12]."
    res = check(body=body, input_claim_ids=["abcdef12aa"])
    assert res.passed
