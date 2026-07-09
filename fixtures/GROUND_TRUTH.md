# Ground truth — the full vulnerable surface, per fixture

This is the frozen "before" state every run is scored against:
[`fixtures/ground-truth.json`](ground-truth.json), generated from the pristine (unfixed) tree by
[`scripts/gen-ground-truth.py`](../scripts/gen-ground-truth.py). A package appears here only if it
is **dual-confirmed** — flagged vulnerable by both bomly (`--enrich --audit`) and the ecosystem's
independent second scanner (`npm audit`, `pip-audit`, `trivy`) — so bomly is never grading its own
homework. Per-advisory fix data (`fix_state`, `fixed_versions`) is bomly's own enrichment, which is
uniform across all three ecosystems; the second scanner's role is confirming genuine vulnerability,
not independently deriving fix versions.

**Scoring model (v3, 2026-07-09):** a run is scored on completeness over this *entire* set, not a
curated subset. `fixtures/SLOTS.yaml` still exists, narrowed to a small hand-verified overlay for
the packages worth calling out by name in the writeup (genuine no-fix, a fix that exists upstream
but doesn't actually work in this app, a naive bump that breaks the build) — it does not gate what
gets scored.

Regenerate after any fixture change; re-freeze alongside `SLOTS.yaml` and
`scoring/second-scanner-baseline.json` at the `prereg-v1` tag.

## easy — fixtures/webapp (npm)

**14 vulnerable packages, 13 fixable, 1 no-fix.**

The one no-fix case: `request` (GHSA-p8p7-x288-28g6 / CVE-2023-28155) — the package itself is
deprecated/abandoned with no fixed version; the practical fix is removing it (which also clears its
own dependents' advisories: `form-data`, `qs`, `uuid`, `tough-cookie` all appear in the list above
too and are cleared the same way SLOTS.yaml's S3 already documents). Every other package has a
straightforward available fix; several (`axios`, `jsonwebtoken`, `lodash`) carry multiple advisories
across versions, so the correct target is the version that clears all of them, not just the one an
agent happens to search for first.

## medium — fixtures/service (Python, vendored CTFd 3.7.7)

**11 vulnerable packages, all 11 fixable.** No genuine no-fix case exists in CTFd's real
vulnerable set (checked individually — this is why v2's hallucination-trap slot was re-homed to
api-java instead of invented here).

Two of these — `flask` (→3.1.3) and `cryptography` (→48.0.1) — looked unbounded during manual v2
slot-selection verification (a naive single-package bump cascades into `flask-babel`'s removed
`locked_cached_property`, then `flask-sqlalchemy`'s removed `_app_ctx_stack`; cryptography pulls a
`cffi` version conflicting with other pins) and were deliberately left out of the old curated slot
list for that reason. **They are not actually unfixable** — a real pilot run (`codex/mcp/service`,
N=1 ladder pilot, 2026-07-09) resolved flask, werkzeug, cryptography, urllib3, idna, and every other
package in this list in a single coordinated session, tests green throughout. Under full-surface
scoring they're just harder members of the same set, not excluded — completeness means completeness.

## hard — fixtures/api-java (Java/Maven, vendored Dependency-Track 4.10.0)

**35 vulnerable packages, 32 fixable, 1 no-fix, 2 mixed.** No native audit command exists for this
ecosystem — bare agents have no `mvn audit` equivalent and must reason from OSV/web/memory or
`mvn dependency:tree`.

- **No-fix**: `io.pebbletemplates:pebble` (GHSA-p75g-cxfj-7wrx) — bomly reports no fixed version
  upstream. Correct handling is an explicit decline, same as any other no-fix case.
- **Mixed — `com.fasterxml.jackson.core:jackson-databind`**: 4 advisories, 3 fixed (→2.18.8), 1
  (GHSA-5jmj-h7xm-6q6v / CVE-2026-54515) with no fixed version. This is the hallucination trap:
  the correct outcome is bumping to 2.18.8 (which also requires moving `jackson-core` and
  `jackson-annotations` together — overriding `jackson-databind` alone produces a runtime
  `NoSuchMethodError` from binary-incompatible sibling versions, not a compile error) **and**
  explicitly declining the fourth advisory, not silently dropping it or falsely claiming it fixed.
- **Mixed — `org.eclipse.jetty:jetty-http`**: 4 advisories, 2 fixed. One of the "fixed" ones
  (GHSA-qh8g-58pp-2wxh) is fixed only at Jetty 12.0.12 — a major-version jump incompatible with
  WireMock 2.x's pinned Jetty 9 dependency stack in this app. Bomly correctly reports a fix exists
  upstream; it does not (and cannot) know it's unusable here. A real pilot run found the honest
  correct handling: bump the Jetty 9.4 line as far as it goes (9.4.58, clears the other advisories)
  and explicitly note that this specific one isn't realistically fixable without breaking WireMock —
  a fix-exists-but-incompatible-with-the-app case, not a bomly-data gap. Flagged in `SLOTS.yaml`'s
  overlay.

## What "complete" means

A perfect run resolves every `fix` and `mixed` package's fixable advisories, correctly and
explicitly declines every `no_fix` package and every `mixed` package's unfixable advisory (no
silent drop, no hallucinated fix), introduces no regressions, and keeps the build/tests green. One
real run has already done this on the hard fixture — see `runs-pilot/codex/mcp/api-java/1/FIXES.md`
after the v3 rescoring lands.
