# Dependency vulnerability remediation

Application scanned: `fixtures/bigapp` (Grouper 4.x, 13-module Maven reactor,
built from `grouper-parent`). Findings were produced with the bomly MCP server
(`bomly scan --enrich --audit`). The build/test gate is `make test` at the repo
root (`mvn -B -DskipTests install` of the whole reactor); it passes before and
after these changes.

## Summary

The initial scan reported **21 vulnerable packages** (63 vulnerability
findings). After remediation, **17 packages are fully fixed** and one
(`jackson-databind`) is partially fixed (3 of its 4 CVEs). **4 findings remain
because no fixed version exists** for them (see the "No fix available" section);
these are documented, not hidden.

All fixes are version-only changes (overrides, property bumps, exclusion +
replacement). No application code was changed and no features were added.

Where a package is transitive, it is pinned in the parent
`grouper-parent/pom.xml` `<dependencyManagement>` so every module resolves the
fixed version. Where a package is a direct dependency it was bumped in place.

---

## Fixed — pinned via `grouper-parent/pom.xml` `<dependencyManagement>`

### io.netty netty-codec / netty-codec-http / netty-common / netty-handler `4.1.72.Final` → `4.1.135.Final`
- **Found:** ~20 CVEs across the Netty stack, incl. GHSA-3qp7-7mw8-wx86,
  GHSA-c653-97m9-rcg9, GHSA-x4gw-5cx5-pgmh (handler), GHSA-57rv-r2g8-2cj3,
  GHSA-f6hv-jmp6-3vwv, GHSA-pwqr-wmgm-9rr8 (codec-http), GHSA-mj4r-2hfc-f8p6
  (codec), GHSA-389x-839f-4rhx, GHSA-xq3w-v528-46rv (common), and others.
- **Changed:** imported `io.netty:netty-bom:4.1.135.Final` (scope `import`) so
  every Netty module is pinned consistently to a fixed release.
- **Why:** a BOM import keeps all Netty artifacts on the same fixed line and
  avoids version skew between the many netty-* modules present transitively.

### com.google.guava:guava `31.1-jre` → `32.0.0-jre`
- **Found:** GHSA-7g45-4rm6-3mm3 (CVE-2023-2976, temp-dir information disclosure)
  and GHSA-5mg8-w23w-74h3.
- **Changed:** pinned `32.0.0-jre` (the `-jre` variant matching the existing
  classifier; the advisory's `32.0.0-android` is the same fix line).

### com.google.oauth-client:google-oauth-client `1.33.2` → `1.33.3`
- **Found:** GHSA-hw42-3568-wj87 (IDToken/IDTokenVerifier signature bypass).
- **Changed:** pinned `1.33.3`.

### com.google.protobuf:protobuf-java `4.26.1` → `4.27.5`
- **Found:** GHSA-735f-pc8j-v9w8 (uncontrolled recursion / DoS).
- **Changed:** pinned `4.27.5`.

### com.nimbusds:nimbus-jose-jwt `9.37` → `9.37.4`
- **Found:** GHSA-gvpg-vgmx-xg6w (high) and GHSA-xwmg-2g98-w7v9 (DoS).
- **Changed:** pinned `9.37.4`.

### org.apache.james:apache-mime4j-core `0.7.2` → `0.8.10`
- **Found:** GHSA-jw7r-rxff-gv24 (temp-file information disclosure).
- **Changed:** pinned `0.8.10`.

### org.apache.neethi:neethi `3.0.2` → `3.2.2`
- **Found:** GHSA-2hfh-9h53-qc24, GHSA-g36m-9g3m-2vmp (high) and
  GHSA-287c-fxr7-3w6c — XML/DoS issues. Pulled transitively via axis2-kernel.
- **Changed:** pinned `3.2.2`.

### com.fasterxml.jackson.core:jackson-core `2.18.2` → `2.18.8`
- **Found:** GHSA-72hv-8253-57qq.
- **Changed:** added a `dependencyManagement` entry pinning jackson-core to
  `${jackson.databind}` (now 2.18.8) so the transitively-pulled core matches the
  fixed databind line.

### com.fasterxml.woodstox:woodstox-core `6.2.8` → `6.4.0`
- **Found:** GHSA-3f7h-mf4q-vrm4 (CVE-2022-40152, DoS). **Introduced by** the
  axis2 1.8.2 upgrade below (axis2 1.8.2 → axiom → woodstox-core 6.2.8); it was
  not present in the original tree.
- **Changed:** pinned the fixed `6.4.0`, so the axis2 upgrade nets no new
  vulnerability.

---

## Fixed — direct dependency version bumps in module POMs

### org.apache.commons:commons-compress `1.25.0` → `1.26.0`  (`grouper-misc/grouper-installer/pom.xml`)
- **Found:** GHSA-4265-ccf5-phj5 and GHSA-4g9r-vxhx-9pgx (DoS).
- **Changed:** bumped the pinned version to `1.26.0`.

### org.bitbucket.b_c:jose4j `0.9.3` → `0.9.6`  (`grouper-misc/grouper-box/pom.xml`)
- **Found:** GHSA-3677-xxcr-wjqv (high) and GHSA-6qvw-249j-h44c.
- **Changed:** bumped the pinned version to `0.9.6`. (box-java-sdk already had
  its own jose4j excluded, so this direct declaration governs the version.)

### org.apache.axis2:axis2-transport-http `1.6.4` → `1.8.2`  (`grouper-ws/grouper-ws/pom.xml`)
- **Found:** GHSA-wwq7-pxwc-p4rc. The fix is only in axis2 `1.8.0+`; there is no
  patch to the 1.6.x line.
- **Changed:** bumped the whole axis2 stack used by grouper-ws
  (`axis2-kernel`, `axis2-transport-http`, `axis2-transport-local`,
  `axis2-adb`) to `1.8.2` so the modules stay on a single, compatible axis2
  version. grouper-ws only references `org.apache.axis2.context.MessageContext`
  and `org.apache.axis2.transport.http.AxisServlet` (both present and
  compatible in 1.8.2); the reactor compiles cleanly. The rampart-based
  `grouper-ws-java-generated-client` module (which pins axis2 1.6.x) is **not**
  part of the `make test` reactor, so this does not affect it.
- **Note:** this upgrade pulled woodstox-core 6.2.8 transitively, remediated
  above.

---

## Fixed — exclusion + replacement (no in-line version fix possible)

### org.bouncycastle:bcprov-jdk15on / bcpkix-jdk15on `1.52` → excluded, replaced by jdk18on `1.84`  (`grouper-misc/grouper-box/pom.xml`)
- **Found:** ~19 CVEs on bcprov-jdk15on 1.52 (GHSA-2j2x-hx4g-2gf4,
  GHSA-4vhj-98r6-424h, GHSA-qcj7-g2j5-g7r3, GHSA-r97x-3g8f-gx3m,
  GHSA-rrvx-pwf8-p59p, GHSA-8xfc-gm6g-vgpv/CVE-2024-29857,
  GHSA-v435-xc8x-wvr9/CVE-2024-30171, …) and bcpkix-jdk15on 1.52
  (GHSA-4cx2-fc23-5wg6/CVE-2025-8916, GHSA-wg6q-6289-32hp/CVE-2026-5588).
  Pulled transitively via `com.box:box-java-sdk@2.17.0`.
- **Why a version bump alone does not work:** the `bcprov-jdk15on` /
  `bcpkix-jdk15on` artifacts were discontinued at **1.70** (verified on Maven
  Central). The fixes for several of these CVEs (1.78, 1.79, 1.84) only exist in
  the renamed **`jdk18on`** artifact line.
- **Changed:** excluded `bcprov-jdk15on` and `bcpkix-jdk15on` from
  `box-java-sdk`, and added explicit `bcprov-jdk18on` / `bcpkix-jdk18on`
  dependencies (version `1.84`, managed by `grouper-parent`'s existing
  `${bouncyCastle.version}`). The jdk18on artifacts expose the identical
  `org.bouncycastle.*` classes, so box-java-sdk resolves them at runtime; the
  parent already used jdk18on 1.84 elsewhere.

### software.amazon.ion:ion-java `1.0.2` → excluded from aws-java-sdk-core  (`grouper-parent/pom.xml`)
- **Found:** GHSA-264p-99wq-f4j6 (CVE-2024-21634, StackOverflow DoS). Pulled
  transitively via `com.amazonaws:aws-java-sdk-core@1.12.267`.
- **Why a version bump alone does not work:** the vulnerable GAV
  `software.amazon.ion:ion-java` was abandoned at **1.5.1** (all releases are
  still in the affected `<1.10.5` range). The fix (1.10.5+) only ships under the
  renamed GAV `com.amazon.ion:ion-java`, whose Java package differs, so it is
  not a drop-in replacement for aws-java-sdk-core's `software.amazon.ion` imports.
- **Changed:** excluded `software.amazon.ion:ion-java` from `aws-java-sdk-core`
  in the parent `dependencyManagement`. Newer AWS SDK v1 releases (e.g.
  1.12.788) drop this dependency entirely, and Grouper uses only the S3/SQS/SNS
  (JSON) protocols — not the ION serializer — so the exclusion removes the
  vulnerable artifact without affecting functionality.

---

## Partially fixed

### com.fasterxml.jackson.core:jackson-databind `2.18.2` → `2.18.8`
- **Found (4 CVEs):** GHSA-j3rv-43j4-c7qm (high), GHSA-rmj7-2vxq-3g9f (high),
  GHSA-hgj6-7826-r7m5 (medium) — **all fixed** by bumping the `jackson.databind`
  property to `2.18.8`. The fourth, **GHSA-5jmj-h7xm-6q6v (CVE-2026-54515)**,
  remains (see below).
- **Changed:** bumped property `jackson.databind` 2.18.2 → 2.18.8 (this property
  drives the parent DM entry and the module declarations).

---

## No fix available (cannot be fixed by a version change)

These remain after remediation. bomly classifies each as `no-fix-upstream`
(grype `fix state: not-fixed`): **no released version fixes the vulnerability**
within the artifact's usable line, so they are reported rather than "fixed" with
a version that does not exist.

### org.hibernate:hibernate-core `5.6.10.Final` — GHSA-2p5w-cvg5-gc5c (CVE-2026-0603, high, SQL injection)
- Affected range `>=5.2.8,<=5.6.15`; **no fixed release exists in the Hibernate
  5.x line** (5.6.15 is the last 5.6.x). A fix would require migrating to
  Hibernate 6.x (Jakarta namespace) — a major, application-breaking upgrade, not
  a version bump. Left unchanged.

### com.fasterxml.jackson.core:jackson-databind — GHSA-5jmj-h7xm-6q6v (CVE-2026-54515, medium)
- grype reports `fix state: not-fixed`; the advisory references an unreleased
  fix commit, so **no published jackson-databind version resolves it** yet
  (already on the latest 2.18.x, 2.18.8). Left as-is pending an upstream release.

### commons-httpclient:commons-httpclient `3.1` — GHSA-3832-9276-x7gf (CVE-2012-5783, medium, improper certificate validation)
- Affected range `>=3.0,<4.0`; commons-httpclient 3.1 is the **final release of
  the abandoned 3.x line — no fixed version was ever published**. The successor
  is the separate `org.apache.httpcomponents:httpclient` 4.x GAV (a code
  migration, not a version bump). Pulled transitively via grouper-installer and
  axis2-kernel. Left unchanged.

### commons-lang:commons-lang `2.6` — GHSA-j288-q9x7-2f5v (CVE-2025-48924, medium, uncontrolled recursion)
- Affected range `>=2.0,<=2.6`; **2.6 is the last-ever release of the
  `commons-lang:commons-lang` GAV — no fix exists**. The fix lives in the
  separate `org.apache.commons:commons-lang3` GAV (a code migration). Pulled
  transitively via the grouper core. Left unchanged.
