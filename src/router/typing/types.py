from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body

from src.model import Project, Request
from src.router.utils.dto import DTOGenerator

__all__ = ["RequestDTO", "RequestWithRawFile"]

RequestDTO = DTOGenerator[Request](read_kwargs={"max_nested_depth": 1}, write_kwargs={"max_nested_depth": 0})
ProjectDTO = DTOGenerator[Project](read_kwargs={"max_nested_depth": 1}, write_kwargs={"max_nested_depth": 0})


@dataclass
class _RequestWithRawFile:
    project_id: UUID
    prompt: str
    file: UploadFile


RequestWithRawFile = Annotated[_RequestWithRawFile, Body(media_type=RequestEncodingType.MULTI_PART)]
