from pathlib import Path
from uuid import UUID

from src.model import Request
from src.service.storage import StorageServer

__all__ = ("generate_output",)


ParentPath = Path(__file__).parents[0]
ResourcePath = ParentPath / "resource"


async def generate_output(request: Request, storage: StorageServer) -> UUID:
    if request.output_image is not None:
        await storage.delete(request.output_image)
    with Path(ResourcePath / "sample_output.jpeg").open("rb") as file:
        return await storage.create(file.read())
