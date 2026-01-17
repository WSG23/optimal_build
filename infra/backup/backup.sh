#!/bin/bash
# =============================================================================
# PostgreSQL Backup Script for optimal_build
# =============================================================================
# Supports:
# - Local filesystem storage
# - AWS S3 storage
# - Point-in-time recovery (PITR) with WAL archiving
#
# Usage:
#   ./backup.sh [full|incremental|wal] [--upload-s3]
#
# Environment Variables:
#   POSTGRES_HOST     - Database host (default: localhost)
#   POSTGRES_PORT     - Database port (default: 5432)
#   POSTGRES_USER     - Database user (default: postgres)
#   POSTGRES_DB       - Database name (default: building_compliance)
#   PGPASSWORD        - Database password (required)
#   BACKUP_DIR        - Local backup directory (default: /var/backups/postgresql)
#   S3_BUCKET         - S3 bucket for backup storage
#   S3_PREFIX         - S3 key prefix (default: backups/postgresql)
#   RETENTION_DAYS    - Days to keep local backups (default: 7)
#   RETENTION_WEEKLY  - Weeks to keep weekly backups (default: 4)
#   RETENTION_MONTHLY - Months to keep monthly backups (default: 12)
# =============================================================================

set -euo pipefail

# Configuration with defaults
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-building_compliance}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/postgresql}"
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-backups/postgresql}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
RETENTION_WEEKLY="${RETENTION_WEEKLY:-4}"
RETENTION_MONTHLY="${RETENTION_MONTHLY:-12}"

# Timestamp formats
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE=$(date +%Y%m%d)
WEEK=$(date +%Y_W%V)
MONTH=$(date +%Y%m)

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
    exit 1
}

# Check required tools
check_requirements() {
    command -v pg_dump >/dev/null 2>&1 || error "pg_dump not found"
    command -v gzip >/dev/null 2>&1 || error "gzip not found"

    if [[ -n "${S3_BUCKET}" ]]; then
        command -v aws >/dev/null 2>&1 || error "aws-cli not found (required for S3 upload)"
    fi

    if [[ -z "${PGPASSWORD:-}" ]]; then
        error "PGPASSWORD environment variable is required"
    fi
}

# Create backup directories
init_directories() {
    mkdir -p "${BACKUP_DIR}/daily"
    mkdir -p "${BACKUP_DIR}/weekly"
    mkdir -p "${BACKUP_DIR}/monthly"
    mkdir -p "${BACKUP_DIR}/wal"
    log "Backup directories initialized"
}

# Full database backup
backup_full() {
    local backup_file="${BACKUP_DIR}/daily/${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

    log "Starting full backup of ${POSTGRES_DB}..."

    pg_dump \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --format=plain \
        --no-owner \
        --no-privileges \
        --verbose \
        2>&1 | gzip > "${backup_file}"

    local backup_size=$(du -h "${backup_file}" | cut -f1)
    log "Full backup completed: ${backup_file} (${backup_size})"

    # Create weekly backup on Sundays
    if [[ $(date +%u) -eq 7 ]]; then
        local weekly_file="${BACKUP_DIR}/weekly/${POSTGRES_DB}_${WEEK}.sql.gz"
        cp "${backup_file}" "${weekly_file}"
        log "Weekly backup created: ${weekly_file}"
    fi

    # Create monthly backup on 1st of month
    if [[ $(date +%d) -eq 01 ]]; then
        local monthly_file="${BACKUP_DIR}/monthly/${POSTGRES_DB}_${MONTH}.sql.gz"
        cp "${backup_file}" "${monthly_file}"
        log "Monthly backup created: ${monthly_file}"
    fi

    echo "${backup_file}"
}

# Custom format backup (for parallel restore)
backup_custom() {
    local backup_file="${BACKUP_DIR}/daily/${POSTGRES_DB}_${TIMESTAMP}.dump"

    log "Starting custom format backup of ${POSTGRES_DB}..."

    pg_dump \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --format=custom \
        --compress=9 \
        --verbose \
        -f "${backup_file}" \
        2>&1

    local backup_size=$(du -h "${backup_file}" | cut -f1)
    log "Custom backup completed: ${backup_file} (${backup_size})"

    echo "${backup_file}"
}

# Schema-only backup
backup_schema() {
    local backup_file="${BACKUP_DIR}/daily/${POSTGRES_DB}_schema_${TIMESTAMP}.sql"

    log "Starting schema backup of ${POSTGRES_DB}..."

    pg_dump \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --schema-only \
        --no-owner \
        --no-privileges \
        -f "${backup_file}" \
        2>&1

    log "Schema backup completed: ${backup_file}"
    echo "${backup_file}"
}

# Upload to S3
upload_to_s3() {
    local file_path="$1"
    local filename=$(basename "${file_path}")
    local s3_key="${S3_PREFIX}/${filename}"

    if [[ -z "${S3_BUCKET}" ]]; then
        log "S3_BUCKET not set, skipping S3 upload"
        return 0
    fi

    log "Uploading ${filename} to s3://${S3_BUCKET}/${s3_key}..."

    aws s3 cp \
        "${file_path}" \
        "s3://${S3_BUCKET}/${s3_key}" \
        --storage-class STANDARD_IA \
        --only-show-errors

    log "Upload completed: s3://${S3_BUCKET}/${s3_key}"
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."

    # Daily backups - keep for RETENTION_DAYS
    find "${BACKUP_DIR}/daily" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    find "${BACKUP_DIR}/daily" -name "*.dump" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true

    # Weekly backups - keep for RETENTION_WEEKLY weeks
    local weekly_days=$((RETENTION_WEEKLY * 7))
    find "${BACKUP_DIR}/weekly" -name "*.sql.gz" -mtime +${weekly_days} -delete 2>/dev/null || true

    # Monthly backups - keep for RETENTION_MONTHLY months
    local monthly_days=$((RETENTION_MONTHLY * 30))
    find "${BACKUP_DIR}/monthly" -name "*.sql.gz" -mtime +${monthly_days} -delete 2>/dev/null || true

    # WAL files older than 7 days
    find "${BACKUP_DIR}/wal" -name "*.gz" -mtime +7 -delete 2>/dev/null || true

    log "Cleanup completed"
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"

    log "Verifying backup integrity: ${backup_file}"

    if [[ "${backup_file}" == *.gz ]]; then
        gzip -t "${backup_file}" || error "Backup verification failed: corrupt gzip file"
    elif [[ "${backup_file}" == *.dump ]]; then
        pg_restore --list "${backup_file}" >/dev/null || error "Backup verification failed: corrupt dump file"
    fi

    log "Backup verification passed"
}

# Main execution
main() {
    local backup_type="${1:-full}"
    local upload_s3="${2:-}"

    log "=== PostgreSQL Backup Started ==="
    log "Database: ${POSTGRES_DB}@${POSTGRES_HOST}:${POSTGRES_PORT}"
    log "Backup type: ${backup_type}"

    check_requirements
    init_directories

    local backup_file=""

    case "${backup_type}" in
        full)
            backup_file=$(backup_full)
            ;;
        custom)
            backup_file=$(backup_custom)
            ;;
        schema)
            backup_file=$(backup_schema)
            ;;
        *)
            error "Unknown backup type: ${backup_type}. Use: full, custom, or schema"
            ;;
    esac

    verify_backup "${backup_file}"

    if [[ "${upload_s3}" == "--upload-s3" ]]; then
        upload_to_s3 "${backup_file}"
    fi

    cleanup_old_backups

    log "=== PostgreSQL Backup Completed ==="
}

main "$@"
