from unittest.mock import Mock

import pytest

from src.tuicubserver.common.errors import ValidationError
from src.tuicubserver.controllers.users import UsersController


@pytest.fixture()
def sut(
    gamerooms_service, games_service, users_service, messages_service
) -> UsersController:
    return UsersController(users_service=users_service, messages_service=messages_service)


class TestCreateUser:
    def test_when_body_valid__returns_token_and_user(
        self, sut, app, base_context, users_service, user_no_gameroom, user_token
    ):
        users_service.create_user = Mock(return_value=(user_no_gameroom, user_token))
        expected = {
            "token": user_token.token,
            "user": {"id": str(user_no_gameroom.id), "name": user_no_gameroom.name},
        }

        with app.test_request_context(json={"name": "John"}):
            result = sut.create_user(context=base_context)
            assert result == expected

    def test_when_body_valid__calls_service_with_name_from_json(
        self, sut, app, base_context, users_service, user_no_gameroom, user_token
    ):
        users_service.create_user = Mock(return_value=(user_no_gameroom, user_token))

        with app.test_request_context(json={"name": "Bob"}):
            sut.create_user(context=base_context)
            users_service.create_user.assert_called_once_with(base_context, name="Bob")

    def test_when_name_empty__raises_validation_error(self, sut, app, base_context):
        with app.test_request_context(json={"name": ""}):
            with pytest.raises(ValidationError, match="Name cannot be empty"):
                sut.create_user(context=base_context)

    def test_when_name_missing__raises_validation_error(self, sut, app, base_context):
        with app.test_request_context(json={}):
            with pytest.raises(ValidationError, match="name is required"):
                sut.create_user(context=base_context)
