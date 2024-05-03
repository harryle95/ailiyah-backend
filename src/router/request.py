from src.model.request import Request
from src.router.base import BaseController
from src.router.typing.types import RequestDTO

__all__ = ("RequestController",)


class RequestController(BaseController[Request]):
    path = "/request"
    dto = RequestDTO.write_dto
    return_dto = RequestDTO.read_dto
