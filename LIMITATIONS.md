# Limitations

Read this before quoting any number from the study. Everything below is also
reflected, more briefly, in the blog post and in [REPORT.md](REPORT.md)'s
threats-to-validity section. Phrasing rule we hold ourselves to: results are
"in our setup, on these fixtures, on these dates" — never a general benchmark
claim.

1. **N=5 per cell, one fixture per regime.** Five runs per agent × condition
   × fixture, and exactly one fixture represents the large-project regime
   (`bigapp`). The large-project finding is suggestive, not established. A
   different large project, a different day, or different model versions
   could move the numbers.

2. **`bigapp` is scored by bomly alone.** For the other fixtures every scored
   package is dual-confirmed by an independent scanner; for `bigapp` no
   independent scanner can resolve the transitive multi-module Maven graph,
   so the vulnerable surface is bomly's own resolution plus a hand-verified
   overlay. A skeptic can fairly note that bomly defines part of the test it
   is being evaluated on. Mitigations: the *outcome* of each run (build
   state, which versions changed, whether an advisory still applies) is
   checked from the workspace and diff independently of bomly's scan; the
   overlay cases were verified by hand; and the full surface is published in
   [`fixtures/GROUND_TRUTH.md`](fixtures/GROUND_TRUTH.md) for anyone to audit.

3. **Claude Code ran different models on different fixtures.**
   `claude-sonnet-5` on webapp/service/api-java, `claude-opus-4-8` on
   `bigapp` (chosen to remove a sonnet-specific build-breaking behavior as a
   confound). Bare-vs-MCP comparisons *within* a fixture are clean;
   comparisons of Claude numbers *across* fixtures are not.

4. **One agent's bare runs are high-variance — report the spread, not the
   mean.** Claude Code's bare completeness on `bigapp` was 91%, 98%, 98%,
   14%, 14%. A mean of 63% is arithmetically true and materially misleading
   in both directions; per-run values are in
   [`analysis/results.csv`](analysis/results.csv) and every figure shows all
   five runs.

5. **The two agents are not comparable to each other.** Different models,
   different reasoning-effort settings, different CLI harnesses. Nothing in
   this study supports "agent A beats agent B," and we do not claim it.

6. **`bigapp` and the model change postdate the `prereg-v1` tag.** The
   preregistered design covered the three-fixture ladder; the large fixture
   was added after that design hit a ceiling. The deviation list in
   [METHODOLOGY.md](METHODOLOGY.md) is the honest account; treat the
   `bigapp` result as a well-documented follow-up, not a preregistered
   confirmation.

7. **Round 1 on `bigapp` had a minor workspace leak, identical in both
   conditions.** A Makefile build comment visible to the agent mentioned a
   scoring-internal term. It named no packages and pointed at nothing
   actionable, both conditions saw the same bytes, and rounds 2–5 (with the
   comment removed) reproduce round 1's result — so we kept round 1 in the
   data rather than silently rerunning it. Judge for yourself:
   the diff is in the repo history.

8. **Hallucination scoring leans on the run's own `FIXES.md` self-report.**
   "Claimed fixed but not fixed" requires parsing the agent's claim;
   the matchers had real bugs during the pilots (fixed, documented in
   [METHODOLOGY.md](METHODOLOGY.md)), and ambiguous cases were adjudicated by
   hand and logged in [`scoring/adjudications.md`](scoring/adjudications.md).
   The raw transcripts are published, so every such call can be re-checked.

9. **The smaller fixtures' advisories are plausibly in model training data.**
   CTFd 3.7.7 and Dependency-Track 4.10.0 are public, and their CVEs are
   old. That is part of why capable agents saturate them bare — and why we
   don't read the ceiling as "agents don't need dependency data in general."

10. **MCP was not free on the tractable fixtures.** Where the bare agent
    already saturates, adding the server mostly added tool calls and
    wall-clock time (e.g. round-1 webapp: both agents were slower with MCP).
    The value we measured is regime-dependent; on small projects the honest
    reading is "no benefit in our setup."
