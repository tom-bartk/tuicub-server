from unittest.mock import create_autospec, patch

from sqlalchemy import Engine

from src.tuicubserver.common.db import Database
from src.tuicubserver.models.db import DbBase


class TestSessionFactory:
    def test_consecutive_accesses_do_not_cause_multiple_connect_attempts(
        self,
    ) -> None:
        sut = Database(connstr="foo")
        engine = create_autospec(Engine)

        with patch(
            "sqlalchemy.create_engine", return_value=engine
        ) as mocked_create_engine, patch.object(DbBase.metadata, "create_all"), patch(
            "sqlalchemy.orm.sessionmaker"
        ):
            _ = sut.session_factory
            _ = sut.session_factory
            _ = sut.session_factory

            mocked_create_engine.assert_called_once_with(
                "foo", echo=False, isolation_level="REPEATABLE READ"
            )

    def test_connect_to_database__creates_engine_with_repeatable_read_isolation(
        self,
    ) -> None:
        sut = Database(connstr="foo")
        engine = create_autospec(Engine)

        with patch(
            "sqlalchemy.create_engine", return_value=engine
        ) as mocked_create_engine, patch.object(DbBase.metadata, "create_all"), patch(
            "sqlalchemy.orm.sessionmaker"
        ):
            _ = sut.session_factory

            mocked_create_engine.assert_called_once_with(
                "foo", echo=False, isolation_level="REPEATABLE READ"
            )

    def test_connect_to_database__creates_models(
        self,
    ) -> None:
        sut = Database(connstr="foo")
        engine = create_autospec(Engine)

        with patch("sqlalchemy.create_engine", return_value=engine), patch.object(
            DbBase.metadata, "create_all"
        ) as mocked_create_all, patch("sqlalchemy.orm.sessionmaker"):
            _ = sut.session_factory

            mocked_create_all.assert_called_once_with(engine)

    def test_connect_to_database__creates_sessionmaker_with_expire_on_commit_autoflush(
        self,
    ) -> None:
        sut = Database(connstr="foo")
        engine = create_autospec(Engine)

        with patch("sqlalchemy.create_engine", return_value=engine), patch.object(
            DbBase.metadata, "create_all"
        ), patch("sqlalchemy.orm.sessionmaker") as mocked_sessionmaker:
            _ = sut.session_factory

            mocked_sessionmaker.assert_called_once_with(
                engine, expire_on_commit=True, autoflush=True
            )
