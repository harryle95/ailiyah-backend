from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar import Litestar
from litestar.testing import AsyncTestClient

from src.helpers import create_db_config, on_test_shutdown, provide_test_storage, provide_transaction
from src.router import ImageController, ProjectController, PromptController, RequestController
from src.service.storage.base import StorageServer


@pytest.fixture(scope="function", autouse=True)
async def test_client() -> AsyncGenerator[AsyncTestClient[Litestar], None]:
    p = Path("test.sqlite")
    db_config = create_db_config("test.sqlite")
    app = Litestar(
        [ProjectController, RequestController, PromptController, ImageController],
        dependencies={"transaction": provide_transaction, "storage": provide_test_storage},
        plugins=[SQLAlchemyPlugin(db_config)],
        on_shutdown=[on_test_shutdown],
    )
    async with AsyncTestClient(app=app) as client:
        yield client
    p.unlink(missing_ok=True)


@pytest.fixture(scope="function")
async def storage() -> AsyncGenerator[StorageServer, None]:
    storage = await provide_test_storage().__anext__()
    yield storage
