# Vulnerability remediation log

Findings from `npm audit` (webapp), `pip-audit` (service), and Maven
Central / OSV/GHSA advisory lookups against the resolved dependency tree
(`mvn dependency:tree`) for api-java. One entry per package.

## fixtures/webapp (npm)

| Package | Found | Fixed to | Action / rationale |
|---|---|---|---|
| axios | 1.6.0 — multiple SSRF, prototype-pollution, ReDoS, DoS advisories (e.g. GHSA-8hc4-vh64-cxmj, GHSA-jr5f-v2jv-69x6, GHSA-4hjh-wcwx-xvwj and others affecting <1.15.x/<1.18.x) | 1.18.1 | Bumped to latest release; no code changes needed. |
| express | 4.19.2 — high-severity advisories in this range | 4.22.2 | Bumped within the 4.x line (non-breaking). This also upgrades vulnerable transitive deps pulled in by express: `body-parser` (GHSA-qwcr-r2fm-qrc7), `cookie` (GHSA-pxg6-pf52-xh8x), `path-to-regexp` (GHSA-9wv6-86v2-598j and others), `send` (GHSA-m6fv-jmcg-4jfg), and `serve-static`. |
| jsonwebtoken | 8.5.1 — GHSA-8cf7-32gw-wr33 (legacy key usage), GHSA-hjrf-2m68-5959 (forgeable RSA→HMAC tokens), GHSA-qwph-4952-7xr6 (insecure default algorithm in `verify()`) | 9.0.3 | Bumped (breaking change). Updated `src/auth.js`: removed the 8.x-specific comment block; `verifyToken` now passes `algorithms: ["HS256"]` explicitly to close the algorithm-confusion issue described in GHSA-qwph-4952-7xr6. `sign()`/`verify()`/`decode()` call shapes were otherwise already 9.x-compatible; tests pass unchanged. |
| lodash (devDependency) | 4.17.20 — GHSA-35jh-r3h4-6jhm (command injection), GHSA-29mw-wpgm-hmr9 (ReDoS), GHSA-r5fr-rjxr-66jc (`_.template` code injection), GHSA-f23m-r3pf-42rh / GHSA-xxjr-mmjv-4gpg (prototype pollution) | 4.18.1 | Bumped; only used in the dev-only `scripts/seed.js`. |
| request | 2.88.2 — package is unmaintained/deprecated; direct transitive `form-data` (GHSA-fjxv-7rqg-78g4, critical) and `tough-cookie` (moderate) have **no fixed version reachable through `request`'s own dependency tree** | removed | No version of `request` resolves these — the package has been deprecated since 2020 and its pinned transitive deps were never updated. Replaced its only call site (`fetchXml` in `src/importer.js`) with `axios`, which is already a dependency used elsewhere in the app. Dependency removed from `package.json`. |
| xml2js | 0.6.2 | *(unchanged)* | Not flagged by `npm audit`; no known advisory affects this version. Left as-is per instructions to avoid unnecessary changes. |

Transitive-only advisories cleared as a side effect of the `express` bump (see above): `body-parser`, `cookie`, `path-to-regexp`, `send`, `serve-static`. Transitive-only advisories cleared by removing `request`: `form-data`, `qs` (the `request`-bundled copy), `tough-cookie`, `uuid`.

Result: `npm audit` reports **0 vulnerabilities** after the changes; `npm run build && npm test` passes (12/12).

## fixtures/service (pip)

| Package | Found | Fixed to | Action / rationale |
|---|---|---|---|
| pyjwt | 1.7.1 — PYSEC-2022-202 (CVE-2022-29217, algorithm-confusion signature bypass) plus several later advisories fixed only in 2.4.0+/2.12.0+/2.13.0 | 2.13.0 | Bumped in `requirements.in` and `requirements.txt`. Updated `app/auth.py`: PyJWT 2.x's `encode()` returns `str` directly, so the `.decode("utf-8")` call (needed only for 1.x's `bytes` return) was removed. `read_token()` already restricted `algorithms=["HS256"]`, so no further change was needed there. Tests pass unchanged (they only assert `isinstance(token, str)`). |
| urllib3 | 1.26.5 — several advisories with no fix in the 1.26.x line for the newer CVEs (e.g. CVE-2025-50181, CVE-2025-66418, CVE-2025-66471, CVE-2026-21441) plus older CVE-2023-45803/CVE-2024-37891 | 2.7.0 | Bumped the compiled pin in `requirements.txt` (transitive dep of `requests`; `requests==2.34.2` already permits `urllib3<3`, so this required no change to `requirements.in`). Removed the stale comment noting the pin had drifted, since it's now current. |
| ecdsa | 0.19.2 — CVE-2024-23342 (Minerva timing side-channel attack on P-256 signing/ECDH; affects `SigningKey.sign_digest()` and related key-generation/ECDH paths) | **no fix available — left unchanged** | The `python-ecdsa` maintainers have stated this is out of scope and will not be fixed: a pure-Python implementation cannot be made constant-time, so no patched version exists (see [GHSA-wj6h-64fc-37mp](https://github.com/advisories/GHSA-wj6h-64fc-37mp)). `pip-audit` does not currently flag any `ecdsa` version for this CVE (no affected-version range is published), so it will not surface via automated scanning either. Documented here explicitly per instructions rather than guessing at a fix. Residual risk: `app/reports.py` uses `ecdsa` to sign report payloads with a NIST P-256 key; a local/co-located attacker able to measure signing latency could in theory recover the private key. If this needs closing, the real fix is swapping to a different ECDSA implementation (e.g. `cryptography`'s OpenSSL-backed bindings), which is a larger code change outside the scope of a version bump. |

Result: `pip-audit` reports **no known vulnerabilities** after the changes (ecdsa aside, per above); `pytest` passes (8/8).

## fixtures/api-java (Maven)

| Package | Found | Fixed to | Action / rationale |
|---|---|---|---|
| jackson-databind | 2.13.0 — multiple deserialization-gadget CVEs fixed in later 2.13.x/2.14.x+ releases | 2.22.0 | Bumped to the latest 2.x release. No code changes needed (`ObjectMapper.readValue`/`writeValueAsString` usage in `JsonMapper.java` is unaffected). |
| commons-configuration2 | 2.7 — transitively pulled `commons-text:1.8`, vulnerable to CVE-2022-42889 ("Text4Shell": RCE via `${script:...}`/`${dns:...}`/`${url:...}` interpolator lookups in `StringSubstitutor`); commons-configuration2 2.7 also predates the 2.8.0 fix for CVE-2022-33980 (unrestricted class loading via the `script` config interpolator) | 2.15.1 | Bumped, which pulls in `commons-text:1.15.0` (fixed) and postdates the 2.8.0 interpolator fix. Confirmed via `mvn -o dependency:tree` that `commons-text` now resolves to 1.15.0. No code changes needed; `ConfigLoader.java`'s `${...}` interpolation usage is standard variable substitution, not the vulnerable script/dns/url lookups. |

Result: `mvn -o dependency:tree` shows no known-vulnerable versions in the resolved graph; `mvn -o test` passes (4/4).
