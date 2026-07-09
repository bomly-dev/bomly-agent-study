# Dependency Vulnerability Fixes

## webapp

- `axios`: Found multiple axios advisories affecting `1.6.0`, with bomly reporting `1.16.0` as the minimum safe version. Upgraded direct dependency `axios` to `1.16.0`.
- `express`: Found an Express XSS advisory affecting `4.19.2`, plus vulnerable transitives pulled through the Express line. Upgraded direct dependency `express` to `4.22.2` so patched transitives are selected.
- `body-parser`: Found DoS advisory GHSA-qwcr-r2fm-qrc7 via Express. Remediated by upgrading Express, which now resolves `body-parser` to `1.20.5`.
- `cookie`: Found out-of-bounds character advisory GHSA-pxg6-pf52-xh8x via Express. Remediated by upgrading Express, which now resolves `cookie` to `0.7.2`.
- `qs`: Found DoS advisories GHSA-6rw7-vpxm-498p, GHSA-w7fw-mjwx-w883, and GHSA-q8mj-m7cp-5q26 via Express. Remediated by upgrading Express, which now resolves `qs` to `6.15.3`.
- `send`: Found XSS advisory GHSA-m6fv-jmcg-4jfg via Express. Remediated by upgrading Express, which now resolves `send` to `0.19.2`.
- `jsonwebtoken`: Found GHSA-8cf7-32gw-wr33, GHSA-hjrf-2m68-5959, and GHSA-qwph-4952-7xr6 affecting `8.5.1`. Upgraded direct dependency `jsonwebtoken` to `9.0.0`.
- `lodash`: Found lodash advisories affecting `4.17.20`, with bomly reporting `4.18.0` as the minimum safe version. Upgraded direct dev dependency `lodash` to `4.18.0`.
- `request`: Found SSRF advisory GHSA-p8p7-x288-28g6 affecting `2.88.2`, with bomly reporting no fixed version for `request`. Replaced the single importer use with existing `axios` and removed `request`.
- `form-data`: Found GHSA-fjxv-7rqg-78g4 and GHSA-hmw2-7cc7-3qxx in `form-data@2.3.3` via `request`. Removed `request`, which removed the vulnerable `form-data@2.3.3` path.
- `tough-cookie`: Found GHSA-72xf-g2v4-qvf3 in `tough-cookie@2.5.0` via `request`. Removed `request`, which removed the vulnerable `tough-cookie` path.
- `uuid`: Found GHSA-w5hq-g745-h8pq in `uuid@3.4.0` via `request`. Removed `request`, which removed the vulnerable `uuid` path.

## service

- `pyjwt`: Found GHSA-752w-5fwx-jx9f, GHSA-993g-76c3-p5m4, GHSA-ffqj-6fqr-9h24, GHSA-fhv5-28vv-h8m8, and GHSA-xgmm-8j9v-c9wx affecting `1.7.1`. Upgraded `pyjwt` to `2.13.0` and kept token creation compatible with both byte and string return values.
- `urllib3`: Found multiple urllib3 advisories affecting `1.26.5`, with bomly reporting `2.7.0` as the minimum safe version. Upgraded the explicit transitive pin to `urllib3==2.7.0`, which is allowed by the installed `requests` constraint.
- `ecdsa`: Found GHSA-wj6h-64fc-37mp / CVE-2024-23342 affecting `ecdsa@0.19.2`. bomly reports `fix_state: not-fixed`; no version-only remediation exists, so the package remains pinned by resolution and this is documented rather than guessed.

## api-java

- `com.fasterxml.jackson.core:jackson-databind`: Found multiple fixed advisories affecting `2.13.0`, with bomly reporting `2.18.8` as the minimum safe version for those fixed advisories. Upgraded direct dependency `jackson-databind` to `2.18.8`. GHSA-5jmj-h7xm-6q6v / CVE-2026-54515 remains reported by bomly as `fix_state: not-fixed`; no version-only remediation exists for that advisory.
- `com.fasterxml.jackson.core:jackson-core`: Found jackson-core DoS advisories via `jackson-databind@2.13.0`. Remediated by upgrading `jackson-databind`, which now resolves `jackson-core` to `2.18.8`.
- `org.apache.commons:commons-configuration2`: Found GHSA-337m-mw94-2v6g, GHSA-9w38-p64v-xpmv, GHSA-xj57-8qj4-c4m6, and GHSA-xjp4-hw94-mvp5 affecting `2.7`. Upgraded direct dependency `commons-configuration2` to `2.15.0`.
