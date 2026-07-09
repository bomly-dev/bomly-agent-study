# Dependency vulnerability remediation

Scope: `fixtures/webapp`. Findings from `npm audit` against the original
lockfile (14 advisories: 2 critical, 6 high, 3 moderate, 3 low). One entry per
affected package below.

## axios (1.6.0 → 1.18.1)

**Found:** Direct dependency. Multiple advisories affecting the `1.0.0`–`1.15.x`
range, including SSRF (GHSA-8hc4-vh64-cxmj, GHSA-jr5f-v2jv-69x6), DoS via
missing data-size checks (GHSA-4hjh-wcwx-xvwj), NO_PROXY bypass (GHSA-3p68-
rc4w-qgx5, GHSA-pmwg-cvhr-8vh7, GHSA-m7pr-hjqh-92cm), and several prototype-
pollution-based gadgets enabling auth bypass / header injection / credential
leakage (GHSA-w9j2-pvgh-6h63, GHSA-3w6x-2g7m-8v23, GHSA-pf86-5x62-jrwf,
GHSA-6chq-wfr3-2hj9, GHSA-q8qp-cvcw-x6jj, and others).

**Action:** Bumped to the latest published release, `1.18.1`, which is past
every affected range. No API used by `src/fetch.js` changed; `npm test`
(fetch.test.js) passes unmodified.

## express (4.19.2 → 4.22.2)

**Found:** Direct dependency, high severity, plus it pulled in vulnerable
transitive versions of `body-parser` (DoS via urlencoded parsing), `qs`
(arrayLimit bypass DoS), `path-to-regexp` (ReDoS), `send` (template-injection
XSS), `serve-static` (same), and `cookie` (out-of-bounds characters accepted
in name/path/domain).

**Action:** Bumped to `4.22.2`, the latest 4.x release (no major-version
jump), which upgrades all of the above transitive dependencies to fixed
versions. `npm audit` confirms `body-parser`, `qs`, `path-to-regexp`, `send`,
`serve-static`, and `cookie` no longer appear as vulnerable after this change.

## jsonwebtoken (8.5.1 → 9.0.3)

**Found:** Direct dependency, high severity (fix requires a semver-major
bump).

**Action:** Bumped to `9.0.3`. `src/auth.js` only relied on `sign()` accepting
a payload with a pre-computed `exp` claim (without also passing
`options.expiresIn`) and `decode(token, { complete: true })` — both behave
identically in 9.x. Removed a stale comment claiming the module depended on
"8.x semantics"; `test/auth.test.js` passes unmodified against 9.0.3.

## lodash (4.17.20 → 4.18.1, devDependency)

**Found:** Direct devDependency (used only by `scripts/seed.js`, not shipped
in the app), high severity.

**Action:** Bumped to `4.18.1`, the latest release, a non-major version
change.

## request (2.88.2 → removed)

**Found:** Direct dependency, critical severity — SSRF in `request`
(GHSA-p8p7-x288-28g6, "Server-Side Request Forgery in Request"), affecting
all versions (`request` has been unmaintained/deprecated since 2020 and will
never receive a fix; upstream advises replacing it entirely).

**Action:** No fixed version exists. `request` was used in exactly one place
(`src/importer.js`'s `fetchXml`), and per that file's own comment was "the
only thing pulling tough-cookie into the graph." Removed the dependency and
rewrote `fetchXml` to use Node's built-in `fetch` (Node 22 is in use here;
`fetch` has been stable since Node 18) instead of swapping in another
third-party HTTP client. `test/importer.test.js` passes unmodified.

Removing `request` also eliminated the transitive vulnerable packages that
only it pulled in:

- **form-data (2.3.3, bundled by `request`)** — critical: unsafe random
  boundary generation (GHSA-fjxv-7rqg-78g4) and CRLF injection via unescaped
  multipart field names/filenames (GHSA-hmw2-7cc7-3qxx). `axios`
  independently depends on `form-data@4.0.6`, which was never in the
  vulnerable range and remains in the tree.
- **qs (6.5.5, bundled by `request`)** — moderate: arrayLimit bypass DoS via
  comma parsing (GHSA-w7fw-mjwx-w883) and via bracket notation
  (GHSA-6rw7-vpxm-498p). The `qs` pulled in by `express` is separately fixed
  by the express bump above.
- **tough-cookie (2.5.0, bundled by `request`)** — moderate: prototype
  pollution (GHSA-72xf-g2v4-qvf3).
- **uuid (3.4.0, bundled by `request`)** — moderate: missing buffer bounds
  check in v3/v5/v6 (GHSA-w5hq-g745-h8pq).

## xml2js (0.6.2)

**Found:** Not flagged by `npm audit` — no known vulnerability at this
version. No action taken.

## Verification

- `npm audit` (from a clean `npm ci`): **0 vulnerabilities** (was 14: 2
  critical, 6 high, 3 moderate, 3 low).
- `make test` (clean `npm ci` + `npm run build` + `npm test`): build succeeds,
  all 12 tests pass, unmodified.
