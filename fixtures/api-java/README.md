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
  unset, bomly silently falls back to a pom.xml-only parse that sees **direct
  dependencies only** — so the transitive slot (S10) would be missed. Always
  scan this fixture with `JAVA_HOME` set:

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

  `harness/verify.py`'s `resolve_java_home()` tries `JAVA_HOME`, then
  `/usr/libexec/java_home` (macOS), then a `/usr/lib/jvm/*` glob (common
  Linux layout) — but never guesses a specific path silently. If none of
  those resolve, it raises a clear error rather than picking one machine's
  path at random (that used to be a bug here: an earlier version hardcoded
  the Apple-Silicon-Homebrew path as a fallback, which is wrong on every
  other machine).

The study's Docker image (`harness/Dockerfile`) sets `JAVA_HOME` itself and
pre-warms `~/.m2` with `mvn dependency:go-offline` at build time, so scans
*inside the container* are deterministic and need no local JDK setup at all —
the guidance above is only for running this fixture directly on your host.
