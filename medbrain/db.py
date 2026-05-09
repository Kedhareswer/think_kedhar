"""SQLAlchemy engine + session factory."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from medbrain.config import DB_PATH, ensure_brain_dirs
from medbrain.models import Base


def _engine_url() -> str:
    ensure_brain_dirs()
    return f"sqlite:///{DB_PATH}"


engine = create_engine(_engine_url(), echo=False, future=True)
SessionFactory = sessionmaker(engine, expire_on_commit=False, future=True)


def init_schema() -> None:
    """Create all tables. Idempotent."""
    ensure_brain_dirs()
    Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional session. Commits on success, rolls back on exception."""
    sess = SessionFactory()
    try:
        yield sess
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    finally:
        sess.close()
