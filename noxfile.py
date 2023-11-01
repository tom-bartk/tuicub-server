import os
import pathlib

import nox

PYTHON_DEFAULT_VERSION = "3.11"
LINT_DEPENDENCIES = [
    "black==23.7.0",
    "interrogate==1.5.0",
    "mypy==1.6.1",
    "ruff==0.0.275",
    "types-requests",
]

SRC_DIR = "src/tuicubserver"
REPO_ROOT = pathlib.Path(os.path.dirname(__file__)).resolve()
REPORTS_OUTPUT_DIR = REPO_ROOT / "reports"

nox.options.sessions = ["test"]


@nox.session(python=PYTHON_DEFAULT_VERSION)
def test(session: nox.Session) -> None:
    session.install("-e", ".")
    session.install("pytest", "pytest-asyncio")
    session.run("pytest", "tests/")


@nox.session(python=PYTHON_DEFAULT_VERSION)
def ci(session: nox.Session) -> None:
    REPORTS_OUTPUT_DIR.mkdir(exist_ok=True)

    session.install("-e", ".")
    session.install("pytest", "pytest-asyncio", "pytest-cov", "coverage[toml]")
    session.install(*LINT_DEPENDENCIES)

    # Tests
    session.run(
        "pytest",
        "--junit-xml",
        str(REPORTS_OUTPUT_DIR / "test.xml"),
        "--cov=src.tuicubserver",
        "--cov-report=term-missing",
        "tests/"
    )

    # Coverage
    session.run("coverage", "xml", "-o", str(REPORTS_OUTPUT_DIR / "coverage.xml"))
    session.run("coverage", "erase")

    # Linting
    session.run(
        "ruff",
        "check",
        "--format",
        "junit",
        "--output-file",
        str(REPORTS_OUTPUT_DIR / "lint.xml"),
        ".",
    )

    # Formatting
    session.run("black", "--check", "tests", SRC_DIR)

    # Typing
    session.run("mypy", "--junit-xml", str(REPORTS_OUTPUT_DIR / "typing.xml"), SRC_DIR)

    # Docstrings
    session.run(
        "interrogate",
        "--badge-format",
        "svg",
        "--badge-style",
        "flat",
        "--generate-badge",
        str(REPORTS_OUTPUT_DIR / "interrogate.svg"),
    )
