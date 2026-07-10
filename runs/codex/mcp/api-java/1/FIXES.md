# Vulnerability Remediation Record

- `ch.qos.logback:logback-core` was resolved at `1.2.13` and flagged vulnerable. I pinned `logback-core` and its paired `logback-classic` module to `1.5.35` in Maven dependency management so transitive logging dependencies resolve to a patched line.

- `com.fasterxml.jackson.core:jackson-core` was resolved at `2.15.2` and flagged vulnerable. I pinned it to `2.18.8`, which clears the known fixable advisory.

- `com.fasterxml.jackson.core:jackson-databind` was resolved at `2.15.2` and flagged vulnerable. I pinned it to `2.18.8`, which clears the known fixable advisories. A final scan still reports `GHSA-5jmj-h7xm-6q6v` / `CVE-2026-54515` against `2.18.8` as `no-fix-upstream`, so no version-only remediation currently exists for that remaining advisory.

- `com.github.jknack:handlebars` was resolved at `4.3.1` and flagged vulnerable. I pinned it to `4.5.3`, a patched version above the vulnerable range.

- `com.jayway.jsonpath:json-path` was resolved at `2.7.0` and flagged vulnerable. I pinned it to `2.9.0`, the fixed version recommended by the scanner.

- `com.mysql:mysql-connector-j` was resolved at `8.0.33` via the old `mysql:mysql-connector-java` coordinates and flagged vulnerable. I changed the direct dependency to the current `com.mysql:mysql-connector-j` coordinates and bumped it to `8.2.0`.

- `com.nimbusds:nimbus-jose-jwt` was resolved at `9.30.2` and flagged vulnerable. I pinned it to `9.37.4`, the patched version recommended by the scanner.

- `com.sun.mail:jakarta.mail` was resolved at `1.6.7` and flagged vulnerable. I pinned it to `1.6.8`, which contains the upstream fix.

- `commons-beanutils:commons-beanutils` was resolved at `1.9.4` and flagged vulnerable. I pinned it to `1.11.0`, a patched version above the affected range.

- `commons-fileupload:commons-fileupload` was resolved at `1.4` and flagged vulnerable. I pinned it to `1.6.0`, which clears the reported advisories.

- `commons-io:commons-io` was resolved at `2.13.0` and flagged vulnerable. I pinned it to `2.14.0`, the fixed version recommended by the scanner.

- `io.netty:netty-codec` was resolved at `4.1.86.Final` and flagged vulnerable. I pinned it to `4.1.135.Final` in dependency management.

- `io.netty:netty-codec-http` was resolved at `4.1.86.Final` and flagged vulnerable. I pinned it to `4.1.135.Final` in dependency management.

- `io.netty:netty-codec-http2` was resolved at `4.1.86.Final` and flagged vulnerable. I pinned it to `4.1.135.Final` in dependency management.

- `io.netty:netty-common` was resolved at `4.1.86.Final` and flagged vulnerable. I pinned it to `4.1.135.Final` in dependency management.

- `io.netty:netty-handler` was resolved at `4.1.86.Final` and flagged vulnerable. I pinned it to `4.1.135.Final` in dependency management.

- `io.netty:netty-handler-proxy` was resolved at `4.1.86.Final` and flagged vulnerable. I pinned it to `4.1.135.Final` in dependency management.

- `io.pebbletemplates:pebble` was resolved at `3.2.0` and flagged for `GHSA-p75g-cxfj-7wrx` / `CVE-2025-1686`. The scanner reports this advisory as `no-fix-upstream`, with no fixed Pebble version released, so I left the version unchanged and did not claim a version remediation.

- `org.apache.commons:commons-compress` was resolved at `1.25.0` and flagged vulnerable. I bumped the direct dependency to `1.26.0`, which clears the reported advisory.

- `org.apache.commons:commons-lang3` was resolved at `3.13.0` and flagged vulnerable. I pinned it to `3.18.0`, a patched version above the affected range.

- `org.assertj:assertj-core` was resolved at `3.24.2` and flagged vulnerable. I overrode the test dependency version to `3.27.7`.

- `org.bouncycastle:bcpkix-jdk18on` was resolved at `1.72` and flagged vulnerable. I pinned it to `1.84` and also pinned the related Bouncy Castle modules for a consistent resolved set.

- `org.bouncycastle:bcprov-jdk18on` was resolved at `1.72` and flagged vulnerable. I pinned it to `1.84`.

- `org.codehaus.plexus:plexus-utils` was resolved at `3.5.1` and flagged vulnerable. I pinned it to `3.6.1`, the patched version recommended by the scanner.

- `org.cyclonedx:cyclonedx-core-java` was resolved at `8.0.3` and flagged vulnerable. I bumped the direct dependency to `11.0.1` and made the minimal API import/model updates required by the newer CycloneDX library.

- `org.eclipse.jetty.http2:http2-common` was resolved from the old WireMock test dependency on the Jetty 9 line and flagged vulnerable. I replaced `wiremock-jre8` with `org.wiremock:wiremock-jetty12:3.13.2` and imported the Jetty 12.0.33 BOMs so this module resolves to the patched Jetty 12 line.

- `org.eclipse.jetty.http2:http2-hpack` was resolved from the old WireMock test dependency on the Jetty 9 line and flagged vulnerable. I replaced the WireMock artifact and imported the Jetty 12.0.33 BOMs so this module resolves to a patched version.

- `org.eclipse.jetty.http2:http2-server` was resolved from the old WireMock test dependency on the Jetty 9 line and flagged vulnerable. I replaced the WireMock artifact and imported the Jetty 12.0.33 BOMs so this module resolves to a patched version.

- `org.eclipse.jetty:jetty-http` was resolved from the old WireMock test dependency and flagged vulnerable. I replaced `wiremock-jre8` with the Jetty 12 WireMock artifact and imported the Jetty 12.0.33 BOMs, which clears the Jetty HTTP advisories.

- `org.eclipse.jetty:jetty-server` was resolved from the old WireMock test dependency and flagged vulnerable. I replaced `wiremock-jre8` with the Jetty 12 WireMock artifact and imported the Jetty 12.0.33 BOMs, which clears the Jetty server advisories.

- `org.eclipse.jetty:jetty-servlets` was resolved from the old WireMock test dependency on the Jetty 9 line and flagged vulnerable. Replacing `wiremock-jre8` with `org.wiremock:wiremock-jetty12:3.13.2` removed the vulnerable Jetty 9 servlet dependency from the resolved graph.

- `org.eclipse.jetty:jetty-xml` was resolved from the old WireMock test dependency on the Jetty 9 line and flagged vulnerable. Replacing `wiremock-jre8` with `org.wiremock:wiremock-jetty12:3.13.2` removed the vulnerable Jetty 9 XML dependency from the resolved graph.

- `org.mozilla:rhino` was resolved at `1.7.7.2` and flagged vulnerable. I pinned it to `1.7.14.1`, which clears the reported advisory.

- `org.postgresql:postgresql` was resolved at `42.6.0` and flagged vulnerable. I bumped the direct dependency to `42.7.11`, a patched version above the affected range.

- `org.xmlunit:xmlunit-core` was resolved at `2.9.0` and flagged vulnerable. I pinned it to `2.10.0`, the patched version recommended by the scanner.
