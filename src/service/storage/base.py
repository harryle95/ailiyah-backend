# ruff: noqa: A002
import abc
import uuid
from abc import ABC
from uuid import UUID

from litestar.datastructures import UploadFile

ImageLike = UploadFile


class StorageServer(ABC):
    @abc.abstractmethod
    def create(self, image: ImageLike) -> UUID:
        return uuid.uuid4()

    @abc.abstractmethod
    def read(self, id: UUID) -> ImageLike | None:
        return None

    @abc.abstractmethod
    def update(self, image: ImageLike, id: UUID) -> UUID:
        return id

    @abc.abstractmethod
    def delete(self, id: UUID) -> UUID:
        return id
