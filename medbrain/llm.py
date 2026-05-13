"""Claude CLI subprocess wrapper.

Each LLM call spawns `claude --print ...` non-interactively. Uses the user's
Claude Max subscription via the installed CLI; no API key needed. Heavier
per-call than direct SDK (subprocess + auth roundtrip) but matches the
existing student-session pattern and reserves the option of giving agents
the full Claude Code tool environment later.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from medbrain.config import BRAIN_DIR, LLM_MODEL

LLM_DEBUG_DIR = BRAIN_DIR / ".llm-debug"
LLM_DEBUG = os.getenv("MEDBRAIN_LLM_DEBUG", "1") not in ("0", "false", "")

# Thinking-budget magic phrase prepended to every user prompt.
# Claude Code CLI honors: "think" | "think hard" | "think harder" | "ultrathink".
# Empty string disables.
THINKING_HINT = os.getenv("MEDBRAIN_THINKING_HINT", "ultrathink").strip()


class LLMError(RuntimeError):
    pass


# Env vars stripped before spawning to avoid nested-instance conflicts when
# MedBrain itself is invoked from a Claude Code session.
_STRIP_ENV = {
    "CLAUDECODE",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_SSE_PORT",
    "CLAUDE_CODE_DEV",
    "ANTHROPIC_API_KEY",
}


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _STRIP_ENV}


def _resolve_cli() -> str:
    """Find claude CLI executable. Returns full path; errors clearly if missing.

    On Windows, prefer `claude.cmd` over the bare `claude` shim. The npm-global
    `claude` resolves to `claude.ps1`, which a default PowerShell ExecutionPolicy
    (`Restricted`) refuses to run, breaking every LLM call. `claude.cmd` is a
    plain batch wrapper and bypasses the policy entirely.
    """
    if platform.system() == "Windows":
        exe = shutil.which("claude.cmd") or shutil.which("claude.exe") or shutil.which("claude")
    else:
        exe = shutil.which("claude")
    if exe is None:
        raise LLMError(
            "Claude CLI ('claude') not found on PATH. "
            "Install Claude Code: https://claude.ai/code"
        )
    return exe


def call(
    system: str,
    user: str,
    *,
    model: str | None = None,
    timeout: float = 180.0,
    cwd: str | None = None,
) -> str:
    """Single non-interactive Claude CLI call. Returns stdout text.

    Uses --print (non-interactive) + --append-system-prompt + --output-format text.
    """
    exe = _resolve_cli()
    mdl = model or LLM_MODEL
    if THINKING_HINT:
        user = f"{THINKING_HINT}\n\n{user}"
    # Pipe user prompt via stdin. Avoids "Input must be provided either through
    # stdin or as a prompt argument" when --append-system-prompt eats the
    # positional slot, and dodges Windows command-line length limits for big
    # user prompts (e.g. compaction passes whole .md files).
    #
    # Pure-inference invocation — MedBrain wants the model to obey OUR prompt,
    # not Claude Code's default conversational behaviour:
    # - --system-prompt     REPLACE system prompt (not append). Without this our
    #                       JSON-only directive gets diluted by the default
    #                       Claude Code system prompt.
    #                       NB: --bare would also help but it disables keychain
    #                       reads, killing Claude Max OAuth. Avoid.
    # - --allowed-tools ""  empty allow-list = no built-in tools available
    # - --disallowed-tools "*"  explicit deny-all (defence in depth)
    # - --strict-mcp-config ignore user-level MCP servers (PubMed, ChEMBL etc.
    #                       defined in user settings won't auto-load and trigger
    #                       permission prompts).
    # - --permission-mode plan  read-only; tool attempts error instead of
    #                       prompting interactively (would block the subprocess).
    cmd = [
        exe,
        "--print",
        "--model", mdl,
        "--system-prompt", system,
        "--output-format", "text",
        "--allowed-tools", "",
        "--disallowed-tools", "*",
        "--strict-mcp-config",
    ]
    try:
        proc = subprocess.run(
            cmd,
            input=user,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_clean_env(),
            cwd=cwd,
            shell=False,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired as e:
        raise LLMError(f"Claude CLI timeout after {timeout}s") from e
    if proc.returncode != 0:
        raise LLMError(
            f"Claude CLI exit {proc.returncode}: {proc.stderr.strip()[:500]}"
        )
    out = proc.stdout.strip()
    _debug_dump(system=system, user=user, raw=out, stderr=proc.stderr or "")
    return out


def _debug_dump(*, system: str, user: str, raw: str, stderr: str) -> None:
    """Write the last LLM exchange to brain/.llm-debug/ for inspection."""
    if not LLM_DEBUG:
        return
    try:
        LLM_DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
        path = LLM_DEBUG_DIR / f"{ts}.txt"
        path.write_text(
            "===== SYSTEM =====\n"
            + system
            + "\n\n===== USER =====\n"
            + user
            + "\n\n===== STDOUT =====\n"
            + raw
            + ("\n\n===== STDERR =====\n" + stderr if stderr.strip() else "")
            + "\n",
            encoding="utf-8",
        )
        # Always overwrite a stable "last.txt" pointer for quick `type` access.
        (LLM_DEBUG_DIR / "last.txt").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    except OSError:
        pass  # debug log must never break the call


_JSON_PREAMBLE = (
    "OUTPUT REQUIREMENT: Return VALID JSON ONLY. "
    "Your entire response must be parseable by json.loads(). "
    "First character of your output must be `{` or `[`. "
    "No prose. No explanations. No markdown fences. No apologies. "
    "If the requested data is unavailable, return the schema with empty/null values, "
    "still as valid JSON. Tools are intentionally disabled — do not request access to them.\n\n"
)

_FIRST_OBJ = re.compile(r"\{.*\}|\[.*\]", re.DOTALL)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        first_nl = text.find("\n")
        if first_nl > 0:
            text = text[first_nl + 1 :]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return text


def _extract_json_blob(text: str) -> str | None:
    """Find the largest balanced {...} or [...] substring. Tolerates LLM preamble/coda."""
    text = _strip_fences(text)
    m = _FIRST_OBJ.search(text)
    return m.group(0) if m else None


def call_json(
    system: str,
    user: str,
    *,
    model: str | None = None,
    timeout: float = 180.0,
    cwd: str | None = None,
) -> Any:
    """Call expecting JSON. Strips fences and tolerates surrounding prose.

    Strategy:
      1. Prepend a hard JSON-only preamble to the system prompt.
      2. Try strict json.loads on the stripped output.
      3. On failure, regex-extract the first {...} or [...] blob and try again.
      4. On final failure, raise LLMError with the raw output's location on disk.
    """
    raw = call(_JSON_PREAMBLE + system, user, model=model, timeout=timeout, cwd=cwd)
    text = _strip_fences(raw)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    blob = _extract_json_blob(text)
    if blob is not None:
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            pass

    debug_hint = (
        f" Raw output saved to {LLM_DEBUG_DIR / 'last.txt'}." if LLM_DEBUG else ""
    )
    raise LLMError(
        f"Claude CLI did not return valid JSON.{debug_hint}\nRaw[:500]: {raw[:500]}"
    )
