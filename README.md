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
dependencies, keep the tests passing" — across four applications: a small
npm app, CTFd 3.7.7 (Python), Dependency-Track 4.10.0 (Java/Maven), and
Internet2 Grouper 4.x (a 13-module Maven reactor with ~300 resolved
dependencies). We run each agent in two conditions:

- **bare** — the agent works with whatever it already knows and the ecosystem's
  own tooling.
- **mcp** — the same agent, plus a running [Bomly](https://bomly.dev) MCP server
  it can query for the dependency graph and fix context.

Then we score every run mechanically and publish the raw transcripts, the
scoring code, and the full results — including the runs where the graph did not
help.

**The results are in:** [REPORT.md](REPORT.md) is the long-form writeup,
[METHODOLOGY.md](METHODOLOGY.md) the as-run protocol (including where it
changed and why), and [LIMITATIONS.md](LIMITATIONS.md) the honest caveat
list. Short version: on the three tractable fixtures both agents saturated
the task without the server; on the large Maven fixture, no MCP-connected
run finished below 98% completeness while bare runs ranged 14–100%.

## Reproduce a run

Everything below runs on Linux, macOS, or Windows (via WSL2) with
[Docker](https://docs.docker.com/get-docker/) installed. See
[Architecture & platform support](#architecture--platform-support) below for
what's actually been verified vs. what should work.

### 1. Get credentials

You need a Claude Code and/or a Codex CLI credential — see
[CREDENTIALS.md](CREDENTIALS.md) for the full guide, including why the two
agents are set up differently (a real pilot run caught a wrong assumption
here — Claude's isn't a directory-based credential the way Codex's is).

```bash
# Claude Code: prints a token — export it yourself, never paste it anywhere:
claude setup-token
export CLAUDE_CODE_OAUTH_TOKEN=<the token you were just given>

# Codex: writes a real credential file, so it's set up into a dedicated dir:
mkdir -p ~/.bomly-study-creds/codex
CODEX_HOME=~/.bomly-study-creds/codex codex login

# OR, for either agent: API key (pay-per-token), no setup beyond exporting it:
export ANTHROPIC_API_KEY=...   # for claude runs, if CLAUDE_CODE_OAUTH_TOKEN isn't set
export OPENAI_API_KEY=...      # for codex runs, if no /creds/codex mount is present
```

### 2. Run one agent+condition end to end

```bash
make reproduce-one AGENT=claude CONDITION=mcp SCOPE=webapp RUN_NUMBER=1
```

First invocation builds the Docker image (a few minutes); later ones reuse
it. `AGENT` is `claude` or `codex`; `CONDITION` is `bare` or `mcp`; `SCOPE` is
`webapp`, `service`, `api-java`, `bigapp`, or `all`. Output lands in
`runs/<agent>/<condition>/<fixture>/<run-number>/` — raw transcript,
normalized transcript, `diff.patch`, `FIXES.md`, `meta.json`, `timing.json`,
and `result.json` (the per-package verdicts). Both `model` and the
reasoning-effort level actually used are recorded in `meta.json`.

#### Model and reasoning effort

| | Model | Effort | Env var overrides |
|---|---|---|---|
| Claude Code | `claude-sonnet-5` (default) · `claude-opus-4-8` on `bigapp` | `high` | `BOMLY_STUDY_CLAUDE_MODEL`, `BOMLY_STUDY_CLAUDE_EFFORT` |
| Codex | `gpt-5.5` | `medium` | `BOMLY_STUDY_CODEX_MODEL`, `BOMLY_STUDY_CODEX_EFFORT` |

Both defaults were confirmed against the real CLIs, not guessed: Claude
Code's `--effort` flag accepts `low`/`medium`/`high`/`xhigh`/`max`; `gpt-5.5`
is a real, current Codex model slug (`codex debug models`) whose own default
reasoning level is `medium`, with `low`/`medium`/`high`/`xhigh` supported —
Codex sets it via the `model_reasoning_effort` config key. Set any override
to an **empty string** to fall back to that CLI's own default instead of the
study's default, e.g.:

```bash
BOMLY_STUDY_CLAUDE_MODEL=claude-opus-4-8 BOMLY_STUDY_CLAUDE_EFFORT=xhigh \
  make reproduce-one AGENT=claude CONDITION=mcp SCOPE=webapp
```

The published run set pins one model+effort pair per agent per fixture — the
pairs in the table above are what actually ran, and each run's `meta.json`
records what it used. The `bigapp` fixture runs Claude on `claude-opus-4-8`
(the reasoning is in [METHODOLOGY.md](METHODOLOGY.md), deviation #5). These
env vars exist for reproduction and exploration, not for mixing models
within a published cell.

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
make verify-only RUN=runs/claude/mcp/bigapp/1
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
fixtures/    the four intentionally-vulnerable apps + the frozen ground truth
             (ground-truth.json / GROUND_TRUTH.md) + the SLOTS.yaml overlay
prompts/     the exact task prompt and the two condition instruction files
harness/     run + verify + aggregate scripts, per-agent adapters, Dockerfile
runs/        raw transcripts, diffs, and per-run results
analysis/    aggregated results (results.csv) and generated figures
scoring/     the scoring rubric and any manual adjudications
scripts/     ground-truth + figure generators
```

See [CREDENTIALS.md](CREDENTIALS.md) for the full credential setup guide (both
supported auth modes, exactly what gets copied where, and the isolation
guarantees behind it).

## Method, in short

Everything that could bias the result is pinned and published *before* the
runs: the scoring rubric and the frozen ground truth were committed under the
`prereg-v1` tag before the first full run, and results landed in later
commits. Where the design changed after that tag (it did — most notably the
fourth fixture), the change and its reasoning are published rather than
papered over. Numbers are reported "in our setup, on this fixture, on these
dates" — never as a general benchmark.

See [METHODOLOGY.md](METHODOLOGY.md), [LIMITATIONS.md](LIMITATIONS.md), and
[REPORT.md](REPORT.md).
