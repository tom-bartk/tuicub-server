from __future__ import annotations

import sqlalchemy as sa

from ..models.db import DbBase


class Database:
    """The database connection."""

    @property
    def session_factory(self) -> sa.orm.sessionmaker:
        """The factory creating database sessions for requests."""
        if not self._sessionmaker:
            _sessionmaker = self._connect()
            self._sessionmaker: sa.orm.sessionmaker | None = _sessionmaker
            return _sessionmaker
        else:
            return self._sessionmaker

    def __init__(self, connstr: str):
        """Initialize new database connection.

        Args:
            connstr (str): The database connection string.
        """
        self._connstr: str = connstr
        self._sessionmaker = None

    def _connect(self) -> sa.orm.sessionmaker:
        engine: sa.Engine = sa.create_engine(
            self._connstr, echo=False, isolation_level="REPEATABLE READ"
        )
        DbBase.metadata.create_all(engine)
        return sa.orm.sessionmaker(engine, expire_on_commit=True, autoflush=True)
