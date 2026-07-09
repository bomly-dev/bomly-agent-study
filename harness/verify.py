#!/usr/bin/env python3
"""Mechanical, no-API-key scorer for one run's workspace.

Two entry points:
  - Inline, from run.py: verify_workspace(repo, scope, fixture_ref) is called
    against the live post-agent workspace, right before it's deleted.
  - Standalone / zero-API-key re-audit:
      harness/verify.py --from-run runs/<agent>/<condition>/<n>
    reconstructs an equivalent workspace by fresh-cloning the frozen fixture
    ref and applying that run's diff.patch, then runs the identical checks.
    No agent is re-invoked, so this costs nothing and needs no credentials —
    it only re-scores what the agent already did.

Per-slot taxonomy (see fixtures/SLOTS.yaml and cs-a-design.md):
  FIXED / FIXED_BUILD_BROKEN / ATTEMPTED_NOT_FIXED / NOT_ATTEMPTED /
  CORRECTLY_DECLINED (S6 only) / HALLUCINATED
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_capture(cmd: list[str], cwd: Path | None = None, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def load_ground_truth() -> dict:
    """The full dual-confirmed vulnerable surface per fixture, frozen at
    freeze time by scripts/gen-ground-truth.py. This is the primary scoring
    input as of v3 (2026-07-09, Ahmed): completeness is scored over every
    vulnerable package a fixture has, not a curated subset."""
    gt_path = REPO_ROOT / "fixtures" / "ground-truth.json"
    if not gt_path.exists():
        raise SystemExit(
            f"{gt_path} not found. Run scripts/gen-ground-truth.py first "
            "(see its docstring for the exact in-container invocation)."
        )
    return json.loads(gt_path.read_text())


def load_overlay() -> dict[tuple[str, str], dict]:
    """{(ecosystem, package): overlay_entry} from fixtures/SLOTS.yaml — the
    narrow hand-verified notable-case overlay (see that file's header): only
    fix_incompatible_advisory_ids (changes scoring) and
    naive_fix_breaks_build (informational) live here now."""
    slots_path = REPO_ROOT / "fixtures" / "SLOTS.yaml"
    if not slots_path.exists() or yaml is None:
        return {}
    data = yaml.safe_load(slots_path.read_text()) or {}
    return {(e["ecosystem"], e["package"]): e for e in data.get("overlay", [])}


FIXTURE_DIR = {"npm": "webapp", "pypi": "service", "maven": "api-java"}

# Frozen at fixture-freeze: the exact advisory IDs each second scanner emits
# for each package on the PRISTINE (unfixed) fixture. A slot's second scanner
# only counts as "still flagged" if it currently reports an ID that was in
# this frozen set — anything new is a post-freeze advisory, out of scope by
# pre-registration. Regenerate with scripts/gen-second-scanner-baseline.py.
BASELINE_IDS_PATH = REPO_ROOT / "scoring" / "second-scanner-baseline.json"


def load_baseline_ids() -> dict[str, dict[str, set[str]]]:
    """{ecosystem: {package: {ADVISORY_ID, ...}}}, or {} if not generated yet."""
    if not BASELINE_IDS_PATH.exists():
        return {}
    raw = json.loads(BASELINE_IDS_PATH.read_text())
    return {eco: {pkg: set(ids) for pkg, ids in pkgs.items()} for eco, pkgs in raw.items()}


def resolve_java_home() -> str:
    """Find a JDK 17+ home directory, portably.

    Inside harness/Dockerfile, JAVA_HOME is always set via ENV, so this only
    matters for local/bare-host use (e.g. `make verify-only` outside the
    container). Tries, in order: the JAVA_HOME env var (any OS); macOS's
    `/usr/libexec/java_home` (a no-op error, not a crash, on other OSes); the
    common Linux JVM install glob. No hardcoded package-manager path is used
    as a silent fallback — if nothing is found, this raises a clear,
    actionable error instead of guessing a path that may not exist on the
    caller's machine.
    """
    env_value = os.environ.get("JAVA_HOME")
    if env_value:
        return env_value

    mac = run_capture(["/usr/libexec/java_home"])
    if mac.returncode == 0 and mac.stdout.strip():
        return mac.stdout.strip()

    for candidate in sorted(Path("/usr/lib/jvm").glob("*"), reverse=True) if Path("/usr/lib/jvm").is_dir() else []:
        if (candidate / "bin" / "java").exists():
            return str(candidate)

    raise SystemExit(
        "JAVA_HOME is not set and no JDK could be auto-detected.\n"
        "Set it explicitly, e.g.:\n"
        "  macOS (Homebrew):  export JAVA_HOME=\"$(/usr/libexec/java_home)\"\n"
        "  Linux:             export JAVA_HOME=/usr/lib/jvm/<your-jdk-17>\n"
        "  Windows (WSL):     same as Linux, inside the WSL shell\n"
        "Inside harness/Dockerfile this is always pre-set — this error should "
        "only appear when running verify.py/run.py directly on the bare host."
    )


def rebuild_and_test(repo: Path, scope: str) -> dict:
    """Fresh-install rebuild + test each in-scope fixture. Returns pass/fail per app."""
    results = {}
    dirs = ["webapp", "service", "api-java"] if scope == "all" else [scope]
    for d in dirs:
        path = repo / "fixtures" / d
        if not path.exists():
            continue
        if d == "webapp":
            install = run_capture(["npm", "ci"], cwd=path, timeout=300)
            build = run_capture(["npm", "run", "build"], cwd=path, timeout=120) if install.returncode == 0 else install
            test = run_capture(["npm", "test"], cwd=path, timeout=180) if build.returncode == 0 else build
        elif d == "service":
            # Vendored CTFd 3.7.7. Commands mirror the root Makefile's
            # test-service target — deliberately duplicated here rather than
            # invoking `make`, so scoring never executes an agent-modified
            # Makefile (the workspace copy is part of the agent's writable
            # tree; diff.patch can carry Makefile edits).
            venv = path / ".venv"
            shutil.rmtree(venv, ignore_errors=True)
            python_bin = os.environ.get("BOMLY_STUDY_PYTHON", "python3.12")
            run_capture([python_bin, "-m", "venv", str(venv)], cwd=path)
            pip = venv / "bin" / "pip"
            install = run_capture([str(pip), "install", "--quiet", "-r", "requirements.txt"], cwd=path, timeout=600)
            if install.returncode == 0:
                dev_lines = [
                    l for l in (path / "development.txt").read_text().splitlines()
                    if l.strip() and not re.match(
                        r"^-r |.*(psycopg2|bandit|sphinx|pip-tools|flask_profiler|flask-debugtoolbar|pipdeptree)", l
                    )
                ]
                (path / ".dev-test.txt").write_text("\n".join(dev_lines) + "\n")
                install = run_capture([str(pip), "install", "--quiet", "-r", ".dev-test.txt"], cwd=path, timeout=600)
            test = (
                run_capture(
                    [str(venv / "bin" / "python"), "-m", "pytest", "tests/test_config.py", "tests/users",
                     "-q", "-p", "no:randomly"],
                    cwd=path, timeout=600,
                )
                if install.returncode == 0 else install
            )
            build = install
        elif d == "api-java":
            java_home = resolve_java_home()
            env = os.environ.copy()
            env["JAVA_HOME"] = java_home
            env["PATH"] = f"{java_home}/bin:" + env.get("PATH", "")
            # NOT -o (offline): a real pilot run proved that wrong. The
            # container's ~/.m2 is only pre-warmed with the FROZEN fixture's
            # original versions — any agent that successfully bumps a Maven
            # dependency (exactly the thing being verified) introduces a
            # version that was never cached, and -o has no way to fetch it.
            # The live pilot run's own result looked fine only because the
            # agent's own `mvn test` calls (with network access) had already
            # warmed that container's cache moments earlier; a standalone
            # `make verify-only` re-audit on a fresh clone has no such luck
            # and would spuriously report FIXED_BUILD_BROKEN for a
            # perfectly good fix. npm ci / pip install elsewhere in this same
            # function already use the network for exactly this reason —
            # Maven should be consistent with them, not stricter.
            #
            # Vendored Dependency-Track 4.10.0: the full suite is 186 test
            # classes (way beyond a scoring pass' budget), so run the same
            # bounded subset as the root Makefile's test-java target —
            # duplicated here rather than invoking `make`, so scoring never
            # executes an agent-modified Makefile. -P enhance: DataNucleus
            # JDO bytecode enhancement is a profile upstream, not part of
            # the default lifecycle (DEVELOPING.md, "DataNucleus Bytecode
            # Enhancement") — every @PersistenceCapable-backed test fails
            # with NucleusUserException without it.
            test = subprocess.run(
                ["mvn", "-B", "-P", "enhance", "test",
                 "-Dtest=org.dependencytrack.model.**,org.dependencytrack.util.**,org.dependencytrack.parser.**",
                 "-DfailIfNoTests=false"],
                cwd=path, capture_output=True, text=True, env=env, timeout=1800,
            )
            build = test
            install = test
        else:
            continue
        results[d] = {
            "install_ok": install.returncode == 0,
            "build_ok": build.returncode == 0,
            "test_ok": test.returncode == 0,
            "test_stdout_tail": "\n".join(test.stdout.splitlines()[-30:]),
            "test_stderr_tail": "\n".join(test.stderr.splitlines()[-30:]),
        }
    return results


def bomly_scan(repo: Path, fixture_dir: str) -> dict:
    path = repo / "fixtures" / fixture_dir
    env = os.environ.copy()
    if fixture_dir == "api-java":
        java_home = resolve_java_home()
        env["JAVA_HOME"] = java_home
        env["PATH"] = f"{java_home}/bin:" + env.get("PATH", "")
    p = subprocess.run(
        ["bomly", "scan", "--path", str(path), "--enrich", "--audit", "--format", "json"],
        capture_output=True, text=True, env=env, timeout=180,
    )
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"error": "bomly scan did not return valid JSON", "stderr": p.stderr[-2000:]}


def second_scanner(repo: Path, ecosystem: str) -> str:
    """Returns raw JSON output of the ecosystem's independent scanner.

    All three now emit JSON (not human tables): the scorer needs per-package
    advisory IDs, not just "does this package name appear anywhere", so it can
    tell "still vulnerable to the advisory this slot tracks" apart from "a
    NEWER, unrelated advisory was published against the fixed version after
    SLOTS.yaml was frozen". See extract_advisory_ids() and the frozen baseline
    in scoring/second-scanner-baseline.json.
    """
    if ecosystem == "npm":
        p = run_capture(["npm", "audit", "--json"], cwd=repo / "fixtures" / "webapp", timeout=120)
        return p.stdout
    if ecosystem == "pypi":
        # Deliberately NOT resolved via ambient PATH (shutil.which) anymore.
        # pip-audit lives in an isolated venv (harness/Dockerfile's
        # /opt/study-tools) specifically so it's invisible to bomly's own
        # pip detector, which falls back to inspecting whatever's on the
        # ambient interpreter's PATH when no project venv exists yet — a
        # real pilot run proved that fallback picks up pip-audit's own
        # dependency tree if pip-audit is ambient-installed. Same isolated
        # path for local/bare-host use (harness/.venv, created by this
        # repo's own tooling) and BOMLY_STUDY_PIP_AUDIT for anything else.
        pip_audit = (
            os.environ.get("BOMLY_STUDY_PIP_AUDIT")
            or next((p for p in ("/opt/study-tools/bin/pip-audit",) if Path(p).exists()), None)
            or shutil.which("pip-audit")
        )
        if not pip_audit:
            raise SystemExit(
                "pip-audit not found. Expected /opt/study-tools/bin/pip-audit (inside the study "
                "Docker image) or BOMLY_STUDY_PIP_AUDIT set to its path (local/bare-host use) — "
                "not ambient PATH, since that's exactly what caused bomly's own pip detector to "
                "misresolve in a real pilot run."
            )
        p = run_capture(
            [pip_audit, "-r", "requirements.txt", "--vulnerability-service", "osv",
             "--format", "json", "--progress-spinner", "off"],
            cwd=repo / "fixtures" / "service", timeout=180,
        )
        return p.stdout
    if ecosystem == "maven":
        env = os.environ.copy()
        # --skip-db-update: without it, trivy checks mirror.gcr.io for a
        # fresher DB on every single invocation, which (a) makes second-
        # scanner results non-deterministic across the run window — the
        # opposite of the frozen-ground-truth design this study relies on
        # — and (b) hung for 180s and failed outright the first time this
        # was tried against a real network, even though a same-day cached
        # DB was already on disk. The Dockerfile pre-warms this DB at
        # build time (see the trivy install step) the same way ~/.m2 is
        # pre-warmed for Maven, so this always has a DB to skip-update to.
        p = subprocess.run(
            ["trivy", "fs", "--scanners", "vuln", "--skip-db-update", "--quiet", "--format", "json", "."],
            cwd=repo / "fixtures" / "api-java",
            capture_output=True, text=True, env=env, timeout=180,
        )
        return p.stdout
    return ""


# Recognized advisory-ID shapes across all three second scanners. Used only to
# pull identifiers out of scanner output; SLOTS.yaml's own advisories are CVEs,
# but npm audit reports GHSAs (no CVE), pip-audit/OSV reports PYSEC ids plus a
# CVE+GHSA alias list, and trivy reports CVEs — so the frozen baseline stores
# whatever each scanner actually emits, and matching is a set intersection
# against that, never a cross-ecosystem CVE<->GHSA translation.
_ADVISORY_ID_RE = re.compile(r"(?:CVE-\d{4}-\d+|GHSA-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}|PYSEC-\d{4}-\d+)", re.IGNORECASE)


def extract_advisory_ids(ecosystem: str, raw: str) -> dict[str, set[str]]:
    """Parse a second scanner's JSON into {package_name: {ADVISORY_ID, ...}}.

    Package keys are exactly what the scanner emits (bare name for npm/pypi,
    "group:artifact" for trivy/maven), upper-cased advisory IDs. Returns {} on
    empty/unparseable input — a clean scan legitimately produces no findings.
    """
    out: dict[str, set[str]] = {}
    if not raw or not raw.strip():
        return out
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return out

    if ecosystem == "npm":
        # npm audit v2+: vulnerabilities keyed by package; each `via` entry is
        # either a dict (a real advisory, GHSA in its url) or a string (the
        # name of another package it's vulnerable *through*).
        for name, node in (data.get("vulnerabilities") or {}).items():
            ids: set[str] = set()
            for via in node.get("via", []):
                if isinstance(via, dict):
                    ids.update(m.group(0).upper() for m in _ADVISORY_ID_RE.finditer(via.get("url", "")))
            if ids:
                out.setdefault(name, set()).update(ids)
    elif ecosystem == "pypi":
        # pip-audit --format json: {dependencies: [{name, vulns: [{id, aliases}]}]}
        deps = data.get("dependencies", data if isinstance(data, list) else [])
        for dep in deps:
            name = (dep.get("name") or "").lower()
            ids = set()
            for v in dep.get("vulns", []) or []:
                for tok in [v.get("id", "")] + (v.get("aliases") or []):
                    ids.update(m.group(0).upper() for m in _ADVISORY_ID_RE.finditer(tok))
            if ids:
                out.setdefault(name, set()).update(ids)
    elif ecosystem == "maven":
        # trivy --format json: {Results: [{Vulnerabilities: [{VulnerabilityID, PkgName}]}]}
        for res in data.get("Results", []) or []:
            for v in res.get("Vulnerabilities", []) or []:
                name = v.get("PkgName", "")
                vid = (v.get("VulnerabilityID") or "").upper()
                if name and vid:
                    out.setdefault(name, set()).add(vid)
    return out


def _package_second_scanner_ids(reported: dict[str, set[str]], package: str) -> set[str]:
    """IDs the second scanner currently reports for this package. Tries the
    full coordinate and the bare last segment as keys (trivy uses
    "group:artifact"; npm/pip-audit use the bare name)."""
    return (
        reported.get(package)
        or reported.get(package.split(":")[-1].lower())
        or reported.get(package.split(":")[-1])
        or set()
    )



def bomly_flagged_advisory_ids(bomly_scan_result: dict, package_needle: str, tracked_ids: set[str]) -> set[str]:
    """The subset of TRACKED advisories bomly still reports for this package.
    Advisory-ID-scoped, not "does the package have any vuln at all" — a
    package fixed for its tracked CVEs may still carry a different, untracked
    advisory, and whether bomly's enrichment happens to include that untracked
    advisory depends on OSV-cache freshness, which would make scoring
    non-deterministic across the run window. A real case: a fix bumping
    jackson-databind past its 3 tracked CVEs still leaves untracked jackson
    advisories that a fresher bomly cache flags and a staler one doesn't —
    scoping to the package's own tracked advisories removes that dependence.

    Returns the matched subset (not just a bool) so the full-surface scorer
    can tell WHICH tracked advisories remain — a fixable one remaining is a
    miss, an unfixable one remaining is expected.

    Matches by bare package name (last path segment for maven coordinates),
    since bomly's `packages[].name` isn't always the fully-qualified
    coordinate; matches advisories against each vuln's `id` plus `aliases`
    (bomly reports a GHSA id and the CVE alias per vuln).
    """
    needle = package_needle.split(":")[-1].lower()
    tracked = {t.upper() for t in tracked_ids}
    flagged: set[str] = set()
    for pkg in bomly_scan_result.get("packages", []) or []:
        name = (pkg.get("name") or "").lower()
        if name == needle or name.endswith("/" + needle) or name.endswith(":" + needle):
            for v in pkg.get("vulnerabilities") or []:
                ids = {str(v.get("id", "")).upper()} | {str(a).upper() for a in (v.get("aliases") or [])}
                flagged |= ids & tracked
    return flagged


def read_fixes_md(repo: Path) -> str:
    p = repo / "FIXES.md"
    return p.read_text() if p.exists() else ""


def _owning_section(text: str, anchors: list[str]) -> str | None:
    """Return the FIXES.md section whose own subject is one of `anchors`,
    per PROMPT.md's "one entry per package" instruction — as opposed to a
    section that merely mentions the package in passing (e.g. "form-data
    (via `request`)" inside form-data's own entry, which must not count as
    request's entry). Two real conventions observed across agents: a
    top-level `- **pkg**` list item (claude) or a `## pkg` markdown heading
    (codex) — both split and matched. `anchors` should list the full
    "group:artifact" identifier before the bare short name: a real
    codex/bare/api-java entry headed its bullet with the full Maven
    coordinate (`` `ch.qos.logback:logback-core` ``), which the short name
    alone ("logback-core") doesn't match at the start of the line — it
    only matches partway through "ch.qos.logback:logback-core". Returns
    None if no section is headed by any anchor, so callers can fall back
    to whole-text proximity matching for FIXES.md that follows neither
    convention."""
    chunks = re.split(r"\n(?=[-*]\s|#{1,6}\s)", text)
    for anchor in anchors:
        heading = re.compile(
            rf"^(?:[-*]\s+|#{{1,6}}\s+)[`*_]*{re.escape(anchor)}[`*_]*\b",
            re.IGNORECASE,
        )
        for chunk in chunks:
            if heading.match(chunk.strip()):
                return chunk
    return None


def _near_after(anchor: str, phrase_pattern: str, text: str, window: int = 300) -> bool:
    """True if `phrase_pattern` appears within `window` chars after ANY
    occurrence of `anchor` in `text` — checked from every occurrence, not
    just the first. Fallback for text that doesn't follow FIXES.md's
    per-package section convention (see `_owning_section`, tried first).
    FIXES.md entries often name a package several times before its real
    justification lands (claude/mcp/webapp's uuid: the package is named 5
    times in one bullet; the decline phrase "cannot be applied here" sits in
    the window after the *second* mention, well past a naive first-match
    anchor — checked from every occurrence to catch that)."""
    for m in re.finditer(re.escape(anchor), text, re.IGNORECASE):
        if re.search(phrase_pattern, text[m.end():m.end() + window], re.IGNORECASE):
            return True
    return False


def _pkg_claims(anchors: list[str], fixed_pattern: str, declined_pattern: str, fixes_text: str) -> tuple[bool, bool]:
    """(claims_fixed, claims_declined) for one package. Prefers matching
    within the package's own FIXES.md section (unambiguous — no proximity
    bound needed once scoped); falls back to whole-text proximity matching,
    anchored on the last (shortest/broadest) of `anchors`, if the text
    doesn't have a section headed by this package."""
    section = _owning_section(fixes_text, anchors)
    if section is not None:
        scope = re.sub(r"\s+", " ", section)
        return (
            bool(re.search(fixed_pattern, scope, re.IGNORECASE)),
            bool(re.search(declined_pattern, scope, re.IGNORECASE)),
        )
    flat_text = re.sub(r"\s+", " ", fixes_text)
    fallback_anchor = anchors[-1]
    return (
        _near_after(fallback_anchor, fixed_pattern, flat_text),
        _near_after(fallback_anchor, declined_pattern, flat_text),
    )


def score_package(
    package: str,
    ecosystem: str,
    gt_entry: dict,
    overlay_entry: dict | None,
    bomly_blob: dict,
    second_ids: dict[str, set[str]],
    baseline_ids: dict,
    build_ok: bool,
    fixes_text: str,
    added_removed_lines: str,
) -> dict:
    """Score ONE package against the full vulnerable-surface ground truth
    (v3, 2026-07-09). Every dual-confirmed vulnerable package is scored —
    completeness over the whole set, not a curated ~10 — see
    fixtures/ground-truth.json / fixtures/GROUND_TRUTH.md.

    fix_incompatible_advisory_ids (fixtures/SLOTS.yaml overlay) move an
    advisory from fixable to unfixable-in-practice: bomly correctly reports a
    fix exists upstream, but it's been hand-verified not to actually work in
    this app (a version conflict or major-jump a scanner can't see). Treated
    exactly like a genuine no-fix for scoring — explicitly declining it is
    correct, silently leaving it is not, but it's never counted as a "miss".
    """
    fixture_dir = FIXTURE_DIR[ecosystem]
    overlay_entry = overlay_entry or {}
    fix_incompatible = {a.upper() for a in overlay_entry.get("fix_incompatible_advisory_ids", [])}

    fixable_ids = {
        a["id"] for a in gt_entry["advisories"] if a.get("fix_state") == "fixed"
    } - fix_incompatible
    unfixable_ids = {
        a["id"] for a in gt_entry["advisories"] if a.get("fix_state") != "fixed"
    } | fix_incompatible
    tracked = fixable_ids | unfixable_ids

    bomly_flagged = bomly_flagged_advisory_ids(bomly_blob, package, tracked)
    reported = _package_second_scanner_ids(second_ids.get(ecosystem, {}), package)
    if ecosystem in ("pypi", "maven"):
        # trivy's VulnerabilityID and pip-audit/OSV's id+aliases both expose
        # the CVE directly, so match the tracked set and ignore every other
        # advisory on the same package (OSV-cache-freshness independence —
        # same reasoning as the old score_slot).
        second_flagged = reported & tracked
    else:
        # npm audit reports only GHSA ids (no CVE, no alias list). Fall back
        # to the frozen freeze-era GHSA set for the package
        # (scoring/second-scanner-baseline.json) so a GHSA published after
        # freeze can't misscore a real fix. If no baseline exists, over-flag
        # (safe) rather than silently pass.
        baseline = _package_second_scanner_ids(baseline_ids.get(ecosystem, {}), package)
        second_flagged = (reported & baseline) if baseline else reported & tracked

    still_flagged = bomly_flagged | second_flagged  # either scanner seeing an id = not clean for that id
    fixable_remaining = fixable_ids & still_flagged
    unfixable_remaining = unfixable_ids & still_flagged
    fixable_resolved = fixable_ids - fixable_remaining
    unfixable_resolved = unfixable_ids - unfixable_remaining  # bonus: agent found a real solution

    pkg_short = package.split(":")[-1]
    # Matched within the package's own FIXES.md bullet where one exists
    # (PROMPT.md requires "one entry per package"), so a co-mention in a
    # NEIGHBORING package's bullet ("form-data (via `request`) ... Fixes
    # ...") can't satisfy request's own claims_fixed, and a justification
    # anchored past a naive fixed-width window (claude/mcp/webapp's uuid —
    # named 5x in one bullet; its decline phrase sits well past a 150-char
    # window from the first mention) is still found because the whole
    # section is in scope. See `_pkg_claims` / `_owning_section`. Anchors
    # try the full "group:artifact" identifier before the bare short name —
    # a real codex/bare/api-java entry headed its bullet with the full
    # Maven coordinate, which the short name alone doesn't match at the
    # start of the line.
    #
    # Phrase list grown from real transcripts, not invented up front — see
    # git history for the pilot run that needed "no version-only remediation
    # exists" added (claims_fixed's "fix" substring otherwise wins on
    # "fix_state" in an unrelated bomly-status mention). "no compatible
    # fix(ed)", "did not (keep|change|apply)", and "version-only remediation"
    # (without requiring a leading "no") added from codex/mcp/webapp's uuid
    # entry, which declines correctly but in wording ("Did not keep a
    # version override... No compatible fixed uuid version exists...
    # outside version-only remediation") none of the earlier phrases caught.
    # "remains unchanged"/"left unchanged" added from codex/bare/api-java's
    # logback-core entry ("...so the version remains unchanged to keep the
    # build passing") — a correct decline the earlier list still missed.
    claims_fixed, claims_declined = _pkg_claims(
        [package, pkg_short],
        r"fix",
        r"(no fix|cannot|can't|unable to fix|no fixed version|no compatible fix|"
        r"did not (?:keep|change|apply)|version-only remediation|"
        r"remains unchanged|left unchanged)",
        fixes_text,
    )
    touched = bool(re.search(r"\b" + re.escape(pkg_short) + r"\b", added_removed_lines, re.IGNORECASE))

    if not fixable_ids:
        # Pure no-fix package (or every advisory was overlay-marked
        # incompatible): the only correct outcomes are an explicit decline or
        # silence. Any claim of a version fix is a hallucination regardless
        # of what the scanners currently see. claims_declined MUST be
        # checked before claims_fixed — see score_package's proximity-bound
        # comment above; a decline mentioning "fix" in "no fix available"
        # must not lose to the generic claims_fixed substring match.
        if claims_declined:
            outcome = "CORRECTLY_DECLINED"
        elif claims_fixed:
            outcome = "HALLUCINATED"
        else:
            outcome = "NOT_ATTEMPTED"
    elif not fixable_remaining:
        # Every fixable advisory is gone.
        if unfixable_remaining and not (claims_declined or claims_fixed):
            # Fixable part done, but a genuinely-unfixable advisory was left
            # with no acknowledgment at all — resolved in substance, but
            # silent on the part that needed an explicit decline. Recorded
            # distinctly so the writeup can tell "complete and honest" apart
            # from "complete but silent" without a whole new bucket. Found
            # via a real re-score (claude/mcp/service, N=1 ladder pilot)
            # that this branch originally didn't check build_ok at all,
            # unlike the sibling RESOLVED/RESOLVED_BUILD_BROKEN branch below
            # — silently dropping whether the build was actually green.
            outcome = "RESOLVED_SILENT_ON_UNFIXABLE" if build_ok else "RESOLVED_SILENT_ON_UNFIXABLE_BUILD_BROKEN"
        else:
            outcome = "RESOLVED" if build_ok else "RESOLVED_BUILD_BROKEN"
    else:
        # At least one fixable advisory remains. claims_declined MUST be
        # checked before claims_fixed — a real regression, caught by a real
        # re-score (claude/mcp/webapp's uuid: FIXES.md explicitly and
        # correctly explains uuid can't be bumped without breaking request's
        # legacy `require('uuid/v4')` import, but also says "a fix exists
        # (11.1.1)" and "no fixed version" nearby, so claims_fixed's naive
        # "<package>.*fix" match won on priority and scored a careful,
        # justified decline as HALLUCINATED. This is the exact same lesson
        # already applied to the no-fix branch above and to the old
        # score_slot() this replaced (see git history, S3/S6) — it just
        # didn't get carried over to this branch during the full-surface
        # rewrite.
        if claims_declined:
            # Declining a package that genuinely has a fixable advisory
            # remaining is a miss dressed as a decline, not a correct one —
            # distinct from CORRECTLY_DECLINED (only valid when nothing
            # fixable remains). Still recorded as a real miss, just labeled
            # accurately instead of as a fabricated-success hallucination.
            outcome = "INCORRECTLY_DECLINED"
        elif claims_fixed:
            outcome = "HALLUCINATED"  # claimed fixed, scanners disagree
        else:
            outcome = "ATTEMPTED_NOT_FIXED" if touched else "NOT_ATTEMPTED"

    return {
        "package": package,
        "ecosystem": ecosystem,
        "outcome": outcome,
        "fixable_total": len(fixable_ids),
        "fixable_resolved": len(fixable_resolved),
        "fixable_remaining_ids": sorted(fixable_remaining),
        "unfixable_total": len(unfixable_ids),
        "unfixable_remaining_ids": sorted(unfixable_remaining),
        "unfixable_resolved_bonus_ids": sorted(unfixable_resolved),
        "build_ok": build_ok,
    }


def verify_workspace(repo: Path, scope: str, fixture_ref: str = "HEAD") -> dict:
    ground_truth = load_ground_truth()
    overlay = load_overlay()
    fixtures = [scope] if scope != "all" else list(FIXTURE_DIR.values())

    build_results = rebuild_and_test(repo, scope)

    bomly_blobs = {}
    second_ids = {}
    for eco, fdir in FIXTURE_DIR.items():
        if fdir not in fixtures:
            continue
        bomly_blobs[fdir] = bomly_scan(repo, fdir)
        second_ids[eco] = extract_advisory_ids(eco, second_scanner(repo, eco))

    baseline_ids = load_baseline_ids()

    fixes_text = read_fixes_md(repo)
    diff_text = run_capture(["git", "diff", "--no-color"], cwd=repo).stdout
    added_removed_lines = "\n".join(
        line for line in diff_text.splitlines()
        if (line.startswith("+") or line.startswith("-"))
        and not line.startswith(("+++", "---"))
    )
    touched_files = {l[6:] for l in diff_text.splitlines() if l.startswith("+++ b/")}

    package_results = []
    regressions: list[dict] = []
    for fdir in fixtures:
        eco = {v: k for k, v in FIXTURE_DIR.items()}[fdir]
        gt = ground_truth["fixtures"].get(fdir, {}).get("packages", {})
        build = build_results.get(fdir, {})
        build_ok = build.get("build_ok", True) and build.get("test_ok", True)
        bomly_blob = bomly_blobs.get(fdir, {})

        for package, gt_entry in sorted(gt.items()):
            r = score_package(
                package, eco, gt_entry, overlay.get((eco, package)),
                bomly_blob, second_ids, baseline_ids, build_ok, fixes_text, added_removed_lines,
            )
            package_results.append(r)

        # Regressions: a package whose version line was actually TOUCHED by
        # the diff, now flagged (by either scanner) for an advisory ID that
        # was never in this package's ground-truth set at all — a version
        # change the agent made introduced a DIFFERENT vulnerability, not a
        # remaining/known one. Scoped to touched packages specifically so
        # ordinary OSV drift on packages the agent never went near (a new
        # advisory published on an untouched, already-frozen package during
        # the run window) never gets misread as agent-caused — same
        # discipline as the advisory-ID-scoped baseline elsewhere in this
        # file.
        known_ids_by_pkg = {
            pkg: {a["id"] for a in entry["advisories"]} | {al for a in entry["advisories"] for al in a["aliases"]}
            for pkg, entry in gt.items()
        }
        for pkg_key, ids in second_ids.get(eco, {}).items():
            bare = pkg_key.split(":")[-1].split("/")[-1].lower()
            if bare not in known_ids_by_pkg:
                continue
            if not any(bare in f.lower() for f in touched_files):
                continue
            new_ids = ids - known_ids_by_pkg[bare]
            if new_ids:
                regressions.append({"package": bare, "ecosystem": eco, "new_advisory_ids": sorted(new_ids)})

    fixable_total = sum(p["fixable_total"] for p in package_results)
    fixable_resolved = sum(p["fixable_resolved"] for p in package_results)

    return {
        "scope": scope,
        "fixture_ref": fixture_ref,
        "build_results": build_results,
        "packages": package_results,
        "completeness": (fixable_resolved / fixable_total) if fixable_total else None,
        "fixable_total": fixable_total,
        "fixable_resolved": fixable_resolved,
        "regressions": regressions,
        "unrelated_changes_flag": _looks_unrelated(diff_text),
    }


def _looks_unrelated(diff_text: str) -> bool:
    # A real pilot run flagged legitimate test-file updates as "unrelated"
    # (fixtures/service/tests/test_auth.py, fixtures/webapp/test/importer.test.js)
    # — needed because PyJWT's 1.x->2.x migration and the importer's move off
    # `request` both required matching test updates, which the task prompt
    # explicitly allows ("keep tests passing"). Maven's src/test/java/... was
    # already covered by "src/"; webapp's top-level test/ and service's tests/
    # were the gap.
    # v2 real-world fixtures widen the legitimate-edit surface: CTFd's
    # application code lives under fixtures/service/CTFd/ (not src/ or
    # app/), with migrations/ and manage.py at its root, and its dev deps in
    # development.txt; Dependency-Track keeps everything under src/ and
    # pom.xml, already covered.
    allowed_patterns = (
        "package.json", "package-lock.json", "requirements.in", "requirements.txt",
        "requirements-dev", "development.txt", "pom.xml", "FIXES.md",
        "src/", "app/", "test/", "tests/", "CTFd/", "migrations/", "manage.py",
    )
    changed_files = [l[6:] for l in diff_text.splitlines() if l.startswith("+++ b/")]
    return any(not any(p in f for p in allowed_patterns) for f in changed_files)


def verify_from_run(run_dir: Path) -> dict:
    """Zero-API-key re-audit: fresh-clone the frozen ref, apply diff.patch, score."""
    meta = json.loads((run_dir / "meta.json").read_text())
    timing_path = run_dir / "timing.json"
    timing = json.loads(timing_path.read_text()) if timing_path.exists() else {}
    diff_path = run_dir / "diff.patch"
    workspace = Path(tempfile.mkdtemp(prefix="bomly-verify-only-"))
    try:
        repo = workspace / "repo"
        subprocess.run(["git", "clone", "--quiet", str(REPO_ROOT), str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "checkout", "--quiet", meta["fixture_ref"]], check=True)
        if diff_path.stat().st_size > 0:
            subprocess.run(["git", "-C", str(repo), "apply", str(diff_path.resolve())], check=True)
        fixes_src = run_dir / "FIXES.md"
        if fixes_src.exists():
            shutil.copy(fixes_src, repo / "FIXES.md")
        result = verify_workspace(repo, meta.get("scope", "all"), fixture_ref=meta["fixture_ref"])
        # Reconstruct run_meta from meta.json/timing.json — verify_workspace()
        # itself has no notion of which run it's scoring, only run.py's
        # inline path (right after a live run) sets this normally. Missing
        # this here silently dropped agent/condition/run_number/mcp_calls
        # from every run rescored via `make verify-only`, which then went
        # missing from aggregate.py's CSV too (found when the aggregated
        # results showed blank agent/condition columns for exactly the runs
        # that had been rescored and promoted this way).
        result["run_meta"] = {
            "agent": meta.get("agent"),
            "condition": meta.get("condition"),
            "run_number": meta.get("run_number"),
            "wall_seconds": timing.get("wall_seconds"),
            "timeout": timing.get("timeout", meta.get("timeout")),
            "turns": timing.get("turns"),
            "tool_calls": timing.get("tool_calls"),
            "mcp_calls": timing.get("mcp_calls"),
            "tokens": timing.get("tokens"),
            "cost_usd": timing.get("cost_usd"),
            "mcp_tool_errors": meta.get("mcp_tool_errors", []),
        }
        return result
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-run", required=True, help="runs/<agent>/<condition>/<n>")
    args = ap.parse_args()
    run_dir = Path(args.from_run)
    result = verify_from_run(run_dir)
    print(json.dumps(result, indent=2))
    (run_dir / "result.rescored.json").write_text(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
