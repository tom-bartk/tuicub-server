from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.tuicubserver.repositories.games import GamesRepository


@pytest.fixture()
def sut(mapper) -> GamesRepository:
    return GamesRepository(mapper=mapper)


class TestGetGameroomById:
    def test_returns_mapped_db_model(self, sut, session, mapper) -> None:
        expected = Mock()
        mapper.to_domain_game = Mock(return_value=expected)

        result = sut.get_game_by_id(session=session, id=uuid4())

        assert result == expected


class TestSaveGame:
    def test_uses_game_mapper(self, sut, session, mapper, game) -> None:
        sut.save_game(session=session, game=game)

        mapper.to_db_game.assert_called_once_with(game)

    def test_uses_game_db_mapper(self, sut, session, mapper, game) -> None:
        expected = Mock()
        session.merge = Mock(return_value=expected)

        sut.save_game(session=session, game=game)

        mapper.to_domain_game.assert_called_once_with(expected)

    def test_returns_game_db_mapper_result(self, sut, session, mapper, game) -> None:
        expected = Mock()
        mapper.to_domain_game = Mock(return_value=expected)

        result = sut.save_game(session=session, game=game)

        assert result == expected


class TestDeleteGame:
    def test_uses_game_mapper(self, sut, session, mapper, game) -> None:
        sut.save_game(session=session, game=game)

        mapper.to_db_game.assert_called_once_with(game)

    def test_uses_game_db_mapper(self, sut, session, mapper, game) -> None:
        expected = Mock()
        session.merge = Mock(return_value=expected)

        sut.save_game(session=session, game=game)

        mapper.to_domain_game.assert_called_once_with(expected)

    def test_deletes_merged_db_game(self, sut, session, game) -> None:
        expected = Mock()
        session.merge = Mock(return_value=expected)

        sut.delete_game(session=session, game=game)

        session.delete.assert_called_once_with(expected)
