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
# Model/effort defaults (Ahmed, 2026-07-06): Claude Code -> claude-sonnet-5 at
# --effort high; Codex -> gpt-5.5 at reasoning effort medium (both confirmed
# against the real CLIs, not guessed — see harness/adapters/*.py). Override
# per run with BOMLY_STUDY_CLAUDE_MODEL / BOMLY_STUDY_CLAUDE_EFFORT /
# BOMLY_STUDY_CODEX_MODEL / BOMLY_STUDY_CODEX_EFFORT; an empty string falls
# back to that CLI's own default instead of the study default.
#
# Auth — TWO supported modes, see CREDENTIALS.md for the full setup:
#   1. Subscription-based (session-limited, no extra cost): run
#      `claude setup-token` / `codex login` once into a dedicated directory
#      (default ~/.bomly-study-creds/{claude,codex}; override with
#      BOMLY_STUDY_CLAUDE_CREDS_DIR / BOMLY_STUDY_CODEX_CREDS_DIR). This
#      script mounts that directory READ-ONLY into the container; run.py
#      copies only the credential file it needs into that run's fresh,
#      throwaway config dir before invoking the agent — the mounted template
#      is never written to, and no conversation history ever touches it.
#   2. API key: set ANTHROPIC_API_KEY / OPENAI_API_KEY in the calling shell.
# If both are present for an agent, the credential-directory mode wins.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="bomly-agent-study:harness"

CLAUDE_CREDS_DIR="${BOMLY_STUDY_CLAUDE_CREDS_DIR:-$HOME/.bomly-study-creds/claude}"
CODEX_CREDS_DIR="${BOMLY_STUDY_CODEX_CREDS_DIR:-$HOME/.bomly-study-creds/codex}"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "building $IMAGE (first run only; subsequent runs reuse the cached image)..." >&2
  docker build -f "$ROOT/harness/Dockerfile" -t "$IMAGE" "$ROOT"
fi

MOUNT_ARGS=()
if [ -d "$CLAUDE_CREDS_DIR" ]; then
  MOUNT_ARGS+=(-v "$CLAUDE_CREDS_DIR:/creds/claude:ro")
fi
if [ -d "$CODEX_CREDS_DIR" ]; then
  MOUNT_ARGS+=(-v "$CODEX_CREDS_DIR:/creds/codex:ro")
fi

docker run --rm \
  -e ANTHROPIC_API_KEY \
  -e OPENAI_API_KEY \
  -e BOMLY_STUDY_FIXTURE_REF \
  -e BOMLY_STUDY_CLAUDE_MODEL \
  -e BOMLY_STUDY_CLAUDE_EFFORT \
  -e BOMLY_STUDY_CODEX_MODEL \
  -e BOMLY_STUDY_CODEX_EFFORT \
  -e BOMLY_STUDY_MAX_BUDGET_USD \
  "${MOUNT_ARGS[@]}" \
  -v "$ROOT:/work/bomly-agent-study" \
  -w /work/bomly-agent-study \
  "$IMAGE" \
  python3 harness/run.py "$@"
