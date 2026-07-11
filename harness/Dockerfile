# CS-A study runner: pinned toolchain for reproducible agent runs.
#
# Build with the REPO ROOT as context (not harness/), so fixtures/ is reachable:
#   docker build -f harness/Dockerfile -t bomly-agent-study .
#
# Every binary version here is pinned and recorded in each run's meta.json.
# This image is where --permission-mode bypassPermissions (Claude Code) and
# --dangerously-bypass-approvals-and-sandbox (Codex) are allowed to execute —
# harness/adapters/*.py refuse to use those modes unless BOTH /.dockerenv
# exists AND BOMLY_STUDY_IN_CONTAINER=1 is set (set below), so an unattended,
# unrestricted agent never runs on the operator's bare host.
#
# Both bypass modes are load-bearing here, confirmed via real pilot runs, not
# assumed: Codex's own internal `workspace-write` sandbox uses bubblewrap to
# create a Linux user namespace, which Docker's default container profile
# blocks outright ("bwrap: No permissions to create a new namespace") —
# irrelevant to root vs. non-root, since this container already IS the
# sandbox boundary Codex's docs say that flag is "intended solely for."
# Claude Code's bypassPermissions, separately, refuses to run at all as root
# ("cannot be used with root/sudo privileges for security reasons") — that's
# why this image creates and runs as a non-root user below.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    BOMLY_STUDY_IN_CONTAINER=1 \
    JAVA_HOME=/opt/openjdk-17 \
    PATH=/opt/openjdk-17/bin:/usr/local/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates git build-essential unzip \
      python3.12 python3.12-venv python3-pip \
      maven \
    && rm -rf /var/lib/apt/lists/*

# --- Node.js 22 (Claude Code + Codex CLI are npm packages) ---
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# --- JDK 17 (api-java fixture; matches maven.compiler.release in pom.xml) ---
# TARGETARCH is set automatically by BuildKit (amd64|arm64) — Docker Desktop
# on Apple Silicon builds arm64 by default, and an emulated amd64 JVM under
# Rosetta failed here on first build ("failed to open elf ... Trace/breakpoint
# trap"), so both binaries below are fetched per-arch rather than hardcoded.
ARG TARGETARCH
RUN case "$TARGETARCH" in \
      amd64) JDK_ARCH=x64 ;; \
      arm64) JDK_ARCH=aarch64 ;; \
      *) echo "unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac \
    && curl -fsSL -o /tmp/openjdk17.tar.gz \
      "https://download.java.net/java/GA/jdk17.0.2/dfd4a8d0985749f896bed50d7138ee7f/8/GPL/openjdk-17.0.2_linux-${JDK_ARCH}_bin.tar.gz" \
    && mkdir -p /opt/openjdk-17 \
    && tar -xzf /tmp/openjdk17.tar.gz -C /opt/openjdk-17 --strip-components=1 \
    && rm /tmp/openjdk17.tar.gz

# --- bomly CLI (pinned release; verify against fixtures/SLOTS.yaml's
#     metadata.bomly_version before freeze) ---
# 0.16.1: picks up the pip-detector fix (bomly-cli#237/#238/#239) — the
# ambient-interpreter fallback no longer resolves an unrelated project's
# dependencies when the Python fixture has no venv yet. This is what caused
# the mcp-condition pilot batch to under-report on fixtures/service; those 4
# runs (runs-pilot/*/mcp/*) predate this fix and are not representative.
# 0.16.2: picks up the Maven TGF fix (bomly-cli#243/#244) — mvn dependency:tree
# now runs with -B (batch mode) and the TGF parser strips ANSI escapes
# defensively, so it no longer silently falls back to a direct-deps-only scan
# and drops S10 (the transitive Maven slot) from every pilot run so far.
# 0.17.0: picks up the MCP revamp (bomly-cli#245/#246) — bomly_scan's MCP
# response was ~1.8-2.9MB, truncating 4 of 8 real scan calls to an error;
# compact response is now measured at ~9.2KB. Also removes the
# bomly_vuln_fix_context MCP tool (folded into bomly_scan's remediation
# groups) and changes the CLI --format json schema itself ("findings[] are
# now pure references... join packages[] by purl" per the PR) — verified
# harness/verify.py's parsing still holds against the new schema before
# trusting any scored run under this version; see prompts/condition-mcp/ for
# the corresponding tool-list disclosure update.
# 0.17.1: fixes the maven-detector's multi-module TGF parser (bomly-cli#252) —
# `mvn dependency:tree -DoutputType=tgf` emits one TGF block per reactor module,
# and the parser dropped every block after the first, failing every native
# scan of a multi-module reactor ("maven tgf references unknown package"). This
# is what makes the `bigapp` fixture (the 13-module Internet2 Grouper reactor)
# scannable at all — see harness/verify.py's maven-detector invocation.
ARG BOMLY_VERSION=0.17.1
RUN curl -fsSL -o /tmp/bomly.tar.gz \
      "https://github.com/bomly-dev/bomly-cli/releases/download/v${BOMLY_VERSION}/bomly_${BOMLY_VERSION}_linux_${TARGETARCH}.tar.gz" \
    && tar -xzf /tmp/bomly.tar.gz -C /usr/local/bin bomly \
    && rm /tmp/bomly.tar.gz \
    && bomly --version

# --- Agent CLIs (versions pinned at freeze; overridable at build time) ---
ARG CLAUDE_CODE_VERSION=2.1.201
ARG CODEX_VERSION=0.142.5
RUN npm install -g \
      "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
      "@openai/codex@${CODEX_VERSION}"

# --- Second-opinion scanners (independent of bomly; used by verify.py) ---
# pip-audit and the harness's own Python deps (PyYAML) go into a DEDICATED
# venv at /opt/study-tools, deliberately NOT on the ambient PATH. A real
# pilot run proved why this matters: bomly's pip detector needs an installed
# environment to resolve requirements.txt's dependency graph (the file
# itself has no edge/parent-child data), and when no project-specific venv
# exists yet (i.e. the agent calls bomly_scan before running `pip install` —
# a completely realistic thing to do first), it falls back to inspecting
# whatever's on the ambient interpreter's PATH via `pip inspect --local`
# (internal/detectors/python/venv.go in bomly-cli, confirmed by reading the
# source). With pip-audit installed system-wide, that fallback returned
# pip-audit's OWN dependency tree (cachecontrol, boolean-py, cyclonedx-
# python-lib, ...) instead of the fixture's actual requirements.txt — a real
# run's bomly_scan call on the Python fixture came back looking clean,
# because it was silently scanning the wrong project. Reproduced directly:
# with pip-audit merely present on PATH, `bomly scan --path
# fixtures/service` returns pip-audit's dependency list, not the fixture's.
# Keeping the ambient python3.12/pip3 as clean as a genuinely fresh
# developer machine — nothing installed beyond the base interpreter — is
# also just the more realistic simulation regardless of this specific bug.
RUN python3.12 -m venv /opt/study-tools
COPY harness/requirements.txt /tmp/harness-requirements.txt
RUN /opt/study-tools/bin/pip install --quiet --upgrade pip \
    && /opt/study-tools/bin/pip install --quiet pip-audit -r /tmp/harness-requirements.txt
RUN curl -fsSL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# --- Non-root user ---
# Confirmed via a real pilot run, not assumed: Claude Code refuses
# `--permission-mode bypassPermissions` outright when running as root/sudo
# ("cannot be used with root/sudo privileges for security reasons"). Reusing
# the `ubuntu` user the base image already ships (UID/GID 1000, home
# /home/ubuntu) rather than creating a new one — `useradd --uid 1000` failed
# here with "UID 1000 is not unique" on a first real build, since Ubuntu
# 24.04 provisions that account itself.
USER ubuntu
ENV HOME=/home/ubuntu

# --- Pre-warm Maven's local repo so the api-java scan/build is fully offline
#     inside the container. Done as the `ubuntu` user (not root) so it warms
#     $HOME/.m2 under the same account that will actually run `mvn` at study
#     time.
#
# Vendored Dependency-Track 4.10.0 needs more than `dependency:go-offline`
# against a bare pom.xml (that was enough for the old toy fixture): its
# DataNucleus JDO layer requires bytecode enhancement, which upstream binds
# to a Maven PROFILE (`-P enhance`, see fixtures/api-java/DEVELOPING.md,
# "DataNucleus Bytecode Enhancement") rather than the default lifecycle —
# `go-offline` doesn't resolve an inactive profile's plugins, and enhancement
# itself needs real compiled classes, not just the POM. So this copies the
# full source tree (.dockerignore drops target/) and runs the SAME bounded
# command harness/verify.py and the fixture's own Makefile target use, which
# both resolves every dependency/plugin needed AND primes the enhancer's
# output — confirming at build time, not just at scoring time, that the
# offline run actually works.
COPY --chown=ubuntu:ubuntu fixtures/api-java /tmp/warm-pom
RUN cd /tmp/warm-pom \
    && mvn -B -P enhance test -Dtest="org.dependencytrack.model.**,org.dependencytrack.util.**,org.dependencytrack.parser.**" -DfailIfNoTests=false \
    && rm -rf /tmp/warm-pom

# --- Maven Central mirror (Google's GCS mirror, a faithful copy) for the
#     ubuntu user. The bigapp reactor (Grouper, 13 modules) resolves hundreds
#     of transitive artifacts on a cold cache; a direct repo.maven.apache.org
#     resolve reliably drew HTTP 429 with a 30-minute cooldown during fixture
#     selection. This changes only WHERE artifacts download from, not WHICH
#     resolve, so it does not affect any ground truth. Placed AFTER the
#     api-java warm-up so that fixture's frozen build is untouched; it applies
#     to bigapp's warm-up below and to every runtime `mvn` (both Maven
#     fixtures) — the latter is a pure robustness win.
RUN mkdir -p /home/ubuntu/.m2 && printf '%s\n' \
    '<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0">' \
    '  <mirrors><mirror>' \
    '    <id>gcs-central</id>' \
    '    <url>https://maven-central.storage-download.googleapis.com/maven2/</url>' \
    '    <mirrorOf>central</mirrorOf>' \
    '  </mirror></mirrors>' \
    '</settings>' > /home/ubuntu/.m2/settings.xml

# --- Pre-warm Maven for the bigapp fixture (Internet2 Grouper 4.x, a
#     13-module reactor). Plain multi-module install, but with one gotcha: the
#     `grouper` module depends on grouperClient's TEST jar, so `-DskipTests`
#     (which still COMPILES tests and builds test-jars) is required and
#     `-Dmaven.test.skip=true` must NOT be used (it skips test-jar creation and
#     the reactor then fails to resolve the internal test-jar). Runs the same
#     `mvn install` from grouper-parent that the fixture's warm/scan path uses,
#     proving at build time that the offline reactor build works and priming
#     ~/.m2 with every external dependency + the internal module jars.
COPY --chown=ubuntu:ubuntu fixtures/bigapp /tmp/warm-bigapp
RUN cd /tmp/warm-bigapp/grouper-parent \
    && mvn -B -DskipTests install \
    && rm -rf /tmp/warm-bigapp

# --- Pre-warm trivy's vulnerability DB (used as the Maven fixture's
#     independent second scanner, harness/verify.py) into $HOME/.cache/trivy,
#     same rationale as the Maven warm-up above. Without this, every scoring
#     run's `trivy fs` call hits mirror.gcr.io fresh: non-deterministic
#     results across the run window (a different DB snapshot per run) at
#     best, a hung/failed scan at worst if that registry is slow or
#     unreachable from wherever the container happens to run — confirmed
#     directly: trivy hung 180s and failed even with a same-day cached DB
#     already on disk, purely because it insisted on checking for a newer
#     one first. verify.py passes --skip-db-update and relies on this.
RUN trivy image --download-db-only --quiet

WORKDIR /work
