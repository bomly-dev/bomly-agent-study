# Dependency vulnerability remediation

Findings from `bomly_scan --enrich --audit` against each fixture, and the action
taken for each. All three fixtures still build and pass their test suites
(`make test`) after these changes.

## fixtures/webapp (npm)

| Package | Found at | Vulnerabilities | Action |
|---|---|---|---|
| axios | 1.6.0 | 26 GHSAs (1 critical, many high/medium — SSRF, credential leakage on cross-origin redirect, ReDoS, proxy-auth leak, etc.) | Bumped to **1.18.1** (latest 1.x). Fixed. |
| express | 4.19.2 | GHSA-qw6h-vgh9-j6wx (low, XSS via response redirect) | Bumped to **4.22.2** (latest 4.x — stayed on 4.x since 5.x is a breaking major and out of scope). Fixed, and pulls in fixed transitive versions of body-parser/cookie/path-to-regexp/qs/send/serve-static (see below). |
| jsonwebtoken | 8.5.1 | GHSA-8cf7-32gw-wr33 (high), GHSA-hjrf-2m68-5959, GHSA-qwph-4952-7xr6 | Bumped to **9.0.3**. This is a breaking major version: `jwt.encode()` returns a `str` directly in 9.x instead of `bytes`. Updated `src/auth.js` to drop the 8.x-specific `.decode("utf-8")` call. All existing tests (`test/auth.test.js`) still pass. |
| lodash (devDependency) | 4.17.20 | 5 GHSAs (prototype pollution, ReDoS, command injection in `_.template`) | Bumped to **4.18.1**. Fixed. |
| body-parser | 1.20.2 (transitive via express) | GHSA-qwcr-r2fm-qrc7 (high) | Resolved automatically by the express 4.22.2 bump (now 1.20.5+). Fixed. |
| cookie | 0.6.0 (transitive via express) | GHSA-pxg6-pf52-xh8x (low) | Resolved automatically by the express 4.22.2 bump (now 0.7.x). Fixed. |
| path-to-regexp | 0.1.7 (transitive via express) | 3 GHSAs (high, ReDoS) | Resolved automatically by the express 4.22.2 bump (now 0.1.13). Fixed. |
| qs | 6.11.0 (transitive via express) | GHSA-6rw7-vpxm-498p, GHSA-w7fw-mjwx-w883 | Resolved automatically by the express 4.22.2 bump (now 6.15.x). Fixed. |
| send | 0.18.0 (transitive via express) | GHSA-m6fv-jmcg-4jfg (low) | Resolved automatically by the express 4.22.2 bump (now 0.19.x). Fixed. |
| serve-static | 1.15.0 (transitive via express) | GHSA-cm22-4g7w-348p (low) | Resolved automatically by the express 4.22.2 bump (now 1.16.x). Fixed. |
| **request** | 2.88.2 | GHSA-p8p7-x288-28g6 (medium, SSRF via redirect) | **Not fixed — no version exists that fixes this.** `request` was deprecated in 2020 and never patched; this is the latest release on npm. `bomly_vuln_fix_context` and `npm view request versions` both confirm no newer version exists. Left in place; used only by `src/importer.js` (`fetchXml`) for a legacy XML-feed importer. Removing/replacing `request` (e.g. with `axios`/`fetch`) would fix this but is a functional rewrite outside the scope of a version-only remediation. |
| form-data | 2.3.3 (transitive, only via `request`) | GHSA-fjxv-7rqg-78g4 (critical), GHSA-hmw2-7cc7-3qxx (high) | **Not fixed.** A patched release (2.5.4) exists on the registry, but `request@2.88.2` pins `form-data: ~2.3.2`, so it is unreachable without forcing an out-of-range override on `request`'s own dependency — effectively running `request` against a `form-data` version it was never tested with. Left as-is; tied to the `request` decision above. |
| qs (nested under request) | 6.5.5 | GHSA-6rw7-vpxm-498p (medium) | **Not fixed**, same reason: `request@2.88.2` pins `qs: ~6.5.2`, and the fixed version (6.14.1) falls outside that range. |
| tough-cookie | 2.5.0 (transitive, only via `request`) | GHSA-72xf-g2v4-qvf3 (medium) | **Not fixed**, same reason: `request` pins `tough-cookie: ~2.5.0`; fixed version (4.1.3) is outside that range. |
| uuid | 3.4.0 (transitive, only via `request`) | GHSA-w5hq-g745-h8pq (medium) | **Not fixed**, same reason: `request` pins `uuid: ^3.3.2`; fixed version (11.1.1) is outside that range. |

Verified with `npm audit` after the changes: the only 5 remaining advisories are `request` and its 4 captive transitive dependencies listed above, all blocked on the same unmaintained package.

## fixtures/service (pip)

| Package | Found at | Vulnerabilities | Action |
|---|---|---|---|
| pyjwt | 1.7.1 | 5 GHSAs (high — algorithm confusion / `crit` header issues) | Bumped `requirements.in` pin to **2.13.0** and recompiled `requirements.txt`. This is a breaking major version: `jwt.encode()` returns a `str` in 2.x instead of `bytes`. Updated `app/auth.py`'s `make_token()` to drop the 1.x-specific `.decode("utf-8")` call. All existing tests (`tests/test_auth.py`) still pass. |
| urllib3 | 1.26.5 | 8 GHSAs (high/medium — various request-smuggling / redirect / decompression issues) | `requirements.txt` had a hand-pinned, stale `urllib3==1.26.5` with a comment noting it had drifted behind what `requests` allows. Recompiled with `pip-compile --upgrade-package urllib3`, which now resolves to **2.7.0** (within `requests`' `urllib3<3` constraint). Fixed. |
| **ecdsa** | 0.19.2 | GHSA-wj6h-64fc-37mp (high, Minerva timing side-channel on P-256, CVE-2024-23342) | **Not fixed — no version exists that fixes this.** 0.19.2 is the latest release on PyPI. The `python-ecdsa` maintainers' own `SECURITY.md` documents this as a won't-fix: pure-Python code can't be made constant-time against this class of timing attack, and they recommend using `pyca/cryptography` instead. Left as-is; a real fix would mean replacing the `ecdsa` dependency, which is outside the scope of a version-only remediation. |

The `jinja2==3.1.6` "invalid SPDX license: non-standard" finding is a license-policy warning, not a CVE — jinja2 is already at its latest release, so there is no version to bump. Left as-is (out of scope: no vulnerability).

## fixtures/api-java (Maven)

| Package | Found at | Vulnerabilities | Action |
|---|---|---|---|
| jackson-databind | 2.13.0 | 9 GHSAs (several high — polymorphic-typing gadget chains, DoS) | Bumped to **2.21.5**. (2.22.0, the latest release, was deliberately avoided: it carries a newly-disclosed, currently unfixed regression, GHSA-5jmj-h7xm-6q6v/CVE-2026-54515, affecting `>=2.22.0,<2.22.1`; 2.21.5 predates that regression and postdates all the originally-found CVEs.) Verified via `mvn dependency:tree` and a fresh `bomly_scan` that 2.21.5 has zero vulnerability findings. |
| jackson-core | 2.13.0 (transitive via jackson-databind) | GHSA-72hv-8253-57qq, GHSA-h46c-h94j-95f3 | Resolved automatically by the jackson-databind bump (now resolves to matching 2.21.5). Fixed. |
| commons-configuration2 | 2.7 | 4 GHSAs (1 critical — GHSA-xj57-8qj4-c4m6, RCE via unrestricted class instantiation in interpolation) | Bumped to **2.15.1**. Fixed. |
| commons-lang3 | 3.9 (transitive via commons-configuration2) | GHSA-j288-q9x7-2f5v (medium) | Resolved automatically by the commons-configuration2 bump (now resolves to 3.20.0). Fixed. |
| commons-text | 1.8 (transitive via commons-configuration2) | GHSA-599f-7c49-w659 (critical, CVE-2022-42889 "Text4Shell") | Resolved automatically by the commons-configuration2 bump (now resolves to 1.15.0). Fixed. |

The `junit-jupiter*`/`junit-platform-*` "invalid SPDX license: non-standard" findings are license-policy warnings, not CVEs, on test-scope-only dependencies. Left as-is (out of scope: no vulnerability).

## Verification

- `fixtures/webapp`: `npm run build && npm test` — 12/12 tests pass.
- `fixtures/service`: fresh venv, `pip install -r requirements.txt -r requirements-dev.txt`, `pytest -q` — 8/8 tests pass.
- `fixtures/api-java`: `mvn -o test` — 4/4 tests pass.
- `make test` from the repo root passes end-to-end for all three fixtures.
- Re-ran `bomly_scan --enrich --audit` against each fixture after the changes: `api-java` and `service` now show zero vulnerability findings (only the pre-existing, out-of-scope license warnings remain); `webapp` is reduced from 50 findings to the 5 tied to the unfixable `request` package.
