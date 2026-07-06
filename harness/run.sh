#!/usr/bin/env bash
# Thin wrapper: build (if needed) and run one agent+condition inside the
# study's Docker image, matching harness/Dockerfile. This is the ONLY
# supported way to execute a live agent run — harness/adapters/*.py refuse to
# use bypassPermissions / --dangerously-bypass-approvals-and-sandbox unless
# they detect BOMLY_STUDY_IN_CONTAINER=1 AND /.dockerenv, both of which this
# image sets/provides.
#
# Usage:
#   harness/run.sh <claude|codex> <bare|mcp> <run-number> [--scope webapp|service|api-java]
#
# Requires ANTHROPIC_API_KEY (claude) or OPENAI_API_KEY (codex) in the
# environment calling this script — never hardcode a key here or in the image.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="bomly-agent-study:harness"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "building $IMAGE (first run only; subsequent runs reuse the cached image)..." >&2
  docker build -f "$ROOT/harness/Dockerfile" -t "$IMAGE" "$ROOT"
fi

docker run --rm \
  -e ANTHROPIC_API_KEY \
  -e OPENAI_API_KEY \
  -e BOMLY_STUDY_FIXTURE_REF \
  -e BOMLY_STUDY_CLAUDE_MODEL \
  -e BOMLY_STUDY_CODEX_MODEL \
  -e BOMLY_STUDY_MAX_BUDGET_USD \
  -v "$ROOT:/work/bomly-agent-study" \
  -w /work/bomly-agent-study \
  "$IMAGE" \
  python3 harness/run.py "$@"
