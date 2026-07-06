# Security policy

## This repository is intentionally vulnerable

This is a **research fixture**. The applications under [`fixtures/`](fixtures/)
deliberately pin dependency versions with known, published vulnerabilities so we
can measure how coding agents remediate them. This is by design.

- **Do not deploy** any application in this repository.
- **Do not copy** its dependency manifests or pinned versions into real projects.
- The vulnerabilities here are **already public** (each is tracked by an OSV /
  CVE / GHSA advisory). Nothing here is a new or undisclosed weakness.

Every package we pin is a *vulnerable* release of an otherwise-legitimate
package. We do **not** include malicious or compromised packages, install-time
attack code, or anything that would harm a machine that merely clones or
installs the fixtures for study.

## Reporting

Because the vulnerabilities are intentional and already disclosed upstream,
there is nothing to report about the fixtures themselves. If you believe
something here is unsafe *beyond* the documented intentional vulnerabilities —
for example an actual malicious package slipped in — please open an issue or
contact the maintainer, and we will remove it.

## Automated updates are disabled

Dependency auto-updates (Dependabot) are turned off
([`.github/dependabot.yml`](.github/dependabot.yml)) so the intentional pins are
not "helpfully" bumped. That is expected.
