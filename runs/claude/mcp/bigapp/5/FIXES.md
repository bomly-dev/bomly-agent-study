# Dependency vulnerability remediation

Scope: the Grouper 4.x Maven reactor under `fixtures/bigapp` (rooted at
`grouper-parent/pom.xml`, 13 modules). Vulnerabilities were identified with the
`bomly` MCP server (`bomly_scan --enrich --audit`, then `bomly_explain` per
package). The scan found **21 packages carrying real security advisories** out of
293 resolved dependencies. (The many `[WARNING]` entries in the scan are
license/metadata policy notes — invalid-SPDX or unknown-license — not
vulnerabilities, and are out of scope for version remediation.)

All version pins were applied centrally in `grouper-parent/pom.xml`
(`<dependencyManagement>` / properties) except where an artifact had to be
swapped out via `<exclusions>` (Bouncy Castle, ion-java), which was done in the
module that introduces it. Fixed-version availability was verified against Maven
Central before pinning. Build gate: `make test` (`mvn -B -DskipTests install`).

## Fixed

| # | Package | Was | Now | Advisories addressed | Where / how |
|---|---------|-----|-----|----------------------|-------------|
| 1 | io.netty:netty-* (netty-handler, netty-codec, netty-codec-http, netty-common, …) | 4.1.72.Final | 4.1.135.Final | GHSA-3qp7-7mw8-wx86, GHSA-c653-97m9-rcg9, GHSA-x4gw-5cx5-pgmh, GHSA-57rv-r2g8-2cj3, GHSA-f6hv-jmp6-3vwv, GHSA-pwqr-wmgm-9rr8, GHSA-mj4r-2hfc-f8p6 (+ ~13 medium/low) | Imported `netty-bom:4.1.135.Final` in parent `dependencyManagement` (manages every netty module consistently; same 4.1.x ABI). |
| 2 | com.fasterxml.jackson.core:jackson-databind | 2.18.2 | 2.18.9 | GHSA-j3rv-43j4-c7qm, GHSA-rmj7-2vxq-3g9f, GHSA-hgj6-7826-r7m5, GHSA-5jmj-h7xm-6q6v (CVE-2026-54512/13/14/15) | Bumped existing `<jackson.databind>` property in parent. 2.18.8 fixes the first three; 2.18.9 also fixes CVE-2026-54515 (affected `<2.18.9`). |
| 3 | com.fasterxml.jackson.core:jackson-core | 2.18.2 | 2.18.9 | GHSA-72hv-8253-57qq (nested-value DoS, fixed 2.18.6) | New pin in parent `dependencyManagement` (kept in lockstep with jackson-databind). |
| 4 | org.bouncycastle:bcprov-jdk15on | 1.52 | replaced by bcprov-jdk18on 1.84 | GHSA-2j2x-hx4g-2gf4, GHSA-4vhj-98r6-424h, GHSA-qcj7-g2j5-g7r3, GHSA-r97x-3g8f-gx3m, GHSA-rrvx-pwf8-p59p, GHSA-w285-wf9q-5w69, GHSA-xqj7-j8j5-f2xr (+ 10 medium/low) | See note below — excluded from `com.box:box-java-sdk` in `grouper-box`, replaced by the class-compatible `bcprov-jdk18on` 1.84 the app already standardizes on. |
| 5 | org.bouncycastle:bcpkix-jdk15on | 1.52 | replaced by bcpkix-jdk18on 1.84 | GHSA-4cx2-fc23-5wg6, GHSA-wg6q-6289-32hp | Same exclusion/replacement as bcprov (fix needs 1.79/1.84, unreachable on the jdk15on line). |
| 6 | org.bitbucket.b_c:jose4j | 0.9.3 | 0.9.6 | GHSA-3677-xxcr-wjqv (high), GHSA-6qvw-249j-h44c | Directly declared in `grouper-box`; bumped there and pinned in parent `dependencyManagement` for safety. |
| 7 | org.apache.neethi:neethi | 3.0.2 | 3.2.2 | GHSA-2hfh-9h53-qc24, GHSA-g36m-9g3m-2vmp (high), GHSA-287c-fxr7-3w6c | New pin in parent `dependencyManagement`. |
| 8 | com.nimbusds:nimbus-jose-jwt | 9.37 | 9.37.4 | GHSA-gvpg-vgmx-xg6w (high), GHSA-xwmg-2g98-w7v9 | New pin in parent `dependencyManagement`. |
| 9 | com.google.oauth-client:google-oauth-client | 1.33.2 | 1.33.3 | GHSA-hw42-3568-wj87 (high, IDToken signature verification) | New pin in parent `dependencyManagement`. |
| 10 | com.google.protobuf:protobuf-java | 4.26.1 | 4.27.5 | GHSA-735f-pc8j-v9w8 (high, recursion DoS) | New pin in parent `dependencyManagement`. |
| 11 | org.apache.commons:commons-compress | 1.25.0 | 1.26.0 | GHSA-4265-ccf5-phj5 (CVE-2024-26308), GHSA-4g9r-vxhx-9pgx (CVE-2024-25710) | New pin in parent `dependencyManagement`. |
| 12 | com.google.guava:guava | 31.1-jre | 32.1.3-jre | GHSA-7g45-4rm6-3mm3 (CVE-2023-2976), GHSA-5mg8-w23w-74h3 (low) | New pin in parent `dependencyManagement` (kept the `-jre` flavor). |
| 13 | org.apache.james:apache-mime4j-core | 0.7.2 | 0.8.10 | GHSA-jw7r-rxff-gv24 (DoS) | New pin in parent `dependencyManagement`. |
| 14 | software.amazon.ion:ion-java | 1.0.2 | replaced by com.amazon.ion:ion-java 1.10.5 | GHSA-264p-99wq-f4j6 (CVE-2024-21634, StackOverflow DoS) | Excluded from `com.amazonaws:aws-java-sdk-core` in `grouper` and replaced with `com.amazon.ion:ion-java:1.10.5` (same `com.amazon.ion.*` packages). The old `software.amazon.ion` coordinate is abandoned (last 1.5.1, still affected). |

The netty row covers four separately-advised packages (netty-handler,
netty-codec, netty-codec-http, netty-common), so the 14 rows above remediate
all **17** of the 21 vulnerable packages; the remaining 4 are listed below.

### Bouncy Castle note (items 4 & 5)
`bcprov-jdk15on`/`bcpkix-jdk15on` 1.52 were pulled transitively **only** through
`com.box:box-java-sdk@2.17.0` in `grouper-box`. The `-jdk15on` artifact line was
discontinued at **1.70**, so it can never reach the versions that fix the newer
CVEs (bcprov needs 1.78, bcpkix needs 1.79/1.84) — a plain version pin would be
incomplete. Because `-jdk15on` and `-jdk18on` expose identical `org.bouncycastle.*`
classes, and the `grouper` core module already ships `bcprov/bcpkix-jdk18on`
**1.84** (managed in the parent), the complete fix is to exclude the jdk15on
artifacts from `box-java-sdk` and add the jdk18on 1.84 equivalents in
`grouper-box`. This closes every bcprov/bcpkix advisory, including the two
bcprov issues with no version listed by the advisory feed (they predate 1.84).

## Not fixed — no fixed version exists on a compatible line

| Package | Version | Advisory | Why not fixed |
|---------|---------|----------|---------------|
| commons-httpclient:commons-httpclient | 3.1 | GHSA-3832-9276-x7gf (CVE-2012-5783, improper cert validation) | The Commons HttpClient 3.x line is **end-of-life**; 3.1 (2007) is its last release and no fixed 3.x version was ever published. The successor is a different artifact (`org.apache.httpcomponents:httpclient` 4.x/5.x) with an incompatible API — not a version bump. Pulled transitively via `grouper-installer` and `axis2-kernel`. Remediating requires a code migration, out of scope for version-only remediation. |
| commons-lang:commons-lang | 2.6 | GHSA-j288-q9x7-2f5v (CVE-2025-48924, uncontrolled recursion) | Advisory affected range is `>=2.0,<=2.6`; **2.6 is the last release of the commons-lang 2.x line** and no fixed 2.x version exists. The fix ships only in the separate `org.apache.commons:commons-lang3` artifact (3.18.0). commons-lang 2.6 arrives transitively through the `grouper` core; swapping it for commons-lang3 is an API change, not a version bump. (Note: the reactor already also uses commons-lang3.) |
| org.hibernate:hibernate-core | 5.6.10.Final | GHSA-2p5w-cvg5-gc5c (CVE-2026-0603, SQL injection) | Advisory affected range is `>=5.2.8,<=5.6.15` — **the entire Hibernate 5.6 line is affected and there is no fixed 5.6.x release**. The fix requires Hibernate 6.x/7.x, a breaking major migration (Jakarta Persistence namespace, bootstrap/API changes) touching Grouper's persistence layer. Not achievable by a version bump without breaking the build. |
| org.apache.axis2:axis2-transport-http | 1.6.4 | GHSA-wwq7-pxwc-p4rc (CVE-2012-5785, improper input validation) | A fixed version (**1.8.0**) exists, but `axis2-transport-http` must match the rest of the Axis2 stack that `grouper-ws` pins to 1.6.4 (`axis2-kernel`, `axis2-adb`, `axis2-transport-local`). Axis2 1.8.0 is a breaking major upgrade (Axiom 1.2→1.4, restructured/renamed APIs) that the WS module compiles against directly; bumping the whole stack in isolation breaks the build. Left at 1.6.4 to keep the reactor building; a full Axis2 1.8 migration is the real remediation and is out of scope here. |

## Verification
- Fixed-version existence confirmed against Maven Central (repo1) before pinning.
- Build gate: `make test` (`cd fixtures/bigapp/grouper-parent && mvn -B -DskipTests install`).
- Re-scan after the changes: `bomly_scan --enrich --audit` on `fixtures/bigapp/grouper-parent`.
