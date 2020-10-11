from requests_whaor import __version__
from requests_whaor.paths import (
    PROJECT_ROOT_PATH,
    SOURCE_ROOT_PATH,
    TEST_PATH,
    TEMPLATE_DIRECTORY,
)
import toml


def test_sanity():
    pyproject_path = PROJECT_ROOT_PATH / "pyproject.toml"
    assert pyproject_path.exists()

    with open(pyproject_path, mode="r") as file:
        content = toml.loads(file.read())

    assert content["tool"]["poetry"].get("version") is not None
    assert content["tool"]["poetry"].get("version") == __version__


def test_sanity_two():
    assert SOURCE_ROOT_PATH.exists()


def test_test_path_exists():
    assert TEST_PATH.exists()


def test_template_path_exists():
    assert TEMPLATE_DIRECTORY.exists()
