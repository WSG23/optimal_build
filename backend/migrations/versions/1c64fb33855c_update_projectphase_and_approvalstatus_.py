"""update projectphase and approvalstatus enums to lowercase

Revision ID: 1c64fb33855c
Revises: a4d8de5a445b
Create Date: 2025-11-13 12:59:23.247835

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1c64fb33855c"
down_revision: Union[str, None] = "a4d8de5a445b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update projectphase and approvalstatus enum values from uppercase to lowercase to match Python enums."""

    # ProjectPhase enum mappings
    phase_mappings = {
        "CONCEPT": "concept",
        "FEASIBILITY": "feasibility",
        "DESIGN": "design",
        "APPROVAL": "approval",
        "TENDER": "tender",
        "CONSTRUCTION": "construction",
        "TESTING_COMMISSIONING": "testing_commissioning",
        "HANDOVER": "handover",
        "OPERATION": "operation",
    }

    # ApprovalStatus enum mappings
    approval_mappings = {
        "NOT_SUBMITTED": "not_submitted",
        "PENDING": "pending",
        "APPROVED": "approved",
        "APPROVED_WITH_CONDITIONS": "approved_with_conditions",
        "REJECTED": "rejected",
        "RESUBMISSION_REQUIRED": "resubmission_required",
        "EXPIRED": "expired",
    }

    # Step 1: Add new lowercase enum values for projectphase
    for new_value in phase_mappings.values():
        op.execute(f"ALTER TYPE projectphase ADD VALUE IF NOT EXISTS '{new_value}'")

    # Step 2: Add new lowercase enum values for approvalstatus
    for new_value in approval_mappings.values():
        op.execute(f"ALTER TYPE approvalstatus ADD VALUE IF NOT EXISTS '{new_value}'")

    # Step 3: Update existing data in projects table to use lowercase values
    for old_value, new_value in phase_mappings.items():
        op.execute(
            f"UPDATE projects SET current_phase = '{new_value}' "
            f"WHERE current_phase = '{old_value}'"
        )

    # Step 4: Update URA approval status
    for old_value, new_value in approval_mappings.items():
        op.execute(
            f"UPDATE projects SET ura_approval_status = '{new_value}' "
            f"WHERE ura_approval_status = '{old_value}'"
        )

    # Step 5: Update BCA approval status
    for old_value, new_value in approval_mappings.items():
        op.execute(
            f"UPDATE projects SET bca_approval_status = '{new_value}' "
            f"WHERE bca_approval_status = '{old_value}'"
        )

    # Step 6: Update SCDF approval status
    for old_value, new_value in approval_mappings.items():
        op.execute(
            f"UPDATE projects SET scdf_approval_status = '{new_value}' "
            f"WHERE scdf_approval_status = '{old_value}'"
        )

    # Note: Cannot remove old enum values in PostgreSQL without recreating the type
    # This is safe because we're adding new values and migrating data


def downgrade() -> None:
    """Revert projectphase and approvalstatus enum values back to uppercase."""

    # ProjectPhase enum mappings (reversed)
    phase_mappings = {
        "concept": "CONCEPT",
        "feasibility": "FEASIBILITY",
        "design": "DESIGN",
        "approval": "APPROVAL",
        "tender": "TENDER",
        "construction": "CONSTRUCTION",
        "testing_commissioning": "TESTING_COMMISSIONING",
        "handover": "HANDOVER",
        "operation": "OPERATION",
    }

    # ApprovalStatus enum mappings (reversed)
    approval_mappings = {
        "not_submitted": "NOT_SUBMITTED",
        "pending": "PENDING",
        "approved": "APPROVED",
        "approved_with_conditions": "APPROVED_WITH_CONDITIONS",
        "rejected": "REJECTED",
        "resubmission_required": "RESUBMISSION_REQUIRED",
        "expired": "EXPIRED",
    }

    # Revert data in projects table
    for new_value, old_value in phase_mappings.items():
        op.execute(
            f"UPDATE projects SET current_phase = '{old_value}' "
            f"WHERE current_phase = '{new_value}'"
        )

    for new_value, old_value in approval_mappings.items():
        op.execute(
            f"UPDATE projects SET ura_approval_status = '{old_value}' "
            f"WHERE ura_approval_status = '{new_value}'"
        )

    for new_value, old_value in approval_mappings.items():
        op.execute(
            f"UPDATE projects SET bca_approval_status = '{old_value}' "
            f"WHERE bca_approval_status = '{new_value}'"
        )

    for new_value, old_value in approval_mappings.items():
        op.execute(
            f"UPDATE projects SET scdf_approval_status = '{old_value}' "
            f"WHERE scdf_approval_status = '{new_value}'"
        )
