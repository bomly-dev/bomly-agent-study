# bomly-agent-study

A reproducible study of how AI coding agents remediate known-vulnerable
dependencies — **with and without** a dependency-graph tool (an MCP server)
available to them.

> ⚠️ **This repository is intentionally vulnerable.** The fixtures under
> [`fixtures/`](fixtures/) pin dependency versions with *known, published*
> vulnerabilities on purpose. Do not deploy any of this code, and do not copy
> its dependency pins into a real project. See [SECURITY.md](SECURITY.md).

## What this is

We give two coding agents the same task — "find and fix the vulnerable
dependencies, keep the tests passing" — across three small applications
(npm, Python, and Java/Maven). We run each agent in two conditions:

- **bare** — the agent works with whatever it already knows and the ecosystem's
  own tooling.
- **mcp** — the same agent, plus a running [Bomly](https://bomly.dev) MCP server
  it can query for the dependency graph and fix context.

Then we score every run mechanically and publish the raw transcripts, the
scoring code, and the full results — including the runs where the graph did not
help.

## Reproduce a run

Everything below runs on Linux, macOS, or Windows (via WSL2) with
[Docker](https://docs.docker.com/get-docker/) installed. See
[Architecture & platform support](#architecture--platform-support) below for
what's actually been verified vs. what should work.

### 1. Get credentials

You need either a Claude Code or a Codex CLI credential — see
[CREDENTIALS.md](CREDENTIALS.md) for the full guide. Short version: run
**one** of these once, then leave the resulting directory in place (the
harness reads from it on every run; it's never modified):

```bash
# Subscription-based (session-limited, no per-token billing) — recommended:
mkdir -p ~/.bomly-study-creds/claude && \
  CLAUDE_CONFIG_DIR=~/.bomly-study-creds/claude claude setup-token
mkdir -p ~/.bomly-study-creds/codex && \
  CODEX_HOME=~/.bomly-study-creds/codex codex login

# OR: API key (pay-per-token), no setup needed beyond exporting it:
export ANTHROPIC_API_KEY=...   # for claude runs
export OPENAI_API_KEY=...      # for codex runs
```

### 2. Run one agent+condition end to end

```bash
make reproduce-one AGENT=claude CONDITION=mcp SCOPE=webapp RUN_NUMBER=1
```

First invocation builds the Docker image (a few minutes); later ones reuse
it. `AGENT` is `claude` or `codex`; `CONDITION` is `bare` or `mcp`; `SCOPE` is
`webapp`, `service`, `api-java`, or `all` (all three, slower). Output lands in
`runs/<agent>/<condition>/<run-number>/` — raw transcript, normalized
transcript, `diff.patch`, `FIXES.md`, `meta.json`, `timing.json`, and
`result.json` (the per-slot verdicts).

To exercise the isolation/scoring pipeline without invoking a real agent or
touching any credentials (useful for checking your setup, costs nothing):

```bash
docker run --rm -v "$(pwd):/work/bomly-agent-study" -w /work/bomly-agent-study \
  bomly-agent-study:harness python3 harness/run.py claude bare 1 --scope webapp --dry-run
```

### 3. Re-score a run with zero API key

Anyone can audit the scoring on an already-published run without spending
anything or holding any credential — it fresh-clones the frozen fixture ref,
applies that run's `diff.patch`, and re-runs the same mechanical checks:

```bash
make verify-only RUN=runs/claude/mcp/1
```

### 4. Aggregate results

```bash
make aggregate   # rolls every runs/*/*/*/result.json into analysis/results.csv
```

## Architecture & platform support

- **Docker image (`harness/Dockerfile`)**: builds natively for **linux/amd64**
  and **linux/arm64** (Docker's `TARGETARCH` build arg selects the matching
  JDK and `bomly` binary downloads — both were originally hardcoded to
  amd64, which crashed under Rosetta emulation on Apple Silicon; fixed and
  verified on arm64). No other architecture is supported — that's also the
  limit of what upstream (`bomly-cli`, Eclipse Temurin/OpenJDK builds) ships
  release binaries for.
- **Verified so far**: built and run end-to-end (`--dry-run`, no live agent
  yet) on **macOS, Apple Silicon, Docker Desktop**. Not yet verified on
  Linux hosts or Windows/WSL2 — the image itself has no Mac-specific step, so
  it's expected to work, but "expected" isn't "verified." If you build on a
  different host, please report back (or open a PR) with what you found.
  amd64 Linux (e.g. GitHub Actions runners) is the most likely next
  environment this gets exercised on.
- **Everything that touches a live agent only ever runs inside the
  container** — `harness/adapters/{claude,codex}.py` hard-refuse the
  full-autonomy permission modes they need for unattended runs
  (`--permission-mode bypassPermissions` /
  `--dangerously-bypass-approvals-and-sandbox`) unless they detect both
  `/.dockerenv` and `BOMLY_STUDY_IN_CONTAINER=1`, which only `harness/run.sh`
  sets. There is no supported bare-host path for a live run.
- **Bare-host use is limited to `make verify-only` and `make test`** (rebuilding
  and testing the fixtures directly, no agent involved). These need a local
  JDK 17+ for the `api-java` fixture; `harness/verify.py`'s
  `resolve_java_home()` tries `JAVA_HOME`, then macOS's
  `/usr/libexec/java_home`, then a `/usr/lib/jvm/*` glob (common Linux
  layout), and raises a clear error with per-OS instructions rather than
  guessing if none resolve. (An earlier version of this hardcoded an
  Apple-Silicon-Homebrew path as a silent fallback — wrong on every other
  machine, including Intel Macs; removed.) Note: Homebrew's `openjdk` on
  macOS is keg-only and does **not** register with `/usr/libexec/java_home`,
  so Homebrew users on macOS still need to export `JAVA_HOME` explicitly —
  see [fixtures/api-java/README.md](fixtures/api-java/README.md).

## Layout

```
fixtures/    the three intentionally-vulnerable apps + SLOTS.yaml (ground truth)
prompts/     the exact task prompt and the two condition instruction files
harness/     run + verify + aggregate scripts, per-agent adapters, Dockerfile
runs/        raw transcripts, diffs, and per-run results
analysis/    aggregated results and figures
scoring/     the scoring rubric and any manual adjudications
```

See [CREDENTIALS.md](CREDENTIALS.md) for the full credential setup guide (both
supported auth modes, exactly what gets copied where, and the isolation
guarantees behind it).

## Method, in short

Everything that could bias the result is pinned and published *before* the runs:
methodology, the scoring rubric, the ground-truth `SLOTS.yaml`, and a
limitations section — all committed under a `prereg-v1` tag before the first
full run. Results land in later commits. Numbers are reported "in our setup, on
this fixture, on these dates" — never as a general benchmark.

See [METHODOLOGY.md](METHODOLOGY.md) and [LIMITATIONS.md](LIMITATIONS.md) once published.
