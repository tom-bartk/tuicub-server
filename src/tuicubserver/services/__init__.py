from __future__ import annotations

import json
from collections.abc import Callable
from typing import TYPE_CHECKING

from theine import Cache

from ..messages.client import MessagesClient
from ..messages.message import MessageEnvelopeSchema
from ..messages.service import MessagesService
from ..repositories import Repositories
from .auth import AuthService
from .game_toolkit import GameToolkit
from .gamerooms import GameroomsService
from .games import GamesService
from .rng import RngService
from .tilesets import TilesetsService
from .users import UsersService

if TYPE_CHECKING:
    from ..common.config import Config


class Services:
    @property
    def auth(self) -> AuthService:
        return self._auth

    @property
    def games(self) -> GamesService:
        return self._games

    @property
    def gamerooms(self) -> GameroomsService:
        return self._gamerooms

    @property
    def messages(self) -> MessagesService:
        return self._messages

    @property
    def users(self) -> UsersService:
        return self._users

    def __init__(self, repositories: Repositories, config: Config) -> None:
        rng_service = RngService()
        game_toolkit = GameToolkit(
            rng_service=rng_service,
            tilesets_service=TilesetsService(
                valid_tilesets=get_valid_tilesets(
                    valid_tilesets_path="res/valid_tilesets.json"
                ),
                validity_cache=Cache("tlfu", 10000),
                values_cache=Cache("tlfu", 10000),
            ),
        )
        self._auth: AuthService = AuthService(
            users_repository=repositories.users,
            events_secret=config.events_secret,
            messages_secret=config.messages_secret,
        )
        self._games: GamesService = GamesService(
            games_repository=repositories.games,
            game_toolkit=game_toolkit,
            rng_service=rng_service,
        )
        self._gamerooms: GameroomsService = GameroomsService(
            gamerooms_repository=repositories.gamerooms,
            game_toolkit=game_toolkit,
            games_repository=repositories.games,
            games_service=self._games,
        )
        self._messages: MessagesService = MessagesService(
            client=MessagesClient(
                host=config.messages_host,
                port=config.messages_port,
                token=config.messages_secret,
                schema=MessageEnvelopeSchema(),
            )
        )
        self._users: UsersService = UsersService(
            auth_service=self._auth, users_repository=repositories.users
        )


def get_valid_tilesets(
    valid_tilesets_path: str,
) -> Callable[[], frozenset[tuple[int, ...]]]:
    def wrapped() -> frozenset[tuple[int, ...]]:
        with open(valid_tilesets_path) as fp:
            return frozenset(tuple(tileset) for tileset in json.load(fp))

    return wrapped
