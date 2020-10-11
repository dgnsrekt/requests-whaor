import nox
from pathlib import Path

project_path = Path(__file__).parent
package = project_path / "requests_whaor"
tests_directory = project_path / "tests"
examples_directory = project_path / "examples"

assert package.exists()
assert tests_directory.exists()
assert examples_directory.exists()

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ["tests", "lint"]


@nox.session
def tests(session):
    session.install("poetry")
    session.run("poetry", "install")
    session.run("poetry", "check")
    session.run("poetry", "run", "pytest", "-vv")


@nox.session
def lint(session):
    session.install(
        "black",
        "flake8",
        "flake8-import-order",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-annotations",
        "pylint",
        "codespell",
    )
    for filename in package.glob("*.py"):
        session.run("black", "--line-length", "99", "--check", "--quiet", str(filename))
        session.run("flake8", "--import-order-style", "google", str(filename))
        session.run("pylint", "--disable=E0401,R0903", str(filename))
        session.run("codespell", str(filename))

    # for filename in tests_directory.glob("*.py"):
    #     session.run("black", "--line-length", "99", "--check", "--quiet", str(filename))
    #     session.run("flake8", "--import-order-style", "google", str(filename))
    #     session.run("pylint", "--disable=E0401,R0903", str(filename))
    #     session.run("codespell", str(filename))


@nox.session
def docs(session):
    session.install("pydoc-markdown", "mkdocs-material", "mkdocs-mermaid2-plugin")
    session.run("python", "examples/burnit.py")
    session.run("pydoc-markdown", "pydoc-markdown.yml", "--server", "--open")
