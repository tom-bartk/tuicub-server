from collections.abc import Callable
from typing import Any

from flask import Flask
from flask.typing import ResponseReturnValue

from ..common.context import Context
from ..controllers.games import GamesController


def attach_games_routes(
    app: Flask,
    controller: GamesController,
    with_context: Callable[[Callable[..., Any]], Callable[..., Any]],
) -> None:
    """Registers routes for the games resource."""

    @app.post("/games/<id>/moves")
    @with_context
    def move(context: Context, id: str) -> ResponseReturnValue:
        return controller.move(context=context, id=id)

    @app.delete("/games/<id>/moves")
    @with_context
    def undo(context: Context, id: str) -> ResponseReturnValue:
        return controller.undo(context=context, id=id)

    @app.patch("/games/<id>/moves")
    @with_context
    def redo(context: Context, id: str) -> ResponseReturnValue:
        return controller.redo(context=context, id=id)

    @app.post("/games/<id>/turns/end")
    @with_context
    def end_turn(context: Context, id: str) -> ResponseReturnValue:
        return controller.end_turn(context=context, id=id)

    @app.post("/games/<id>/turns/draw")
    @with_context
    def draw(context: Context, id: str) -> ResponseReturnValue:
        return controller.draw(context=context, id=id)
