# Credentials

The harness needs a real, working Claude Code and/or Codex CLI credential to
run a live agent. Claude Code and Codex work **differently** here — this was
originally designed symmetrically (a mounted, read-only credential directory
for both), and a real pilot run proved that wrong for Claude. Keep that in
mind if you're extending this to a third agent: check what its subscription
auth actually produces before assuming a directory-mount pattern will work.

## Claude Code: `CLAUDE_CODE_OAUTH_TOKEN` (an environment variable, not a file)

```bash
claude setup-token
```

This performs a live OAuth flow (you'll need a browser) and prints a
long-lived token tied to your Claude subscription — session-limited, not
per-token billing. It ends with:

```
Use this token by setting: export CLAUDE_CODE_OAUTH_TOKEN=<token>
```

Export it in whatever shell you'll run the harness from:

```bash
export CLAUDE_CODE_OAUTH_TOKEN=<the token you were just given>
```

**Treat this token like a password — never commit it, paste it into a chat,
or write it to a file in this repo.** If you ever do, revoke/regenerate it
immediately (`claude auth logout`, then `claude setup-token` again) — a
long-lived token that's been exposed anywhere outside your own shell should
be considered compromised.

`harness/run.sh` passes it straight through to the container as an
environment variable (`-e CLAUDE_CODE_OAUTH_TOKEN`) — never written to a
file, never baked into the image, never appears in any committed artifact.

### Why this isn't a directory-based credential (a real mistake, corrected)

The original design assumed `claude setup-token` would write a credential
file into `CLAUDE_CONFIG_DIR`, the same way Codex's `codex login` writes
`auth.json` into `CODEX_HOME` — and built a symmetric mounted-directory
mechanism for both. A real pilot run proved that wrong: redirecting
`CLAUDE_CONFIG_DIR` and running `claude setup-token` produces a `.claude.json`
containing nothing but app telemetry (machine ID, migration flags) — no
credential at all. Claude Code's normal OAuth session lives in the **macOS
Keychain** (confirmed via `claude --bare --help`'s own text: "OAuth and
keychain are never read" under `--bare`), which doesn't exist inside a Linux
container. `claude setup-token` exists specifically to produce a portable
bearer token for exactly this headless/Docker scenario — an environment
variable, not a file. Falls back to `ANTHROPIC_API_KEY` if
`CLAUDE_CODE_OAUTH_TOKEN` isn't set.

## Codex: `auth.json` (genuinely file-based — mounted read-only)

```bash
mkdir -p ~/.bomly-study-creds/codex
CODEX_HOME=~/.bomly-study-creds/codex codex login
```

- Does the standard ChatGPT OAuth flow (needs a browser) — cannot be
  automated or run on your behalf by an agent.
- **Why the `CODEX_HOME=` prefix matters:** without it, this would write into
  your real `~/.codex` — your daily-driver config and conversation history.
  Pointing at a dedicated, empty directory means this one-time setup step
  never touches your actual environment.
- Run this once per machine. `codex login` writes `auth.json` into that
  directory; unlike Claude, this genuinely is the credential.

### How the harness consumes it

`harness/run.sh` mounts `~/.bomly-study-creds/codex` (override with
`BOMLY_STUDY_CODEX_CREDS_DIR` if you used a different path) **read-only**
into the container, at `/creds/codex`. Before each run, `harness/run.py`
copies just `auth.json` from there into *that run's* fresh, empty, throwaway
`CODEX_HOME` — never the whole mounted directory, and never in the other
direction. The per-run `config.toml` stays otherwise clean, because the
harness writes the bomly MCP server registration into it separately via
`codex mcp add` for that run only.

Because the mount is read-only and is never itself used to run an actual
agent session, it cannot accumulate history and cannot be modified by a
run — every run still starts from a completely clean, isolated config
directory, authenticated but with no memory of any other run.

Falls back to `OPENAI_API_KEY` if no `/creds/codex` mount is present.

## Honest limitation (applies to both agents)

An unattended agent with valid credentials *could*, in principle, try to read
and exfiltrate them over the network during a run (a general risk of running
any autonomous coding agent with real credentials, not specific to this
harness). The isolation here protects against runs contaminating *each
other* and against the harness touching your daily-driver config — it does
not sandbox against a sufficiently adversarial agent action within a single
run. Mitigate by using scoped/revocable credentials where your provider
supports it, and by treating the fixture repo (which you're not editing
during a run) as the only thing that needs to be trusted not to instruct the
agent to do something like that.

## Fallback: API keys (pay-per-token)

Simpler, no one-time setup step:

```bash
export ANTHROPIC_API_KEY=...   # for claude runs, if CLAUDE_CODE_OAUTH_TOKEN isn't set
export OPENAI_API_KEY=...      # for codex runs, if no /creds/codex mount is present
```

Never written to a file, never baked into the image.

## What `meta.json`'s `credential_copy_mode` tells you

| Value | Agent | What happened |
|---|---|---|
| `"oauth-token-env-var"` | Claude | `CLAUDE_CODE_OAUTH_TOKEN` was set — the intended path |
| `"api-key-env-var"` | Claude | Fell back to `ANTHROPIC_API_KEY` |
| `"known-files"` | Codex | Copied `auth.json` from the `/creds/codex` mount — the intended path |
| `"full-tree-fallback"` | Codex | `auth.json` wasn't found in the mount; copied the whole directory instead (functional, but investigate why) |
| `"none"` | either | No credential source was found — the run almost certainly failed auth |
