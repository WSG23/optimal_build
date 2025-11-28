"""add_voice_notes_table

Revision ID: 20251129_000026
Revises: 8706cd5fd7e5
Create Date: 2025-11-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251129_000026"
down_revision: Union[str, None] = "8706cd5fd7e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "property_voice_notes",
        sa.Column("id", sa.UUID(), primary_key=True),
        # Property Reference
        sa.Column("property_id", sa.UUID(), nullable=False),
        sa.Column("photo_id", sa.UUID(), nullable=True),
        # Audio File Details
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("filename", sa.String(255), nullable=True),
        sa.Column(
            "mime_type", sa.String(50), nullable=True, server_default="audio/webm"
        ),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Numeric(8, 2), nullable=True),
        # Recording Metadata
        sa.Column("capture_date", sa.DateTime(), nullable=True),
        sa.Column(
            "capture_location",
            sa.String(),  # Geometry stored as WKT string
            nullable=True,
        ),
        # Transcription
        sa.Column("transcript", sa.String(), nullable=True),
        sa.Column("transcript_confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column(
            "transcript_language", sa.String(10), nullable=True, server_default="en"
        ),
        # User Notes
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        # Audio Metadata
        sa.Column("audio_metadata", sa.JSON(), nullable=True),
        # Base model timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Foreign key constraints
    op.create_foreign_key(
        "fk_voice_notes_property_id",
        "property_voice_notes",
        "properties",
        ["property_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_voice_notes_photo_id",
        "property_voice_notes",
        "property_photos",
        ["photo_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Indexes for foreign keys (Rule 9)
    op.create_index("idx_voice_note_property", "property_voice_notes", ["property_id"])
    op.create_index("idx_voice_note_photo", "property_voice_notes", ["photo_id"])
    op.create_index(
        "idx_voice_note_capture_date", "property_voice_notes", ["capture_date"]
    )


def downgrade() -> None:
    # Use raw SQL with IF EXISTS guards for safe downgrade
    op.execute("DROP INDEX IF EXISTS idx_voice_note_capture_date")
    op.execute("DROP INDEX IF EXISTS idx_voice_note_photo")
    op.execute("DROP INDEX IF EXISTS idx_voice_note_property")
    op.execute(
        "ALTER TABLE IF EXISTS property_voice_notes "
        "DROP CONSTRAINT IF EXISTS fk_voice_notes_photo_id"
    )
    op.execute(
        "ALTER TABLE IF EXISTS property_voice_notes "
        "DROP CONSTRAINT IF EXISTS fk_voice_notes_property_id"
    )
    op.execute("DROP TABLE IF EXISTS property_voice_notes CASCADE")
