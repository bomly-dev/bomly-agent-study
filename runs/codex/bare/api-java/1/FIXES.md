# Vulnerability Remediation

- `com.mysql:mysql-connector-j`: OSV reported `GHSA-m6vm-37g8-gqvh` against MySQL Connector/J 8.0.33. Changed the JDBC driver coordinate from the relocated `mysql:mysql-connector-java` artifact to `com.mysql:mysql-connector-j` and upgraded to 8.2.0, the first fixed version.

- `org.postgresql:postgresql`: OSV reported `GHSA-24rp-q3w6-vc56` and `GHSA-98qh-xjc8-98pq` against 42.6.0. Upgraded the PostgreSQL JDBC driver to 42.7.13, which is beyond the fixed versions for both advisories.

- `com.sun.mail:jakarta.mail`: OSV reported `GHSA-9342-92gg-6v29` against 1.6.7. Overrode the parent-managed JavaMail version to 1.6.8, the fixed 1.x release.

- `com.fasterxml.jackson.core:jackson-core`: OSV reported `GHSA-72hv-8253-57qq` against 2.15.2. Overrode the parent-managed Jackson 2.x version to 2.18.8, which OSV reports as fixed.

- `com.fasterxml.jackson.core:jackson-databind`: OSV reported `GHSA-hgj6-7826-r7m5`, `GHSA-j3rv-43j4-c7qm`, and `GHSA-rmj7-2vxq-3g9f` against 2.15.2. Overrode the parent-managed Jackson databind version to 2.18.8, which fixes those advisories. OSV still reports `GHSA-5jmj-h7xm-6q6v` for `com.fasterxml.jackson.core:jackson-databind`, and OSV lists no fixed version for the `com.fasterxml` artifact line; no version-only remediation exists for that advisory.

- `tools.jackson.core:jackson-core`: Introduced through `net.logstash.logback:logstash-logback-encoder` 9.0 and OSV reported `GHSA-2m67-wjpj-xhg9`, `GHSA-6v53-7c9g-w56r`, and `GHSA-72hv-8253-57qq` against 3.0.1. Added dependency management to force 3.1.4, which OSV reports as fixed.

- `tools.jackson.core:jackson-databind`: Introduced through `net.logstash.logback:logstash-logback-encoder` 9.0 and OSV reported multiple Jackson databind advisories against 3.0.1. Added dependency management to force 3.1.4, which OSV reports as fixed.

- `ch.qos.logback:logback-core`: OSV reported multiple advisories against 1.2.13, including `GHSA-25qh-j22f-pwp8`, `GHSA-6v67-2wr5-gvf4`, `GHSA-jhq6-gfmj-v8fx`, `GHSA-p47f-322f-whfh`, `GHSA-pr98-23f8-jwxv`, and `GHSA-qqpg-mvqg-649v`. Overrode Logback to 1.5.35 and aligned SLF4J/logstash encoder versions for compatibility.

- `org.cyclonedx:cyclonedx-core-java`: OSV reported `GHSA-683x-4444-jxh8` and `GHSA-6fhj-vr9j-g45r` against 8.0.3. Upgraded to 11.0.1, which fixes both, and adjusted the small API changes for parser/generator factories and license expressions.

- `io.pebbletemplates:pebble`: OSV reported `GHSA-p75g-cxfj-7wrx` against 3.2.0. Upgraded to 3.2.4, the first 3.x version OSV reports as not affected.

- `commons-io:commons-io`: OSV reported `GHSA-78wr-2p64-hpwj` against 2.13.0. Overrode the parent-managed version to 2.22.0.

- `org.apache.commons:commons-lang3`: OSV reported `GHSA-j288-q9x7-2f5v` against 3.13.0. Overrode the parent-managed version to 3.20.0.

- `org.apache.commons:commons-compress`: OSV reported `GHSA-4265-ccf5-phj5` and `GHSA-4g9r-vxhx-9pgx` against 1.25.0. Upgraded the direct dependency to 1.28.0 and adjusted one catch block for the newer exception hierarchy.

- `org.codehaus.plexus:plexus-utils`: OSV reported `GHSA-6fmv-xxpf-w3cw` against 3.5.1 through `maven-artifact`. Added dependency management to force 3.6.1, the fixed 3.x release.

- `com.nimbusds:nimbus-jose-jwt`: OSV reported `GHSA-gvpg-vgmx-xg6w` and `GHSA-xwmg-2g98-w7v9` against 9.30.2. Added dependency management to force 9.37.4, the fixed 9.x release.

- `commons-beanutils:commons-beanutils`: OSV reported `GHSA-wxr5-93ph-8wr9` against 1.9.4 from test dependencies. Added dependency management to force 1.11.0.

- `commons-fileupload:commons-fileupload`: OSV reported `GHSA-hfrx-6qgj-fp6c` and `GHSA-vv7r-c36w-3prj` against 1.4 from test dependencies. Added dependency management to force 1.6.0.

- `com.jayway.jsonpath:json-path`: OSV reported `GHSA-pfh2-hfmq-phg5` against 2.7.0 from test dependencies. Added dependency management to force 2.10.0.

- `org.xmlunit:xmlunit-core`: OSV reported `GHSA-chfm-68vv-pvw5` against 2.9.0 from test dependencies. Added dependency management to force 2.12.0.

- `org.assertj:assertj-core`: OSV reported `GHSA-rqfh-9r24-8c9r` against 3.24.2. Overrode the parent-managed test version to 3.27.7.

- `com.github.jknack:handlebars`: OSV reported `GHSA-r4gv-qr8j-p3pg` against 4.3.1 from WireMock test dependencies. Added dependency management to force 4.5.3.

- `org.mozilla:rhino`: OSV reported `GHSA-3w8q-xq97-5j7x` against 1.7.7.2 from test dependencies. Added dependency management to force 1.8.1.

- `org.bouncycastle:bcprov-jdk18on`: OSV reported multiple Bouncy Castle advisories against 1.72 from MockServer test dependencies. Added dependency management to force 1.84.

- `org.bouncycastle:bcpkix-jdk18on`: OSV reported multiple Bouncy Castle advisories against 1.72 from MockServer test dependencies. Added dependency management to force 1.84.

- `io.netty:netty-common`: OSV reported `GHSA-389x-839f-4rhx` and `GHSA-xq3w-v528-46rv` against 4.1.86.Final from MockServer test dependencies. Upgraded MockServer and imported the Netty BOM at 4.1.135.Final.

- `io.netty:netty-codec`: OSV reported `GHSA-3p8m-j85q-pgmj` and `GHSA-mj4r-2hfc-f8p6` against 4.1.86.Final from test dependencies. Upgraded MockServer and imported the Netty BOM at 4.1.135.Final.

- `io.netty:netty-codec-http`: OSV reported multiple HTTP parsing and request smuggling advisories against 4.1.86.Final from test dependencies. Upgraded MockServer and imported the Netty BOM at 4.1.135.Final.

- `io.netty:netty-codec-http2`: OSV reported multiple HTTP/2 advisories against 4.1.86.Final from test dependencies. Upgraded MockServer and imported the Netty BOM at 4.1.135.Final.

- `io.netty:netty-handler`: OSV reported multiple handler/SNI advisories against 4.1.86.Final from test dependencies. Upgraded MockServer and imported the Netty BOM at 4.1.135.Final.

- `io.netty:netty-handler-proxy`: OSV reported `GHSA-45q3-82m4-75jr` against 4.1.86.Final from test dependencies. Upgraded MockServer and imported the Netty BOM at 4.1.135.Final.

- `org.eclipse.jetty:jetty-server`: OSV reported multiple Jetty 9 advisories against 9.4.49 from `wiremock-jre8`. Replaced the obsolete WireMock dependency with `org.wiremock:wiremock` 4.0.0-beta.38 plus `org.wiremock:wiremock-junit4`, and imported Jetty BOM 12.1.11.

- `org.eclipse.jetty:jetty-http`: OSV reported multiple advisories against Jetty 9.4.49, and later against Jetty 11.0.26 where OSV only lists Jetty 12 fixes. Moved WireMock to the Jetty 12 beta line and imported Jetty BOM 12.1.11.

- `org.eclipse.jetty:jetty-xml`: OSV reported `GHSA-58qw-p7qm-5rvh` against 9.4.49 from `wiremock-jre8`. Moved WireMock to the Jetty 12 beta line and imported Jetty BOM 12.1.11.

- `org.eclipse.jetty:jetty-servlets`: OSV reported `GHSA-3gh6-v5v9-6v9j` and `GHSA-j26w-f9rq-mr2q` against 9.4.49 from `wiremock-jre8`. Moved WireMock to the Jetty 12 beta line and imported Jetty BOM 12.1.11.

- `org.eclipse.jetty.http2:http2-common`: OSV reported multiple HTTP/2 advisories against 9.4.49 from `wiremock-jre8`. Moved WireMock to the Jetty 12 beta line and imported Jetty BOM 12.1.11.

- `org.eclipse.jetty.http2:http2-hpack`: OSV reported `GHSA-wgh7-54f2-x98r` against 9.4.49 from `wiremock-jre8`. Moved WireMock to the Jetty 12 beta line and imported Jetty BOM 12.1.11.

- `org.eclipse.jetty.http2:http2-server`: OSV reported `GHSA-qppj-fm5r-hxr3` against 9.4.49 from `wiremock-jre8`. Moved WireMock to the Jetty 12 beta line and imported Jetty BOM 12.1.11.
