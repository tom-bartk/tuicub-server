from ..services import Services
from .gamerooms import GameroomsController
from .games import GamesController
from .users import UsersController


class Controllers:
    @property
    def games(self) -> GamesController:
        return self._games

    @property
    def gamerooms(self) -> GameroomsController:
        return self._gamerooms

    @property
    def users(self) -> UsersController:
        return self._users

    def __init__(self, services: Services) -> None:
        self._games: GamesController = GamesController(
            games_service=services.games,
            gamerooms_service=services.gamerooms,
            messages_service=services.messages,
        )
        self._gamerooms: GameroomsController = GameroomsController(
            auth_service=services.auth,
            gamerooms_service=services.gamerooms,
            games_service=services.games,
            users_service=services.users,
            messages_service=services.messages,
        )
        self._users: UsersController = UsersController(
            users_service=services.users, messages_service=services.messages
        )
