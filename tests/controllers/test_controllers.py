from src.tuicubserver.controllers import Controllers
from src.tuicubserver.controllers.gamerooms import GameroomsController
from src.tuicubserver.controllers.games import GamesController
from src.tuicubserver.controllers.users import UsersController


class TestControllers:
    def test_creates_valid_instances(self, services) -> None:
        sut = Controllers(services=services)

        assert isinstance(sut.games, GamesController)
        assert isinstance(sut.gamerooms, GameroomsController)
        assert isinstance(sut.users, UsersController)
