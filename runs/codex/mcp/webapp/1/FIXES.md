# Vulnerability Remediation Log

## axios

Found `axios@1.6.0` with multiple SSRF, DoS, header injection, credential leak, response tampering, and prototype-pollution gadget advisories, including GHSA-8hc4-vh64-cxmj, GHSA-jr5f-v2jv-69x6, and GHSA-35jp-ww65-95wh. Changed the direct dependency to `axios@1.18.1`, which is newer than the highest fixed version bomly reported (`1.16.0`) and keeps the existing preview/import HTTP client behavior.

## body-parser

Found transitive `body-parser@1.20.2` via `express@4.19.2`, vulnerable to denial of service in URL encoding (GHSA-qwcr-r2fm-qrc7). Changed the direct `express` dependency to `express@4.22.2`, which resolves `body-parser@1.20.6`.

## cookie

Found transitive `cookie@0.6.0` via `express@4.19.2`, vulnerable to accepting out-of-bounds characters (GHSA-pxg6-pf52-xh8x). Changed the direct `express` dependency to `express@4.22.2`, which resolves `cookie@0.7.2`.

## express

Found direct `express@4.19.2`, vulnerable to XSS via `response.redirect()` (GHSA-qw6h-vgh9-j6wx). Changed the direct dependency to `express@4.22.2`, which stays on the 4.x API line while exceeding the reported fixed version (`4.20.0`).

## form-data

Found transitive `form-data@2.3.3` via `request@2.88.2`, vulnerable to unsafe multipart boundary generation and CRLF injection (GHSA-fjxv-7rqg-78g4, GHSA-hmw2-7cc7-3qxx). Removed `request`; the only remaining `form-data` is `4.0.6` via patched `axios@1.18.1`.

## jsonwebtoken

Found direct `jsonwebtoken@8.5.1`, vulnerable to unrestricted key type, insecure key retrieval, and signature validation bypass advisories (GHSA-8cf7-32gw-wr33, GHSA-hjrf-2m68-5959, GHSA-qwph-4952-7xr6). Changed the direct dependency to `jsonwebtoken@9.0.3`, above the reported fixed version (`9.0.0`), and removed obsolete 8.x comments.

## lodash

Found dev dependency `lodash@4.17.20`, vulnerable to command/code injection, ReDoS, and prototype pollution advisories (GHSA-35jh-r3h4-6jhm, GHSA-r5fr-rjxr-66jc, GHSA-29mw-wpgm-hmr9, GHSA-f23m-r3pf-42rh, GHSA-xxjr-mmjv-4gpg). Changed the dev dependency to `lodash@4.18.1`, above the highest reported fixed version (`4.18.0`).

## path-to-regexp

Found transitive `path-to-regexp@0.1.7` via `express@4.19.2`, vulnerable to ReDoS/backtracking advisories (GHSA-37ch-88jc-xwx2, GHSA-9wv6-86v2-598j, GHSA-rhx6-c78j-4q9w). Changed the direct `express` dependency to `express@4.22.2`, which resolves `path-to-regexp@0.1.13`.

## qs

Found transitive `qs@6.11.0` via `express@4.19.2` and `qs@6.5.5` via `request@2.88.2`, vulnerable to arrayLimit bypass denial of service advisories (GHSA-6rw7-vpxm-498p, GHSA-w7fw-mjwx-w883). Changed `express` to `4.22.2`, resolving `qs@6.15.3`, and removed `request`, eliminating the older `qs@6.5.5` path.

## request

Found direct `request@2.88.2` with SSRF advisory GHSA-p8p7-x288-28g6. Bomly reported no fixed upstream version for `request`; this could not be fixed by changing to a patched `request` version. Removed the dependency and migrated the XML fetch path in `src/importer.js` to the already-used patched `axios` dependency.

## send

Found transitive `send@0.18.0` via `express@4.19.2`, vulnerable to template injection leading to XSS (GHSA-m6fv-jmcg-4jfg). Changed the direct `express` dependency to `express@4.22.2`, which resolves `send@0.19.2`.

## serve-static

Found transitive `serve-static@1.15.0` via `express@4.19.2`, vulnerable to template injection leading to XSS (GHSA-cm22-4g7w-348p). Changed the direct `express` dependency to `express@4.22.2`, which resolves `serve-static@1.16.3`.

## tough-cookie

Found transitive `tough-cookie@2.5.0` via `request@2.88.2`, vulnerable to prototype pollution (GHSA-72xf-g2v4-qvf3). Removed `request`, eliminating `tough-cookie` from the dependency graph.

## uuid

Found transitive `uuid@3.4.0` via `request@2.88.2`, vulnerable to a missing buffer bounds check (GHSA-w5hq-g745-h8pq). Removed `request`, eliminating `uuid` from the dependency graph.
