#!/usr/bin/env bash
# Zero-API-key re-audit of an already-published run: fresh-clones the frozen
# fixture ref, applies that run's diff.patch, and re-scores it — no agent is
# re-invoked, so this costs nothing and needs no credentials. Runs on the bare
# host (not Docker) since it never executes an agent.
#
# Usage: harness/verify.sh runs/<agent>/<condition>/<n>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/harness/.venv/bin/python"
[ -x "$PY" ] || PY=python3.12
exec "$PY" "$ROOT/harness/verify.py" --from-run "$1"
