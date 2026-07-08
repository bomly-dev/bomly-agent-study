# Manual adjudications

Every mechanical scoring override, logged. See cs-a-design.md §3 — manual
adjudication is bounded to specific pre-registered case types, never used to
relitigate an outcome we just don't like.

## runs-pilot/codex/mcp/3, S9 (jackson-databind)

- **Mechanical outcome:** CORRECTLY_DECLINED
- **Adjudicated outcome:** ATTEMPTED_NOT_FIXED
- **Case type:** second-scanner CVE drift on an otherwise-fixed slot (new
  case type, not one of the two pre-registered at design time — added here
  because it surfaced in real data, same principle as growing the
  claims_declined phrase list from real transcripts rather than guessing).

**What happened:** the agent upgraded `jackson-databind` from `2.13.0` to
`2.18.8`, which resolves all three advisories SLOTS.yaml pins for S9
(CVE-2020-36518, CVE-2022-42003, CVE-2022-42004) — bomly agrees
(`bomly_still_flagged: false`). FIXES.md is explicit and honest about this:
it also separately flags GHSA-5jmj-h7xm-6q6v / CVE-2026-54515, a *different*,
newer advisory against `jackson-databind@2.18.8` that has no version-only
fix, and says so in the same sentence as the real fix. Trivy (the second
scanner) flags the package as still having a vulnerability
(`second_scanner_still_flagged: true`) — correctly, but for the newer,
out-of-scope advisory, not the one this slot is actually testing.

**Why not mechanical CORRECTLY_DECLINED:** `score_slot()`'s claims_declined
regex (harness/verify.py) matched "no version-only remediation exists" —
text that's genuinely true, but about the wrong CVE. The regex has no way to
tell "declined for the advisory this slot cares about" from "declined for
an unrelated advisory on the same package, in the same breath as fixing the
one that matters." Character-proximity bounding (tried: 150 chars) doesn't
cleanly separate this from the real S6 decline case — both sit at a similar
distance from the package name in their respective FIXES.md text. This isn't
a fixable regex bug without real semantic understanding of which CVE a given
clause refers to.

**Why not FIXED:** `second_scanner_still_flagged` is package-name-scoped, not
advisory-ID-scoped (harness/verify.py's `package_present()` / second-scanner
comparison functions) — it will flag any current CVE against the installed
version, including ones discovered after fixtures/SLOTS.yaml was frozen.
This is the "OSV drift" risk cs-a-design.md's pre-mortem already names
("frozen SLOTS.yaml is ground truth... new advisories out of scope by
pre-reg"), but the *scoring code* doesn't actually implement that scoping —
it should check second-scanner output against the slot's own pinned
advisory IDs, not just "does this package name appear in the scanner's
output at all." Worth fixing in harness/verify.py before the N=5 freeze;
not fixed here to avoid more regex/scoring changes mid-pilot-check without
re-verifying against a broader set of real runs first.

**Why ATTEMPTED_NOT_FIXED:** the agent made a real, substantive, correctly-
targeted fix (the tracked CVEs are gone per bomly). It isn't FIXED under the
pre-registered dual-scanner-agreement rule (second scanner disagrees, even
if for an out-of-scope reason). It isn't HALLUCINATED — nothing false was
claimed; the agent was more careful and transparent about scope than the
scoring script credits it for.
