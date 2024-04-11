from typing import TYPE_CHECKING, Optional
from uuid import UUID

from litestar.dto import dto_field
from sqlalchemy import UUID as UUID_SQL
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.model.base import Base

if TYPE_CHECKING:
    from src.model.project import Project

__all__ = ("Request",)


class Request(Base):
    __tablename__ = "request_table"  # type: ignore[assignment]

    prompt: Mapped[str] = mapped_column(nullable=True)

    project_id: Mapped[UUID] = mapped_column(ForeignKey("project_table.id"))
