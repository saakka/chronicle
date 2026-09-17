"""Moteur SQLAlchemy + session. Compatible PostgreSQL (prod) et SQLite (dev)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

_connect_args = {"check_same_thread": False, "timeout": 600} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)

if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _):  # pragma: no cover - simple tuning
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def get_session() -> Iterator[Session]:
    """Dépendance FastAPI."""
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


_MIGRATIONS = {  # colonnes ajoutées après la première version (create_all ne modifie pas les tables existantes)
    "collections": {"tradition": "VARCHAR(16) DEFAULT 'sunni'"},
    "hadiths": {"meta": "JSON"},
    "narrators": {"tradition": "VARCHAR(16) DEFAULT 'sunni'"},
    "isnad_links": {"kind": "VARCHAR(16) DEFAULT 'normal'"},
}


def init_db() -> None:
    from sqlalchemy import inspect, text

    from . import models  # noqa: F401  (enregistre les tables)

    models.Base.metadata.create_all(engine)
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, cols in _MIGRATIONS.items():
            existing = {c["name"] for c in insp.get_columns(table)}
            for col, ddl in cols.items():
                if col not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))
