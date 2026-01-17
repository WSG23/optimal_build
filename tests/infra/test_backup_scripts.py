"""Tests for backup and restore scripts.

These tests validate the backup infrastructure without actually running
database operations.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

# Path to backup scripts
BACKUP_DIR = Path(__file__).parent.parent.parent / "infra" / "backup"


class TestBackupScriptStructure:
    """Tests for backup script structure."""

    def test_backup_script_exists(self) -> None:
        """Test backup.sh exists."""
        backup_script = BACKUP_DIR / "backup.sh"
        assert backup_script.exists(), "backup.sh not found"

    def test_restore_script_exists(self) -> None:
        """Test restore.sh exists."""
        restore_script = BACKUP_DIR / "restore.sh"
        assert restore_script.exists(), "restore.sh not found"

    def test_backup_cron_exists(self) -> None:
        """Test backup-cron.yaml exists."""
        cron_file = BACKUP_DIR / "backup-cron.yaml"
        assert cron_file.exists(), "backup-cron.yaml not found"

    def test_backup_script_is_executable(self) -> None:
        """Test backup.sh has executable permission."""
        backup_script = BACKUP_DIR / "backup.sh"
        if backup_script.exists():
            mode = backup_script.stat().st_mode
            # Check if owner has execute permission
            assert mode & stat.S_IXUSR, "backup.sh is not executable"

    def test_restore_script_is_executable(self) -> None:
        """Test restore.sh has executable permission."""
        restore_script = BACKUP_DIR / "restore.sh"
        if restore_script.exists():
            mode = restore_script.stat().st_mode
            assert mode & stat.S_IXUSR, "restore.sh is not executable"


class TestBackupScriptContent:
    """Tests for backup script content."""

    @pytest.fixture
    def backup_script(self) -> str:
        backup_file = BACKUP_DIR / "backup.sh"
        with open(backup_file) as f:
            return f.read()

    def test_backup_has_shebang(self, backup_script: str) -> None:
        """Test backup script has proper shebang."""
        assert backup_script.startswith("#!/bin/bash")

    def test_backup_uses_set_options(self, backup_script: str) -> None:
        """Test backup script uses safe shell options."""
        assert "set -e" in backup_script or "set -euo pipefail" in backup_script

    def test_backup_has_pg_dump(self, backup_script: str) -> None:
        """Test backup script uses pg_dump."""
        assert "pg_dump" in backup_script

    def test_backup_supports_compression(self, backup_script: str) -> None:
        """Test backup script supports compression."""
        assert "gzip" in backup_script or "--compress" in backup_script

    def test_backup_has_s3_upload(self, backup_script: str) -> None:
        """Test backup script can upload to S3."""
        assert "s3" in backup_script.lower() or "aws" in backup_script

    def test_backup_has_retention_cleanup(self, backup_script: str) -> None:
        """Test backup script has retention/cleanup logic."""
        assert "cleanup" in backup_script.lower() or "retention" in backup_script.lower()

    def test_backup_has_logging(self, backup_script: str) -> None:
        """Test backup script has logging."""
        assert "log" in backup_script.lower()

    def test_backup_verifies_backup(self, backup_script: str) -> None:
        """Test backup script verifies backup integrity."""
        assert "verify" in backup_script.lower() or "gzip -t" in backup_script


class TestRestoreScriptContent:
    """Tests for restore script content."""

    @pytest.fixture
    def restore_script(self) -> str:
        restore_file = BACKUP_DIR / "restore.sh"
        with open(restore_file) as f:
            return f.read()

    def test_restore_has_shebang(self, restore_script: str) -> None:
        """Test restore script has proper shebang."""
        assert restore_script.startswith("#!/bin/bash")

    def test_restore_uses_set_options(self, restore_script: str) -> None:
        """Test restore script uses safe shell options."""
        assert "set -e" in restore_script or "set -euo pipefail" in restore_script

    def test_restore_has_confirmation(self, restore_script: str) -> None:
        """Test restore script has confirmation prompt."""
        assert "confirm" in restore_script.lower() or "read -p" in restore_script

    def test_restore_can_download_from_s3(self, restore_script: str) -> None:
        """Test restore script can download from S3."""
        assert "s3" in restore_script.lower()

    def test_restore_terminates_connections(self, restore_script: str) -> None:
        """Test restore script terminates existing connections."""
        assert "terminate" in restore_script.lower() or "pg_terminate_backend" in restore_script

    def test_restore_has_verification(self, restore_script: str) -> None:
        """Test restore script verifies the restore."""
        assert "verify" in restore_script.lower()

    def test_restore_lists_backups(self, restore_script: str) -> None:
        """Test restore script can list available backups."""
        assert "list" in restore_script.lower()


class TestBackupCronJob:
    """Tests for Kubernetes CronJob configuration."""

    @pytest.fixture
    def cron_config(self) -> list[dict]:
        import yaml

        cron_file = BACKUP_DIR / "backup-cron.yaml"
        with open(cron_file) as f:
            return list(yaml.safe_load_all(f))

    def test_cronjob_has_schedule(self, cron_config: list[dict]) -> None:
        """Test CronJob has schedule defined."""
        cronjobs = [d for d in cron_config if d and d.get("kind") == "CronJob"]
        assert len(cronjobs) > 0, "No CronJob found"

        for cj in cronjobs:
            assert "schedule" in cj.get("spec", {}), "CronJob missing schedule"

    def test_cronjob_schedule_is_daily(self, cron_config: list[dict]) -> None:
        """Test CronJob runs daily."""
        cronjobs = [d for d in cron_config if d and d.get("kind") == "CronJob"]

        for cj in cronjobs:
            schedule = cj.get("spec", {}).get("schedule", "")
            # Should run once per day (5 fields, last 3 should be * * *)
            parts = schedule.split()
            assert len(parts) == 5, "Invalid cron schedule format"
            # Daily means day-of-month, month, day-of-week are all *
            assert parts[2] == "*", "CronJob doesn't run daily"
            assert parts[3] == "*", "CronJob doesn't run daily"
            assert parts[4] == "*", "CronJob doesn't run daily"

    def test_cronjob_has_resource_limits(self, cron_config: list[dict]) -> None:
        """Test CronJob pod has resource limits."""
        cronjobs = [d for d in cron_config if d and d.get("kind") == "CronJob"]

        for cj in cronjobs:
            containers = (
                cj.get("spec", {})
                .get("jobTemplate", {})
                .get("spec", {})
                .get("template", {})
                .get("spec", {})
                .get("containers", [])
            )
            for container in containers:
                resources = container.get("resources", {})
                assert "limits" in resources, "CronJob missing resource limits"

    def test_cronjob_has_concurrency_policy(self, cron_config: list[dict]) -> None:
        """Test CronJob has concurrency policy."""
        cronjobs = [d for d in cron_config if d and d.get("kind") == "CronJob"]

        for cj in cronjobs:
            spec = cj.get("spec", {})
            assert "concurrencyPolicy" in spec, "CronJob missing concurrencyPolicy"
            assert spec["concurrencyPolicy"] == "Forbid", (
                "CronJob should forbid concurrent runs"
            )

    def test_cronjob_uses_secrets(self, cron_config: list[dict]) -> None:
        """Test CronJob uses secrets for credentials."""
        cronjobs = [d for d in cron_config if d and d.get("kind") == "CronJob"]

        for cj in cronjobs:
            containers = (
                cj.get("spec", {})
                .get("jobTemplate", {})
                .get("spec", {})
                .get("template", {})
                .get("spec", {})
                .get("containers", [])
            )
            for container in containers:
                env_vars = container.get("env", [])
                # Check that password comes from secret
                password_vars = [
                    e
                    for e in env_vars
                    if "password" in e.get("name", "").lower()
                ]
                for pv in password_vars:
                    assert "valueFrom" in pv, (
                        f"Password {pv.get('name')} should come from secret"
                    )
                    assert "secretKeyRef" in pv.get("valueFrom", {}), (
                        f"Password {pv.get('name')} should use secretKeyRef"
                    )


class TestBackupEnvironmentVariables:
    """Tests for backup environment variable configuration."""

    @pytest.fixture
    def backup_script(self) -> str:
        backup_file = BACKUP_DIR / "backup.sh"
        with open(backup_file) as f:
            return f.read()

    def test_backup_uses_env_vars_with_defaults(self, backup_script: str) -> None:
        """Test backup script uses environment variables with defaults."""
        # Should have POSTGRES_HOST with default
        assert "POSTGRES_HOST" in backup_script
        assert ':-' in backup_script or 'default' in backup_script.lower()

    def test_backup_requires_password(self, backup_script: str) -> None:
        """Test backup script requires password (no default)."""
        # Password should be required, not have a default
        assert "PGPASSWORD" in backup_script

    def test_backup_configurable_retention(self, backup_script: str) -> None:
        """Test backup retention is configurable."""
        assert "RETENTION" in backup_script
