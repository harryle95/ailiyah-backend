import random
from collections.abc import AsyncGenerator, Generator
from typing import Any
from uuid import UUID

import pytest
from litestar.testing import AsyncTestClient

from src.model import Project, Request
from src.model.base import Base
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
            self.fixture[key]["project_id"] = replacement_key  # type: ignore

        # Count number of requests for each project
        self.counter: dict[str, int] = {}
        for _, value in self.fixture.items():
            id = value["project_id"]
            if id in self.counter:
                self.counter[id] += 1
            else:
                self.counter[id] = 1
        async for _ in setup(self.fixture, self.fixture_id, self.fixture_manager, test_client, "request", Request):
            yield

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
        res = await test_client.post("request", json={"project_id": project_id})
        request_id = res.json()["id"]
        await test_client.delete(f"project/{project_id}")
        res = await test_client.get(f"request/{request_id}")
        ResponseValidator.validate_item_not_found(res)
