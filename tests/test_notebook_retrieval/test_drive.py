"""Tests for notebook_pdf.notebook_retrieval.drive (filesystem-testable helpers)."""

import pathlib

import nbformat
import pytest


# ---------------------------------------------------------------------------
# _resolve_notebook_filename
# ---------------------------------------------------------------------------

def test_resolve_uses_raw_name(mocker):
    """_resolve_notebook_filename returns stem+suffix from get_notebook_raw_name."""
    mocker.patch(
        "notebook_pdf.notebook_retrieval.drive.get_notebook_raw_name",
        return_value=pathlib.Path("My Notebook.ipynb"),
    )
    from notebook_pdf.notebook_retrieval.drive import _resolve_notebook_filename
    assert _resolve_notebook_filename() == "My Notebook.ipynb"


def test_resolve_adds_ipynb_suffix_when_missing(mocker):
    """A raw name without a suffix gets .ipynb appended."""
    mocker.patch(
        "notebook_pdf.notebook_retrieval.drive.get_notebook_raw_name",
        return_value=pathlib.Path("My Notebook"),
    )
    from notebook_pdf.notebook_retrieval.drive import _resolve_notebook_filename
    assert _resolve_notebook_filename() == "My Notebook.ipynb"


# ---------------------------------------------------------------------------
# _find_notebook_on_drive
# ---------------------------------------------------------------------------

def test_find_returns_candidate_dir_match(tmp_path):
    """Returns the first candidate dir hit without doing a glob search."""
    nb = tmp_path / "notebook.ipynb"
    nb.touch()

    from notebook_pdf.notebook_retrieval.drive import _find_notebook_on_drive
    result = _find_notebook_on_drive(
        "notebook.ipynb",
        candidate_dirs=[tmp_path],
        drive_root=tmp_path,
    )
    assert result == nb


def test_find_prefers_first_candidate(tmp_path):
    """When multiple candidate dirs contain the file, the first is returned."""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    (dir_a / "notebook.ipynb").touch()
    (dir_b / "notebook.ipynb").touch()

    from notebook_pdf.notebook_retrieval.drive import _find_notebook_on_drive
    result = _find_notebook_on_drive(
        "notebook.ipynb",
        candidate_dirs=[dir_a, dir_b],
        drive_root=tmp_path,
    )
    assert result == dir_a / "notebook.ipynb"


def test_find_falls_back_to_glob(tmp_path):
    """Falls back to recursive glob when no candidate dir matches."""
    subdir = tmp_path / "deep" / "nested"
    subdir.mkdir(parents=True)
    nb = subdir / "notebook.ipynb"
    nb.touch()

    from notebook_pdf.notebook_retrieval.drive import _find_notebook_on_drive
    result = _find_notebook_on_drive(
        "notebook.ipynb",
        candidate_dirs=[tmp_path / "nonexistent"],
        drive_root=tmp_path,
    )
    assert result == nb


def test_find_raises_when_not_found(tmp_path):
    """FileNotFoundError raised when no match exists anywhere."""
    from notebook_pdf.notebook_retrieval.drive import _find_notebook_on_drive
    with pytest.raises(FileNotFoundError, match="Could not find"):
        _find_notebook_on_drive(
            "missing.ipynb",
            candidate_dirs=[tmp_path / "nonexistent"],
            drive_root=tmp_path,
        )


def test_find_raises_on_ambiguous_matches(tmp_path):
    """FileNotFoundError raised when multiple matches are found."""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    (dir_a / "notebook.ipynb").touch()
    (dir_b / "notebook.ipynb").touch()

    from notebook_pdf.notebook_retrieval.drive import _find_notebook_on_drive
    with pytest.raises(FileNotFoundError, match="Found 2 notebooks"):
        _find_notebook_on_drive(
            "notebook.ipynb",
            candidate_dirs=[tmp_path / "nonexistent"],  # skip fast path
            drive_root=tmp_path,
        )


def test_find_error_lists_conflicting_paths(tmp_path):
    """The ambiguity error message includes both conflicting paths."""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    (dir_a / "notebook.ipynb").touch()
    (dir_b / "notebook.ipynb").touch()

    from notebook_pdf.notebook_retrieval.drive import _find_notebook_on_drive
    with pytest.raises(FileNotFoundError) as exc_info:
        _find_notebook_on_drive(
            "notebook.ipynb",
            candidate_dirs=[tmp_path / "nonexistent"],
            drive_root=tmp_path,
        )
    msg = str(exc_info.value)
    assert str(dir_a / "notebook.ipynb") in msg
    assert str(dir_b / "notebook.ipynb") in msg


# ---------------------------------------------------------------------------
# _read_notebook
# ---------------------------------------------------------------------------

def test_read_notebook_returns_node(ipynb_file):
    """_read_notebook returns a NotebookNode for a valid file."""
    from notebook_pdf.notebook_retrieval.drive import _read_notebook
    nb = _read_notebook(ipynb_file)
    assert isinstance(nb, nbformat.NotebookNode)
