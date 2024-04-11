from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from litestar import get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.model.request import Request
from src.router.base import BaseController
from src.router.utils.dto import DTOGenerator

__all__ = ("RequestController",)


RequestDTO = DTOGenerator[Request]()


@dataclass
class RequestData:
    project_id: UUID
    prompt: str
    file: str


class RequestController(BaseController[Request]):
    path = "/request"
    dto = RequestDTO.write_dto
    return_dto = RequestDTO.read_dto

    @post(dto=None, return_dto=None)
    async def create_item(
        self,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> dict[str, str]:
        with open("test_image.jpg", "wb") as file:
            file.write(await data.read())
        return {}
