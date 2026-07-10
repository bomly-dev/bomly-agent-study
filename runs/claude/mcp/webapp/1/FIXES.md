# Dependency vulnerability remediation

Scope: `fixtures/webapp` (npm project `team-bookmarks`). All findings were
identified with the `bomly` MCP server (`bomly_scan`/`bomly_explain`,
enrich+audit) and cross-checked with `npm audit` after the fix.

Baseline scan: 135 packages, 15 vulnerable (39 findings: 1 critical, 16 high,
17 medium, 5 low). Final scan: 88 packages, 0 vulnerable.

## request (2.88.2) — removed

- **Found:** `request` is deprecated/unmaintained and has no fixed release
  for its own SSRF advisory `GHSA-p8p7-x288-28g6` (CVE-2023-28155). It also
  pulled in four vulnerable transitive packages: `form-data@2.3.3`
  (`GHSA-fjxv-7rqg-78g4` critical / CVE-2025-7783 unsafe multipart boundary
  randomness, and `GHSA-hmw2-7cc7-3qxx` high / CVE-2026-12143 CRLF
  injection), `qs@6.5.5` (`GHSA-6rw7-vpxm-498p` medium / CVE-2025-15284
  arrayLimit DoS), `tough-cookie@2.5.0` (`GHSA-72xf-g2v4-qvf3` medium /
  CVE-2023-26136 prototype pollution), and `uuid@3.4.0` (`GHSA-w5hq-g745-h8pq`
  medium / CVE-2026-41907 missing buffer bounds check).
- **Changed:** Since the package's own SSRF vulnerability has no upstream
  fix, version-bumping or overriding transitives would still leave an
  unpatched, deprecated dependency in place. Removed `request` entirely and
  rewrote its one call site (`src/importer.js: fetchXml`) to use `axios`,
  which the project already depends on and already uses the same way in
  `src/fetch.js`. This eliminates `request` and all four vulnerable
  transitives from the dependency graph.
- **Why:** Full removal is the only way to close the no-fix-upstream SSRF
  finding, and it also removes the transitive vulnerabilities as a side
  effect instead of papering over them with `overrides` on a package that
  will never be patched.

## axios (1.6.0 → 1.16.0) — direct version bump

- **Found:** 15 findings ranging medium→high, including SSRF/credential
  leakage via prototype-pollution gadgets in config/proxy merging
  (`GHSA-35jp-ww65-95wh`/CVE-2026-44494, `GHSA-3g43-6gmg-66jw`/CVE-2026-44495,
  `GHSA-898c-q2cr-xwhg`/CVE-2026-44490), header injection
  (`GHSA-6chq-wfr3-2hj9`/CVE-2026-42035, `GHSA-445q-vr5w-6q77`/CVE-2026-42037),
  DoS via `__proto__` key, unbounded recursion, or missing size checks
  (`GHSA-43fc-jf86-j433`/CVE-2026-25639, `GHSA-4hjh-wcwx-xvwj`/CVE-2025-58754,
  `GHSA-62hf-57xw-28j9`/CVE-2026-42039, `GHSA-hfxv-24rg-xrqf`/CVE-2026-44496),
  SSRF via proxy/redirect/NO_PROXY handling
  (`GHSA-8hc4-vh64-cxmj`/CVE-2024-39338, `GHSA-3p68-rc4w-qgx5`/CVE-2025-62718,
  `GHSA-fvcv-3m26-pcqx`/CVE-2026-40175, `GHSA-j5f8-grm9-p9fc`/CVE-2026-44486),
  and CRLF/JSON tampering (`GHSA-445q-vr5w-6q77`, `GHSA-3w6x-2g7m-8v23`/CVE-2026-42044,
  `GHSA-5c9x-8gcm-mpgx`/CVE-2026-42034).
- **Changed:** Bumped the direct dependency to `1.16.0`, which fixes all of
  the above.
- **Why:** Direct dependency, straightforward version bump, no API changes
  used by this project's `src/fetch.js` were affected (verified by running
  the test suite).

## express (4.19.2 → 4.22.2) — direct version bump

- **Found:** Direct finding `GHSA-qw6h-vgh9-j6wx`/CVE-2024-43796 (XSS via
  `response.redirect()`, low). Plus transitive findings pulled in by
  `express`: `path-to-regexp@0.1.7` (three ReDoS advisories —
  `GHSA-37ch-88jc-xwx2`/CVE-2026-4867, `GHSA-9wv6-86v2-598j`/CVE-2024-45296,
  `GHSA-rhx6-c78j-4q9w`/CVE-2024-52798, all high), `body-parser@1.20.2`
  (`GHSA-qwcr-r2fm-qrc7`/CVE-2024-45590 DoS, high), `qs@6.11.0`
  (`GHSA-6rw7-vpxm-498p`/CVE-2025-15284 and `GHSA-w7fw-mjwx-w883`/CVE-2026-2391,
  medium/low DoS), `serve-static@1.15.0`/`send@0.18.0` (template-injection
  XSS — `GHSA-cm22-4g7w-348p`/CVE-2024-43800, `GHSA-m6fv-jmcg-4jfg`/CVE-2024-43799,
  low), and `cookie@0.6.0` (`GHSA-pxg6-pf52-xh8x`/CVE-2024-47764, out-of-bounds
  cookie characters, low).
- **Changed:** Initially bumped to `4.20.0` (the version needed for the
  direct XSS fix) with `package.json` `overrides` pinning
  `path-to-regexp@0.1.13`, `body-parser@1.20.3`, `qs@6.14.2`. On
  verification, `npm audit` still flagged a residual `qs` DoS
  (`GHSA-q8mj-m7cp-5q26`, affecting qs `>=6.11.1 <=6.15.1`, which includes
  `6.14.2`) and showed `body-parser`/`cookie` still resolving to vulnerable
  versions. Replaced that approach with a plain bump to `express@4.22.2`
  (current latest 4.x), which pulls already-patched
  `path-to-regexp@~0.1.12` (resolves to `0.1.13`), `body-parser@~1.20.5`
  (resolves to `1.20.6`), `qs@~6.15.1` (resolves to `6.15.3`, fixed for
  `GHSA-q8mj-m7cp-5q26`), `cookie@~0.7.1` (resolves to `0.7.2`), and
  `send@~0.19.0`/`serve-static@~1.16.2` (resolve to `0.19.2`/`1.16.3`). No
  `overrides` entry was needed in the end.
  `npm audit` reports 0 vulnerabilities after this change.
- **Why:** A same-major (4.x) bump avoids any Express 5/6 breaking-change
  risk while fully closing every finding, including one that only showed up
  after installing and re-auditing (the pinned-override approach would have
  silently left `qs` vulnerable).

## jsonwebtoken (8.5.1 → 9.0.0) — direct version bump

- **Found:** `GHSA-8cf7-32gw-wr33`/CVE-2022-23539 (unrestricted key type
  usage, high), `GHSA-hjrf-2m68-5959`/CVE-2022-23541 (insecure key-retrieval
  default enabling RSA→HMAC token forgery, medium), `GHSA-qwph-4952-7xr6`/
  CVE-2022-23540 (`jwt.verify()` insecure default algorithm allowing
  signature-validation bypass, medium).
- **Changed:** Bumped to `9.0.0`. `src/auth.js` has a comment noting it was
  written against 8.x semantics and that `test/auth.test.js` exercises that
  behavior; verified after the bump that all sign/verify/decode tests
  (HS256 signing, payload-embedded `exp`, `decode(complete)`, login/`/me`
  round trip, garbage-token rejection) still pass unchanged — this project
  only uses HS256 with a plain secret, which the 9.x algorithm/key-type
  restrictions don't affect.
- **Why:** Direct dependency, fixes are only available via the 9.x major
  version; confirmed no behavioral break via the existing test suite.

## lodash (4.17.20 → 4.18.1) — direct version bump (devDependency)

- **Found:** `GHSA-35jh-r3h4-6jhm`/CVE-2021-23337 (command injection, high),
  `GHSA-r5fr-rjxr-66jc`/CVE-2026-4800 (`_.template` code injection via
  import key names, high), `GHSA-29mw-wpgm-hmr9`/CVE-2020-28500 (ReDoS,
  medium), `GHSA-f23m-r3pf-42rh`/CVE-2026-2950 (prototype pollution via
  array-path bypass in `_.unset`/`_.omit`, medium), `GHSA-xxjr-mmjv-4gpg`/
  CVE-2025-13465 (prototype pollution in `_.unset`/`_.omit`, medium).
- **Changed:** Initially bumped to the bomly-recommended `4.18.0`, but `npm
  install` flagged it as deprecated ("Bad release. Please use lodash@4.17.21
  instead."). Used `4.18.1` instead — the current `latest` on the npm
  registry, not deprecated, and a superset fix (newer than 4.18.0, so it
  still covers every advisory above).
- **Why:** devDependency only used by `scripts/seed.js`; version bump is
  low risk, but the registry's own deprecation notice on 4.18.0 was worth
  respecting rather than blindly taking the first "fixed_in" version.

## xml2js (0.6.2) — no action

- **Found:** No vulnerabilities reported by `bomly_explain` for this
  package at the version in use.
- **Changed:** Nothing.
- **Why:** Not vulnerable; left as-is per the "don't change what
  remediation doesn't require" constraint.

## Verification

- `npm audit` (fixtures/webapp): 0 vulnerabilities (was 6 after the first
  express/lodash attempt, confirming the follow-up fixes were needed).
- `bomly_scan --enrich --audit` (fixtures/webapp): 88/88 packages clean (was
  15/135 vulnerable, 39 findings).
- `make test` (repo root): clean `npm ci`, `npm run build`, and `npm test`
  (12/12 tests passing, including the jsonwebtoken 9.x-sensitive auth tests
  and the axios-based `fetchXml` replacement for `request`).
