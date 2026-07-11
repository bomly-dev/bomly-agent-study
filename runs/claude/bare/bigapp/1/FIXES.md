# Dependency vulnerability remediation

Application under audit: `fixtures/bigapp` (Internet2 Grouper, 13-module Maven
reactor).

## How vulnerabilities were identified

There is no built-in audit command for this ecosystem, so I scanned every
`pom.xml` with **Trivy** (`trivy fs --scanners vuln`), which resolves the full
Maven dependency graph (direct + transitive) and matches it against its
vulnerability database. Findings were then triaged by hand: I located the
declaration point of each artifact (direct declaration vs. transitive), chose
the nearest compile-compatible fixed version, and confirmed each replacement
version actually exists on Maven Central before applying it.

## Build status

`make test` (`mvn -B -DskipTests install` on `grouper-parent`) **passes** after
these changes. Note the reactor (`grouper-parent/pom.xml` `<modules>`) builds
these modules only: `grouperClient`, `grouper`, `grouperScim`, `grouper-ui`,
`grouper-ws`, `grouper-installer`, `grouper-pspng`, `grouper-box`,
`grouper-duo`, `googleapps-grouper-provisioner`, `grouper-azure`.
`grouper-shib` and `grouper-ext-auth` are **commented out** of the reactor, and
several other poms (`apacheds-ldappc-schema`, `grouperActivemq`,
`grouper-ws-*-client`, `grouper-ws-test`, `test-plugin`, `grouper-legacy-ui`)
are not reachable from it. Fixes to those modules are still applied for
completeness but are *not* exercised by `make test`; this is called out per
entry.

Where the fix is central, versions are forced via `dependencyManagement` in
`grouper-parent/pom.xml` (a new "SECURITY REMEDIATION" block) so a single edit
covers every module that pulls the artifact transitively.

---

## Fixed — reactor modules (verified by `make test`)

### Central pins in `grouper-parent/pom.xml`

| Package | From | To | CVE(s) | Notes |
|---|---|---|---|---|
| com.fasterxml.jackson.core:jackson-databind | 2.18.2 | 2.18.9 | CVE-2026-54512/54513/54514/54515 | bumped `${jackson.databind}`; stays on 2.18.x |
| com.fasterxml.jackson.core:jackson-core | 2.18.2 | 2.18.9 | GHSA-72hv-8253-57qq | pinned to `${jackson.databind}` |
| io.netty:netty-* (codec, codec-http, common, handler, transport-native-epoll/kqueue) | 4.1.72.Final | 4.1.135.Final | CVE-2024-47535, CVE-2025-25193, CVE-2023-34462, CVE-2024-29025, CVE-2022-24823 + 2025/2026 codec/http/handler advisories | pinned via `netty-bom` import |
| com.google.guava:guava | 31.1-jre | 32.1.3-jre | CVE-2023-2976, CVE-2020-8908 | |
| com.google.oauth-client:google-oauth-client | 1.33.2 | 1.34.1 | CVE-2021-22573 | |
| com.google.protobuf:protobuf-java | 4.26.1 | 4.28.2 | CVE-2024-7254 | |
| com.nimbusds:nimbus-jose-jwt | 9.37 / 9.25.6 | 9.37.4 | CVE-2023-52428, CVE-2025-53864 | |
| xalan:xalan (+ serializer) | 2.7.1 | 2.7.3 | CVE-2014-0107, CVE-2022-34169 | transitive; pulled via exclusions in grouper/grouper-ui |
| org.apache.james:apache-mime4j-core | 0.7.2 | 0.8.10 | CVE-2024-21742 | transitive via axis2 |
| org.apache.neethi:neethi | 3.0.2 | 3.2.2 | CVE-2026-42402/42403/42404 | transitive via axis2 |
| org.bouncycastle:bcprov-jdk15on | 1.51/1.52 | 1.70 | CVE-2016-1000338…346, CVE-2018-1000180, CVE-2020-15522, CVE-2020-26939 | 1.70 is the last jdk15on release; see "partially fixed" below |
| org.bouncycastle:bcpkix-jdk15on | 1.52 | 1.70 | (aligns with bcprov jdk15on line) | |
| org.opensaml:opensaml | 2.6.4 | 2.6.5 | CVE-2015-1796 | bumped `${opensaml.version}`; 2.6.5 is the last 2.x |

### ion-java — groupId relocation (CVE-2024-21634)

`aws-java-sdk-core:1.12.267` pulls `software.amazon.ion:ion-java:1.0.2`. The
patched release (1.10.5) is **only** published under the relocated coordinates
`com.amazon.ion:ion-java`; the old `software.amazon.ion:ion-java` line stops at
1.5.1 and was never patched. A plain version bump is therefore impossible.
Remediation in `grouper-parent/pom.xml`:
- Excluded `software.amazon.ion:ion-java` from all four `aws-java-sdk-*`
  managed entries (an exclusion removes the artifact from the dependency's
  whole subtree, covering the s3/sqs/sns → core → ion paths).
- Added `com.amazon.ion:ion-java:1.10.5` as a managed + global dependency so the
  patched artifact (same `com.amazon.ion` Java package) replaces it on the
  classpath.

### Direct declarations

| Package | Module | From | To | CVE(s) |
|---|---|---|---|---|
| org.bitbucket.b_c:jose4j | grouper-box | 0.9.3 | 0.9.6 | CVE-2024-29371, CVE-2023-51775 |
| org.apache.commons:commons-compress | grouper-installer | 1.25.0 | 1.27.1 | CVE-2024-25710, CVE-2024-26308 |

---

## Fixed — non-reactor modules (applied, not built by `make test`)

| Package | Module | From | To | CVE(s) |
|---|---|---|---|---|
| org.apache.activemq:activemq-broker (+ transitive activemq-client) | grouperActivemq | 5.19.2 | 5.19.7 | CVE-2026-34197/39304/40466/41044/42588/45505/33227/41043/49270 (broker), CVE-2026-39304/33227 (client) |
| org.pac4j:pac4j-* | grouper-ext-auth | 5.7.2 | 5.7.10 | CVE-2026-40458 (pac4j-core); last 5.7.x patch |
| org.apache.commons:commons-lang3 | test-plugin, grouper testImplementation | 3.12.0 | 3.18.0 | CVE-2025-48924 |

(The reactor already carried a patched `commons.lang3` = 3.20.0 and
`commons.collections` = 3.2.2; only these two stragglers hard-coded 3.12.0.)

---

## Partially fixed / not fixable by a version change

### org.bouncycastle:bcprov-jdk15on 1.70 — residual CVEs (grouper-ws-java-generated-client, non-reactor)
CVE-2023-33201, CVE-2024-29857, CVE-2024-30171, CVE-2024-34447 are fixed only in
**1.78+, which ships as the `bcprov-jdk18on` artifact**. That module's
`bcprov-jdk15on` is required by `rampart-core:1.6.3` (needs the jdk15on
artifact), so switching to jdk18on would break resolution. I reverted an initial
(invalid) bump to `1.78` — no such `jdk15on` release exists — and kept `1.70`,
the last jdk15on release. **No version-only fix exists for the residual CVEs on
the jdk15on line.** (The modern stack already uses `bc*-jdk18on:1.84`.)

### commons-httpclient:commons-httpclient 3.1 — CVE-2012-5783 (grouper-installer, grouper-ws)
3.1 is the **final** release of `commons-httpclient`. The "fix" (Trivy's `4.0`)
is the rewritten `org.apache.httpcomponents:httpclient`, a different artifact
with an incompatible API. **No drop-in version fix exists**; remediation would
require porting the calling code to HttpComponents 4.x/5.x, which is beyond a
dependency-version change and would break the build if done blindly.

### org.apache.axis2:axis2-transport-http 1.6.4 — CVE-2012-5785 (grouper-ws, reactor)
The fix (1.8.0) requires upgrading the **entire coupled Axis2 stack**
(`axis2-kernel`/`axis2-adb`/`axis2-transport-local`, currently a mix of
1.6.1/1.6.4). Axis2 1.8 is a different, source-incompatible generation; bumping
only `axis2-transport-http` to 1.8.0 leaves it against `axis2-kernel:1.6.4` and
breaks the build. **Not fixable by a lone version change** without a full Axis2
migration + code changes, so it is left at 1.6.4 and documented here.

### org.hibernate:hibernate-core 5.6.10.Final — CVE-2026-0603 (reactor)
Trivy reports **no fixed version**; the 5.6.x line only advances to 5.6.15.Final
(no security backport for this advisory), and moving to Hibernate 6.x is a major
migration. **No version-only fix available** — left as-is.

### net.sf.json-lib:json-lib 2.4 — CVE-2024-47855 (transitive, many modules)
`json-lib` is abandoned; **no fixed version was ever released**. Left as-is
(transitive). The forward-looking replacement would be a different JSON library.

### commons-lang:commons-lang 2.6 / 2.1 — CVE-2025-48924 (transitive)
The `commons-lang` 2.x line is EOL; the fix is in `commons-lang3` 3.18.0 (a
different artifact, already the managed version in the reactor). **No fix for
the 2.x artifact** — it is pulled transitively by legacy libraries. Left as-is.

### org.apache.velocity:velocity 1.7 — CVE-2020-13936 (transitive, grouper-shib non-reactor)
The 1.x `velocity` artifact was never patched; the fix is in
`org.apache.velocity:velocity-engine-core` 2.x, a different artifact with an
incompatible package layout. **No version-only fix for `velocity` 1.x.**

### dom4j:dom4j 1.6.1 — CVE-2020-10683, CVE-2018-1000632 (transitive, grouper-shib non-reactor)
The old `dom4j:dom4j` coordinates were never patched; the fix is
`org.dom4j:dom4j` 2.x — which the reactor already uses (`${dom4j.version}` =
2.1.4, and `grouper` explicitly excludes the legacy `dom4j:dom4j`). The 1.6.1
copy survives only transitively inside the non-reactor `grouper-shib` legacy
OpenSAML 2.x stack. **No version-only fix on the old coordinates.**

### grouper-shib legacy stack (non-reactor) — spring 2.5.6.SEC02, esapi 2.0.1, vt-ldap 3.3.4, not-yet-commons-ssl 0.3.9, xmlsec 1.5.7, opensaml 2.6.x, xalan/commons-httpclient
`grouper-shib` declares only 3 internal (`${project.version}`) dependencies;
every vulnerable artifact above is pulled **transitively** by the pinned
**OpenSAML/Shibboleth 2.x** stack. Their fixed versions (Spring 5.x/6.x, ESAPI
2.5.x, xmlsec 2.x/3.x, etc.) are incompatible with OpenSAML 2.x and cannot be
forced without breaking the module. Remediating them means migrating off
OpenSAML 2.x — a framework upgrade, not a dependency-version change, and out of
scope for "remediation without adding features/refactoring". The module is not
in the reactor. **Documented, not changed.**

### grouper-ext-auth spring-core 5.3.24 — CVE-2025-41249 (transitive, non-reactor)
Pulled transitively by `pac4j` 5.7.x, which is built on Spring 5.3.x. The fix
(Spring 6.2.11) requires pac4j 6.x — a major upgrade of that module. Bumping
pac4j to 5.7.10 (done, for CVE-2026-40458) keeps it on the Spring 5.3.x line, so
this CVE remains. **Not fixable without a pac4j 6.x migration.**

### apacheds-ldappc-schema (non-reactor) — commons-collections 3.2, commons-lang 2.1
`commons-collections` 3.2 → 3.2.2 fixes CVE-2015-7501/6420, but this pom is a
dead, non-reactor LDAP-schema helper not referenced by any built module; it also
pulls the unfixable `commons-lang` 2.1. Left as-is and documented (no build
impact).
