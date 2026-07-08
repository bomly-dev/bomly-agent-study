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
# Auth — see CREDENTIALS.md. The two agents work differently, corrected after
# a real pilot run proved the original (symmetric, directory-mount-based)
# design wrong for Claude:
#   - Claude Code: subscription auth is CLAUDE_CODE_OAUTH_TOKEN, an env var
#     produced once via `claude setup-token` (NOT a directory-based
#     credential — Claude Code's OAuth session normally lives in the macOS
#     Keychain, which doesn't exist in a Linux container; setup-token exists
#     to produce a portable token instead). Falls back to ANTHROPIC_API_KEY.
#   - Codex: subscription auth genuinely IS file-based — `codex login`
#     writes auth.json into CODEX_HOME. Run it once into a dedicated
#     directory (default ~/.bomly-study-creds/codex; override with
#     BOMLY_STUDY_CODEX_CREDS_DIR); this script mounts that READ-ONLY into
#     the container, and run.py copies just auth.json into that run's fresh,
#     throwaway CODEX_HOME. Falls back to OPENAI_API_KEY if no mount exists.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="bomly-agent-study:harness"

CODEX_CREDS_DIR="${BOMLY_STUDY_CODEX_CREDS_DIR:-$HOME/.bomly-study-creds/codex}"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "building $IMAGE (first run only; subsequent runs reuse the cached image)..." >&2
  docker build -f "$ROOT/harness/Dockerfile" -t "$IMAGE" "$ROOT"
fi

MOUNT_ARGS=()
if [ -d "$CODEX_CREDS_DIR" ]; then
  MOUNT_ARGS+=(-v "$CODEX_CREDS_DIR:/creds/codex:ro")
fi

docker run --rm \
  -e ANTHROPIC_API_KEY \
  -e CLAUDE_CODE_OAUTH_TOKEN \
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
  /opt/study-tools/bin/python harness/run.py "$@"
