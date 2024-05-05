# ruff: noqa: A002
from collections.abc import AsyncGenerator
from pathlib import Path
from uuid import UUID, uuid4

from litestar.exceptions import HTTPException
from litestar.response import Stream
from litestar.stores.file import FileStore

from src.service.storage.base import StorageServer

__all__ = ("LocalFileStorage",)


ParentPath = Path(__file__).parents[3]
FilePath = ParentPath / "storage"
Metadata = FilePath / "metadata.json"


class LocalFileStorage(StorageServer):
    def __init__(self, path: str | Path = FilePath) -> None:
        self.path = path
        self.store = FileStore(FilePath / path)

    async def create(self, image: bytes) -> UUID:
        image_id = uuid4()
        await self.store.set(str(image_id), image)
        return image_id

    async def update(self, image: bytes, id: UUID) -> None:
        await self.store.set(str(id), image)
        return

    async def delete(self, id: UUID) -> None:
        if await self.store.exists(str(id)):
            await self.store.delete(str(id))

    async def read(self, id: UUID) -> bytes | None:
        if await self.store.exists(str(id)):
            return await self.store.get(str(id))
        return None

    async def delete_all(self) -> None:
        await self.store.delete_all()

    async def stream(self, id: UUID) -> Stream:
        if await self.store.exists(str(id)):

            async def stream_image() -> AsyncGenerator[bytes, None]:
                data = await self.read(id)
                yield data  # type: ignore[misc]

            return Stream(stream_image, headers={"Content-Type": "image/*"})
        raise HTTPException(detail="file does not exist", status_code=404)
