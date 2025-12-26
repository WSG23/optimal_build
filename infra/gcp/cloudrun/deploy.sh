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
GAR_REPOSITORY="${GAR_REPOSITORY:-}"
API_SERVICE="${API_SERVICE:-}"
WEB_SERVICE="${WEB_SERVICE:-}"
MIGRATE_JOB="${MIGRATE_JOB:-}"
CLOUDSQL_INSTANCE="${CLOUDSQL_INSTANCE:-}"

require PROJECT_ID
require REGION
require GAR_REPOSITORY
require API_SERVICE
require WEB_SERVICE

IMAGE_API="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY}/api:$(git rev-parse --short HEAD)"
IMAGE_WEB="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY}/web:$(git rev-parse --short HEAD)"

deploy_api() {
  echo "Building backend image: ${IMAGE_API}"
  docker build -t "${IMAGE_API}" -f backend/Dockerfile backend
  docker push "${IMAGE_API}"

  echo "Deploying Cloud Run service: ${API_SERVICE}"
  args=(run deploy "${API_SERVICE}" --image "${IMAGE_API}" --region "${REGION}" --platform managed --allow-unauthenticated)
  if [[ -n "${CLOUDSQL_INSTANCE}" ]]; then
    args+=(--add-cloudsql-instances "${CLOUDSQL_INSTANCE}")
  fi
  gcloud "${args[@]}"

  gcloud run services describe "${API_SERVICE}" --region "${REGION}" --format='value(status.url)'
}

deploy_web() {
  local api_url="$1"
  if [[ -z "${api_url}" ]]; then
    echo "API URL is required to build the frontend (VITE_API_BASE_URL)." >&2
    exit 2
  fi

  echo "Building frontend image: ${IMAGE_WEB} (VITE_API_BASE_URL=${api_url})"
  docker build \
    --build-arg "VITE_API_BASE_URL=${api_url}" \
    -t "${IMAGE_WEB}" \
    -f frontend/Dockerfile \
    .
  docker push "${IMAGE_WEB}"

  echo "Deploying Cloud Run service: ${WEB_SERVICE}"
  gcloud run deploy "${WEB_SERVICE}" \
    --image "${IMAGE_WEB}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated
}

migrate() {
  if [[ -z "${MIGRATE_JOB}" ]]; then
    echo "Set MIGRATE_JOB (e.g. optimal-build-migrate) before running migrations." >&2
    exit 2
  fi

  echo "Deploying migration job: ${MIGRATE_JOB}"
  args=(run jobs deploy "${MIGRATE_JOB}" --image "${IMAGE_API}" --region "${REGION}" --command python --args "-m","backend.migrations","alembic","upgrade","head")
  if [[ -n "${CLOUDSQL_INSTANCE}" ]]; then
    args+=(--add-cloudsql-instances "${CLOUDSQL_INSTANCE}")
  fi
  gcloud "${args[@]}"

  echo "Executing migration job: ${MIGRATE_JOB}"
  gcloud run jobs execute "${MIGRATE_JOB}" --region "${REGION}" --wait
}

cmd="${1:-deploy}"
case "${cmd}" in
  deploy)
    api_url="$(deploy_api)"
    deploy_web "${api_url}"
    ;;
  migrate)
    migrate
    ;;
  *)
    echo "Usage: $0 [deploy|migrate]" >&2
    exit 2
    ;;
esac
