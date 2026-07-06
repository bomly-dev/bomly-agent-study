# CS-A study runner: pinned toolchain for reproducible agent runs.
#
# Build with the REPO ROOT as context (not harness/), so fixtures/ is reachable:
#   docker build -f harness/Dockerfile -t bomly-agent-study .
#
# Every binary version here is pinned and recorded in each run's meta.json.
# This image is where --permission-mode bypassPermissions (Claude Code) and
# --dangerously-bypass-approvals-and-sandbox (Codex, only if ever enabled)
# are allowed to execute — harness/adapters/*.py refuse to use those modes
# unless BOTH /.dockerenv exists AND BOMLY_STUDY_IN_CONTAINER=1 is set (set
# below), so an unattended, unrestricted agent never runs on the operator's
# bare host.
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
ARG BOMLY_VERSION=0.16.0
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
RUN pip3 install --break-system-packages --quiet pip-audit
RUN curl -fsSL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# --- Harness Python deps ---
COPY harness/requirements.txt /tmp/harness-requirements.txt
RUN pip3 install --break-system-packages --quiet -r /tmp/harness-requirements.txt

# --- Pre-warm Maven's local repo so the api-java scan/build is fully offline
#     inside the container (see fixtures/api-java/README.md) ---
COPY fixtures/api-java/pom.xml /tmp/warm-pom/pom.xml
RUN cd /tmp/warm-pom && mvn -q dependency:go-offline && rm -rf /tmp/warm-pom

WORKDIR /work
