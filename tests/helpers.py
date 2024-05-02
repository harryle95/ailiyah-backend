import datetime
import os
import random
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Literal, TypeVar
from uuid import UUID

import pytest
from httpx import Response

from src.model.base import Base

HTTP_CODE = Literal[200, 201, 204, 404, 500, 409]
T = TypeVar("T", bound=Base)


if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient


class ResponseValidator:
    @staticmethod
    def validate_status(expected_code: HTTP_CODE, response: Response) -> None:
        assert response.status_code == expected_code

    @staticmethod
    def validate_body_empty(response: Response) -> None:
        ResponseValidator.validate_return_item_count(0, response)

    @staticmethod
    def validate_return_item_count(expected_count: int, response: Response) -> None:
        assert len(response.json()) == expected_count

    @staticmethod
    def validate_response_body(response_body: dict[str, Any], **kwargs: Any) -> None:
        for key, value in kwargs.items():
            assert response_body.get(key, None) == value

    @staticmethod
    def validate_item_created(response: Response, **kwargs: Any) -> None:
        ResponseValidator.validate_status(201, response)
        ResponseValidator.validate_response_body(response.json(), **kwargs)

    @staticmethod
    def validate_item_updated(response: Response, **kwargs: Any) -> None:
        ResponseValidator.validate_status(200, response)
        ResponseValidator.validate_response_body(response.json(), **kwargs)
        if "created_at" in kwargs and "updated_at" in kwargs:
            assert kwargs["updated_at"] - kwargs["created_at"] >= datetime.timedelta(milliseconds=0.1)

    @staticmethod
    def validate_item_exist(response: Response, **kwargs: Any) -> None:
        ResponseValidator.validate_status(200, response)
        ResponseValidator.validate_response_body(response.json(), **kwargs)

    @staticmethod
    def validate_item_deleted(response: Response, **kwargs: Any) -> None:
        ResponseValidator.validate_status(204, response)

    @staticmethod
    def validate_item_not_found(response: Response, **kwargs: Any) -> None:
        ResponseValidator.validate_status(404, response)

    @staticmethod
    def validate_item_conflict(response: Response, **kwargs: Any) -> None:
        ResponseValidator.validate_status(409, response)


class AbstractFixtureManager(Generic[T]):
    model_class: ClassVar[type[Base]]

    def __class_getitem__(cls, model_type: type[T]) -> type:
        cls.model_class = model_type
        cls_dict = {"model_class": cls.model_class}
        return type(f"FixtureManager[{model_type.__name__}]", (cls,), cls_dict)

    def __init__(
        self,
        create_item_success_hooks: list[Callable],
        create_item_failure_hooks: list[Callable],
        update_item_success_hooks: list[Callable],
    ) -> None:
        self.create_item_success_hooks = create_item_success_hooks
        self.create_item_failure_hooks = create_item_failure_hooks
        self.update_item_success_hooks = update_item_success_hooks

    async def create_item_success(self, test_client: "AsyncTestClient", path: str, **kwargs: Any) -> UUID:
        item = self.model_class(**kwargs)
        async with test_client as client:
            response = await client.post(path, json=item.to_dict())
            # Run success hook
            for hook in self.create_item_success_hooks:
                hook(response, **kwargs)
            result: UUID = response.json()["id"]
            return result

    async def create_item_failure(self, test_client: "AsyncTestClient", path: str, **kwargs: Any) -> None:
        item = self.model_class(**kwargs)
        async with test_client as client:
            response = await client.post(path, json=item.to_dict())
            # Run failure
            for hook in self.create_item_failure_hooks:
                hook(response, **kwargs)

    async def destroy_item(self, test_client: "AsyncTestClient", fixture_id: UUID, path: str) -> None:
        async with test_client as client:
            response = await client.delete(os.path.join(path, str(fixture_id)))
            ResponseValidator.validate_item_deleted(response)
            response = await client.get(os.path.join(path, str(fixture_id)))
            ResponseValidator.validate_item_not_found(response)

    async def update_item(self, test_client: "AsyncTestClient", fixture_id: UUID, path: str, **kwargs: Any) -> None:
        if fixture_id is not None:
            async with test_client as client:
                response = await client.put(os.path.join(path, str(fixture_id)), json=kwargs)
                # Run update check
                for hook in self.update_item_success_hooks:
                    hook(response, **kwargs)


class AbstractBaseTestSuite(Generic[T]):
    path: ClassVar[str]
    fixture: ClassVar[dict[str, dict[str, Any]]]
    update_fixture: ClassVar[dict[str, dict[str, Any]]]
    invalid_create_fixture: ClassVar[dict[str, dict[str, Any]]] = {}
    fixture_id: ClassVar[dict[str, UUID]] = {}
    create_item_success_hooks: ClassVar[list[Callable]] = [ResponseValidator.validate_item_created]
    create_item_failure_hooks: ClassVar[list[Callable]] = [ResponseValidator.validate_item_conflict]
    update_item_success_hooks: ClassVar[list[Callable]] = [ResponseValidator.validate_item_updated]
    fixture_manager: ClassVar[AbstractFixtureManager]

    def __class_getitem__(cls, model_type: type[T]) -> type:
        fixture_manager = AbstractFixtureManager[model_type](  # type: ignore[valid-type]
            create_item_failure_hooks=cls.create_item_failure_hooks,
            create_item_success_hooks=cls.create_item_success_hooks,
            update_item_success_hooks=cls.update_item_success_hooks,
        )

        cls_dict = {"fixture_manager": fixture_manager}

        return type(f"TestSuite[{model_type.__name__}]", (cls,), cls_dict)

    @pytest.fixture(scope="function", autouse=True)
    async def setup_create(self, test_client: "AsyncTestClient") -> AsyncGenerator[None, None]:
        titles = random.sample(list(self.fixture.keys()), len(self.fixture))

        for title in titles:
            self.fixture_id[title] = await self.fixture_manager.create_item_success(
                test_client, path=self.path, **self.fixture[title]
            )

        yield

        for key, id in self.fixture_id.items():
            await self.fixture_manager.destroy_item(test_client, path=self.path, fixture_id=id)

    async def test_find_items_by_id_successful(self, test_client: "AsyncTestClient") -> None:
        async with test_client as client:
            for key, fixture_id in self.fixture_id.items():
                response = await client.get(os.path.join(self.path, str(fixture_id)))
                ResponseValidator.validate_item_exist(response, **self.fixture[key])

    async def test_find_all_items_successful(self, test_client: "AsyncTestClient") -> None:
        async with test_client as client:
            response = await client.get(self.path)
            ResponseValidator.validate_status(200, response)
            ResponseValidator.validate_return_item_count(len(self.fixture), response)

    async def test_update_items_successful(self, test_client: "AsyncTestClient") -> None:
        for key, fixture in self.update_fixture.items():
            fixture_id = self.fixture_id[key]
            await self.fixture_manager.update_item(test_client, fixture_id=fixture_id, path=self.path, **fixture)

    async def test_create_invalid_items_unsuccessful(self, test_client: "AsyncTestClient") -> None:
        if self.invalid_create_fixture:
            for key, fixture in self.invalid_create_fixture.items():
                await self.fixture_manager.create_item_failure(test_client, path=self.path, **fixture)
