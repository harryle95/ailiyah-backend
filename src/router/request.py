from uuid import UUID

from litestar import get, post
from litestar.response import Stream
from sqlalchemy.ext.asyncio import AsyncSession

from src.model.request import Request
from src.router.base import BaseController, create_item
from src.router.typing.types import RequestDTO, RequestWithRawFile
from src.service.storage.local import LocalFileStorage


class RequestController(BaseController[Request]):
    path = "/request"
    dto = RequestDTO.write_dto
    return_dto = RequestDTO.read_dto

    @post(dto=None)
    async def create_item(
        self,
        data: RequestWithRawFile,
        transaction: AsyncSession,
    ) -> Request:
        storage = LocalFileStorage()  # type: ignore
        id = await storage.create(data.file)
        request_data = Request(
            prompt=data.prompt,
            project_id=data.project_id,
            input_image=id,
            output_image=id,
        )
        result: Request = await create_item(session=transaction, table=Request, data=request_data)
        return result

    @get(path="/image/{id: uuid}", return_dto=None)
    async def get_image(self, transaction: AsyncSession, id: UUID) -> Stream:
        storage = LocalFileStorage()  # type: ignore
        return await storage.read_stream(id)
