import json
import random
from collections.abc import AsyncGenerator, Generator
from typing import Any
from uuid import UUID

import pytest
from litestar.testing import AsyncTestClient

from src.model import Project, Request
from src.service.storage.base import StorageServer
from tests.helpers import (
    AbstractBaseTestSuite,
    FixtureManager,
    ResponseValidator,
    setup,
)

fixture_manager = FixtureManager()

dependent_fixture = {
    "first_project": {"name": "first_project"},
    "second_project": {"name": "second_project"},
    "third_project": {"name": "third_project"},
}


@pytest.fixture(scope="function")
def fixture() -> dict[str, dict[str, Any]]:
    return {
        "first_request": {"project_id": "first_project"},
        "second_request": {"project_id": "second_project"},
        "third_request": {"project_id": "first_project"},
    }


@pytest.fixture(scope="function")
def dependent_fixture_id() -> Generator[dict[str, UUID], None, None]:
    yield {}


@pytest.fixture(scope="function")
async def setup_dependent(
    test_client: "AsyncTestClient", dependent_fixture_id: dict[str, UUID]
) -> AsyncGenerator[dict[str, UUID], None]:
    async for _ in setup(dependent_fixture, dependent_fixture_id, fixture_manager, test_client, "project", Project):
        yield dependent_fixture_id


class TestCreateRequest(AbstractBaseTestSuite[Request]):
    path = "request"

    @pytest.fixture(scope="function", autouse=True)
    def _fixture(self, fixture: dict[str, dict[str, Any]]) -> None:
        self.fixture = fixture  # type: ignore[misc]

    @pytest.fixture(scope="function", autouse=True)
    async def setup(
        self, test_client: "AsyncTestClient", setup_dependent: dict[str, UUID]
    ) -> AsyncGenerator[None, None]:
        dependent_fixture_id = setup_dependent
        # Replace project name with corresponding id
        for key, value in self.fixture.items():
            dependent_key = value["project_id"]
            replacement_key = dependent_fixture_id[dependent_key]
            self.fixture[key]["project_id"] = replacement_key

        # Count number of requests for each project
        self.counter: dict[str, int] = {}
        for _, value in self.fixture.items():
            id = value["project_id"]
            if id in self.counter:
                self.counter[id] += 1
            else:
                self.counter[id] = 1

        titles = random.sample(list(self.fixture.keys()), len(self.fixture))

        for title in titles:
            self.fixture_id[title] = await fixture_manager.create_item_success(
                test_client, path="request/base", model_class=Request, **self.fixture[title]
            )
        yield
        for key, id in self.fixture_id.items():
            await fixture_manager.destroy_item(test_client, path="request", fixture_id=id)

    async def test_requesting_project_shows_requests(self, test_client: "AsyncTestClient") -> None:
        for id, count in self.counter.items():
            data = await test_client.get(f"project/{id}")
            assert len(data.json()["requests"]) == count

    async def test_removing_project_also_deletes_requests(
        self,
        test_client: "AsyncTestClient",
    ) -> None:
        res = await test_client.post("project", json={"name": "dummy"})
        project_id = res.json()["id"]
        res = await test_client.post("request/base", json={"project_id": project_id})
        request_id = res.json()["id"]
        await test_client.delete(f"project/{project_id}")
        res = await test_client.get(f"request/{request_id}")
        ResponseValidator.validate_item_not_found(res)


@pytest.fixture(scope="function")
async def setup_project(test_client: "AsyncTestClient") -> AsyncGenerator[UUID, None]:
    res = await test_client.post("project", json={"name": "dummy"})
    assert res.status_code == 201
    project_id = res.json()["id"]

    yield project_id

    await test_client.delete(f"project/{project_id}")
    res = await test_client.get(f"project/{project_id}")
    assert res.status_code == 404


FIRST_PROMPT = "first_prompt"
SECOND_PROMPT = "second_prompt"
UPDATE_PROMPT = "update_prompt"
FIRST_IMAGE = b"first_image"
SECOND_IMAGE = b"second_image"
UPDATE_IMAGE = b"update_image"


@pytest.fixture(scope="function")
async def setup_prompts_with_image(
    test_client: "AsyncTestClient", setup_project: UUID
) -> AsyncGenerator[tuple[UUID, UUID], None]:
    project_id = setup_project
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
    yield project_id, request.json()["id"]


@pytest.fixture(scope="function")
async def setup_prompts_with_and_without_image(
    test_client: "AsyncTestClient", setup_project: UUID
) -> AsyncGenerator[tuple[UUID, UUID], None]:
    project_id = setup_project
    request = await test_client.post(
        "request",
        files=[("images", FIRST_IMAGE), ("images", b"")],
        data={
            "text": json.dumps([FIRST_PROMPT, SECOND_PROMPT]),
            "id": json.dumps([None, None]),
            "project_id": str(project_id),
        },
    )
    assert request.status_code == 201
    yield project_id, request.json()["id"]


@pytest.fixture(scope="function")
async def get_prompts_with_and_without_image(
    test_client: "AsyncTestClient", setup_prompts_with_and_without_image: tuple[UUID, UUID]
) -> AsyncGenerator[tuple[UUID, UUID, UUID, UUID], None]:
    project_id, request_id = setup_prompts_with_and_without_image
    request = await test_client.get(f"request/{request_id}")
    assert request.status_code == 200
    prompts = request.json()["prompts"]
    assert len(prompts) == 2
    has_image, no_image = [None, None]
    for prompt in prompts:
        if "image" in prompt and prompt["image"] is not None:
            has_image = prompt["id"]
        else:
            no_image = prompt["id"]
    assert no_image is not None
    assert has_image is not None
    yield project_id, request_id, has_image, no_image


async def test_given_request_with_one_image_read_successful(
    setup_prompts_with_image: tuple[UUID, UUID], test_client: "AsyncTestClient", storage: "StorageServer"
) -> None:
    _, request_id = setup_prompts_with_image
    request = await test_client.get(f"request/{request_id}")
    assert request.status_code == 200
    assert len(request.json()["prompts"]) == 1
    prompt_id = request.json()["prompts"][0]["id"]
    prompt_request = await test_client.get(f"prompt/{prompt_id}")
    assert prompt_request.status_code == 200
    assert prompt_request.json()["text"] == FIRST_PROMPT
    assert prompt_request.json()["image"] is not None
    assert await storage.read(prompt_request.json()["image"]) == FIRST_IMAGE


async def test_given_request_with_and_without_image_update_remove_image_from_prompt_with_image(
    test_client: "AsyncTestClient",
    get_prompts_with_and_without_image: tuple[UUID, UUID, UUID, UUID],
) -> None:
    # Make update
    project_id, request_id, has_image, no_image = get_prompts_with_and_without_image
    request = await test_client.put(
        f"request/{request_id}",
        files=[("images", b""), ("images", b"")],
        data={
            "text": json.dumps([UPDATE_PROMPT, UPDATE_PROMPT]),
            "id": json.dumps([has_image, no_image]),
            "project_id": str(project_id),
        },
    )
    assert request.status_code == 200

    # Validate
    no_image_prompt = await test_client.get(f"prompt/{no_image}")
    assert no_image_prompt.json()["image"] is None
    assert no_image_prompt.json()["text"] == UPDATE_PROMPT
    has_image_prompt = await test_client.get(f"prompt/{has_image}")
    assert has_image_prompt.json()["image"] is None
    assert has_image_prompt.json()["text"] == UPDATE_PROMPT


async def test_given_request_with_and_without_image_update_add_image_from_prompt_with_no_image(
    test_client: "AsyncTestClient",
    get_prompts_with_and_without_image: tuple[UUID, UUID, UUID, UUID],
    storage: StorageServer,
) -> None:
    # Make update
    project_id, request_id, has_image, no_image = get_prompts_with_and_without_image
    request = await test_client.put(
        f"request/{request_id}",
        files=[("images", FIRST_IMAGE), ("images", SECOND_IMAGE)],
        data={
            "text": json.dumps([UPDATE_PROMPT, UPDATE_PROMPT]),
            "id": json.dumps([has_image, no_image]),
            "project_id": str(project_id),
        },
    )
    assert request.status_code == 200

    # Validate
    no_image_prompt = await test_client.get(f"prompt/{no_image}")
    assert no_image_prompt.json()["image"] is not None
    assert await storage.read(no_image_prompt.json()["image"]) == SECOND_IMAGE
    assert no_image_prompt.json()["text"] == UPDATE_PROMPT
    has_image_prompt = await test_client.get(f"prompt/{has_image}")
    assert has_image_prompt.json()["image"] is not None
    assert await storage.read(has_image_prompt.json()["image"]) == FIRST_IMAGE
    assert has_image_prompt.json()["text"] == UPDATE_PROMPT


async def test_given_request_with_and_without_image_update_add_null_id_add_new_prompt(
    test_client: "AsyncTestClient",
    get_prompts_with_and_without_image: tuple[UUID, UUID, UUID, UUID],
    storage: StorageServer,
) -> None:
    # Make update
    project_id, request_id, has_image, no_image = get_prompts_with_and_without_image
    request = await test_client.put(
        f"request/{request_id}",
        files=[("images", FIRST_IMAGE), ("images", SECOND_IMAGE), ("images", UPDATE_IMAGE)],
        data={
            "text": json.dumps([UPDATE_PROMPT, UPDATE_PROMPT, UPDATE_PROMPT]),
            "id": json.dumps([has_image, no_image, None]),
            "project_id": str(project_id),
        },
    )
    assert request.status_code == 200
    request = await test_client.get(f"request/{request_id}")
    assert len(request.json()["prompts"]) == 3
    new_prompt_id = None
    for prompt in request.json()["prompts"]:
        if prompt["id"] not in [has_image, no_image]:
            new_prompt_id = prompt["id"]
    assert new_prompt_id is not None
    # Validate
    no_image_prompt = await test_client.get(f"prompt/{no_image}")
    assert no_image_prompt.json()["image"] is not None
    assert await storage.read(no_image_prompt.json()["image"]) == SECOND_IMAGE
    assert no_image_prompt.json()["text"] == UPDATE_PROMPT
    has_image_prompt = await test_client.get(f"prompt/{has_image}")
    assert has_image_prompt.json()["image"] is not None
    assert await storage.read(has_image_prompt.json()["image"]) == FIRST_IMAGE
    assert has_image_prompt.json()["text"] == UPDATE_PROMPT
    new_prompt = await test_client.get(f"prompt/{new_prompt_id}")
    assert new_prompt.json()["image"] is not None
    assert await storage.read(new_prompt.json()["image"]) == UPDATE_IMAGE
    assert new_prompt.json()["text"] == UPDATE_PROMPT


async def test_given_request_with_and_without_image_update_no_remention_previous_prompts_delete(
    test_client: "AsyncTestClient",
    get_prompts_with_and_without_image: tuple[UUID, UUID, UUID, UUID],
    storage: StorageServer,
) -> None:
    # Make update
    project_id, request_id, has_image, no_image = get_prompts_with_and_without_image
    request = await test_client.put(
        f"request/{request_id}",
        files=[("images", FIRST_IMAGE), ("images", UPDATE_IMAGE)],
        data={
            "text": json.dumps([UPDATE_PROMPT, UPDATE_PROMPT]),
            "id": json.dumps([has_image, None]),
            "project_id": str(project_id),
        },
    )
    assert request.status_code == 200
    request = await test_client.get(f"request/{request_id}")
    assert len(request.json()["prompts"]) == 2
    new_prompt_id = None
    for prompt in request.json()["prompts"]:
        if prompt["id"] not in [has_image, no_image]:
            new_prompt_id = prompt["id"]
    assert new_prompt_id is not None
    # Validate
    no_image_prompt = await test_client.get(f"prompt/{no_image}")
    assert no_image_prompt.status_code == 404
    has_image_prompt = await test_client.get(f"prompt/{has_image}")
    assert has_image_prompt.json()["image"] is not None
    assert await storage.read(has_image_prompt.json()["image"]) == FIRST_IMAGE
    assert has_image_prompt.json()["text"] == UPDATE_PROMPT
    new_prompt = await test_client.get(f"prompt/{new_prompt_id}")
    assert new_prompt.json()["image"] is not None
    assert await storage.read(new_prompt.json()["image"]) == UPDATE_IMAGE
    assert new_prompt.json()["text"] == UPDATE_PROMPT


async def test_given_request_with_and_without_image_update_remove_previous_prompts(
    test_client: "AsyncTestClient",
    get_prompts_with_and_without_image: tuple[UUID, UUID, UUID, UUID],
    storage: StorageServer,
) -> None:
    # Make update
    project_id, request_id, has_image, no_image = get_prompts_with_and_without_image

    request = await test_client.put(
        f"request/{request_id}",
        files=[("images", FIRST_IMAGE)],
        data={
            "text": json.dumps([FIRST_PROMPT]),
            "id": json.dumps([None]),
            "project_id": str(project_id),
        },
    )
    assert request.status_code == 200
    request = await test_client.get(f"request/{request_id}")
    assert len(request.json()["prompts"]) == 1
    new_prompt_id = None
    for prompt in request.json()["prompts"]:
        if prompt["id"] not in [has_image, no_image]:
            new_prompt_id = prompt["id"]
    assert new_prompt_id is not None
    # Validate
    no_image_prompt = await test_client.get(f"prompt/{no_image}")
    assert no_image_prompt.status_code == 404
    has_image_prompt = await test_client.get(f"prompt/{has_image}")
    assert has_image_prompt.status_code == 404
    new_prompt = await test_client.get(f"prompt/{new_prompt_id}")
    assert new_prompt.json()["image"] is not None
    assert await storage.read(new_prompt.json()["image"]) == FIRST_IMAGE
    assert new_prompt.json()["text"] == FIRST_PROMPT


async def test_given_request_with_and_without_image_read_successful(
    test_client: "AsyncTestClient",
    get_prompts_with_and_without_image: tuple[UUID, UUID, UUID, UUID],
    storage: "StorageServer",
) -> None:
    _, _, has_image, no_image = get_prompts_with_and_without_image
    no_image_prompt = await test_client.get(f"prompt/{no_image}")
    assert no_image_prompt.json()["image"] is None
    assert no_image_prompt.json()["text"] == SECOND_PROMPT
    has_image_prompt = await test_client.get(f"prompt/{has_image}")
    image_id = has_image_prompt.json()["image"]
    assert image_id is not None
    assert await storage.read(image_id) == FIRST_IMAGE
    assert has_image_prompt.json()["text"] == FIRST_PROMPT


async def test_delete_request_delete_all_prompts(
    test_client: "AsyncTestClient",
    get_prompts_with_and_without_image: tuple[UUID, UUID, UUID, UUID],
) -> None:
    _, request_id, has_image, no_image = get_prompts_with_and_without_image
    response = await test_client.delete(f"request/{request_id}")
    assert response.status_code == 204
    get_request = await test_client.get(f"request/{request_id}")
    assert get_request.status_code == 404
    get_has_image = await test_client.get(f"prompt/{has_image}")
    assert get_has_image.status_code == 404
    get_no_image = await test_client.get(f"prompt/{no_image}")
    assert get_no_image.status_code == 404
