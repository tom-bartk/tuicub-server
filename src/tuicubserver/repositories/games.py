from uuid import UUID

from sqlalchemy.orm import Session

from ..models.db import DbGame
from ..models.gameroom import Game
from .base import BaseRepository


class GamesRepository(BaseRepository):
    """The repository of game models."""

    __slots__ = ()

    def get_game_by_id(
        self, session: Session, id: str | UUID, for_update: bool = True
    ) -> Game:
        """Get a game for an id.

        Args:
            session (Session): The current database session.
            id (str | UUID): The id of the game.
            for_update (bool): If true, the query will lock the game for updating.

        Returns:
            The game with the given id.

        Raises:
            NotFoundError: Raised when a game with the given id does not exist.
        """
        return self._get_by_id(
            session=session,
            id=id,
            db_type=DbGame,
            mapper=self._mapper.to_domain_game,
            for_update=for_update,
        )

    def save_game(self, session: Session, game: Game) -> Game:
        """Save a game.

        Stores the database representation of the game in the database.

        Args:
            session (Session): The current database session.
            game (Game): The game to save.

        Returns:
            The saved game.
        """
        return self._save(
            session=session,
            model=game,
            db_type=DbGame,
            mapper=self._mapper.to_db_game,
            mapper_db=self._mapper.to_domain_game,
        )

    def delete_game(self, session: Session, game: Game) -> None:
        """Delete a game.

        Deletes the database representation of the game from the database.

        Args:
            session (Session): The current database session.
            game (Game): The game to delete.
        """
        self._delete(
            session=session, model=game, db_type=DbGame, mapper=self._mapper.to_db_game
        )
