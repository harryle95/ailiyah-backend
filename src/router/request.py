import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Self
from uuid import UUID

from litestar import delete, post, put
from litestar.contrib.pydantic import PydanticDTO
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from src.model.request import Request
from src.router.base import BaseController, create_item, read_item_by_id
from src.router.prompt import _PromptRawDTO, create_prompt, delete_prompt, update_prompt
from src.router.typing.types import RequestDTO
from src.service.storage.base import StorageServer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


__all__ = ("RequestController",)


def parse_text(value: str) -> list[str]:
    try:
        parsed_value = json.loads(value)
        if isinstance(parsed_value, list):
            return parsed_value
        raise ValueError(value)
    except Exception:
        raise


def parse_id(value: str) -> list[UUID | None]:
    try:
        parsed_value = json.loads(value)
        if isinstance(parsed_value, list):
            return [UUID(item) if item else None for item in parsed_value]
        raise ValueError(value)
    except Exception:
        raise


class CompositeRequest(BaseModel):
    project_id: UUID
    text: str
    images: list[UploadFile]
    id: str
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("images", mode="before")
    @classmethod
    def parse_images(cls, value: UploadFile | list[UploadFile]) -> list[UploadFile]:
        if isinstance(value, UploadFile):
            return [value]
        if isinstance(value, list):
            return value
        raise ValueError(value)


CompositeRequestAnnotated = Annotated[CompositeRequest, Body(media_type=RequestEncodingType.MULTI_PART)]
CompositeRequestDTO = PydanticDTO[CompositeRequest]


def parse(data: CompositeRequest) -> tuple[list[str], list[UUID | None]]:
    parsed_text = parse_text(data.text)
    parsed_id = parse_id(data.id)
    assert len(parsed_text) == len(parsed_id), "size of id and prompt must be equal"
    assert len(parsed_text) == len(data.images), "size of text and size of images must be equal"

    return (parsed_text, parsed_id)


async def delete_request(session: "AsyncSession", storage: "StorageServer", id: UUID) -> None:
    request: Request = await read_item_by_id(session, Request, id)
    prompts = request.prompts
    prompts_ids = [item.id for item in prompts]
    for prompt_id in prompts_ids:
        await delete_prompt(id=prompt_id, session=session, storage=storage)
    await session.delete(request)


class RequestController(BaseController[Request]):
    path = "/request"
    return_dto = RequestDTO.read_dto

    @post("/base")
    async def create_base_request(self, transaction: "AsyncSession", data: Request) -> Request:
        request: Request = await create_item(session=transaction, table=Request, data=data)
        return request

    @post()
    async def create_item(
        self, transaction: "AsyncSession", data: CompositeRequestAnnotated, storage: StorageServer
    ) -> Request:
        [texts, _] = parse(data)
        files = data.images

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
        [texts, prompt_ids] = parse(data)
        files = data.images

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
