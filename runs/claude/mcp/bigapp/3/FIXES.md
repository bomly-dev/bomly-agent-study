# Vulnerable dependency remediation

Application: `fixtures/bigapp` (Internet2 Grouper 4.x, 13-module Maven reactor
rooted at `grouper-parent`). Vulnerabilities were identified with the `bomly`
MCP server (`bomly_scan --enrich --audit`, drilled down with `bomly_explain`)
and cross-checked against Maven Central for the existence of fixed releases.

The initial scan reported **21 vulnerable packages / 63 vulnerability findings**
(the many `INVALID-*` / `UNKNOWN-*` `[WARNING]` entries are unknown-license
policy notices, not vulnerabilities, and are out of scope for this task).

Every vulnerable package was transitive except `jose4j` (declared directly in
`grouper-box`). Fixes therefore work by pinning fixed versions in the parent
`<dependencyManagement>` (inherited by all modules), by correcting explicit
versions at their declaration sites, or by excluding/replacing a discontinued
artifact.

Result: **17 of 21 packages fully remediated**; 4 have no drop-in version fix
and are documented below. A post-change `bomly_scan` shows all 4 remaining
findings are the documented no-fix / deferred cases.

Files changed:
- `fixtures/bigapp/grouper-parent/pom.xml` — AWS SDK + jackson properties, new
  `<dependencyManagement>` pins.
- `fixtures/bigapp/grouper-misc/grouper-box/pom.xml` — jose4j bump; Bouncy
  Castle jdk15on → jdk18on.
- `fixtures/bigapp/grouper-misc/grouper-installer/pom.xml` — commons-compress bump.

---

## Fixed by a version change

| Package | From → To | Advisories | How |
|---|---|---|---|
| `com.fasterxml.jackson.core:jackson-core` | 2.18.2 → 2.18.9 | GHSA-72hv-8253-57qq | parent depMgmt (new) |
| `com.fasterxml.jackson.core:jackson-databind` | 2.18.2 → 2.18.9 | GHSA-rmj7-2vxq-3g9f, GHSA-j3rv-43j4-c7qm, GHSA-hgj6-7826-r7m5, GHSA-5jmj-h7xm-6q6v | `jackson.databind` property |
| `com.google.guava:guava` | 31.1-jre → 32.0.0-jre | GHSA-7g45-4rm6-3mm3, GHSA-5mg8-w23w-74h3 | parent depMgmt (new) |
| `com.google.oauth-client:google-oauth-client` | 1.33.2 → 1.33.3 | GHSA-hw42-3568-wj87 | parent depMgmt (new) |
| `com.google.protobuf:protobuf-java` | 4.26.1 → 4.27.5 | GHSA-735f-pc8j-v9w8 | parent depMgmt (new) |
| `com.nimbusds:nimbus-jose-jwt` | 9.37 → 9.37.4 | GHSA-gvpg-vgmx-xg6w, GHSA-xwmg-2g98-w7v9 | parent depMgmt (new) |
| `io.netty:netty-codec-http` | 4.1.72.Final → 4.1.135.Final | GHSA-269q-hmxg-m83q, GHSA-38f8-5428-x5cv, GHSA-57rv-r2g8-2cj3, GHSA-5jpm-x58v-624v, GHSA-84h7-rjj3-6jx4, GHSA-f6hv-jmp6-3vwv, GHSA-fghv-69vj-qj49, GHSA-hvcg-qmg6-jm4c, GHSA-m4cv-j2px-7723, GHSA-pwqr-wmgm-9rr8, GHSA-v8h7-rr48-vmmv, GHSA-xxqh-mfjm-7mv9 | `netty-bom` import |
| `io.netty:netty-handler` | 4.1.72.Final → 4.1.135.Final | GHSA-3qp7-7mw8-wx86, GHSA-6mjq-h674-j845, GHSA-c653-97m9-rcg9, GHSA-x4gw-5cx5-pgmh | `netty-bom` import |
| `io.netty:netty-codec` | 4.1.72.Final → 4.1.135.Final | GHSA-3p8m-j85q-pgmj, GHSA-mj4r-2hfc-f8p6 | `netty-bom` import |
| `io.netty:netty-common` | 4.1.72.Final → 4.1.135.Final | GHSA-389x-839f-4rhx, GHSA-xq3w-v528-46rv | `netty-bom` import |
| `org.apache.commons:commons-compress` | 1.25.0 → 1.26.0 | GHSA-4265-ccf5-phj5, GHSA-4g9r-vxhx-9pgx | direct version in `grouper-installer` (+ parent depMgmt) |
| `org.apache.james:apache-mime4j-core` | 0.7.2 → 0.8.10 | GHSA-jw7r-rxff-gv24 | parent depMgmt (new) |
| `org.apache.neethi:neethi` | 3.0.2 → 3.2.2 | GHSA-2hfh-9h53-qc24, GHSA-g36m-9g3m-2vmp, GHSA-287c-fxr7-3w6c | parent depMgmt (new) |
| `org.bitbucket.b_c:jose4j` | 0.9.3 → 0.9.6 | GHSA-3677-xxcr-wjqv, GHSA-6qvw-249j-h44c | direct version in `grouper-box` (+ parent depMgmt) |
| `org.bouncycastle:bcprov-jdk15on` | 1.52 → **jdk18on 1.84** | GHSA-2j2x-hx4g-2gf4, GHSA-4vhj-98r6-424h, GHSA-qcj7-g2j5-g7r3, GHSA-r97x-3g8f-gx3m, GHSA-rrvx-pwf8-p59p, GHSA-w285-wf9q-5w69, GHSA-xqj7-j8j5-f2xr, GHSA-6xx3-rg99-gc3p, GHSA-72m5-fvvv-55m6, GHSA-8xfc-gm6g-vgpv, GHSA-9gp4-qrff-c648, GHSA-c8xf-m4ff-jcxj, GHSA-r9ch-m4fh-fc7q, GHSA-v435-xc8x-wvr9, GHSA-fjqm-246c-mwqg, **GHSA-hr8g-6v94-x4m9, GHSA-wjxj-5m7g-mg7q** | exclude + replace in `grouper-box` |
| `org.bouncycastle:bcpkix-jdk15on` | 1.52 → **jdk18on 1.84** | GHSA-4cx2-fc23-5wg6, GHSA-wg6q-6289-32hp | exclude + replace in `grouper-box` |
| `software.amazon.ion:ion-java` | 1.0.2 → **removed** | GHSA-264p-99wq-f4j6 | bump `aws-java-sdk-*` 1.12.267 → 1.12.788 |

### Notes on the non-obvious fixes

**Bouncy Castle (`bcprov-jdk15on` / `bcpkix-jdk15on` 1.52).** Dragged in by
`com.box:box-java-sdk:2.17.0` (via `grouper-box`). Two advisories
(GHSA-hr8g-6v94-x4m9 / CVE-2023-33201 and GHSA-wjxj-5m7g-mg7q / CVE-2023-33202)
have **no fix in the `jdk15on` line at all** — that artifact line was
discontinued at 1.70 (verified on Maven Central), and `bomly`'s suggested
"pin to 1.78/1.84" targets the *renamed* `jdk18on` line, which does not exist
under the `jdk15on` coordinate. So a pure `jdk15on` version bump cannot fix
these. Instead the legacy `bcprov-jdk15on` / `bcpkix-jdk15on` are **excluded**
from `box-java-sdk` and replaced with the maintained `bcprov-jdk18on` /
`bcpkix-jdk18on` artifacts, which `grouper-parent` already manages at
`${bouncyCastle.version}` = 1.84. They expose the identical `org.bouncycastle.*`
API (only the JDK build target differs) and 1.84 post-dates every fix version,
so this closes all 19 Bouncy Castle advisories including the two the `jdk15on`
line never fixed.

**ion-java 1.0.2 (GHSA-264p-99wq-f4j6 / CVE-2024-21634).** Pulled by
`com.amazonaws:aws-java-sdk-core:1.12.267`. There is **no fixed release under
the `software.amazon.ion:ion-java` coordinate** — it is frozen at 1.5.1 on
Maven Central, still inside the affected `<1.10.5` range; the patched line moved
to the different `com.amazon.ion:ion-java` coordinate (incompatible package
names), so no drop-in pin works. The upstream remediation is the AWS SDK itself:
`aws-java-sdk-core` **1.12.746+ no longer depends on ion-java**. Bumping all four
`aws.java.sdk.*` properties (core/s3/sqs/sns) from 1.12.267 to 1.12.788 drops the
vulnerable ion-java from the graph entirely (confirmed removed by the post-change
scan).

---

## Not fixed — no version fix exists (stated explicitly, per instructions)

| Package | Advisory | Why no version fix |
|---|---|---|
| `org.hibernate:hibernate-core` 5.6.10.Final | GHSA-2p5w-cvg5-gc5c (CVE-2026-0603, SQL injection, HIGH) | Affected range is `>=5.2.8,<=5.6.15`; the entire Hibernate 5.6 line is vulnerable and it **ended at 5.6.15.Final** (verified on Maven Central). No 5.x fix is published — the fix lands only in Hibernate ORM 6.x/7.x, a major migration (Jakarta namespace + breaking API) that is not a version bump and would break the build. Left at 5.6.10.Final. |
| `commons-httpclient:commons-httpclient` 3.1 | GHSA-3832-9276-x7gf (CVE-2012-5783, improper cert validation) | `commons-httpclient` is EOL; 3.1 (2011) is the last release and no fixed version exists for this coordinate. The successor is a different artifact/package (`org.apache.httpcomponents:httpclient` 4.x), i.e. a code migration, not a version change. Left as-is. |
| `commons-lang:commons-lang` 2.6 | GHSA-j288-q9x7-2f5v (CVE-2025-48924, uncontrolled recursion) | Affected range `>=2.0,<=2.6`; commons-lang 2.x is EOL at 2.6 with no fixed release. The fix exists only in the separate `org.apache.commons:commons-lang3` (>=3.18) artifact/package — a migration, not a bump. (The project already ships commons-lang3 3.20.0 for its own code; the 2.6 copy is transitive.) Left as-is. |

## Not fixed — fix exists but requires an out-of-scope breaking upgrade

| Package | Advisory | Why deferred |
|---|---|---|
| `org.apache.axis2:axis2-transport-http` 1.6.4 | GHSA-wwq7-pxwc-p4rc (SSRF, MEDIUM) | Fixed in 1.8.0, but `grouper-ws` (and `grouper-ws-java-generated-client`) declare the whole Axis2 stack — `axis2-kernel`, `axis2-adb`, `axis2-transport-http`, `axis2-transport-local` — directly at 1.6.4. Axis2 modules are version-locked; bumping only `axis2-transport-http` to 1.8.0 mismatches the 1.6.4 kernel, and a full 1.6.4 → 1.8.0 stack upgrade is an API-breaking major migration that would not compile. Fixing it safely requires a coordinated Axis2 upgrade with code changes, which is beyond a version-pin remediation and conflicts with the hard requirement to keep the build passing. Left at 1.6.4 and documented; a stack-wide Axis2 upgrade is the follow-up. |
