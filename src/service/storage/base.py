# ruff: noqa: A002
import abc
import uuid
from abc import ABC
from uuid import UUID

__all__ = ("StorageServer",)


class StorageServer(ABC):
    @abc.abstractmethod
    async def create(self, image: bytes) -> UUID:
        return uuid.uuid4()

    @abc.abstractmethod
    async def update(self, image: bytes, id: UUID) -> None:
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
