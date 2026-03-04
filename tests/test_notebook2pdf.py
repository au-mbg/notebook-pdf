"""Tests for notebook_pdf.notebook2pdf routing and local branch behaviour."""

import pathlib
import shutil

import nbformat
import pytest


# ---------------------------------------------------------------------------
# Routing tests
# ---------------------------------------------------------------------------

def test_routes_to_colab_branch(mocker, tmp_path, ipynb_file):
    """When is_colab() is True, _notebook2pdf_colab is called."""
    mocker.patch("notebook_pdf.notebook2pdf.is_colab", return_value=True)
    mocker.patch("notebook_pdf.notebook2pdf.ensure_quarto")
    colab_fn = mocker.patch(
        "notebook_pdf.notebook2pdf.notebook2pdf_colab",
        return_value=str(tmp_path / "out.pdf"),
    )

    from notebook_pdf.notebook2pdf import notebook2pdf
    notebook2pdf(retrieval_method="drive")

    colab_fn.assert_called_once()


def test_routes_to_local_branch(mocker, tmp_path, ipynb_file):
    """When is_colab() is False, _notebook2pdf_local is called."""
    mocker.patch("notebook_pdf.notebook2pdf.is_colab", return_value=False)
    mocker.patch("notebook_pdf.notebook2pdf.ensure_quarto")
    local_fn = mocker.patch(
        "notebook_pdf.notebook2pdf.notebook2pdf_local",
        return_value=str(tmp_path / "out.pdf"),
    )

    from notebook_pdf.notebook2pdf import notebook2pdf
    notebook2pdf(path=ipynb_file)

    local_fn.assert_called_once()


def test_retrieval_method_forwarded_to_colab_branch(mocker, tmp_path):
    """retrieval_method is forwarded to _notebook2pdf_colab."""
    mocker.patch("notebook_pdf.notebook2pdf.is_colab", return_value=True)
    mocker.patch("notebook_pdf.notebook2pdf.ensure_quarto")
    colab_fn = mocker.patch(
        "notebook_pdf.notebook2pdf.notebook2pdf_colab",
        return_value=str(tmp_path / "out.pdf"),
    )

    from notebook_pdf.notebook2pdf import notebook2pdf
    notebook2pdf(retrieval_method="blocking")

    _, kwargs = colab_fn.call_args
    assert kwargs.get("retrieval_method") == "blocking" or colab_fn.call_args[0][1] == "blocking"


# ---------------------------------------------------------------------------
# Local branch behaviour
# ---------------------------------------------------------------------------

def test_local_branch_does_not_overwrite_source(mocker, ipynb_file):
    """The source .ipynb is not modified by the local render pipeline."""
    original_content = ipynb_file.read_text()

    def fake_render(output_dir, notebook_stem):
        (output_dir / f"{notebook_stem}.pdf").write_bytes(b"%PDF fake")

    mocker.patch("notebook_pdf.notebook2pdf.ensure_quarto")
    mocker.patch("notebook_pdf.notebook2pdf.is_colab", return_value=False)
    mocker.patch("notebook_pdf._local.validate_image_urls")
    mocker.patch("notebook_pdf._local.render_notebook", side_effect=fake_render)
    mocker.patch("notebook_pdf._local.create_quarto_config")
    mocker.patch("notebook_pdf._local.IPython.get_ipython", return_value=None)

    from notebook_pdf.notebook2pdf import notebook2pdf
    notebook2pdf(path=ipynb_file)

    assert ipynb_file.read_text() == original_content


def test_local_branch_pdf_placed_next_to_source(mocker, ipynb_file):
    """The output PDF is written to the same directory as the source notebook."""
    def fake_render(output_dir, notebook_stem):
        (output_dir / f"{notebook_stem}.pdf").write_bytes(b"%PDF fake")

    mocker.patch("notebook_pdf.notebook2pdf.ensure_quarto")
    mocker.patch("notebook_pdf.notebook2pdf.is_colab", return_value=False)
    mocker.patch("notebook_pdf._local.validate_image_urls")
    mocker.patch("notebook_pdf._local.render_notebook", side_effect=fake_render)
    mocker.patch("notebook_pdf._local.create_quarto_config")
    mocker.patch("notebook_pdf._local.IPython.get_ipython", return_value=None)

    from notebook_pdf.notebook2pdf import notebook2pdf
    result = notebook2pdf(path=ipynb_file)

    assert result is not None
    pdf_path = pathlib.Path(result)
    assert pdf_path.parent == ipynb_file.parent
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.exists()


def test_local_branch_render_failure_propagates(mocker, ipynb_file):
    """Exceptions from render_notebook propagate out of notebook2pdf."""
    mocker.patch("notebook_pdf.notebook2pdf.ensure_quarto")
    mocker.patch("notebook_pdf.notebook2pdf.is_colab", return_value=False)
    mocker.patch("notebook_pdf._local.validate_image_urls")
    mocker.patch(
        "notebook_pdf._local.render_notebook",
        side_effect=RuntimeError("quarto exploded"),
    )
    mocker.patch("notebook_pdf._local.create_quarto_config")

    from notebook_pdf.notebook2pdf import notebook2pdf
    with pytest.raises(RuntimeError, match="quarto exploded"):
        notebook2pdf(path=ipynb_file)
