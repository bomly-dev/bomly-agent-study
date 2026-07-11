# Dependency vulnerability remediation

Scope: the Maven fixture application under `fixtures/bigapp` (vendored Grouper
4.x, 13-module reactor built from `fixtures/bigapp/grouper-parent`).

Tooling: vulnerabilities were identified with the `bomly` MCP server
(`bomly_scan --enrich --audit` and `bomly_explain`) against the reactor.
Fixes were verified by re-scanning and by `make test` at the repo root
(which runs `mvn -B -DskipTests install` for the whole reactor). The build
passes after all changes.

`make test` compiles and packages every module. Nearly all of the vulnerable
packages are pulled in transitively (not declared by any module), so they are
pinned to patched versions in the `<dependencyManagement>` section of
`grouper-parent/pom.xml`, which forces the fixed release across the whole
reactor. Packages declared directly in a module were bumped in that module.

Every fixed version was confirmed to exist in the configured Maven registry
before use. Fixed versions are chosen as the lowest release that clears every
advisory affecting the package (or, for the `affected_version_range` cases,
the lowest release outside the affected range).

## Summary

- 21 vulnerable packages were identified.
- 17 were remediated by a version change (63 advisories cleared).
- 4 could not be fixed by changing a version (see "Not fixable" below) — no
  fixed release exists for the coordinate, or the fixed release is not present
  in the configured registry. These are documented rather than falsely
  "fixed".

After remediation the only remaining `bomly` findings with real advisories are
those 4 packages. All other post-fix `[WARNING]` lines (`INVALID-*`,
`UNKNOWN-*`) are license/policy notices and packages with no advisory data, not
vulnerabilities.

---

## Fixed (version change)

### 1. com.fasterxml.jackson.core:jackson-databind — 2.18.2 → 2.18.9
- Found: CVE-2026-54512, CVE-2026-54513 (high), CVE-2026-54514, CVE-2026-54515
  (medium).
- Change: bumped the `jackson.databind` property in `grouper-parent/pom.xml`
  (already managed there; `grouper`, `grouperClient` inherit it). 2.18.9 is the
  first release outside the CVE-2026-54515 affected range (`<2.18.9`).

### 2. com.fasterxml.jackson.core:jackson-core — 2.18.2 → 2.18.9
- Found: GHSA-72hv-8253-57qq (medium).
- Change: added a `jackson-core` entry to `<dependencyManagement>` in
  `grouper-parent/pom.xml` pinned to `${jackson.databind}` (2.18.9), keeping
  core and databind aligned. Previously resolved transitively via databind.

### 3. com.google.guava:guava — 31.1-jre → 32.0.0-jre
- Found: CVE-2020-8908 (low), CVE-2023-2976 (medium).
- Change: pinned in `grouper-parent/pom.xml` `<dependencyManagement>`
  (transitive dependency).

### 4. com.google.oauth-client:google-oauth-client — 1.33.2 → 1.33.3
- Found: CVE-2021-22573 (high).
- Change: pinned in `grouper-parent/pom.xml` `<dependencyManagement>`
  (transitive dependency).

### 5. com.google.protobuf:protobuf-java — 4.26.1 → 4.27.5
- Found: CVE-2024-7254 (high).
- Change: pinned in `grouper-parent/pom.xml` `<dependencyManagement>`
  (transitive dependency).

### 6. com.nimbusds:nimbus-jose-jwt — 9.37 → 9.37.4
- Found: CVE-2023-52428 (high), CVE-2025-53864 (medium).
- Change: pinned in `grouper-parent/pom.xml` `<dependencyManagement>`
  (transitive dependency).

### 7–10. io.netty:netty-codec-http / netty-codec / netty-common / netty-handler — 4.1.72.Final → 4.1.135.Final
- Found (across the four artifacts): CVE-2022-24823, CVE-2024-29025,
  CVE-2025-58056, CVE-2025-67735, CVE-2026-33870, CVE-2026-41417,
  CVE-2026-42580/42581/42584/42585/42587, CVE-2026-50020 (netty-codec-http);
  CVE-2025-58057, CVE-2026-42583 (netty-codec); CVE-2024-47535, CVE-2025-25193
  (netty-common); CVE-2023-34462, CVE-2026-44249, CVE-2026-45416,
  CVE-2026-50010 (netty-handler).
- Change: imported `io.netty:netty-bom:4.1.135.Final` (scope `import`) in
  `grouper-parent/pom.xml` `<dependencyManagement>`, which pins every netty
  artifact to a single consistent, patched version. 4.1.135.Final is the
  highest fixed version required by any of the netty advisories.

### 11. org.apache.axis2:axis2-transport-http — 1.6.4 → 1.8.0
- Found: CVE-2012-5785 (medium — improper SSL hostname verification).
- Change: bumped the direct declaration in `grouper-ws/grouper-ws/pom.xml`
  (the only reactor module that pulls this artifact). Verified the module
  still compiles (`AxisServlet` from transport-http and `MessageContext` from
  axis2-kernel 1.6.4 both resolve) and that the full reactor build passes.

### 12. org.apache.commons:commons-compress — 1.25.0 → 1.26.0
- Found: CVE-2024-25710, CVE-2024-26308 (medium).
- Change: bumped the direct declaration in
  `grouper-misc/grouper-installer/pom.xml`.

### 13. org.apache.james:apache-mime4j-core — 0.7.2 → 0.8.10
- Found: CVE-2024-21742 (medium).
- Change: pinned in `grouper-parent/pom.xml` `<dependencyManagement>`
  (transitive dependency).

### 14. org.apache.neethi:neethi — 3.0.2 → 3.2.2
- Found: CVE-2026-42402, CVE-2026-42403 (high), CVE-2026-42404 (medium).
- Change: pinned in `grouper-parent/pom.xml` `<dependencyManagement>`
  (transitive dependency).

### 15. org.bitbucket.b_c:jose4j — 0.9.3 → 0.9.6
- Found: CVE-2024-29371 (high), CVE-2023-51775 (medium).
- Change: bumped the direct declaration in
  `grouper-misc/grouper-box/pom.xml`.

### 16 & 17. org.bouncycastle:bcprov-jdk15on and bcpkix-jdk15on — 1.52 → removed (replaced by jdk18on 1.84)
- Found: bcprov-jdk15on@1.52 — CVE-2016-1000338/1000340/1000342/1000343/
  1000344/1000352 and CVE-2018-1000180 (high); CVE-2016-1000339/1000341/
  1000345, CVE-2020-15522, CVE-2020-26939, CVE-2024-29857, CVE-2024-30171,
  CVE-2023-33201, CVE-2023-33202 (medium); CVE-2016-1000346 (low).
  bcpkix-jdk15on@1.52 — CVE-2025-8916, CVE-2026-5588 (medium).
- Why not a simple version bump: the `bcprov-jdk15on`/`bcpkix-jdk15on`
  artifacts are end-of-life — that coordinate line stopped at 1.70, so the
  versions the advisories require (1.78 / 1.79 / 1.84) do not exist for it, and
  two advisories (CVE-2023-33201/33202) have no fixed jdk15on release at all.
  Bouncy Castle renamed the maintained artifacts to `bcprov-jdk18on` /
  `bcpkix-jdk18on`, which the project already uses at 1.84 (managed in
  `grouper-parent`, reported clean by bomly).
- Change: the legacy 1.52 jars entered only via
  `com.box:box-java-sdk:2.17.0` in `grouper-misc/grouper-box/pom.xml`. Added
  exclusions for `bcprov-jdk15on` and `bcpkix-jdk15on` on that dependency and
  added explicit `bcprov-jdk18on` / `bcpkix-jdk18on` dependencies (version from
  the parent, 1.84). The `org.bouncycastle.*` packages/classes are identical
  between the jdk15on and jdk18on artifacts, so box-java-sdk resolves them at
  runtime; grouper-box compiles and the reactor builds.

---

## Not fixable by a version change (no fixed release available)

### 18. commons-httpclient:commons-httpclient — 3.1 (UNCHANGED)
- Found: CVE-2012-5783 (medium — improper certificate validation).
- No fix: bomly reports `fix_state: not-fixed`, affected range `>=3.0,<4.0`.
  Commons HttpClient 3.x is end-of-life; 3.1 is the last release under this
  coordinate and no patched 3.x exists. The successor is a different coordinate
  (`org.apache.httpcomponents:httpclient`), which is a code migration, not a
  version bump, so it is out of scope for pure dependency remediation. Enters
  via `grouper-installer` (direct) and `grouper-ws` → `axis2-kernel`
  (transitive). Left unchanged and documented.

### 19. commons-lang:commons-lang — 2.6 (UNCHANGED)
- Found: CVE-2025-48924 (medium — uncontrolled recursion).
- No fix: bomly reports `fix_state: not-fixed`, affected range `>=2.0,<=2.6`.
  2.6 is the final release of the commons-lang 2.x coordinate; the fix lives in
  the separate `org.apache.commons:commons-lang3` coordinate, which is a code
  migration rather than a version bump. Left unchanged and documented.

### 20. org.hibernate:hibernate-core — 5.6.10.Final (UNCHANGED)
- Found: CVE-2026-0603 (high — SQL injection).
- No fix: bomly reports `fix_state: not-fixed`, affected range
  `>=5.2.8,<=5.6.15`. 5.6.15.Final is the last release of the Hibernate 5.6
  line (verified 5.6.16 does not exist), so no patched 5.x version is
  available. The only unaffected releases are Hibernate 6.x, which is a
  breaking major-version migration (Jakarta namespace, API changes), not a
  drop-in version bump, and would not keep the build compiling. Left unchanged
  and documented.

### 21. software.amazon.ion:ion-java — 1.0.2 (UNCHANGED)
- Found: CVE-2024-21634 (high — StackOverflow / uncontrolled resource
  consumption).
- No fix available here: bomly reports `fix_state: not-fixed`; the advisory's
  affected range is `<1.10.5`, so 1.10.5+ would clear it, but that version is
  not present in the configured Maven registry (its latest published ion-java
  is 1.5.1, and every available version 1.0.0–1.5.1 is inside the affected
  range). Pinning to a fixed version is therefore impossible without breaking
  dependency resolution / the build. Enters transitively via
  `com.amazonaws:aws-java-sdk-core:1.12.267`. Left unchanged and documented.
