import uuid

from sqlalchemy.orm import Session

from ..common.context import BaseContext
from ..models.user import User, UserToken
from ..repositories.users import UsersRepository
from ..services.auth import AuthService


class UsersService:
    """The service for querying and manipulating users and tokens."""

    __slots__ = ("_auth_service", "_users_repository")

    def __init__(self, auth_service: AuthService, users_repository: UsersRepository):
        """Initialize new service.

        Args:
            auth_service (AuthService): The authentication service.
            users_repository (UsersRepository): The users repository.
        """
        self._auth_service: AuthService = auth_service
        self._users_repository: UsersRepository = users_repository

    def create_user(self, context: BaseContext, name: str) -> tuple[User, UserToken]:
        """Create a new user.

        Create a new user with the given name, and generates a new authentication token.

        Args:
            context (BaseContext): The request context.
            name (str): The name of the user to create.

        Returns:
            The created user and the authentication token.
        """
        user_id = uuid.uuid4()
        user = self._users_repository.save_user(
            session=context.session,
            user=User(id=user_id, name=name, current_gameroom_id=None),
        )
        token = self._users_repository.save_user_token(
            session=context.session,
            user_token=UserToken(
                id=uuid.uuid4(),
                user_id=user_id,
                token=self._auth_service.generate_token(),
            ),
        )

        return user, token

    def get_user_token(self, session: Session, token: str) -> UserToken:
        """Get user's authentication token by token value.

        Args:
            session (Session): The database session of the request.
            token (str): The token value.

        Returns:
            The authentication token for the user.

        Raises:
            UnauthorizedError: Raised when no user authentication token is found
                for the given token value.
        """
        return self._users_repository.get_user_token_by_token(
            session=session, token=token
        )

    def get_user_by_id(self, session: Session, user_id: uuid.UUID) -> User:
        """Get user for the given id.

        Args:
            session (Session): The database session of the request.
            user_id (uuid.UUID): The id of the user.

        Returns:
            The user having the given id.

        Raises:
            NotFoundError: Raised when no user is found with the given id.
        """
        return self._users_repository.get_user_by_id(session=session, id=user_id)
