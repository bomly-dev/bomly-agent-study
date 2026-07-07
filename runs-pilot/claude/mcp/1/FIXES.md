# Dependency vulnerability remediation

Findings from `bomly_scan` (enrich + audit) against each fixture, and the
action taken for each. One entry per package.

## fixtures/webapp (npm)

| Package | Found | Action |
|---|---|---|
| `axios` | 1.6.0 — 26 advisories (SSRF, prototype pollution, credential/header leaks, ReDoS, DoS), up to critical/high | **Fixed.** Bumped to `1.16.0` (`package.json`), the lowest version clearing every advisory. |
| `express` | 4.19.2 — GHSA-qw6h-vgh9-j6wx, XSS via `response.redirect()` | **Fixed.** Bumped to `4.22.2`. This also pulls forward the transitive deps below. |
| `jsonwebtoken` | 8.5.1 — GHSA-8cf7-32gw-wr33 (unrestricted key type), GHSA-hjrf-2m68-5959 (RSA→HMAC key confusion), GHSA-qwph-4952-7xr6 (signature validation bypass) | **Fixed.** Bumped to `9.0.0`. `src/auth.js` has a comment warning it's written against 8.x semantics; verified with the full test suite (`npm test`) that sign/verify/decode behavior used by this app is unaffected — all 12 tests still pass. |
| `lodash` (devDependency) | 4.17.20 — GHSA-29mw-wpgm-hmr9 (ReDoS), GHSA-35jh-r3h4-6jhm (command injection), GHSA-f23m-r3pf-42rh / GHSA-xxjr-mmjv-4gpg (prototype pollution), GHSA-r5fr-rjxr-66jc (code injection via `_.template`) | **Fixed.** Bumped to `4.18.1`. bomly's reported minimum safe version was `4.18.0`, but npm marks that exact release deprecated ("Bad release. Please use lodash@4.17.21 instead"); used `4.18.1` (current `latest` dist-tag, not deprecated, still ≥4.18.0) instead. |
| `serve-static`, `send`, `body-parser`, `cookie`, `path-to-regexp`, `qs` (express's copy) | Transitive vulnerabilities via `express@4.19.2` (template-injection XSS, DoS, ReDoS) | **Fixed automatically** by the `express` bump above — express 4.22.2's own manifest pins newer, patched ranges for all of these (verified via `npm ls`: serve-static 1.16.3, send 0.19.2, body-parser 1.20.5, cookie 0.7.2, path-to-regexp 0.1.13, qs 6.15.3). |
| `request` | 2.88.2 — GHSA-p8p7-x288-28g6, SSRF (CVE-2023-28155) | **Not fixed — no fixed version exists.** 2.88.2 is the latest published release; the package has been deprecated since 2020 with no further releases. `bomly_vuln_fix_context` reports `fix_state: "not-fixed"` for this advisory. Left at the current version; still used by `src/importer.js` for the legacy XML-feed fetch. |
| `tough-cookie`, `form-data`, `qs` (request's own bundled copy), `uuid` | Transitive vulnerabilities pulled in solely via `request@2.88.2` (prototype pollution, unsafe boundary/CRLF injection, arrayLimit DoS, buffer bounds check) | **Not fixed — cannot be remediated without breaking `request`.** Fixed versions exist upstream in isolation, but `request`'s own `package.json` pins old ranges, and `request` has had no release since 2.88.2 to pick them up. Tried forcing newer versions via npm `overrides`; confirmed this breaks `request` outright: `request/lib/auth.js`, `lib/oauth.js`, and `lib/multipart.js` all do `require('uuid/v4')` at module load, a deep-import path that no longer exists once `uuid` is bumped past v6 — so requiring `request` at all throws. Left unfixed and documented rather than shipping a broken override. |

## fixtures/api-java (Maven)

| Package | Found | Action |
|---|---|---|
| `jackson-databind` | 2.13.0 — 9 advisories, including several high-severity DoS/deserialization/PolymorphicTypeValidator-bypass issues | **Mostly fixed.** Bumped to `2.18.8`, clearing 8 of the 9 advisories (GHSA-3wrr-7qpf-2prh, GHSA-3x8x-79m2-3w2w, GHSA-57j2-w4cx-62h2, GHSA-hgj6-7826-r7m5, GHSA-j3rv-43j4-c7qm, GHSA-jjjh-jjxp-wpff, GHSA-rgv9-q543-rqg4, GHSA-rmj7-2vxq-3g9f). GHSA-5jmj-h7xm-6q6v (case-insensitive deserialization bypass of per-property `@JsonIgnoreProperties`, CVE-2026-54515) is reported by bomly as `fix_state: "not-fixed"` — no released version fixes it as of this scan, so it remains present after the upgrade. |
| `commons-configuration2` | 2.7 — GHSA-337m-mw94-2v6g, GHSA-9w38-p64v-xpmv, GHSA-xjp4-hw94-mvp5 (StackOverflow DoS via cyclical config objects), GHSA-xj57-8qj4-c4m6 (critical: code injection, CVE-2022-33980) | **Fixed.** Bumped to `2.15.0`, clearing all 4 advisories. |
| `junit-jupiter` | 5.10.2 — flagged only for "invalid SPDX license" (license string `Eclipse Public License v2.0` isn't a recognized SPDX identifier) | **No action.** This is a license-metadata warning, not a vulnerability. |

Verified with `mvn test` (online, to pull the new artifacts) and `mvn -o test` (offline, matching the `make test-java` target) — 4/4 tests pass both ways.

## fixtures/service (Python / pip)

`bomly_scan --enrich --audit` found **zero vulnerabilities** across all 31 packages resolved from `requirements.txt` / `requirements-dev.txt`. The only two findings were license-metadata warnings, not vulnerabilities:

- `defusedxml` 0.7.1 — "invalid SPDX license: non-standard"
- `pip-audit` 2.10.1 — "invalid SPDX license: non-standard"

No dependency changes made in this fixture.
