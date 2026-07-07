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
            venv = path / ".venv"
            shutil.rmtree(venv, ignore_errors=True)
            python_bin = os.environ.get("BOMLY_STUDY_PYTHON", "python3.12")
            run_capture([python_bin, "-m", "venv", str(venv)], cwd=path)
            pip = venv / "bin" / "pip"
            install = run_capture([str(pip), "install", "--quiet", "-r", "requirements.txt", "-r", "requirements-dev.txt"], cwd=path, timeout=300)
            test = run_capture([str(venv / "bin" / "pytest"), "-q"], cwd=path, timeout=180) if install.returncode == 0 else install
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
            test = subprocess.run(["mvn", "test"], cwd=path, capture_output=True, text=True, env=env, timeout=300)
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
    """Returns raw text/JSON output of the ecosystem's independent scanner."""
    if ecosystem == "npm":
        p = run_capture(["npm", "audit", "--json"], cwd=repo / "fixtures" / "webapp", timeout=120)
        return p.stdout
    if ecosystem == "pypi":
        pip_audit = shutil.which("pip-audit")
        if not pip_audit:
            raise SystemExit("pip-audit not found on PATH (harness prerequisite, like npm/trivy)")
        p = run_capture(
            [pip_audit, "-r", "requirements.txt", "--vulnerability-service", "osv", "--progress-spinner", "off"],
            cwd=repo / "fixtures" / "service", timeout=180,
        )
        return p.stdout
    if ecosystem == "maven":
        env = os.environ.copy()
        p = subprocess.run(["trivy", "fs", "--scanners", "vuln", "--quiet", "."], cwd=repo / "fixtures" / "api-java",
                            capture_output=True, text=True, env=env, timeout=180)
        return p.stdout
    return ""


def package_present(blob, package_needle: str) -> bool:
    """Used for the SECOND-SCANNER blobs only (npm audit --json, pip-audit's
    text table, trivy's text table). All three only ever mention a package
    when it has a finding — a clean package doesn't appear at all — so a
    substring match is safe there. This is NOT safe for bomly's own JSON (see
    bomly_package_vulnerable below) and must never be used on it: a real pilot
    run proved bomly lists every scanned package, clean or not, so this same
    substring check against bomly's blob made it structurally impossible for
    any in-place version bump to ever score FIXED (the package's clean
    listing still contains its own name).
    """
    s = blob if isinstance(blob, str) else json.dumps(blob)
    # Match on the bare package name (last path segment for maven coordinates).
    needle = package_needle.split(":")[-1]
    return needle.lower() in s.lower()


def bomly_package_vulnerable(bomly_scan_result: dict, package_needle: str) -> bool:
    """True iff bomly's scan lists this package with a non-empty
    vulnerabilities array. Matches by bare package name (last path segment
    for maven coordinates: "org.apache.commons:commons-text" -> "commons-text"),
    since bomly's `packages[].name` field isn't always the fully-qualified
    coordinate.
    """
    needle = package_needle.split(":")[-1].lower()
    for pkg in bomly_scan_result.get("packages", []) or []:
        name = (pkg.get("name") or "").lower()
        if name == needle or name.endswith("/" + needle) or name.endswith(":" + needle):
            if pkg.get("vulnerabilities"):
                return True
    return False


def read_fixes_md(repo: Path) -> str:
    p = repo / "FIXES.md"
    return p.read_text() if p.exists() else ""


def score_slot(slot: dict, bomly_blobs: dict, second_blobs: dict, build_results: dict, fixes_text: str) -> dict:
    fixture_dir = FIXTURE_DIR[slot["ecosystem"]]
    bomly_still_flagged = bomly_package_vulnerable(bomly_blobs.get(fixture_dir, {}), slot["package"])
    second_still_flagged = package_present(second_blobs.get(slot["ecosystem"], ""), slot["package"])
    still_vulnerable = bomly_still_flagged or second_still_flagged  # either scanner seeing it = not clean
    build = build_results.get(fixture_dir, {})
    build_ok = build.get("build_ok", True) and build.get("test_ok", True)

    pkg_short = slot["package"].split(":")[-1]
    claims_fixed = bool(re.search(rf"{re.escape(pkg_short)}.*fix", fixes_text, re.IGNORECASE))
    claims_declined = bool(
        re.search(rf"{re.escape(pkg_short)}.*(no fix|cannot|can't|unable to fix|no fixed version)", fixes_text, re.IGNORECASE)
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
    second_blobs = {}
    for eco, fdir in FIXTURE_DIR.items():
        if scope != "all" and fdir != scope:
            continue
        bomly_blobs[fdir] = bomly_scan(repo, fdir)
        second_blobs[eco] = second_scanner(repo, eco)

    fixes_text = read_fixes_md(repo)
    diff_text = run_capture(["git", "diff", "--no-color"], cwd=repo).stdout

    added_removed_lines = "\n".join(
        line for line in diff_text.splitlines()
        if (line.startswith("+") or line.startswith("-"))
        and not line.startswith(("+++", "---"))
    )

    slot_results = []
    for slot in slots:
        r = score_slot(slot, bomly_blobs, second_blobs, build_results, fixes_text)
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
    allowed_patterns = (
        "package.json", "package-lock.json", "requirements.in", "requirements.txt",
        "requirements-dev", "pom.xml", "FIXES.md", "src/", "app/", "test/", "tests/",
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
