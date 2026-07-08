#!/usr/bin/env python3
"""Run one agent+condition end to end, in an isolated workspace.

Isolation, per fixture (see ../cs-a-design.md and TRACKER CS-A2):
  - Fresh workspace per run, never reused, never a shared worktree — but NOT
    a plain `git clone` of this repo. A real pilot run proved that wrong:
    Claude Code read fixtures/SLOTS.yaml (the scorer's ground-truth answer
    key) on its own initiative, and declined to use it — but the fixture
    repo genuinely does ship its own answer key to whatever clones it,
    regardless of whether that particular model chose not to exploit it. See
    AGENT_EXCLUDED_PATHS and fresh_clone() below: the agent's workspace is a
    history-free snapshot (`git archive`, not `git clone`) with the
    answer key, the scoring engine (harness/), both conditions' instructions
    (prompts/), and every other run's output (runs/, runs-pilot/) removed
    before the agent ever sees the directory.
  - Fresh, EMPTY per-run config directories for the agent CLI
    (CLAUDE_CONFIG_DIR / CODEX_HOME) so conversation history, project-trust
    decisions, and MCP registrations never carry across runs, and never touch
    the operator's real ~/.claude or ~/.codex.
  - No session-resume flags are ever passed to the agent CLI — every
    invocation is a brand-new single-shot conversation.
  - The bomly MCP server (mcp condition only) is never a separately-managed
    process here: prompts/mcp-config.json (Claude) / `codex mcp add` (Codex)
    use the stdio transport, so the AGENT CLI ITSELF spawns `bomly mcp serve`
    as its own child subprocess for the duration of that one invocation. It
    cannot outlive the run or be shared across runs — the client owns it.
  - Credentials — the two agents work differently here, corrected after a
    real pilot run proved the original design wrong for Claude (see
    ../CREDENTIALS.md for the full story):
      * Claude Code: subscription-based auth is `CLAUDE_CODE_OAUTH_TOKEN`, an
        environment variable produced once via `claude setup-token` — NOT a
        directory-based credential. (The original design tried copying
        `.claude.json` out of a mounted CLAUDE_CONFIG_DIR template; that file
        turned out to hold zero auth state — Claude Code's OAuth session
        normally lives in the macOS Keychain, which doesn't exist in a Linux
        container, and `setup-token` exists specifically to produce a
        portable env-var token instead.) Falls back to ANTHROPIC_API_KEY if
        the token isn't set. Either way: inherited as an environment
        variable only, never written to any file under the workspace.
      * Codex: subscription-based auth genuinely IS file-based — `codex
        login` writes `auth.json` into CODEX_HOME. harness/run.sh mounts a
        dedicated, external credential directory READ-ONLY into the
        container at /creds/codex (populated once, outside this repo);
        this script copies just that one file into THIS run's fresh, empty
        CODEX_HOME before invoking the adapter. The read-only mount means no
        run can ever write back into the template, and the template is never
        used to run an actual agent session itself, so it never accumulates
        conversation history. Falls back to OPENAI_API_KEY if no mount is
        present.

Usage:
  run.py <claude|codex> <bare|mcp> <run-number> [--scope webapp|service|api-java]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_TAG_ENV = "BOMLY_STUDY_FIXTURE_REF"  # set at freeze; defaults to HEAD pre-freeze
DEFAULT_TIMEOUT_SECONDS = 45 * 60

# Fixed mount point harness/run.sh uses for Codex's read-only credential
# template directory (see CREDENTIALS.md). Not configurable here — the
# container-internal path is an implementation detail; what's configurable is
# where run.sh mounts FROM on the host (BOMLY_STUDY_CODEX_CREDS_DIR). Claude
# has no equivalent: its subscription credential is CLAUDE_CODE_OAUTH_TOKEN,
# an environment variable, not a file — see the module docstring.
CODEX_CREDS_MOUNT = Path("/creds/codex")

# Codex's OAuth credential file is well-documented and stable — copy just
# this one file, never the whole directory, so a stray config.toml in the
# template (if one ever exists there) can't collide with the MCP-server
# registration `codex mcp add` writes into THIS run's fresh CODEX_HOME below.
CODEX_CRED_FILES = ["auth.json"]


def copy_credentials(mount_point: Path, known_files: list[str], dest: Path) -> str:
    """Copy only known credential file(s) from a read-only template mount
    into this run's fresh config dir (Codex only — see module docstring for
    why Claude doesn't use this path). Returns a mode string recorded in
    meta.json: 'none' (no mount present — falling back to the API key env
    var), 'known-files' (copied only the expected credential file(s)), or
    'full-tree-fallback' (none of the known filenames were found; copied
    everything as a functional fallback — should be tightened once verified).
    """
    if not mount_point.is_dir():
        return "none"
    matched = [f for f in known_files if (mount_point / f).exists()]
    if matched:
        for name in matched:
            src = mount_point / name
            if src.is_dir():
                shutil.copytree(src, dest / name, dirs_exist_ok=True)
            else:
                shutil.copy(src, dest / name)
        return "known-files"
    # Fallback: copy everything. Safe because mount_point is read-only.
    for item in mount_point.iterdir():
        dest_item = dest / item.name
        if item.is_dir():
            shutil.copytree(item, dest_item, dirs_exist_ok=True)
        else:
            shutil.copy(item, dest_item)
    return "full-tree-fallback"


def claude_credential_mode(env: dict) -> str:
    """Claude's credential isn't a file to copy — just report which env var
    resolved so meta.json stays informative and symmetric with Codex's
    credential_copy_mode field."""
    if env.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return "oauth-token-env-var"
    if env.get("ANTHROPIC_API_KEY"):
        return "api-key-env-var"
    return "none"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_of(path: Path) -> str | None:
    if not path or not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_capture(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# Never expose these to the agent's workspace — a real pilot run proved this
# necessary: Claude Code read fixtures/SLOTS.yaml on its own (the scorer's
# ground-truth answer key — advisory IDs, minimum safe versions, remediation
# class per slot) and, to its credit, refused to just transcribe it and asked
# for guidance instead of proceeding. A less careful model, or the same model
# on a different day, might not. A plain `git clone` of this repo hands the
# agent everything: the answer key, harness/ (the entire scoring engine —
# enough to reverse-engineer or game it), prompts/ (BOTH conditions'
# instructions, so a "bare" run could read condition-mcp/CLAUDE.md and learn
# an MCP server exists — defeating the bare/mcp comparison), and every other
# run's FIXES.md/diff under runs/ or runs-pilot/. A regular clone ALSO carries
# full git history, so even deleting these paths from the working tree
# wouldn't be enough — `git log -p` / `git show <old-sha>:fixtures/SLOTS.yaml`
# could still retrieve them. See _agent_facing_snapshot() below for the fix.
AGENT_EXCLUDED_PATHS = [
    "fixtures/SLOTS.yaml",
    "harness",
    "prompts",
    "scoring",
    "runs",
    "runs-pilot",
    "analysis",
    "CREDENTIALS.md",
    "METHODOLOGY.md",
    "LIMITATIONS.md",
    # Found in the same pass as the above, checking what a real pilot run
    # could actually see: the root README.md describes the entire study
    # design in plain English (harness/ and prompts/ layout, "the ground-
    # truth SLOTS.yaml", the scoring rubric, credential setup) — arguably as
    # informative as the excluded directories themselves. scripts/ is a
    # maintainer-only dev tool (verify-fixtures.sh) that also names
    # SLOTS.yaml directly.
    "README.md",
    "scripts",
]

# General mechanism for files that mix legitimate agent-facing content with
# sensitive detail (e.g. fixtures/api-java/README.md's practical JAVA_HOME
# setup vs. its "Vulnerability slots" section, which is answer-key-equivalent
# for that fixture specifically) — whole-file exclusion would throw away the
# legitimate part too. Anything between these HTML-comment markers is
# stripped from every text file in the agent's workspace.
AGENT_EXCLUDE_BEGIN = "<!-- AGENT-EXCLUDE:BEGIN -->"
AGENT_EXCLUDE_END = "<!-- AGENT-EXCLUDE:END -->"


def _strip_excluded_sections(root: Path) -> None:
    pattern = re.compile(
        re.escape(AGENT_EXCLUDE_BEGIN) + r".*?" + re.escape(AGENT_EXCLUDE_END) + r"\n?",
        re.DOTALL,
    )
    for path in root.rglob("*"):
        if not path.is_file() or path.is_relative_to(root / ".git"):
            continue
        try:
            text = path.read_text()
        except (UnicodeDecodeError, ValueError):
            continue  # binary file, nothing to strip
        if AGENT_EXCLUDE_BEGIN in text:
            path.write_text(pattern.sub("", text))


MAKEFILE_HARNESS_MARKER = "# --- Harness targets ---"


def _trim_agent_makefile(makefile_path: Path) -> None:
    """The root Makefile is needed for `make test` and isn't in
    AGENT_EXCLUDED_PATHS, but its harness section (reproduce-one,
    verify-only, aggregate, and their comments — 'Needs a credential', 'Add
    PILOT=1', references to CREDENTIALS.md) reveals the agent is part of a
    structured multi-condition study, found the same way SLOTS.yaml was:
    inspecting what a real pilot run could actually see. Lower severity than
    the answer key (no vulnerability info here), but still meta-context a
    real repo wouldn't have and that could bias behavior. Truncates at the
    marker comment, keeping only the test/clean targets the agent legitimately
    needs — derived from the real Makefile rather than hand-maintaining a
    second copy that could drift out of sync.
    """
    if not makefile_path.exists():
        return
    text = makefile_path.read_text()
    marker_idx = text.find(MAKEFILE_HARNESS_MARKER)
    if marker_idx == -1:
        return
    trimmed = text[:marker_idx].rstrip() + "\n"
    # .PHONY still lists the now-removed harness target names on its
    # continuation line — harmless to Make (a no-op for a target that
    # doesn't exist) but still a residual name leak. Drop the continuation.
    trimmed = re.sub(r"(\.PHONY:[^\n]*) \\\n\s*\S[^\n]*\n", r"\1\n", trimmed)
    makefile_path.write_text(trimmed)


def fresh_clone(workspace: Path, ref: str) -> None:
    """Materialize the agent's workspace at workspace/repo: the fixture tree
    at the frozen ref, with AGENT_EXCLUDED_PATHS removed, and NO git history —
    just a single fresh commit over the already-redacted tree, so later
    diff-capture (`git -C repo diff`) still works unchanged, comparing
    against exactly what the agent was shown, nothing more.
    """
    dest = workspace / "repo"
    dest.mkdir(parents=True)
    # `git archive` reads directly from REPO_ROOT's own history at `ref` and
    # extracts a plain file tree — no .git, no history, nothing beyond what's
    # in that one tree to inspect.
    archive_proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "archive", "--format=tar", ref],
        capture_output=True, check=True,
    )
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive_proc.stdout, check=True)

    for rel in AGENT_EXCLUDED_PATHS:
        target = dest / rel
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        elif target.exists():
            target.unlink()

    _trim_agent_makefile(dest / "Makefile")
    _strip_excluded_sections(dest)

    # Fresh, single-commit git history over the redacted tree — enough for
    # `git diff`/`git status` to work normally, nothing more to discover.
    # Generic identity/message: the ORIGINAL version used "bomly-agent-study"
    # as the commit author name, which a `git log`/`git show` inspection
    # would surface even with history otherwise squashed to one commit —
    # naming the study in its own git metadata.
    subprocess.run(["git", "-C", str(dest), "init", "--quiet"], check=True)
    subprocess.run(["git", "-C", str(dest), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(dest), "-c", "user.email=fixture@example.com", "-c", "user.name=fixture",
         "commit", "--quiet", "-m", "Initial commit"],
        check=True,
    )
    # `git commit` writes reflog entries (.git/logs/) even for this one
    # commit, carrying the same author/message metadata again — belt and
    # suspenders, drop them; reflogs aren't needed for git diff/status.
    shutil.rmtree(dest / ".git" / "logs", ignore_errors=True)


def write_condition_files(dest: Path, condition: str) -> None:
    cond_dir = REPO_ROOT / "prompts" / f"condition-{condition}"
    if not cond_dir.exists():
        raise SystemExit(f"missing prompts dir: {cond_dir}")
    for name in ("CLAUDE.md", "AGENTS.md", "GEMINI.md"):
        src = cond_dir / name
        if src.exists():
            shutil.copy(src, dest / name)


def scope_paths(scope: str, repo: Path) -> list[Path]:
    if scope == "all":
        return [repo / "fixtures" / d for d in ("webapp", "service", "api-java")]
    return [repo / "fixtures" / scope]


def capture_diff(repo: Path, out_path: Path) -> None:
    diff = run_capture(["git", "-C", str(repo), "diff", "--no-color"])
    out_path.write_text(diff.stdout)


def find_fixes_md(repo: Path) -> Path | None:
    p = repo / "FIXES.md"
    return p if p.exists() else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("agent", choices=["claude", "codex"])
    ap.add_argument("condition", choices=["bare", "mcp"])
    ap.add_argument("run_number", type=int)
    ap.add_argument("--scope", default="all", choices=["all", "webapp", "service", "api-java"])
    ap.add_argument(
        "--pilot", action="store_true",
        help="Write output under runs-pilot/ instead of runs/. Pilot runs shake out harness bugs "
             "and are published, but per the pre-registered design they are NEVER pooled into the "
             "final dataset — aggregate.py only ever reads runs/, so this keeps that separation "
             "structural rather than relying on remembering not to mix directories.",
    )
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    ap.add_argument("--work-root", default=None, help="Scratch root for the throwaway workspace (default: a temp dir)")
    ap.add_argument("--keep-workspace", action="store_true", help="Don't delete the workspace after capture (debugging)")
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Exercise isolation (clone, fresh config dirs, condition files) WITHOUT invoking a "
             "real agent or scoring — no API key needed, safe on the bare host. For harness "
             "development only; never a substitute for a real Docker run.",
    )
    args = ap.parse_args()

    fixture_ref = os.environ.get(FIXTURE_TAG_ENV, "HEAD")
    fixture_sha = run_capture(["git", "-C", str(REPO_ROOT), "rev-parse", "--short", fixture_ref]).stdout.strip()
    harness_sha = run_capture(["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"]).stdout.strip()

    runs_root = "runs-pilot" if args.pilot else "runs"
    run_dir = REPO_ROOT / runs_root / args.agent / args.condition / str(args.run_number)
    run_dir.mkdir(parents=True, exist_ok=True)

    work_root_auto_created = args.work_root is None
    work_root = Path(args.work_root) if args.work_root else Path(tempfile.mkdtemp(prefix="bomly-study-"))
    workspace = work_root / f"{args.agent}-{args.condition}-{args.run_number}-{int(time.time())}"
    workspace.mkdir(parents=True)
    agent_config_dir = workspace / "agent-config"  # fresh CLAUDE_CONFIG_DIR / CODEX_HOME
    agent_config_dir.mkdir()

    meta = {
        "agent": args.agent,
        "condition": args.condition,
        "run_number": args.run_number,
        "pilot": args.pilot,
        "scope": args.scope,
        "fixture_ref": fixture_ref,
        "fixture_sha": fixture_sha,
        "harness_sha": harness_sha,
        "bomly_version": None,
        "bomly_sha256": None,
        "agent_version": None,
        "model": None,
        "effort": None,
        "started_at": None,
        "ended_at": None,
        "timeout": False,
        "exit_code": None,
        "mcp_tool_errors": [],
        "stderr_tail": None,
        "credential_copy_mode": None,
    }

    bomly_path = shutil.which("bomly")
    if bomly_path:
        meta["bomly_sha256"] = sha256_of(Path(bomly_path))
        v = run_capture(["bomly", "--version"])
        meta["bomly_version"] = v.stdout.strip().splitlines()[0] if v.stdout else None

    try:
        fresh_clone(workspace, fixture_ref)
        repo = workspace / "repo"
        write_condition_files(repo, args.condition)

        # No separately-managed MCP server process: prompts/mcp-config.json
        # uses the stdio transport, so the agent CLI itself spawns
        # `bomly mcp serve` (no path flag — bomly's MCP tools take `path` as
        # a per-call argument, not a server-startup flag; passing --path
        # here caused the subprocess to exit immediately with "unknown
        # flag: --path", which is why every mcp-condition run so far had
        # zero real mcp_calls — the server never got a chance to start) as
        # its own child subprocess, scoped to exactly this one invocation
        # and inheriting cwd=repo. It cannot outlive the run or be shared
        # across runs — the client owns it.
        adapter_mod = __import__(f"adapters.{args.agent}", fromlist=["run"])

        prompt_path = REPO_ROOT / "prompts" / "PROMPT.md"
        prompt = prompt_path.read_text()

        env = os.environ.copy()
        if args.agent == "claude":
            # CLAUDE_CONFIG_DIR is still set to a fresh, empty per-run dir —
            # still worth isolating whatever local cache/trust state Claude
            # Code writes during a session — but nothing is copied into it.
            # Auth is CLAUDE_CODE_OAUTH_TOKEN (or ANTHROPIC_API_KEY), plain
            # environment variables inherited via os.environ.copy() above.
            env["CLAUDE_CONFIG_DIR"] = str(agent_config_dir)
            meta["credential_copy_mode"] = claude_credential_mode(env)
        elif args.agent == "codex":
            env["CODEX_HOME"] = str(agent_config_dir)
            meta["credential_copy_mode"] = copy_credentials(CODEX_CREDS_MOUNT, CODEX_CRED_FILES, agent_config_dir)
            if args.condition == "mcp":
                # Codex has no per-invocation --mcp-config flag; it reads MCP
                # servers from $CODEX_HOME/config.toml. `codex mcp add` writes
                # into whatever CODEX_HOME the subprocess sees, so pointing it
                # at this run's fresh, empty config dir keeps the
                # registration scoped to this run only.
                subprocess.run(
                    ["codex", "mcp", "add", "bomly", "--", "bomly", "mcp", "serve"],
                    env=env, cwd=repo, check=True, capture_output=True, text=True,
                )

        started = now_iso()
        t0 = time.monotonic()
        if args.dry_run:
            # No agent invoked, no credentials touched, no cost. Proves the
            # clone/isolation/condition-file/verify pipeline end to end using
            # only the unmodified fixture — real scoring will (correctly)
            # show every slot as NOT_ATTEMPTED since nothing changed.
            (raw := run_dir / "transcript.raw.jsonl").write_text("")
            result = {
                "agent_version": "dry-run (no agent invoked)",
                "model": "n/a",
                "effort": "n/a",
                "exit_code": 0,
                "timeout": False,
                "turns": 0,
                "tool_calls": 0,
                "mcp_calls": 0,
                "mcp_tool_errors": [],
                "tokens": None,
                "cost_usd": None,
                "normalized_events": [],
                "stderr_tail": None,
            }
        else:
            result = adapter_mod.run(
                repo=repo,
                prompt=prompt,
                condition=args.condition,
                env=env,
                timeout_seconds=args.timeout,
                raw_transcript_path=run_dir / "transcript.raw.jsonl",
                mcp_config_path=(REPO_ROOT / "prompts" / "mcp-config.json" if args.condition == "mcp" else None),
            )
        wall = time.monotonic() - t0
        ended = now_iso()

        meta.update(
            {
                "agent_version": result.get("agent_version"),
                "model": result.get("model", meta["model"]),
                "effort": result.get("effort", meta["effort"]),
                "started_at": started,
                "ended_at": ended,
                "timeout": result.get("timeout", False),
                "exit_code": result.get("exit_code"),
                "mcp_tool_errors": result.get("mcp_tool_errors", []),
                "stderr_tail": result.get("stderr_tail"),
            }
        )

        # Normalized transcript (adapter-specific parsing of the raw output).
        norm_events = result.get("normalized_events", [])
        with open(run_dir / "transcript.norm.jsonl", "w") as f:
            for ev in norm_events:
                f.write(json.dumps(ev) + "\n")

        timing = {
            "started_at": started,
            "ended_at": ended,
            "wall_seconds": round(wall, 2),
            "timeout": result.get("timeout", False),
            "turns": result.get("turns"),
            "tool_calls": result.get("tool_calls"),
            "mcp_calls": result.get("mcp_calls"),
            "tokens": result.get("tokens"),
            "cost_usd": result.get("cost_usd"),
        }
        (run_dir / "timing.json").write_text(json.dumps(timing, indent=2))

        capture_diff(repo, run_dir / "diff.patch")
        fixes = find_fixes_md(repo)
        if fixes:
            shutil.copy(fixes, run_dir / "FIXES.md")
        else:
            (run_dir / "FIXES.md").write_text("(agent did not create FIXES.md)\n")

        (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))

        # Score the workspace WHILE it still exists (post-agent state) — this
        # is the fast path. `make verify-only` (harness/verify.py --from-run)
        # reconstructs an equivalent workspace later from diff.patch alone, so
        # scoring is independently reproducible without re-running any agent.
        import verify as verify_mod  # local import: sys.path set in __main__

        score_result = verify_mod.verify_workspace(repo, args.scope, fixture_ref=fixture_ref)
        score_result["run_meta"] = {
            "agent": args.agent,
            "condition": args.condition,
            "run_number": args.run_number,
            "wall_seconds": timing["wall_seconds"],
            "timeout": timing["timeout"],
            "turns": timing["turns"],
            "tool_calls": timing["tool_calls"],
            "mcp_calls": timing["mcp_calls"],
            "tokens": timing.get("tokens"),
            "cost_usd": timing.get("cost_usd"),
            "mcp_tool_errors": meta["mcp_tool_errors"],
        }
        (run_dir / "result.json").write_text(json.dumps(score_result, indent=2))

        print(f"run complete: {run_dir}")
        print(f"workspace: {workspace}" + (" (kept)" if args.keep_workspace else " (will be removed)"))
        return 0
    finally:
        if not args.keep_workspace:
            shutil.rmtree(workspace, ignore_errors=True)
            if work_root_auto_created:
                shutil.rmtree(work_root, ignore_errors=True)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
