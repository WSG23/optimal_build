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
CLOUDSQL_INSTANCE="${CLOUDSQL_INSTANCE:-}"
CLOUDSQL_DB="${CLOUDSQL_DB:-building_compliance}"
CLOUDSQL_USER="${CLOUDSQL_USER:-app}"

require PROJECT_ID
require REGION
require CLOUDSQL_INSTANCE

echo "==> Creating Cloud SQL Postgres instance: ${CLOUDSQL_INSTANCE}"
gcloud sql instances create "${CLOUDSQL_INSTANCE}" \
  --project="${PROJECT_ID}" \
  --database-version=POSTGRES_15 \
  --region="${REGION}" \
  --cpu=2 \
  --memory=8GB \
  --storage-type=SSD \
  --storage-size=50 \
  --backup-start-time=03:00 \
  --quiet

echo "==> Creating database: ${CLOUDSQL_DB}"
gcloud sql databases create "${CLOUDSQL_DB}" \
  --instance="${CLOUDSQL_INSTANCE}" \
  --project="${PROJECT_ID}" \
  --quiet

echo "==> Creating user: ${CLOUDSQL_USER}"
echo "Choose a strong password when prompted."
gcloud sql users create "${CLOUDSQL_USER}" \
  --instance="${CLOUDSQL_INSTANCE}" \
  --project="${PROJECT_ID}"

echo "==> Done. Next: enable PostGIS with 'CREATE EXTENSION postgis;'"
