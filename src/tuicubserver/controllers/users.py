from typing import Any

from marshmallow import fields, validate

from ..common.context import BaseContext
from ..models.dto import UserDto
from ..services.users import UsersService
from .base import BaseBodySchema, BaseController


class UsersController(BaseController):
    """The controller for the users resource."""

    __slots__ = ("_users_service",)

    def __init__(self, users_service: UsersService, *args: Any, **kwargs: Any):
        """Initialize new controller.

        Args:
            users_service (UsersService): The users service.
            args (Any): Additional positional arguments.
            kwargs (Any): Additional keyword arguments.
        """
        self._users_service: UsersService = users_service
        super().__init__(*args, **kwargs)

    def create_user(self, context: BaseContext) -> dict:
        """Create a new user.

        The user's name must be present in the request body and cannot be empty.

        Args:
            context (BaseContext): The request context.

        Returns:
            The created user and the authentication token.

        Raises:
            ValidationError: Raised when the name is missing form the request body
                or is empty.
        """
        body: dict = self._deserialize_json(CreateUserBodySchema())
        user, token = self._users_service.create_user(context, name=body["name"])
        return {"user": UserDto.create(user).serialize(), "token": token.token}


class CreateUserBodySchema(BaseBodySchema):
    """The schema of the create user request body."""

    name = fields.Str(
        validate=validate.Length(min=1, error="Name cannot be empty."),
        required=True,
        error_messages={
            "required": "A valid name is required.",
            "null": "Name cannot be null.",
        },
    )
