# Vulnerability Remediation Record

Inventory source: `bomly scan --path fixtures/bigapp/grouper-parent --enrich --audit`.

## com.fasterxml.jackson.core:jackson-core

Found `2.18.2` with GHSA-72hv-8253-57qq. Pinned `jackson-core` through parent dependency management at `2.18.9` using the existing Jackson version property. This is above the fixed `2.18.6` level and keeps Jackson artifacts aligned.

## com.fasterxml.jackson.core:jackson-databind

Found `2.18.2` with GHSA-5jmj-h7xm-6q6v, GHSA-hgj6-7826-r7m5, GHSA-j3rv-43j4-c7qm, and GHSA-rmj7-2vxq-3g9f. Updated the parent Jackson version property to `2.18.9`, which closes the advisories in the follow-up bomly scan and keeps `jackson-databind`, `jackson-core`, and `jackson-annotations` on the same patch level.

## com.google.guava:guava

Found transitive `31.1-jre` with GHSA-5mg8-w23w-74h3 and GHSA-7g45-4rm6-3mm3 via Google API client dependencies. Pinned `com.google.guava:guava` to `32.0.0-android` in parent dependency management because bomly identified that as the fixed version.

## com.google.oauth-client:google-oauth-client

Found transitive `1.33.2` with GHSA-hw42-3568-wj87. Pinned `com.google.oauth-client:google-oauth-client` to `1.33.3` in parent dependency management because bomly identified that as the fixed version.

## com.google.protobuf:protobuf-java

Found transitive `4.26.1` with GHSA-735f-pc8j-v9w8 via MySQL Connector/J. Pinned `com.google.protobuf:protobuf-java` to `4.27.5` in parent dependency management because bomly identified that as the fixed version.

## com.nimbusds:nimbus-jose-jwt

Found transitive `9.37` with GHSA-gvpg-vgmx-xg6w and GHSA-xwmg-2g98-w7v9. Pinned `com.nimbusds:nimbus-jose-jwt` to `9.37.4` in parent dependency management, covering the highest fixed version required by the advisories.

## commons-httpclient:commons-httpclient

Found `3.1` with GHSA-3832-9276-x7gf. No version change was made because bomly reports `Fix state: not-fixed` for the `3.x` coordinate, and Maven has no published `commons-httpclient:commons-httpclient:3.2`; replacing the library would require application code changes beyond a dependency-version remediation.

## commons-lang:commons-lang

Found `2.6` with GHSA-j288-q9x7-2f5v. No version change was made because bomly reports `Fix state: not-fixed` for `commons-lang`, and Maven has no published `commons-lang:commons-lang:2.7`; moving to `commons-lang3` would require source-level migration.

## io.netty:netty-codec

Found transitive `4.1.72.Final` with GHSA-3p8m-j85q-pgmj and GHSA-mj4r-2hfc-f8p6 through Qpid JMS. Pinned `io.netty:netty-codec` to `4.1.135.Final` in parent dependency management, covering the highest fixed Netty version required.

## io.netty:netty-codec-http

Found transitive `4.1.72.Final` with multiple Netty HTTP decoder advisories, including GHSA-hvcg-qmg6-jm4c. Pinned `io.netty:netty-codec-http` to `4.1.135.Final` in parent dependency management, covering the highest fixed Netty version required.

## io.netty:netty-common

Found transitive `4.1.72.Final` with GHSA-389x-839f-4rhx and GHSA-xq3w-v528-46rv through Qpid JMS. Pinned `io.netty:netty-common` to `4.1.135.Final` in parent dependency management, above the required fixed versions.

## io.netty:netty-handler

Found transitive `4.1.72.Final` with GHSA-3qp7-7mw8-wx86, GHSA-6mjq-h674-j845, GHSA-c653-97m9-rcg9, and GHSA-x4gw-5cx5-pgmh through Qpid JMS. Pinned `io.netty:netty-handler` to `4.1.135.Final` in parent dependency management because bomly identified that as the highest fixed version required.

## org.apache.axis2:axis2-transport-http

Found direct `1.6.4` with GHSA-wwq7-pxwc-p4rc in WS modules. Added a parent version property at `1.8.0` and changed explicit module versions to use it because bomly identified `1.8.0` as fixed.

## org.apache.commons:commons-compress

Found direct `1.25.0` with GHSA-4265-ccf5-phj5 and GHSA-4g9r-vxhx-9pgx in the installer module. Added a parent version property at `1.26.0` and changed the installer dependency to use it because bomly identified `1.26.0` as fixed.

## org.apache.james:apache-mime4j-core

Found transitive `0.7.2` with GHSA-jw7r-rxff-gv24 through Axis2/Axiom. Pinned `org.apache.james:apache-mime4j-core` to `0.8.10` in parent dependency management because bomly identified that as the fixed version.

## org.apache.neethi:neethi

Found transitive `3.0.2` with GHSA-287c-fxr7-3w6c, GHSA-2hfh-9h53-qc24, and GHSA-g36m-9g3m-2vmp through Axis2. Pinned `org.apache.neethi:neethi` to `3.2.2` in parent dependency management because bomly identified that as the fixed version.

## org.bitbucket.b_c:jose4j

Found direct `0.9.3` with GHSA-3677-xxcr-wjqv and GHSA-6qvw-249j-h44c in the Box module. Added a parent `jose4j.version` property at `0.9.6` and changed the Box module to use it because bomly identified `0.9.6` as the fixed version.

## org.bouncycastle:bcpkix-jdk15on

Found transitive `1.52` with GHSA-4cx2-fc23-5wg6 and GHSA-wg6q-6289-32hp through `box-java-sdk`. Excluded the discontinued `bcpkix-jdk15on` artifact from `box-java-sdk` and added `org.bouncycastle:bcpkix-jdk15to18` at `1.84`, because the fixed `jdk15on` versions bomly suggested are not published under the old coordinate and the maintained `jdk15to18` coordinate provides the same Bouncy Castle packages.

## org.bouncycastle:bcprov-jdk15on

Found transitive `1.52` with multiple Bouncy Castle advisories through `box-java-sdk`. Excluded the discontinued `bcprov-jdk15on` artifact from `box-java-sdk` and added `org.bouncycastle:bcprov-jdk15to18` at `1.84`, because patched versions such as `1.78` are not published under the old `jdk15on` coordinate and the maintained `jdk15to18` coordinate provides the same Bouncy Castle packages.

## org.hibernate:hibernate-core

Found `5.6.10.Final` with GHSA-2p5w-cvg5-gc5c. No version change was made because bomly reports `Fix state: not-fixed` for the 5.6 line and Maven has no published `org.hibernate:hibernate-core:5.6.16.Final`; changing major Hibernate lines would be an application migration, not a safe dependency-version remediation.

## software.amazon.ion:ion-java

Found transitive `1.0.2` with GHSA-264p-99wq-f4j6 through AWS SDK core. No version change was made because bomly reports `Fix state: not-fixed`, and the fixed-looking `1.10.5` coordinate is not published for `software.amazon.ion:ion-java`; tested newer-looking `1.11.x` coordinates are also unpublished in Maven.
