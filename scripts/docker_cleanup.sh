#!/usr/bin/env bash
# Remove unused Docker containers, images, volumes, and networks created during local development.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/docker_cleanup.sh [--aggressive] [--dry-run]

By default the script prunes stopped containers, dangling images, unused volumes, and orphaned networks.
Pass --aggressive to also remove all unused images (not just dangling layers).
Use --dry-run to print the Docker commands without executing them.
USAGE
}

AGGRESSIVE=0
DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --aggressive)
      AGGRESSIVE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  if (( DRY_RUN )); then
    echo "docker CLI not available. Showing the commands that would run." >&2
  else
    echo "docker CLI not available. Install Docker Desktop or Docker Engine to use this helper." >&2
    exit 127
  fi
fi

run() {
  if (( DRY_RUN )); then
    printf 'DRY-RUN: %s\n' "$*"
  else
    "$@"
  fi
}

printf '\n🧹 Pruning stopped containers...\n'
run docker container prune -f

printf '\n🗑️  Pruning unused volumes...\n'
run docker volume prune -f

printf '\n🕸️  Pruning orphaned networks...\n'
run docker network prune -f

printf '\n📦 Pruning %s images...\n' "$( (( AGGRESSIVE )) && echo 'unused' || echo 'dangling' )"
if (( AGGRESSIVE )); then
  run docker image prune -a -f
else
  run docker image prune -f
fi

if (( DRY_RUN )); then
  printf '\n✅ Dry-run complete. No Docker commands were executed.\n'
else
  printf '\n✅ Docker cleanup complete.\n'
fi
