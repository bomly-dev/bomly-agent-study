#!/usr/bin/env python3
"""Run one agent+condition end to end, in an isolated workspace.

Isolation, per fixture (see ../cs-a-design.md and TRACKER CS-A2):
  - Fresh `git clone` of the fixture repo into a throwaway workspace (never
    reuses a prior run's checkout, never a shared worktree).
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
  - Credentials, two supported modes (see ../CREDENTIALS.md):
      1. Subscription-based: harness/run.sh mounts a dedicated, external
         credential directory READ-ONLY into the container at /creds/claude
         and/or /creds/codex (populated once, outside this repo, via
         `claude setup-token` / `codex login`). This script copies only the
         known credential file(s) from there into THIS run's fresh, empty
         config dir before invoking the adapter — the read-only mount means
         no run can ever write back into the template, and the template is
         never used to run an actual agent session itself, so it never
         accumulates conversation history to begin with.
      2. API key: ANTHROPIC_API_KEY / OPENAI_API_KEY environment variables,
         inherited as-is, never written to any file under the workspace.
    If a /creds mount is present for an agent, it takes precedence.

Usage:
  run.py <claude|codex> <bare|mcp> <run-number> [--scope webapp|service|api-java]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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

# Fixed mount points harness/run.sh uses for the read-only credential
# template directories (see CREDENTIALS.md). Not configurable here — the
# container-internal path is an implementation detail; what's configurable is
# where run.sh mounts FROM on the host (BOMLY_STUDY_*_CREDS_DIR).
CLAUDE_CREDS_MOUNT = Path("/creds/claude")
CODEX_CREDS_MOUNT = Path("/creds/codex")

# Codex's OAuth/API credential file is well-documented and stable — copy just
# this one file, never the whole directory, so a stray config.toml in the
# template (if one ever exists there) can't collide with the MCP-server
# registration `codex mcp add` writes into THIS run's fresh CODEX_HOME below.
CODEX_CRED_FILES = ["auth.json"]

# Claude Code's exact credential filename for `claude setup-token` output
# hasn't been confirmed against a real template directory yet (first real
# pilot run should confirm and this list should be tightened accordingly).
# Try known/likely candidates first; if none match, fall back to copying the
# whole template tree so auth still works, but flag that fallback in
# meta.json (credential_copy_mode) so it's visible and auditable rather than
# silently uncertain.
CLAUDE_CRED_FILES = [".credentials.json", ".claude.json"]


def copy_credentials(mount_point: Path, known_files: list[str], dest: Path) -> str:
    """Copy only known credential file(s) from a read-only template mount
    into this run's fresh config dir. Returns a mode string recorded in
    meta.json: 'none' (no mount present — falling back to API key env vars),
    'known-files' (copied only the expected credential file(s)), or
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
    # Fallback: copy everything. Safe because mount_point is read-only and
    # (for Claude) is expected to only ever hold setup-token output, never a
    # real session's history.
    for item in mount_point.iterdir():
        dest_item = dest / item.name
        if item.is_dir():
            shutil.copytree(item, dest_item, dirs_exist_ok=True)
        else:
            shutil.copy(item, dest_item)
    return "full-tree-fallback"


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


def fresh_clone(workspace: Path, ref: str) -> None:
    """Clone the fixture repo fresh into workspace/repo at the given ref."""
    dest = workspace / "repo"
    subprocess.run(["git", "clone", "--quiet", str(REPO_ROOT), str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "--quiet", ref], check=True)
    # A clone still carries .git history/remotes — irrelevant to the agent's
    # task but harmless; the workspace itself is unique and freshly created
    # per run and is deleted after artifact capture.


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
        # `bomly mcp serve --path .` as its own child subprocess, scoped to
        # exactly this one invocation and inheriting cwd=repo. It cannot
        # outlive the run or be shared across runs — the client owns it.
        adapter_mod = __import__(f"adapters.{args.agent}", fromlist=["run"])

        prompt_path = REPO_ROOT / "prompts" / "PROMPT.md"
        prompt = prompt_path.read_text()

        env = os.environ.copy()
        if args.agent == "claude":
            env["CLAUDE_CONFIG_DIR"] = str(agent_config_dir)
            meta["credential_copy_mode"] = copy_credentials(CLAUDE_CREDS_MOUNT, CLAUDE_CRED_FILES, agent_config_dir)
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
                    ["codex", "mcp", "add", "bomly", "--", "bomly", "mcp", "serve", "--path", "."],
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
