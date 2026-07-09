# Dependency Vulnerability Fixes

## fixtures/webapp

- `axios`: `npm audit` reported multiple vulnerabilities in `1.6.0`, including SSRF, credential leakage, denial of service, prototype pollution gadgets, and header/CRLF injection issues. Updated direct dependency to `1.18.1`, the non-major fixed version reported by npm audit.
- `express`: `npm audit` reported `express` `4.19.2` and its dependency chain as vulnerable, including `response.redirect()` XSS plus vulnerable `body-parser`, `cookie`, `path-to-regexp`, `qs`, `send`, and `serve-static` versions. Updated direct dependency to `4.22.2`, the non-major fixed version reported by npm audit.
- `body-parser`: Reported transitively through `express` for denial of service in URL encoding. No direct pin existed; resolved by updating `express` to `4.22.2`.
- `cookie`: Reported transitively through `express` for accepting out-of-bounds cookie characters. No direct pin existed; resolved by updating `express` to `4.22.2`.
- `path-to-regexp`: Reported transitively through `express` for ReDoS/backtracking route expressions. No direct pin existed; resolved by updating `express` to `4.22.2`.
- `send`: Reported transitively through `express`/`serve-static` for template injection leading to XSS. No direct pin existed; resolved by updating `express` to `4.22.2`.
- `serve-static`: Reported transitively through `express` for template injection leading to XSS. No direct pin existed; resolved by updating `express` to `4.22.2`.
- `jsonwebtoken`: `npm audit` reported key confusion/default algorithm validation issues in `8.5.1`. Updated direct dependency to `9.0.3`, the fixed version reported by npm audit.
- `lodash`: `npm audit` reported command/code injection, ReDoS, and prototype pollution issues in `4.17.20`. Updated dev dependency to `4.18.1`, the fixed version reported by npm audit.
- `request`: `npm audit` reported SSRF in `request` `2.88.2`; npm reported no fixed version. Removed `request` and migrated the one call site to the already-used `axios` dependency, because a version-only fix does not exist.
- `form-data`: Reported transitively through `request` for unsafe multipart boundary generation and CRLF injection. No direct pin existed and npm reported no fix through `request`; resolved by removing `request`.
- `tough-cookie`: Reported transitively through `request` for prototype pollution. No direct pin existed and npm reported no fix through `request`; resolved by removing `request`.
- `uuid`: Reported transitively through `request` for missing buffer bounds checks. No direct pin existed and npm reported no fix through `request`; resolved by removing `request`.
- `qs`: Reported transitively through both `express` and `request` for denial-of-service issues. Resolved the `express` path by updating `express` to `4.22.2` and the `request` path by removing `request`.

## fixtures/service

- `pyjwt`: `pip-audit` reported multiple vulnerabilities for `1.7.1`, including CVE-2022-29217 and later token validation/JWK/JWKS issues fixed through `2.13.0`. Updated `requirements.in` and `requirements.txt` to `pyjwt==2.13.0` and adjusted token creation for PyJWT 2.x returning `str`.
- `urllib3`: `pip-audit` reported redirect/header handling and decompression/resource-consumption vulnerabilities in `1.26.5`, with fixes through `2.7.0`. Updated the compiled transitive pin in `requirements.txt` to `urllib3==2.7.0`, which is allowed by the existing `requests` constraint.
- `ecdsa`: `pip-audit` reported PYSEC-2026-1325 / CVE-2024-23342, the Minerva timing attack on P-256 operations, for `0.19.2`. The advisory reports no fix versions and says the project considers side-channel attacks out of scope with no planned fix, so no version change was made.

## fixtures/api-java

- `com.fasterxml.jackson.core:jackson-databind`: OSV reported multiple vulnerabilities in `2.13.0`, including denial of service and polymorphic type validation issues. Updated to `2.22.0`, the latest published `com.fasterxml.jackson.core:jackson-databind` version in Maven Central, which clears the older advisories. OSV still reports GHSA-5jmj-h7xm-6q6v for `2.22.0`; its fixed `2.22.1` release is not published in Maven Central, so no available version-only fix exists for that remaining advisory.
- `org.apache.commons:commons-configuration2`: OSV reported CVE-2022-33980 code injection via default interpolators plus StackOverflowError/resource-consumption issues fixed by later releases. Updated direct dependency from `2.7` to `2.15.0`, which OSV reports as not vulnerable.
