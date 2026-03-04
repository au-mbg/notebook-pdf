"""Tests for notebook_pdf.render._render (render_notebook)."""

import shutil
import subprocess
import unittest.mock as mock

import nbformat
import pytest

requires_quarto = pytest.mark.skipif(
    not shutil.which("quarto"), reason="Quarto not on PATH"
)


def test_render_success(mocker, tmp_path):
    """No exception raised when quarto exits with code 0."""
    mocker.patch(
        "subprocess.run",
        return_value=mock.Mock(returncode=0, stdout="", stderr=""),
    )

    from notebook_pdf.render._render import render_notebook
    render_notebook(tmp_path, "my_notebook")  # should not raise


def test_render_passes_correct_command(mocker, tmp_path):
    """The command string contains the notebook stem and --to typst."""
    run = mocker.patch(
        "subprocess.run",
        return_value=mock.Mock(returncode=0, stdout="", stderr=""),
    )

    from notebook_pdf.render._render import render_notebook
    render_notebook(tmp_path, "my_notebook")

    cmd = run.call_args[0][0]
    assert "my_notebook.ipynb" in cmd
    assert "--to typst" in cmd


def test_render_uses_output_dir_as_cwd(mocker, tmp_path):
    """subprocess.run is called with cwd=output_dir."""
    run = mocker.patch(
        "subprocess.run",
        return_value=mock.Mock(returncode=0, stdout="", stderr=""),
    )

    from notebook_pdf.render._render import render_notebook
    render_notebook(tmp_path, "my_notebook")

    assert run.call_args.kwargs["cwd"] == str(tmp_path)


def test_render_raises_on_nonzero_exit(mocker, tmp_path):
    """CalledProcessError raised with stdout/stderr when quarto fails."""
    mocker.patch(
        "subprocess.run",
        return_value=mock.Mock(returncode=1, stdout="out", stderr="err"),
    )

    from notebook_pdf.render._render import render_notebook
    with pytest.raises(subprocess.CalledProcessError):
        render_notebook(tmp_path, "my_notebook")


# ---------------------------------------------------------------------------
# Integration tests — require Quarto on PATH
# ---------------------------------------------------------------------------


@pytest.mark.integration
@requires_quarto
def test_render_produces_pdf(tmp_path):
    """render_notebook actually calls quarto and produces a PDF."""
    from notebook_pdf.render._config import create_quarto_config
    from notebook_pdf.render._render import render_notebook

    # Write a trivial notebook
    nb = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("x = 1")])
    nbformat.validator.normalize(nb)
    nb_path = tmp_path / "simple.ipynb"
    nbformat.write(nb, nb_path.open("w", encoding="utf-8"))

    create_quarto_config(tmp_path)
    render_notebook(tmp_path, "simple")  # should not raise

    assert (tmp_path / "simple.pdf").exists(), "Quarto did not produce a PDF"
    assert (tmp_path / "simple.pdf").stat().st_size > 0

