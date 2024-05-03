from collections.abc import Generator
from dataclasses import dataclass
from typing import Annotated

import pytest
from litestar import Controller, Litestar, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.testing import TestClient, create_test_client


@dataclass
class _PromptRawDTO:
    text: str
    image: UploadFile | None = None


PromptRawDTO = Annotated[_PromptRawDTO, Body(media_type=RequestEncodingType.MULTI_PART)]


class PromptController(Controller):
    path = "prompt"

    @post()
    def create_prompt(self, data: PromptRawDTO) -> str:
        return "Sucess"


@pytest.fixture(scope="function")
def test_client() -> Generator[TestClient[Litestar], None, None]:
    test_client = create_test_client([PromptController])
    yield test_client


def test_with_file(test_client: TestClient[Litestar]) -> None:
    # This works
    data = test_client.post("prompt", files={"image": "data"}, data={"text": "prompt"})
    assert data.status_code == 201


def test_with_no_file(test_client: TestClient[Litestar]) -> None:
    data = test_client.post("prompt", files={"not_data": "data"}, data={"text": "prompt"})
    # Fails here
    assert data.status_code == 201
