"""Create initial schema."""

from alembic import op

from app.models import Base


revision = "20231201_000000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables defined in SQLAlchemy models."""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    """Drop all tables defined in SQLAlchemy models."""
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, checkfirst=True)
