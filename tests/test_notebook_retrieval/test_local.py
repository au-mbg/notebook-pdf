"""Tests for notebook_pdf.notebook_retrieval.local."""

import nbformat
import pytest


def test_reads_valid_notebook(ipynb_file):
    """A valid .ipynb file is read and returned as a NotebookNode."""
    from notebook_pdf.notebook_retrieval.local import get_notebook_content_from_path

    nb = get_notebook_content_from_path(ipynb_file)
    assert isinstance(nb, nbformat.NotebookNode)
    assert len(nb.cells) > 0


def test_raises_for_missing_file(tmp_path):
    """FileNotFoundError raised when the path does not exist."""
    from notebook_pdf.notebook_retrieval.local import get_notebook_content_from_path

    with pytest.raises(FileNotFoundError):
        get_notebook_content_from_path(tmp_path / "nonexistent.ipynb")


def test_accepts_string_path(ipynb_file):
    """A string path is accepted as well as a pathlib.Path."""
    from notebook_pdf.notebook_retrieval.local import get_notebook_content_from_path

    nb = get_notebook_content_from_path(str(ipynb_file))
    assert isinstance(nb, nbformat.NotebookNode)
