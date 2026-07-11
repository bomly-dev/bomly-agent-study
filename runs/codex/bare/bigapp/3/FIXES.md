# Vulnerable Dependency Remediation

Audit source: resolved Maven dependency graph from `fixtures/bigapp/grouper-parent` checked against OSV.

## com.fasterxml.jackson.core:jackson-core

Found `2.18.2` affected by `GHSA-72hv-8253-57qq`. Updated Jackson version management to `2.18.9`, which is outside the affected `jackson-core` range.

## com.fasterxml.jackson.core:jackson-databind

Found `2.18.2` affected by `GHSA-5jmj-h7xm-6q6v`, `GHSA-hgj6-7826-r7m5`, `GHSA-j3rv-43j4-c7qm`, and `GHSA-rmj7-2vxq-3g9f`. Updated Jackson version management and WS Jackson modules to `2.18.9`, which fixes all but `GHSA-5jmj-h7xm-6q6v`. OSV lists no fixed version for `GHSA-5jmj-h7xm-6q6v` on the `com.fasterxml.jackson.core:jackson-databind` 2.x coordinate, so no complete version-only fix exists for that remaining advisory.

## com.google.guava:guava

Found `31.1-jre` affected by `GHSA-5mg8-w23w-74h3` and `GHSA-7g45-4rm6-3mm3`. Added dependency management for `33.5.0-jre`, removing the vulnerable resolved version.

## com.google.oauth-client:google-oauth-client

Found `1.33.2` affected by `GHSA-hw42-3568-wj87`. Added dependency management for `1.39.0`, removing the vulnerable resolved version.

## com.google.protobuf:protobuf-java

Found `4.26.1` affected by `GHSA-735f-pc8j-v9w8`. Added dependency management for `4.28.2`, removing the vulnerable resolved version.

## com.nimbusds:nimbus-jose-jwt

Found `9.37` affected by `GHSA-gvpg-vgmx-xg6w` and `GHSA-xwmg-2g98-w7v9`. Added dependency management for `9.37.4`, removing the vulnerable resolved version while staying compatible with `oauth2-oidc-sdk`.

## commons-httpclient:commons-httpclient

Found `3.1` affected by `GHSA-3832-9276-x7gf`. There is no fixed release for the retired `commons-httpclient` 3.x coordinate, so the installer module was migrated to the already-managed `org.apache.httpcomponents:httpclient` 4.x API and the unused helper tied to `HttpMethodBase` was removed.

## commons-lang:commons-lang

Found `2.6` affected by `GHSA-j288-q9x7-2f5v`. OSV lists `2.6` as the last affected version and no fixed version exists for the retired `commons-lang:commons-lang` coordinate. The application still uses the old `org.apache.commons.lang` API broadly, so this cannot be fixed by changing only a dependency version; remediation requires a source migration to `commons-lang3`.

## io.netty:netty-codec-http

Found `4.1.72.Final` affected by multiple Netty HTTP advisories including `GHSA-269q-hmxg-m83q`, `GHSA-38f8-5428-x5cv`, `GHSA-57rv-r2g8-2cj3`, `GHSA-5jpm-x58v-624v`, `GHSA-84h7-rjj3-6jx4`, `GHSA-f6hv-jmp6-3vwv`, `GHSA-fghv-69vj-qj49`, `GHSA-hvcg-qmg6-jm4c`, `GHSA-m4cv-j2px-7723`, `GHSA-pwqr-wmgm-9rr8`, `GHSA-v8h7-rr48-vmmv`, and `GHSA-xxqh-mfjm-7mv9`. Added Netty dependency management for `4.1.135.Final` and updated Qpid JMS to a compatible `1.11.0`, removing the vulnerable resolved version.

## io.netty:netty-codec

Found `4.1.72.Final` affected by `GHSA-3p8m-j85q-pgmj` and `GHSA-mj4r-2hfc-f8p6`. Added Netty dependency management for `4.1.135.Final`, removing the vulnerable resolved version.

## io.netty:netty-common

Found `4.1.72.Final` affected by `GHSA-389x-839f-4rhx` and `GHSA-xq3w-v528-46rv`. Added Netty dependency management for `4.1.135.Final`, removing the vulnerable resolved version.

## io.netty:netty-handler

Found `4.1.72.Final` affected by `GHSA-3qp7-7mw8-wx86`, `GHSA-6mjq-h674-j845`, `GHSA-c653-97m9-rcg9`, and `GHSA-x4gw-5cx5-pgmh`. Added Netty dependency management for `4.1.135.Final`, removing the vulnerable resolved version.

## org.apache.axis2:axis2-transport-http

Found `1.6.4` affected by `GHSA-wwq7-pxwc-p4rc`. Updated WS Axis2 transport and related Axis2 module pins to `1.8.2`, removing the vulnerable resolved version.

## org.apache.commons:commons-compress

Found `1.25.0` affected by `GHSA-4265-ccf5-phj5` and `GHSA-4g9r-vxhx-9pgx`. Updated the installer module to `1.28.0`, removing the vulnerable resolved version.

## org.apache.james:apache-mime4j-core

Found `0.7.2` affected by `GHSA-jw7r-rxff-gv24`. Added dependency management for `0.8.13`, removing the vulnerable transitive version from Axis2/Axiom.

## org.apache.neethi:neethi

Found `3.0.2` affected by `GHSA-287c-fxr7-3w6c`, `GHSA-2hfh-9h53-qc24`, and `GHSA-g36m-9g3m-2vmp`. Added dependency management for `3.2.2`, removing the vulnerable transitive version.

## org.bitbucket.b_c:jose4j

Found `0.9.3` affected by `GHSA-3677-xxcr-wjqv` and `GHSA-6qvw-249j-h44c`. Updated the Box module direct dependency to `0.9.6`, removing the vulnerable resolved version.

## org.bouncycastle:bcpkix-jdk15on

Found `1.52` affected by `GHSA-4cx2-fc23-5wg6` and `GHSA-wg6q-6289-32hp`. The `jdk15on` line is retired, so the Box SDK transitive was excluded and replaced with the maintained `bcpkix-jdk18on` artifact already managed at `1.84`.

## org.bouncycastle:bcprov-jdk15on

Found `1.52` affected by multiple Bouncy Castle advisories including `GHSA-2j2x-hx4g-2gf4`, `GHSA-4vhj-98r6-424h`, `GHSA-6xx3-rg99-gc3p`, `GHSA-72m5-fvvv-55m6`, `GHSA-8xfc-gm6g-vgpv`, `GHSA-9gp4-qrff-c648`, `GHSA-c8xf-m4ff-jcxj`, `GHSA-fjqm-246c-mwqg`, `GHSA-hr8g-6v94-x4m9`, `GHSA-qcj7-g2j5-g7r3`, `GHSA-r97x-3g8f-gx3m`, `GHSA-r9ch-m4fh-fc7q`, `GHSA-rrvx-pwf8-p59p`, `GHSA-v435-xc8x-wvr9`, `GHSA-w285-wf9q-5w69`, `GHSA-wjxj-5m7g-mg7q`, and `GHSA-xqj7-j8j5-f2xr`. The `jdk15on` line is retired, so WSS4J and Box SDK transitives were excluded and replaced with the maintained `bcprov-jdk18on` artifact already managed at `1.84`.

## org.hibernate:hibernate-core

Found `5.6.10.Final` affected by `GHSA-2p5w-cvg5-gc5c`. OSV marks the 5.6 line affected through `5.6.15`, and there is no `org.hibernate:hibernate-core:5.6.16.Final` artifact. The fixed Hibernate line uses the `org.hibernate.orm`/Hibernate 6 coordinate and Jakarta APIs, which is not a version-only replacement for this Javax-based application. No compatible fixed version exists for the current coordinate.

## software.amazon.ion:ion-java

Found `1.0.2` affected by `GHSA-264p-99wq-f4j6`. Updated AWS SDK modules to `1.12.792` and added Ion dependency management for `1.10.5`, removing the vulnerable resolved version.

## com.fasterxml.woodstox:woodstox-core

Found `6.2.8` introduced by the Axis2/Axiom upgrade and affected by `GHSA-3f7h-mf4q-vrm4`. Added dependency management for `6.4.0`, removing the vulnerable resolved version.
