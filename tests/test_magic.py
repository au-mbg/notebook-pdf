"""Unit tests for the %notebook2pdf IPython magic command."""

import pytest
from IPython.core.interactiveshell import InteractiveShell

from notebook_pdf.magic import Notebook2PDFMagics


@pytest.fixture(scope="module")
def ip():
    """A real (non-Colab) InteractiveShell instance."""
    shell = InteractiveShell.instance()
    yield shell
    InteractiveShell.clear_instance()


@pytest.fixture
def magics(ip):
    return Notebook2PDFMagics(shell=ip)


def test_magic_calls_notebook2pdf_no_args(magics, mocker):
    """Empty line passes name=None to notebook2pdf."""
    mock = mocker.patch("notebook_pdf.magic.Notebook2PDFMagics.notebook2pdf.__wrapped__" if hasattr(Notebook2PDFMagics.notebook2pdf, "__wrapped__") else "notebook_pdf.notebook2pdf.notebook2pdf")
    # Patch at the import site inside the magic method
    mock_fn = mocker.patch("notebook_pdf.notebook2pdf.notebook2pdf")
    magics.notebook2pdf("")
    mock_fn.assert_called_once_with(name=None)


def test_magic_calls_notebook2pdf_with_name(magics, mocker):
    """A non-empty line is forwarded as name=."""
    mock_fn = mocker.patch("notebook_pdf.notebook2pdf.notebook2pdf")
    magics.notebook2pdf("  my_output.pdf  ")
    mock_fn.assert_called_once_with(name="my_output.pdf")


def test_magic_strips_whitespace(magics, mocker):
    """Leading/trailing whitespace in line is stripped."""
    mock_fn = mocker.patch("notebook_pdf.notebook2pdf.notebook2pdf")
    magics.notebook2pdf("   report.pdf   ")
    mock_fn.assert_called_once_with(name="report.pdf")


def test_register_magic_no_error_outside_ipython(mocker):
    """register_magic() silently does nothing when no IPython shell is active."""
    mocker.patch("IPython.get_ipython", return_value=None)
    from notebook_pdf.magic import register_magic
    register_magic()  # must not raise


def test_load_ipython_extension_registers_magic(mocker):
    """load_ipython_extension registers the magics class on the given shell."""
    fake_shell = mocker.MagicMock()
    from notebook_pdf.magic import load_ipython_extension
    load_ipython_extension(fake_shell)
    fake_shell.register_magics.assert_called_once_with(Notebook2PDFMagics)
