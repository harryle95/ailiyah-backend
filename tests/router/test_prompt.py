from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
from litestar.testing import AsyncTestClient

from src.helpers import provide_test_storage
from src.service.storage.base import StorageServer

IMAGE = b"image"
PROMPT = "prompt"


@pytest.fixture(scope="function")
async def storage() -> AsyncGenerator[StorageServer, None]:
    storage = await provide_test_storage().__anext__()
    yield storage


@pytest.fixture(scope="function")
async def setup(test_client: "AsyncTestClient") -> AsyncGenerator[UUID, None]:
    res = await test_client.post("project", json={"name": "dummy"})
    project_id = res.json()["id"]
    res = await test_client.post("request/base", json={"project_id": project_id})
    request_id = res.json()["id"]

    yield request_id

    await test_client.delete(f"project/{project_id}")


@pytest.fixture(scope="function")
async def setup_prompt_no_image(
    test_client: "AsyncTestClient", setup: UUID
) -> AsyncGenerator[tuple[UUID, UUID | None], None]:
    res = await test_client.post("/prompt", files={"not_image": IMAGE}, data={"text": PROMPT, "request_id": setup})
    assert res.status_code == 201
    id: UUID = res.json()["id"]
    image: UUID | None = res.json()["image"]
    yield (id, image)


@pytest.fixture(scope="function")
async def setup_prompt(test_client: "AsyncTestClient", setup: UUID) -> AsyncGenerator[tuple[UUID, UUID | None], None]:
    res = await test_client.post("/prompt", files={"image": IMAGE}, data={"text": PROMPT, "request_id": setup})
    assert res.status_code == 201
    id: UUID = res.json()["id"]
    image: UUID | None = res.json()["image"]
    yield (id, image)


async def test_upload_accepts_both_prompt_and_image(
    test_client: AsyncTestClient, setup_prompt: tuple[UUID, UUID], storage: StorageServer
) -> None:
    id, image = setup_prompt
    res = await test_client.get(f"/prompt/{id}")
    assert res.status_code == 200
    data = res.json()
    assert data["image"] == image
    assert data["text"] == PROMPT
    assert await storage.read(image) == IMAGE


async def test_upload_accepts_prompt_with_no_image(
    test_client: AsyncTestClient, setup_prompt_no_image: tuple[UUID, UUID | None], storage: StorageServer
) -> None:
    id, image = setup_prompt_no_image
    assert image is None
    res = await test_client.get(f"/prompt/{id}")
    assert res.status_code == 200
    data = res.json()
    assert data["image"] == image
    assert data["text"] == PROMPT


async def test_upload_does_not_accept_empty_prompt(test_client: AsyncTestClient, setup: UUID) -> None:
    res = await test_client.post("/prompt", files={"not_image": "data"}, data={"request_id": setup})
    assert res.status_code == 400


async def test_delete_cleans_up_image_in_storage(
    test_client: AsyncTestClient, setup_prompt: tuple[UUID, UUID], storage: StorageServer
) -> None:
    id, image = setup_prompt

    # Check that image exists in storage prior
    assert await storage.read(image) == IMAGE

    # Check that image does not exist after delete
    await test_client.delete(f"prompt/{id}")
    assert await storage.read(image) is None


async def test_update_old_prompt_has_image_new_prompt_has_image(
    test_client: AsyncTestClient, setup_prompt: tuple[UUID, UUID], storage: StorageServer, setup: UUID
) -> None:
    new_image = b"new_data"
    new_prompt = "new_prompt"

    id, image = setup_prompt

    res = await test_client.put(
        f"/prompt/{id}", files={"image": new_image}, data={"text": new_prompt, "request_id": setup}
    )
    assert res.status_code == 200
    res = await test_client.get(f"/prompt/{id}")
    assert res.status_code == 200
    assert res.json()["text"] == new_prompt
    assert await storage.read(image) == new_image


async def test_update_old_prompt_has_image_new_prompt_no_image(
    test_client: AsyncTestClient, setup_prompt: tuple[UUID, UUID], storage: StorageServer, setup: UUID
) -> None:
    new_prompt = "new_prompt"

    id, image = setup_prompt
    assert image is not None

    res = await test_client.put(
        f"/prompt/{id}", files={"not_image": IMAGE}, data={"text": new_prompt, "request_id": setup}
    )
    assert res.status_code == 200
    res = await test_client.get(f"/prompt/{id}")
    assert res.status_code == 200
    assert res.json()["text"] == new_prompt

    # Old image in storage is removed, new image reference is also null
    assert res.json()["image"] is None
    assert await storage.read(image) is None


async def test_update_old_prompt_no_image_new_prompt_no_image(
    test_client: AsyncTestClient, setup_prompt_no_image: tuple[UUID, UUID | None], storage: StorageServer, setup: UUID
) -> None:
    new_prompt = "new_prompt"

    id, image = setup_prompt_no_image
    assert image is None

    res = await test_client.put(
        f"/prompt/{id}", files={"not_image": IMAGE}, data={"text": new_prompt, "request_id": setup}
    )
    assert res.status_code == 200
    res = await test_client.get(f"/prompt/{id}")
    assert res.status_code == 200
    assert res.json()["text"] == new_prompt
    assert res.json()["image"] is None


async def test_update_old_prompt_no_image_new_prompt_has_image(
    test_client: AsyncTestClient, setup_prompt_no_image: tuple[UUID, UUID | None], storage: StorageServer, setup: UUID
) -> None:
    new_prompt = "new_prompt"
    new_image = b"new_image"
    id, image = setup_prompt_no_image
    assert image is None

    res = await test_client.put(
        f"/prompt/{id}", files={"image": new_image}, data={"text": new_prompt, "request_id": setup}
    )
    assert res.status_code == 200
    res = await test_client.get(f"/prompt/{id}")
    assert res.status_code == 200
    assert res.json()["text"] == new_prompt
    assert res.json()["image"] is not None
    assert await storage.read(res.json()["image"]) == new_image


async def test_update_new_prompt_no_text_throws_error(
    test_client: AsyncTestClient, setup_prompt_no_image: tuple[UUID, UUID | None], storage: StorageServer, setup: UUID
) -> None:
    new_image = b"new_image"
    id, image = setup_prompt_no_image
    assert image is None

    res = await test_client.put(f"/prompt/{id}", files={"image": new_image}, data={"request_id": setup})
    assert res.status_code == 400
