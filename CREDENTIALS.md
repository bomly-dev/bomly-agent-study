# Credentials

The harness needs a real, working Claude Code and/or Codex CLI credential to
run a live agent. Two modes are supported. You can set up one or both,
independently, for either agent.

## Mode 1 — subscription-based (recommended: session-limited, no per-token billing)

Both CLIs support generating a long-lived credential tied to your existing
subscription, meant for exactly this kind of unattended/headless use:

```bash
mkdir -p ~/.bomly-study-creds/claude ~/.bomly-study-creds/codex

CLAUDE_CONFIG_DIR=~/.bomly-study-creds/claude claude setup-token
CODEX_HOME=~/.bomly-study-creds/codex codex login
```

- `claude setup-token`'s own description: "Set up a long-lived authentication
  token (requires Claude subscription)." This is the sanctioned CLI mechanism
  for exactly this use case — not a workaround.
- `codex login` does the standard ChatGPT OAuth flow.
- **Why the `CLAUDE_CONFIG_DIR=`/`CODEX_HOME=` prefix matters:** without it,
  each command would write into your real `~/.claude` / `~/.codex` — your
  daily-driver config, conversation history, and project trust decisions.
  Pointing at a dedicated, empty directory means this one-time setup step
  never touches your actual environment, and the resulting directory holds
  *only* what the login step wrote (no conversation history, since no
  conversation happens during `setup-token`/`login`).
- Both commands need live browser/OAuth interaction — they cannot be
  automated or run on your behalf by an agent.
- Run this once per machine. The resulting directories are read repeatedly
  (read-only) by every future run; they don't need to be redone unless the
  token expires or you revoke it.

### How the harness consumes it

`harness/run.sh` mounts `~/.bomly-study-creds/claude` and
`~/.bomly-study-creds/codex` (override with `BOMLY_STUDY_CLAUDE_CREDS_DIR` /
`BOMLY_STUDY_CODEX_CREDS_DIR` if you used different paths) **read-only** into
the container, at `/creds/claude` and `/creds/codex`. Before each run,
`harness/run.py` copies only the credential file it needs from there into
*that run's* fresh, empty, throwaway config directory — never the whole
mounted template, and never in the other direction. Concretely:

- **Codex**: copies just `auth.json` (Codex's documented credential file).
  The per-run config dir's `config.toml` stays otherwise clean, because the
  harness writes the bomly MCP server registration into it separately via
  `codex mcp add` for that run only.
- **Claude Code**: the harness doesn't yet have a confirmed filename for what
  `claude setup-token` writes (no one has run it against this harness yet —
  see the note below). It tries a couple of likely candidates
  (`.credentials.json`, `.claude.json`) first; if neither is present, it
  falls back to copying the whole template directory. That fallback is safe
  (the template is mounted read-only and is expected to hold nothing but
  auth state, never a real session's history) but should be tightened to an
  exact filename once confirmed — check `runs/<agent>/<condition>/<n>/meta.json`'s
  `credential_copy_mode` field after your first real run: `"known-files"`
  means it matched a known name; `"full-tree-fallback"` means it didn't and
  someone should narrow `CLAUDE_CRED_FILES` in `harness/run.py` accordingly.

Because the mount is read-only and is never itself used to run an actual
agent session, it cannot accumulate history and cannot be modified by a
run — every run still starts from a completely clean, isolated config
directory, authenticated but with no memory of any other run.

**Honest limitation:** an unattended agent with these credentials mounted
*could*, in principle, try to read and exfiltrate the token over the network
during a run (this is a general risk of running any autonomous coding agent
with real credentials, not specific to this harness). The isolation here
protects against runs contaminating *each other* and against the harness
touching your daily-driver config — it does not sandbox against a
sufficiently adversarial agent action within a single run. Mitigate by using
scoped/revocable credentials where your provider supports it, and by treating
the fixture repo (which you're not editing during a run) as the only thing
that needs to be trusted not to instruct the agent to do something like that.

## Mode 2 — API key (pay-per-token)

Simpler, no one-time setup step:

```bash
export ANTHROPIC_API_KEY=...   # for claude runs
export OPENAI_API_KEY=...      # for codex runs
```

`harness/run.sh` passes these through to the container as environment
variables (`-e ANTHROPIC_API_KEY -e OPENAI_API_KEY`); they're never written
to a file, never baked into the image, and never appear in any committed
artifact. If a `/creds/<agent>` mount is *also* present, the mounted
credential directory takes precedence for that agent — the API key won't be
used unless the mount is absent.

## Precedence and mixing

You can use subscription auth for one agent and an API key for the other —
each is resolved independently. Whatever `meta.json`'s `credential_copy_mode`
says for a given run tells you which path was actually used:

| `credential_copy_mode` | What happened |
|---|---|
| `"known-files"` | Copied a specific, confirmed credential file from the `/creds` mount |
| `"full-tree-fallback"` | No known filename matched; copied the whole mounted directory instead (functional, but should be tightened — see above) |
| `"none"` | No `/creds/<agent>` mount was present; the agent authenticated via its API key environment variable instead |
