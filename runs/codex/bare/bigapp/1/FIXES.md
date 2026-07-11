# Dependency Vulnerability Remediation

Scan source: `trivy fs --scanners vuln fixtures/bigapp`.

- `ca.juliusdavies:not-yet-commons-ssl`: Trivy identified CVE-2014-3604 at 0.3.9 via `grouper-misc/grouper-shib`. Trivy listed 0.3.15 as fixed, but `ca.juliusdavies:not-yet-commons-ssl:0.3.15` is not available from Maven Central for this coordinate, so no version-only fix was applied.
- `com.amazon.ion:ion-java` / `software.amazon.ion:ion-java`: Trivy identified CVE-2024-21634 in `software.amazon.ion:ion-java` 1.0.2. The old `software.amazon.ion` coordinate has no 1.10.5 release in Maven Central, so `software.amazon.ion:ion-java` was excluded from AWS SDK dependencies and replaced with the fixed `com.amazon.ion:ion-java` 1.10.5 coordinate.
- `com.fasterxml.jackson.core:jackson-core`: Trivy identified GHSA-72hv-8253-57qq at 2.18.2. Updated the shared Jackson version to 2.18.9 and added parent and standalone test-plugin dependency-management overrides so transitive Jackson core resolves to the fixed line.
- `com.fasterxml.jackson.core:jackson-databind`: Trivy identified CVE-2026-54512, CVE-2026-54513, CVE-2026-54514, and CVE-2026-54515 at 2.18.2. Updated the shared Jackson version to 2.18.9 and aligned directly pinned WS Jackson artifacts to that property.
- `com.fasterxml.woodstox:woodstox-core`: Trivy identified CVE-2022-40152 at 6.2.6. Added parent dependency management for 6.4.0.
- `com.google.guava:guava`: Trivy identified CVE-2020-8908 and CVE-2023-2976 at 31.1-jre. Added parent dependency management for 32.1.3-jre.
- `com.google.oauth-client:google-oauth-client`: Trivy identified CVE-2021-22573 at 1.33.2. Added parent dependency management for 1.33.3.
- `com.google.protobuf:protobuf-java`: Trivy identified CVE-2024-7254 at 4.26.1. Added parent and standalone test-plugin dependency management for 4.28.2.
- `com.nimbusds:nimbus-jose-jwt`: Trivy identified CVE-2023-52428 and CVE-2025-53864 at 9.25.6/9.37. Added parent and standalone test-plugin dependency management for 9.37.4.
- `commons-collections:commons-collections`: Trivy identified CVE-2015-6420 and CVE-2015-7501 at 3.2. Added a direct 3.2.2 override in `apacheds-ldappc-schema`; the parent was already managing 3.2.2.
- `commons-httpclient:commons-httpclient`: Trivy identified CVE-2012-5783 at 3.1 and listed 4.0 as fixed. `commons-httpclient:commons-httpclient:4.0` is not available in Maven Central because HttpClient 4.x uses a different coordinate, so no version-only fix exists for this package.
- `commons-lang:commons-lang`: Trivy identified CVE-2025-48924 at 2.1 and 2.6. Trivy reports this coordinate as affected with no fixed version, so no version-only fix exists.
- `dom4j:dom4j`: Trivy identified CVE-2018-1000632 and CVE-2020-10683 at 1.6.1 via legacy Shibboleth dependencies. Trivy reports this coordinate as affected with no fixed version; the maintained artifact is a different coordinate already used elsewhere in the parent, so no version-only fix exists for `dom4j:dom4j`.
- `edu.vt.middleware:vt-ldap`: Trivy identified CVE-2014-3607 at 3.3.4. Added parent dependency management for 3.3.8.
- `io.netty:netty-codec`: Trivy identified CVE-2025-58057 and CVE-2026-42583 at 4.1.72.Final. Added parent and standalone test-plugin dependency management for 4.1.135.Final.
- `io.netty:netty-codec-http`: Trivy identified multiple HTTP parsing/request-smuggling CVEs at 4.1.72.Final. Added parent and standalone test-plugin dependency management for 4.1.135.Final.
- `io.netty:netty-common`: Trivy identified CVE-2024-47535 and CVE-2025-25193 at 4.1.72.Final. Added parent and standalone test-plugin dependency management for 4.1.135.Final.
- `io.netty:netty-handler`: Trivy identified CVE-2023-34462, CVE-2026-44249, CVE-2026-45416, and CVE-2026-50010 at 4.1.72.Final. Added parent and standalone test-plugin dependency management for 4.1.135.Final.
- `io.netty:netty-transport-native-epoll`: Trivy identified CVE-2026-45536 at 4.1.72.Final. Added parent and standalone test-plugin dependency management for 4.1.135.Final.
- `io.netty:netty-transport-native-kqueue`: Trivy identified CVE-2026-45536 at 4.1.72.Final. Added parent and standalone test-plugin dependency management for 4.1.135.Final.
- `net.sf.json-lib:json-lib`: Trivy identified CVE-2024-47855 at 2.4. Trivy reports this coordinate as affected with no fixed version, so no version-only fix exists.
- `org.apache.activemq:activemq-broker`: Trivy identified multiple CVEs at 5.19.2. Updated `grouperActivemq` to 5.19.7.
- `org.apache.activemq:activemq-client`: Trivy identified CVE-2026-33227 and CVE-2026-39304 at 5.19.2 transitively from ActiveMQ. Updating `grouperActivemq` to 5.19.7 remediates the transitive client version.
- `org.apache.axis2:axis2-transport-http`: Trivy identified CVE-2012-5785 at 1.6.4. Added parent dependency management for Axis2 1.8.0 and changed direct WS Axis2 pins to use that property.
- `org.apache.commons:commons-compress`: Trivy identified CVE-2024-25710 and CVE-2024-26308 at 1.25.0. Updated `grouper-installer` to 1.26.0.
- `org.apache.commons:commons-lang3`: Trivy identified CVE-2025-48924 at 3.12.0 in standalone test-plugin POMs. Updated those direct pins to 3.20.0; the parent was already managing 3.20.0.
- `org.apache.james:apache-mime4j-core`: Trivy identified CVE-2024-21742 at 0.7.2. Added parent dependency management for 0.8.10.
- `org.apache.neethi:neethi`: Trivy identified CVE-2026-42402, CVE-2026-42403, and CVE-2026-42404 at 3.0.2. Added parent dependency management for 3.2.2.
- `org.apache.santuario:xmlsec`: Trivy identified CVE-2021-40690 and CVE-2023-44483 at 1.5.7/1.5.8/3.0.2. Added parent dependency management for 3.0.3.
- `org.apache.velocity:velocity`: Trivy identified CVE-2020-13936 at 1.7 via legacy Shibboleth dependencies. Trivy reports this coordinate as affected with no fixed version, so no version-only fix exists.
- `org.bitbucket.b_c:jose4j`: Trivy identified CVE-2023-51775 and CVE-2024-29371 at 0.9.3. Updated `grouper-box` to 0.9.6.
- `org.bouncycastle:bcpkix-jdk15on`: Trivy identified CVE-2025-8916 and CVE-2026-5588 at 1.52/1.70. Raised old transitive usages to 1.70, the highest published `bcpkix-jdk15on` version; Trivy's listed fixed versions 1.79 and 1.84 do not exist on this coordinate, so full version-only remediation is not available.
- `org.bouncycastle:bcprov-jdk15on`: Trivy identified older fixed CVEs plus CVE-2023-33201 and 2024 CVEs at 1.51/1.52/1.70. Raised old transitive usages to 1.70, the highest published `bcprov-jdk15on` version; Trivy's listed 1.78 fixed version does not exist on this coordinate and CVE-2023-33201 has no fixed version listed, so full version-only remediation is not available.
- `org.hibernate:hibernate-core`: Trivy identified CVE-2026-0603 at 5.6.10.Final. Trivy reports this coordinate as affected with no fixed version, so no version-only fix exists.
- `org.opensaml:opensaml`: Trivy identified CVE-2015-1796 at 2.6.4. Updated the parent `opensaml.version` to 2.6.5.
- `org.owasp.esapi:esapi`: Trivy identified CVE-2013-5679, CVE-2013-5960, CVE-2022-23457, CVE-2022-24891, GHSA-7c2q-5qmr-v76q, and GHSA-r68h-jhhj-9jvm at 2.0.1. Added parent dependency management for 2.6.0.0.
- `org.pac4j:pac4j-core`: Trivy identified CVE-2026-40458 at 5.7.2. Updated `grouper-ext-auth` to pac4j 5.7.10.
- `org.springframework:spring-beans`: Trivy identified CVE-2022-22965 and CVE-2022-22970 at 2.5.6.SEC02. Added parent dependency management for Spring 6.2.11.
- `org.springframework:spring-context`: Trivy identified CVE-2022-22968, CVE-2024-38820, and CVE-2025-22233 at 2.5.6.SEC02. Added parent dependency management for Spring 6.2.11.
- `org.springframework:spring-core`: Trivy identified multiple CVEs at 2.5.6.SEC02 and CVE-2025-41249 at 5.3.24. Added parent dependency management for Spring 6.2.11.
- `org.springframework:spring-web`: Trivy identified multiple CVEs at 2.5.6.SEC02. Added parent dependency management for Spring 6.2.11.
- `xalan:xalan`: Trivy identified CVE-2014-0107 and CVE-2022-34169 at 2.7.1. Added parent dependency management for 2.7.3.

Validation:

- `make test` at the repository root completed successfully after remediation.
