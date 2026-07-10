"""Shared incomplete-session detection, used by both agent adapters and by
harness/run_study.py's orchestrator-level check.

v3 (2026-07-09, Ahmed): a session that hits an AI usage/rate limit mid-task
must be marked INCOMPLETE — distinct from a real low score — and retried
after the allowance resets, not scored or pooled into the real numbers.
Under v3's full-surface scoring, this matters more than it used to: a
partial remediation of a "fix everything" task looks like genuine low
completeness unless the run is flagged as never having finished.

A real usage-limit event was FIRST observed on 2026-07-10 during CS-A3
batch 2 (claude/mcp/service, n=1): Claude Code wrapped it as
`"Agent terminated early due to an API error: You've hit your session limit
· resets 6:10am (UTC)"`. That exposed a real bug in the original ordering —
the generic network phrase "api error" (checked first) shadowed the true
cause, mislabelling a usage limit as a network truncation. Since the label
drives retry TIMING (a network blip can retry immediately; a session limit
must wait for the reset), the specific categories (usage_limit, rate_limit)
are now checked BEFORE the generic network_truncation, and "session limit"
is a usage_limit signature. Everything else here still follows the same
discipline used across this harness: grow the phrase list from real
occurrences, matched as text against the raw transcript + stderr, not an
elaborate structured-event parser for shapes not yet seen. The earlier
confirmed incident (a dropped connection mid-task, "API Error: Connection
closed mid-response") remains under network_truncation.
"""
from __future__ import annotations

import re

# Phrases indicating the SESSION was cut short by something outside the
# agent's own task — a dropped connection, a rate limit, or a subscription
# usage cap — as opposed to the agent choosing to stop, decline, or run out
# of turns on its own. Checked against raw transcript text + stderr.
# Order matters: the SPECIFIC subscription/rate categories come first, so a
# session-limit message that Claude Code happens to wrap as "an API error"
# is labelled by its true cause (usage_limit) rather than the generic
# network phrase that also matches it. detect_incomplete_reason returns the
# first category with any hit.
INCOMPLETE_SIGNATURES: dict[str, tuple[str, ...]] = {
    "usage_limit": (
        # Confirmed 2026-07-10 (claude/mcp/service, CS-A3 batch 2): Claude
        # Code prints "You've hit your session limit · resets <time>". The
        # rest are the plainest phrasing either CLI's usage-limit messaging
        # would plausibly use; extend/correct from real occurrences.
        "session limit",
        "usage limit",
        "quota exceeded",
        "resets at",
        "upgrade your plan",
    ),
    "rate_limit": (
        "rate_limit_error",
        "rate limit exceeded",
        "429 too many requests",
    ),
    "network_truncation": (
        # The first real incident this project had: a dropped connection
        # mid-task, confirmed via a real pilot run (27 real tool calls, zero
        # diff, this exact phrase in the final result text). "api error" is
        # deliberately LAST — Claude Code also wraps a session limit as "an
        # API error", so a genuine network drop is only what reaches here
        # without matching a more specific category above.
        "api error",
        "connection closed",
        "connection reset",
        "overloaded_error",
    ),
}


def detect_incomplete_reason(text: str) -> str | None:
    """text should be the raw transcript + stderr, lowercased already or not
    (matching is case-insensitive). Returns the first matching category name,
    or None. Category order matters for the returned label when multiple
    phrases could match the same incident — the specific subscription/rate
    categories are checked before the generic network_truncation (see the
    INCOMPLETE_SIGNATURES comment and the 2026-07-10 real occurrence in the
    module docstring)."""
    lowered = text.lower()
    for reason, phrases in INCOMPLETE_SIGNATURES.items():
        if any(p in lowered for p in phrases):
            return reason
    return None


# Kept as a flat tuple too, for callers (harness/run_study.py) that only need
# the "was this run truncated at all" check, not which specific category.
ALL_INCOMPLETE_PHRASES: tuple[str, ...] = tuple(
    p for phrases in INCOMPLETE_SIGNATURES.values() for p in phrases
)
