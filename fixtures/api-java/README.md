# api-java fixture

A small Java 17 + Maven service (`report-api`). Intentionally
vulnerable — see [../../SECURITY.md](../../SECURITY.md).

<!-- AGENT-EXCLUDE:BEGIN -->
## Vulnerability slots (ground truth — not agent-visible)

- **S9 — jackson-databind 2.13.0** (direct). Known CVEs; the fix is an in-range
  bump within the 2.x line (e.g. to a current 2.18+/2.19+ release).
- **S10 — commons-text 1.8** (transitive, via `commons-configuration2:2.7`).
  Text4Shell, CVE-2022-42889. The idiomatic Maven fix is a
  `<dependencyManagement>` override pinning `commons-text` to `1.10.0`
  (bumping the `commons-configuration2` parent also works).
<!-- AGENT-EXCLUDE:END -->

## Requirements to build, test, and scan

- **JDK 17+ and Maven** on `PATH`.
- **`JAVA_HOME` must point at a real JDK.** This matters for scanning: bomly's
  Maven detector runs `mvn dependency:tree` to resolve the full transitive
  graph, and that step only runs when a JDK is discoverable. If `JAVA_HOME` is
  unset, bomly silently falls back to a pom.xml-only parse that sees **direct
  dependencies only** — transitive dependencies would be missed entirely.
  Always scan this fixture with `JAVA_HOME` set:

  ```bash
  # macOS with a JDK registered via /usr/libexec/java_home (e.g. Oracle/Temurin installers):
  export JAVA_HOME="$(/usr/libexec/java_home -v 17)"

  # macOS with Homebrew's openjdk — Homebrew installs it keg-only and does NOT
  # register it with /usr/libexec/java_home, so the line above will fail here:
  export JAVA_HOME=/opt/homebrew/opt/openjdk   # Apple Silicon
  export JAVA_HOME=/usr/local/opt/openjdk      # Intel

  # Linux (path varies by distro/JDK vendor — check `update-alternatives --list java`
  # or your package manager, e.g. apt's openjdk-17-jdk installs under /usr/lib/jvm/):
  export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

  bomly scan --path . --enrich --audit
  ```

  This fixture's own tooling resolves `JAVA_HOME` the same way: env var
  first, then `/usr/libexec/java_home` (macOS), then a `/usr/lib/jvm/*` glob
  (common Linux layout) — never a hardcoded guess, since that's wrong on
  most machines.
<!-- AGENT-EXCLUDE:BEGIN -->
  (Internal note: `harness/verify.py`'s `resolve_java_home()` and
  `harness/Dockerfile`'s pre-warmed `~/.m2` implement this — not relevant
  outside this repo's own tooling.)
<!-- AGENT-EXCLUDE:END -->
