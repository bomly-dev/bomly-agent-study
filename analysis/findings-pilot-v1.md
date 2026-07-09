# Pilot v1 findings — why we rebuilt the fixtures before the full study

This document records what the first-generation ("v1") pilot fixtures showed, the three
bomly-cli bugs the pilot uncovered, and why we replaced two of the three fixtures before
freezing the study design. Nothing here is part of the final dataset: v1 pilot runs live in
`runs-pilot-v1/` and are re-scorable only at the git tag `v1-fixtures-final` (the ground truth
in `fixtures/SLOTS.yaml` changed after that tag). Frozen CSVs:

- `analysis/results-pilot-v1-fixtures.csv` — all 16 v1 pilot runs (runs 1–4).
- `analysis/results-pilot-run3-pre-245-fix.csv` — the run-3 snapshot taken before the
  bomly-cli#245 fix, kept for the before/after comparison below.

## The hypothesis

An agent connected to a dependency-graph MCP server (`bomly mcp serve`) fixes vulnerable
dependencies more correctly and more efficiently than the same agent with only its default
tools ("bare" condition).

## Timeline

| When | What |
|---|---|
| Jul 6 | Runs 1–2 (N=2 batch, bomly 0.16.0): harness shake-out. Multiple harness and scoring bugs found and fixed; results not comparable to later runs. |
| Jul 7 | [bomly-cli#237](https://github.com/bomly-dev/bomly-cli/issues/237) and [#243](https://github.com/bomly-dev/bomly-cli/issues/243) found, fixed upstream (v0.16.1, v0.16.2), each verified in a rebuilt container. Run 3 collected on 0.16.2. Scoring made advisory-ID-scoped; per-run token/cost capture added. [bomly-cli#245](https://github.com/bomly-dev/bomly-cli/issues/245) filed from run-3 evidence. |
| Jul 8 | #245 fixed upstream (v0.17.0). Run 4 collected on 0.17.0. Ceiling effect diagnosed from transcripts; decision to rebuild the fixture ladder (this document). |

## Three real bomly-cli bugs, found by the pilot itself

1. **#237 — pip detector ambient-interpreter fallback.** With `pip-audit` installed system-wide
   in the runner image and no project venv yet, `bomly scan` on the Python fixture silently
   returned pip-audit's own dependency tree instead of the fixture's. Agents in the mcp
   condition were told "no vulnerabilities" by a scan of the wrong project. Fixed in v0.16.1.
2. **#243 — Maven ANSI color codes broke transitive resolution.** `mvn dependency:tree` output
   carried ANSI escapes in the container; bomly's TGF parser matched a literal `[INFO]` prefix,
   parsed zero packages, and silently fell back to a direct-deps-only scan — every transitive
   Maven dependency (including slot S10) was invisible in both conditions. Fixed in v0.16.2.
3. **#245 — oversized MCP scan responses.** `bomly_scan` over MCP returned the full scan JSON:
   1.8–2.9 MB on the npm fixture (89% of it the `findings[]` array, which embedded a full
   duplicated package object per finding). In a real session, 4 of 8 scan calls exceeded the
   agent's tool-result limit and were truncated to an error. Fixed in v0.17.0 (compact
   agent-facing responses; the same scans now return 21–24 KB).

Also found in run-3 data and worth keeping: the mcp condition once hallucinated a fix (claude,
S3) while its scan results were being truncated by #245 — that regression did not recur after
the fix.

## Run 3 (bomly 0.16.2, #245 present) vs run 4 (bomly 0.17.0, #245 fixed)

One run per cell (N=1), all three fixtures in a single agent session, advisory-ID-scoped
scoring, identical prompts and models across runs.

**Accuracy (slots FIXED out of 10; the tenth slot, S6, is a deliberate no-fix trap that both
conditions correctly declined in every run):**

| agent  | condition | run 3 | run 4 |
|--------|-----------|-------|-------|
| claude | bare      | 9/10  | 9/10  |
| claude | mcp       | 8/10 (S3 hallucinated) | 9/10 |
| codex  | bare      | 9/10  | 9/10  |
| codex  | mcp       | 9/10  | 9/10  |

In run 4, per-slot outcomes are identical between bare and mcp for both agents.

**Efficiency and cost:**

| agent  | condition | run | tool_calls | mcp_calls | wall (s) | input tokens | output tokens | cost (USD) |
|--------|-----------|-----|-----------|-----------|----------|--------------|---------------|------------|
| claude | bare | 3 | 87 | 0  | 536 | 125 | 31,923 | 2.42 |
| claude | mcp  | 3 | 93 | 13 | 624 | 155 | 42,497 | 4.13 |
| codex  | bare | 3 | 43 | 0  | 289 | 1,168,842 | 10,684 | n/a |
| codex  | mcp  | 3 | 58 | 28 | 326 | 3,875,146 | 10,040 | n/a |
| claude | bare | 4 | 60 | 0  | 349 | 95  | 23,597 | 1.80 |
| claude | mcp  | 4 | 84 | 8  | 495 | 117 | 31,811 | 2.83 |
| codex  | bare | 4 | 43 | 0  | 260 | 1,324,788 | 10,482 | n/a |
| codex  | mcp  | 4 | 43 | 14 | 351 | 2,203,093 | 12,051 | n/a |

(claude reports near-zero raw input tokens because almost all input is prompt-cache reads —
run 3: 4.5M cache-read bare vs 8.0M mcp; codex folds cache reads into `input`. Codex runs on a
subscription, so no per-run dollar cost is reported by its CLI.)

The #245 fix moved the mcp condition's overhead substantially: claude mcp/bare cost ratio
1.71× → 1.57×, codex mcp/bare input-token ratio 3.31× → 1.66×, codex tool calls under mcp
dropped to exactly bare's count. mcp remained slower and costlier than bare in absolute terms
in every run.

## Why the v1 fixtures could not answer the hypothesis (ceiling effect)

Bare agents hit 9/10 every time, so there was no headroom for the mcp condition to show an
accuracy advantage — the fixtures saturate. The transcripts show exactly how the bare agents
did it, and each mechanism is a property of the fixture design:

1. **The dependency trees are tiny.** 135 npm packages, ~30 Python, 16 Maven. `mvn
   dependency:tree` output fits in a single tool result; a lockfile fits in context. The graph
   problem a dependency-graph server solves does not exist at this scale.
2. **The CVEs are famous.** Text4Shell, jackson-databind, jsonwebtoken 8→9, PyJWT 1→2 — heavily
   documented, deep inside the models' training data.
3. **Egress is open and OSV is one curl away.** codex/bare/4 first probed for scanners
   (`which dependency-check || which osv-scanner || which grype || which snyk`), found none,
   then hand-built the equivalent: direct `POST https://api.osv.dev/v1/query` per Maven
   package, `~/.m2` listings for available versions, Maven Central metadata for latest
   releases. Its FIXES.md cites the exact GHSA IDs from those responses and gets the
   transitive remediation right. claude/bare/4 did the same with `mvn dependency:tree` +
   Maven Central + its own knowledge of these CVEs. The "no native audit tool" ecosystem
   (Maven) was fully substituted by network + memory + a 16-package tree.

A note on egress as an axis: restricting network would not isolate mcp value either, because
bomly's own `--enrich` needs the network too. Dropped as a design axis.

## Decision: fixture ladder v2 (recorded 2026-07-08)

Two of three fixtures are replaced with vendored real-world applications, forming a difficulty
ladder that keeps the audit-tool-availability axis and adds the scale axis the v1 fixtures
lacked:

| rung | directory | contents | native audit tool | why |
|---|---|---|---|---|
| easy | `fixtures/webapp` | unchanged v1 npm app (135 pkgs) | `npm audit` (strong) | regime where bare agents are known-strong; establishes the baseline honestly |
| medium | `fixtures/service` | real-world Python app, ~150–300 pkgs, old tag | `pip-audit` (weaker) | real code, fixes need real edits |
| hard | `fixtures/api-java` | real-world Maven app, 200–400 artifacts, old tag | none | tree too large to read into context or hand-query per-package; the regime where a dependency graph should matter — if it doesn't show value here, that is a finding too |

Protocol change at the same time: each fixture now runs in its own agent session
((agent × condition × fixture × n) instead of one three-fixture session), for clean
per-difficulty metrics and finer failure isolation. v1 and v2 runs are therefore never pooled
or compared per-run. Vulnerabilities are never injected — real apps are pinned at real
historical tags and every scored slot is verified by bomly and an independent second scanner
at selection time.
