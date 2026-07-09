# Vulnerability Remediation Log

## axios

Found `axios@1.6.0` with multiple SSRF, denial-of-service, header injection, credential leak, and prototype-pollution gadget advisories: GHSA-35jp-ww65-95wh, GHSA-3g43-6gmg-66jw, GHSA-3p68-rc4w-qgx5, GHSA-3w6x-2g7m-8v23, GHSA-43fc-jf86-j433, GHSA-445q-vr5w-6q77, GHSA-4hjh-wcwx-xvwj, GHSA-5c9x-8gcm-mpgx, GHSA-62hf-57xw-28j9, GHSA-6chq-wfr3-2hj9, GHSA-898c-q2cr-xwhg, GHSA-8hc4-vh64-cxmj, GHSA-fvcv-3m26-pcqx, GHSA-hfxv-24rg-xrqf, GHSA-j5f8-grm9-p9fc, GHSA-jr5f-v2jv-69x6, GHSA-m7pr-hjqh-92cm, GHSA-p92q-9vqr-4j8v, GHSA-pf86-5x62-jrwf, GHSA-pmwg-cvhr-8vh7, GHSA-q8qp-cvcw-x6jj, GHSA-vf2m-468p-8v99, GHSA-w9j2-pvgh-6h63, GHSA-xhjh-pmcv-23jw, and GHSA-xx6v-rp6x-q39c. Changed the direct dependency to `axios@1.18.1`, which is newer than the highest fixed version reported by bomly and npm audit.

## body-parser

Found transitive `body-parser@1.20.2` via Express with GHSA-qwcr-r2fm-qrc7. Changed the direct `express` dependency to `4.22.2`, which resolved `body-parser` to `1.20.6`; no separate override was needed.

## cookie

Found transitive `cookie@0.6.0` via Express with GHSA-pxg6-pf52-xh8x. Changed the direct `express` dependency to `4.22.2`, which resolved `cookie` to `0.7.2`; no separate override was needed.

## express

Found direct `express@4.19.2` with GHSA-qw6h-vgh9-j6wx. Changed the direct dependency to `express@4.22.2`, which is newer than the reported fixed version and also pulled patched Express transitive dependencies.

## form-data

Found transitive `form-data@2.3.3` via `request` with GHSA-fjxv-7rqg-78g4 and GHSA-hmw2-7cc7-3qxx. Added an npm override to force `form-data@2.5.6`, because `request@2.88.2` does not publish a newer release that pulls this patched dependency.

## jsonwebtoken

Found direct `jsonwebtoken@8.5.1` with GHSA-8cf7-32gw-wr33, GHSA-hjrf-2m68-5959, and GHSA-qwph-4952-7xr6. Changed the direct dependency to `jsonwebtoken@9.0.3`, which is newer than the reported fixed version.

## lodash

Found dev dependency `lodash@4.17.20` with GHSA-29mw-wpgm-hmr9, GHSA-35jh-r3h4-6jhm, GHSA-f23m-r3pf-42rh, GHSA-r5fr-rjxr-66jc, and GHSA-xxjr-mmjv-4gpg. Changed the dev dependency to `lodash@4.18.1`, which is newer than the highest fixed version reported by bomly.

## path-to-regexp

Found transitive `path-to-regexp@0.1.7` via Express with GHSA-37ch-88jc-xwx2, GHSA-9wv6-86v2-598j, and GHSA-rhx6-c78j-4q9w. Changed the direct `express` dependency to `4.22.2`, which resolved `path-to-regexp` to `0.1.13`; no separate override was needed.

## qs

Found transitive `qs@6.5.5` via `request` and `qs@6.11.0` via Express with GHSA-6rw7-vpxm-498p and GHSA-w7fw-mjwx-w883. A follow-up scan also identified GHSA-q8mj-m7cp-5q26 against `qs@6.14.2`. Added an npm override to force `qs@6.15.2`, the fixed version reported for all observed `qs` findings.

## request

Found direct `request@2.88.2` with GHSA-p8p7-x288-28g6. Did not change the package version because bomly reports no fixed upstream `request` version for this advisory. Replacing `request` with a different HTTP client would be a code migration rather than a version remediation, so it was left unchanged and explicitly documented.

## send

Found transitive `send@0.18.0` via Express with GHSA-m6fv-jmcg-4jfg. Changed the direct `express` dependency to `4.22.2`, which resolved `send` to `0.19.2`; no separate override was needed.

## serve-static

Found transitive `serve-static@1.15.0` via Express with GHSA-cm22-4g7w-348p. Changed the direct `express` dependency to `4.22.2`, which resolved `serve-static` to `1.16.3`; no separate override was needed.

## tough-cookie

Found transitive `tough-cookie@2.5.0` via `request` with GHSA-72xf-g2v4-qvf3. Added an npm override to force `tough-cookie@4.1.3`, the fixed version reported by bomly, because `request@2.88.2` has no newer release that pulls this patched dependency.

## uuid

Found transitive `uuid@3.4.0` via `request` with GHSA-w5hq-g745-h8pq. Did not keep a version override: the reported fixed line starts at `uuid@11.1.1`, but `request@2.88.2` imports the legacy `uuid/v4` subpath that is not exported by `uuid@11.1.1`, causing the build to fail. No compatible fixed `uuid` version exists for `request@2.88.2`; fixing this would require replacing or patching `request`, which is outside version-only remediation.
