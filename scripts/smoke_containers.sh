#!/usr/bin/env bash
set -euo pipefail

API_IMAGE="${API_IMAGE:-optimal-build-backend:smoke}"
WEB_IMAGE="${WEB_IMAGE:-optimal-build-frontend:smoke}"

API_PORT="${API_PORT:-18080}"
WEB_PORT="${WEB_PORT:-18081}"

NETWORK="ob-smoke-$(date +%s)"
API_CONTAINER="${NETWORK}-api"
WEB_CONTAINER="${NETWORK}-web"

cleanup() {
  docker rm -f "${API_CONTAINER}" "${WEB_CONTAINER}" >/dev/null 2>&1 || true
  docker network rm "${NETWORK}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "==> Building backend image (${API_IMAGE})"
docker build -t "${API_IMAGE}" -f backend/Dockerfile backend

echo "==> Building frontend image (${WEB_IMAGE})"
docker build \
  --build-arg "VITE_API_BASE_URL=http://127.0.0.1:${API_PORT}" \
  -t "${WEB_IMAGE}" \
  -f frontend/Dockerfile \
  .

echo "==> Creating network (${NETWORK})"
docker network create "${NETWORK}" >/dev/null

echo "==> Starting backend container"
docker run -d --name "${API_CONTAINER}" --network "${NETWORK}" -p "${API_PORT}:8080" \
  -e SECRET_KEY="smoke-test-secret-key" \
  -e ENVIRONMENT="development" \
  "${API_IMAGE}" >/dev/null

echo "==> Waiting for backend /health"
ok=""
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1; then
    ok="1"
    break
  fi
  sleep 1
done
if [[ -z "${ok}" ]]; then
  echo "Backend did not become ready" >&2
  docker ps -a --filter "name=${API_CONTAINER}" >&2 || true
  docker logs --tail=200 "${API_CONTAINER}" >&2 || true
  exit 1
fi
health="$(curl -fsS "http://127.0.0.1:${API_PORT}/health")"
echo "${health}" | grep -q '"status"' || { echo "Backend /health missing status" >&2; exit 1; }
echo "${health}" | grep -q '"service"' || { echo "Backend /health missing service" >&2; exit 1; }

echo "==> Starting frontend container"
docker run -d --name "${WEB_CONTAINER}" --network "${NETWORK}" -p "${WEB_PORT}:8080" \
  "${WEB_IMAGE}" >/dev/null

echo "==> Waiting for frontend /"
ok=""
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${WEB_PORT}/" >/dev/null 2>&1; then
    ok="1"
    break
  fi
  sleep 1
done
if [[ -z "${ok}" ]]; then
  echo "Frontend did not become ready" >&2
  docker ps -a --filter "name=${WEB_CONTAINER}" >&2 || true
  docker logs --tail=200 "${WEB_CONTAINER}" >&2 || true
  exit 1
fi

html="$(curl -fsS "http://127.0.0.1:${WEB_PORT}/")"
echo "${html}" | grep -Eqi "<!doctype html>|<div id=\"root\"" || {
  echo "Frontend did not return expected HTML" >&2
  exit 1
}

echo "OK"
