# Attribution

This directory vendors **CTFd** (https://github.com/CTFd/CTFd), an open-source
capture-the-flag platform, pinned at its historical release **3.7.7**
(commit `ce098c38ffc10e881a8ce6f5361b7c54d52c369d`, 2025-04-14).

- Upstream license: Apache License 2.0 (see `LICENSE` in this directory).
- Copyright: CTFd LLC and the CTFd contributors.

## Why it is here, and what was changed

This is a research fixture in a dependency-remediation study: the application
is used **as it existed at this historical release**, including its pinned
dependency set from that point in time. Nothing about the application code or
its dependency pins has been modified. Newer upstream releases exist; do not
treat this copy as current CTFd, and do not report findings about this copy to
the CTFd project.

Local additions, for the study only:
- this `ATTRIBUTION.md` file.

Tests are executed as a bounded subset (selected at the study repo root's
Makefile) purely to keep per-run verification time reasonable.
