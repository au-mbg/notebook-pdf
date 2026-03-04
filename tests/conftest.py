"""Shared fixtures for the notebook-pdf test suite."""

import json
import pathlib

import nbformat
import pytest


# ---------------------------------------------------------------------------
# Sample notebook factories
# ---------------------------------------------------------------------------

def make_notebook(*cell_specs) -> nbformat.NotebookNode:
    """Build an in-memory v4 notebook from (type, source) pairs.

    Example::
        nb = make_notebook(("code", "x = 1"), ("markdown", "# Hello"))
    """
    cells = []
    for cell_type, source in cell_specs:
        if cell_type == "code":
            cells.append(nbformat.v4.new_code_cell(source))
        elif cell_type == "markdown":
            cells.append(nbformat.v4.new_markdown_cell(source))
    return nbformat.v4.new_notebook(cells=cells)


@pytest.fixture()
def simple_notebook() -> nbformat.NotebookNode:
    """A minimal two-cell notebook with no special markers."""
    return make_notebook(
        ("code", "x = 1"),
        ("markdown", "# Hello"),
    )


@pytest.fixture()
def notebook_with_marker() -> nbformat.NotebookNode:
    """A notebook where one cell contains the --Colab2PDF marker."""
    return make_notebook(
        ("code", "# --Colab2PDF\nfrom notebook_pdf import notebook2pdf"),
        ("code", "x = 1"),
        ("markdown", "# Keep me"),
    )


@pytest.fixture()
def notebook_with_image_urls() -> nbformat.NotebookNode:
    """A notebook with markdown cells that reference HTTP image URLs."""
    return make_notebook(
        ("markdown", "![ok](https://example.com/good.png)"),
        ("markdown", "![bad](https://example.com/missing.png)"),
    )


@pytest.fixture()
def ipynb_file(tmp_path, simple_notebook) -> pathlib.Path:
    """Write a simple notebook to a temporary .ipynb file and return its path."""
    path = tmp_path / "test_notebook.ipynb"
    nbformat.write(simple_notebook, path.open("w", encoding="utf-8"))
    return path


@pytest.fixture()
def server_runtime_dir(tmp_path) -> pathlib.Path:
    """A fake Jupyter runtime directory containing one server info file."""
    server_info = {
        "url": "http://localhost:9999",
        "token": "testtoken",
        "root_dir": str(tmp_path),
    }
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "nbserver-12345.json").write_text(json.dumps(server_info))
    return runtime
