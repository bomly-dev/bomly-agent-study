# Dependency vulnerability remediation

Scope: `fixtures/api-java` (Maven). Found via `bomly scan --enrich --audit`. GitHub Actions
workflow manifests were also scanned but produced only "unknown license" warnings, no
vulnerabilities, so no action was needed there.

All fixes below were applied either as a direct version bump (for dependencies declared
in `pom.xml`) or as a `<dependencyManagement>` pin (for transitive dependencies pulled in
by `alpine-*`, `maven-artifact`, `wiremock-jre8`, or `mockserver-netty`). `make test`
passes (336/336) after all changes.

## Fixed by direct version bump

| Package | Was | Now | Advisories fixed |
|---|---|---|---|
| `org.postgresql:postgresql` | 42.6.0 | 42.7.11 | GHSA-24rp-q3w6-vc56 (critical, SQLi via line comment), GHSA-98qh-xjc8-98pq |
| `com.mysql:mysql-connector-j` (was `mysql:mysql-connector-java`, deprecated/relocated at 8.0.33) | 8.0.33 | 8.2.0 | GHSA-m6vm-37g8-gqvh (CVE-2023-22102) |
| `org.apache.commons:commons-compress` | 1.25.0 | 1.26.0 | GHSA-4265-ccf5-phj5, GHSA-4g9r-vxhx-9pgx |
| `org.assertj:assertj-core` (test) | 3.24.2 | 3.27.7 | GHSA-rqfh-9r24-8c9r |
| `org.cyclonedx:cyclonedx-core-java` | 8.0.3 | 11.0.1 | GHSA-683x-4444-jxh8 (XXE), GHSA-6fhj-vr9j-g45r (XXE in BOM validation) |

The `cyclonedx-core-java` bump is a major-version jump (8→11) with real API breakage:
`BomGeneratorFactory`/`BomParserFactory` moved from `org.cyclonedx` to
`org.cyclonedx.generators` / `org.cyclonedx.parsers`, and `LicenseChoice.getExpression()`
now returns an `org.cyclonedx.model.license.Expression` object instead of a `String`.
Updated call sites: `CycloneDXExporter.java`, `BomUploadProcessingTask.java`,
`VexUploadProcessingTask.java`, `CycloneDXVexImporterTest.java` (import paths), and
`ModelConverter.java` (unwrap/wrap the license expression via `Expression.getValue()` /
`new Expression(String)`).

The MySQL driver's Maven coordinates changed at exactly 8.0.33 (Oracle relocated the
artifact from `mysql:mysql-connector-java` to `com.mysql:mysql-connector-j`); no fixed
version was ever published under the old coordinates, so the `<dependency>` block itself
had to be switched, not just the version.

## Fixed by pinning transitive dependencies (`<dependencyManagement>`)

| Package | Was | Now | Pulled in via | Advisories fixed |
|---|---|---|---|---|
| `com.fasterxml.jackson.core:jackson-databind` (+ `jackson-core`/`jackson-annotations` via imported `jackson-bom`) | 2.15.2 | 2.18.8 | `alpine-server` | GHSA-j3rv-43j4-c7qm (PolymorphicTypeValidator bypass, high), GHSA-rmj7-2vxq-3g9f (allowlist bypass, high), GHSA-hgj6-7826-r7m5 (SSRF), GHSA-72hv-8253-57qq |
| `io.netty:*` (imported `netty-bom`) | 4.1.86.Final | 4.1.135.Final | `mockserver-netty` (test) | GHSA-3p8m-j85q-pgmj, GHSA-mj4r-2hfc-f8p6, GHSA-38f8-5428-x5cv, GHSA-57rv-r2g8-2cj3, GHSA-5jpm-x58v-624v, GHSA-84h7-rjj3-6jx4, GHSA-f6hv-jmp6-3vwv, GHSA-fghv-69vj-qj49, GHSA-hvcg-qmg6-jm4c, GHSA-m4cv-j2px-7723, GHSA-pwqr-wmgm-9rr8, GHSA-v8h7-rr48-vmmv, GHSA-xxqh-mfjm-7mv9, GHSA-563q-j3cm-6jxm, GHSA-5x3r-wrvg-rp6q, GHSA-c2gf-v879-257j, GHSA-prj3-ccx8-p6x4, GHSA-w9fj-cfpg-grvv, GHSA-xpw8-rcwv-8f8p, GHSA-389x-839f-4rhx, GHSA-xq3w-v528-46rv, GHSA-3qp7-7mw8-wx86, GHSA-6mjq-h674-j845, GHSA-c653-97m9-rcg9, GHSA-x4gw-5cx5-pgmh, GHSA-45q3-82m4-75jr |
| `ch.qos.logback:logback-core` / `logback-classic` | 1.2.13 | 1.5.35 | `alpine-server` | GHSA-25qh-j22f-pwp8, GHSA-6v67-2wr5-gvf4, GHSA-jhq6-gfmj-v8fx, GHSA-p47f-322f-whfh, GHSA-pr98-23f8-jwxv, GHSA-qqpg-mvqg-649v |
| `org.bouncycastle:bcprov-jdk18on` / `bcpkix-jdk18on` | 1.72 | 1.80.2 | `mockserver-netty` (test) | GHSA-574f-3g2m-x479 (critical, GOST keystream reuse), GHSA-4h8f-2wvx-gg5w, GHSA-67mf-3cr5-8w23, GHSA-8xfc-gm6g-vgpv, GHSA-hr8g-6v94-x4m9, GHSA-v435-xc8x-wvr9 (Marvin attack), GHSA-wjxj-5m7g-mg7q |
| `org.eclipse.jetty:*` / `org.eclipse.jetty.http2:*` (all 9.4.x modules) | 9.4.49.v20220914 | 9.4.58.v20250814 | `wiremock-jre8` (test) | GHSA-hmr7-m48g-48f6 (CVE-2023-40167), GHSA-mmxm-8w33-wc4h, GHSA-qppj-fm5r-hxr3, GHSA-rggv-cv7r-mw98, GHSA-g8m5-722r-8whq, GHSA-p26g-97m4-6q7c |
| `org.apache.commons:commons-lang3` | 3.13.0 | 3.18.0 | `alpine-common` | GHSA-j288-q9x7-2f5v |
| `commons-io:commons-io` | 2.13.0 | 2.14.0 | `alpine-server` | GHSA-78wr-2p64-hpwj |
| `com.nimbusds:nimbus-jose-jwt` | 9.30.2 | 9.37.4 | `alpine-server` (via `oauth2-oidc-sdk`) | GHSA-gvpg-vgmx-xg6w, GHSA-xwmg-2g98-w7v9 |
| `com.sun.mail:jakarta.mail` | 1.6.7 | 1.6.8 | `alpine-server` | GHSA-9342-92gg-6v29 |
| `org.codehaus.plexus:plexus-utils` | 3.5.1 | 3.6.1 | `org.apache.maven:maven-artifact` | GHSA-6fmv-xxpf-w3cw |
| `commons-fileupload:commons-fileupload` (test) | 1.4 | 1.6.0 | `wiremock-jre8` | GHSA-hfrx-6qgj-fp6c, GHSA-vv7r-c36w-3prj |
| `com.jayway.jsonpath:json-path` (test) | 2.7.0 | 2.9.0 | `wiremock-jre8` | GHSA-pfh2-hfmq-phg5 |
| `com.github.jknack:handlebars` / `handlebars-helpers` (test) | 4.3.1 | 4.5.2 | `wiremock-jre8` | GHSA-r4gv-qr8j-p3pg |
| `org.xmlunit:xmlunit-core` / `xmlunit-legacy` / `xmlunit-placeholders` (test) | 2.9.0 | 2.10.0 | `wiremock-jre8` | GHSA-chfm-68vv-pvw5 |
| `commons-beanutils:commons-beanutils` (test) | 1.9.4 | 1.11.0 | `mockserver-netty` (via commons-configuration) | GHSA-wxr5-93ph-8wr9 |

## No fix available upstream (not remediated by a version change)

These were verified via `bomly_explain` — each advisory's `fix_state` is `not-fixed` and
the affected-version range extends through (or beyond) the latest published release, so
no version bump closes them:

- **`io.pebbletemplates:pebble` 3.2.0** — GHSA-p75g-cxfj-7wrx / CVE-2025-1686 (Arbitrary
  Local File Inclusion via the `include` macro, high). Affected range is `<=3.2.3`
  (the latest release), i.e. every published version is vulnerable. Upstream issue:
  https://github.com/PebbleTemplates/pebble/issues/680. Left at 3.2.0; no safe upgrade
  target exists today.
- **`org.eclipse.jetty:jetty-http` (9.4.x line, test-only via `wiremock-jre8`)** —
  - GHSA-355h-qmc2-wpwf / CVE-2026-2332 (HTTP request smuggling via chunked extension
    quoted-string parsing). Affected range `>=9.4.0,<=9.4.59`, i.e. unfixed anywhere in
    the 9.4.x branch (which is EOL). Only fixed in the Jetty 12.x line, which
    `wiremock-jre8` 2.35.x does not support.
  - GHSA-wjpw-4j6x-6rwh / CVE-2025-11143 (inconsistent invalid-URI parsing, low).
    Same situation: affected range `>=9.4.0,<=9.4.58`, no 9.4.x fix exists.
  - Both are test-scope only (exercised by WireMock in tests, not shipped in the
    application), and the module was still bumped to the latest available 9.4.x patch
    (9.4.58.v20250814) to pick up the advisories that *are* fixed at that version
    (see table above).
- **`com.fasterxml.jackson.core:jackson-databind`** — GHSA-5jmj-h7xm-6q6v /
  CVE-2026-54515 (case-insensitive deserialization bypasses per-property
  `@JsonIgnoreProperties`, medium). Affected range `>=2.8.0,<2.18.9`; no fixed version
  has been released as of this scan (2026-07-10). jackson-databind was still bumped to
  2.18.8 to close the other three advisories on it (see table above); this one specific
  CVE remains open pending an upstream release.

## Not addressed (license policy, not a vulnerability)

`bomly` also flagged several `INVALID-*` "unknown/non-standard SPDX license" findings
(e.g. on `system-rules`, `jboss-logging`, various `google-*`/`jnr-*` transitive
packages, and every GitHub Actions workflow file). These are license-policy warnings,
not known vulnerabilities, and are out of scope for this remediation pass.
