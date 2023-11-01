from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ..common.errors import NotFoundError
from ..models.db import DbGameroom
from ..models.gameroom import Gameroom
from ..models.status import GameroomStatus
from .base import BaseRepository


class GameroomsRepository(BaseRepository):
    """The repository of gameroom models."""

    __slots__ = ()

    def get_gamerooms(self, session: Session) -> Sequence[Gameroom]:
        """Get all not deleted gamerooms.

        Args:
            session (Session): The current database session.

        Returns:
            The list of all not deleted gamerooms.
        """
        values: Sequence[DbGameroom] = session.scalars(
            sa.select(DbGameroom).where(DbGameroom.status != GameroomStatus.DELETED)
        ).all()
        return [self._mapper.to_domain_gameroom(value) for value in values]

    def get_gameroom_by_id(
        self, session: Session, id: str | UUID, for_update: bool = True
    ) -> Gameroom:
        """Get a gameroom for an id.

        Args:
            session (Session): The current database session.
            id (str | UUID): The id of the gameroom.
            for_update (bool): If true, the query will lock the gameroom for updating.

        Returns:
            The gameroom with the given id.

        Raises:
            NotFoundError: Raised when a gameroom with the given id does not exist,
                or has been deleted.
        """
        gameroom: Gameroom = self._get_by_id(
            session=session,
            id=id,
            db_type=DbGameroom,
            mapper=self._mapper.to_domain_gameroom,
            for_update=for_update,
        )

        if gameroom.status == GameroomStatus.DELETED:
            raise NotFoundError()

        return gameroom

    def save_gameroom(self, session: Session, gameroom: Gameroom) -> Gameroom:
        """Save a gameroom.

        Stores the database representation of the gameroom in the database.

        Args:
            session (Session): The current database session.
            gameroom (Gameroom): The gameroom to save.

        Returns:
            The saved gameroom.
        """
        return self._save(
            session=session,
            model=gameroom,
            db_type=DbGameroom,
            mapper=self._mapper.to_db_gameroom,
            mapper_db=self._mapper.to_domain_gameroom,
        )

    def delete_gameroom(self, session: Session, gameroom: Gameroom) -> None:
        """Delete a gameroom.

        Deletes the database representation of the gameroom from the database.

        Args:
            session (Session): The current database session.
            gameroom (Gameroom): The gameroom to delete.
        """
        self._delete(
            session=session,
            model=gameroom,
            db_type=DbGameroom,
            mapper=self._mapper.to_db_gameroom,
        )
