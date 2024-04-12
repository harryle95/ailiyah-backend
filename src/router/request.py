from pathlib import Path

from litestar import post

from src.model.request import Request
from src.router.base import BaseController
from src.router.typing.types import RequestDTO, RequestWithRawFile

__all__ = ("RequestController",)


class RequestController(BaseController[Request]):
    path = "/request"
    dto = RequestDTO.write_dto
    return_dto = RequestDTO.read_dto

    @post(dto=None, return_dto=None)
    async def create_item(
        self,
        data: RequestWithRawFile,
    ) -> dict[str, str]:
        with Path("test_image.jpg").open("wb") as file:
            file.write(await data.file.read())
        return {}
