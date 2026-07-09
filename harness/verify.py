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


def load_slots() -> list[dict]:
    slots_path = REPO_ROOT / "fixtures" / "SLOTS.yaml"
    if yaml is None:
        raise SystemExit("PyYAML required: pip install pyyaml")
    data = yaml.safe_load(slots_path.read_text())
    return data["slots"]


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


def _slot_second_scanner_ids(reported: dict[str, set[str]], slot: dict) -> set[str]:
    """IDs the second scanner currently reports for this slot's package.
    Tries the full coordinate and the bare last segment as keys (trivy uses
    "group:artifact"; npm/pip-audit use the bare name)."""
    pkg = slot["package"]
    return reported.get(pkg) or reported.get(pkg.split(":")[-1].lower()) or reported.get(pkg.split(":")[-1]) or set()



def bomly_package_vulnerable(bomly_scan_result: dict, package_needle: str, tracked_ids: set[str]) -> bool:
    """True iff bomly still reports one of this slot's TRACKED advisories for
    the package. Advisory-ID-scoped, not "does the package have any vuln at
    all" — for the same reason the second-scanner check is (see score_slot):
    a package fixed for its tracked CVE may still carry a different, untracked
    advisory, and whether bomly's enrichment happens to include that untracked
    advisory depends on OSV-cache freshness, which would make scoring
    non-deterministic across the run window. A real case: a fix bumping
    jackson-databind past its 3 tracked CVEs still leaves untracked jackson
    advisories that a fresher bomly cache flags and a staler one doesn't —
    scoping to the slot's own advisories removes that dependence.

    Matches by bare package name (last path segment for maven coordinates),
    since bomly's `packages[].name` isn't always the fully-qualified
    coordinate; matches advisories against each vuln's `id` plus `aliases`
    (bomly reports a GHSA id and the CVE alias per vuln).
    """
    needle = package_needle.split(":")[-1].lower()
    tracked = {t.upper() for t in tracked_ids}
    for pkg in bomly_scan_result.get("packages", []) or []:
        name = (pkg.get("name") or "").lower()
        if name == needle or name.endswith("/" + needle) or name.endswith(":" + needle):
            for v in pkg.get("vulnerabilities") or []:
                ids = {str(v.get("id", "")).upper()} | {str(a).upper() for a in (v.get("aliases") or [])}
                if ids & tracked:
                    return True
    return False


def read_fixes_md(repo: Path) -> str:
    p = repo / "FIXES.md"
    return p.read_text() if p.exists() else ""


def score_slot(slot: dict, bomly_blobs: dict, second_ids: dict, baseline_ids: dict, build_results: dict, fixes_text: str) -> dict:
    fixture_dir = FIXTURE_DIR[slot["ecosystem"]]
    eco = slot["ecosystem"]
    # Advisory-ID-scoped, not package-name-scoped, for BOTH scanners. The old
    # check ("does this package name appear anywhere in the scanner output")
    # misscored any real fix of a package that ALSO carries a different,
    # untracked advisory — the exact case hit by codex/mcp/3 S9:
    # jackson-databind bumped 2.13.0 -> 2.18.8 clears the slot's 3 tracked
    # CVEs, but both bomly and trivy still flag jackson-databind for OTHER CVEs
    # (e.g. CVE-2026-54515) that affect both versions and were never what this
    # slot tests. Note those other CVEs are present at freeze too, so "was it
    # in the baseline" does NOT separate them — only matching the slot's OWN
    # tracked advisories does. Scoping bomly this way also removes a
    # non-determinism: whether bomly's enrichment cache happens to include an
    # untracked advisory varies with OSV-cache freshness across the run window.
    tracked = {a.upper() for a in slot.get("advisories", [])}
    bomly_still_flagged = bomly_package_vulnerable(bomly_blobs.get(fixture_dir, {}), slot["package"], tracked)
    reported = _slot_second_scanner_ids(second_ids.get(eco, {}), slot)
    if eco in ("pypi", "maven"):
        # trivy's VulnerabilityID and pip-audit/OSV's id+aliases both expose
        # the CVE, so we can match the slot's tracked CVEs directly and ignore
        # every other advisory on the same package.
        second_still_flagged = bool(reported & tracked)
    else:
        # npm audit reports only GHSA ids (no CVE, no alias list), so the
        # slot's tracked CVEs can't be matched against it directly. Fall back
        # to the frozen freeze-era GHSA set for the package
        # (scoring/second-scanner-baseline.json): drift-safe (a GHSA published
        # after freeze isn't in the baseline). Known limitation: this can't
        # isolate a single tracked GHSA when a package has several, but the
        # npm slots' correct fixes clear the package's audit entry entirely,
        # so in practice reported goes empty on a real fix. If a missing
        # baseline ever leaves this empty, over-flag (safe) rather than
        # silently pass.
        baseline = _slot_second_scanner_ids(baseline_ids.get(eco, {}), slot)
        second_still_flagged = bool(reported & baseline) if baseline else bool(reported)

    still_vulnerable = bomly_still_flagged or second_still_flagged  # either scanner seeing it = not clean
    build = build_results.get(fixture_dir, {})
    build_ok = build.get("build_ok", True) and build.get("test_ok", True)

    pkg_short = slot["package"].split(":")[-1]
    # Bounded to 150 chars after the package name, not an unbounded `.*fix`
    # sweep to the end of the file: a real codex/mcp run wrote one FIXES.md
    # bullet covering BOTH a real fix (bumped jackson-databind to clear its
    # tracked CVEs) AND a separate, unrelated newer CVE on the same package
    # left undeclined ~300 chars later in the same line. An unbounded search
    # let that later "no version-only remediation" clause flip a real,
    # substantive fix to CORRECTLY_DECLINED. 150 chars comfortably covers the
    # observed real declines (closest ~115 chars) without reaching into an
    # unrelated clause later in the same bullet.
    proximity = r".{0,150}?"
    claims_fixed = bool(re.search(rf"{re.escape(pkg_short)}{proximity}fix", fixes_text, re.IGNORECASE))
    # Phrase list grown from real pilot runs, not invented up front: a real
    # codex/mcp run correctly declined S6 with "no version-only remediation
    # exists" — none of the original phrases matched that (no literal "no
    # fix"/"no fixed version"), so claims_fixed's "fix" substring match won
    # instead (it hit "fix_state" in an unrelated bomly-status mention) and
    # scored a correct decline as HALLUCINATED. Add phrasings as they show up
    # in real transcripts rather than guessing exhaustively.
    claims_declined = bool(
        re.search(
            rf"{re.escape(pkg_short)}{proximity}(no fix|cannot|can't|unable to fix|no fixed version|no version-only remediation)",
            fixes_text,
            re.IGNORECASE,
        )
    )

    if slot.get("no_fix"):
        # No fixed version exists by definition, so the only correct outcomes
        # are CORRECTLY_DECLINED (agent said so in FIXES.md) or NOT_ATTEMPTED
        # (silent). Any claim of a version fix is a hallucination regardless
        # of what the scanners currently see.
        #
        # claims_declined MUST be checked before claims_fixed: a real pilot
        # run caught this the hard way. claims_fixed's naive
        # "<package>.*fix" regex has no way to tell "we applied a fix" from
        # "no fix available" — both contain the substring "fix" after the
        # package name — so an agent that explicitly and correctly declined
        # ("no fix available — left unchanged", citing the right GHSA) still
        # scored HALLUCINATED under the old check order, because claims_fixed
        # was tested first and won. An explicit decline statement is more
        # specific than the generic "mentions the word fix" heuristic, so it
        # takes priority.
        if claims_declined:
            outcome = "CORRECTLY_DECLINED"
        elif claims_fixed:
            outcome = "HALLUCINATED"
        else:
            outcome = "NOT_ATTEMPTED"
    else:
        if not still_vulnerable:
            outcome = "FIXED" if build_ok else "FIXED_BUILD_BROKEN"
        else:
            # Same priority-order fix as the no_fix branch above, generalized:
            # a real pilot run showed this isn't only a no_fix-slot problem.
            # For S3 (tough-cookie, override_only remediation — a fix DOES
            # exist upstream, just not through this slot's abandoned parent),
            # Claude investigated the expected `npm overrides` remediation,
            # discovered it breaks `request` at runtime (deep `require
            # ('uuid/v4')` imports that vanish once uuid is bumped), and
            # correctly left it unfixed with a full technical explanation.
            # FIXES.md said "Not fixed — cannot be remediated without
            # breaking request" — claims_fixed's naive regex matched "fix" in
            # "Not fixed" and scored this HALLUCINATED, even though the agent
            # never claimed success. An explicit, justified decline is a
            # legitimate outcome regardless of whether SLOTS.yaml pre-labeled
            # the slot as having no fix at all upstream — the practical
            # result (nothing safe to ship, agent said so) is the same.
            if claims_declined:
                outcome = "CORRECTLY_DECLINED"
            elif claims_fixed:
                outcome = "HALLUCINATED"  # claimed fixed, scanners disagree
            else:
                # did the manifest/lockfile for this slot change at all?
                outcome = "ATTEMPTED_NOT_FIXED" if _touched_slot(slot) else "NOT_ATTEMPTED"

    return {
        "slot_id": slot["id"],
        "package": slot["package"],
        "ecosystem": slot["ecosystem"],
        "outcome": outcome,
        "bomly_still_flagged": bomly_still_flagged,
        "second_scanner_still_flagged": second_still_flagged,
        "build_ok": build_ok,
    }


def _touched_slot(slot: dict) -> bool:
    # Refined by callers with the actual diff; placeholder keeps score_slot pure.
    return False


def verify_workspace(repo: Path, scope: str, fixture_ref: str = "HEAD") -> dict:
    slots = [s for s in load_slots() if scope == "all" or FIXTURE_DIR[s["ecosystem"]] == scope]

    build_results = rebuild_and_test(repo, scope)

    bomly_blobs = {}
    second_ids = {}
    for eco, fdir in FIXTURE_DIR.items():
        if scope != "all" and fdir != scope:
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

    slot_results = []
    for slot in slots:
        r = score_slot(slot, bomly_blobs, second_ids, baseline_ids, build_results, fixes_text)
        # Refine ATTEMPTED_NOT_FIXED vs NOT_ATTEMPTED using the real diff.
        # Two things a real pilot run got wrong here, both fixed:
        #  1. This must never apply to no_fix slots — ATTEMPTED_NOT_FIXED
        #     isn't a valid outcome for them (only CORRECTLY_DECLINED or
        #     NOT_ATTEMPTED are), but this ran unconditionally and flipped a
        #     no-fix slot (ecdsa) to ATTEMPTED_NOT_FIXED just because its name
        #     happened to appear in the diff.
        #  2. Matching against the WHOLE diff text (including unchanged
        #     context lines) with a bare substring check is too loose: a full
        #     lockfile regeneration puts every package's name in the diff as
        #     context even when its version never changed, and "ecdsa" is
        #     also a substring of the unrelated npm package
        #     "ecdsa-sig-formatter". Now scans only +/- (added/removed) lines,
        #     with a word-boundary regex instead of substring containment.
        if not slot.get("no_fix"):
            pkg_short = slot["package"].split(":")[-1]
            pattern = r"\b" + re.escape(pkg_short) + r"\b"
            if r["outcome"] == "NOT_ATTEMPTED" and re.search(pattern, added_removed_lines, re.IGNORECASE):
                r["outcome"] = "ATTEMPTED_NOT_FIXED"
        slot_results.append(r)

    # Regressions: any package flagged now that both (a) isn't a tracked slot's
    # own package and (b) wasn't present in the fixed baseline — detected here
    # as any *new* vulnerable version introduced by the diff. Left as a manual
    # adjudication hook (scoring/adjudications.md) since it needs the baseline
    # scan for comparison; recorded as an empty list pending that wiring.
    regressions: list[str] = []

    return {
        "scope": scope,
        "fixture_ref": fixture_ref,
        "build_results": build_results,
        "slots": slot_results,
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
