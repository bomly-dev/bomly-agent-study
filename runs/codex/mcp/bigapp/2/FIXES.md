# Dependency Vulnerability Remediation

Scan target: `fixtures/bigapp/grouper-parent` with `bomly scan --enrich --audit`.

- `com.fasterxml.jackson.core:jackson-core`
  - Found: `2.18.2` was vulnerable to GHSA-72hv-8253-57qq.
  - Action: managed Jackson artifacts at `2.18.8` in `fixtures/bigapp/grouper-parent/pom.xml` and changed hardcoded Grouper WS Jackson versions to `${jackson.databind}`.
  - Why: `2.18.8` is above the fixed version bomly reported for the vulnerable Jackson core line.

- `com.fasterxml.jackson.core:jackson-databind`
  - Found: `2.18.2` was vulnerable to GHSA-j3rv-43j4-c7qm, GHSA-rmj7-2vxq-3g9f, GHSA-hgj6-7826-r7m5, and GHSA-5jmj-h7xm-6q6v.
  - Action: upgraded the managed Jackson version to `2.18.8`.
  - Why: `2.18.8` fixes the first three advisories. Bomly reports no fixed version released for GHSA-5jmj-h7xm-6q6v, so that advisory remains explicitly unfixed upstream.

- `com.google.guava:guava`
  - Found: `31.1-jre` was vulnerable to GHSA-7g45-4rm6-3mm3 and GHSA-5mg8-w23w-74h3.
  - Action: pinned `com.google.guava:guava` to `32.0.0-android` in parent dependency management.
  - Why: bomly reported `32.0.0-android` as the fixed version.

- `com.google.oauth-client:google-oauth-client`
  - Found: `1.33.2` was vulnerable to GHSA-hw42-3568-wj87.
  - Action: pinned `com.google.oauth-client:google-oauth-client` to `1.33.3` in parent dependency management.
  - Why: bomly reported `1.33.3` as the fixed version.

- `com.google.protobuf:protobuf-java`
  - Found: `4.26.1` was vulnerable to GHSA-735f-pc8j-v9w8.
  - Action: pinned `com.google.protobuf:protobuf-java` to `4.27.5` in parent dependency management.
  - Why: bomly reported `4.27.5` as the fixed version.

- `com.nimbusds:nimbus-jose-jwt`
  - Found: `9.37` was vulnerable to GHSA-gvpg-vgmx-xg6w and GHSA-xwmg-2g98-w7v9.
  - Action: pinned `com.nimbusds:nimbus-jose-jwt` to `9.37.4` in parent dependency management.
  - Why: `9.37.4` covers both fixed-version requirements reported by bomly.

- `commons-httpclient:commons-httpclient`
  - Found: `3.1` was vulnerable to GHSA-3832-9276-x7gf.
  - Action: no version change.
  - Why: bomly reports no fixed version released for this package line. The remaining dependency paths come through `grouper-installer` and Axis2.

- `commons-lang:commons-lang`
  - Found: `2.6` was vulnerable to GHSA-j288-q9x7-2f5v.
  - Action: no version change.
  - Why: bomly reports no fixed version released for `commons-lang:commons-lang`.

- `io.netty:netty-codec-http`
  - Found: `4.1.72.Final` was vulnerable to multiple Netty HTTP codec advisories, including GHSA-57rv-r2g8-2cj3, GHSA-f6hv-jmp6-3vwv, and GHSA-pwqr-wmgm-9rr8.
  - Action: pinned `io.netty:netty-codec-http` to `4.1.135.Final` in parent dependency management.
  - Why: `4.1.135.Final` is above the highest fixed version needed for the reported advisories.

- `io.netty:netty-codec`
  - Found: `4.1.72.Final` was vulnerable to GHSA-mj4r-2hfc-f8p6 and GHSA-3p8m-j85q-pgmj.
  - Action: pinned `io.netty:netty-codec` to `4.1.135.Final` in parent dependency management.
  - Why: `4.1.135.Final` is above the fixed versions reported by bomly.

- `io.netty:netty-common`
  - Found: `4.1.72.Final` was vulnerable to GHSA-389x-839f-4rhx and GHSA-xq3w-v528-46rv.
  - Action: pinned `io.netty:netty-common` to `4.1.135.Final` in parent dependency management.
  - Why: `4.1.135.Final` is above the fixed versions reported by bomly.

- `io.netty:netty-handler`
  - Found: `4.1.72.Final` was vulnerable to GHSA-3qp7-7mw8-wx86, GHSA-c653-97m9-rcg9, GHSA-x4gw-5cx5-pgmh, and GHSA-6mjq-h674-j845.
  - Action: pinned `io.netty:netty-handler` to `4.1.135.Final` in parent dependency management.
  - Why: `4.1.135.Final` covers the highest fixed version bomly reported.

- `org.apache.axis2:axis2-transport-http`
  - Found: `1.6.4` was vulnerable to GHSA-wwq7-pxwc-p4rc.
  - Action: added `${axis2.transport.http.version}` at `1.8.0`, managed it in the parent POM, and changed direct declarations in Grouper WS POMs to that property.
  - Why: bomly reported `1.8.0` as the fixed version, and direct dependency versions are not overridden by dependency management.

- `org.apache.commons:commons-compress`
  - Found: `1.25.0` was vulnerable to GHSA-4265-ccf5-phj5 and GHSA-4g9r-vxhx-9pgx.
  - Action: changed the installer dependency to `${commons.compress.version}` and set that property to `1.26.0`.
  - Why: bomly reported `1.26.0` as the fixed version.

- `org.apache.james:apache-mime4j-core`
  - Found: `0.7.2` was vulnerable to GHSA-jw7r-rxff-gv24.
  - Action: pinned `org.apache.james:apache-mime4j-core` to `0.8.10` in parent dependency management.
  - Why: bomly reported `0.8.10` as the fixed version.

- `org.apache.neethi:neethi`
  - Found: `3.0.2` was vulnerable to GHSA-2hfh-9h53-qc24, GHSA-g36m-9g3m-2vmp, and GHSA-287c-fxr7-3w6c.
  - Action: pinned `org.apache.neethi:neethi` to `3.2.2` in parent dependency management.
  - Why: bomly reported `3.2.2` as the fixed version.

- `org.bitbucket.b_c:jose4j`
  - Found: `0.9.3` was vulnerable to GHSA-3677-xxcr-wjqv and GHSA-6qvw-249j-h44c.
  - Action: changed the Grouper Box direct dependency to `${jose4j.version}` and set that property to `0.9.6`.
  - Why: `0.9.6` covers both fixed-version requirements reported by bomly.

- `org.bouncycastle:bcpkix-jdk15on`
  - Found: `1.52` was vulnerable to GHSA-4cx2-fc23-5wg6 and GHSA-wg6q-6289-32hp.
  - Action: excluded `bcpkix-jdk15on` from `box-java-sdk` and added `org.bouncycastle:bcpkix-jdk18on` as a direct Grouper Box dependency, using the existing managed `1.84` version.
  - Why: bomly's same-artifact target version for the old `jdk15on` line is not resolvable from Maven Central; replacing it with the modern `jdk18on` artifact removes the vulnerable package and keeps the build passing.

- `org.bouncycastle:bcprov-jdk15on`
  - Found: `1.52` was vulnerable to multiple Bouncy Castle advisories, including GHSA-2j2x-hx4g-2gf4, GHSA-4vhj-98r6-424h, GHSA-8xfc-gm6g-vgpv, and GHSA-v435-xc8x-wvr9.
  - Action: excluded `bcprov-jdk15on` from `box-java-sdk` and added `org.bouncycastle:bcprov-jdk18on` as a direct Grouper Box dependency, using the existing managed `1.84` version.
  - Why: bomly reported some fixed advisories on the old artifact line but also reported no fixed version for GHSA-hr8g-6v94-x4m9 and GHSA-wjxj-5m7g-mg7q; replacing the obsolete artifact removes the vulnerable package from the resolved graph.

- `org.hibernate:hibernate-core`
  - Found: `5.6.10.Final` was vulnerable to GHSA-2p5w-cvg5-gc5c.
  - Action: no version change.
  - Why: bomly reports no fixed version released for this Hibernate advisory.

- `software.amazon.ion:ion-java`
  - Found: `1.0.2` was vulnerable to GHSA-264p-99wq-f4j6.
  - Action: no version change.
  - Why: bomly reports no fixed version released for this Ion Java advisory.

Verification:

- `make test` completed successfully.
- Post-remediation bomly scan reports five vulnerable package/version pairs remaining: `com.fasterxml.jackson.core:jackson-databind@2.18.8`, `commons-httpclient:commons-httpclient@3.1`, `commons-lang:commons-lang@2.6`, `org.hibernate:hibernate-core@5.6.10.Final`, and `software.amazon.ion:ion-java@1.0.2`; each remaining vulnerability is classified by bomly as `no_fix_upstream`.
