from collections.abc import Callable, Sequence
from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..common.errors import NotFoundError
from ..common.utils import as_uuid
from ..models.mapper import Mapper

_TModel = TypeVar("_TModel")
_TDbModel = TypeVar("_TDbModel")


class BaseRepository:
    """The base class for database repositories."""

    __slots__ = ("_mapper",)

    def __init__(self, mapper: Mapper):
        """Initialize new repository.

        Args:
            mapper (Mapper): The mapper to map between domain and database models.
        """
        self._mapper: Mapper = mapper

    def _get_by_id(
        self,
        session: Session,
        id: str | UUID,
        db_type: type[_TDbModel],
        mapper: Callable[[_TDbModel], _TModel],
        for_update: bool = True,
    ) -> _TModel:
        """Get model for id.

        Args:
            session (Session): The current database session.
            id (str | UUID): The id of the model.
            db_type (type[_TDbModel]): The type of the database model.
            mapper (Callable[[_TDbModel], _TModel]): A function that maps a database
                model to a domain one.
            for_update (bool): If true, the query will lock the resource for updating.

        Returns:
            The model with the given id.

        Raises:
            NotFoundError: Raised when a model with the given id does not exist.
        """
        if value := session.get(
            db_type, as_uuid(id), populate_existing=True, with_for_update=for_update
        ):
            return mapper(value)
        raise NotFoundError()

    def _get_all(
        self,
        session: Session,
        db_type: type[_TDbModel],
        mapper: Callable[[_TDbModel], _TModel],
    ) -> Sequence[_TModel]:
        """Get all models.

        Args:
            session (Session): The current database session.
            db_type (type[_TDbModel]): The type of the database model.
            mapper (Callable[[_TDbModel], _TModel]): A function that maps a database
                model to a domain one.

        Returns:
            The queried models.
        """
        return [mapper(value) for value in session.scalars(select(db_type)).all()]

    def _save(
        self,
        session: Session,
        model: _TModel,
        db_type: type[_TDbModel],
        mapper: Callable[[_TModel], _TDbModel],
        mapper_db: Callable[[_TDbModel], _TModel],
    ) -> _TModel:
        """Save a model.

        Args:
            session (Session): The current database session.
            model (_TModel): The model to save.
            db_type (type[_TDbModel]): The type of the database model.
            mapper (Callable[[_TModel], _TDbModel]): The function that maps a domain
                model to a database one.
            mapper_db (Callable[[_TDbModel], _TModel]): The function that maps a database
                model to a domain one.

        Returns:
            The saved model.
        """
        return mapper_db(session.merge(mapper(model), load=True))

    def _delete(
        self,
        session: Session,
        model: _TModel,
        db_type: type[_TDbModel],
        mapper: Callable[[_TModel], _TDbModel],
    ) -> None:
        """Delete a model.

        Args:
            session (Session): The current database session.
            model (_TModel): The model to delete.
            db_type (type[_TDbModel]): The type of the database model.
            mapper (Callable[[_TModel], _TDbModel]): The function that maps a domain
                model to a database one.
        """
        obj = session.merge(mapper(model), load=True)
        session.delete(obj)
