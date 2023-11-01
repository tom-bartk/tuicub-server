import asyncio

import click
from flask import Flask, request_finished
from sqlalchemy.exc import OperationalError

from .common import Common
from .common.context import BaseContext, Context
from .common.errors import ErrorHandler, TuicubError
from .common.utils import is_host_valid
from .controllers import Controllers
from .events.api_client import EventsApiClient
from .events.server import EventsServer
from .messages.server import MessagesServer
from .repositories import Repositories
from .routes.gamerooms import attach_gamerooms_routes
from .routes.games import attach_games_routes
from .routes.users import attach_users_routes
from .services import Services


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option(
    "-p",
    "--port",
    help="Port to bind to.",
    show_default=True,
    default=5000,
    metavar="PORT",
)
@click.option(
    "-h",
    "--host",
    help="Host to bind to.",
    show_default=True,
    default="0.0.0.0",
    metavar="HOST",
)
def api(port: int, host: str) -> None:
    """Start the API server."""
    if not is_host_valid(host=host):
        raise click.BadParameter(message="Host has an invalid format.")

    app = create_app()
    app.run(host=host, port=port)


@cli.command()
@click.option(
    "--events-port",
    help="Port to bind events server to.",
    show_default=True,
    default=23432,
    metavar="PORT",
)
@click.option(
    "--events-host",
    help="Host to bind events server to.",
    show_default=True,
    default="0.0.0.0",
    metavar="HOST",
)
@click.option(
    "--messages-port",
    help="Port to bind messages server to.",
    show_default=True,
    default=23433,
    metavar="PORT",
)
@click.option(
    "--messages-host",
    help="Host to bind messages server to.",
    show_default=True,
    default="0.0.0.0",
    metavar="HOST",
)
@click.option(
    "--api-url",
    help="Base URL of the API for disconnect callbacks.",
    show_default=True,
    default="https://api.tuicub.com",
    metavar="URL",
)
def events(
    events_port: int,
    events_host: str,
    messages_host: str,
    messages_port: int,
    api_url: str,
) -> None:
    """Start the events and messages server."""
    loop = asyncio.get_event_loop()
    common = Common()
    services = Services(repositories=Repositories(), config=common.config)

    events_server = EventsServer(
        loop=loop,
        session_factory=common.db.session_factory,
        users_service=services.users,
        api_client=EventsApiClient(
            api_url=api_url,
            token=common.config.events_secret,
        ),
        logger=common.logger,
    )
    messages_server = MessagesServer(auth_service=services.auth, logger=common.logger)
    messages_server.set_delegate(events_server)

    async def start() -> None:
        async with asyncio.TaskGroup() as group:
            group.create_task(events_server.listen(host=events_host, port=events_port))
            group.create_task(
                messages_server.listen(host=messages_host, port=messages_port)
            )

    loop.run_until_complete(start())


def create_app() -> Flask:
    app = Flask(__name__)

    common = Common()
    services = Services(repositories=Repositories(), config=common.config)
    controllers = Controllers(services=services)

    base_context_decorator = BaseContext.base_decorator(
        session_factory=common.db.session_factory, logger=common.logger
    )
    context_decorator = Context.decorator(
        services=services, session_factory=common.db.session_factory, logger=common.logger
    )

    attach_gamerooms_routes(
        app,
        controller=controllers.gamerooms,
        with_context=context_decorator,
        with_base_context=base_context_decorator,
    )
    attach_games_routes(app, controller=controllers.games, with_context=context_decorator)
    attach_users_routes(
        app, controller=controllers.users, with_base_context=base_context_decorator
    )

    error_handler = ErrorHandler(logger=common.logger)
    app.register_error_handler(TuicubError, error_handler.handle_tuicub_error)
    app.register_error_handler(OperationalError, error_handler.handle_sqlalchemy_error)

    request_finished.connect(common.logger.log_response, app)

    services.messages.connect()

    return app


def main() -> None:
    cli()
