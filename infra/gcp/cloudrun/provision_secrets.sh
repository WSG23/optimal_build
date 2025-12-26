#!/usr/bin/env bash
set -euo pipefail

require() {
  if [[ -z "${!1:-}" ]]; then
    echo "Missing required env var: $1" >&2
    exit 2
  fi
}

PROJECT_ID="${PROJECT_ID:-}"
require PROJECT_ID

cmd="${1:-}"
name="${2:-}"

if [[ -z "${cmd}" || -z "${name}" ]]; then
  echo "Usage:" >&2
  echo "  PROJECT_ID=... $0 create <SECRET_NAME>" >&2
  exit 2
fi

case "${cmd}" in
  create)
    echo "Enter secret value for ${name} (stdin):" >&2
    gcloud secrets create "${name}" --project="${PROJECT_ID}" --replication-policy=automatic --quiet || true
    gcloud secrets versions add "${name}" --project="${PROJECT_ID}" --data-file=- --quiet
    ;;
  *)
    echo "Unknown command: ${cmd}" >&2
    exit 2
    ;;
esac
