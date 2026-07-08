# Vulnerability Fixes

## fixtures/webapp

- `axios` 1.6.0: bomly found multiple fixable SSRF, denial-of-service, header injection, credential leak, and prototype-pollution advisories including GHSA-8hc4-vh64-cxmj, GHSA-4hjh-wcwx-xvwj, GHSA-3p68-rc4w-qgx5, GHSA-43fc-jf86-j433, and GHSA-35jp-ww65-95wh. Changed the direct dependency to 1.16.0 because bomly reported that version as the required fixed version for the newest axios advisories.
- `express` 4.19.2: bomly found GHSA-qw6h-vgh9-j6wx, an XSS issue in `response.redirect()`, fixed in 4.20.0. Changed the direct dependency to 4.22.2, the latest 4.x release, to stay on the existing major line while also pulling fixed `send`, `serve-static`, and `cookie` transitives.
- `body-parser` 1.20.2, via `express`: bomly found GHSA-qwcr-r2fm-qrc7, a denial-of-service issue fixed in 1.20.3. Added an npm override to 1.20.3.
- `path-to-regexp` 0.1.7, via `express`: bomly found ReDoS advisories GHSA-9wv6-86v2-598j, GHSA-rhx6-c78j-4q9w, and GHSA-37ch-88jc-xwx2. Added an npm override to 0.1.13 because bomly reported that as the version that covers the newest advisory.
- `qs` 6.11.0 via `express` and 6.5.5 via `request`: bomly found GHSA-6rw7-vpxm-498p, GHSA-w7fw-mjwx-w883, and GHSA-q8mj-m7cp-5q26 denial-of-service issues. Added an npm override to 6.15.2 because bomly reported that version as covering the newest advisory.
- `send` 0.18.0, via `express`: bomly found GHSA-m6fv-jmcg-4jfg. Updated `express` to 4.22.2, which uses fixed `send` 0.19.0.
- `serve-static` 1.15.0, via `express`: bomly found GHSA-cm22-4g7w-348p. Updated `express` to 4.22.2, which uses fixed `serve-static` 1.16.x.
- `cookie` 0.6.0, via `express`: bomly found GHSA-pxg6-pf52-xh8x. Updated `express` to 4.22.2, which uses fixed `cookie` 0.7.x.
- `jsonwebtoken` 8.5.1: bomly found GHSA-8cf7-32gw-wr33, GHSA-hjrf-2m68-5959, and GHSA-qwph-4952-7xr6. Changed the direct dependency to 9.0.0 because bomly reported that as the fixed version.
- `lodash` 4.17.20: bomly found GHSA-35jh-r3h4-6jhm, GHSA-29mw-wpgm-hmr9, GHSA-xxjr-mmjv-4gpg, GHSA-f23m-r3pf-42rh, and GHSA-r5fr-rjxr-66jc. Changed the dev dependency to 4.18.1 because bomly reported 4.18.0 as the fixed boundary for the newest advisories and npm marks 4.18.0 as a bad release.
- `form-data` 2.3.3, via `request`: bomly found GHSA-fjxv-7rqg-78g4 and GHSA-hmw2-7cc7-3qxx. Removed `request`, which removed this vulnerable 2.x transitive; the remaining `form-data` comes from patched `axios` and resolves to 4.x.
- `tough-cookie` 2.5.0, via `request`: bomly found GHSA-72xf-g2v4-qvf3. Removed `request`, which removed this vulnerable transitive.
- `uuid` 3.4.0, via `request`: bomly found GHSA-w5hq-g745-h8pq. Removed `request`, which removed this vulnerable transitive. Overriding `uuid` to the fixed modern version breaks `request` because it imports the removed `uuid/v4` subpath, so the dependency using it had to be removed instead.
- `request` 2.88.2: bomly found GHSA-p8p7-x288-28g6 / CVE-2023-28155, an SSRF vulnerability. No fixed upstream version exists according to bomly, so this could not be fixed by changing the `request` version; removed the dependency and migrated the small XML fetch wrapper to the already-present patched `axios`.

## fixtures/service

- `urllib3` 1.26.5: bomly found multiple fixable redirect/header/decompression advisories including GHSA-v845-jxx5-vc9f, GHSA-g4mx-q9vg-27p4, GHSA-34jh-p97f-mpxf, GHSA-pq67-6m6q-mj2v, GHSA-2xpw-w6gg-jr37, GHSA-gm62-xv2j-4w53, GHSA-38jv-5279-wg99, and GHSA-qccp-gfcp-xxvc. Changed the compiled pin to 2.7.0 because bomly reported that version as covering the newest advisory and `requests` allows urllib3 `<3`.
- `pyjwt` 1.7.1: bomly found GHSA-ffqj-6fqr-9h24, GHSA-752w-5fwx-jx9f, GHSA-xgmm-8j9v-c9wx, GHSA-993g-76c3-p5m4, and GHSA-fhv5-28vv-h8m8. Changed the input and compiled pins to 2.13.0 because bomly reported that version as covering the newest advisories. Updated the small compatibility shim because PyJWT 2.x returns a string from `encode()`.
- `ecdsa` 0.19.2: bomly found GHSA-wj6h-64fc-37mp / CVE-2024-23342. No fixed upstream version exists according to bomly, so no version change was made.

## fixtures/api-java

- `com.fasterxml.jackson.core:jackson-databind` 2.13.0: bomly found multiple fixable denial-of-service and polymorphic deserialization advisories including GHSA-3x8x-79m2-3w2w, GHSA-57j2-w4cx-62h2, GHSA-jjjh-jjxp-wpff, GHSA-rgv9-q543-rqg4, GHSA-3wrr-7qpf-2prh, GHSA-j3rv-43j4-c7qm, GHSA-rmj7-2vxq-3g9f, and GHSA-hgj6-7826-r7m5. Changed the direct dependency to 2.18.8 because bomly reported that version as covering the newest fixable advisories.
- `com.fasterxml.jackson.core:jackson-core` 2.13.0, via `jackson-databind`: bomly found GHSA-h46c-h94j-95f3 and GHSA-72hv-8253-57qq. Added dependency management pinning `jackson-core` to 2.18.6 because bomly reported that as the version covering both advisories.
- `com.fasterxml.jackson.core:jackson-databind` remaining advisory: bomly found GHSA-5jmj-h7xm-6q6v / CVE-2026-54515 and reported no fixed upstream version. The direct dependency was still upgraded for all fixable advisories, but this specific advisory remains without a version-based fix.
- `org.apache.commons:commons-configuration2` 2.7: bomly found GHSA-xj57-8qj4-c4m6, GHSA-xjp4-hw94-mvp5, GHSA-9w38-p64v-xpmv, and GHSA-337m-mw94-2v6g. Changed the direct dependency to 2.15.0 because bomly reported that version as covering the newest advisory.
- `org.apache.commons:commons-text` 1.8, via `commons-configuration2`: bomly found GHSA-599f-7c49-w659 / CVE-2022-42889. Added dependency management pinning `commons-text` to 1.10.0, the fixed version reported by bomly.
- `org.apache.commons:commons-lang3` 3.9, via `commons-configuration2`: bomly found GHSA-j288-q9x7-2f5v / CVE-2025-48924. Added dependency management pinning `commons-lang3` to 3.18.0, the fixed version reported by bomly.
