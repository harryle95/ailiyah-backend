from collections.abc import Sequence

from litestar import get
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.model.request import Request
from src.router.base import BaseController
from src.router.utils.dto import DTOGenerator

__all__ = ("RequestController",)


RequestDTO = DTOGenerator[Request]()


class RequestController(BaseController[Request]):
    path = "/request"
    dto = RequestDTO.write_dto
    return_dto = RequestDTO.read_dto
