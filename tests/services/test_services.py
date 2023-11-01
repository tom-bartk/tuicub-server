from unittest.mock import Mock, create_autospec, patch

import pytest

from src.tuicubserver.common.config import Config
from src.tuicubserver.messages.service import MessagesService
from src.tuicubserver.repositories import Repositories
from src.tuicubserver.services import Services, get_valid_tilesets
from src.tuicubserver.services.auth import AuthService
from src.tuicubserver.services.gamerooms import GameroomsService
from src.tuicubserver.services.games import GamesService
from src.tuicubserver.services.users import UsersService


@pytest.fixture()
def mock_open() -> Mock:
    context_manager = Mock()
    context_manager.__enter__ = Mock()
    context_manager.__exit__ = Mock()
    return context_manager


@pytest.fixture()
def config() -> Config:
    config = create_autospec(Config)
    config.messages_secret = "foo"
    return config


@pytest.fixture()
def repositories() -> Repositories:
    return create_autospec(Repositories)


class TestServices:
    def test_creates_valid_instances(self, config, repositories) -> None:
        sut = Services(repositories=repositories, config=config)

        assert isinstance(sut.auth, AuthService)
        assert isinstance(sut.games, GamesService)
        assert isinstance(sut.gamerooms, GameroomsService)
        assert isinstance(sut.messages, MessagesService)
        assert isinstance(sut.users, UsersService)


class TestGetValidTilesets:
    def test_returns_valid_tilesets_getter(self, mock_open) -> None:
        fp = Mock()
        mock_open.__enter__.return_value = fp
        expected = frozenset([(1, 2, 3), (4, 5, 6)])

        with patch("builtins.open", return_value=mock_open) as mocked_open, patch(
            "json.load", return_value=[[1, 2, 3], [4, 5, 6]]
        ) as mocked_load:
            sut = get_valid_tilesets("foo")
            result = sut()

            mocked_open.assert_called_with("foo")
            mocked_load.assert_called_once_with(fp)
            assert result == expected
