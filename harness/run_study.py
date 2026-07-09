#!/usr/bin/env python3
"""Orchestrate the full N-per-cell study matrix — resumable by design.

Motivation: at N=5 (2 agents x 2 conditions x 3 fixtures x 5 = 60 sessions),
hitting a subscription/session usage limit partway through is a real,
expected possibility, not an edge case. Re-invoking this script after ANY
interruption (session limit, crash, killed process, laptop sleep) must pick
up exactly where it left off — never redo already-valid runs, never require
figuring out by hand which cells are missing.

Usage:
  harness/run_study.py --agents claude,codex --conditions bare,mcp --scopes webapp,service,api-java --n 5
  harness/run_study.py --dry-run   # just print the plan, run nothing

v2 protocol: every cell is ONE fixture in its own agent session
(agent x condition x scope x n), so the ladder's easy/medium/hard rungs are
measured independently and an interruption costs one fixture-session, not
three. The hard fixture (api-java) gets a longer per-session timeout.

Safe to re-invoke any number of times. Each invocation:
  1. Enumerates the full (agent, condition, scope, run_number) matrix.
  2. For each cell, checks whether a VALID result already exists (see
     _cell_status below). Three non-valid states, all retryable but reported
     distinctly: 'missing' (never run), 'incomplete' (v3, 2026-07-09 — the
     session actually ran and hit a real usage/rate limit or dropped
     connection mid-task; harness/run.py detects this and skips scoring
     entirely, so it's never mistaken for a real low-completeness result),
     'invalid' (ran, produced no real output, and no incomplete signal
     explains why).
  3. Skips valid cells, (re)runs everything else, one at a time.
  4. Prints a clear pending/done summary before and after, so a resumed run
     is transparent about what it's about to do — and distinguishes "still
     waiting on a usage-limit reset" (expected, exit code 2) from "something
     is actually broken" (exit code 1).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "harness"))
from adapters import signals  # noqa: E402 — see harness/adapters/signals.py:
# the phrase list this module used to keep locally (TRUNCATION_SIGNATURES) is
# now shared with both agent adapters, which detect the same signal at
# capture time (v3, 2026-07-09) rather than this orchestrator being the only
# place it's checked. Kept here too as a second line of defense — a run
# where the adapter-level check somehow missed it can still be caught from
# the same transcript text after the fact.


# Per-session timeout, seconds. The hard fixture (api-java: a real Maven app
# with a 200-400 artifact tree) legitimately needs longer than the default 45
# minutes; the easy/medium rungs don't.
SCOPE_TIMEOUT_SECONDS = {"api-java": 75 * 60}
DEFAULT_TIMEOUT_SECONDS = 45 * 60


def _cell_dir(runs_root: Path, agent: str, condition: str, scope: str, n: int) -> Path:
    return runs_root / agent / condition / scope / str(n)


def _cell_status(cell_dir: Path) -> tuple[str, str]:
    """Returns (status, reason). status is 'valid', 'missing', 'incomplete',
    or 'invalid'. 'incomplete' and 'missing' are both retryable (treated as
    pending by main() below); the distinction is purely for operator
    visibility — an incomplete session actually ran and hit a real usage/
    rate limit, a missing one just hasn't been attempted (or attempted) yet.

    Deliberately does NOT treat `timeout: true` or a nonzero `exit_code` in
    meta.json as invalid — both are legitimate, pre-registered outcomes for
    this study (a real 45-minute timeout is scored as TIMEOUT, not retried;
    Claude Code can exit nonzero purely because an MCP tool call errored
    mid-session, which the design already records as `mcp_tool_errors` data
    rather than a failure — confirmed against a real pilot run,
    runs-pilot/claude/mcp/2, which has exit_code=1 and 3 mcp_tool_errors but
    is a fully valid run with a real diff and 6 slots FIXED).
    """
    meta_path = cell_dir / "meta.json"
    if not meta_path.exists():
        return "missing", "no meta.json yet — never run"

    try:
        meta = json.loads(meta_path.read_text())
    except (json.JSONDecodeError, OSError):
        return "invalid", "meta.json unreadable"

    # v3 (2026-07-09, Ahmed): a session cut short by a usage/rate limit or
    # dropped connection is INCOMPLETE, not scored, and always retryable —
    # harness/run.py detects this at capture time (harness/adapters/signals.py)
    # and skips scoring entirely for it, so it never gets a result.json at
    # all. Checked before result_path.exists() below specifically so this
    # reads as "ran, got interrupted" rather than being lumped into the
    # generic "missing" bucket a genuinely never-attempted cell would show.
    if meta.get("incomplete_reason"):
        return "incomplete", f"session cut short ({meta['incomplete_reason']}) — retry after the usage limit resets"

    result_path = cell_dir / "result.json"
    if not result_path.exists():
        return "missing", "meta.json present but no result.json — run didn't finish scoring"

    diff_path = cell_dir / "diff.patch"
    fixes_path = cell_dir / "FIXES.md"
    has_real_output = (diff_path.exists() and diff_path.stat().st_size > 0) or (
        fixes_path.exists() and fixes_path.stat().st_size > 0
    )
    transcript_path = cell_dir / "transcript.raw.jsonl"
    stderr_path = cell_dir / "transcript.raw.jsonl.stderr.log"
    text = ""
    if transcript_path.exists():
        text += transcript_path.read_text(errors="replace").lower()
    if stderr_path.exists():
        text += stderr_path.read_text(errors="replace").lower()
    # Checked unconditionally, not just when output is empty: an incomplete
    # signal the adapter missed (older run, or a genuinely new phrasing) can
    # still show up in a run that also has SOME real diff/FIXES.md content
    # from before the interruption — that partial content doesn't make it a
    # trustworthy data point for a "fix everything" completeness score.
    if signals.detect_incomplete_reason(text):
        return "incomplete", "network/usage-limit signature found in transcript (adapter-level check missed it)"
    if not has_real_output:
        return "invalid", "empty diff.patch and empty FIXES.md — no real agent output"

    return "valid", "ok"


def build_matrix(agents: list[str], conditions: list[str], scopes: list[str], n: int) -> list[tuple[str, str, str, int]]:
    return [(a, c, s, i) for a in agents for c in conditions for s in scopes for i in range(1, n + 1)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", default="claude,codex")
    ap.add_argument("--conditions", default="bare,mcp")
    ap.add_argument("--scopes", default="webapp,service,api-java")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--pilot", action="store_true", help="Write to runs-pilot/ instead of runs/")
    ap.add_argument("--dry-run", action="store_true", help="Print the plan only; run nothing")
    args = ap.parse_args()

    agents = [a.strip() for a in args.agents.split(",") if a.strip()]
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    scopes = [s.strip() for s in args.scopes.split(",") if s.strip()]
    matrix = build_matrix(agents, conditions, scopes, args.n)
    runs_root = REPO_ROOT / ("runs-pilot" if args.pilot else "runs")

    statuses = {}
    for agent, condition, scope, n in matrix:
        statuses[(agent, condition, scope, n)] = _cell_status(_cell_dir(runs_root, agent, condition, scope, n))

    valid = [k for k, (status, _) in statuses.items() if status == "valid"]
    incomplete = [k for k, (status, _) in statuses.items() if status == "incomplete"]
    pending = [k for k, (status, _) in statuses.items() if status != "valid"]

    print(
        f"Matrix: {len(agents)} agent(s) x {len(conditions)} condition(s) x "
        f"{len(scopes)} fixture(s) x N={args.n} = {len(matrix)} sessions"
    )
    print(f"  already valid: {len(valid)}")
    print(f"  pending (missing/invalid/incomplete): {len(pending)}")
    if incomplete:
        # Called out separately from missing/invalid: these sessions
        # actually ran and hit a real usage/rate limit mid-task — expected
        # at N=5's scale, not a harness problem, and re-running this same
        # command after the limit resets is the entire fix.
        print(f"    ({len(incomplete)} of those hit a usage/rate limit — expected, just re-run after it resets)")
    for agent, condition, scope, n in pending:
        status, reason = statuses[(agent, condition, scope, n)]
        print(f"    {agent:8} {condition:5} {scope:9} run {n} — {status} ({reason})")

    if args.dry_run:
        print("\n--dry-run: stopping here, nothing executed.")
        return 0

    if not pending:
        print("\nNothing to do — every cell already has a valid result.")
        return 0

    print(f"\nRunning {len(pending)} session(s)...\n")
    failures = []
    for i, (agent, condition, scope, n) in enumerate(pending, 1):
        timeout = SCOPE_TIMEOUT_SECONDS.get(scope, DEFAULT_TIMEOUT_SECONDS)
        print(f"[{i}/{len(pending)}] {agent} {condition} {scope} run {n} (timeout {timeout // 60}m) ...")
        cmd = [
            str(REPO_ROOT / "harness" / "run.sh"),
            agent, condition, str(n),
            "--scope", scope,
            "--timeout", str(timeout),
        ]
        if args.pilot:
            cmd.append("--pilot")
        proc = subprocess.run(cmd)
        status, reason = _cell_status(_cell_dir(runs_root, agent, condition, scope, n))
        if status != "valid":
            print(
                f"  -> still {status} after running ({reason}; harness exit code {proc.returncode}) "
                "— will retry on next invocation"
            )
            failures.append((agent, condition, scope, n, status))
        else:
            print("  -> valid")

    still_incomplete = [f for f in failures if f[4] == "incomplete"]
    still_broken = [f for f in failures if f[4] != "incomplete"]

    print(f"\nDone this pass: {len(pending) - len(failures)}/{len(pending)} succeeded.")
    if failures:
        print(f"{len(failures)} session(s) still need a retry — just re-run this same command:")
        for agent, condition, scope, n, status in failures:
            print(f"    {agent} {condition} {scope} run {n} ({status})")
    if still_incomplete and not still_broken:
        # Every remaining session is retryable-and-expected (still inside a
        # usage/rate-limit window), not a real harness problem — a distinct
        # exit code so an automated caller (or a human skimming CI-style
        # output) doesn't treat "waiting for a limit to reset" the same as
        # "something is actually broken."
        print(f"\nAll {len(still_incomplete)} remaining are usage/rate-limit INCOMPLETE — expected, not a failure. Re-run after it resets.")
        return 2
    if still_broken:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
