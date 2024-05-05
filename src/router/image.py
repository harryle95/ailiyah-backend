from uuid import UUID

from litestar import Controller, get
from litestar.response import Stream

from src.service.storage import StorageServer

__all__ = ("ImageController",)


class ImageController(Controller):
    path: str = "image"

    @get("/{id:uuid}")
    async def get_image(self, storage: StorageServer, id: UUID) -> Stream:
        return await storage.stream(id)
