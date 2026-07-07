#!/usr/bin/env python3
"""Orchestrate the full N-per-cell study matrix — resumable by design.

Motivation: at N=5 (2 agents x 2 conditions x 5 = 20 runs), hitting a
subscription/session usage limit partway through is a real, expected
possibility, not an edge case. Re-invoking this script after ANY
interruption (session limit, crash, killed process, laptop sleep) must pick
up exactly where it left off — never redo already-valid runs, never require
figuring out by hand which cells are missing.

Usage:
  harness/run_study.py --agents claude,codex --conditions bare,mcp --n 5 --scope all
  harness/run_study.py --dry-run   # just print the plan, run nothing

Safe to re-invoke any number of times. Each invocation:
  1. Enumerates the full (agent, condition, run_number) matrix.
  2. For each cell, checks whether a VALID result already exists (see
     _cell_status below — this is more than "does result.json exist": a run
     truncated by a dropped API connection mid-task still writes a
     syntactically valid result.json full of NOT_ATTEMPTED, which is not a
     real data point and must not be silently accepted as "done").
  3. Skips valid cells, (re)runs everything else, one at a time.
  4. Prints a clear pending/done summary before and after, so a resumed run
     is transparent about what it's about to do.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Text signatures of a run truncated by a transient network/API failure
# rather than genuine agent behavior — found via a real pilot run where a
# dropped connection mid-task left an agent with 27 real tool calls, zero
# diff, and one of these exact phrases in its final result text. A run with
# a nonzero diff or a written FIXES.md is NOT flagged even if one of these
# phrases also appears somewhere (real runs can legitimately mention
# connection issues while investigating network-facing code) — the
# combination of {no real output} + {error phrase} is what actually
# indicates a truncated, invalid run.
TRUNCATION_SIGNATURES = (
    "api error",
    "connection closed",
    "connection reset",
    "overloaded_error",
    "rate_limit_error",
    "usage limit",
    "quota exceeded",
)


def _cell_dir(runs_root: Path, agent: str, condition: str, n: int) -> Path:
    return runs_root / agent / condition / str(n)


def _cell_status(cell_dir: Path) -> tuple[str, str]:
    """Returns (status, reason). status is 'valid', 'missing', or 'invalid'.

    Deliberately does NOT treat `timeout: true` or a nonzero `exit_code` in
    meta.json as invalid — both are legitimate, pre-registered outcomes for
    this study (a real 45-minute timeout is scored as TIMEOUT, not retried;
    Claude Code can exit nonzero purely because an MCP tool call errored
    mid-session, which the design already records as `mcp_tool_errors` data
    rather than a failure — confirmed against a real pilot run,
    runs-pilot/claude/mcp/2, which has exit_code=1 and 3 mcp_tool_errors but
    is a fully valid run with a real diff and 6 slots FIXED). The only
    invalid case is a run that produced no real output at all — including
    the one known failure mode, a dropped API connection truncating the
    agent mid-task (result.json still gets written in that case, just full
    of NOT_ATTEMPTED, which is not a trustworthy data point).
    """
    result_path = cell_dir / "result.json"
    meta_path = cell_dir / "meta.json"
    if not result_path.exists() or not meta_path.exists():
        return "missing", "no result.json/meta.json yet"

    try:
        json.loads(meta_path.read_text())
    except (json.JSONDecodeError, OSError):
        return "invalid", "meta.json unreadable"

    diff_path = cell_dir / "diff.patch"
    fixes_path = cell_dir / "FIXES.md"
    has_real_output = (diff_path.exists() and diff_path.stat().st_size > 0) or (
        fixes_path.exists() and fixes_path.stat().st_size > 0
    )
    if not has_real_output:
        transcript_path = cell_dir / "transcript.raw.jsonl"
        stderr_path = cell_dir / "transcript.raw.jsonl.stderr.log"
        text = ""
        if transcript_path.exists():
            text += transcript_path.read_text(errors="replace").lower()
        if stderr_path.exists():
            text += stderr_path.read_text(errors="replace").lower()
        if any(sig in text for sig in TRUNCATION_SIGNATURES):
            return "invalid", "empty diff/FIXES.md + network-truncation signature in transcript"
        return "invalid", "empty diff.patch and empty FIXES.md — no real agent output"

    return "valid", "ok"


def build_matrix(agents: list[str], conditions: list[str], n: int) -> list[tuple[str, str, int]]:
    return [(a, c, i) for a in agents for c in conditions for i in range(1, n + 1)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", default="claude,codex")
    ap.add_argument("--conditions", default="bare,mcp")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--scope", default="all")
    ap.add_argument("--pilot", action="store_true", help="Write to runs-pilot/ instead of runs/")
    ap.add_argument("--dry-run", action="store_true", help="Print the plan only; run nothing")
    args = ap.parse_args()

    agents = [a.strip() for a in args.agents.split(",") if a.strip()]
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    matrix = build_matrix(agents, conditions, args.n)
    runs_root = REPO_ROOT / ("runs-pilot" if args.pilot else "runs")

    statuses = {}
    for agent, condition, n in matrix:
        statuses[(agent, condition, n)] = _cell_status(_cell_dir(runs_root, agent, condition, n))

    valid = [k for k, (status, _) in statuses.items() if status == "valid"]
    pending = [k for k, (status, _) in statuses.items() if status != "valid"]

    print(f"Matrix: {len(agents)} agent(s) x {len(conditions)} condition(s) x N={args.n} = {len(matrix)} cells")
    print(f"  already valid: {len(valid)}")
    print(f"  pending (missing or invalid): {len(pending)}")
    for agent, condition, n in pending:
        status, reason = statuses[(agent, condition, n)]
        print(f"    {agent:8} {condition:5} run {n} — {status} ({reason})")

    if args.dry_run:
        print("\n--dry-run: stopping here, nothing executed.")
        return 0

    if not pending:
        print("\nNothing to do — every cell already has a valid result.")
        return 0

    print(f"\nRunning {len(pending)} cell(s)...\n")
    failures = []
    for i, (agent, condition, n) in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] {agent} {condition} run {n} ...")
        cmd = [str(REPO_ROOT / "harness" / "run.sh"), agent, condition, str(n), "--scope", args.scope]
        if args.pilot:
            cmd.append("--pilot")
        proc = subprocess.run(cmd)
        status, reason = _cell_status(_cell_dir(runs_root, agent, condition, n))
        if status != "valid":
            print(
                f"  -> still {status} after running ({reason}; harness exit code {proc.returncode}) "
                "— will retry on next invocation"
            )
            failures.append((agent, condition, n))
        else:
            print("  -> valid")

    print(f"\nDone this pass: {len(pending) - len(failures)}/{len(pending)} succeeded.")
    if failures:
        print(f"{len(failures)} cell(s) still need a retry — just re-run this same command:")
        for agent, condition, n in failures:
            print(f"    {agent} {condition} run {n}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
