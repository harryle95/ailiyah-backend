from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.model.base import Base

__all__ = ("Request",)


class Request(Base):
    __tablename__ = "request_table"  # type: ignore[assignment]

    prompt: Mapped[str] = mapped_column(nullable=True)
    input_image: Mapped[UUID] = mapped_column(nullable=True)
    output_image: Mapped[UUID] = mapped_column(nullable=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("project_table.id", ondelete="CASCADE"))
