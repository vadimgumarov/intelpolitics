# ventures/intelpolitics/k8s/Dockerfile
#
# Container image for the intelpolitics scrape pipeline running as a
# Kubernetes Job on Olares. Built on Olares with nerdctl per the pattern
# locked in `Vadim's Inbox/archive/ops-build-image-on-olares-2026-05-09/result.md`.
#
# Build (Ops, on Olares):
#   nerdctl --namespace=k8s.io build \
#     -t intelpolitics-scraper:2026-05-12-phase-c \
#     -f /tmp/intelpolitics-build/Dockerfile \
#     /tmp/intelpolitics-build/
#
# Image is referenced by `scrape-job.yaml` with `imagePullPolicy: Never` so k3s
# does not attempt a pull. The image lives in the local containerd namespace
# `k8s.io` only — no registry push (DR-25 supply-chain posture).
#
# Local-LLM-only invariant (DR-25): the import-linter gate at build-time
# rejects any anthropic / claude_sdk / openai dependency in the source tree.

FROM python:3.11-slim-bookworm AS base

# Pin apt cache state; pull build deps for curl_cffi (cffi → libcurl).
# We need libcurl4-openssl-dev + build-essential at build-time; libcurl4 stays
# at runtime for curl_cffi's vendored libcurl-impersonate.
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        build-essential \
        libcurl4-openssl-dev \
        libssl-dev \
        libffi-dev \
 && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Build deps as a virtualenv so the final image stays small if we ever switch
# to a multi-stage build. For now single-stage is fine — the image is run as
# a one-shot Job, not pulled on every node.
# ---------------------------------------------------------------------------

WORKDIR /app

# Copy dependency manifest first for layer-cache efficiency.
COPY pyproject.toml /app/pyproject.toml

# Install runtime Python deps. We install from pyproject.toml's [project]
# dependencies block. Patchright/Playwright is NOT installed in this image —
# the scrape-pipeline targets gov.uk Search API + speech pages with curl_cffi
# only. If a future Job needs Patchright, derive a separate image.
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir \
        "httpx>=0.27" \
        "PyYAML>=6.0" \
        "psycopg[binary]>=3.2" \
        "tenacity>=9.0" \
        "curl-cffi>=0.7" \
        "beautifulsoup4>=4.12" \
        "openpyxl>=3.1"

# Copy source. We pull only what the pipeline needs at runtime: src/.
# We deliberately exclude the Next.js app, components, fixtures, tests.
COPY src/ /app/src/
COPY sources.yaml /app/sources.yaml
COPY sources.v2.yaml /app/sources.v2.yaml

# Copy the in-cluster entrypoint.
COPY k8s/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# ---------------------------------------------------------------------------
# DR-25 local-LLM-only gate. The image MUST NOT contain anthropic /
# claude_sdk / openai imports. The gate fails the build if any source file
# under /app/src imports these.
#
# We grep for `import <lib>` / `from <lib>` patterns, not the bare word, to
# avoid false positives from prose comments (cf. the stall-prober regression
# documented in `ops-build-image-on-olares-2026-05-09/result.md` §2b).
# ---------------------------------------------------------------------------
RUN set -e; \
    if grep -RE '^[[:space:]]*(import|from)[[:space:]]+(anthropic|claude_sdk|openai)\b' /app/src; then \
        echo "DR-25 violation: forbidden LLM SDK import found in /app/src"; \
        exit 1; \
    fi

# ---------------------------------------------------------------------------
# Runtime configuration via env (all overridable in the Job manifest):
#   POSTGRES_HOST            in-cluster service name (default: postgres)
#   POSTGRES_PORT            (default: 5432)
#   POSTGRES_DB              from pg-creds secret
#   POSTGRES_USER            from pg-creds secret
#   POSTGRES_PASSWORD        from pg-creds secret
#   POSTGRES_URL             optional override — full DSN; takes precedence
#   OLLAMA_BASE_URL          (default: http://ollama.ollamaserver-shared.svc.cluster.local:11434)
#   OLLAMA_MODEL             (default: gemma4:e4b)
#   OLLAMA_TIMEOUT_SEC       (default: 60)
#   PIPELINE_MAX_ROWS        (default: 95)
#   PIPELINE_POLITICIAN_SLUG (default: starmer)
#   PIPELINE_METRICS_CSV     (default: /tmp/metrics.csv — Job ephemeral)
#   PACE_SEC                 (default: 3.0)
# ---------------------------------------------------------------------------

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    POSTGRES_HOST=postgres \
    POSTGRES_PORT=5432 \
    OLLAMA_BASE_URL=http://ollama.ollamaserver-shared.svc.cluster.local:11434 \
    OLLAMA_MODEL=gemma4:e4b \
    OLLAMA_TIMEOUT_SEC=60 \
    PIPELINE_MAX_ROWS=95 \
    PIPELINE_POLITICIAN_SLUG=starmer \
    PIPELINE_METRICS_CSV=/tmp/metrics.csv \
    PACE_SEC=3.0

ENTRYPOINT ["/app/entrypoint.sh"]
