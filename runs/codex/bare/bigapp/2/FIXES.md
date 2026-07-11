# Dependency Vulnerability Fixes

Vulnerability source: `trivy fs --scanners vuln --pkg-types library fixtures/bigapp`.

| Package | What was found | Action taken | Why |
| --- | --- | --- | --- |
| `ca.juliusdavies:not-yet-commons-ssl` | `0.3.9` is vulnerable to CVE-2014-3604. Trivy lists `0.3.15` as fixed. | No version change. | Maven Central only publishes `0.3.9` for this coordinate, so no fixed version exists that can be applied by changing the version. |
| `com.fasterxml.jackson.core:jackson-core` | `2.18.2` was vulnerable to GHSA-72hv-8253-57qq. | Managed Jackson core at `2.18.9`; standalone test plugin POMs now declare `2.18.9`. | `2.18.9` is in the fixed line and keeps the app on the existing Jackson minor family. |
| `com.fasterxml.jackson.core:jackson-databind` | `2.18.2` was vulnerable to CVE-2026-54512, CVE-2026-54513, CVE-2026-54514, and CVE-2026-54515. | Updated `jackson.databind` to `2.18.9`; standalone test plugin POMs now declare `2.18.9`. | `2.18.9` is the fixed `2.18.x` release reported by the scanner. |
| `com.fasterxml.woodstox:woodstox-core` | `6.2.6` was vulnerable to CVE-2022-40152 after the Axis2 update. | Managed `woodstox-core` at `6.4.0`. | `6.4.0` is a fixed version and builds successfully. |
| `com.google.guava:guava` | `31.1-jre` was vulnerable to CVE-2020-8908 and CVE-2023-2976. | Managed Guava at `33.4.8-jre`. | The new version is beyond the fixed range and resolves through the Google Apps module. |
| `com.google.oauth-client:google-oauth-client` | `1.33.2` was vulnerable to CVE-2021-22573. | Managed `google-oauth-client` at `1.33.3`. | `1.33.3` is the fixed version reported by the scanner. |
| `com.google.protobuf:protobuf-java` | `4.26.1` was vulnerable to CVE-2024-7254. | Managed `protobuf-java` at `4.28.2`; standalone test plugin POMs now declare `4.28.2`. | `4.28.2` is in the fixed range. |
| `com.nimbusds:nimbus-jose-jwt` | `9.25.6` and `9.37` were vulnerable to CVE-2023-52428 and CVE-2025-53864. | Managed `nimbus-jose-jwt` at `9.37.4`; updated ext-auth OAuth SDK inheritance and standalone test plugin POMs. | `9.37.4` is the fixed 9.x line. |
| `commons-collections:commons-collections` | `3.2` was vulnerable to CVE-2015-6420 and CVE-2015-7501. | Added a direct `3.2.2` override in `apacheds-ldappc-schema`; parent already manages `3.2.2`. | `3.2.2` is the fixed version. |
| `commons-httpclient:commons-httpclient` | `3.1` is vulnerable to CVE-2012-5783. Trivy lists `4.0` as fixed. | No version change. | The `commons-httpclient:commons-httpclient` coordinate has no Maven-resolvable `4.0` release; Apache HttpComponents 4.x is a different API/coordinate, not a safe version-only remediation. |
| `commons-lang:commons-lang` | `2.1` and `2.6` are affected by CVE-2025-48924. | No version change. | The legacy `commons-lang:commons-lang` coordinate has no fixed version; the fixed library line is `org.apache.commons:commons-lang3`, which is a different API. |
| `dom4j:dom4j` | `1.6.1` is affected by CVE-2018-1000632 and CVE-2020-10683. | No version change. | No fixed version exists for the legacy `dom4j:dom4j` coordinate; fixed releases are on the newer `org.dom4j:dom4j` coordinate already used elsewhere. |
| `edu.vt.middleware:vt-ldap` | `3.3.4` was vulnerable to CVE-2014-3607. | Managed `vt-ldap` at `3.3.8`. | `3.3.8` is the fixed version. |
| `io.netty:netty-codec` | `4.1.72.Final` was vulnerable to CVE-2025-58057 and CVE-2026-42583. | Managed Netty at `4.1.135.Final`; standalone test plugin POMs now declare fixed Netty modules. | `4.1.135.Final` is beyond all reported fixed 4.1.x versions. |
| `io.netty:netty-codec-http` | `4.1.72.Final` had multiple HTTP request parsing/smuggling CVEs. | Managed and declared `4.1.135.Final` where needed. | `4.1.135.Final` clears the reported fixed ranges. |
| `io.netty:netty-common` | `4.1.72.Final` was vulnerable to CVE-2024-47535 and CVE-2025-25193. | Managed Netty at `4.1.135.Final`. | `4.1.135.Final` is fixed. |
| `io.netty:netty-handler` | `4.1.72.Final` had CVE-2023-34462 and 2026 handler advisories. | Managed Netty at `4.1.135.Final`. | `4.1.135.Final` is fixed. |
| `io.netty:netty-transport-native-epoll` | `4.1.72.Final` was vulnerable to CVE-2026-45536. | Managed and declared `4.1.135.Final` where needed. | `4.1.135.Final` is fixed. |
| `io.netty:netty-transport-native-kqueue` | `4.1.72.Final` was vulnerable to CVE-2026-45536. | Managed and declared `4.1.135.Final` where needed. | `4.1.135.Final` is fixed. |
| `net.sf.json-lib:json-lib` | `2.4` is affected by CVE-2024-47855. | No version change. | No fixed version exists for `net.sf.json-lib:json-lib`. |
| `org.apache.activemq:activemq-broker` | `5.19.2` had multiple 2026 ActiveMQ advisories. | Updated `grouperActivemq` to `5.19.7`. | `5.19.7` is in the fixed 5.x line. |
| `org.apache.activemq:activemq-client` | `5.19.2` was pulled by ActiveMQ and vulnerable to CVE-2026-33227 and CVE-2026-39304. | Updated ActiveMQ dependencies to `5.19.7`. | The client resolves from the fixed ActiveMQ version. |
| `org.apache.axis2:axis2-transport-http` | `1.6.4` was vulnerable to CVE-2012-5785. | Updated Axis2 dependencies to `1.8.0`. | `1.8.0` is the fixed version and the reactor still builds. |
| `org.apache.commons:commons-compress` | `1.25.0` was vulnerable to CVE-2024-25710 and CVE-2024-26308. | Updated the installer dependency to `1.26.0`. | `1.26.0` is fixed. |
| `org.apache.commons:commons-lang3` | `3.12.0` was vulnerable to CVE-2025-48924 in standalone test plugin POMs. | Updated those POMs to `3.18.0`; parent was already newer. | `3.18.0` is the fixed version. |
| `org.apache.james:apache-mime4j-core` | `0.7.2` was vulnerable to CVE-2024-21742. | Managed `apache-mime4j-core` at `0.8.10`. | `0.8.10` is fixed. |
| `org.apache.neethi:neethi` | `3.0.2` was vulnerable to CVE-2026-42402, CVE-2026-42403, and CVE-2026-42404. | Managed `neethi` at `3.2.2`. | `3.2.2` is fixed. |
| `org.apache.santuario:xmlsec` | `1.5.7`, `1.5.8`, and `3.0.2` were vulnerable to XML Security advisories. | Managed `xmlsec` at `3.0.3`. | `3.0.3` is fixed and the reactor builds. |
| `org.apache.velocity:velocity` | `1.7` is affected by CVE-2020-13936. | No version change. | No fixed version exists for `org.apache.velocity:velocity`; fixed Velocity releases use the different `velocity-engine-core` artifact/API. |
| `org.bitbucket.b_c:jose4j` | `0.9.3` was vulnerable to CVE-2023-51775 and CVE-2024-29371. | Updated `grouper-box` to use managed `0.9.6`. | `0.9.6` is fixed. |
| `org.bouncycastle:bcpkix-jdk15on` | `1.52` and `1.70` were reported vulnerable; scanner lists `1.79`/`1.84` as fixed. | Managed old `jdk15on` Bouncy Castle artifacts at `1.70`. | `1.70` is the newest Maven-resolvable version for this coordinate; the scanner's newer fixed versions are not available under `bcpkix-jdk15on`, so no fixed version exists for the same coordinate. |
| `org.bouncycastle:bcprov-jdk15on` | `1.51`, `1.52`, and `1.70` were reported vulnerable. | Managed old `jdk15on` Bouncy Castle artifacts at `1.70`. | `1.70` is the newest Maven-resolvable `bcprov-jdk15on`; fixed newer Bouncy Castle releases are on replacement coordinates, so no fixed same-coordinate version exists. |
| `org.hibernate:hibernate-core` | `5.6.10.Final` is affected by CVE-2026-0603. | No version change. | Trivy reports no fixed version for this Hibernate coordinate/version line. |
| `org.opensaml:opensaml` | `2.6.4` was vulnerable to CVE-2015-1796. | Updated `opensaml.version` to `2.6.5`. | `2.6.5` is the fixed version. |
| `org.owasp.esapi:esapi` | `2.0.1` had multiple ESAPI advisories. | Managed ESAPI at `2.6.0.0`. | `2.6.0.0` is in the fixed range. |
| `org.pac4j:pac4j-core` | `5.7.2` was vulnerable to CVE-2026-40458. | Updated ext-auth `pac4j.version` to `5.7.10`. | `5.7.10` is the fixed 5.x line. |
| `org.springframework:spring-beans` | `2.5.6.SEC02` was vulnerable to CVE-2022-22965 and CVE-2022-22970. | Managed Spring at `6.2.11`. | The version clears all reported Spring fixed ranges. |
| `org.springframework:spring-context` | `2.5.6.SEC02` and later `5.3.39` had Spring advisories. | Managed Spring at `6.2.11`. | `6.2.11` is beyond the reported fixed versions. |
| `org.springframework:spring-core` | `2.5.6.SEC02` and later `5.3.39` had Spring advisories. | Managed Spring at `6.2.11`. | `6.2.11` is fixed. |
| `org.springframework:spring-web` | `2.5.6.SEC02` and later `5.3.39` had Spring advisories. | Managed Spring at `6.2.11`. | `6.2.11` is fixed. |
| `software.amazon.ion:ion-java` | `1.0.2` was vulnerable to CVE-2024-21634. | Updated AWS SDK v1 modules from `1.12.267` to `1.12.793`. | The updated SDK resolution removes the vulnerable old Ion dependency from the final scan. |
| `xalan:xalan` | `2.7.1` was vulnerable to CVE-2014-0107 and CVE-2022-34169. | Managed `xalan` at `2.7.3`. | `2.7.3` is fixed. |
