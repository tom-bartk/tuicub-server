from collections.abc import Callable, Sequence
from typing import TypeVar
from unittest.mock import Mock, create_autospec
from uuid import UUID, uuid4

import pytest
from sqlalchemy import ScalarResult
from sqlalchemy.orm import Session

from src.tuicubserver.common.errors import InvalidIdentifierError, NotFoundError
from src.tuicubserver.models.db import DbGame
from src.tuicubserver.repositories.base import BaseRepository

_TModel = TypeVar("_TModel")
_TDbModel = TypeVar("_TDbModel")


class DummyRepository(BaseRepository):
    def get_by_id(
        self,
        session: Session,
        id: str | UUID,
        db_type: type[_TDbModel],
        mapper: Callable[[_TDbModel], _TModel],
        for_update: bool = True,
    ) -> _TModel:
        return self._get_by_id(
            session=session, id=id, db_type=db_type, mapper=mapper, for_update=for_update
        )

    def get_all(
        self,
        session: Session,
        db_type: type[_TDbModel],
        mapper: Callable[[_TDbModel], _TModel],
    ) -> Sequence[_TModel]:
        return self._get_all(session=session, db_type=db_type, mapper=mapper)

    def save(
        self,
        session: Session,
        model: _TModel,
        db_type: type[_TDbModel],
        mapper: Callable[[_TModel], _TDbModel],
        mapper_db: Callable[[_TDbModel], _TModel],
    ) -> _TModel:
        return self._save(
            session=session,
            model=model,
            db_type=db_type,
            mapper=mapper,
            mapper_db=mapper_db,
        )

    def delete(
        self,
        session: Session,
        model: _TModel,
        db_type: type[_TDbModel],
        mapper: Callable[[_TModel], _TDbModel],
    ) -> None:
        return self._delete(session=session, model=model, db_type=db_type, mapper=mapper)


@pytest.fixture()
def sut(mapper) -> DummyRepository:
    return DummyRepository(mapper=mapper)


class TestGetById:
    def test_when_id_is_invalid_uuid__raises_invalid_identifier_error(
        self, sut, session
    ) -> None:
        with pytest.raises(InvalidIdentifierError):
            sut.get_by_id(session=session, id="foo", db_type=Mock, mapper=Mock())

    def test_when_session_returns_none__raises_not_found_error(
        self, sut, session
    ) -> None:
        session.get = Mock(return_value=None)

        with pytest.raises(NotFoundError):
            sut.get_by_id(session=session, id=uuid4(), db_type=Mock, mapper=Mock())

    def test_when_session_returns_value__returns_mapping_result(
        self, sut, session
    ) -> None:
        value = Mock()
        expected = Mock()
        mapper = Mock(return_value=expected)
        session.get = Mock(return_value=value)

        result = sut.get_by_id(session=session, id=uuid4(), db_type=Mock, mapper=mapper)

        assert result == expected


class TestGetAll:
    def test_returns_list_of_mapped_scalar_values(self, sut, session) -> None:
        scalars = create_autospec(ScalarResult)
        scalars.all = Mock(return_value=[Mock(), Mock()])
        session.scalars = Mock(return_value=scalars)

        mapping_result = Mock()
        expected = [mapping_result, mapping_result]

        result = sut.get_all(
            session=session, db_type=DbGame, mapper=Mock(return_value=mapping_result)
        )

        assert result == expected


class TestSave:
    def test_merges_mapped_db_model_with_data_loaded_from_db(self, sut, session) -> None:
        expected = Mock()
        mapper = Mock(return_value=expected)

        sut.save(
            session=session, model=Mock(), db_type=Mock, mapper=mapper, mapper_db=Mock()
        )

        session.merge.assert_called_once_with(expected, load=True)

    def test_returns_mapped_model_from_merged_db_model(self, sut, session) -> None:
        expected = Mock()
        model = Mock()
        mapper_db = Mock(return_value=expected)
        session.merge = Mock(return_value=model)

        result = sut.save(
            session=session, model=model, db_type=Mock, mapper=Mock(), mapper_db=mapper_db
        )

        assert result == expected
        mapper_db.assert_called_once_with(model)


class TestDelete:
    def test_merges_mapped_db_model_with_data_loaded_from_db(self, sut, session) -> None:
        expected = Mock()
        mapper = Mock(return_value=expected)

        sut.delete(session=session, model=Mock(), db_type=Mock, mapper=mapper)

        session.merge.assert_called_once_with(expected, load=True)

    def test_deletes_merged_db_model(self, sut, session) -> None:
        expected = Mock()
        session.merge = Mock(return_value=expected)

        sut.delete(session=session, model=Mock(), db_type=Mock, mapper=Mock())

        session.delete.assert_called_once_with(expected)
