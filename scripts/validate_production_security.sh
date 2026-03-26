#!/bin/bash
#
# Production security validator for optimal_build.
#
# Validates the production deployment surface for obvious unsafe defaults:
# - placeholder secrets in production env files
# - insecure redis:// URLs in production env files
# - wildcard CORS origins in production env files/manifests
# - literal values for SECRET_KEY / S3_SECRET_KEY in Kubernetes and Helm templates
# - missing HTTPS redirect posture in ingress definitions
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VIOLATIONS=0

red() { printf '\033[0;31m%s\033[0m\n' "$1"; }
green() { printf '\033[0;32m%s\033[0m\n' "$1"; }
yellow() { printf '\033[1;33m%s\033[0m\n' "$1"; }

violation() {
  red "✗ $1"
  VIOLATIONS=$((VIOLATIONS + 1))
}

success() {
  green "✓ $1"
}

warning() {
  yellow "⚠ $1"
}

check_env_file() {
  local file="$1"
  [ -f "$file" ] || return 0

  echo "Checking env file: $file"

  if grep -qiE '^(SECRET_KEY|S3_SECRET_KEY)=.*(dev-|change-me|minioadmin|placeholder|example)' "$file"; then
    violation "placeholder or development secret value found in $file"
  fi

  if grep -qiE '^(REDIS_URL|RQ_REDIS_URL|RATE_LIMIT_REDIS_URL)=redis://' "$file"; then
    violation "insecure redis:// URL found in production env file $file"
  fi

  if grep -qiE '^(BACKEND_ALLOWED_ORIGINS|ALLOWED_ORIGINS)=.*(\*|\["\*"\])' "$file"; then
    violation "wildcard origins found in production env file $file"
  fi
}

check_secret_ref_block() {
  local file="$1"
  local env_name="$2"
  local block

  block="$(awk -v target="$env_name" '
    $0 ~ "- name: " target "$" {capture=1; next}
    capture && $0 ~ "- name: " {exit}
    capture {print}
  ' "$file")"

  if [ -z "$block" ]; then
    violation "$file does not define required env var $env_name"
    return
  fi

  if ! printf '%s\n' "$block" | grep -q 'secretKeyRef:'; then
    violation "$file configures $env_name without secretKeyRef"
  fi

  if printf '%s\n' "$block" | grep -q 'value:'; then
    violation "$file configures $env_name with a literal value"
  fi
}

check_non_wildcard_origins() {
  local file="$1"
  if [ ! -f "$file" ]; then
    return
  fi
  if grep -qE 'BACKEND_ALLOWED_ORIGINS.*(\*|\["\*"\])' "$file"; then
    violation "$file exposes wildcard BACKEND_ALLOWED_ORIGINS"
  fi
}

check_https_ingress() {
  local file="$1"
  [ -f "$file" ] || return 0

  echo "Checking ingress posture: $file"

  if ! grep -q 'alb.ingress.kubernetes.io/listen-ports:.*HTTPS' "$file"; then
    violation "$file is missing an HTTPS listener annotation"
  fi

  if ! grep -q 'ssl-redirect' "$file"; then
    violation "$file is missing HTTPS redirect configuration"
  fi
}

echo "Production Security Validation"
echo "=================================="

check_env_file "$PROJECT_ROOT/.env.production"
check_env_file "$PROJECT_ROOT/.env.production.template"
check_env_file "$PROJECT_ROOT/backend/.env.production"
check_env_file "$PROJECT_ROOT/backend/.env.production.template"

K8S_BACKEND="$PROJECT_ROOT/infra/kubernetes/backend-deployment.yaml"
HELM_BACKEND="$PROJECT_ROOT/infra/helm/optimal-build/templates/backend-deployment.yaml"
INGRESS="$PROJECT_ROOT/infra/kubernetes/ingress.yaml"

if [ -f "$K8S_BACKEND" ]; then
  echo "Checking Kubernetes backend deployment"
  check_secret_ref_block "$K8S_BACKEND" "SECRET_KEY"
  check_secret_ref_block "$K8S_BACKEND" "S3_SECRET_KEY"
  check_non_wildcard_origins "$K8S_BACKEND"
else
  warning "Skipping missing Kubernetes backend deployment manifest"
fi

if [ -f "$HELM_BACKEND" ]; then
  echo "Checking Helm backend deployment template"
  check_secret_ref_block "$HELM_BACKEND" "SECRET_KEY"
  check_secret_ref_block "$HELM_BACKEND" "S3_SECRET_KEY"
  check_non_wildcard_origins "$HELM_BACKEND"
else
  warning "Skipping missing Helm backend deployment template"
fi

check_https_ingress "$INGRESS"

echo "=================================="
if [ "$VIOLATIONS" -eq 0 ]; then
  success "All production security checks passed"
  exit 0
fi

red "✗ Found $VIOLATIONS production-readiness violation(s)"
exit 1
