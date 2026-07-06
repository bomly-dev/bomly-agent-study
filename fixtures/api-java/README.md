# api-java fixture

A small Java 17 + Maven service (`report-api`) used in the study. Intentionally
vulnerable — see [../../SECURITY.md](../../SECURITY.md).

## Vulnerability slots

- **S9 — jackson-databind 2.13.0** (direct). Known CVEs; the fix is an in-range
  bump within the 2.x line (e.g. to a current 2.18+/2.19+ release).
- **S10 — commons-text 1.8** (transitive, via `commons-configuration2:2.7`).
  Text4Shell, CVE-2022-42889. The idiomatic Maven fix is a
  `<dependencyManagement>` override pinning `commons-text` to `1.10.0`
  (bumping the `commons-configuration2` parent also works).

## Requirements to build, test, and scan

- **JDK 17+ and Maven** on `PATH`.
- **`JAVA_HOME` must point at a real JDK.** This matters for scanning: bomly's
  Maven detector runs `mvn dependency:tree` to resolve the full transitive
  graph, and that step only runs when a JDK is discoverable. If `JAVA_HOME` is
  unset (or `java` is only the macOS stub), bomly silently falls back to a
  pom.xml-only parse that sees **direct dependencies only** — so the transitive
  slot (S10) would be missed. Always scan this fixture with `JAVA_HOME` set:

  ```bash
  export JAVA_HOME="$(/usr/libexec/java_home 2>/dev/null || echo /opt/homebrew/opt/openjdk)"
  bomly scan --path . --enrich --audit
  ```

The study's Docker image sets `JAVA_HOME` and pre-warms `~/.m2` with
`mvn dependency:go-offline`, so scans there are deterministic and offline.
