from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from litestar import Controller, delete, get, post, put
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body

from src.model.prompt import Prompt
from src.router.base import create_item, delete_item, read_item_by_id, read_items_by_attrs
from src.service.storage.base import StorageServer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class _PromptRawDTO:
    text: str
    request_id: UUID
    image: UploadFile | None = None


PromptRawDTO = Annotated[_PromptRawDTO, Body(media_type=RequestEncodingType.MULTI_PART)]


async def create_prompt(data: PromptRawDTO, session: "AsyncSession", storage: StorageServer) -> Prompt:
    if hasattr(data, "image") and data.image is not None:
        image_id = await storage.create(data.image)
        prompt_data = Prompt(text=data.text, image=image_id, request_id=data.request_id)
    else:
        prompt_data = Prompt(text=data.text, request_id=data.request_id)
    await create_item(session, Prompt, prompt_data)
    return prompt_data


async def update_prompt(data: PromptRawDTO, session: "AsyncSession", id: UUID, storage: StorageServer) -> Prompt:
    prompt: Prompt = await read_item_by_id(session, Prompt, id)
    if hasattr(data, "image") and data.image is not None:
        if prompt.image is not None:
            await storage.update(data.image, prompt.image)
        else:
            id = await storage.create(data.image)
            prompt.image = id
    else:
        if prompt.image is not None:
            await storage.delete(prompt.image)
        prompt.image = None
    prompt.text = data.text
    return prompt


async def delete_prompt(id: UUID, session: "AsyncSession", storage: StorageServer) -> None:
    prompt: Prompt = await read_item_by_id(session, Prompt, id)
    if prompt.image is not None:
        await storage.delete(prompt.image)
    await delete_item(session, prompt.id, Prompt)


class PromptController(Controller):
    path = "prompt"

    @get("/{id:uuid}")
    async def get_prompt_by_id(self, transaction: "AsyncSession", id: UUID) -> Prompt:
        return await read_item_by_id(transaction, Prompt, id)  # type: ignore[no-any-return]

    @post()
    async def create_prompt(self, data: PromptRawDTO, transaction: "AsyncSession", storage: StorageServer) -> Prompt:
        return await create_prompt(data, transaction, storage)

    @put("/{id:uuid}")
    async def update_prompt(
        self, data: PromptRawDTO, transaction: "AsyncSession", id: UUID, storage: StorageServer
    ) -> Prompt:
        return await update_prompt(data, transaction, id, storage)

    @delete("/{id:uuid}")
    async def delete_prompt(self, id: UUID, transaction: "AsyncSession", storage: StorageServer) -> None:
        return await delete_prompt(id, transaction, storage)
