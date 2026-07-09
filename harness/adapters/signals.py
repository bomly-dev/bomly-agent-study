"""Shared incomplete-session detection, used by both agent adapters and by
harness/run_study.py's orchestrator-level check.

v3 (2026-07-09, Ahmed): a session that hits an AI usage/rate limit mid-task
must be marked INCOMPLETE — distinct from a real low score — and retried
after the allowance resets, not scored or pooled into the real numbers.
Under v3's full-surface scoring, this matters more than it used to: a
partial remediation of a "fix everything" task looks like genuine low
completeness unless the run is flagged as never having finished.

No real usage-limit event has been observed in any of the ~26 real Claude
Code / Codex runs collected so far (checked directly against every
committed transcript before writing this) — both agents' documented
structured-error signals (Claude's `result.subtype`, Codex's per-event
schema) have no confirmed usage-limit-specific shape to match on yet. This
starts from the one incident that DID happen for real this session (a
dropped API connection mid-task, "API Error: Connection closed mid-response"
— see TRUNCATION_SIGNATURES below, originally found in harness/run_study.py)
plus the plainest, most likely human-readable phrasing either CLI would use
for a subscription/rate limit, matched as text against the raw transcript
and stderr rather than a specific structured event. Grow this list from real
occurrences as they happen, the same discipline used everywhere else in this
harness — do not invent an elaborate structured-event parser for a failure
mode that hasn't been observed yet.
"""
from __future__ import annotations

import re

# Phrases indicating the SESSION was cut short by something outside the
# agent's own task — a dropped connection, a rate limit, or a subscription
# usage cap — as opposed to the agent choosing to stop, decline, or run out
# of turns on its own. Checked against raw transcript text + stderr.
INCOMPLETE_SIGNATURES: dict[str, tuple[str, ...]] = {
    "network_truncation": (
        # The one real incident this session had: a dropped connection
        # mid-task, confirmed via a real pilot run (27 real tool calls, zero
        # diff, this exact phrase in the final result text).
        "api error",
        "connection closed",
        "connection reset",
        "overloaded_error",
    ),
    "rate_limit": (
        "rate_limit_error",
        "rate limit exceeded",
        "429 too many requests",
    ),
    "usage_limit": (
        # Not yet observed in a real transcript — the plainest phrasing
        # either CLI's own usage-limit messaging would plausibly use.
        # Extend/correct from a real occurrence, don't guess further.
        "usage limit",
        "quota exceeded",
        "resets at",
        "upgrade your plan",
    ),
}


def detect_incomplete_reason(text: str) -> str | None:
    """text should be the raw transcript + stderr, lowercased already or not
    (matching is case-insensitive). Returns the first matching category name,
    or None. Category order matters only for the returned label when
    multiple phrases could match the same incident — check network_truncation
    first since that category's phrases are the ones actually confirmed
    against a real run."""
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
