# Methodology

How the study was actually run — including the places where the design changed
after the `prereg-v1` tag, and why. The short version is in the
[README](README.md); the long-form results writeup is [REPORT.md](REPORT.md);
the honest list of weaknesses is [LIMITATIONS.md](LIMITATIONS.md).

## The question

When a coding agent is asked to remediate the known-vulnerable dependencies of
a project, does giving it a dependency-graph tool over MCP (the
[Bomly](https://bomly.dev) MCP server) change what it accomplishes — and if
so, where?

## Agents and conditions

| | Version | Model | Reasoning effort |
|---|---|---|---|
| Claude Code | 2.1.201 | `claude-sonnet-5` (webapp/service/api-java) · `claude-opus-4-8` (bigapp) | high |
| Codex CLI | 0.142.5 | `gpt-5.5` | medium |

Model, effort, agent version, bomly version (with binary checksum), start/end
timestamps, token counts, and tool/MCP call counts are recorded per run in
that run's `meta.json`. The scored runs were executed on 2026-07-10
(webapp/service/api-java, bomly 0.17.0) and 2026-07-11 (bigapp, bomly 0.17.1).

Two conditions per agent:

- **bare** — the agent, its own tools, and open network access. Nothing is
  blocked: the agent may run `npm audit`/`pip-audit` where they exist, query
  OSV, search the web, or use whatever it knows.
- **mcp** — the same setup plus a running Bomly MCP server (`bomly mcp
  serve`), which exposes the dependency graph, the vulnerable-package list,
  and per-package fix context as tools.

The task prompt ([prompts/PROMPT.md](prompts/PROMPT.md)) is identical in both
conditions: find and fix the known-vulnerable dependencies, keep the build
green. The per-condition instruction files differ by one equal-length,
neutrally-worded line disclosing which tools are available — so neither
condition gets extra nudging. The disclosure line is scope-aware: a
Maven-only session is not told about npm/pip tooling.

## Fixtures

Four fixtures, in [`fixtures/`](fixtures/). Three are real applications
vendored at old, genuinely vulnerable tags; one is purpose-built. No
vulnerability is ever injected or invented — every scored advisory is a real,
published advisory against a real package version, and licenses are
Apache/MIT/BSD with attribution.

| Fixture | Ecosystem | What it is | Vulnerable surface |
|---|---|---|---|
| `webapp` | npm | small API app built for the study | 14 packages (13 fixable) |
| `service` | Python | [CTFd](https://github.com/CTFd/CTFd) 3.7.7 | 11 packages (all fixable, one real partial exception) |
| `api-java` | Maven (single-module) | [Dependency-Track](https://github.com/DependencyTrack/dependency-track) 4.10.0 | 35 packages (32 fixable, 1 no-fix, 2 mixed) |
| `bigapp` | Maven (13-module reactor) | [Internet2 Grouper](https://github.com/Internet2/grouper) 4.x (`6c294076`) | 21 packages / 56 fixable advisories in ~300 resolved dependencies |

The first three form a small→hard ladder of *tractable* projects. `bigapp`
exists to test a different regime: a project large enough that *finding* the
vulnerable packages — not fixing them — is the main work, with no native
audit tool to lean on. See "How the design changed" below for why it was
added.

## Ground truth and scoring

- **The answer key is frozen before runs.**
  [`fixtures/ground-truth.json`](fixtures/ground-truth.json) (human-readable
  summary: [`fixtures/GROUND_TRUTH.md`](fixtures/GROUND_TRUTH.md)) lists every
  package counted as vulnerable, per fixture, plus per-advisory fix data.
- **Dual confirmation.** For webapp/service/api-java, a package is scored
  only if flagged by both bomly (`--enrich --audit`) *and* the ecosystem's
  independent second scanner (`npm audit` / `pip-audit` / `trivy`) — so bomly
  does not grade its own homework.
- **The exception: `bigapp` is bomly-only scored.** None of the study's
  second scanners (npm audit / pip-audit / trivy) can resolve the transitive
  dependency graph of a multi-module Maven reactor — commercial tools that
  can exist, but were not available for this study — so a dual-confirm there
  would shrink the scored surface to what the weaker scanner happens to see. We trust bomly's native Maven
  resolution for the surface, keep a hand-verified overlay
  ([`fixtures/SLOTS.yaml`](fixtures/SLOTS.yaml)) for the notable cases, and —
  the mitigation that matters — verify *task success* independently of bomly:
  whether the build is green and which package versions actually changed is
  read from the workspace and the diff, not from bomly. This is a real
  limitation and is listed first in [LIMITATIONS.md](LIMITATIONS.md).
- **Completeness over the full surface.** A run is scored on the *entire*
  confirmed-vulnerable set, not a curated subset: `run_completeness` = fixable
  advisories resolved / fixable advisories total. Genuinely unfixable
  advisories don't count against completeness when correctly declined.
- **Per-package outcomes.** Each package in each run is labeled
  (`RESOLVED`, `CORRECTLY_DECLINED`, `NOT_ATTEMPTED`, `ATTEMPTED_NOT_FIXED`,
  `HALLUCINATED`, `INCORRECTLY_DECLINED`, …) by mechanical checks over the
  rebuilt workspace, the diff, and the run's own `FIXES.md` self-report — a
  *hallucinated* fix is one the self-report claims fixed but the advisory
  still applies. Edge cases are adjudicated by hand and logged in
  [`scoring/adjudications.md`](scoring/adjudications.md).
- **Completeness and the hallucination label are independent measures.**
  Completeness counts fixable advisories actually resolved. A hallucinated
  claim can target a *fixable* package (the claimed fix didn't land — this
  also lowers completeness) or an *unfixable* one (the run claims a fix for a
  package whose honest outcome is a decline — completeness is unaffected,
  since only fixable advisories are counted). This is how a run can be 100%
  complete and still contain a hallucinated claim: it resolved everything
  fixable, and additionally overclaimed on a no-fix package.
- Scoring is re-runnable by anyone with Docker and no credentials:
  `make verify-only RUN=runs/<agent>/<condition>/<fixture>/<n>`.

## Isolation

- Each run starts from a fresh `git archive` snapshot of the fixture with the
  answer key and the scoring engine stripped out — the agent never sees
  `ground-truth.json`, `SLOTS.yaml`, or the scorers.
- Everything that touches a live agent runs inside a pinned Docker image
  (`harness/Dockerfile`, amd64 + arm64). The per-agent adapters refuse to run
  in full-autonomy mode outside the container.
- Credentials are isolated per agent (see [CREDENTIALS.md](CREDENTIALS.md));
  `~/.m2` and scanner DBs are pre-warmed in the image so network flakiness
  doesn't contaminate timing.
- `bigapp` is scanned with `--detectors maven-detector --install-first`
  (bomly ≥ 0.17.1 — see the dogfooding notes in [REPORT.md](REPORT.md)).

## Execution

- **N=5 per cell on `bigapp`; N=1 per cell on the three smaller fixtures.**
  The design planned N=5 everywhere (agent × condition × fixture), but the
  smaller fixtures' remaining rounds were dropped after round 1 came back at
  a ceiling — see deviation 4 below. Runs were human-gated *fixture-batches*:
  one batch = both agents × both conditions on one fixture at one run number
  (4 sessions), with results and remaining usage budget reviewed between
  batches.
- **Interrupted sessions are never scored.** A session cut off by an external
  usage/rate limit is marked incomplete and re-run after the window resets.
  Deliberately, an agent hitting its own turn ceiling is *not* treated as
  incomplete — running out of budget while over-scoping is a legitimate
  outcome this study exists to measure, and silently retrying it would bias
  the results.
- The orchestrator (`harness/run_study.py`, `make study` / `make batch`) is
  resumable and only executes missing or invalid cells.

## How the design changed (deviations from `prereg-v1`)

We publish these rather than pretending the first design worked:

1. **Pilot v1 saturated** (tag `v1-fixtures-final`, arc in
   [`analysis/findings-pilot-v1.md`](analysis/findings-pilot-v1.md)): three
   tiny fixtures, ~10 curated slots; bare agents scored 9/10 in every valid
   run. Fixtures too small, CVEs too famous. The pilot's real output was four
   bomly bug fixes.
2. **v2 — real-world fixture ladder.** CTFd and Dependency-Track vendored at
   historical tags replaced the toy medium/hard rungs; one fixture per agent
   session.
3. **v3 — full-surface scoring.** The curated ~10-slot scoring hid exactly
   the signal a hard fixture exists to surface (a pilot run remediated ~35
   real packages but only 3 were scored). Scoring switched to the full
   dual-confirmed surface before the `prereg-v1` freeze, plus the
   incomplete-session policy above.
4. **Round 1 of N=5 confirmed a ceiling, so the remaining rounds on the three
   tractable fixtures were dropped.** One agent's bare condition finished at
   100%, build green, on all three fixtures in round 1 — with no completeness
   headroom, more rounds could only re-confirm the ceiling. That null result
   is reported, not buried.
5. **`bigapp` was added after `prereg-v1`** to reach the regime the ladder
   couldn't: large tree, no audit tool. Two consequences worth flagging
   plainly: it is bomly-only scored (above), and Claude Code runs it on
   `claude-opus-4-8` rather than sonnet — the sonnet runs on the smaller
   fixtures showed a model-specific over-scoping/build-breaking behavior we
   did not want confounding the bare-vs-mcp comparison. Within-fixture
   comparisons are unaffected; cross-fixture comparisons of Claude numbers
   are not apples-to-apples.
6. **Round 1 on `bigapp` had a minor, symmetric workspace leak** (a Makefile
   build comment mentioned a scoring-internal term). Both conditions saw it
   identically; it was removed for rounds 2–5, which reproduce round 1's
   result. Details in [LIMITATIONS.md](LIMITATIONS.md).

## Figures

Every figure in [REPORT.md](REPORT.md) (and the blog post) is generated from
[`analysis/results.csv`](analysis/results.csv) by
[`scripts/gen_figures.py`](scripts/gen_figures.py) — no hand-drawn numbers.
