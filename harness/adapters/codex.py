"""Codex CLI adapter: invoke `codex exec` headless, capture + normalize.

Isolation notes specific to this adapter:
  - `env` passed in by run.py already has CODEX_HOME pointed at a fresh,
    empty per-run directory — never the operator's real ~/.codex.
  - No `codex exec resume` is ever used. Every invocation starts a brand new
    session with no memory of any other run.
  - Sandbox: `-s workspace-write` is Codex's own OS-level sandbox, scoped to
    the workspace, and is documented as safe for unattended/agentic use
    without needing external containment — unlike Claude Code's
    bypassPermissions, this does NOT require the container guard by default.
    `sandbox_workspace_write.network_access=true` is set because the task
    needs package-registry access (npm/pip installs), matching the "full
    egress in both conditions" isolation note in cs-a-design.md.
  - `--dangerously-bypass-approvals-and-sandbox` is NOT used by default. It
    exists only as an escape hatch if workspace-write proves insufficient,
    and if ever enabled it must go through the same `_require_container()`
    guard as Claude's bypassPermissions, per Ahmed's decision — Codex's own
    docs describe that flag as "intended solely for running in environments
    that are externally sandboxed."

Schema note: Codex's `--json` JSONL event schema is less well-established here
than Claude's; this parser is defensive (buckets unrecognized event types
into a raw passthrough) and the turn/tool-call counters should be re-verified
against one real container-run transcript before the numbers are trusted.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


class NotInContainerError(RuntimeError):
    pass


def _require_container() -> None:
    in_container_marker = Path("/.dockerenv").exists()
    in_container_env = os.environ.get("BOMLY_STUDY_IN_CONTAINER") == "1"
    if not (in_container_marker and in_container_env):
        raise NotInContainerError(
            "refusing to invoke codex with --dangerously-bypass-approvals-and-sandbox "
            "outside the study's Docker container (missing /.dockerenv and/or "
            "BOMLY_STUDY_IN_CONTAINER=1)."
        )


def run(
    *,
    repo: Path,
    prompt: str,
    condition: str,
    env: dict,
    timeout_seconds: int,
    raw_transcript_path: Path,
    mcp_config_path: Path | None,
) -> dict:
    use_dangerous_bypass = os.environ.get("BOMLY_STUDY_CODEX_DANGEROUS_BYPASS") == "1"
    if use_dangerous_bypass:
        _require_container()

    version_p = subprocess.run(["codex", "--version"], capture_output=True, text=True, env=env)
    agent_version = version_p.stdout.strip()

    # Defaults per Ahmed's 2026-07-06 decision; override with
    # BOMLY_STUDY_CODEX_MODEL / BOMLY_STUDY_CODEX_EFFORT (empty string
    # disables the corresponding flag). Both values confirmed against the
    # real model catalog (`codex debug models`): slug "gpt-5.5" exists, its
    # own CLI default reasoning level is "medium", and supported levels are
    # low/medium/high/xhigh. The config key `model_reasoning_effort` was
    # confirmed by inspecting strings in the installed codex binary — not
    # documented in `--help`, so this is worth re-checking against a newer
    # Codex CLI release before assuming it still applies.
    model = env.get("BOMLY_STUDY_CODEX_MODEL", "gpt-5.5")
    effort = env.get("BOMLY_STUDY_CODEX_EFFORT", "medium")

    cmd = ["codex", "exec", prompt, "--json"]
    if use_dangerous_bypass:
        cmd += ["--dangerously-bypass-approvals-and-sandbox"]
    else:
        cmd += ["-s", "workspace-write", "-c", "sandbox_workspace_write.network_access=true"]
    if model:
        cmd += ["-m", model]
    if effort:
        cmd += ["-c", f'model_reasoning_effort="{effort}"']
    # mcp_config_path is unused here: unlike Claude's --mcp-config flag, Codex
    # reads MCP servers from $CODEX_HOME/config.toml. run.py registers the
    # bomly server via `codex mcp add` against this run's fresh CODEX_HOME
    # before invoking this adapter, so no per-invocation flag is needed.
    _ = mcp_config_path

    timed_out = False
    raw_lines: list[str] = []
    exit_code = None
    with open(raw_transcript_path, "w") as raw_f:
        try:
            proc = subprocess.run(
                cmd,
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            raw_f.write(proc.stdout)
            raw_lines = proc.stdout.splitlines()
            exit_code = proc.returncode
        except subprocess.TimeoutExpired as e:
            timed_out = True
            if e.stdout:
                out = e.stdout if isinstance(e.stdout, str) else e.stdout.decode("utf-8", "replace")
                raw_f.write(out)
                raw_lines = out.splitlines()

    normalized_events = []
    turns = 0
    tool_calls = 0
    mcp_calls = 0
    mcp_tool_errors = []

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            normalized_events.append({"type": "unparsed", "raw": line[:500]})
            continue

        etype = ev.get("type", "")
        # Defensive bucketing — Codex's JSONL schema uses event names like
        # "item.completed"/"turn.completed"/etc; match loosely on substrings
        # rather than assuming an exact enum, and record everything so the
        # raw transcript remains the source of truth regardless.
        lower = etype.lower()
        if "turn" in lower:
            turns += 1
            normalized_events.append({"type": "turn", "raw_type": etype})
        elif "tool" in lower or "function_call" in lower or "command" in lower:
            tool_name = ev.get("name") or ev.get("tool") or ev.get("command", "")
            is_mcp = "mcp" in lower or "bomly" in str(tool_name).lower()
            tool_calls += 1
            if is_mcp:
                mcp_calls += 1
            if ev.get("error") or ev.get("is_error"):
                mcp_tool_errors.append({"tool": str(tool_name), "error": str(ev.get("error") or "")[:500]})
            normalized_events.append({"type": "tool_call", "tool": str(tool_name), "is_mcp": is_mcp})
        elif "message" in lower or "text" in lower:
            normalized_events.append({"type": "text", "raw_type": etype, "text": str(ev.get("text", ""))[:2000]})
        else:
            normalized_events.append({"type": etype or "unknown"})

    return {
        "agent_version": agent_version,
        "model": model,
        "effort": effort or None,
        "exit_code": exit_code,
        "timeout": timed_out,
        "turns": turns,
        "tool_calls": tool_calls,
        "mcp_calls": mcp_calls,
        "mcp_tool_errors": mcp_tool_errors,
        "normalized_events": normalized_events,
    }
