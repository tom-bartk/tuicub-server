from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Concatenate, ParamSpec, TypeVar
from uuid import uuid4

from flask import request
from sqlalchemy.orm import Session, sessionmaker

from ..models.user import User
from .logger import Logger

if TYPE_CHECKING:
    from ..services import Services

_P = ParamSpec("_P")
_T = TypeVar("_T")


class BaseContext:
    """A basic context of a single api request."""

    __slots__ = ("_session",)

    @property
    def session(self) -> Session:
        """The database session of the request."""
        return self._session

    def __init__(self, session: Session):
        """Initialzie new context.

        Args:
            session (Session): The database session.
        """
        self._session: Session = session

    @classmethod
    def base_decorator(
        cls, session_factory: sessionmaker, logger: Logger
    ) -> Callable[
        [Callable[[BaseContext, _P.args, _P.kwargs], _T]],
        Callable[[_P.args, _P.kwargs], _T],
    ]:
        """Create a new decorator for api endpoints.

        The decorator injects a request context to the endpoint function.
        The context contains a database session, which is commited and flushed
        after calling the endpoint function.

        Args:
            session_factory (sessionmaker): The session factory to use.
            logger (Logger): The logger.

        Returns:
            The decorator to use for api endpoints.
        """

        def with_context(
            func: Callable[Concatenate[BaseContext, _P], _T]
        ) -> Callable[_P, _T]:
            def wrapped(*args: _P.args, **kwds: _P.kwargs) -> _T:
                logger.bind_contextvars(
                    request_id=str(uuid4()), path=request.path, method=request.method
                )

                with session_factory() as session:
                    context = BaseContext(session=session)

                    result = func(context, *args, **kwds)

                    session.commit()
                    session.flush()

                    return result

            wrapped.__name__ = func.__name__
            return wrapped

        return with_context


class Context(BaseContext):
    """An authenticated context of a single api request."""

    __slots__ = ("_user",)

    @property
    def user(self) -> User:
        """The requesting user."""
        return self._user

    def __init__(self, user: User, session: Session):
        """Initialize new context.

        Args:
            user (User): The requesting user.
            session (Session): The database session.
        """
        self._user: User = user
        super().__init__(session=session)

    @classmethod
    def decorator(
        cls, services: Services, session_factory: sessionmaker, logger: Logger
    ) -> Callable[
        [Callable[[Context, _P.args, _P.kwargs], _T]], Callable[[_P.args, _P.kwargs], _T]
    ]:
        """Create a new decorator for authenticated api endpoints.

        The decorator injects a request context to the endpoint function.
        The user is authenticated, and if successful, added to the context as
        the requesting user. The context contains a database session, which is commited
        and flushed after calling the endpoint function.

        Args:
            services (Services): The services container.
            session_factory (sessionmaker): The session factory to use.
            logger (Logger): The logger.

        Returns:
            The decorator to use for api endpoints.
        """

        def with_context(
            func: Callable[Concatenate[Context, _P], _T]
        ) -> Callable[_P, _T]:
            def wrapped(*args: _P.args, **kwds: _P.kwargs) -> _T:
                with session_factory() as session:
                    user = services.auth.authorize(
                        session=session, headers=request.headers
                    )

                    logger.bind_contextvars(
                        request_id=str(uuid4()),
                        path=request.path,
                        method=request.method,
                        user_id=str(user.id),
                    )

                    context = Context(user=user, session=session)

                    result = func(context, *args, **kwds)

                    session.commit()
                    session.flush()

                    return result

            wrapped.__name__ = func.__name__
            return wrapped

        return with_context
