# Dependency Vulnerability Remediation

## org.postgresql:postgresql
Found `42.6.0` with GHSA-24rp-q3w6-vc56 / CVE-2024-1597 and GHSA-98qh-xjc8-98pq / CVE-2026-42198. Changed `lib.jdbc-driver.postgresql.version` to `42.7.11`, which includes the required fixed versions.

## com.mysql:mysql-connector-j
Found the MySQL connector at vulnerable `8.0.33` with GHSA-m6vm-37g8-gqvh / CVE-2023-22102. Changed the dependency from the legacy `mysql:mysql-connector-java` coordinates to `com.mysql:mysql-connector-j` and set `lib.jdbc-driver.mysql.version` to `8.2.0`, the fixed version reported by bomly.

## org.cyclonedx:cyclonedx-core-java
Found `8.0.3` with GHSA-683x-4444-jxh8 / CVE-2024-38374 and GHSA-6fhj-vr9j-g45r / CVE-2025-64518. Changed `lib.cyclonedx-java.version` to `11.0.1`, and updated the small set of CycloneDX API imports/license-expression calls required by that version.

## org.apache.commons:commons-compress
Found `1.25.0` with GHSA-4265-ccf5-phj5 / CVE-2024-26308 and GHSA-4g9r-vxhx-9pgx / CVE-2024-25710. Added `lib.commons-compress.version` and changed the direct dependency to `1.26.0`.

## commons-io:commons-io
Found transitive `2.13.0` through Alpine with GHSA-78wr-2p64-hpwj / CVE-2024-47554. Pinned `commons-io` to `2.14.0` in dependency management.

## org.apache.commons:commons-lang3
Found transitive `3.13.0` through Alpine with GHSA-j288-q9x7-2f5v / CVE-2025-48924. Pinned `commons-lang3` to `3.18.0` in dependency management.

## com.nimbusds:nimbus-jose-jwt
Found transitive `9.30.2` through Alpine with GHSA-gvpg-vgmx-xg6w / CVE-2023-52428 and GHSA-xwmg-2g98-w7v9 / CVE-2025-53864. Pinned `nimbus-jose-jwt` to `9.37.4` in dependency management.

## com.fasterxml.jackson.core:jackson-databind
Found transitive `2.15.2` through Alpine with GHSA-j3rv-43j4-c7qm / CVE-2026-54512, GHSA-rmj7-2vxq-3g9f / CVE-2026-54513, GHSA-hgj6-7826-r7m5 / CVE-2026-54514, and GHSA-5jmj-h7xm-6q6v / CVE-2026-54515. Pinned `jackson-databind` to `2.18.8`, which fixes the first three; bomly reports no fixed upstream version for GHSA-5jmj-h7xm-6q6v, so that advisory remains unremediated by version change.

## ch.qos.logback:logback-core
Found transitive `1.2.13` through Alpine with multiple Logback advisories including GHSA-25qh-j22f-pwp8 / CVE-2025-11226, GHSA-pr98-23f8-jwxv / CVE-2024-12798, GHSA-6v67-2wr5-gvf4 / CVE-2024-12801, GHSA-jhq6-gfmj-v8fx / CVE-2026-10532, GHSA-p47f-322f-whfh / CVE-2026-9828, and GHSA-qqpg-mvqg-649v / CVE-2026-1225. Pinned `logback-core` and `logback-classic` to `1.5.35` to keep the Logback modules aligned and fixed.

## com.sun.mail:jakarta.mail
Found transitive `1.6.7` through Alpine with GHSA-9342-92gg-6v29 / CVE-2025-7962. Pinned `jakarta.mail` to `1.6.8` in dependency management.

## org.codehaus.plexus:plexus-utils
Found transitive `3.5.1` through `maven-artifact` with GHSA-6fmv-xxpf-w3cw / CVE-2025-67030. Pinned `plexus-utils` to `3.6.1` in dependency management.

## io.pebbletemplates:pebble
Found direct `3.2.0` with GHSA-p75g-cxfj-7wrx / CVE-2025-1686. bomly reports no fixed upstream version, so no version change was made.

## commons-fileupload:commons-fileupload
Found test-transitive `1.4` through WireMock with GHSA-hfrx-6qgj-fp6c / CVE-2023-24998 and GHSA-vv7r-c36w-3prj / CVE-2025-48976. Pinned `commons-fileupload` to `1.6.0` in dependency management.

## org.eclipse.jetty:jetty-server
Found test-transitive `9.4.49.v20220914` through WireMock with GHSA-q4rv-gq96-w7c5 / CVE-2024-13009, GHSA-g8m5-722r-8whq / CVE-2024-8184, GHSA-qw69-rqj8-6qw8 / CVE-2023-26048, and GHSA-p26g-97m4-6q7c / CVE-2023-26049. Imported Jetty BOM `9.4.58.v20250814`, which moves WireMock's Jetty 9 stack to the latest patched 9.4 line.

## org.eclipse.jetty.http2:http2-common
Found test-transitive `9.4.49.v20220914` through WireMock with GHSA-mmxm-8w33-wc4h / CVE-2025-5115, GHSA-rggv-cv7r-mw98 / CVE-2024-22201, and GHSA-qppj-fm5r-hxr3 / CVE-2023-44487. Imported Jetty BOM `9.4.58.v20250814` and pinned `http2-common` to that version.

## org.eclipse.jetty:jetty-http
Found test-transitive `9.4.49.v20220914` through WireMock with GHSA-hmr7-m48g-48f6 / CVE-2023-40167, GHSA-qh8g-58pp-2wxh / CVE-2024-6763, and after the Jetty 9 update GHSA-355h-qmc2-wpwf / CVE-2026-2332. Importing Jetty BOM `9.4.58.v20250814` fixes the older Jetty 9 advisory; bomly reports no fixed upstream version for GHSA-355h-qmc2-wpwf, and GHSA-qh8g-58pp-2wxh is only reported fixed in Jetty `12.0.12`, which is not a compatible version-only override for WireMock 2.x's Jetty 9 dependency stack.

## org.eclipse.jetty:jetty-servlets
Found test-transitive `9.4.49.v20220914` through WireMock with GHSA-j26w-f9rq-mr2q / CVE-2024-9823 and GHSA-3gh6-v5v9-6v9j / CVE-2023-36479. Imported Jetty BOM `9.4.58.v20250814` to move the Jetty 9 stack to a fixed version.

## com.github.jknack:handlebars
Found test-transitive `4.3.1` through WireMock with GHSA-r4gv-qr8j-p3pg / CVE-2026-55760. Pinned `handlebars` to `4.5.2` in dependency management.

## org.xmlunit:xmlunit-core
Found test-transitive `2.9.0` through WireMock with GHSA-chfm-68vv-pvw5 / CVE-2024-31573. Pinned `xmlunit-core` to `2.10.0` in dependency management.

## com.fasterxml.jackson.core:jackson-core
Found test-transitive `2.15.2` through WireMock with GHSA-72hv-8253-57qq. Pinned `jackson-core` to `2.18.6` in dependency management.

## com.jayway.jsonpath:json-path
Found test-transitive `2.7.0` through WireMock with GHSA-pfh2-hfmq-phg5 / CVE-2023-51074. Pinned `json-path` to `2.9.0` in dependency management.

## org.assertj:assertj-core
Found direct test dependency `3.24.2` with GHSA-rqfh-9r24-8c9r / CVE-2026-24400. Overrode `lib.assertj.version` to `3.27.7`.

## org.bouncycastle:bcprov-jdk18on
Found test-transitive `1.72` through MockServer with multiple Bouncy Castle advisories, and later `1.80.2` still affected by GHSA-c3fc-8qff-9hwx / CVE-2026-0636. Pinned `bcprov-jdk18on` to `1.84` in dependency management.

## org.bouncycastle:bcpkix-jdk18on
Found test-transitive `1.72` through MockServer with GHSA-4cx2-fc23-5wg6 / CVE-2025-8916, GHSA-wg6q-6289-32hp / CVE-2026-5588, and GHSA-wjxj-5m7g-mg7q / CVE-2023-33202. Pinned `bcpkix-jdk18on` to `1.84` in dependency management.

## io.netty:netty-handler
Found test-transitive `4.1.86.Final` through MockServer with GHSA-3qp7-7mw8-wx86 / CVE-2026-44249, GHSA-c653-97m9-rcg9 / CVE-2026-50010, GHSA-x4gw-5cx5-pgmh / CVE-2026-45416, and GHSA-6mjq-h674-j845 / CVE-2023-34462. Imported Netty BOM `4.1.135.Final`.

## io.netty:netty-common
Found test-transitive `4.1.86.Final` through MockServer with GHSA-389x-839f-4rhx / CVE-2025-25193 and GHSA-xq3w-v528-46rv / CVE-2024-47535. Imported Netty BOM `4.1.135.Final`.

## commons-beanutils:commons-beanutils
Found test-transitive `1.9.4` through MockServer with GHSA-wxr5-93ph-8wr9 / CVE-2025-48734. Pinned `commons-beanutils` to `1.11.0` in dependency management.

## org.mozilla:rhino
Found test-transitive `1.7.7.2` through MockServer with GHSA-3w8q-xq97-5j7x / CVE-2025-66453. Pinned `rhino` to `1.8.1` in dependency management.
