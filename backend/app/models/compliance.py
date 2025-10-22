"""Compliance status tracking for regulatory checks.

This module defines compliance-related enums and models that can be used
across different jurisdictions and property types.
"""

from enum import Enum


class ComplianceStatus(str, Enum):
    """BCA/URA compliance check status.

    This enum represents the status of regulatory compliance checks
    for building and planning authorities (e.g., BCA, URA in Singapore).

    Can be used for:
    - Building Code Authority (BCA) compliance
    - Urban Redevelopment Authority (URA) compliance
    - Other jurisdiction-specific regulatory checks
    """

    PENDING = "pending"  # Not yet checked
    PASSED = "passed"  # Compliant with all requirements
    WARNING = "warning"  # Minor issues, may need attention
    FAILED = "failed"  # Major violations detected
