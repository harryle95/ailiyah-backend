from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from litestar import delete, post, put
from litestar.dto import DataclassDTO

from src.model.request import Request
from src.router.base import BaseController, create_item, read_item_by_id
from src.router.prompt import PromptRawDTO, create_prompt, delete_prompt, update_prompt
from src.router.typing.types import RequestDTO
from src.service.storage.base import StorageServer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


__all__ = ("RequestController",)


@dataclass
class _CompositeRequestDTO:
    project_id: UUID
    prompts: list[PromptRawDTO]


CompositeRequestDTO = DataclassDTO[_CompositeRequestDTO]


class RequestController(BaseController[Request]):
    path = "/request"
    dto = RequestDTO.write_dto
    return_dto = RequestDTO.read_dto

    @post("/base")
    async def create_base_request(self, transaction: "AsyncSession", data: Request) -> Request:
        request: Request = await create_item(session=transaction, table=Request, data=data)
        return request

    @post(dto=CompositeRequestDTO)
    async def create_item(
        self, transaction: "AsyncSession", data: _CompositeRequestDTO, storage: StorageServer
    ) -> Request:
        request: Request = await create_item(
            session=transaction, table=Request, data=Request(project_id=data.project_id)
        )
        for prompt in data.prompts:
            init_prompt = PromptRawDTO(text=prompt.text, request_id=request.id, image=prompt.image)
            await create_prompt(data=init_prompt, session=transaction, storage=storage)
        return request

    @put("/{id:uuid}", dto=CompositeRequestDTO)
    async def update_item(
        self, transaction: "AsyncSession", id: UUID, data: _CompositeRequestDTO, storage: StorageServer
    ) -> Request:
        request: Request = await read_item_by_id(transaction, Request, id)
        initial_prompts = request.prompts
        intial_prompts_id = [item.id for item in initial_prompts]
        for prompt in data.prompts:
            # New prompt -> Create
            if prompt.id is None:
                init_prompt = PromptRawDTO(text=prompt.text, request_id=request.id, image=prompt.image)
                await create_prompt(data=init_prompt, session=transaction, storage=storage)
            else:
                # Old prompt -> Update
                if prompt.id in intial_prompts_id:
                    await update_prompt(data=prompt, session=transaction, id=prompt.id, storage=storage)
                    intial_prompts_id.remove(prompt.id)

        # Remaining prompts -> has been deleted -> Delete
        for prompt_id in intial_prompts_id:
            await delete_prompt(id=prompt_id, session=transaction, storage=storage)
        return request

    @delete("/{id:uuid}")
    async def delete_item(self, transaction: "AsyncSession", id: UUID, storage: StorageServer) -> None:
        request: Request = await read_item_by_id(transaction, Request, id)
        prompts = request.prompts
        prompts_ids = [item.id for item in prompts]
        for prompt_id in prompts_ids:
            await delete_prompt(id=prompt_id, session=transaction, storage=storage)
