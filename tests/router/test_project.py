from collections.abc import AsyncGenerator

import pytest
from litestar.testing import AsyncTestClient

from src.model import Project
from tests.helpers import AbstractBaseTestSuite, setup


class TestProject(AbstractBaseTestSuite[Project]):
    path = "project"
    fixture = {"first": {"name": "first"}, "second": {"name": "second"}, "third": {"name": "third"}}
    update_fixture = {
        "first": {"name": "first_project"},
        "second": {"name": "second_project"},
        "third": {"name": "third_project"},
    }

    @pytest.fixture(scope="function", autouse=True)
    async def setup_create(self, test_client: "AsyncTestClient") -> AsyncGenerator[None, None]:
        async for _ in setup(
            self.fixture, self.fixture_id, self.fixture_manager, test_client, self.path, self.model_class
        ):
            yield

    async def test_read_by_name(self, test_client: "AsyncTestClient") -> None:
        result = await test_client.get("project", params={"name": "first_project"})
        assert result.status_code == 200
