"""Integration tests: execute real notebooks with nbmake.

These tests are marked ``integration`` and are skipped unless Quarto is on PATH.
Run them explicitly with::

    uv run pytest -m integration

or skip them (default CI) with::

    uv run pytest -m 'not integration'
"""

import shutil
import pathlib
import subprocess
import sys

import pytest

NOTEBOOKS_DIR = pathlib.Path(__file__).parent / "notebooks"


def quarto_available():
    return shutil.which("quarto") is not None


@pytest.mark.integration
@pytest.mark.skipif(not quarto_available(), reason="Quarto not on PATH")
def test_local_render_notebook(tmp_path):
    """Execute the fixture notebook and assert a PDF is produced next to it."""
    import shutil as _shutil

    # Copy fixture into tmp_path so the PDF lands there (keeps repo clean)
    src = NOTEBOOKS_DIR / "test_local_render.ipynb"
    dest = tmp_path / src.name
    _shutil.copy(src, dest)

    result = subprocess.run(
        [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "notebook",
            "--execute",
            "--ExecutePreprocessor.timeout=120",
            "--inplace",
            str(dest),
        ],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )

    assert result.returncode == 0, (
        f"Notebook execution failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

    pdfs = list(tmp_path.glob("*.pdf"))
    assert pdfs, (
        f"No PDF found in {tmp_path} after execution.\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert pdfs[0].stat().st_size > 0, "PDF file is empty"
