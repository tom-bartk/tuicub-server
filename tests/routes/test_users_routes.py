from collections.abc import Callable
from unittest.mock import create_autospec

import pytest

from src.tuicubserver.controllers.users import UsersController
from src.tuicubserver.routes.users import attach_users_routes


@pytest.fixture()
def users_controller() -> UsersController:
    return create_autospec(UsersController)


@pytest.fixture()
def sut(users_controller, with_base_context, app) -> Callable[[], None]:
    def wrapped() -> None:
        attach_users_routes(
            app=app, controller=users_controller, with_base_context=with_base_context
        )

    return wrapped


class TestPostUsers:
    def test_calls_controller_create_user(
        self, sut, users_controller, flask_client
    ) -> None:
        sut()
        flask_client.post("/users")

        users_controller.create_user.assert_called_once()
