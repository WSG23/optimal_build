"""Merge migration heads before multi-tenancy.

Revision ID: 20251226_000001
Revises: 20251207_000038, 20251208_000038
Create Date: 2025-12-26
"""

revision = "20251226_000001"
down_revision = ("20251207_000038", "20251208_000038")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
