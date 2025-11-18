"""Compliance domain models and enums shared across jurisdictions."""

from enum import Enum


class ComplianceStatus(str, Enum):
    """BCA/URA compliance check status."""

    PENDING = "pending"  # Not yet checked
    PASSED = "passed"  # Compliant with all requirements
    WARNING = "warning"  # Minor issues, may need attention
    FAILED = "failed"  # Major violations detected


__all__ = ["ComplianceStatus"]
