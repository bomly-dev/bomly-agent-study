# Manual adjudications

Every mechanical scoring override, logged. See cs-a-design.md §3 — manual
adjudication is bounded to specific pre-registered case types, never used to
relitigate an outcome we just don't like.

## (resolved in code — no longer a manual adjudication) codex/mcp/3 S9

An earlier version of this file adjudicated `runs-pilot/codex/mcp/3` S9
(jackson-databind) from a mechanical HALLUCINATED to ATTEMPTED_NOT_FIXED. That
adjudication is withdrawn: the underlying scoring bug is now fixed in code, and
the mechanical scorer returns the correct outcome (FIXED) on its own.

**Root cause (the bug, now fixed):** `score_slot()`'s second-scanner check was
package-*name*-scoped — "does this package name appear anywhere in the scanner
output" — so any real fix of a package that ALSO carries a different, untracked
advisory was misscored. jackson-databind bumped 2.13.0 → 2.18.8/2.22.0 clears
the slot's three tracked CVEs (CVE-2020-36518, CVE-2022-42003, CVE-2022-42004),
but trivy still reports jackson-databind for OTHER CVEs (e.g. CVE-2026-54515)
that affect both versions and are not what S9 tests. The old check saw the name
and marked the slot still-vulnerable.

Note this was NOT a post-freeze-drift problem — those other CVEs are present at
freeze too, so "was the advisory in the frozen baseline" does not separate them.
Only matching the slot's OWN tracked advisories does.

**The fix (harness/verify.py):** second-scanner matching is now advisory-ID-
scoped. All three scanners emit JSON; the scorer extracts advisory IDs per
package and, for pypi/maven (where pip-audit's aliases and trivy's
VulnerabilityID both expose the CVE), intersects them with the slot's own
tracked CVEs. npm audit emits only GHSA ids, so npm falls back to the frozen
freeze-era GHSA set for the package (scoring/second-scanner-baseline.json),
which is drift-safe.

**Side effect worth noting:** the same bug was also *falsely* scoring genuine
bare-condition S9 fixes (claude/bare/3, codex/bare/3, both of which bumped
jackson-databind to 2.22.0) as HALLUCINATED. After the fix, S9 is FIXED in all
four run-3 cells. An earlier summary that read S9 as "hallucinated bare, fixed
under mcp — the clearest MCP signal" was itself an artifact of this scoring bug,
not a real condition difference. Corrected in the run-3 results.

(No open manual adjudications at this time.)
