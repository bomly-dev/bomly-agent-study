# Dependency vulnerability remediation

Scope: the Maven application under `fixtures/bigapp` (vendored Grouper 4.x,
13-module reactor). There is no built-in audit command for this ecosystem, so
every declared dependency coordinate across all `pom.xml` files was resolved
(properties + `dependencyManagement`) and queried against the OSV.dev
vulnerability database (GitHub Advisory data). 14 distinct vulnerable
coordinates were identified. Each is listed below with what was found and the
action taken.

Fixed versions were chosen to stay within the same minor/patch line wherever
possible to avoid breaking the build; `make test` (full-reactor
`mvn -DskipTests install`) still succeeds after these changes.

A note on the reactor: `make test` builds only the modules listed in
`grouper-parent/pom.xml`. `grouperActivemq`, `grouper-ext-auth`,
`test-plugin`, and the test `testImplementation` module are *not* in that
reactor, but they are part of the application and were remediated too.

---

## Remediated (version bumped)

### 1. com.fasterxml.jackson.core:jackson-databind — 2.18.2 → 2.18.8
- **Found:** GHSA-hgj6-7826-r7m5, GHSA-j3rv-43j4-c7qm, GHSA-rmj7-2vxq-3g9f
  (DNS-triggering InetSocketAddress deserialization, PolymorphicTypeValidator
  bypasses / allowlist bypass).
- **Changed:** `jackson.databind` property in `grouper-parent/pom.xml`; and the
  three hard-coded `2.18.2` jackson artifacts in
  `grouper-ws/grouper-ws/pom.xml` (jackson-jaxrs-base, jackson-jaxrs-json-provider,
  jackson-datatype-jsr310) — all → `2.18.8`.
- **Why 2.18.8:** first patch on the 2.18 line that fixes all three (verified
  clean-of-those against OSV); staying on 2.18.x keeps the API identical.
- **Residual — no fix available:** GHSA-5jmj-h7xm-6q6v (case-insensitive
  deserialization bypasses per-property `@JsonProperty`). OSV confirms 2.18.8 is
  still affected and there is **no fixed release on the 2.x line** (the issue was
  patched then reintroduced in 2.19+; no clean 2.x version exists). Cannot be
  remediated by a version change; would require a code-level mitigation.

### 2. org.apache.activemq:activemq-broker — 5.19.2 → 5.19.7 (`grouperActivemq`)
- **Found:** 9 advisories incl. RCE / code-injection (GHSA-mr6m-xj7v-3cv3,
  GHSA-w3w2-mpp5-92gm), classpath validation (GHSA-h2h4-5m64-m273), DoS,
  and XSS.
- **Changed:** `activemq-broker` **and** `activemq-jaas` `5.19.2` → `5.19.7` in
  `grouper-misc/grouperActivemq/pom.xml` (both bumped to keep the ActiveMQ
  release aligned). 5.19.7 is the highest fix required across the 9 advisories
  and is the latest 5.19.x patch; OSV-clean.

### 3. org.apache.commons:commons-compress — 1.25.0 → 1.26.0 (`grouper-installer`)
- **Found:** GHSA-4265-ccf5-phj5, GHSA-4g9r-vxhx-9pgx (OOM / infinite-loop DoS).
- **Changed:** `grouper-misc/grouper-installer/pom.xml` → `1.26.0` (the fix
  version; OSV-clean).

### 4. org.bitbucket.b_c:jose4j — 0.9.3 → 0.9.6 (`grouper-box`)
- **Found:** GHSA-6qvw-249j-h44c (fixed 0.9.4) and GHSA-3677-xxcr-wjqv
  (DoS via compressed JWE, fixed 0.9.6).
- **Changed:** `grouper-misc/grouper-box/pom.xml` → `0.9.6` (covers both;
  OSV-clean).

### 5. org.pac4j:pac4j-core — 5.7.2 → 5.7.10 (`grouper-ext-auth`)
- **Found:** GHSA-xw5c-jc7x-gf75 (CSRF).
- **Changed:** `pac4j.version` in `grouper-misc/grouper-ext-auth/pom.xml`
  → `5.7.10` (fix on the 5.7.x line; keeps compatibility with the pinned
  `javaee-pac4j` 7.1.0 and the other pac4j modules). OSV-clean.

### 6. org.apache.commons:commons-lang3 — 3.12.0 → 3.18.0 (test plugins)
- **Found:** GHSA-j288-q9x7-2f5v (uncontrolled recursion in `LocaleUtils`).
- **Changed:** `grouper-misc/test-plugin/pom.xml` and
  `grouper/src/test/edu/internet2/middleware/grouper/plugins/testImplementation/pom.xml`
  → `3.18.0` (the fix version; OSV-clean).
- **Note:** the reactor modules already use the parent-managed
  `commons.lang3.version` = 3.20.0 (already safe); only these two standalone
  plugin POMs pinned the old 3.12.0.

### 7. org.bouncycastle:bcprov-jdk15on 1.70 → org.bouncycastle:bcprov-jdk18on 1.84
       (`grouper-ws-java-generated-client`)
- **Found:** GHSA-4h8f-2wvx-gg5w, GHSA-8xfc-gm6g-vgpv, GHSA-v435-xc8x-wvr9
  (DNS poisoning, cert-parsing CPU DoS, RSA timing side-channel) — all fixed in
  Bouncy Castle 1.78 — plus GHSA-hr8g-6v94-x4m9 and GHSA-wjxj-5m7g-mg7q.
- **Why an artifact change, not just a version bump:** the `bcprov-jdk15on`
  artifact line is retired at 1.70 — there is no 1.78+ under that artifactId.
  The patched successor is `bcprov-jdk18on` (identical `org.bouncycastle`
  packages, drop-in on Java 17).
- **Changed:** in `grouper-ws/grouper-ws-java-generated-client/pom.xml` replaced
  the explicit `bcprov-jdk15on:1.70` with `bcprov-jdk18on:${bouncyCastle.version}`
  (1.84, matching the version already managed in `grouper-parent`).
  **Also** added a `bcprov-jdk15on` exclusion to the `wss4j` 1.6.19 dependency:
  wss4j pulls an old `bcprov-jdk15on` (~1.49) transitively, which the explicit
  1.70 previously overrode; without the exclusion the vulnerable jdk15on jar
  would have reappeared on the classpath next to the new jdk18on jar.
  (rampart-core already excluded it.) bcprov-jdk18on 1.84 is OSV-clean.

### 8. org.opensaml:opensaml — 2.6.4 → 2.6.5 (parent-managed; used by grouper, grouper-ui)
- **Found:** GHSA-78fq-w796-q537 (improper certificate validation, CVE-2015-1796).
- **Changed:** `opensaml.version` in `grouper-parent/pom.xml` → `2.6.5` (the
  fixed release).
- **Extra change required:** opensaml 2.6.5 is **not published to Maven Central**
  (Central only has up to 2.6.4); it exists only in the Shibboleth releases
  repository. Added that repository to `<repositories>` in
  `grouper-parent/pom.xml` so the patched artifact resolves. OSV-clean at 2.6.5.

---

## Identified but NOT fixed — no version-only remediation exists

### 9. commons-httpclient:commons-httpclient — 3.1 (`grouper-installer`)
- **Found:** GHSA-3832-9276-x7gf (improper certificate/hostname validation,
  CVE-2012-5783).
- **No fix:** 3.1 is the final release of this artifact; the project was
  abandoned and superseded by `org.apache.httpcomponents:httpclient` (a
  different artifact, which the app already uses at 4.5.13 elsewhere). There is
  **no fixed 3.x version** to move to. Remediation would require migrating the
  installer's code off the legacy `org.apache.commons.httpclient` API — a code
  change, not a version bump. Left unchanged and documented.

### 10. commons-lang:commons-lang — 2.6 (parent-managed)
- **Found:** GHSA-j288-q9x7-2f5v (uncontrolled recursion — same CVE class as
  item 6, but the legacy `commons-lang` artifact).
- **No fix:** 2.6 is the last release of the old `commons-lang` artifact; the
  fix ships only in the *different* artifact `org.apache.commons:commons-lang3`
  (≥ 3.18.0). There is **no fixed 2.x release.** Migrating the many
  `org.apache.commons.lang.*` usages to `lang3` is a code change across the
  codebase, out of scope for version remediation. Left unchanged and documented.

### 11. net.sf.json-lib:json-lib — 2.4 (jdk15 classifier, parent-managed)
- **Found:** GHSA-wwcp-26wc-3fxm (mishandled unbalanced comment string / DoS).
- **No fix:** 2.4 (2010) is the final release of `net.sf.json-lib:json-lib`;
  OSV reports the vulnerability as unfixed with no later version. Left unchanged
  and documented.

### 12. org.apache.axis2:axis2-transport-http — 1.6.4
       (`grouper-ws`, `grouper-ws-java-generated-client`)
- **Found:** GHSA-wwq7-pxwc-p4rc (improper input validation / SSRF).
- **Fix version exists (1.8.0) but is not adoptable by a version bump alone.**
  The module is locked to the Axis2 1.6.x framework (`axis2-kernel` 1.6.4,
  `axis2-adb`, `axis2-transport-local`) plus **rampart-core 1.6.3** for
  WS-Security. Bumping only `axis2-transport-http` to 1.8.x against a 1.6.4
  kernel is an incompatible mismatch, and moving the whole stack to Axis2 1.8.x
  has no counterpart in Rampart — Rampart is abandoned (last release 1.7.1,
  built for Axis2 1.7.x) and never shipped an Axis2-1.8-compatible version.
  A full framework migration off Axis2/Rampart is required; it is a breaking
  code change, not a version bump, and would break the build. Left unchanged and
  documented.

### 13. org.hibernate:hibernate-core — 5.6.10.Final (parent-managed; grouper, grouper-azure)
- **Found:** GHSA-2p5w-cvg5-gc5c (SQL injection, CVE-2019-14900).
- **No fix on the 5.x line.** OSV marks the entire 5.2.8 → 5.6.15 range as
  affected with no 5.x fixed release (5.6.15 is the last 5.6 patch and is still
  affected). The fix is only in Hibernate ORM 6.x — a breaking major upgrade
  (the coordinate changes to `org.hibernate.orm:hibernate-core`, plus the
  Jakarta Persistence namespace migration). That is well beyond a version-only
  change and would break the build. Left unchanged and documented.

---

## Also considered — the Apache Tomcat bump (item covered above under Remediated)

### org.apache.tomcat:tomcat-catalina — 8.5.60 → 9.0.118 (`grouper-ext-auth`, `provided`)
- **Found:** 23 advisories against Tomcat 8.5.x, several of which have **no fix
  on the 8.5 line** (last-affected 8.5.100 — the 8.5 branch is end-of-life), e.g.
  RCE/info-disclosure GHSA-83qj-6fr2-vhqg, path traversal GHSA-wmwf-9ccg-fff5,
  auth bypass GHSA-xcpr-7mr4-h4xq.
- **Changed:** `grouper-misc/grouper-ext-auth/pom.xml` → `9.0.118` (latest 9.0.x;
  OSV-clean). 9.0.x is still on the `javax.servlet` / `org.apache.catalina` API
  the plugin compiles against (Realm/Valve/listener classes), so it is
  source-compatible (unlike Tomcat 10+, which moves to `jakarta.*`). The
  dependency is `provided` scope. This module is not in the `make test` reactor.
