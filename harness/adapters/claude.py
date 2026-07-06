"""Claude Code adapter: invoke `claude -p` headless, capture + normalize.

Isolation notes specific to this adapter:
  - `env` passed in by run.py already has CLAUDE_CONFIG_DIR pointed at a
    fresh, empty per-run directory — never the operator's real ~/.claude.
  - No --resume / --continue is ever passed. Every invocation starts a brand
    new conversation with no memory of any other run.
  - --permission-mode bypassPermissions grants the agent full autonomy with
    no approval gates — required because a headless run has nobody to answer
    a prompt (any narrower mode risks hanging until the timeout kills it,
    corrupting timing data instead of doing real work). Per Ahmed's decision,
    that mode is only ever exercised inside the ephemeral, network/filesystem
    -scoped Docker container the study uses for real runs — see
    `_require_container()` below, which refuses to proceed otherwise. Local
    harness development against the bare host must use dry-run/inspection
    paths, not a live agent invocation.
  - --max-budget-usd is a hard per-run cost ceiling, independent of the wall-
    clock timeout, set via BOMLY_STUDY_MAX_BUDGET_USD (default modest).

Schema note: the exact shape of `--output-format stream-json` events (system /
assistant / user / result, content blocks of type text / tool_use /
tool_result) is Anthropic's documented streaming format. Parsing here is
defensive (skips anything it doesn't recognize into a raw passthrough event)
rather than assuming a rigid shape — reconfirm against one real pilot
transcript before trusting the aggregate turn/tool-call counts.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


class NotInContainerError(RuntimeError):
    pass


def _require_container() -> None:
    """Refuse to run an unattended, permission-bypassed agent outside the
    study's ephemeral Docker container. Fails closed: BOTH signals must be
    present, not just one — a stray env var on the bare host should not be
    enough to bypass this.
    """
    in_container_marker = Path("/.dockerenv").exists()
    in_container_env = os.environ.get("BOMLY_STUDY_IN_CONTAINER") == "1"
    if not (in_container_marker and in_container_env):
        raise NotInContainerError(
            "refusing to invoke claude with --permission-mode bypassPermissions "
            "outside the study's Docker container (missing /.dockerenv and/or "
            "BOMLY_STUDY_IN_CONTAINER=1). Build/run inside harness/Dockerfile, "
            "or use --dry-run for local harness development."
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
    _require_container()

    version_p = subprocess.run(["claude", "--version"], capture_output=True, text=True, env=env)
    agent_version = version_p.stdout.strip()

    # Defaults per Ahmed's 2026-07-06 decision; override with
    # BOMLY_STUDY_CLAUDE_MODEL / BOMLY_STUDY_CLAUDE_EFFORT (empty string
    # disables the corresponding flag and falls back to the CLI's own
    # default). --effort is a real Claude Code flag (low/medium/high/xhigh/max
    # — confirmed via `claude --help`), not a model-name suffix.
    model = env.get("BOMLY_STUDY_CLAUDE_MODEL", "claude-sonnet-5")
    effort = env.get("BOMLY_STUDY_CLAUDE_EFFORT", "high")
    max_budget = env.get("BOMLY_STUDY_MAX_BUDGET_USD", "5")

    cmd = [
        "claude",
        "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--permission-mode", "bypassPermissions",
        "--max-budget-usd", str(max_budget),
    ]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    if condition == "mcp" and mcp_config_path:
        cmd += ["--mcp-config", str(mcp_config_path)]

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
    final_result = None

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            normalized_events.append({"type": "unparsed", "raw": line[:500]})
            continue

        etype = ev.get("type")
        if etype in ("assistant", "user"):
            turns += 1
            message = ev.get("message", {})
            content = message.get("content", [])
            for block in content if isinstance(content, list) else []:
                btype = block.get("type")
                if btype == "text":
                    normalized_events.append({"type": "text", "role": etype, "text": block.get("text", "")[:2000]})
                elif btype == "tool_use":
                    tool_name = block.get("name", "")
                    is_mcp = tool_name.startswith("mcp__") or "bomly" in tool_name.lower()
                    tool_calls += 1
                    if is_mcp:
                        mcp_calls += 1
                    normalized_events.append(
                        {"type": "tool_call", "tool": tool_name, "is_mcp": is_mcp, "input": block.get("input", {})}
                    )
                elif btype == "tool_result":
                    if block.get("is_error"):
                        mcp_tool_errors.append(
                            {"tool": block.get("tool_use_id", ""), "error": str(block.get("content", ""))[:500]}
                        )
                    normalized_events.append({"type": "tool_result", "is_error": bool(block.get("is_error"))})
        elif etype == "result":
            final_result = ev
            normalized_events.append({"type": "final_result", "subtype": ev.get("subtype"), "is_error": ev.get("is_error")})
        else:
            normalized_events.append({"type": etype or "unknown"})

    if final_result:
        turns = final_result.get("num_turns", turns)
        model = final_result.get("model", model)

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
