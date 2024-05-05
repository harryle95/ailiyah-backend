import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from litestar import delete, post, put
from litestar.datastructures import UploadFile
from litestar.dto import DataclassDTO
from litestar.enums import RequestEncodingType
from litestar.params import Body

from src.model.request import Request
from src.router.base import BaseController, create_item, read_item_by_id
from src.router.prompt import _PromptRawDTO, create_prompt, delete_prompt, update_prompt
from src.router.typing.types import RequestDTO
from src.service.storage.base import StorageServer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


__all__ = ("RequestController",)


@dataclass
class CompositeRequest:
    project_id: UUID
    text: str
    images: list[UploadFile]
    id: str


CompositeRequestAnnotated = Annotated[CompositeRequest, Body(media_type=RequestEncodingType.MULTI_PART)]
CompositeRequestDTO = DataclassDTO[CompositeRequest]


async def delete_request(session: "AsyncSession", storage: "StorageServer", id: UUID) -> None:
    request: Request = await read_item_by_id(session, Request, id)
    prompts = request.prompts
    prompts_ids = [item.id for item in prompts]
    for prompt_id in prompts_ids:
        await delete_prompt(id=prompt_id, session=session, storage=storage)
    await session.delete(request)


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
        self, transaction: "AsyncSession", data: CompositeRequestAnnotated, storage: StorageServer
    ) -> Request:
        texts: list[str] = json.loads(data.text)
        files = data.images

        if len(texts) != len(files):
            raise ValueError("Length of text list must match number of attached files")

        request: Request = await create_item(
            session=transaction, table=Request, data=Request(project_id=data.project_id)
        )
        for i in range(len(texts)):
            init_prompt = _PromptRawDTO(text=texts[i], request_id=request.id, image=files[i])
            await create_prompt(data=init_prompt, session=transaction, storage=storage)
        return request

    @put("/{id:uuid}", dto=CompositeRequestDTO)
    async def update_item(
        self, transaction: "AsyncSession", id: UUID, data: CompositeRequestAnnotated, storage: StorageServer
    ) -> Request:
        texts: list[str] = json.loads(data.text)
        files = data.images
        prompt_ids_str: list[str] = json.loads(data.id)
        prompt_ids: list[UUID | None] = [UUID(item) if item else None for item in prompt_ids_str]
        if len(texts) != len(files):
            raise ValueError("Length of text list must match number of attached files")
        if len(prompt_ids) != len(texts):
            raise ValueError("Length of text list must match length of prompt ids")

        request: Request = await read_item_by_id(transaction, Request, id)
        initial_prompts = request.prompts
        initial_prompts_id = [item.id for item in initial_prompts]
        for i in range(len(texts)):
            text = texts[i]
            image = files[i]
            prompt_id = prompt_ids[i]
            # New prompt -> Create
            if prompt_id is None:
                init_prompt = _PromptRawDTO(text=text, request_id=request.id, image=image)
                await create_prompt(data=init_prompt, session=transaction, storage=storage)
            else:
                # Old prompt -> Update
                if prompt_id in initial_prompts_id:
                    prompt = _PromptRawDTO(text=text, request_id=id, image=image, id=prompt_id)
                    await update_prompt(data=prompt, session=transaction, id=prompt_id, storage=storage)
                    initial_prompts_id.remove(prompt_id)

        # Remaining prompts -> has been deleted -> Delete
        for prompt_id in initial_prompts_id:
            await delete_prompt(id=prompt_id, session=transaction, storage=storage)
        return request

    @delete("/{id:uuid}")
    async def delete_item(self, transaction: "AsyncSession", id: UUID, storage: StorageServer) -> None:
        await delete_request(transaction, storage, id)
