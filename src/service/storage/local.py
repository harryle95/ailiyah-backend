# ruff: noqa: A002
from pathlib import Path
from uuid import UUID, uuid4

from litestar.datastructures import UploadFile
from litestar.stores.file import FileStore

from src.service.storage.base import StorageServer

__all__ = ("LocalFileStorage",)


ParentPath = Path(__file__).parents[3]
FilePath = ParentPath / "storage"
Metadata = FilePath / "metadata.json"


class LocalFileStorage(StorageServer):
    def __init__(self, path: str | Path = FilePath) -> None:
        self.store = FileStore(FilePath / path)

    async def create(self, image: UploadFile) -> UUID:
        data = await image.read()
        id = uuid4()
        await self.store.set(str(id), data)
        return id

    async def update(self, image: UploadFile, id: UUID) -> None:
        data = await image.read()
        await self.store.set(str(id), data)
        return

    async def delete(self, id: UUID) -> None:
        if await self.store.exists(str(id)):
            await self.store.delete(str(id))
        return

    async def read(self, id: UUID) -> bytes | None:
        if await self.store.exists(str(id)):
            return await self.store.get(str(id))
        return None

    async def delete_all(self) -> None:
        await self.store.delete_all()
