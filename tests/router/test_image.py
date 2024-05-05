import json
from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from litestar.testing import AsyncTestClient

from src.service.storage import StorageServer


async def test_request_invalid_image_throws(test_client: "AsyncTestClient") -> None:
    response = await test_client.get(f"image/{uuid4()}")
    assert response.status_code == 404


FIRST_IMAGE = b"first_image"
FIRST_PROMPT = "first_prompt"


@pytest.fixture(scope="function")
async def setup(test_client: "AsyncTestClient", storage: "StorageServer") -> AsyncGenerator[UUID, None]:
    project_res = await test_client.post("project", json={"name": "dummy"})
    assert project_res.status_code == 201
    project_id = project_res.json()["id"]
    request = await test_client.post(
        "request",
        files=[("images", FIRST_IMAGE)],
        data={
            "text": json.dumps([FIRST_PROMPT]),
            "id": json.dumps([None]),
            "project_id": str(project_id),
        },
    )
    assert request.status_code == 201
    request_id = request.json()["id"]
    request = await test_client.get(f"request/{request_id}")
    assert request.status_code == 200
    image_id = request.json()["prompts"][0]["image"]
    assert await storage.read(image_id) == FIRST_IMAGE
    yield image_id


async def test_read_valid_image(test_client: "AsyncTestClient", setup: UUID) -> None:
    image_id = setup
    result = await test_client.get(f"image/{image_id}")
    assert result.status_code == 200
