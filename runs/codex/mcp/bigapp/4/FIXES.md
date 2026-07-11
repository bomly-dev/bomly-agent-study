# Dependency Vulnerability Remediation

Scan target: `fixtures/bigapp/grouper-parent` with `bomly scan --enrich --audit`.

## com.fasterxml.jackson.core:jackson-core

Found `2.18.2` via Jackson dependencies with GHSA-72hv-8253-57qq. Updated the shared Jackson version in `fixtures/bigapp/grouper-parent/pom.xml` to `2.18.8` and added `jackson-core` to dependency management so transitives resolve to the patched line. This is above the bomly fixed version, `2.18.6`.

## com.fasterxml.jackson.core:jackson-databind

Found `2.18.2` with GHSA-5jmj-h7xm-6q6v, GHSA-hgj6-7826-r7m5, GHSA-j3rv-43j4-c7qm, and GHSA-rmj7-2vxq-3g9f. Updated the shared Jackson version in `fixtures/bigapp/grouper-parent/pom.xml` to `2.18.8`, which remediates the fix-available advisories. Bomly still reports GHSA-5jmj-h7xm-6q6v against `2.18.8` as `no_fix_upstream`, so there is no fixed version to select for that advisory.

## com.google.guava:guava

Found `31.1-jre` via `google-api-client` with GHSA-5mg8-w23w-74h3 and GHSA-7g45-4rm6-3mm3. Added dependency management in `fixtures/bigapp/grouper-parent/pom.xml` to pin `guava` to `32.0.0-jre`, the patched JRE artifact corresponding to bomly's fixed `32.0.0` line.

## com.google.oauth-client:google-oauth-client

Found `1.33.2` via `google-api-client` with GHSA-hw42-3568-wj87. Added dependency management in `fixtures/bigapp/grouper-parent/pom.xml` to pin `google-oauth-client` to `1.33.3`, the bomly fixed version.

## com.google.protobuf:protobuf-java

Found `4.26.1` via `mysql-connector-j` with GHSA-735f-pc8j-v9w8. Added dependency management in `fixtures/bigapp/grouper-parent/pom.xml` to pin `protobuf-java` to `4.27.5`, the bomly fixed version.

## com.nimbusds:nimbus-jose-jwt

Found `9.37` via `oauth2-oidc-sdk` with GHSA-gvpg-vgmx-xg6w and GHSA-xwmg-2g98-w7v9. Added dependency management in `fixtures/bigapp/grouper-parent/pom.xml` to pin `nimbus-jose-jwt` to `9.37.4`, the bomly fixed version for both advisories.

## commons-httpclient:commons-httpclient

Found `3.1` via `grouper-installer` with GHSA-3832-9276-x7gf. Bomly reports this as `no_fix_upstream`; the affected range is the old 3.x artifact line and there is no fixed version to select. No version change was made.

## commons-lang:commons-lang

Found `2.6` with GHSA-j288-q9x7-2f5v. Bomly reports this as `no_fix_upstream` for the legacy `commons-lang` 2.x artifact. No version change was made because remediation would require replacing API usage with `commons-lang3`, not selecting a fixed 2.x version.

## io.netty:netty-codec

Found `4.1.72.Final` via `qpid-jms-client` with GHSA-3p8m-j85q-pgmj and GHSA-mj4r-2hfc-f8p6. Added dependency management in `fixtures/bigapp/grouper-parent/pom.xml` to pin Netty modules to `4.1.135.Final`, above the bomly fixed versions.

## io.netty:netty-codec-http

Found `4.1.72.Final` via `qpid-jms-client` with multiple HTTP parsing and DoS advisories, including GHSA-57rv-r2g8-2cj3, GHSA-f6hv-jmp6-3vwv, and GHSA-pwqr-wmgm-9rr8. Added dependency management in `fixtures/bigapp/grouper-parent/pom.xml` to pin Netty modules to `4.1.135.Final`, the highest fixed version bomly required for the reported Netty set.

## io.netty:netty-common

Found `4.1.72.Final` via `qpid-jms-client` with GHSA-389x-839f-4rhx and GHSA-xq3w-v528-46rv. Added dependency management in `fixtures/bigapp/grouper-parent/pom.xml` to pin Netty modules to `4.1.135.Final`.

## io.netty:netty-handler

Found `4.1.72.Final` via `qpid-jms-client` with GHSA-3qp7-7mw8-wx86, GHSA-6mjq-h674-j845, GHSA-c653-97m9-rcg9, and GHSA-x4gw-5cx5-pgmh. Added dependency management in `fixtures/bigapp/grouper-parent/pom.xml` to pin Netty modules to `4.1.135.Final`, the bomly fixed version.

## org.apache.axis2:axis2-transport-http

Found `1.6.4` with GHSA-wwq7-pxwc-p4rc. Updated `fixtures/bigapp/grouper-ws/grouper-ws/pom.xml` to `1.8.0`, the bomly fixed version.

## org.apache.commons:commons-compress

Found `1.25.0` in `grouper-installer` with GHSA-4265-ccf5-phj5 and GHSA-4g9r-vxhx-9pgx. Updated `fixtures/bigapp/grouper-misc/grouper-installer/pom.xml` to `1.26.0`, the bomly fixed version.

## org.apache.james:apache-mime4j-core

Found `0.7.2` via Axis/Axiom with GHSA-jw7r-rxff-gv24. Added dependency management in `fixtures/bigapp/grouper-parent/pom.xml` to pin `apache-mime4j-core` to `0.8.10`, the bomly fixed version.

## org.apache.neethi:neethi

Found `3.0.2` via Axis2 with GHSA-287c-fxr7-3w6c, GHSA-2hfh-9h53-qc24, and GHSA-g36m-9g3m-2vmp. Added dependency management in `fixtures/bigapp/grouper-parent/pom.xml` to pin `neethi` to `3.2.2`, the bomly fixed version.

## org.bitbucket.b_c:jose4j

Found `0.9.3` in `grouper-box` with GHSA-3677-xxcr-wjqv and GHSA-6qvw-249j-h44c. Updated `fixtures/bigapp/grouper-misc/grouper-box/pom.xml` to `0.9.6`, the bomly fixed version.

## org.bouncycastle:bcpkix-jdk15on

Found `1.52` via `box-java-sdk` with GHSA-4cx2-fc23-5wg6 and GHSA-wg6q-6289-32hp. The `jdk15on` artifact line only publishes through `1.70`, below the fixed `1.84` line for the reported advisories, so I excluded `bcpkix-jdk15on` from `box-java-sdk` and added the already managed `bcpkix-jdk18on` dependency at `1.84`.

## org.bouncycastle:bcprov-jdk15on

Found `1.52` via `box-java-sdk` with multiple Bouncy Castle advisories, including GHSA-2j2x-hx4g-2gf4, GHSA-rrvx-pwf8-p59p, GHSA-w285-wf9q-5w69, and GHSA-xqj7-j8j5-f2xr. Excluded `bcprov-jdk15on` from `box-java-sdk` and added the already managed `bcprov-jdk18on` dependency at `1.84`, because the old `jdk15on` artifact line has no release high enough for the latest fixed versions.

## org.hibernate:hibernate-core

Found `5.6.10.Final` with GHSA-2p5w-cvg5-gc5c. Bomly reports this as `no_fix_upstream` for the current artifact line. No version change was made because the available 5.6.x line remains in the affected range, and moving to Hibernate 6 would be a larger API migration rather than a safe version-only remediation.

## software.amazon.ion:ion-java

Found `1.0.2` via `aws-java-sdk-core` with GHSA-264p-99wq-f4j6. Bomly reports this as `no_fix_upstream`. Maven Central only publishes `software.amazon.ion:ion-java` through `1.5.1`, below the advisory's unaffected range, so there is no fixed version to select. No version change was made.
