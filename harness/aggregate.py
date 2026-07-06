#!/usr/bin/env python3
"""Roll every runs/<agent>/<condition>/<n>/result.json into analysis/results.csv.

One row per (run, slot) — i.e. a run against all 10 slots produces 10 rows —
plus the run-level fields (wall time, tool calls, timeout, regressions)
repeated on each of that run's rows so the CSV stays flat and pivotable in any
spreadsheet tool without a join.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = REPO_ROOT / "runs"
OUT_PATH = REPO_ROOT / "analysis" / "results.csv"

FIELDS = [
    "agent", "condition", "run_number", "scope",
    "slot_id", "package", "ecosystem", "outcome",
    "bomly_still_flagged", "second_scanner_still_flagged", "build_ok",
    "wall_seconds", "timeout", "turns", "tool_calls", "mcp_calls",
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
                "mcp_tool_error_count": len(run_meta.get("mcp_tool_errors", [])),
                "regression_count": len(data.get("regressions", [])),
                "unrelated_changes_flag": data.get("unrelated_changes_flag"),
            }
        )
    return rows


def main() -> int:
    if not RUNS_DIR.exists():
        print("no runs/ directory yet — nothing to aggregate", file=sys.stderr)
        return 0

    all_rows = []
    for result_path in sorted(RUNS_DIR.glob("*/*/*/result.json")):
        all_rows.extend(rows_for_result(result_path))

    if not all_rows:
        print("no result.json files found under runs/", file=sys.stderr)
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    n_runs = len(list(RUNS_DIR.glob("*/*/*/result.json")))
    print(f"wrote {len(all_rows)} rows from {n_runs} runs to {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
