#!/usr/bin/env bash
set -euo pipefail

require() {
  if [[ -z "${!1:-}" ]]; then
    echo "Missing required env var: $1" >&2
    exit 2
  fi
}

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-}"
BUCKET_PREFIX="${BUCKET_PREFIX:-}"

require PROJECT_ID
require REGION
require BUCKET_PREFIX

for suffix in imports exports documents; do
  bucket="gs://${BUCKET_PREFIX}-${suffix}"
  echo "==> Creating bucket: ${bucket}"
  gcloud storage buckets create "${bucket}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access \
    --quiet || true
done

echo "==> Done"
