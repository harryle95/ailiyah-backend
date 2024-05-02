# ruff: noqa: A002
import json
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any
from uuid import UUID

import aiofiles
from litestar.response import Stream

from src.service.storage.base import ImageLike, StorageServer

__all__ = ("LocalFileStorage", )


ParentPath = Path(__file__).parents[3]
FilePath = ParentPath / "storage"
Metadata = FilePath / "metadata.json"


class LocalFileStorage(StorageServer):
    def __init__(self) -> None:
        if not FilePath.exists():
            FilePath.mkdir(parents=True, exist_ok=True)
        if not Metadata.exists():
            Metadata.touch(exist_ok=True)
            with Metadata.open("r+") as f:
                json.dump({}, f)

    async def _read_metadata(self) -> dict[str, Any]:
        with Metadata.open("r") as f:
            return json.load(f)  # type: ignore[no-any-return]

    async def _write_metadata(self, new_entry: dict[str, str], remove_key: str | None = None) -> None:
        data = await self._read_metadata()
        data.update(new_entry)
        if remove_key is not None:
            data.pop(remove_key)
        with Metadata.open("w") as f:
            json.dump(data, f)

    async def _write_image(self, image_path: Path, image: ImageLike) -> None:
        data = await image.read()
        async with aiofiles.open(str(image_path), "wb") as file:
            await file.write(data)

    async def create(self, image: ImageLike) -> UUID:
        new_id = uuid.uuid4()
        img_path = FilePath / f"{new_id}.png"
        await self._write_image(img_path, image)
        await self._write_metadata({str(new_id): str(img_path)})
        return new_id

    async def update(self, image: ImageLike, id: "UUID") -> None:
        metadata = await self._read_metadata()
        if id in metadata:
            file_path = metadata[str(id)]
            await self._write_image(file_path, image)

    async def delete(self, id: UUID) -> None:
        await self._write_metadata({}, remove_key=str(id))
        await self._write_metadata({}, remove_key=str(id))

    async def read_stream(self, id: UUID) -> Stream:
        metadata = await self._read_metadata()

        def stream_image() -> Generator[bytes, Any, Any]:
            with Path(metadata[str(id)]).open("rb") as file:
                yield from file

        return Stream(stream_image, headers={"Content-Type": "image/jpeg"})
