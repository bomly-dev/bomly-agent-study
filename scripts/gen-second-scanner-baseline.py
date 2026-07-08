#!/usr/bin/env python3
"""Freeze the second scanners' advisory-ID baseline for the PRISTINE fixtures.

Writes scoring/second-scanner-baseline.json: {ecosystem: {package: [ids]}} —
exactly the advisory IDs npm audit / pip-audit / trivy each report for each
package on the unfixed fixture tree, at freeze time. The scorer
(harness/verify.py) counts a slot's second scanner as "still flagged" only if
it currently reports an ID from this frozen set, so a NEWER advisory published
against a fixed version after freeze can't misscore a real fix (see
scoring/adjudications.md, codex/mcp/3 S9 for the case this prevents).

Run this from a CLEAN checkout of the frozen fixture tag, inside the study
Docker image (so scanner versions match the run environment):

  docker run --rm -v "$PWD:/work/bomly-agent-study" -w /work/bomly-agent-study \
    -e BOMLY_STUDY_PIP_AUDIT=/opt/study-tools/bin/pip-audit \
    bomly-agent-study:harness \
    bash -lc 'cd fixtures/webapp && npm ci --silent >/dev/null 2>&1; cd /work/bomly-agent-study \
      && /opt/study-tools/bin/python scripts/gen-second-scanner-baseline.py'

Regenerate whenever the fixtures or the pinned scanner versions change, and
re-freeze the result alongside SLOTS.yaml.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "harness"))
import verify  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    out: dict[str, dict[str, list[str]]] = {}
    for eco in ("npm", "pypi", "maven"):
        raw = verify.second_scanner(REPO_ROOT, eco)
        ids = verify.extract_advisory_ids(eco, raw)
        out[eco] = {pkg: sorted(v) for pkg, v in sorted(ids.items())}
        print(f"{eco}: {len(out[eco])} packages with findings", file=sys.stderr)

    dest = REPO_ROOT / "scoring" / "second-scanner-baseline.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {dest.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
