# Vulnerability Remediation Record

Inventory source: resolved Maven reactor dependencies from `fixtures/bigapp/grouper-parent`, checked with OSV.

- `com.fasterxml.jackson.core:jackson-core` 2.18.2: OSV reported GHSA-72hv-8253-57qq. Updated the shared Jackson version to 2.18.8, which resolves `jackson-core` to a non-vulnerable version.
- `com.fasterxml.jackson.core:jackson-databind` 2.18.2: OSV reported GHSA-5jmj-h7xm-6q6v, GHSA-hgj6-7826-r7m5, GHSA-j3rv-43j4-c7qm, and GHSA-rmj7-2vxq-3g9f. Updated to 2.18.8, which fixes the advisories with fixed 2.x releases. GHSA-5jmj-h7xm-6q6v remains because OSV publishes no fixed `com.fasterxml.jackson.core:jackson-databind` 2.x version; the fixed line is the Jackson 3 `tools.jackson.core` artifact, which is not a version-only change for this app.
- `com.google.guava:guava` 31.1-jre: OSV reported GHSA-5mg8-w23w-74h3 and GHSA-7g45-4rm6-3mm3. Added parent dependency management for 32.1.3-jre, which resolves the vulnerable transitive version from the Google API client.
- `com.google.oauth-client:google-oauth-client` 1.33.2: OSV reported GHSA-hw42-3568-wj87. Added parent dependency management for 1.33.3, the fixed release.
- `com.google.protobuf:protobuf-java` 4.26.1: OSV reported GHSA-735f-pc8j-v9w8. Added parent dependency management for 4.28.2, a fixed release.
- `com.nimbusds:nimbus-jose-jwt` 9.37: OSV reported GHSA-gvpg-vgmx-xg6w and GHSA-xwmg-2g98-w7v9. Added parent dependency management for 9.37.4, the fixed 9.x release.
- `commons-httpclient:commons-httpclient` 3.1: OSV reported GHSA-3832-9276-x7gf. No fixed version exists for this discontinued artifact, so it was left unchanged.
- `commons-lang:commons-lang` 2.6: OSV reported GHSA-j288-q9x7-2f5v. No fixed `commons-lang:commons-lang` 2.x version exists; the fix is migrating code to `org.apache.commons:commons-lang3`, which is not a version-only dependency remediation.
- `io.netty:netty-codec` 4.1.72.Final: OSV reported GHSA-3p8m-j85q-pgmj and GHSA-mj4r-2hfc-f8p6. Added parent dependency management for 4.1.135.Final.
- `io.netty:netty-codec-http` 4.1.72.Final: OSV reported multiple HTTP parsing and request smuggling advisories. Added parent dependency management for 4.1.135.Final.
- `io.netty:netty-common` 4.1.72.Final: OSV reported GHSA-389x-839f-4rhx and GHSA-xq3w-v528-46rv. Added parent dependency management for 4.1.135.Final.
- `io.netty:netty-handler` 4.1.72.Final: OSV reported GHSA-3qp7-7mw8-wx86, GHSA-6mjq-h674-j845, GHSA-c653-97m9-rcg9, and GHSA-x4gw-5cx5-pgmh. Added parent dependency management for 4.1.135.Final.
- `io.netty:netty-transport-native-epoll` 4.1.72.Final: OSV reported GHSA-w573-9ffj-6ff9. Added classifier-specific parent dependency management for `linux-x86_64` at 4.1.135.Final.
- `io.netty:netty-transport-native-kqueue` 4.1.72.Final: OSV reported GHSA-w573-9ffj-6ff9. Added classifier-specific parent dependency management for `osx-x86_64` at 4.1.135.Final.
- `net.sf.json-lib:json-lib` 2.4: OSV reported GHSA-wwcp-26wc-3fxm. No fixed `net.sf.json-lib:json-lib` version exists; OSV points to the replacement `org.kordamp.json:json-lib-core`, which is not a version-only change for this app.
- `org.apache.axis2:axis2-transport-http` 1.6.4: OSV reported GHSA-wwq7-pxwc-p4rc. Updated Axis2 dependencies in the WS modules to 1.8.2, a fixed release.
- `org.apache.commons:commons-compress` 1.25.0: OSV reported GHSA-4265-ccf5-phj5 and GHSA-4g9r-vxhx-9pgx. Updated the installer dependency to 1.26.0, the fixed release.
- `org.apache.james:apache-mime4j-core` 0.7.2: OSV reported GHSA-jw7r-rxff-gv24. Added parent dependency management for 0.8.10, the fixed release.
- `org.apache.neethi:neethi` 3.0.2: OSV reported GHSA-287c-fxr7-3w6c, GHSA-2hfh-9h53-qc24, and GHSA-g36m-9g3m-2vmp. Added parent dependency management for 3.2.2, the fixed release.
- `org.bitbucket.b_c:jose4j` 0.9.3: OSV reported GHSA-3677-xxcr-wjqv and GHSA-6qvw-249j-h44c. Updated the direct Box module dependency to 0.9.6.
- `org.bouncycastle:bcpkix-jdk15on` 1.52: OSV reported GHSA-4cx2-fc23-5wg6 and GHSA-wg6q-6289-32hp. Excluded this vulnerable transitive from `box-java-sdk` and added the already-managed `bcpkix-jdk18on` dependency at 1.84.
- `org.bouncycastle:bcprov-jdk15on` 1.52: OSV reported multiple cryptographic advisories. Excluded this vulnerable transitive from `box-java-sdk` and added the already-managed `bcprov-jdk18on` dependency at 1.84.
- `org.hibernate:hibernate-core` 5.6.10.Final: OSV reported GHSA-2p5w-cvg5-gc5c. OSV publishes no fixed 5.x release; Hibernate 6 is a Jakarta/API migration for this app, not a safe version-only remediation, so this dependency was left unchanged.
- `software.amazon.ion:ion-java` 1.0.2: OSV reported GHSA-264p-99wq-f4j6. Updated AWS SDK 1.x dependencies from 1.12.267 to 1.12.797, which removes this vulnerable transitive from the resolved reactor graph.
