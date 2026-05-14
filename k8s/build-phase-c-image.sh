#!/usr/bin/env bash
# Build and import Phase C scraper image into Olares containerd.
#
# Run this script ON Olares (ssh olares, then run it) or via:
#   scp this script to olares:/tmp/
#   ssh olares bash /tmp/build-phase-c-image.sh
#
# Prerequisites:
#   - nerdctl available on Olares (comes with k3s/containerd install)
#   - The intelpolitics source tree synced to /tmp/intelpolitics-build/ on Olares
#
# What it does:
#   1. Creates /tmp/intelpolitics-build/ and copies the required source files.
#   2. Builds the image with nerdctl into the k8s.io containerd namespace.
#   3. Verifies the image is visible to k3s.
#
# After this script succeeds, the CronJob manual job can be fired:
#   kubectl create job phase-c-first-scrape \
#     --from=cronjob/intelpolitics-scrape-nightly \
#     -n intelpolitics-conductor

set -euo pipefail

IMAGE_TAG="intelpolitics-scraper:2026-05-13-phase-c-metrics"
BUILD_DIR="/tmp/intelpolitics-build"
# Path to venture repo on Olares — adjust if the repo is cloned elsewhere.
REPO_ROOT="${REPO_ROOT:-/root/00_FOUNDATION/ventures/intelpolitics}"

echo "=== Phase C image build ==="
echo "Tag:       $IMAGE_TAG"
echo "Build dir: $BUILD_DIR"
echo "Repo:      $REPO_ROOT"

# 1. Prepare build context.
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

cp "$REPO_ROOT/k8s/Dockerfile"       "$BUILD_DIR/Dockerfile"
cp "$REPO_ROOT/pyproject.toml"       "$BUILD_DIR/pyproject.toml"
cp "$REPO_ROOT/sources.yaml"         "$BUILD_DIR/sources.yaml"
cp "$REPO_ROOT/sources.v2.yaml"      "$BUILD_DIR/sources.v2.yaml"
cp "$REPO_ROOT/k8s/entrypoint.sh"    "$BUILD_DIR/entrypoint.sh"
cp -r "$REPO_ROOT/src"               "$BUILD_DIR/src"

echo "Build context prepared."

# 2. Build.
nerdctl --namespace=k8s.io build \
  -t "$IMAGE_TAG" \
  -f "$BUILD_DIR/Dockerfile" \
  "$BUILD_DIR/"

echo "Build complete."

# 3. Verify image is present.
nerdctl --namespace=k8s.io images | grep "intelpolitics-scraper"

echo "=== Image build SUCCESS: $IMAGE_TAG ==="
echo ""
echo "Next: apply migration 002, then fire the first scrape job:"
echo "  kubectl cp /root/00_FOUNDATION/ventures/intelpolitics/k3s/migrations/002_sources_v2.sql intelpolitics-conductor/postgres-0:/tmp/"
echo "  kubectl exec -n intelpolitics-conductor postgres-0 -- psql -U intelpolitics_app -d intelpolitics_db -f /tmp/002_sources_v2.sql"
echo "  kubectl create job phase-c-first-scrape --from=cronjob/intelpolitics-scrape-nightly -n intelpolitics-conductor"
