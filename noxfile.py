import nox
from pathlib import Path

current_path = Path(__file__).parent
package = current_path / "requests_whaor"

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
