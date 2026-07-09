#!/usr/bin/env python3
"""Roll every runs/<agent>/<condition>/<scope>/<n>/result.json into analysis/results.csv.

v3 (2026-07-09): one row per (run, package) over the FULL vulnerable surface
— e.g. a run against the hard fixture produces ~35 rows, not a curated ~10 —
plus the run-level fields (completeness, wall time, tool calls, tokens,
regressions) repeated on each of that run's rows so the CSV stays flat and
pivotable in any spreadsheet tool without a join.

Reads ONLY runs/ by default — never runs-pilot/. Per the pre-registered
design, pilot runs are published but never pooled into the final dataset;
pass --pilot to aggregate runs-pilot/ instead, into a separate
analysis/results-pilot.csv, for inspecting pilot behavior on its own.

Incomplete runs (usage/rate-limit hit mid-session — see harness/run_study.py)
are never pooled into the real numbers: skipped from the per-package rows,
counted and reported separately so they're visible without polluting
completeness stats.
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
    "package", "ecosystem", "outcome",
    "package_fixable_total", "package_fixable_resolved",
    "package_unfixable_total", "package_unfixable_remaining",
    "build_ok",
    "run_completeness", "run_fixable_total", "run_fixable_resolved",
    "wall_seconds", "timeout", "turns", "tool_calls", "mcp_calls",
    "input_tokens", "output_tokens", "cache_read_tokens", "cost_usd",
    "mcp_tool_error_count", "regression_count", "unrelated_changes_flag",
]


def rows_for_result(result_path: Path) -> list[dict]:
    data = json.loads(result_path.read_text())
    run_meta = data.get("run_meta", {})
    rows = []
    for pkg in data.get("packages", []):
        rows.append(
            {
                "agent": run_meta.get("agent"),
                "condition": run_meta.get("condition"),
                "run_number": run_meta.get("run_number"),
                "scope": data.get("scope"),
                "package": pkg.get("package"),
                "ecosystem": pkg.get("ecosystem"),
                "outcome": pkg.get("outcome"),
                "package_fixable_total": pkg.get("fixable_total"),
                "package_fixable_resolved": pkg.get("fixable_resolved"),
                "package_unfixable_total": pkg.get("unfixable_total"),
                "package_unfixable_remaining": len(pkg.get("unfixable_remaining_ids", [])),
                "build_ok": pkg.get("build_ok"),
                "run_completeness": data.get("completeness"),
                "run_fixable_total": data.get("fixable_total"),
                "run_fixable_resolved": data.get("fixable_resolved"),
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

    # v2 layout: runs/<agent>/<condition>/<scope>/<n>/{meta,result}.json —
    # one fixture per session, scope in the path. An INCOMPLETE session
    # (harness/run.py, v3 2026-07-09) never gets a result.json at all — it's
    # skipped before the expensive scoring pipeline runs, since a partial
    # remediation of a "fix everything" task isn't a real data point. Counted
    # from meta.json (always written) purely for visibility, never pooled.
    all_rows = []
    result_paths = sorted(runs_dir.glob("*/*/*/*/result.json"))
    for result_path in result_paths:
        all_rows.extend(rows_for_result(result_path))
    scored_count = len(result_paths)

    incomplete_count = 0
    for meta_path in runs_dir.glob("*/*/*/*/meta.json"):
        meta = json.loads(meta_path.read_text())
        if meta.get("incomplete_reason"):
            incomplete_count += 1

    if not all_rows and not incomplete_count:
        print(f"no result.json files found under {runs_dir.name}/", file=sys.stderr)
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"wrote {len(all_rows)} rows from {scored_count} scored runs to {out_path}")
    if incomplete_count:
        print(f"skipped {incomplete_count} INCOMPLETE run(s) — not pooled, retry after the usage limit resets", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
