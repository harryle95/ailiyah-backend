# ruff: noqa: A002
import abc
import uuid
from abc import ABC
from uuid import UUID

from litestar.datastructures import UploadFile

__all__ = ("StorageServer",)


class StorageServer(ABC):
    @abc.abstractmethod
    async def create(self, image: UploadFile) -> UUID:
        return uuid.uuid4()

    @abc.abstractmethod
    async def update(self, image: UploadFile, id: UUID) -> None:
        return

    @abc.abstractmethod
    async def delete(self, id: UUID) -> None:
        return

    @abc.abstractmethod
    async def read(self, id: UUID) -> bytes | None:
        return None

    @abc.abstractmethod
    async def delete_all(self) -> None:
        return
