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

_Filled in once the harness lands._ The design commits to a `make reproduce-one`
target that runs a single agent+condition end to end, and a **zero-API-key**
`make verify-only` target that re-scores an already-published run so you can
audit the scoring without spending anything.

## Layout

```
fixtures/    the three intentionally-vulnerable apps + SLOTS.yaml (ground truth)
prompts/     the exact task prompt and the two condition instruction files
harness/     run + verify + aggregate scripts, per-agent adapters, Dockerfile
runs/        raw transcripts, diffs, and per-run results
analysis/    aggregated results and figures
scoring/     the scoring rubric and any manual adjudications
```

## Method, in short

Everything that could bias the result is pinned and published *before* the runs:
methodology, the scoring rubric, the ground-truth `SLOTS.yaml`, and a
limitations section — all committed under a `prereg-v1` tag before the first
full run. Results land in later commits. Numbers are reported "in our setup, on
this fixture, on these dates" — never as a general benchmark.

See [METHODOLOGY.md](METHODOLOGY.md) and [LIMITATIONS.md](LIMITATIONS.md) once published.
