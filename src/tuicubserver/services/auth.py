from sqlalchemy.orm import Session
from werkzeug.datastructures import Headers

from ..common.errors import UnauthorizedError
from ..common.utils import generate_token, parse_token
from ..models.user import User
from ..repositories.users import UsersRepository


class AuthService:
    """The service for authorizing users."""

    __slots__ = ("_users_repository", "_events_secret", "_messages_secret")

    def __init__(
        self, users_repository: UsersRepository, events_secret: str, messages_secret: str
    ):
        """Initialize a new service.

        Args:
            users_repository (UsersRepository): The users repository.
            events_secret (str): The secret used to authorize the events server.
            messages_secret (str): The secret used to authorize incoming messages.
        """
        self._users_repository: UsersRepository = users_repository
        self._events_secret: str = events_secret
        self._messages_secret: str = messages_secret

    def authorize(self, session: Session, headers: Headers) -> User:
        """Authorize a request.

        Authorizes a request by the token passed in the `Authorization` header,
        and returns the requesting user.

        Args:
            session (Session): The database session for this request.
            headers (Headers): The headers of the request.

        Returns:
            The requesting user.

        Raises:
            UnauthorizedError: Raised when the authorization header is missing,
                the token is invaild, or there is no user for that token.
        """
        if token := parse_token(headers):
            return self._users_repository.get_user_by_token(session=session, token=token)
        raise UnauthorizedError()

    def authorize_events_server(self, headers: Headers) -> None:
        """Authorize a request made by the events server.

        Verifies the token passed in the `Authorization` header against the
        preconfigured secret.

        Args:
            headers (Headers): The headers of the request.

        Raises:
            UnauthorizedError: Raised when the authorization header is missing,
                the token is invaild, or the token does not match the secret.
        """
        token = parse_token(headers)
        if not token or token != self._events_secret:
            raise UnauthorizedError()

    def authorize_message(self, secret: str) -> None:
        """Authorize an incoming message.

        Verifies the token from the message envelope against the preconfigured secret.

        Args:
            secret (str): The secret from the message envelope.

        Raises:
            UnauthorizedError: Raised when the secret is incorrect.
        """
        if secret != self._messages_secret:
            raise UnauthorizedError()

    def generate_token(self) -> str:
        """Generate a new token.

        Returns:
            The generated token.
        """
        return generate_token()
