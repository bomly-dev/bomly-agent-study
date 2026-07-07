# Dependency Vulnerability Fixes

## fixtures/webapp

### axios
- Found: `axios@1.6.0` with multiple fixed advisories: GHSA-35jp-ww65-95wh, GHSA-3g43-6gmg-66jw, GHSA-3p68-rc4w-qgx5, GHSA-3w6x-2g7m-8v23, GHSA-43fc-jf86-j433, GHSA-445q-vr5w-6q77, GHSA-4hjh-wcwx-xvwj, GHSA-5c9x-8gcm-mpgx, GHSA-62hf-57xw-28j9, GHSA-6chq-wfr3-2hj9, GHSA-898c-q2cr-xwhg, GHSA-8hc4-vh64-cxmj, GHSA-fvcv-3m26-pcqx, GHSA-hfxv-24rg-xrqf, GHSA-j5f8-grm9-p9fc, GHSA-jr5f-v2jv-69x6, GHSA-m7pr-hjqh-92cm, GHSA-p92q-9vqr-4j8v, GHSA-pf86-5x62-jrwf, GHSA-pjwm-pj3p-43mv, GHSA-pmwg-cvhr-8vh7, GHSA-q8qp-cvcw-x6jj, GHSA-vf2m-468p-8v99, GHSA-w9j2-pvgh-6h63, GHSA-xhjh-pmcv-23jw, and GHSA-xx6v-rp6x-q39c.
- Changed: upgraded direct dependency to `axios@1.16.0`.
- Why: bomly reported `1.16.0` as the minimum safe version covering the axios findings.

### express
- Found: `express@4.19.2` vulnerable to GHSA-qw6h-vgh9-j6wx.
- Changed: upgraded direct dependency to `express@4.22.2`.
- Why: `4.22.2` keeps the app on the Express 4 line while resolving the direct Express advisory and pulling patched transitive ranges.

### body-parser
- Found: transitive `body-parser@1.20.2` via Express vulnerable to GHSA-qwcr-r2fm-qrc7.
- Changed: upgraded Express to `4.22.2`, which resolves `body-parser@1.20.5`.
- Why: the vulnerable package was introduced by Express, and the fixed body-parser line is available through a newer Express 4 release.

### cookie
- Found: transitive `cookie@0.6.0` via Express vulnerable to GHSA-pxg6-pf52-xh8x.
- Changed: upgraded Express to `4.22.2`, which resolves `cookie@0.7.2`.
- Why: the vulnerable package was introduced by Express, and the fixed cookie line is available through a newer Express 4 release.

### qs
- Found: transitive `qs@6.11.0` via Express vulnerable to GHSA-6rw7-vpxm-498p and GHSA-w7fw-mjwx-w883; an intermediate update exposed GHSA-q8mj-m7cp-5q26 until Express was moved to `4.22.2`.
- Changed: upgraded Express to `4.22.2`, which resolves `qs@6.15.3`.
- Why: `qs@6.15.3` is above the fixed versions reported for all identified qs advisories.

### jsonwebtoken
- Found: `jsonwebtoken@8.5.1` vulnerable to GHSA-8cf7-32gw-wr33, GHSA-hjrf-2m68-5959, and GHSA-qwph-4952-7xr6.
- Changed: upgraded direct dependency to `jsonwebtoken@9.0.0`.
- Why: bomly reported `9.0.0` as the fixed version for the identified jsonwebtoken advisories.

### lodash
- Found: dev dependency `lodash@4.17.20` vulnerable to GHSA-29mw-wpgm-hmr9, GHSA-35jh-r3h4-6jhm, GHSA-f23m-r3pf-42rh, GHSA-r5fr-rjxr-66jc, and GHSA-xxjr-mmjv-4gpg.
- Changed: upgraded dev dependency to `lodash@4.18.1`.
- Why: bomly reported `4.18.0` as the minimum fixed version; `4.18.1` is non-deprecated and remains above that fixed threshold.

### request
- Found: direct dependency `request@2.88.2` vulnerable to GHSA-p8p7-x288-28g6 / CVE-2023-28155.
- Changed: removed `request` and migrated the XML fetch helper to the already-used `axios` dependency.
- Why: bomly reported `request` as `not-fixed`; there is no patched `request` version to upgrade to.

### form-data
- Found: transitive `form-data@2.3.3` via `request` vulnerable to GHSA-fjxv-7rqg-78g4 and GHSA-hmw2-7cc7-3qxx.
- Changed: removed `request`, eliminating the vulnerable `form-data@2.3.3` path. The remaining `form-data` resolved by axios is `4.0.6`.
- Why: the vulnerable instance was only introduced by `request`; removing the unfixed parent dependency removes this vulnerable package instance.

### tough-cookie
- Found: transitive `tough-cookie@2.5.0` via `request` vulnerable to GHSA-72xf-g2v4-qvf3.
- Changed: removed `request`, eliminating `tough-cookie` from the webapp dependency graph.
- Why: the vulnerable package was only present through the unfixed `request` dependency.

## fixtures/api-java

### com.fasterxml.jackson.core:jackson-databind
- Found: `jackson-databind@2.13.0` vulnerable to GHSA-3wrr-7qpf-2prh, GHSA-3x8x-79m2-3w2w, GHSA-57j2-w4cx-62h2, GHSA-hgj6-7826-r7m5, GHSA-j3rv-43j4-c7qm, GHSA-jjjh-jjxp-wpff, GHSA-rgv9-q543-rqg4, and GHSA-rmj7-2vxq-3g9f with fixed versions available. Also found GHSA-5jmj-h7xm-6q6v / CVE-2026-54515, which bomly marks `not-fixed`.
- Changed: upgraded direct dependency to `jackson-databind@2.18.8`.
- Why: bomly reported `2.18.8` as the minimum safe version for the fixed jackson-databind advisories. GHSA-5jmj-h7xm-6q6v remains unresolved because bomly reports no fixed version, and `2.18.9` is not published in Maven Central.

### org.apache.commons:commons-configuration2
- Found: `commons-configuration2@2.7` vulnerable to GHSA-337m-mw94-2v6g, GHSA-9w38-p64v-xpmv, GHSA-xj57-8qj4-c4m6, and GHSA-xjp4-hw94-mvp5.
- Changed: upgraded direct dependency to `commons-configuration2@2.15.0`.
- Why: bomly reported `2.15.0` as the minimum safe version covering all identified commons-configuration2 advisories.

## fixtures/service

No Python dependency vulnerabilities were identified by bomly. The scan reported license warnings only, so no dependency versions were changed for `fixtures/service`.
