# Vulnerability Remediation Log

## fixtures/webapp

- `axios`: Found multiple SSRF, DoS, header injection, redirect credential leak, and prototype-pollution gadget advisories against `axios@1.6.0` including GHSA-8hc4-vh64-cxmj, GHSA-jr5f-v2jv-69x6, GHSA-4hjh-wcwx-xvwj, GHSA-3p68-rc4w-qgx5, GHSA-pjwm-pj3p-43mv, GHSA-p92q-9vqr-4j8v, GHSA-j5f8-grm9-p9fc, GHSA-35jp-ww65-95wh, and related 2026 axios advisories. Upgraded the direct dependency to `axios@1.18.1`, which npm audit and bomly report as not vulnerable.

- `express`: Found GHSA-qw6h-vgh9-j6wx against `express@4.19.2`. Upgraded the direct dependency to `express@4.22.2`, staying on the 4.x line while pulling patched transitive versions.

- `body-parser`: Found GHSA-qwcr-r2fm-qrc7 through `express@4.19.2`. Upgrading `express` to `4.22.2` moved `body-parser` to `1.20.5`, which resolves the finding.

- `cookie`: Found GHSA-pxg6-pf52-xh8x through `express@4.19.2`. Upgrading `express` to `4.22.2` moved `cookie` to `0.7.2`, which resolves the finding.

- `path-to-regexp`: Found GHSA-9wv6-86v2-598j, GHSA-rhx6-c78j-4q9w, and GHSA-37ch-88jc-xwx2 through `express@4.19.2`. Upgrading `express` to `4.22.2` moved `path-to-regexp` to `0.1.13`, which resolves the findings.

- `send`: Found GHSA-m6fv-jmcg-4jfg through `express@4.19.2`. Upgrading `express` to `4.22.2` moved `send` to `0.19.2`, which resolves the finding.

- `serve-static`: Found GHSA-cm22-4g7w-348p through `express@4.19.2`. Upgrading `express` to `4.22.2` moved `serve-static` to `1.16.3`, which resolves the finding.

- `qs`: Found GHSA-w7fw-mjwx-w883 and GHSA-6rw7-vpxm-498p through `express` and `request`. Upgrading `express` moved its `qs` to `6.15.3`; removing `request` removed its vulnerable `qs` path. npm audit now reports no `qs` vulnerability.

- `jsonwebtoken`: Found GHSA-8cf7-32gw-wr33, GHSA-hjrf-2m68-5959, and GHSA-qwph-4952-7xr6 against `jsonwebtoken@8.5.1`. Upgraded the direct dependency to `jsonwebtoken@9.0.3`, which resolves the findings.

- `lodash`: Found GHSA-35jh-r3h4-6jhm, GHSA-29mw-wpgm-hmr9, GHSA-r5fr-rjxr-66jc, GHSA-f23m-r3pf-42rh, and GHSA-xxjr-mmjv-4gpg against `lodash@4.17.20`. Upgraded the direct dev dependency to `lodash@4.18.1`, which resolves the findings.

- `request`: Found GHSA-p8p7-x288-28g6 against `request@2.88.2`. No fixed version exists for the deprecated `request` package, so I removed the dependency and migrated the XML fetch path to the already-used `axios` client.

- `form-data`: Found GHSA-fjxv-7rqg-78g4 and GHSA-hmw2-7cc7-3qxx through `request`'s pinned `form-data@2.3.3`. `request` has no fixed version that updates this transitive dependency, so removing `request` removed the vulnerable package path.

- `tough-cookie`: Found GHSA-72xf-g2v4-qvf3 through `request`. `request` has no fixed version that updates this transitive dependency, so removing `request` removed the vulnerable package path.

- `uuid`: Found GHSA-w5hq-g745-h8pq through `request`. `request` has no fixed version that updates this transitive dependency, so removing `request` removed the vulnerable package path.

## fixtures/service

- `pyjwt`: Found PYSEC-2022-202, PYSEC-2026-120, PYSEC-2026-179, PYSEC-2026-175, and PYSEC-2026-177 against `pyjwt@1.7.1`. Upgraded the direct dependency to `pyjwt@2.13.0` and adjusted token encoding code for PyJWT 2.x string-return semantics; pip-audit reports no remaining PyJWT vulnerabilities.

- `urllib3`: Found PYSEC-2023-192, PYSEC-2023-212, PYSEC-2026-141, CVE-2024-37891, CVE-2025-50181, CVE-2025-66418, CVE-2025-66471, and CVE-2026-21441 against `urllib3@1.26.5`. Updated the compiled runtime pin to `urllib3@2.7.0`, which is allowed by `requests` and clears the pip-audit findings.

## fixtures/api-java

- `com.fasterxml.jackson.core:jackson-databind`: Found GHSA-3wrr-7qpf-2prh, GHSA-3x8x-79m2-3w2w, GHSA-57j2-w4cx-62h2, GHSA-hgj6-7826-r7m5, GHSA-j3rv-43j4-c7qm, GHSA-jjjh-jjxp-wpff, GHSA-rgv9-q543-rqg4, and GHSA-rmj7-2vxq-3g9f against `2.13.0`; upgraded to `2.18.8`, which resolves those fixed-version advisories. GHSA-5jmj-h7xm-6q6v / CVE-2026-54515 remains reported by bomly as `not-fixed`; no fixed version is available, so I did not claim it fixed by version.

- `org.apache.commons:commons-configuration2`: Found GHSA-xj57-8qj4-c4m6, GHSA-9w38-p64v-xpmv, GHSA-xjp4-hw94-mvp5, and GHSA-337m-mw94-2v6g against `2.7`. Upgraded to `2.15.0`, which resolves the findings.
