"""Codex CLI adapter: invoke `codex exec` headless, capture + normalize.

Isolation notes specific to this adapter:
  - `env` passed in by run.py already has CODEX_HOME pointed at a fresh,
    empty per-run directory — never the operator's real ~/.codex.
  - No `codex exec resume` is ever used. Every invocation starts a brand new
    session with no memory of any other run.
  - Sandbox: `--dangerously-bypass-approvals-and-sandbox` is the default here
    (Ahmed's decision, 2026-07-06), behind the same `_require_container()`
    guard as Claude's bypassPermissions. This was NOT the original design —
    `-s workspace-write` (Codex's own internal sandbox) was tried first, on
    the theory that it's documented as safe for unattended use without
    needing external containment. A real pilot run proved that wrong inside
    Docker specifically: workspace-write shells out through bubblewrap to
    create a Linux user namespace, and Docker's default container security
    profile blocks that outright ("bwrap: No permissions to create a new
    namespace"), regardless of root vs. non-root — every command failed
    before running. Since this container already IS the external sandbox
    boundary (network and filesystem scoped, ephemeral, never reused across
    runs), asking Codex to also nest its own sandbox inside it was redundant
    even before it broke — matching what Codex's own docs say the
    dangerous-bypass flag is "intended solely for."

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
    # Default ON (Ahmed's 2026-07-06 decision) — set to "0" to force Codex's
    # own workspace-write sandbox instead (known broken under Docker, kept
    # only for comparison/debugging on a host where it might actually work).
    use_dangerous_bypass = os.environ.get("BOMLY_STUDY_CODEX_DANGEROUS_BYPASS", "1") == "1"
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
    stderr_text = ""
    stderr_path = raw_transcript_path.with_suffix(raw_transcript_path.suffix + ".stderr.log")
    # See claude.py for why this is always captured: a fast, silent failure
    # writes nothing useful to stdout, and stderr used to be discarded here.
    with open(raw_transcript_path, "w") as raw_f, open(stderr_path, "w") as err_f:
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
            stderr_text = proc.stderr
            err_f.write(stderr_text)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired as e:
            timed_out = True
            if e.stdout:
                out = e.stdout if isinstance(e.stdout, str) else e.stdout.decode("utf-8", "replace")
                raw_f.write(out)
                raw_lines = out.splitlines()
            if e.stderr:
                stderr_text = e.stderr if isinstance(e.stderr, str) else e.stderr.decode("utf-8", "replace")
                err_f.write(stderr_text)

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
        # Real schema, confirmed against actual pilot-run transcripts (this
        # was originally guessed and wrong — see below): the OUTER type is
        # thread.started / turn.started / turn.completed / item.started /
        # item.completed. The interesting content (what kind of item this
        # is — a shell command, an agent message, an MCP tool call) is
        # NESTED at ev["item"]["type"], never at the top level. The first
        # version of this parser matched substrings against the OUTER type
        # only, so "item.completed"/"item.started" (containing neither
        # "turn" nor "tool"/"function_call"/"command") fell through to
        # "unknown" every time — only turn.started/turn.completed happened
        # to contain "turn", so turns counted correctly by accident while
        # tool_calls and mcp_calls silently stayed at 0 for every real run
        # until this was caught by a suspiciously-zero result.
        item = ev.get("item") or {}
        item_type = str(item.get("type", ""))

        if etype == "turn.completed":
            turns += 1
            normalized_events.append({"type": "turn", "raw_type": etype})
        elif etype == "item.completed" and item_type == "command_execution":
            tool_calls += 1
            failed = item.get("status") == "failed" or (item.get("exit_code") not in (None, 0))
            normalized_events.append(
                {"type": "tool_call", "tool": item.get("command", ""), "is_mcp": False, "failed": failed}
            )
        elif etype == "item.completed" and item_type == "mcp_tool_call":
            tool_calls += 1
            mcp_calls += 1
            tool_name = f"{item.get('server', '')}/{item.get('tool', '')}"
            if item.get("error"):
                mcp_tool_errors.append({"tool": tool_name, "error": str(item.get("error"))[:500]})
            normalized_events.append({"type": "tool_call", "tool": tool_name, "is_mcp": True})
        elif etype == "item.completed" and item_type == "agent_message":
            normalized_events.append({"type": "text", "role": "assistant", "text": str(item.get("text", ""))[:2000]})
        elif etype in ("item.started",):
            pass  # superseded by the matching item.completed; avoid double-counting
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
        "stderr_tail": stderr_text[-2000:] if stderr_text else None,
    }
