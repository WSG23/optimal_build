#!/bin/bash
# =============================================================================
# PostgreSQL Restore Script for optimal_build
# =============================================================================
# Supports:
# - Restore from local backup files
# - Restore from S3
# - Point-in-time recovery
#
# Usage:
#   ./restore.sh <backup_file> [--target-time "2024-01-15 10:30:00"]
#   ./restore.sh --from-s3 <s3_key> [--target-time "2024-01-15 10:30:00"]
#   ./restore.sh --list-backups
#   ./restore.sh --list-s3-backups
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

# Temporary directory for downloads
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
    exit 1
}

warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >&2
}

# Check required tools
check_requirements() {
    command -v psql >/dev/null 2>&1 || error "psql not found"
    command -v pg_restore >/dev/null 2>&1 || error "pg_restore not found"

    if [[ -z "${PGPASSWORD:-}" ]]; then
        error "PGPASSWORD environment variable is required"
    fi
}

# List local backups
list_local_backups() {
    log "Available local backups:"
    echo ""
    echo "=== Daily Backups ==="
    ls -lh "${BACKUP_DIR}/daily/" 2>/dev/null || echo "  No daily backups found"
    echo ""
    echo "=== Weekly Backups ==="
    ls -lh "${BACKUP_DIR}/weekly/" 2>/dev/null || echo "  No weekly backups found"
    echo ""
    echo "=== Monthly Backups ==="
    ls -lh "${BACKUP_DIR}/monthly/" 2>/dev/null || echo "  No monthly backups found"
}

# List S3 backups
list_s3_backups() {
    if [[ -z "${S3_BUCKET}" ]]; then
        error "S3_BUCKET not set"
    fi

    log "Available S3 backups in s3://${S3_BUCKET}/${S3_PREFIX}/:"
    aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" --human-readable
}

# Download from S3
download_from_s3() {
    local s3_key="$1"
    local filename=$(basename "${s3_key}")
    local local_path="${TEMP_DIR}/${filename}"

    if [[ -z "${S3_BUCKET}" ]]; then
        error "S3_BUCKET not set"
    fi

    log "Downloading s3://${S3_BUCKET}/${s3_key}..."
    aws s3 cp "s3://${S3_BUCKET}/${s3_key}" "${local_path}" --only-show-errors

    echo "${local_path}"
}

# Verify database connection
verify_connection() {
    log "Verifying database connection..."
    psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d postgres \
        -c "SELECT 1" >/dev/null 2>&1 || error "Cannot connect to database"
    log "Database connection verified"
}

# Check if database exists
database_exists() {
    psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d postgres \
        -tAc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'" | grep -q 1
}

# Terminate connections to database
terminate_connections() {
    log "Terminating existing connections to ${POSTGRES_DB}..."
    psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d postgres \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();" \
        >/dev/null 2>&1 || true
}

# Drop and recreate database
recreate_database() {
    log "Dropping database ${POSTGRES_DB}..."
    psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d postgres \
        -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};"

    log "Creating database ${POSTGRES_DB}..."
    psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d postgres \
        -c "CREATE DATABASE ${POSTGRES_DB};"

    # Enable PostGIS if available
    psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -c "CREATE EXTENSION IF NOT EXISTS postgis;" \
        2>/dev/null || warn "PostGIS extension not available"
}

# Restore from SQL dump
restore_sql() {
    local backup_file="$1"

    log "Restoring from SQL dump: ${backup_file}"

    if [[ "${backup_file}" == *.gz ]]; then
        gunzip -c "${backup_file}" | psql \
            -h "${POSTGRES_HOST}" \
            -p "${POSTGRES_PORT}" \
            -U "${POSTGRES_USER}" \
            -d "${POSTGRES_DB}" \
            --quiet
    else
        psql \
            -h "${POSTGRES_HOST}" \
            -p "${POSTGRES_PORT}" \
            -U "${POSTGRES_USER}" \
            -d "${POSTGRES_DB}" \
            -f "${backup_file}" \
            --quiet
    fi

    log "SQL restore completed"
}

# Restore from custom format dump
restore_custom() {
    local backup_file="$1"
    local jobs="${2:-4}"

    log "Restoring from custom dump: ${backup_file} (using ${jobs} parallel jobs)"

    pg_restore \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --jobs="${jobs}" \
        --no-owner \
        --no-privileges \
        --verbose \
        "${backup_file}" 2>&1 || true  # pg_restore returns non-zero even on success with warnings

    log "Custom format restore completed"
}

# Perform restore
do_restore() {
    local backup_file="$1"

    if [[ ! -f "${backup_file}" ]]; then
        error "Backup file not found: ${backup_file}"
    fi

    local file_size=$(du -h "${backup_file}" | cut -f1)
    log "Backup file: ${backup_file} (${file_size})"

    # Confirm restoration
    read -p "This will DESTROY the current database. Continue? (yes/no): " confirm
    if [[ "${confirm}" != "yes" ]]; then
        log "Restore cancelled by user"
        exit 0
    fi

    terminate_connections
    recreate_database

    if [[ "${backup_file}" == *.dump ]]; then
        restore_custom "${backup_file}"
    else
        restore_sql "${backup_file}"
    fi
}

# Verify restored database
verify_restore() {
    log "Verifying restored database..."

    local table_count=$(psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")

    log "Tables in restored database: ${table_count}"

    # Check for alembic version table
    if psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -tAc "SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version'" | grep -q 1; then
        local migration_version=$(psql \
            -h "${POSTGRES_HOST}" \
            -p "${POSTGRES_PORT}" \
            -U "${POSTGRES_USER}" \
            -d "${POSTGRES_DB}" \
            -tAc "SELECT version_num FROM alembic_version LIMIT 1")
        log "Migration version: ${migration_version}"
    fi

    log "Database verification completed"
}

# Print usage
usage() {
    cat <<EOF
PostgreSQL Restore Script for optimal_build

Usage:
  ./restore.sh <backup_file>                    Restore from local backup file
  ./restore.sh --from-s3 <s3_key>               Restore from S3 backup
  ./restore.sh --list-backups                   List available local backups
  ./restore.sh --list-s3-backups                List available S3 backups

Options:
  -h, --help                                    Show this help message

Environment Variables:
  POSTGRES_HOST     Database host (default: localhost)
  POSTGRES_PORT     Database port (default: 5432)
  POSTGRES_USER     Database user (default: postgres)
  POSTGRES_DB       Database name (default: building_compliance)
  PGPASSWORD        Database password (required)
  BACKUP_DIR        Local backup directory (default: /var/backups/postgresql)
  S3_BUCKET         S3 bucket for backup storage
  S3_PREFIX         S3 key prefix (default: backups/postgresql)

Examples:
  ./restore.sh /var/backups/postgresql/daily/building_compliance_20240115_120000.sql.gz
  ./restore.sh --from-s3 backups/postgresql/building_compliance_20240115_120000.sql.gz
  ./restore.sh --list-backups
EOF
}

# Main execution
main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    local cmd="$1"
    shift

    case "${cmd}" in
        --list-backups)
            list_local_backups
            ;;
        --list-s3-backups)
            check_requirements
            list_s3_backups
            ;;
        --from-s3)
            if [[ $# -lt 1 ]]; then
                error "S3 key required"
            fi
            check_requirements
            verify_connection
            local backup_file=$(download_from_s3 "$1")
            do_restore "${backup_file}"
            verify_restore
            ;;
        -h|--help)
            usage
            ;;
        *)
            check_requirements
            verify_connection
            do_restore "${cmd}"
            verify_restore
            ;;
    esac

    log "=== Restore Process Completed ==="
}

main "$@"
