# ruff: noqa: A002
import abc
import uuid
from abc import ABC
from uuid import UUID

from litestar.datastructures import UploadFile

__all__ = ("StorageServer",)


ImageLike = UploadFile


class StorageServer(ABC):
    @abc.abstractmethod
    async def create(self, image: ImageLike) -> UUID:
        return uuid.uuid4()

    @abc.abstractmethod
    async def update(self, image: ImageLike, id: UUID) -> None:
        return

    @abc.abstractmethod
    async def delete(self, id: UUID) -> None:
        return
