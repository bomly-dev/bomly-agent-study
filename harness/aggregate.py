#!/usr/bin/env python3
"""Roll every runs/<agent>/<condition>/<n>/result.json into analysis/results.csv.

One row per (run, slot) — i.e. a run against all 10 slots produces 10 rows —
plus the run-level fields (wall time, tool calls, timeout, regressions)
repeated on each of that run's rows so the CSV stays flat and pivotable in any
spreadsheet tool without a join.

Reads ONLY runs/ by default — never runs-pilot/. Per the pre-registered
design, pilot runs are published but never pooled into the final dataset;
pass --pilot to aggregate runs-pilot/ instead, into a separate
analysis/results-pilot.csv, for inspecting pilot behavior on its own.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FIELDS = [
    "agent", "condition", "run_number", "scope",
    "slot_id", "package", "ecosystem", "outcome",
    "bomly_still_flagged", "second_scanner_still_flagged", "build_ok",
    "wall_seconds", "timeout", "turns", "tool_calls", "mcp_calls",
    "input_tokens", "output_tokens", "cache_read_tokens", "cost_usd",
    "mcp_tool_error_count", "regression_count", "unrelated_changes_flag",
]


def rows_for_result(result_path: Path) -> list[dict]:
    data = json.loads(result_path.read_text())
    run_meta = data.get("run_meta", {})
    rows = []
    for slot in data.get("slots", []):
        rows.append(
            {
                "agent": run_meta.get("agent"),
                "condition": run_meta.get("condition"),
                "run_number": run_meta.get("run_number"),
                "scope": data.get("scope"),
                "slot_id": slot.get("slot_id"),
                "package": slot.get("package"),
                "ecosystem": slot.get("ecosystem"),
                "outcome": slot.get("outcome"),
                "bomly_still_flagged": slot.get("bomly_still_flagged"),
                "second_scanner_still_flagged": slot.get("second_scanner_still_flagged"),
                "build_ok": slot.get("build_ok"),
                "wall_seconds": run_meta.get("wall_seconds"),
                "timeout": run_meta.get("timeout"),
                "turns": run_meta.get("turns"),
                "tool_calls": run_meta.get("tool_calls"),
                "mcp_calls": run_meta.get("mcp_calls"),
                "input_tokens": (run_meta.get("tokens") or {}).get("input"),
                "output_tokens": (run_meta.get("tokens") or {}).get("output"),
                "cache_read_tokens": (run_meta.get("tokens") or {}).get("cache_read"),
                "cost_usd": run_meta.get("cost_usd"),
                "mcp_tool_error_count": len(run_meta.get("mcp_tool_errors", [])),
                "regression_count": len(data.get("regressions", [])),
                "unrelated_changes_flag": data.get("unrelated_changes_flag"),
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", help="Aggregate runs-pilot/ instead of runs/")
    args = ap.parse_args()

    runs_dir = REPO_ROOT / ("runs-pilot" if args.pilot else "runs")
    out_path = REPO_ROOT / "analysis" / ("results-pilot.csv" if args.pilot else "results.csv")

    if not runs_dir.exists():
        print(f"no {runs_dir.name}/ directory yet — nothing to aggregate", file=sys.stderr)
        return 0

    # v2 layout: runs/<agent>/<condition>/<scope>/<n>/result.json — one
    # fixture per session, scope in the path.
    all_rows = []
    result_paths = sorted(runs_dir.glob("*/*/*/*/result.json"))
    for result_path in result_paths:
        all_rows.extend(rows_for_result(result_path))

    if not all_rows:
        print(f"no result.json files found under {runs_dir.name}/", file=sys.stderr)
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    n_runs = len(result_paths)
    print(f"wrote {len(all_rows)} rows from {n_runs} runs to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
