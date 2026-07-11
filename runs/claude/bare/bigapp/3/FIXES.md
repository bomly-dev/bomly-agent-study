# Dependency vulnerability remediation

Scanner: `trivy fs` (vuln DB updated 2026-07-11) over `fixtures/bigapp`, cross-checked
against the real resolved tree (`mvn dependency:tree`) so that fixes target the
versions actually on the classpath rather than trivy's pom-only guesses.

Verification: `make test` (13-module `grouper-parent` reactor: compile + `install`,
`-DskipTests`) is **green** after all changes.

## Important context that shaped the fixes

* Most trivy findings repeat once per module because every module inherits
  `grouper-parent`. Fixing a version/property/`dependencyManagement` entry in the
  parent propagates the fix to all inheriting modules at once.
* Several trivy findings were **already fixed** in the effective build and needed no
  action — trivy mis-resolved parent property inheritance / groupId renames:
  * `commons-collections` resolves to **3.2.2** (patched), not the reported 3.2.
  * `commons-lang3` resolves to **3.20.0** (patched), not the reported 3.12.0 (except
    the two hard-coded `test-plugin` poms, fixed below).
  * `dom4j` resolves to **org.dom4j:dom4j 2.1.4** (patched); the reported
    `dom4j:dom4j 1.6.1` (old groupId) only appears in the un-built `grouper-shib`.
  * `bcprov/bcpkix-jdk18on` already **1.84** in the core `grouper` module.

## Fixed — version changes

| Package | From → To | Where changed | Notes / CVE class |
|---|---|---|---|
| com.fasterxml.jackson.core:jackson-databind & jackson-core | 2.18.2 → 2.18.9 | `grouper-parent` property `jackson.databind`; hard-coded jackson-jaxrs/datatype 2.18.2 in `grouper-ws/grouper-ws` | databind deserialization / DoS CVEs |
| com.google.guava:guava | 31.1-jre → 32.1.3-jre | `grouper-parent` `dependencyManagement` | CVE-2020-8908, CVE-2023-2976 (temp-dir) — transitive via google-api-client |
| com.google.oauth-client:google-oauth-client | 1.33.2 → 1.34.1 | `grouper-parent` DM | CVE-2021-22573 (token sig check) — transitive |
| com.google.protobuf:protobuf-java | 4.26.1 → 4.28.3 | `grouper-parent` DM | CVE-2024-7254 (recursion DoS) — transitive via mysql-connector-j |
| com.nimbusds:nimbus-jose-jwt | 9.37 / 9.25.6 → 9.37.4 | `grouper-parent` DM | CVE-2023-52428 etc — transitive via oauth2-oidc-sdk |
| io.netty:netty-* (buffer/common/handler/codec/codec-http/transport/…) | 4.1.72.Final → 4.1.135.Final | `grouper-parent` DM: import `netty-bom:4.1.135.Final` | many HIGH/MEDIUM CVEs — transitive via qpid-jms-client |
| org.apache.james:apache-mime4j-core | 0.7.2 → 0.8.11 | `grouper-parent` DM | CVE-2024-21742 — transitive via axis2-kernel |
| org.apache.neethi:neethi | 3.0.2 → 3.2.2 | `grouper-parent` DM | XML/policy DoS fixes — transitive via axis2-kernel |
| software.amazon.ion:ion-java | 1.0.2 → **com.amazon.ion:ion-java 1.10.5** | `grouper-parent` DM + exclude/replace in `grouper/pom.xml` | CVE-2024-21634. Fixed release only exists under the **renamed** coordinates `com.amazon.ion:ion-java` (old groupId tops out at unpatched 1.5.1); Java package `com.amazon.ion.*` is identical, so the old artifact is excluded from `aws-java-sdk-core` and the new one added. |
| org.apache.commons:commons-compress | 1.25.0 → 1.27.1 | `grouper-misc/grouper-installer` | CVE-2024-25710, CVE-2024-26308 |
| org.bitbucket.b_c:jose4j | 0.9.3 → 0.9.6 | `grouper-misc/grouper-box` | CVE-2023-51775 (and later) |
| org.apache.activemq:activemq-broker / activemq-jaas (and transitive activemq-client) | 5.19.2 → 5.19.7 | `grouper-misc/grouperActivemq` | multiple ActiveMQ CVEs |
| org.pac4j:pac4j-core | 5.7.2 → 5.7.10 | `grouper-misc/grouper-ext-auth` (`pac4j.version`) | CVE-2023-6559 (open redirect) |
| org.apache.commons:commons-lang3 | 3.12.0 → 3.20.0 | `grouper-misc/test-plugin` and `grouper/src/test/.../testImplementation` | CVE-2025-48924 (uncontrolled recursion) |
| commons-collections:commons-collections | 3.2 → 3.2.2 | `apacheds-ldappc-schema` (new DM) | CVE-2015-6420 / CVE-2017-15708 deserialization — transitive via apacheds-core 1.0.2 |

## Fixed — dependency exclusion (no clean version bump available)

| Package | Action | Where | Notes |
|---|---|---|---|
| org.bouncycastle:bcprov-jdk15on / bcpkix-jdk15on 1.52 | Excluded from `com.box:box-java-sdk`; the module already gets the modern `bcprov/bcpkix-jdk18on 1.84` (same `org.bouncycastle.*` packages) transitively via its `provided` dependency on `grouper` | `grouper-misc/grouper-box` | The `*-jdk15on` line is end-of-life (no release past 1.70; 17+ CVEs). Swapping to the `*-jdk18on` line is the actual fix. |

## Cannot be fixed by a version change (no fixed release exists)

| Package | Version | Reason |
|---|---|---|
| org.hibernate:hibernate-core | 5.6.10.Final | CVE-2026-0603 (HIGH, information disclosure) has **no fixed version** published in any Hibernate line as of the scan DB. Not remediable by a version bump; requires an upstream patch. |
| commons-httpclient:commons-httpclient | 3.1 | End-of-life (last release is 3.1). The advisory's "fixed in 4.0" refers to the **different** artifact `org.apache.httpcomponents:httpclient`, which is not a drop-in replacement. Present as a direct dep in `grouper-installer` and transitively via axis2-kernel 1.6.4. Fixing requires a code migration to HttpComponents, out of scope for a version-only remediation. |
| commons-lang:commons-lang | 2.6 (and 2.1 in apacheds) | No fixed release exists in the `commons-lang` (2.x) line; it was superseded by the separate artifact `commons-lang3`. Not a drop-in bump. |
| net.sf.json-lib:json-lib | 2.4 (jdk15) | Abandoned project; 2.4 is the last release and no patched version exists. |

## Known-vulnerable but in modules NOT built by `make test` (legacy / disabled)

These modules are outside the `grouper-parent` reactor that `make test` builds
(`grouper-shib` is explicitly commented out of the reactor; `grouper-legacy-ui`,
`grouper-ws-java-generated-client`, `grouper-ws-test`, `grouperScim`, the container
and webapp poms are aggregated elsewhere). They still inherit the parent, so all of
the parent-level fixes above apply to them automatically. The remaining items below
are specific to those legacy modules and require major framework upgrades rather than
a version bump, so they are called out here rather than silently "fixed":

* **grouper-shib** — Spring 2.5.6.SEC02 (spring-core/beans/context/web), xmlsec 1.5.7,
  velocity 1.7, opensaml 2.6.4, esapi 2.0.1, vt-ldap 3.3.4, bcprov-jdk15on 1.51,
  not-yet-commons-ssl 0.3.9, xalan 2.7.1. This is the legacy Shibboleth integration,
  disabled in the reactor and pinned to the ancient Shibboleth 1.x/Spring 2.5 stack;
  fixing these means a full Shibboleth/Spring major upgrade, not a version bump.
* **grouper-ws-java-generated-client** — axis2 1.6.4 (transport-http CVE), bcprov-jdk15on
  1.70 (rampart-core 1.6.3 requires the 15on line), xalan 2.7.1. Bound to the Axis2
  1.6 / Rampart 1.6 SOAP stack; a fix requires migrating that generated client to
  Axis2 1.8+, which is a breaking upgrade beyond version-only remediation.
* **grouper-ext-auth** — spring-core 5.3.24 (advisory fix is Spring 6.2.11) and
  xmlsec 3.0.2 (→ 3.0.3) arrive transitively via pac4j-saml-opensamlv5; the pac4j
  bump to 5.7.10 above is the in-line fix, full Spring 6 is a major upgrade.

## Direct axis2 remediation note

`axis2-transport-http 1.6.4` (MEDIUM, advisory fix 1.8.0) is used by `grouper-ws`.
The whole Axis2 stack (`axis2-kernel`, `-adb`, `-transport-local`, rampart) is pinned
to 1.6.x; bumping only transport-http to 1.8 would create an unsupported version skew
with the 1.6 kernel. A consistent Axis2 1.8 upgrade is a breaking change to the SOAP
services and is out of scope for version-only remediation. Its independently-versioned
vulnerable transitives (`apache-mime4j-core`, `neethi`) **were** upgraded via the
parent `dependencyManagement` above.
