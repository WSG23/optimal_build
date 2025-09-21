"""Rule pack storage primitives with optional SQLAlchemy integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Protocol

try:  # pragma: no cover - SQLAlchemy is optional in the execution environment
    from sqlalchemy import Column, DateTime, Index, Integer, String, Text, UniqueConstraint
    from sqlalchemy import delete, select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql import func

    from app.models.base import BaseModel
    from app.models.types import FlexibleJSONB

    SQLALCHEMY_INSTALLED = True
except ModuleNotFoundError:  # pragma: no cover - gracefully fall back to in-memory storage
    Column = DateTime = Index = Integer = String = Text = UniqueConstraint = object  # type: ignore[assignment]
    AsyncSession = Any  # type: ignore

    class _FuncWrapper:  # pragma: no cover - lightweight fallback
        @staticmethod
        def now() -> datetime:
            return datetime.now(timezone.utc)

    func = _FuncWrapper()
    SQLALCHEMY_INSTALLED = False


class RulePackRepository(Protocol):
    """Protocol describing minimal repository behaviour used by the API."""

    async def list(self) -> List["RulePack"]:
        """Return all persisted rule packs."""

    async def get(self, pack_id: int) -> Optional["RulePack"]:
        """Retrieve a single rule pack by identifier."""


if SQLALCHEMY_INSTALLED:  # pragma: no cover - exercised when dependency is available

    class RulePack(BaseModel):
        """Persisted rule pack definition with metadata and versioning."""

        __tablename__ = "rule_packs"

        id = Column(Integer, primary_key=True, index=True)
        key = Column(String(100), nullable=False, index=True)
        jurisdiction = Column(String(50), nullable=False, index=True)
        authority = Column(String(50), nullable=False, index=True)
        topic = Column(String(100), nullable=False, index=True)
        version = Column(String(50), nullable=False, default="v1")
        revision = Column(Integer, nullable=False, default=1)
        title = Column(String(200))
        description = Column(Text)
        metadata_json = Column("metadata", FlexibleJSONB, nullable=False, default=dict)
        rules_json = Column("rules", FlexibleJSONB, nullable=False, default=list)
        created_at = Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
        updated_at = Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        )

        __table_args__ = (
            UniqueConstraint("key", "version", "revision", name="uq_rule_pack_key_version"),
            Index("idx_rule_packs_jurisdiction_topic", "jurisdiction", "topic"),
            Index("idx_rule_packs_authority", "authority"),
        )

        @property
        def metadata(self) -> Dict[str, Any]:
            """Return metadata dictionary stored for the rule pack."""

            raw = self.metadata_json or {}
            if isinstance(raw, MutableMapping):
                return dict(raw)
            return {}

        @metadata.setter
        def metadata(self, value: Mapping[str, Any] | None) -> None:
            """Update the stored metadata."""

            if value is None:
                self.metadata_json = {}
            else:
                self.metadata_json = dict(value)

        @property
        def rules(self) -> List[Dict[str, Any]]:
            """Return the rules declared within the pack."""

            raw = self.rules_json or []
            if isinstance(raw, list):
                return [dict(item) if isinstance(item, Mapping) else item for item in raw]
            return []

        @rules.setter
        def rules(self, value: Iterable[Mapping[str, Any]] | None) -> None:
            """Set the rules contained in the rule pack."""

            if value is None:
                self.rules_json = []
            else:
                self.rules_json = [dict(item) for item in value]


else:

    @dataclass
    class RulePack:
        """Lightweight rule pack representation used when SQLAlchemy is unavailable."""

        id: Optional[int] = None
        key: str = ""
        jurisdiction: str = ""
        authority: str = ""
        topic: str = ""
        version: str = "v1"
        revision: int = 1
        title: Optional[str] = None
        description: Optional[str] = None
        metadata: Dict[str, Any] = field(default_factory=dict)
        rules: List[Dict[str, Any]] = field(default_factory=list)
        created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
        updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

        def __post_init__(self) -> None:
            self.metadata = dict(self.metadata or {})
            self.rules = [dict(item) if isinstance(item, Mapping) else item for item in self.rules]


class InMemoryRulePackRepository:
    """Simple repository storing rule packs in process memory."""

    def __init__(self) -> None:
        self._items: Dict[int, RulePack] = {}
        self._next_id = 1

    async def list(self) -> List[RulePack]:
        """Return rule packs ordered by creation timestamp."""

        return sorted(
            (self._clone(pack) for pack in self._items.values()),
            key=lambda pack: (pack.created_at, pack.id or 0),
        )

    async def get(self, pack_id: int) -> Optional[RulePack]:
        """Retrieve a rule pack by identifier."""

        item = self._items.get(int(pack_id))
        return self._clone(item) if item is not None else None

    async def add(self, pack: RulePack | Mapping[str, Any]) -> RulePack:
        """Persist a new rule pack returning the stored copy."""

        stored = self._prepare(pack)
        if stored.id is None:
            stored.id = self._next_id
            self._next_id += 1
        now = datetime.now(timezone.utc)
        stored.updated_at = now
        stored.created_at = stored.created_at or now
        self._items[int(stored.id)] = stored
        return self._clone(stored)

    async def replace_all(self, packs: Iterable[RulePack | Mapping[str, Any]]) -> List[RulePack]:
        """Replace existing rule packs with the supplied collection."""

        self.reset()
        stored: List[RulePack] = []
        for pack in packs:
            stored.append(await self.add(pack))
        return stored

    async def clear(self) -> None:
        """Remove all stored rule packs."""

        self.reset()

    def reset(self) -> None:
        """Reset repository contents synchronously."""

        self._items.clear()
        self._next_id = 1

    @staticmethod
    def _clone(pack: RulePack | None) -> RulePack:
        if pack is None:
            return None  # type: ignore[return-value]
        if SQLALCHEMY_INSTALLED:
            # When SQLAlchemy is present, ``pack`` is an ORM object. We rely on Pydantic's
            # ``from_attributes`` support, so returning the instance is acceptable.
            return pack
        return RulePack(
            id=pack.id,
            key=pack.key,
            jurisdiction=pack.jurisdiction,
            authority=pack.authority,
            topic=pack.topic,
            version=pack.version,
            revision=pack.revision,
            title=pack.title,
            description=pack.description,
            metadata=dict(pack.metadata or {}),
            rules=[dict(rule) for rule in pack.rules],
            created_at=pack.created_at,
            updated_at=pack.updated_at,
        )

    @staticmethod
    def _prepare(pack: RulePack | Mapping[str, Any]) -> RulePack:
        if isinstance(pack, RulePack):
            return pack
        return RulePack(**dict(pack))


if SQLALCHEMY_INSTALLED:  # pragma: no cover - exercised when dependency is available

    class SQLAlchemyRulePackRepository:
        """Repository backed by a SQLAlchemy ``AsyncSession``."""

        def __init__(self, session: AsyncSession) -> None:
            self._session = session

        async def list(self) -> List[RulePack]:
            result = await self._session.execute(select(RulePack).order_by(RulePack.created_at))
            return list(result.scalars().all())

        async def get(self, pack_id: int) -> Optional[RulePack]:
            return await self._session.get(RulePack, pack_id)

        async def clear(self) -> None:
            await self._session.execute(delete(RulePack))
            await self._session.commit()


_IN_MEMORY_REPOSITORY = InMemoryRulePackRepository()


def get_in_memory_repository() -> InMemoryRulePackRepository:
    """Return the process-wide in-memory repository instance."""

    return _IN_MEMORY_REPOSITORY


def reset_in_memory_repository() -> None:
    """Reset the in-memory repository to an empty state."""

    _IN_MEMORY_REPOSITORY.reset()


def get_rule_pack_repository(session: AsyncSession | None = None) -> RulePackRepository:
    """Return an appropriate repository based on environment capabilities."""

    if SQLALCHEMY_INSTALLED and session is not None:
        return SQLAlchemyRulePackRepository(session)  # type: ignore[return-value]
    return _IN_MEMORY_REPOSITORY


__all__ = [
    "RulePack",
    "RulePackRepository",
    "InMemoryRulePackRepository",
    "get_in_memory_repository",
    "reset_in_memory_repository",
    "get_rule_pack_repository",
    "SQLALCHEMY_INSTALLED",
]

if SQLALCHEMY_INSTALLED:  # pragma: no cover - exported when dependency exists
    __all__.append("SQLAlchemyRulePackRepository")

