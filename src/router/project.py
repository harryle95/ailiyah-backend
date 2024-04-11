from collections.abc import Sequence

from litestar import get
from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO, SQLAlchemyDTOConfig
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.model.project import Project
from src.router.base import BaseController, read_items_by_attrs
from src.router.utils.dto import DTOGenerator

__all__ = ("ProjectController",)


ProjectDTO = DTOGenerator[Project](read_kwargs={"max_nested_depth": 1}, write_kwargs={"max_nested_depth": 0})


class ProjectLiteDTO(SQLAlchemyDTO[Project]):
    config = SQLAlchemyDTOConfig(include={"id", "name"})


class ProjectController(BaseController[Project]):
    path = "/project"
    dto = ProjectDTO.write_dto
    return_dto = ProjectDTO.read_dto

    @get(return_dto=ProjectLiteDTO)
    async def get_all_items(self, transaction: "AsyncSession") -> Sequence[Project]:  # type: ignore[name-defined]
        return await read_items_by_attrs(transaction, Project)
