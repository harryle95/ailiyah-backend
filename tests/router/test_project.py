from src.model.project import Project
from tests.helpers import AbstractBaseTestSuite


class TestProject(AbstractBaseTestSuite[Project]):
    path = "project"
    fixture = {"first": {"name": "first"}, "second": {"name": "second"}, "third": {"name": "third"}}
    update_fixture = {
        "first": {"name": "first_project"},
        "second": {"name": "second_project"},
        "third": {"name": "third_project"},
    }
