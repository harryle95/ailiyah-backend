from collections.abc import Sequence
from typing import TYPE_CHECKING
from uuid import UUID

from litestar import delete, get
from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO, SQLAlchemyDTOConfig

from src.model.project import Project
from src.router.base import BaseController, read_item_by_id, read_items_by_attrs
from src.router.request import delete_request
from src.router.typing.types import ProjectDTO
from src.service.storage.base import StorageServer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


__all__ = ("ProjectController",)


class ProjectLiteDTO(SQLAlchemyDTO[Project]):
    config = SQLAlchemyDTOConfig(include={"id", "name"})


class ProjectReadDTO(SQLAlchemyDTO[Project]):
    config = SQLAlchemyDTOConfig(max_nested_depth=2)


class ProjectController(BaseController[Project]):
    path = "/project"
    dto = ProjectDTO.write_dto

    @get("/{id:uuid}", return_dto=ProjectReadDTO)
    async def get_item_by_id(self, transaction: "AsyncSession", id: UUID) -> Project:
        data: Project = await read_item_by_id(transaction, Project, id)
        return data

    @get(return_dto=ProjectLiteDTO)
    async def get_all_items(
        self, transaction: "AsyncSession", id: UUID | None = None, name: str | None = None
    ) -> Sequence[Project]:
        return await read_items_by_attrs(transaction, Project, name=name, id=id)

    @delete("/{id:uuid}")
    async def delete_item(self, transaction: "AsyncSession", id: UUID, storage: StorageServer) -> None:
        project: Project = await read_item_by_id(transaction, Project, id)
        requests = project.requests
        for request in requests:
            await delete_request(transaction, storage, request.id)
        await transaction.delete(project)
