from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..common.errors import NotFoundError, UnauthorizedError
from ..models.db import DbUser, DbUserToken
from ..models.user import User, UserToken
from .base import BaseRepository


class UsersRepository(BaseRepository):
    """The repository of user and authentication token models."""

    __slots__ = ()

    def get_user_by_id(self, session: Session, id: str | UUID) -> User:
        """Get a user for an id.

        Args:
            session (Session): The current database session.
            id (str | UUID): The id of the user.

        Returns:
            The user with the given id.

        Raises:
            NotFoundError: Raised when a user with the given id does not exist.
        """
        return self._get_by_id(
            session=session, id=id, db_type=DbUser, mapper=self._mapper.to_domain_user
        )

    def get_user_by_token(self, session: Session, token: str) -> User:
        """Get a user for a token value.

        Args:
            session (Session): The current database session.
            token (str): The value of an authentication token.

        Returns:
            The user with the given token value.

        Raises:
            UnauthorizedError: Raised when no authentication token is found
                for the given token value.
        """
        user_token: DbUserToken | None = session.scalars(
            select(DbUserToken).where(DbUserToken.token == token)
        ).first()

        if not user_token:
            raise UnauthorizedError()

        try:
            return self._get_by_id(
                session=session,
                id=user_token.user_id,
                db_type=DbUser,
                mapper=self._mapper.to_domain_user,
            )
        except NotFoundError as e:
            raise UnauthorizedError() from e

    def save_user(self, session: Session, user: User) -> User:
        """Save a user.

        Stores the database representation of the user in the database.

        Args:
            session (Session): The current database session.
            user (User): The user to save.

        Returns:
            The saved user.
        """
        return self._save(
            session=session,
            model=user,
            db_type=DbUser,
            mapper=self._mapper.to_db_user,
            mapper_db=self._mapper.to_domain_user,
        )

    def save_user_token(self, session: Session, user_token: UserToken) -> UserToken:
        """Save a user authentication token.

        Stores the database representation of the authentication token in the database.

        Args:
            session (Session): The current database session.
            user_token (UserToken): The authentication token to save.

        Returns:
            The saved authentication token.
        """
        return self._save(
            session=session,
            model=user_token,
            db_type=DbUserToken,
            mapper=self._mapper.to_db_user_token,
            mapper_db=self._mapper.to_domain_user_token,
        )

    def get_user_token_by_token(self, session: Session, token: str) -> UserToken:
        """Get a user authentication token for a token value.

        Args:
            session (Session): The current database session.
            token (str): The value of an authentication token.

        Returns:
            The authentication token with the given token value.

        Raises:
            UnauthorizedError: Raised when no authentication token is found
                for the given token value.
        """
        user_token: DbUserToken | None = session.scalars(
            select(DbUserToken).where(DbUserToken.token == token)
        ).first()

        if not user_token:
            raise UnauthorizedError()

        return self._mapper.to_domain_user_token(user_token)
