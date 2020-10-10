"""Module for commonly used paths."""

from pathlib import Path

SOURCE_ROOT_PATH = Path(__file__).parent
"""* A path to the source code directory."""

PROJECT_ROOT_PATH = SOURCE_ROOT_PATH.parent
"""* A path to the project root directory."""

TEST_PATH = PROJECT_ROOT_PATH / "tests"
"""* A path to the test directory."""

TEMPLATE_DIRECTORY = SOURCE_ROOT_PATH / "templates"
"""* A path to the templates directory."""

TEMPORARY_FILES_DIRECTORY = PROJECT_ROOT_PATH / "temporary_files"
"""* A path to the temporary files directory."""
