from unittest.mock import Mock, create_autospec
from uuid import uuid4

import pytest
from sqlalchemy import ScalarResult

from src.tuicubserver.common.errors import NotFoundError
from src.tuicubserver.models.gameroom import Gameroom
from src.tuicubserver.models.status import GameroomStatus
from src.tuicubserver.repositories.gamerooms import GameroomsRepository


@pytest.fixture()
def sut(mapper) -> GameroomsRepository:
    return GameroomsRepository(mapper=mapper)


class TestGetGamerooms:
    def test_returns_list_of_mapped_scalars(self, sut, session, mapper) -> None:
        mapping_result = Mock()
        expected = [mapping_result, mapping_result]
        mapper.to_domain_gameroom = Mock(return_value=mapping_result)

        scalars = create_autospec(ScalarResult)
        scalars.all = Mock(return_value=[Mock(), Mock()])
        session.scalars = Mock(return_value=scalars)

        result = sut.get_gamerooms(session=session)

        assert result == expected


class TestGetGameroomById:
    def test_when_gameroom_is_deleted__raises_not_found_error(
        self, sut, session, mapper
    ) -> None:
        gameroom = create_autospec(Gameroom)
        gameroom.status = GameroomStatus.DELETED
        mapper.to_domain_gameroom = Mock(return_value=gameroom)

        with pytest.raises(NotFoundError):
            sut.get_gameroom_by_id(session=session, id=uuid4())

    def test_returns_mapped_db_model(self, sut, session, mapper) -> None:
        expected = Mock()
        mapper.to_domain_gameroom = Mock(return_value=expected)

        result = sut.get_gameroom_by_id(session=session, id=uuid4())

        assert result == expected


class TestSaveGameroom:
    def test_uses_gameroom_mapper(self, sut, session, mapper, gameroom) -> None:
        sut.save_gameroom(session=session, gameroom=gameroom)

        mapper.to_db_gameroom.assert_called_once_with(gameroom)

    def test_uses_gameroom_db_mapper(self, sut, session, mapper, gameroom) -> None:
        expected = Mock()
        session.merge = Mock(return_value=expected)

        sut.save_gameroom(session=session, gameroom=gameroom)

        mapper.to_domain_gameroom.assert_called_once_with(expected)

    def test_returns_gameroom_db_mapper_result(
        self, sut, session, mapper, gameroom
    ) -> None:
        expected = Mock()
        mapper.to_domain_gameroom = Mock(return_value=expected)

        result = sut.save_gameroom(session=session, gameroom=gameroom)

        assert result == expected


class TestDeleteGameroom:
    def test_uses_gameroom_mapper(self, sut, session, mapper, gameroom) -> None:
        sut.save_gameroom(session=session, gameroom=gameroom)

        mapper.to_db_gameroom.assert_called_once_with(gameroom)

    def test_uses_gameroom_db_mapper(self, sut, session, mapper, gameroom) -> None:
        expected = Mock()
        session.merge = Mock(return_value=expected)

        sut.save_gameroom(session=session, gameroom=gameroom)

        mapper.to_domain_gameroom.assert_called_once_with(expected)

    def test_deletes_merged_db_gameroom(self, sut, session, gameroom) -> None:
        expected = Mock()
        session.merge = Mock(return_value=expected)

        sut.delete_gameroom(session=session, gameroom=gameroom)

        session.delete.assert_called_once_with(expected)
