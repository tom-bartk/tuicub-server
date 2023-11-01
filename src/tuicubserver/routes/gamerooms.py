from collections.abc import Callable
from typing import Any

from flask import Flask
from flask.typing import ResponseReturnValue

from ..common.context import BaseContext, Context
from ..controllers.gamerooms import GameroomsController


def attach_gamerooms_routes(
    app: Flask,
    controller: GameroomsController,
    with_context: Callable[[Callable[..., Any]], Callable[..., Any]],
    with_base_context: Callable[[Callable[..., Any]], Callable[..., Any]],
) -> None:
    """Registers routes for the gamerooms resource."""

    @app.post("/gamerooms")
    @with_context
    def create_gameroom(context: Context) -> ResponseReturnValue:
        return controller.create_gameroom(context=context), 201

    @app.get("/gamerooms")
    @with_context
    def get_gamerooms(context: Context) -> ResponseReturnValue:
        """get_gamerooms.

        Args:
            context (Context): context

        Returns:
            ResponseReturnValue:
        """
        return controller.get_gamerooms(context=context)

    @app.post("/gamerooms/<id>/users")
    @with_context
    def join_gameroom(context: Context, id: str) -> ResponseReturnValue:
        return controller.join_gameroom(context=context, id=id)

    @app.delete("/gamerooms/<id>/users")
    @with_context
    def leave_gameroom(context: Context, id: str) -> ResponseReturnValue:
        return controller.leave_gameroom(context=context, id=id)

    @app.delete("/gamerooms/<id>")
    @with_context
    def delete_gameroom(context: Context, id: str) -> ResponseReturnValue:
        return controller.delete_gameroom(context=context, id=id)

    @app.post("/gamerooms/<id>/game")
    @with_context
    def start_game(context: Context, id: str) -> ResponseReturnValue:
        return controller.start_game(context=context, id=id), 201

    @app.post("/gamerooms/disconnect")
    @with_base_context
    def disconnect(context: BaseContext) -> ResponseReturnValue:
        return controller.disconnect(context=context)
