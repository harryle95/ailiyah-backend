import pytest 

@pytest.fixture(scope="function")
def dummy()->int:
    return 1 

def test_dummy(dummy: int)->None:
    assert dummy == 1 