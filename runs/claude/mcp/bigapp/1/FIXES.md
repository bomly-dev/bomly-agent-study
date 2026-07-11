# Dependency vulnerability remediation

Scope: the Maven application under `fixtures/bigapp` (Grouper 4.x, 13-module
reactor rooted at `grouper-parent`). Findings were produced by the bomly MCP
server (`bomly_scan`/`bomly_explain`, Grype-backed) over
`fixtures/bigapp/grouper-parent`.

The scan reported **21 vulnerable packages**. All are pulled in
**transitively** — none is a direct, first-party dependency. Fixed versions
were confirmed to resolve against the build's configured mirror
(`maven-central.storage-download.googleapis.com`) before being applied.

Remediation strategy:

- Transitive packages with a single introducing path were pinned to a patched
  version in `grouper-parent/pom.xml` `<dependencyManagement>` (a
  reactor-wide override), or, where a child module declares the dependency
  with an explicit `<version>`, in that child pom (dependencyManagement does
  not override a version hard-coded on a child dependency).
- The BouncyCastle `jdk15on` line is discontinued (last release 1.70) and has
  no version carrying the newer fixes, so it was excluded and replaced with
  the patched `jdk18on` artifacts the project already manages.
- Four packages have **no fixed version** that can be applied without breaking
  the application; these are documented as such below and left unchanged.

---

## Remediated by version change

### io.netty : netty-codec-http, netty-codec, netty-handler, netty-common (4.1.72.Final → 4.1.135.Final)
- **Found:** numerous High/Medium/Low advisories across the four netty
  artifacts (e.g. GHSA-3qp7-7mw8-wx86, GHSA-c653-97m9-rcg9, GHSA-x4gw-5cx5-pgmh,
  GHSA-57rv-r2g8-2cj3, GHSA-f6hv-jmp6-3vwv, GHSA-pwqr-wmgm-9rr8,
  GHSA-mj4r-2hfc-f8p6, plus many Medium/Low). Introduced via
  `grouper → org.apache.qpid:qpid-jms-client:0.61.0`.
- **Change:** imported `io.netty:netty-bom:4.1.135.Final` into
  `grouper-parent/pom.xml` `<dependencyManagement>` so **all** netty artifacts
  move to one patched version consistently (netty artifacts are co-versioned;
  pinning only the vulnerable four would risk version skew).
- **Why:** 4.1.135.Final post-dates every fix listed for these advisories.

### com.fasterxml.jackson.core : jackson-databind (2.18.2 → 2.18.9)
- **Found:** GHSA-j3rv-43j4-c7qm, GHSA-rmj7-2vxq-3g9f (High), GHSA-hgj6-7826-r7m5
  (Medium), and GHSA-5jmj-h7xm-6q6v (Medium). Introduced directly via
  `grouper`/`grouperClient` (declared without an explicit version, so managed
  by the parent property). GHSA-5jmj was reported "not-fixed" by the local DB,
  but the upstream advisory lists **2.18.9** as the fix.
- **Change:** bumped the `jackson.databind` property in `grouper-parent/pom.xml`
  from 2.18.2 to 2.18.9.
- **Why:** 2.18.9 covers all four advisories (affected `< 2.18.9`).

### com.fasterxml.jackson.core : jackson-core (2.18.2 → 2.18.9)
- **Found:** GHSA-72hv-8253-57qq (Medium). Introduced transitively via
  jackson-databind.
- **Change:** added a `jackson-core` `<dependencyManagement>` entry in
  `grouper-parent/pom.xml` pinned to `${jackson.databind}` (2.18.9), keeping
  core and databind in lockstep.
- **Why:** fix released in 2.18.6; 2.18.9 is ≥ that.

### org.apache.neethi : neethi (3.0.2 → 3.2.2)
- **Found:** GHSA-2hfh-9h53-qc24, GHSA-g36m-9g3m-2vmp (High), GHSA-287c-fxr7-3w6c
  (Medium). Introduced via `grouper-ws → org.apache.axis2:axis2-kernel:1.6.4`.
- **Change:** pinned neethi to 3.2.2 in `grouper-parent/pom.xml`
  `<dependencyManagement>`.
- **Why:** 3.2.2 is the fixed release for all three.

### com.nimbusds : nimbus-jose-jwt (9.37 → 9.37.4)
- **Found:** GHSA-gvpg-vgmx-xg6w (High), GHSA-xwmg-2g98-w7v9 (Medium).
  Introduced via `grouper → com.nimbusds:oauth2-oidc-sdk:11.6`.
- **Change:** pinned nimbus-jose-jwt to 9.37.4 in the parent
  `<dependencyManagement>`.
- **Why:** 9.37.4 carries both fixes.

### com.google.oauth-client : google-oauth-client (1.33.2 → 1.33.3)
- **Found:** GHSA-hw42-3568-wj87 (High). Introduced via
  `google-apps-provisioner → google-api-client:1.34.0`.
- **Change:** pinned to 1.33.3 in the parent `<dependencyManagement>`.

### com.google.protobuf : protobuf-java (4.26.1 → 4.27.5)
- **Found:** GHSA-735f-pc8j-v9w8 (High). Introduced via
  `grouper-ui → com.mysql:mysql-connector-j:9.1.0`.
- **Change:** pinned to 4.27.5 in the parent `<dependencyManagement>`.

### com.google.guava : guava (31.1-jre → 32.0.0-jre)
- **Found:** GHSA-7g45-4rm6-3mm3 (Medium), GHSA-5mg8-w23w-74h3 (Low).
  Introduced via `google-apps-provisioner → google-api-client:1.34.0`.
- **Change:** pinned to 32.0.0-jre (the `-jre` flavour matching this project)
  in the parent `<dependencyManagement>`.

### org.apache.james : apache-mime4j-core (0.7.2 → 0.8.10)
- **Found:** GHSA-jw7r-rxff-gv24 (Medium). Introduced via
  `grouper-ws → axis2-kernel → axiom-api:1.2.15`.
- **Change:** pinned to 0.8.10 in the parent `<dependencyManagement>`.

### org.bitbucket.b_c : jose4j (0.9.3 → 0.9.6)
- **Found:** GHSA-3677-xxcr-wjqv (High), GHSA-6qvw-249j-h44c (Medium).
  Declared with an explicit version in `grouper-misc/grouper-box/pom.xml`.
- **Change:** bumped the explicit `<version>` there from 0.9.3 to 0.9.6
  (a parent-level override would not win over the child's hard-coded version).

### org.apache.commons : commons-compress (1.25.0 → 1.26.0)
- **Found:** GHSA-4265-ccf5-phj5, GHSA-4g9r-vxhx-9pgx (Medium). Declared with an
  explicit version in `grouper-misc/grouper-installer/pom.xml`.
- **Change:** bumped the explicit `<version>` there from 1.25.0 to 1.26.0.

### org.bouncycastle : bcprov-jdk15on and bcpkix-jdk15on (1.52 → replaced by jdk18on 1.84)
- **Found:** many advisories on bcprov-jdk15on (High/Medium/Low, e.g.
  GHSA-2j2x-hx4g-2gf4, GHSA-4vhj-98r6-424h, GHSA-xqj7-j8j5-f2xr, …) and
  bcpkix-jdk15on (GHSA-4cx2-fc23-5wg6, GHSA-wg6q-6289-32hp). Both introduced
  solely via `grouper-box → com.box:box-java-sdk:2.17.0`.
- **Problem:** the `org.bouncycastle:*-jdk15on` artifacts were discontinued at
  **1.70**; the fixes reported (1.78/1.79/1.84) exist only under the renamed
  `*-jdk18on` coordinates, so a plain version bump of the `jdk15on` artifact is
  impossible (those versions do not exist).
- **Change:** in `grouper-misc/grouper-box/pom.xml`, excluded `bcprov-jdk15on`
  and `bcpkix-jdk15on` from `box-java-sdk` and added explicit dependencies on
  `bcprov-jdk18on` / `bcpkix-jdk18on` (version 1.84, already managed in
  `grouper-parent` and reported clean by the scan).
- **Why:** removes the vulnerable 1.52 jars entirely and substitutes the
  patched modern BouncyCastle the project already uses elsewhere; identical
  `org.bouncycastle.*` Java packages keep box-java-sdk working. This also
  clears the two bcprov advisories the DB marked "not-fixed" for the jdk15on
  line (GHSA-hr8g-6v94-x4m9, GHSA-wjxj-5m7g-mg7q), which do not affect
  jdk18on 1.84.

### org.apache.axis2 : axis2-transport-http (1.6.4 → 1.8.0)
- **Found:** GHSA-wwq7-pxwc-p4rc (Medium). Declared with explicit versions in
  `grouper-ws/grouper-ws/pom.xml` and
  `grouper-ws/grouper-ws-java-generated-client/pom.xml`.
- **Change:** bumped both explicit `<version>` declarations from 1.6.4 to 1.8.0.
- **Why:** 1.8.0 is the fixed release. (The surrounding axis2-kernel/adb stay
  at 1.6.4; the build compiles cleanly, but see note — a future full axis2 1.8
  migration would be cleaner.)

---

## Not fixable by a version change (left unchanged, by design)

### software.amazon.ion : ion-java (1.0.2) — GHSA-264p-99wq-f4j6 (High)
- Introduced via `grouper → com.amazonaws:aws-java-sdk-core:1.12.267`.
- The fix (1.10.5) exists **only** under the renamed `com.amazon.ion:ion-java`
  coordinates, which also changed the Java package to `com.amazon.ion.*`. The
  original `software.amazon.ion:ion-java` line stops at 1.5.1 with no fix, and
  swapping in `com.amazon.ion:ion-java` would break `aws-java-sdk-core`, which
  is compiled against the `software.amazon.ion.*` package. AWS SDK v1 never
  ships a patched ion-java, so upgrading the SDK would not help either.
- **No safe fixed version exists for the artifact as shipped.** Left unchanged.

### org.hibernate : hibernate-core (5.6.10.Final) — GHSA-2p5w-cvg5-gc5c / CVE-2026-0603 (High)
- Managed via `hibernate.core.version` (5.6.10.Final); used across the reactor.
- The advisory covers `>= 5.2.8, <= 5.6.15` with **no patched version** in the
  5.x line. The only non-affected line is Hibernate 6.x, which is a major,
  breaking migration (Jakarta namespace, API changes) — not a version bump and
  well outside remediation scope.
- **No fixed version available.** Left unchanged.

### commons-httpclient : commons-httpclient (3.1) — GHSA-3832-9276-x7gf (Medium)
- Introduced via `grouper-installer`.
- Commons HttpClient 3.x is end-of-life (3.1 is the last release) and has no
  fix; the successor is the separate `org.apache.httpcomponents:httpclient`
  4.x/5.x artifact (a code migration, not a version bump).
- **No fixed version of this artifact exists.** Left unchanged.

### commons-lang : commons-lang (2.6) — GHSA-j288-q9x7-2f5v (Medium)
- Introduced via `grouper-duo`.
- The legacy `commons-lang:commons-lang` 2.x line is end-of-life (2.6 is the
  last release); the fix lives only in the separate
  `org.apache.commons:commons-lang3` artifact (already present in the project
  at 3.20.0 for other code). Replacing the transitive 2.6 usage would require
  code changes in the consumer.
- **No fixed version of the 2.x artifact exists.** Left unchanged.
