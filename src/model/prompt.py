from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.model.base import Base

__all__ = ("Prompt",)


class Prompt(Base):
    __tablename__ = "prompt_table"  # type: ignore[assignment]

    text: Mapped[str] = mapped_column(nullable=False)
    image: Mapped[UUID] = mapped_column(nullable=True)
    request_id: Mapped[UUID] = mapped_column(ForeignKey("request_table.id", ondelete="CASCADE"))
