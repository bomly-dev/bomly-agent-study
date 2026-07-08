# Dependency Vulnerability Remediation

Findings from `bomly_scan` (enrich + audit) against each fixture, and the
action taken for each. License/SPDX "policy_only" findings (e.g. JUnit,
Jinja2 flagged for non-standard SPDX metadata) are not vulnerabilities and
are omitted below.

## fixtures/webapp (npm)

| Package | Found | Action |
|---|---|---|
| `axios` 1.6.0 | 14 CVEs (SSRF, DoS, header/CRLF injection, prototype-pollution gadgets), critical–medium | Bumped direct dependency to **1.16.0**, which fixes all of them. |
| `express` 4.19.2 | Own XSS in `response.redirect()` (GHSA-qw6h-vgh9-j6wx), plus transitive `path-to-regexp`, `body-parser`, `qs`, `serve-static`, `send`, `cookie` CVEs | Bumped direct dependency to **4.22.2** (fixes the redirect XSS and pulls patched `body-parser`, `serve-static`, `send`, `cookie`, `qs`≥6.15.x). Added an `overrides` entry pinning **`path-to-regexp` to 0.1.13**, since even express's latest 4.x line still depends on `^0.1.12` which doesn't cover GHSA-37ch-88jc-xwx2. |
| `jsonwebtoken` 8.5.1 | 3 CVEs: unrestricted key type, RSA→HMAC key confusion, insecure default algorithm in `verify()` | Bumped direct dependency to **9.0.3**. |
| `lodash` 4.17.20 (dev) | 5 CVEs: command injection, `_.template` code injection, ReDoS, prototype pollution (`_.unset`/`_.omit`) | Bumped direct dependency to **4.18.1**. (4.18.0, the version the scanner initially pointed at, is flagged by npm as a "bad release" — `4.18.1` carries the same fixes without that warning.) |
| `request` 2.88.2 → `form-data`, `qs`, `tough-cookie` (transitive) | form-data unsafe-boundary RNG + CRLF injection; qs arrayLimit DoS; tough-cookie prototype pollution | Added `overrides` pinning **`form-data` 2.5.6**, **`qs` 6.15.3** (bumped past the recommended 6.14.2 — that version has its own newly-disclosed DoS, GHSA-q8mj-m7cp-5q26, per `npm audit`), **`tough-cookie` 4.1.3**. Kept these on the same major version as what `request` already vendors, since `request` is unmaintained and pulling a new major (e.g. tough-cookie 6.x) risks its internal API assumptions. |
| `request` 2.88.2 (own) | SSRF, GHSA-p8p7-x288-28g6 / CVE-2023-28155 | **No fixed version exists** — `request` is deprecated/unmaintained upstream and 2.88.2 is its final release. Not fixable by a version change; documented here per instructions rather than guessing at a replacement. `request` is used in exactly one place (`src/importer.js`, a legacy XML-feed importer) — replacing the library is a larger refactor than this remediation pass covers. |
| `request` 2.88.2 → `uuid` 3.4.0 (transitive) | Missing buffer bounds check in `uuid` v3/v5/v6 when a `buf` argument is supplied (GHSA-w5hq-g745-h8pq / CVE-2026-41907) | **Not remediated by overriding the version.** `request`'s internals (`lib/auth.js`, `lib/multipart.js`, `lib/oauth.js`) `require('uuid/v4')` — a deep-import path that only exists in uuid's legacy (no-`exports`-map) releases. Every uuid release that fixes this advisory (9.x+) ships an `exports` map that removes that subpath, so overriding breaks the build (`ERR_PACKAGE_PATH_NOT_EXPORTED`) — confirmed by testing the override. Separately, the vulnerable code path only triggers when the caller passes an explicit `buf` argument to `uuid()`; `request` always calls `uuid()` with no arguments, so this advisory isn't reachable through this app's dependency on `request` either way. Left at 3.4.0 and documented rather than forcing a breaking override.

## fixtures/service (Python)

| Package | Found | Action |
|---|---|---|
| `urllib3` 1.26.5 | 8 CVEs: decompression-bomb bypasses, cross-origin `Cookie`/`Proxy-Authorization` header leaks, redirect/retry handling gaps | Bumped to **2.7.0** in `requirements.txt` (and removed the now-stale comment noting the pin had drifted — `requests`'s own constraint is `urllib3<3,>=1.26`, so 2.7.0 is within bounds). |
| `pyjwt` 1.7.1 | 5 CVEs: unrestricted `crit` header handling, RSA/HMAC key-confusion, JWK-as-HMAC-secret forgery, `PyJWKClient` SSRF via arbitrary URL schemes, unbounded JWKS requests | Bumped to **2.13.0** in `requirements.in`/`requirements.txt`. This is a breaking change for `app/auth.py`, which was written against PyJWT 1.x semantics (`jwt.encode()` returning `bytes`, manually `.decode()`'d). Updated `make_token()` to use PyJWT 2.x's `str`-returning `encode()` directly and removed the now-inaccurate 1.x-behavior comments/docstring in `app/auth.py` and `tests/test_auth.py`. |
| `ecdsa` 0.19.2 | Minerva timing attack on P-256 (GHSA-wj6h-64fc-37mp / CVE-2024-23342), high | **No fixed version exists** — 0.19.2 is already the latest release on PyPI, and upstream has stated the pure-Python implementation can't give the constant-time guarantees needed to close this class of timing attack. Not fixable by a version change; documented here rather than guessing at a replacement. |

## fixtures/api-java (Maven)

| Package | Found | Action |
|---|---|---|
| `commons-configuration2` 2.7 (own) | Code injection (GHSA-xj57-8qj4-c4m6 / CVE-2022-33980, critical), plus 3 StackOverflowError DoS CVEs | Bumped direct dependency to **2.15.0**. |
| `commons-configuration2` 2.7 → `commons-text` 1.8, `commons-lang3` 3.9 (transitive) | Arbitrary code execution in Commons Text (GHSA-599f-7c49-w659 / CVE-2022-42889, critical, EPSS 0.999); uncontrolled recursion in Commons Lang | Resolved by the `commons-configuration2` bump above — 2.15.0 pulls `commons-text` 1.15.0 and `commons-lang3` 3.20.0 transitively (verified via `mvn dependency:tree`), both well past the fixed versions. No explicit `dependencyManagement` override needed. |
| `jackson-databind` 2.13.0 (own) | 8 CVEs: DoS via JDK serialization/deeply-nested JSON, `PolymorphicTypeValidator`/`BasicPolymorphicTypeValidator` bypasses, SSRF via `InetSocketAddress` deserialization | Bumped direct dependency to **2.18.8**. |
| `jackson-databind` 2.13.0 → `jackson-core` 2.13.0 (transitive) | StackOverflowError on deeply nested input; number-length constraint bypass in async parser | Resolved by the `jackson-databind` bump above — 2.18.8 pulls `jackson-core` 2.18.8 transitively. No explicit override needed. |
| `jackson-databind` 2.13.0/2.18.8 (own) | Case-insensitive deserialization bypass of per-property `@JsonIgnoreProperties` (GHSA-5jmj-h7xm-6q6v / CVE-2026-54515), medium | **No fixed version exists** — advisory's affected range is open-ended (`fix_state: not-fixed`) as of 2.18.8, the latest available release. Not fixable by a version change; documented here rather than guessing at a fix. |

## Verification

- `fixtures/webapp`: `npm install && npm run build && npm test` — 12/12 tests pass. Remaining `npm audit` findings are exactly the two documented no-fix-upstream issues (`request` SSRF, transitive `uuid` buffer-bounds check).
- `fixtures/service`: fresh venv, `pip install -r requirements.txt -r requirements-dev.txt`, `pytest` — 8/8 tests pass. Remaining `bomly_scan` finding is the documented no-fix-upstream `ecdsa` issue.
- `fixtures/api-java`: `mvn test` — 4/4 tests pass, `BUILD SUCCESS`. Remaining `bomly_scan` finding is the documented no-fix-upstream `jackson-databind` issue.
