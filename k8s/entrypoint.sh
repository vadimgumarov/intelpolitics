#!/bin/sh
# ventures/intelpolitics/k8s/entrypoint.sh
#
# Pod entrypoint for the intelpolitics scrape Job on Olares.
#
# Modes (selected by PIPELINE_MODE env, default 'multi'):
#   multi  — src.pipelines.multi_politician (5 politicians sequentially)
#   single — src.pipelines.olares_value_test (legacy single-politician)
#
# Responsibilities:
#   1. Resolve POSTGRES_URL from pg-creds env vars.
#   2. Pre-flight reachability for Postgres + Ollama. Fail fast (exit 4).
#   3. Run the selected pipeline as a Python module.
#   4. Print structured summary on completion (stdout).
#
# Exit codes:
#   0   — pipeline completed (per-politician failures rolled into summary).
#   2   — required env var missing.
#   3   — pipeline raised unhandled exception OR (multi-mode) all politicians failed.
#   4   — pre-flight reachability failed.

set -eu

log() {
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    printf '%s [entrypoint] %s\n' "$ts" "$*"
}

fail() {
    code=$1
    shift
    log "FATAL: $*"
    exit "$code"
}

# ---------------------------------------------------------------------------
# 1. Resolve POSTGRES_URL
# ---------------------------------------------------------------------------

if [ -z "${POSTGRES_URL:-}" ]; then
    : "${POSTGRES_HOST:?POSTGRES_HOST not set and POSTGRES_URL not provided}"
    : "${POSTGRES_PORT:?POSTGRES_PORT not set}"
    : "${POSTGRES_DB:?POSTGRES_DB not set (expected from pg-creds secret)}"
    : "${POSTGRES_USER:?POSTGRES_USER not set (expected from pg-creds secret)}"
    : "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD not set (expected from pg-creds secret)}"

    POSTGRES_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
    export POSTGRES_URL
    log "POSTGRES_URL assembled from pg-creds env (host=${POSTGRES_HOST} port=${POSTGRES_PORT} db=${POSTGRES_DB} user=${POSTGRES_USER})"
else
    log "POSTGRES_URL provided via env (override path); skipping assembly"
fi

: "${OLLAMA_BASE_URL:?OLLAMA_BASE_URL not set}"
: "${OLLAMA_MODEL:?OLLAMA_MODEL not set}"
: "${PIPELINE_METRICS_CSV:?PIPELINE_METRICS_CSV not set}"

PIPELINE_MODE="${PIPELINE_MODE:-multi}"
log "config: mode=${PIPELINE_MODE} pace=${PACE_SEC:-3.0}s ollama=${OLLAMA_BASE_URL} model=${OLLAMA_MODEL}"
log "config: pg_target=${POSTGRES_HOST:-from-url}:${POSTGRES_PORT:-from-url}"

# ---------------------------------------------------------------------------
# 2. Pre-flight reachability
# ---------------------------------------------------------------------------

log "pre-flight: checking Postgres reachability"
python3 - <<'PY' || fail 4 "Postgres pre-flight failed"
import os, sys
import psycopg
try:
    with psycopg.connect(os.environ["POSTGRES_URL"], connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
            cur.execute("SELECT COUNT(*) FROM statements;")
            n = cur.fetchone()[0]
    print(f"[preflight] postgres OK; statements row count = {n}", flush=True)
except Exception as e:
    print(f"[preflight] postgres FAIL: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    sys.exit(1)
PY

log "pre-flight: checking Ollama reachability"
python3 - <<'PY' || fail 4 "Ollama pre-flight failed"
import os, sys
import httpx
url = os.environ["OLLAMA_BASE_URL"].rstrip("/") + "/api/tags"
model = os.environ["OLLAMA_MODEL"]
try:
    r = httpx.get(url, timeout=10)
    r.raise_for_status()
    tags = [m.get("name") for m in r.json().get("models", [])]
    present = model in tags
    print(f"[preflight] ollama OK; {len(tags)} models loaded; target {model} present={present}", flush=True)
    if not present:
        print(f"[preflight] WARN: model {model} not in /api/tags response", file=sys.stderr, flush=True)
except Exception as e:
    print(f"[preflight] ollama FAIL: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    sys.exit(1)
PY

# ---------------------------------------------------------------------------
# 3. Run the pipeline
# ---------------------------------------------------------------------------

log "starting scrape pipeline mode=${PIPELINE_MODE}"
start_epoch=$(date +%s)

set +e
if [ "${PIPELINE_MODE}" = "multi" ]; then
    POLITICIANS="${POLITICIANS:-starmer,vance,meloni,merz,von-der-leyen}"
    log "multi mode: politicians=${POLITICIANS}"
    python3 -m src.pipelines.multi_politician \
        --politicians "${POLITICIANS}" \
        --metrics-csv "${PIPELINE_METRICS_CSV}" \
        --log-level "${LOG_LEVEL:-INFO}"
    rc=$?
else
    log "single mode: politician=${PIPELINE_POLITICIAN_SLUG:-starmer} max_rows=${PIPELINE_MAX_ROWS:-95}"
    python3 -m src.pipelines.olares_value_test \
        --max-rows "${PIPELINE_MAX_ROWS:-95}" \
        --metrics-csv "${PIPELINE_METRICS_CSV}" \
        --politician-slug "${PIPELINE_POLITICIAN_SLUG:-starmer}" \
        --log-level "${LOG_LEVEL:-INFO}"
    rc=$?
fi
set -e

end_epoch=$(date +%s)
duration=$((end_epoch - start_epoch))

if [ "$rc" -ne 0 ]; then
    log "pipeline exited rc=${rc} after ${duration}s"
    exit 3
fi

log "pipeline completed rc=0 duration=${duration}s metrics_csv=${PIPELINE_METRICS_CSV}"
log "DONE"
exit 0
