# Top-level build/test tasks.
#
# `make test` rebuilds every fixture from clean installs and runs its test
# suite.
# <!-- AGENT-EXCLUDE:BEGIN -->
# (Internal note: a run's fixes are judged against these same commands, so
# "the fix broke the build" is mechanically detectable.)
# <!-- AGENT-EXCLUDE:END -->

PYTHON ?= python3.12

.PHONY: test test-webapp test-service test-java clean \
        reproduce-one verify-only aggregate study batch

test: test-webapp test-service test-java ## Build + test all three fixtures from clean

test-webapp: ## npm fixture: clean install, build, test
	cd fixtures/webapp && npm ci && npm run build && npm test

test-service: ## Python fixture (vendored CTFd 3.7.7): fresh venv, install, bounded pytest subset
	cd fixtures/service && \
		$(PYTHON) -m venv .venv && \
		.venv/bin/pip install --quiet --upgrade pip && \
		.venv/bin/pip install --quiet -r requirements.txt && \
		grep -vE "^-r |psycopg2|bandit|sphinx|pip-tools|flask_profiler|flask-debugtoolbar|pipdeptree" development.txt > .dev-test.txt && \
		.venv/bin/pip install --quiet -r .dev-test.txt && \
		.venv/bin/python -m pytest tests/test_config.py tests/users -q -p no:randomly

test-java: ## Maven fixture (vendored Dependency-Track 4.10.0): bounded surefire subset
	# -P enhance: DataNucleus JDO bytecode enhancement is a profile upstream,
	# not part of the default lifecycle (see DEVELOPING.md, "DataNucleus
	# Bytecode Enhancement") — without it every @PersistenceCapable-backed
	# test fails with NucleusUserException before ever reaching test logic.
	cd fixtures/api-java && mvn -B -P enhance test -Dtest="org.dependencytrack.model.**,org.dependencytrack.util.**,org.dependencytrack.parser.**" -DfailIfNoTests=false

clean: ## Remove build artifacts and virtualenvs
	rm -rf fixtures/webapp/node_modules fixtures/webapp/dist
	rm -rf fixtures/service/.venv
	rm -rf fixtures/api-java/target

# --- Harness targets ---
# AGENT/CONDITION/SCOPE select the run; RUN_NUMBER numbers repeats within a
# cell. PILOT=1 writes to runs-pilot/ instead of runs/ — pilot runs are
# published but, per the pre-registered design, never pooled into the final
# dataset; aggregate (below) only reads runs/ unless --pilot is passed.
AGENT ?= claude
CONDITION ?= mcp
SCOPE ?= webapp
RUN_NUMBER ?= 1
PILOT ?=

PILOT_FLAG := $(if $(PILOT),--pilot,)

reproduce-one: ## Run one agent+condition+fixture session end to end in Docker, then score it. Needs a credential (see CREDENTIALS.md). Add PILOT=1 for a pilot run.
	./harness/run.sh $(AGENT) $(CONDITION) $(RUN_NUMBER) --scope $(SCOPE) $(PILOT_FLAG)

verify-only: ## Re-score an already-published run, no API key needed:  make verify-only RUN=runs/claude/mcp/webapp/1
	./harness/verify.sh $(RUN)

aggregate: ## Roll per-run result.json files into analysis/results.csv (or results-pilot.csv with PILOT=1)
	$(PYTHON) harness/aggregate.py $(PILOT_FLAG)

N ?= 5
AGENTS ?= claude,codex
CONDITIONS ?= bare,mcp
SCOPES ?= webapp,service,api-java

study: ## Run the full agent x condition x fixture x N matrix (one fixture per session), resuming past any already-valid runs. Safe to re-invoke after a session-limit interruption — only re-executes missing/invalid sessions. DRY=1 to preview without running.
	$(PYTHON) harness/run_study.py --agents $(AGENTS) --conditions $(CONDITIONS) --scopes $(SCOPES) --n $(N) $(PILOT_FLAG) $(if $(DRY),--dry-run,)

batch: ## Run ONE human-gated fixture-batch = both agents x both conditions for one fixture at one run-number (4 sessions), then stop. Set FIXTURE and RUN, e.g. make batch FIXTURE=webapp RUN=1. DRY=1 to preview. The N=5 study runs as 15 of these, one per Ahmed go/no-go (2026-07-09).
	@test -n "$(FIXTURE)" || { echo "set FIXTURE=webapp|service|api-java"; exit 2; }
	@test -n "$(RUN)" || { echo "set RUN=<run-number>"; exit 2; }
	$(PYTHON) harness/run_study.py --agents $(AGENTS) --conditions $(CONDITIONS) --scopes $(FIXTURE) --only-n $(RUN) $(PILOT_FLAG) $(if $(DRY),--dry-run,)
