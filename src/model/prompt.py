from uuid import UUID

from litestar.dto import dto_field
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.model.base import Base
from src.model.request import Request

__all__ = ("Prompt",)


class Prompt(Base):
    __tablename__ = "prompt_table"  # type: ignore[assignment]

    text: Mapped[str] = mapped_column(nullable=False)
    image: Mapped[UUID | None] = mapped_column(nullable=True)
    request_id: Mapped[UUID] = mapped_column(ForeignKey("request_table.id", ondelete="CASCADE"))
    request: Mapped[Request] = relationship(
        lazy="selectin",
        back_populates="prompts",
        info=dto_field("read-only"),
    )
