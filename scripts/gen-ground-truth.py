#!/usr/bin/env python3
"""Freeze the FULL vulnerable-surface ground truth for the pristine fixtures.

v3 scoring change (2026-07-09, Ahmed): score completeness over every
vulnerable package a fixture has, not a curated subset of ~10 hand-picked
slots — a 35-package fixture is pointless to score against 3 of them. This
script enumerates that full surface once, at freeze time, from the PRISTINE
(unfixed) tree, and writes fixtures/ground-truth.json — the frozen "before"
state harness/verify.py scores every run against.

Per package, dual-confirmed (flagged by BOTH bomly --enrich --audit AND the
ecosystem's independent second scanner — the same agreement rule the old
SLOTS.yaml slots required, just applied to every vulnerable package instead
of a hand-picked few). Per advisory on that package: id, aliases, fix_state,
fixed_versions — taken from bomly's own enrichment, which is uniform across
all three ecosystems (the second scanner's per-advisory fix-version data
isn't: npm audit's `via` entries carry a vulnerable *range*, not a fix
target). The second scanner's role stays what it always was — confirming
the package is genuinely vulnerable, not bomly grading its own homework —
not independently deriving fix versions.

A package's `expected` is derived automatically:
  - "fix"              every advisory has fix_state == "fixed"
  - "no_fix"            every advisory has fix_state != "fixed"
  - "mixed"             some fixed, some not (e.g. jackson-databind: 3 fixed
                        CVEs + 1 with no fixed version yet) — both facts are
                        real and both are scored: the fixable ones must be
                        resolved, the unfixable one must be correctly left
                        alone / explicitly declined, not hallucinated.
  - "needs_adjudication" fix_state is missing/ambiguous — flag for a human,
                        never silently guessed.
`min_safe_version` is the max of every FIXED advisory's fixed_versions on
that package (the single bump that clears everything fixable), None if no
advisory is fixed.

Run inside the study Docker image, from a CLEAN checkout of the frozen
fixture tag (matches gen-second-scanner-baseline.py's invocation):

  docker run --rm -v "$PWD:/work/bomly-agent-study" -w /work/bomly-agent-study \
    -e BOMLY_STUDY_PIP_AUDIT=/opt/study-tools/bin/pip-audit \
    bomly-agent-study:harness \
    bash -lc 'cd fixtures/webapp && npm ci --silent >/dev/null 2>&1; cd /work/bomly-agent-study \
      && cd fixtures/service && python3.12 -m venv .venv-gt && .venv-gt/bin/pip install --quiet -r requirements.txt && cd /work/bomly-agent-study \
      && /opt/study-tools/bin/python scripts/gen-ground-truth.py \
      && rm -rf fixtures/webapp/node_modules fixtures/service/.venv-gt'

Regenerate whenever a fixture changes, and re-freeze alongside SLOTS.yaml
(now a narrow hand-verified overlay — see fixtures/SLOTS.yaml's header) and
scoring/second-scanner-baseline.json.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "harness"))
import verify  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# Authoritative dir->ecosystem map lives in harness/verify.py (which also knows
# which fixtures are bomly-only, need the maven-detector, etc.) — reuse it so the
# two never drift.
FIXTURE_ECOSYSTEM = verify.FIXTURE_ECOSYSTEM


def _bomly_package_advisories(bomly_scan_result: dict) -> dict[str, list[dict]]:
    """{bare_package_name: [ {id, aliases, fix_state, fixed_versions, severity}, ... ]}"""
    out: dict[str, list[dict]] = {}
    for pkg in bomly_scan_result.get("packages", []) or []:
        name = (pkg.get("name") or "").lower()
        vulns = pkg.get("vulnerabilities") or []
        if not name or not vulns:
            continue
        entries = []
        for v in vulns:
            entries.append({
                "id": str(v.get("id", "")).upper(),
                "aliases": sorted({str(a).upper() for a in (v.get("aliases") or [])}),
                "fix_state": v.get("fix_state"),
                "fixed_versions": v.get("fixed_versions") or [],
                "severity": v.get("severity"),
            })
        out[name] = entries
    return out


def _max_version(versions: list[str]) -> str | None:
    """Best-effort "highest" version for picking a single target bump. Not a
    full semver comparator (a real one would need per-ecosystem rules), so
    this sorts version tuples numerically where possible and falls back to
    lexicographic — good enough to pick a target among a package's own fixed
    versions, which are usually monotonic within one advisory feed. Verified
    manually per-package in SLOTS.yaml's overlay for anything that matters
    for the writeup; this is ground-truth data, not the final claim."""
    if not versions:
        return None

    def key(v: str) -> tuple:
        parts = re.split(r"[.\-+]", v)
        return tuple((0, int(p)) if p.isdigit() else (1, p) for p in parts)

    return sorted(set(versions), key=key)[-1]


def build_fixture_ground_truth(fixture: str) -> dict:
    ecosystem = FIXTURE_ECOSYSTEM[fixture]
    bomly_result = verify.bomly_scan(REPO_ROOT, fixture)
    bomly_advisories = _bomly_package_advisories(bomly_result)

    bomly_only = fixture in verify.BOMLY_ONLY_FIXTURES
    if bomly_only:
        # No independent second scanner (the transitive Maven surface can't be
        # dual-confirmed by trivy — see verify.BOMLY_ONLY_FIXTURES). bomly's
        # native maven-detector resolution is the ground truth; every package
        # is recorded as bomly-trusted rather than adjudication-flagged.
        second_ids = {}
    else:
        second_raw = verify.second_scanner(REPO_ROOT, ecosystem)
        second_ids = verify.extract_advisory_ids(ecosystem, second_raw)
    # Second-scanner package keys aren't always the bare name bomly uses
    # (trivy: "group:artifact"), so build a set of all-IDs-seen for a
    # simpler presence check: dual-confirmed means the package's OWN
    # advisory IDs (or their aliases) appear somewhere in what the second
    # scanner reported for that package.
    packages: dict[str, dict] = {}
    for name, advisories in sorted(bomly_advisories.items()):
        reported = (
            second_ids.get(name)
            or second_ids.get(f"{fixture}:{name}")
            or set()
        )
        # trivy keys by "group:artifact" or just artifact; try suffix match
        if not reported:
            for key, ids in second_ids.items():
                if key == name or key.endswith(f":{name}") or key.endswith(f"/{name}"):
                    reported = ids
                    break

        bomly_id_set = {a["id"] for a in advisories} | {al for a in advisories for al in a["aliases"]}
        dual_confirmed = bool(reported & bomly_id_set) if reported else False
        if bomly_only:
            # This fixture is scored on bomly alone by design (no second
            # scanner run) — not a confirmation failure.
            status_note = "bomly-trusted (no independent second scanner for transitive Maven)"
        elif not dual_confirmed:
            # Not every real vuln is independently confirmable this way (npm
            # audit's GHSA-only IDs vs a CVE-only bomly alias, etc.) — record
            # it anyway but flag for adjudication rather than silently
            # dropping a bomly-only finding from the ground truth.
            status_note = "bomly-only (second scanner did not independently confirm by ID)"
        else:
            status_note = "dual-confirmed"

        fixed = [a for a in advisories if a["fix_state"] == "fixed"]
        unfixed = [a for a in advisories if a["fix_state"] != "fixed"]
        if unfixed and any(a["fix_state"] is None for a in unfixed):
            expected = "needs_adjudication"
        elif fixed and unfixed:
            expected = "mixed"
        elif fixed:
            expected = "fix"
        else:
            expected = "no_fix"

        min_safe_version = _max_version([v for a in fixed for v in a["fixed_versions"]])

        packages[name] = {
            "advisories": advisories,
            "expected": expected,
            "min_safe_version": min_safe_version,
            "unfixable_advisory_ids": sorted(a["id"] for a in unfixed),
            "confirmation": status_note,
        }

    return {
        "ecosystem": ecosystem,
        "package_count": len(packages),
        "fixable_count": sum(1 for p in packages.values() if p["expected"] in ("fix", "mixed")),
        "no_fix_count": sum(1 for p in packages.values() if p["expected"] == "no_fix"),
        "mixed_count": sum(1 for p in packages.values() if p["expected"] == "mixed"),
        "needs_adjudication_count": sum(1 for p in packages.values() if p["expected"] == "needs_adjudication"),
        "packages": packages,
    }


def main() -> int:
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bomly_version": None,
        "fixtures": {},
    }
    for fixture in FIXTURE_ECOSYSTEM:
        print(f"scanning {fixture}...", file=sys.stderr)
        fg = build_fixture_ground_truth(fixture)
        out["fixtures"][fixture] = fg
        print(
            f"  {fixture}: {fg['package_count']} vulnerable packages "
            f"({fg['fixable_count']} fixable, {fg['no_fix_count']} no-fix, "
            f"{fg['mixed_count']} mixed, {fg['needs_adjudication_count']} need adjudication)",
            file=sys.stderr,
        )

    dest = REPO_ROOT / "fixtures" / "ground-truth.json"
    dest.write_text(json.dumps(out, indent=2, sort_keys=False) + "\n")
    print(f"wrote {dest.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
