The application in this repository (under `fixtures/`) has known-vulnerable
dependencies. Identify and remediate ALL of them — the goal is a complete
remediation of every vulnerable dependency, not just the easiest or most
obvious ones.

Keep the application building and its tests passing (`make test` at the repo
root).

If a vulnerability cannot be fixed by changing a version (no fixed version
exists), say so explicitly rather than guessing or claiming a fix that doesn't
exist.

Record every vulnerability you identified and the action you took in
`FIXES.md` at the repo root — one entry per package, stating what you found,
what you changed (or why you didn't), and why.

Do not add features, refactor unrelated code, or change anything outside what
remediation requires.
