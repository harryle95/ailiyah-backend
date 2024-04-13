from typing import TYPE_CHECKING

from litestar.dto import dto_field
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.model.base import Base

if TYPE_CHECKING:
    from src.model.request import Request

__all__ = ("Project",)


class Project(Base):
    __tablename__ = "project_table"  # type: ignore[assignment]

    name: Mapped[str] = mapped_column(nullable=False)

    requests: Mapped[list["Request"]] = relationship(
        "Request", lazy="selectin", info=dto_field("read-only"), cascade="all, delete"
    )
