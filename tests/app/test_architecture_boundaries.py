"""Architecture boundary checks: package importability and Streamlit isolation."""

import ast
import importlib
import pkgutil
from pathlib import Path

import opra

PACKAGE_ROOT = Path(opra.__file__).resolve().parent
APP_ROOT = PACKAGE_ROOT / "app"


def _imports_streamlit(source: str) -> bool:
    """Return True if the source imports ``streamlit`` (or a submodule of it)."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import) and any(
            alias.name.split(".")[0] == "streamlit" for alias in node.names
        ):
            return True
        if (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and (node.module or "").split(".")[0] == "streamlit"
        ):
            return True
    return False


def test_all_opra_packages_import_cleanly() -> None:
    package_names = [
        info.name for info in pkgutil.walk_packages(opra.__path__, prefix="opra.") if info.ispkg
    ]
    assert "opra.core" in package_names
    assert "opra.app" in package_names
    for name in package_names:
        importlib.import_module(name)


def test_version_is_defined() -> None:
    assert opra.__version__ == "0.1.0"


def test_no_streamlit_import_outside_app_package() -> None:
    checked = [path for path in sorted(PACKAGE_ROOT.rglob("*.py")) if APP_ROOT not in path.parents]
    assert checked, "boundary check found no files outside src/opra/app/"
    offenders = [
        str(path.relative_to(PACKAGE_ROOT))
        for path in checked
        if _imports_streamlit(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_import_detector_flags_streamlit_forms() -> None:
    assert _imports_streamlit("import streamlit")
    assert _imports_streamlit("import streamlit.web as web")
    assert _imports_streamlit("from streamlit import title")
    assert not _imports_streamlit("import json\nfrom pathlib import Path")
