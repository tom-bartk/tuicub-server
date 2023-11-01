# from flasgger import Swagger
from collections.abc import Callable
from typing import Any

from flask import Flask
from flask.typing import ResponseReturnValue

from ..common.context import BaseContext
from ..controllers.users import UsersController


def attach_users_routes(
    app: Flask,
    controller: UsersController,
    with_base_context: Callable[[Callable[..., Any]], Callable[..., Any]],
) -> None:
    """Registers routes for the users resource."""

    @app.post("/users")
    @with_base_context
    def create_user(context: BaseContext) -> ResponseReturnValue:
        return controller.create_user(context=context), 201
