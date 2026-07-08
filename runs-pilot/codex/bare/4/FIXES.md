# Vulnerability Remediation Log

## fixtures/webapp

- `axios`: `npm audit` reported multiple SSRF, denial-of-service, credential leak, header injection, and prototype-pollution advisories affecting `1.6.0` (including GHSA-8hc4-vh64-cxmj, GHSA-jr5f-v2jv-69x6, GHSA-4hjh-wcwx-xvwj, and later Axios advisories through the audited range `<1.16.0`). Updated the direct dependency to `1.18.1`, which is the non-major fixed version reported by npm and clears the advisories.
- `express`: `npm audit` reported direct `express` redirect XSS (GHSA-qw6h-vgh9-j6wx) and vulnerable transitives from the old `4.19.2` graph. Updated the direct dependency to `4.22.2`, the fixed 4.x version reported by npm, to refresh the transitive web stack.
- `body-parser`: `npm audit` reported denial of service in the transitive `body-parser` pulled by `express` (GHSA-qwcr-r2fm-qrc7). Updated `express` to `4.22.2`, which pulls a fixed `body-parser`.
- `cookie`: `npm audit` reported out-of-bounds character handling in the transitive `cookie` pulled by `express` (GHSA-pxg6-pf52-xh8x). Updated `express` to `4.22.2`, which pulls a fixed `cookie`.
- `path-to-regexp`: `npm audit` reported multiple ReDoS advisories in the transitive `path-to-regexp` pulled by `express` (GHSA-9wv6-86v2-598j, GHSA-rhx6-c78j-4q9w, GHSA-37ch-88jc-xwx2). Updated `express` to `4.22.2`, which pulls a fixed `path-to-regexp`.
- `send`: `npm audit` reported template-injection XSS in the transitive `send` pulled by `express` / `serve-static` (GHSA-m6fv-jmcg-4jfg). Updated `express` to `4.22.2`, which pulls a fixed `send`.
- `serve-static`: `npm audit` reported template-injection XSS in the transitive `serve-static` pulled by `express` (GHSA-cm22-4g7w-348p). Updated `express` to `4.22.2`, which pulls a fixed `serve-static`.
- `jsonwebtoken`: `npm audit` reported key handling and signature validation advisories in `8.5.1` (GHSA-8cf7-32gw-wr33, GHSA-hjrf-2m68-5959, GHSA-qwph-4952-7xr6). Updated the direct dependency to `9.0.3`, the fixed version reported by npm.
- `lodash`: `npm audit` reported command/code injection, ReDoS, and prototype pollution advisories in `4.17.20` (including GHSA-35jh-r3h4-6jhm, GHSA-29mw-wpgm-hmr9, GHSA-r5fr-rjxr-66jc). Updated the dev dependency to `4.18.1`, which clears the advisories.
- `request`: `npm audit` reported SSRF in `request` (GHSA-p8p7-x288-28g6) and showed `fixAvailable: false`; there is no fixed `request` version. Replaced the XML feed fetcher with the already-used `axios` client and removed `request`.
- `form-data`: `npm audit` reported unsafe boundary generation and CRLF injection in the `form-data` version pulled by `request` (GHSA-fjxv-7rqg-78g4, GHSA-hmw2-7cc7-3qxx). The audit reported no version-only fix through `request`, so removing `request` removed this vulnerable transitive dependency.
- `qs`: `npm audit` reported denial-of-service advisories in `qs` (GHSA-w7fw-mjwx-w883, GHSA-6rw7-vpxm-498p). Updated `express` for the Express-owned path and removed `request` for the legacy path, eliminating the vulnerable instances.
- `tough-cookie`: `npm audit` reported prototype pollution in the version pulled by `request` (GHSA-72xf-g2v4-qvf3). Removed `request`, which removed this vulnerable transitive dependency.
- `uuid`: `npm audit` reported a buffer bounds advisory in the version pulled by `request` (GHSA-w5hq-g745-h8pq). The audit reported no version-only fix through `request`, so removing `request` removed this vulnerable transitive dependency.

## fixtures/service

- `pyjwt`: `pip-audit` reported multiple JWT verification and JWK/JWKS advisories against `1.7.1`, with fixed versions up to `2.13.0` (including PYSEC-2022-202 / CVE-2022-29217, PYSEC-2026-120 / CVE-2026-32597, PYSEC-2026-179 / CVE-2026-48526, PYSEC-2026-175 / CVE-2026-48522, and PYSEC-2026-177 / CVE-2026-48524). Updated to `2.13.0` and adjusted token encoding compatibility because PyJWT 2.x returns `str`.
- `urllib3`: `pip-audit` reported redirect, proxy-header, and decompression denial-of-service advisories against `1.26.5`, with fixed versions up to `2.7.0` (including PYSEC-2023-192 / CVE-2023-43804, PYSEC-2023-212 / CVE-2023-45803, PYSEC-2026-1995 / CVE-2024-37891, PYSEC-2026-1998 / CVE-2025-66418, PYSEC-2026-1994 / CVE-2025-66471, PYSEC-2026-1996 / CVE-2026-21441, PYSEC-2026-1999 / CVE-2025-50181, and PYSEC-2026-141 / CVE-2026-44431). Updated the transitive pin to `2.7.0`, which is allowed by the current `requests` constraint.
- `ecdsa`: `pip-audit` reported PYSEC-2026-1325 / CVE-2024-23342 / GHSA-wj6h-64fc-37mp for Minerva timing leakage on P-256. The advisory has no fixed versions and states there is no planned fix; the app still imports `ecdsa` for report signing, so no version change was made.

## fixtures/api-java

- `com.fasterxml.jackson.core:jackson-databind`: OSV reported denial-of-service and polymorphic deserialization / validation bypass advisories against `2.13.0` (including GHSA-3wrr-7qpf-2prh, GHSA-3x8x-79m2-3w2w, GHSA-57j2-w4cx-62h2, GHSA-jjjh-jjxp-wpff, GHSA-rgv9-q543-rqg4, GHSA-rmj7-2vxq-3g9f, GHSA-j3rv-43j4-c7qm, and GHSA-5jmj-h7xm-6q6v). Updated to `2.18.9`, the patched 2.18 line named by the advisories, which also updates `jackson-core` and `jackson-annotations`.
- `org.apache.commons:commons-configuration2`: OSV reported code injection and recursion / stack-overflow advisories against `2.7` (GHSA-xj57-8qj4-c4m6, GHSA-9w38-p64v-xpmv, GHSA-xjp4-hw94-mvp5, GHSA-337m-mw94-2v6g). Updated to `2.15.1`, newer than the `2.15.0` fixed version OSV recommends.
- `org.apache.commons:commons-text`: OSV reported arbitrary code execution in transitive `commons-text` `1.8` (GHSA-599f-7c49-w659 / CVE-2022-42889). Updating `commons-configuration2` to `2.15.1` now pulls `commons-text` `1.15.0`, which is above the `1.10.0` fixed version.
