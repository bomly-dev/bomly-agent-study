# Attribution

This directory vendors **Dependency-Track** (https://github.com/DependencyTrack/dependency-track),
an open-source software supply chain component analysis platform, pinned at its
historical release **4.10.0** (tag `4.10.0`, 2023-12-08).

- Upstream license: Apache License 2.0 (see `LICENSE.txt` in this directory).
- Copyright: OWASP Foundation and the Dependency-Track contributors.

## Why it is here, and what was changed

This is a research fixture in a dependency-remediation study: the application
is used **as it existed at this historical release**, including its dependency
tree from that point in time. Nothing about the application code, `pom.xml`, or
dependency versions has been modified. Newer upstream releases exist; do not
treat this copy as current Dependency-Track, and do not report findings about
this copy to the Dependency-Track project.

Local changes, for the study only:
- this `ATTRIBUTION.md` file was added;
- the `docs/` directory (the project's Jekyll documentation site, ~31 MB of
  mostly images) was removed — it plays no role in building or testing the
  application.

Tests are executed as a bounded subset (selected at the study repo root's
Makefile) purely to keep per-run verification time reasonable.
