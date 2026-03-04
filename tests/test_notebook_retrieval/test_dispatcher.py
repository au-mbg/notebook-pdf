"""Tests for notebook_pdf.notebook_retrieval get_notebook_content dispatcher."""

import pytest


def test_dispatches_to_blocking(mocker):
    """method='blocking' calls get_notebook_content_blocking."""
    mock_fn = mocker.patch(
        "notebook_pdf.notebook_retrieval.get_notebook_content_blocking"
    )
    from notebook_pdf.notebook_retrieval import get_notebook_content
    get_notebook_content(method="blocking")
    mock_fn.assert_called_once()


def test_dispatches_to_drive(mocker):
    """method='drive' calls get_notebook_content_from_drive."""
    mock_fn = mocker.patch(
        "notebook_pdf.notebook_retrieval.get_notebook_content_from_drive"
    )
    from notebook_pdf.notebook_retrieval import get_notebook_content
    get_notebook_content(method="drive")
    mock_fn.assert_called_once()


def test_dispatches_to_local(mocker, ipynb_file):
    """method='local' calls get_notebook_content_from_path."""
    mock_fn = mocker.patch(
        "notebook_pdf.notebook_retrieval.get_notebook_content_from_path"
    )
    from notebook_pdf.notebook_retrieval import get_notebook_content
    get_notebook_content(method="local", path=ipynb_file)
    mock_fn.assert_called_once_with(path=ipynb_file)


def test_unknown_method_raises():
    """ValueError raised for an unrecognised method string."""
    from notebook_pdf.notebook_retrieval import get_notebook_content
    with pytest.raises(ValueError, match="Unknown method"):
        get_notebook_content(method="ftp")


def test_kwargs_forwarded(mocker):
    """Extra kwargs are forwarded to the underlying retrieval function."""
    mock_fn = mocker.patch(
        "notebook_pdf.notebook_retrieval.get_notebook_content_blocking"
    )
    from notebook_pdf.notebook_retrieval import get_notebook_content
    get_notebook_content(method="blocking", timeout=20)
    mock_fn.assert_called_once_with(timeout=20)
