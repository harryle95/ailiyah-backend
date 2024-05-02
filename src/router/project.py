from collections.abc import Sequence
from typing import TYPE_CHECKING

from litestar import get
from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO, SQLAlchemyDTOConfig

from src.model.project import Project
from src.router.base import BaseController, read_items_by_attrs
from src.router.typing.types import ProjectDTO

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ("ProjectController",)


class ProjectLiteDTO(SQLAlchemyDTO[Project]):
    config = SQLAlchemyDTOConfig(include={"id", "name"})


class ProjectController(BaseController[Project]):
    path = "/project"
    dto = ProjectDTO.write_dto
    return_dto = ProjectDTO.read_dto

    @get(return_dto=ProjectLiteDTO)
    async def get_all_items(self, transaction: "AsyncSession") -> Sequence[Project]:
        return await read_items_by_attrs(transaction, Project)
