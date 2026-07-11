# Dependency Vulnerability Remediation — `fixtures/bigapp` (Grouper 4.x reactor)

Method: resolved the full reactor dependency tree with
`mvn dependency:tree` and scanned both the POMs and the resolved artifacts with
`trivy`. Findings were then mapped to the module/coordinate that actually pulls
them (direct declaration, parent property, or transitive) so each fix is applied
at the right place. After changes, `make test`
(`mvn -B -DskipTests install` over the 13-module reactor) **passes**, and a
re-run of `dependency:tree` confirms the intended versions now resolve.

Scope note: the reactor built by `make test` is the set of modules listed in
`grouper-parent/pom.xml` (grouperClient, grouper, grouperScim, grouper-ui,
grouper-ws → grouper-ws, grouper-installer, grouper-pspng, grouper-box,
grouper-duo, googleapps-grouper-provisioner, grouper-azure). Some POMs in the
tree (`grouper-shib`, `grouper-ext-auth`, `grouper-legacy-ui`, the
`grouper-ws-*-client`/`-test` modules, containers, `test-plugin`,
`apacheds-ldappc-schema`) are **not** part of that build. They are covered below
for completeness and flagged as non-built where relevant.

---

## A. Remediated — dependencies in the built reactor

| # | Package | Was | Now | CVEs | Where fixed |
|---|---------|-----|-----|------|-------------|
| 1 | com.fasterxml.jackson.core:jackson-databind | 2.18.2 | 2.18.8 | CVE-2026-54512, -54513, -54514, -54515 | parent property `jackson.databind` |
| 2 | com.fasterxml.jackson.core:jackson-core | 2.18.2 | 2.18.8 | GHSA-72hv-8253-57qq | follows databind (transitive) |
| 3 | jackson-jaxrs-base / jackson-jaxrs-json-provider / jackson-datatype-jsr310 | 2.18.2 | 2.18.8 | same jackson family | `grouper-ws/grouper-ws/pom.xml` (hard-coded) |
| 4 | com.google.protobuf:protobuf-java | 4.26.1 | 4.28.2 | CVE-2024-7254 | parent `dependencyManagement` |
| 5 | com.nimbusds:nimbus-jose-jwt | 9.37 (and 9.25.6) | 9.37.4 | CVE-2023-52428, CVE-2025-53864 | parent `dependencyManagement` |
| 6 | io.netty:netty-* (codec, codec-http, common, handler, transport-native-epoll/kqueue) | 4.1.72.Final | 4.1.135.Final | CVE-2022-24823, -2024-29025, -2023-34462, -2024-47535, -2025-25193, -2025-58056/58057, -2025-67735, -2026-33870, -2026-41417, -2026-42580/42581/42583/42584/42585/42587, -2026-44249, -2026-45416/45536, -2026-50010/50020 | parent `dependencyManagement` (import `netty-bom` 4.1.135.Final) |
| 7 | ion-java | software.amazon.ion:ion-java 1.0.2 | com.amazon.ion:ion-java 1.10.5 | CVE-2024-21634 | exclude old artifact from `aws-java-sdk-core` + add new coordinate in `grouper/pom.xml` (managed in parent) |
| 8 | org.apache.james:apache-mime4j-core | 0.7.2 | 0.8.11 | CVE-2024-21742 | parent `dependencyManagement` |
| 9 | org.apache.neethi:neethi | 3.0.2 | 3.2.2 | CVE-2026-42402, -42403, -42404 | parent `dependencyManagement` |
| 10 | com.google.guava:guava | 31.1-jre | 32.1.3-jre | CVE-2023-2976, CVE-2020-8908 | parent `dependencyManagement` |
| 11 | com.google.oauth-client:google-oauth-client | 1.33.2 | 1.34.1 | CVE-2021-22573 | parent `dependencyManagement` |
| 12 | org.bouncycastle:bcprov-jdk15on + bcpkix-jdk15on | 1.52 | excluded → bcprov/bcpkix-jdk18on 1.84 | 17 CVEs incl. CVE-2016-1000338..352, CVE-2018-1000180, CVE-2020-15522/26939, CVE-2023-33201/33202, CVE-2024-29857/30171 | exclude from `box-java-sdk` and use jdk18on 1.84 in `grouper-box/pom.xml` |
| 13 | org.bitbucket.b_c:jose4j | 0.9.3 | 0.9.6 | CVE-2023-51775, CVE-2024-29371 | `grouper-box/pom.xml` (hard-coded) |
| 14 | org.apache.commons:commons-compress | 1.25.0 | 1.27.1 | CVE-2024-25710, CVE-2024-26308 | `grouper-installer/pom.xml` (hard-coded) |
| 15 | org.opensaml:opensaml | 2.6.4 | 2.6.5 | CVE-2015-1796 | parent property `opensaml.version` |

### Notes on the bouncycastle fix (#12)
`com.box:box-java-sdk:2.17.0` transitively pulls the **discontinued**
`bcprov-jdk15on` / `bcpkix-jdk15on` at 1.52. The `jdk15on` line has no release
past 1.70 and several of its CVEs are only fixed in the `jdk18on` line, so a
version bump alone cannot remediate it. The old artifacts are therefore
**excluded** from `box-java-sdk` and replaced with `bcprov-jdk18on` /
`bcpkix-jdk18on` 1.84 (the version the rest of the reactor already uses via the
parent). Same `org.bouncycastle` package, so it is a drop-in replacement.

### Notes on the ion-java fix (#7)
`com.amazonaws:aws-java-sdk-core:1.12.267` pulls
`software.amazon.ion:ion-java:1.0.2`. CVE-2024-21634 is only fixed under the
**newer coordinate** `com.amazon.ion:ion-java` (the old
`software.amazon.ion:ion-java` line stops at 1.5.1 — 1.10.5 does not exist under
it). Both publish the identical `com.amazon.ion` Java package, so the old
artifact is excluded and `com.amazon.ion:ion-java:1.10.5` is added.

---

## B. Remediated — non-built module

| # | Package | Was | Now | CVEs | Where |
|---|---------|-----|-----|------|-------|
| 16 | org.apache.activemq:activemq-broker, activemq-jaas (+ transitive activemq-client) | 5.19.2 | 5.19.7 | CVE-2026-33227, -34197, -39304, -40466, -41043, -41044, -42588, -45505, -49270 | `grouper-misc/grouperActivemq/pom.xml` (hard-coded). Module is **not** in the `make test` reactor, but the versions were still bumped. |

---

## C. Identified but NOT fixed — no fixed version exists (left as-is, by design)

Per the task instructions, these are called out explicitly rather than guessed at.

| Package | Version | CVE(s) | Why not fixed |
|---------|---------|--------|---------------|
| commons-lang:commons-lang | 2.6 | CVE-2025-48924 | No fixed release in the legacy `commons-lang` 2.x line. The advisory is only resolved in `org.apache.commons:commons-lang3` **3.18.0** — a different artifact. `commons-lang` 2.6 here is a transitive legacy dependency; the reactor already ships `commons-lang3` 3.20.0 (not vulnerable). No drop-in version fix available. |
| net.sf.json-lib:json-lib | 2.4 | CVE-2024-47855 | No fixed release published for `net.sf.json-lib:json-lib`. The library is effectively unmaintained; there is no newer non-vulnerable version to move to. |
| org.hibernate:hibernate-core | 5.6.10.Final | CVE-2026-0603 | No fixed release exists in the Hibernate 5.x line; remediation would require a major upgrade to Hibernate 6.x/7.x, which is an API-breaking change well outside a version bump. Flagged, not changed. |
| commons-httpclient:commons-httpclient | 3.1 | CVE-2012-5783 | No fixed release in the legacy `commons-httpclient` 3.x line. The advisory's "fixed 4.0" refers to the successor artifact `org.apache.httpcomponents:httpclient` (already present in the reactor at 4.5.13) — an API-incompatible replacement, not a version bump. Present directly in `grouper-installer` and transitively in `grouper-ws`. |

---

## D. Identified but NOT auto-applied — fix exists but is a breaking major upgrade

| Package | Version | CVE | Fixed in | Why not applied |
|---------|---------|-----|----------|-----------------|
| org.apache.axis2:axis2-transport-http | 1.6.4 | CVE-2012-5785 (hostname verification, MEDIUM) | 1.8.0 | `grouper-ws` hard-codes the whole Axis2 SOAP stack on 1.6.x (`axis2-kernel`, `axis2-adb`, `axis2-transport-local`, `axis2-transport-http`). Moving only `axis2-transport-http` to 1.8.0 mixes incompatible Axis2 majors, and moving the entire stack to 1.8.0 is an API-breaking upgrade that does not compile against the current `grouper-ws` code. Left on 1.6.4 to keep the build green; flagged here for a follow-up dedicated Axis2 upgrade. |

---

## E. Non-built modules — ancient transitive stacks (flagged, not remediated)

These modules are **excluded from the `make test` reactor** (commented out in
`grouper-parent/pom.xml` or not referenced as reactor modules), so their
dependencies are not on the built application's classpath. They are recorded for
completeness; remediating them requires major framework upgrades, not version
bumps:

- **`grouper-misc/grouper-shib`** — depends on `shibboleth-common`/`opensaml`
  2.6.x, which drags in a large set of end-of-life libraries flagged by the
  scanner: `spring-*` 2.5.6.SEC02 (CVE-2022-22965 "Spring4Shell", CVE-2016-1000027,
  and many more), `org.apache.santuario:xmlsec` 1.5.7/1.5.8 (CVE-2021-40690),
  `org.apache.velocity:velocity` 1.7 (CVE-2020-13936, no fix),
  `xalan:xalan` 2.7.1 (CVE-2022-34169), `org.owasp.esapi:esapi` 2.0.1,
  `edu.vt.middleware:vt-ldap` 3.3.4, `ca.juliusdavies:not-yet-commons-ssl` 0.3.9,
  and `bcprov-jdk15on` 1.51. There is no version-bump remediation; it requires
  migrating off the OpenSAML 2 / Shibboleth 1.x stack.
- **`grouper-misc/grouper-ext-auth`** — `org.pac4j:pac4j-*` 5.7.2
  (CVE-2026-40458, fixed 5.7.10) and `spring-core` 5.3.24 (CVE-2025-41249,
  fixed 6.2.11 — a major upgrade). Not in the build.
- **`grouper-misc/test-plugin`** and the `grouper/src/test/.../testImplementation`
  sample — `commons-lang3` 3.12.0 (CVE-2025-48924, fixed 3.18.0). Standalone
  sample POMs, not in the build; the reactor itself uses 3.20.0.
- **`grouper-ws/grouper-ws-java-generated-client`** — `bcpkix-jdk15on` 1.70
  (CVE-2025-8916 etc.). Non-built client module.
</content>
</invoke>
