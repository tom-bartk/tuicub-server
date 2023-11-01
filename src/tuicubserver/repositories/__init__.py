from ..models.mapper import Mapper
from .gamerooms import GameroomsRepository
from .games import GamesRepository
from .users import UsersRepository


class Repositories:
    @property
    def games(self) -> GamesRepository:
        return self._games

    @property
    def gamerooms(self) -> GameroomsRepository:
        return self._gamerooms

    @property
    def users(self) -> UsersRepository:
        return self._users

    def __init__(self) -> None:
        mapper = Mapper()
        self._games: GamesRepository = GamesRepository(mapper=mapper)
        self._gamerooms: GameroomsRepository = GameroomsRepository(mapper=mapper)
        self._users: UsersRepository = UsersRepository(mapper=mapper)
