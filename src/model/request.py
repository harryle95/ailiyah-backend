from typing import TYPE_CHECKING
from uuid import UUID

from litestar.dto import dto_field
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.model.base import Base

if TYPE_CHECKING:
    from src.model.prompt import Prompt

__all__ = ("Request",)


class Request(Base):
    __tablename__ = "request_table"  # type: ignore[assignment]

    output_image: Mapped[UUID] = mapped_column(nullable=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("project_table.id", ondelete="CASCADE"))

    prompts: Mapped[list["Prompt"]] = relationship(lazy="selectin", info=dto_field("read-only"), cascade="all, delete")
