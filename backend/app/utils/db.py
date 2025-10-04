"""Database dependency helpers."""

from typing import Callable, Generator

from sqlalchemy.orm import Session

SessionFactory = Callable[[], Session]


def session_dependency(
    factory: SessionFactory,
) -> Callable[[], Generator[Session, None, None]]:
    """Build a FastAPI dependency that yields a database session."""

    def _get_db() -> Generator[Session, None, None]:
        db = factory()
        try:
            yield db
        finally:
            db.close()

    return _get_db
