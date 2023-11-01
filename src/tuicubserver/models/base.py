# from uuid import UUID
#
# from attrs import frozen
# from sqlalchemy import Uuid
# from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
#
#
# @frozen
# class Model:
#     id: UUID
#
#
# class DbBase(DeclarativeBase):
#     id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
