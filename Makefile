# bomly-agent-study — top-level tasks.
#
# `make test` rebuilds every fixture from clean installs and runs its test
# suite. A run's fixes are judged against these same commands, so "the fix broke
# the build" is mechanically detectable.

PYTHON ?= python3.12

.PHONY: test test-webapp test-service test-java clean \
        reproduce-one verify-only aggregate

test: test-webapp test-service test-java ## Build + test all three fixtures from clean

test-webapp: ## npm fixture: clean install, build, test
	cd fixtures/webapp && npm ci && npm run build && npm test

test-service: ## Python fixture: fresh venv, install, pytest
	cd fixtures/service && \
		$(PYTHON) -m venv .venv && \
		.venv/bin/pip install --quiet --upgrade pip && \
		.venv/bin/pip install --quiet -r requirements.txt -r requirements-dev.txt && \
		.venv/bin/pytest -q

test-java: ## Maven fixture: offline test (deps expected pre-resolved)
	cd fixtures/api-java && mvn -o test

clean: ## Remove build artifacts and virtualenvs
	rm -rf fixtures/webapp/node_modules fixtures/webapp/dist
	rm -rf fixtures/service/.venv
	rm -rf fixtures/api-java/target

# --- Harness targets ---
# AGENT/CONDITION/SCOPE select the run; RUN_NUMBER lets pilot/full runs coexist.
AGENT ?= claude
CONDITION ?= mcp
SCOPE ?= webapp
RUN_NUMBER ?= 1

reproduce-one: ## Run one agent+condition end to end in Docker, then score it. Needs an API key (ANTHROPIC_API_KEY or OPENAI_API_KEY) in the environment.
	./harness/run.sh $(AGENT) $(CONDITION) $(RUN_NUMBER) --scope $(SCOPE)

verify-only: ## Re-score an already-published run, no API key needed:  make verify-only RUN=runs/claude/mcp/1
	./harness/verify.sh $(RUN)

aggregate: ## Roll per-run result.json files into analysis/results.csv
	$(PYTHON) harness/aggregate.py
