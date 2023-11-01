from src.tuicubserver.repositories import Repositories
from src.tuicubserver.repositories.gamerooms import GameroomsRepository
from src.tuicubserver.repositories.games import GamesRepository
from src.tuicubserver.repositories.users import UsersRepository


class TestRepositories:
    def test_creates_valid_instances(self) -> None:
        sut = Repositories()

        assert isinstance(sut.games, GamesRepository)
        assert isinstance(sut.gamerooms, GameroomsRepository)
        assert isinstance(sut.users, UsersRepository)
