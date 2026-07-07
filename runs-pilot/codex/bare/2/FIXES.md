# Vulnerability Remediation Log

## fixtures/webapp

- `axios`: `npm audit` reported SSRF, credential-leakage, DoS, header-injection, and prototype-pollution advisories affecting `1.6.0`. Updated the direct dependency to `1.18.1`, the non-major fixed version reported by npm, because it clears the advisories without an API migration.
- `express`: `npm audit` reported an XSS issue in `express` and vulnerable transitives pulled by `express` (`body-parser`, `cookie`, `path-to-regexp`, `qs`, `send`, and `serve-static`). Updated the direct dependency to `4.22.2`, the non-major fixed version reported by npm, because it refreshes the vulnerable Express dependency subtree.
- `body-parser`: vulnerable transitive via `express` (`urlencoded` denial of service). Updated `express` to `4.22.2`, which pulls a fixed `body-parser`.
- `cookie`: vulnerable transitive via `express` (out-of-bounds characters accepted in cookie attributes). Updated `express` to `4.22.2`, which pulls a fixed `cookie`.
- `path-to-regexp`: vulnerable transitive via `express` (ReDoS/backtracking advisories). Updated `express` to `4.22.2`, which pulls a fixed `path-to-regexp`.
- `qs`: vulnerable transitive via both `express` and `request` (array-limit denial of service advisories). Updated `express` to `4.22.2` and removed `request`; the remaining lockfile uses fixed `qs`.
- `send`: vulnerable transitive via `express`/`serve-static` (template-injection XSS). Updated `express` to `4.22.2`, which pulls a fixed `send`.
- `serve-static`: vulnerable transitive via `express` (template-injection XSS). Updated `express` to `4.22.2`, which pulls a fixed `serve-static`.
- `jsonwebtoken`: `npm audit` reported key-confusion/signature-validation advisories affecting `8.5.1`. Updated the direct dependency to `9.0.3`, the fixed version reported by npm, because the existing HS256 signing and verification path is compatible with 9.x.
- `lodash`: `npm audit` reported command injection, ReDoS, code injection, and prototype-pollution advisories affecting `4.17.20`. Updated the dev dependency to `4.18.1`, the fixed version reported by npm.
- `request`: `npm audit` reported SSRF in `request@2.88.2` and reported `fixAvailable: false`. No fixed `request` version exists, so I migrated the XML import fetch path to the already-used `axios` dependency and removed `request` from `package.json` and `package-lock.json`.
- `form-data`: vulnerable transitive under `request` (unsafe multipart boundary generation and CRLF injection). Because `request` has no fixed version and pins the vulnerable subtree, removed `request`; the remaining `form-data` in the lockfile is the fixed `4.0.6` pulled by `axios`.
- `tough-cookie`: vulnerable transitive under `request` (prototype pollution). Because `request` has no fixed version, removed `request`, which removes `tough-cookie` from the dependency graph.
- `uuid`: vulnerable transitive under `request` (missing buffer bounds check). Because `request` has no fixed version, removed `request`, which removes `uuid` from the dependency graph.

## fixtures/service

- `pyjwt`: `pip-audit` reported multiple advisories against `1.7.1`, including CVE-2022-29217 and later 2026 advisories fixed through `2.13.0`; one disputed advisory had no fix version listed. Updated the direct pin to `2.13.0` and adjusted token encoding code for PyJWT 2.x string return values.
- `urllib3`: `pip-audit` reported redirect/header-leakage and decompression/redirect DoS advisories against `1.26.5`, with fixes through `2.7.0`. Updated the transitive runtime pin to `2.7.0`, which is allowed by the installed `requests` constraint and clears the audit.

## fixtures/api-java

- `com.fasterxml.jackson.core:jackson-databind`: OSV reported multiple advisories against `2.13.0`, including resource-exhaustion and polymorphic deserialization validator bypass issues. Updated to the latest published Maven Central release, `2.22.0`, which remediates the older fixed-version advisories. OSV still reports GHSA-5jmj-h7xm-6q6v/CVE-2026-54515 for `2.22.0`; its advisory says it will be fixed in `2.18.9`, `2.21.5`, and `2.22.1`, but Maven Central currently does not publish those versions, so no fixed 2.x version exists to select.
- `org.apache.commons:commons-configuration2`: OSV reported code injection and StackOverflowError advisories against `2.7`, with fixes through `2.15.0`. Updated to `2.15.1`, the latest published release, because it is beyond all reported fixed versions and OSV returns no vulnerabilities for it.
