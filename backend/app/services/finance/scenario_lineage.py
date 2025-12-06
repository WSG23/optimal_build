"""Scenario lineage tracking with content hashes.

Provides immutable scenario versioning and lineage tracking:
- Content hashing for change detection
- Parent-child relationships for scenario derivation
- Version history tracking
- Diff computation between scenarios
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog
from backend._compat.datetime import utcnow

logger = structlog.get_logger()


class LineageAction(str, Enum):
    """Types of actions that create lineage entries."""

    CREATED = "created"
    CLONED = "cloned"
    MODIFIED = "modified"
    MERGED = "merged"
    IMPORTED = "imported"
    EXPORTED = "exported"
    LOCKED = "locked"
    UNLOCKED = "unlocked"


@dataclass
class ScenarioVersion:
    """A specific version of a scenario's assumptions."""

    version_id: str  # Unique version identifier
    scenario_id: int
    content_hash: str  # SHA-256 of serialized assumptions
    assumptions_snapshot: Dict[str, Any]
    created_at: datetime
    created_by: Optional[str] = None
    action: LineageAction = LineageAction.MODIFIED
    parent_version_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ScenarioLineage:
    """Complete lineage record for a scenario."""

    scenario_id: int
    scenario_name: str
    current_version_id: str
    current_hash: str
    parent_scenario_id: Optional[int] = None
    root_scenario_id: Optional[int] = None
    versions: List[ScenarioVersion] = field(default_factory=list)
    is_locked: bool = False
    locked_at: Optional[datetime] = None
    locked_by: Optional[str] = None
    lock_reason: Optional[str] = None


@dataclass
class LineageDiff:
    """Differences between two scenario versions."""

    from_version_id: str
    to_version_id: str
    from_hash: str
    to_hash: str
    added_keys: List[str]
    removed_keys: List[str]
    modified_keys: List[str]
    changes: Dict[str, Dict[str, Any]]  # {key: {from: val, to: val}}


class ScenarioLineageService:
    """Service for tracking scenario lineage and versioning.

    This service provides:
    - Content-addressable versioning using SHA-256 hashes
    - Parent-child lineage tracking
    - Change detection between versions
    - Scenario locking for audit trails
    """

    def __init__(self) -> None:
        # In-memory storage for lineage data
        # In production, this would be persisted to the database
        self._lineage_store: Dict[int, ScenarioLineage] = {}
        self._version_store: Dict[str, ScenarioVersion] = {}

    def compute_content_hash(self, assumptions: Dict[str, Any]) -> str:
        """Compute a deterministic SHA-256 hash of scenario assumptions.

        The hash is computed from the JSON-serialized assumptions with
        sorted keys to ensure deterministic ordering.
        """
        # Normalize and serialize assumptions
        serialized = json.dumps(assumptions, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    def create_version(
        self,
        scenario_id: int,
        assumptions: Dict[str, Any],
        action: LineageAction = LineageAction.CREATED,
        parent_version_id: Optional[str] = None,
        created_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ScenarioVersion:
        """Create a new version entry for a scenario."""
        content_hash = self.compute_content_hash(assumptions)
        timestamp = utcnow()

        version_id = (
            f"{scenario_id}-{timestamp.strftime('%Y%m%d%H%M%S')}-{content_hash[:8]}"
        )

        version = ScenarioVersion(
            version_id=version_id,
            scenario_id=scenario_id,
            content_hash=content_hash,
            assumptions_snapshot=assumptions.copy(),
            created_at=timestamp,
            created_by=created_by,
            action=action,
            parent_version_id=parent_version_id,
            notes=notes,
        )

        self._version_store[version_id] = version
        logger.info(
            "scenario_lineage.version_created",
            scenario_id=scenario_id,
            version_id=version_id,
            content_hash=content_hash,
            action=action.value,
        )

        return version

    def initialize_lineage(
        self,
        scenario_id: int,
        scenario_name: str,
        assumptions: Dict[str, Any],
        parent_scenario_id: Optional[int] = None,
        created_by: Optional[str] = None,
    ) -> ScenarioLineage:
        """Initialize lineage tracking for a new scenario."""
        # Determine action based on whether this is a clone
        action = LineageAction.CLONED if parent_scenario_id else LineageAction.CREATED

        # Create initial version
        version = self.create_version(
            scenario_id=scenario_id,
            assumptions=assumptions,
            action=action,
            created_by=created_by,
            notes=f"Initial version - {action.value}",
        )

        # Determine root scenario
        root_scenario_id = scenario_id
        if parent_scenario_id and parent_scenario_id in self._lineage_store:
            parent_lineage = self._lineage_store[parent_scenario_id]
            root_scenario_id = parent_lineage.root_scenario_id or parent_scenario_id

        # Create lineage record
        lineage = ScenarioLineage(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            current_version_id=version.version_id,
            current_hash=version.content_hash,
            parent_scenario_id=parent_scenario_id,
            root_scenario_id=root_scenario_id,
            versions=[version],
            is_locked=False,
        )

        self._lineage_store[scenario_id] = lineage
        logger.info(
            "scenario_lineage.initialized",
            scenario_id=scenario_id,
            parent_scenario_id=parent_scenario_id,
            root_scenario_id=root_scenario_id,
        )

        return lineage

    def record_modification(
        self,
        scenario_id: int,
        new_assumptions: Dict[str, Any],
        modified_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Tuple[ScenarioVersion, bool]:
        """Record a modification to a scenario.

        Returns the new version and whether the content actually changed.
        """
        lineage = self._lineage_store.get(scenario_id)
        if not lineage:
            raise ValueError(f"Scenario {scenario_id} has no lineage record")

        if lineage.is_locked:
            raise ValueError(f"Scenario {scenario_id} is locked and cannot be modified")

        # Check if content actually changed
        new_hash = self.compute_content_hash(new_assumptions)
        if new_hash == lineage.current_hash:
            logger.debug(
                "scenario_lineage.no_change",
                scenario_id=scenario_id,
                hash=new_hash,
            )
            # Return current version with no change flag
            current_version = self._version_store[lineage.current_version_id]
            return current_version, False

        # Create new version
        version = self.create_version(
            scenario_id=scenario_id,
            assumptions=new_assumptions,
            action=LineageAction.MODIFIED,
            parent_version_id=lineage.current_version_id,
            created_by=modified_by,
            notes=notes,
        )

        # Update lineage
        lineage.versions.append(version)
        lineage.current_version_id = version.version_id
        lineage.current_hash = version.content_hash

        return version, True

    def lock_scenario(
        self,
        scenario_id: int,
        locked_by: str,
        reason: Optional[str] = None,
    ) -> ScenarioLineage:
        """Lock a scenario to prevent further modifications."""
        lineage = self._lineage_store.get(scenario_id)
        if not lineage:
            raise ValueError(f"Scenario {scenario_id} has no lineage record")

        if lineage.is_locked:
            raise ValueError(f"Scenario {scenario_id} is already locked")

        lineage.is_locked = True
        lineage.locked_at = utcnow()
        lineage.locked_by = locked_by
        lineage.lock_reason = reason

        # Record lock action
        self.create_version(
            scenario_id=scenario_id,
            assumptions=self._version_store[
                lineage.current_version_id
            ].assumptions_snapshot,
            action=LineageAction.LOCKED,
            parent_version_id=lineage.current_version_id,
            created_by=locked_by,
            notes=f"Locked: {reason}" if reason else "Locked",
        )

        logger.info(
            "scenario_lineage.locked",
            scenario_id=scenario_id,
            locked_by=locked_by,
            reason=reason,
        )

        return lineage

    def unlock_scenario(
        self,
        scenario_id: int,
        unlocked_by: str,
        reason: Optional[str] = None,
    ) -> ScenarioLineage:
        """Unlock a scenario to allow modifications."""
        lineage = self._lineage_store.get(scenario_id)
        if not lineage:
            raise ValueError(f"Scenario {scenario_id} has no lineage record")

        if not lineage.is_locked:
            raise ValueError(f"Scenario {scenario_id} is not locked")

        lineage.is_locked = False
        lineage.locked_at = None
        lineage.locked_by = None
        lineage.lock_reason = None

        # Record unlock action
        self.create_version(
            scenario_id=scenario_id,
            assumptions=self._version_store[
                lineage.current_version_id
            ].assumptions_snapshot,
            action=LineageAction.UNLOCKED,
            parent_version_id=lineage.current_version_id,
            created_by=unlocked_by,
            notes=f"Unlocked: {reason}" if reason else "Unlocked",
        )

        logger.info(
            "scenario_lineage.unlocked",
            scenario_id=scenario_id,
            unlocked_by=unlocked_by,
        )

        return lineage

    def get_lineage(self, scenario_id: int) -> Optional[ScenarioLineage]:
        """Get the lineage record for a scenario."""
        return self._lineage_store.get(scenario_id)

    def get_version(self, version_id: str) -> Optional[ScenarioVersion]:
        """Get a specific version by ID."""
        return self._version_store.get(version_id)

    def get_version_history(self, scenario_id: int) -> List[ScenarioVersion]:
        """Get the complete version history for a scenario."""
        lineage = self._lineage_store.get(scenario_id)
        if not lineage:
            return []
        return sorted(lineage.versions, key=lambda v: v.created_at, reverse=True)

    def compute_diff(
        self,
        from_version_id: str,
        to_version_id: str,
    ) -> LineageDiff:
        """Compute the differences between two versions."""
        from_version = self._version_store.get(from_version_id)
        to_version = self._version_store.get(to_version_id)

        if not from_version or not to_version:
            raise ValueError("One or both versions not found")

        from_keys = set(from_version.assumptions_snapshot.keys())
        to_keys = set(to_version.assumptions_snapshot.keys())

        added_keys = list(to_keys - from_keys)
        removed_keys = list(from_keys - to_keys)
        common_keys = from_keys & to_keys

        modified_keys = []
        changes: Dict[str, Dict[str, Any]] = {}

        for key in common_keys:
            from_val = from_version.assumptions_snapshot[key]
            to_val = to_version.assumptions_snapshot[key]
            if from_val != to_val:
                modified_keys.append(key)
                changes[key] = {"from": from_val, "to": to_val}

        for key in added_keys:
            changes[key] = {"from": None, "to": to_version.assumptions_snapshot[key]}

        for key in removed_keys:
            changes[key] = {"from": from_version.assumptions_snapshot[key], "to": None}

        return LineageDiff(
            from_version_id=from_version_id,
            to_version_id=to_version_id,
            from_hash=from_version.content_hash,
            to_hash=to_version.content_hash,
            added_keys=added_keys,
            removed_keys=removed_keys,
            modified_keys=modified_keys,
            changes=changes,
        )

    def get_descendants(self, scenario_id: int) -> List[int]:
        """Get all scenarios that were derived from this scenario."""
        descendants = []
        for sid, lineage in self._lineage_store.items():
            if lineage.parent_scenario_id == scenario_id:
                descendants.append(sid)
                # Recursively find descendants
                descendants.extend(self.get_descendants(sid))
        return descendants

    def get_ancestry(self, scenario_id: int) -> List[int]:
        """Get the ancestry chain of a scenario (parent, grandparent, etc.)."""
        ancestry = []
        lineage = self._lineage_store.get(scenario_id)
        while lineage and lineage.parent_scenario_id:
            ancestry.append(lineage.parent_scenario_id)
            lineage = self._lineage_store.get(lineage.parent_scenario_id)
        return ancestry

    def has_changes(self, scenario_id: int, assumptions: Dict[str, Any]) -> bool:
        """Check if assumptions differ from current version without recording."""
        lineage = self._lineage_store.get(scenario_id)
        if not lineage:
            return True  # No lineage means it's effectively new
        new_hash = self.compute_content_hash(assumptions)
        return new_hash != lineage.current_hash


# Singleton instance
_lineage_service: Optional[ScenarioLineageService] = None


def get_scenario_lineage_service() -> ScenarioLineageService:
    """Get the scenario lineage service singleton."""
    global _lineage_service
    if _lineage_service is None:
        _lineage_service = ScenarioLineageService()
    return _lineage_service


__all__ = [
    "ScenarioLineageService",
    "ScenarioLineage",
    "ScenarioVersion",
    "LineageAction",
    "LineageDiff",
    "get_scenario_lineage_service",
]
