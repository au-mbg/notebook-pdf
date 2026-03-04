"""Tests for notebook_pdf.render._prepare."""

import shutil
import unittest.mock as mock

import nbformat
import pytest

from conftest import make_notebook

requires_quarto = pytest.mark.skipif(
    not shutil.which("quarto"), reason="Quarto not on PATH"
)


def test_prepare_strips_marker_cells(notebook_with_marker):
    """Cells containing --Colab2PDF are removed."""
    from notebook_pdf.render._prepare import prepare_notebook

    result = prepare_notebook(notebook_with_marker)
    sources = [c.source for c in result.cells]
    assert not any("--Colab2PDF" in s for s in sources)
    assert any("x = 1" in s for s in sources)


def test_prepare_keeps_clean_cells(simple_notebook):
    """Cells without the marker are preserved."""
    from notebook_pdf.render._prepare import prepare_notebook

    result = prepare_notebook(simple_notebook)
    assert len(result.cells) == 2


def test_prepare_empty_notebook_gets_placeholder():
    """An all-marker notebook gets a single placeholder cell."""
    from notebook_pdf.render._prepare import prepare_notebook

    nb = make_notebook(("code", "# --Colab2PDF"))
    result = prepare_notebook(nb)
    assert len(result.cells) == 1
    assert result.cells[0].source == "#"


def test_prepare_returns_notebook_node(simple_notebook):
    """Return value is always a NotebookNode."""
    from notebook_pdf.render._prepare import prepare_notebook

    result = prepare_notebook(simple_notebook)
    assert isinstance(result, nbformat.NotebookNode)


def test_validate_image_urls_passes_on_good_urls(mocker, notebook_with_image_urls):
    """No exception raised when all URLs return 200."""
    mock_resp = mock.Mock()
    mock_resp.status_code = 200
    mocker.patch("requests.head", return_value=mock_resp)

    from notebook_pdf.render._prepare import validate_image_urls
    validate_image_urls(notebook_with_image_urls)  # should not raise


def test_validate_image_urls_raises_on_bad_url(mocker, notebook_with_image_urls):
    """Exception raised listing all URLs that did not return 200."""
    def fake_head(url, **kwargs):
        resp = mock.Mock()
        resp.status_code = 200 if "good" in url else 404
        return resp

    mocker.patch("requests.head", side_effect=fake_head)

    from notebook_pdf.render._prepare import validate_image_urls
    with pytest.raises(Exception, match="missing.png"):
        validate_image_urls(notebook_with_image_urls)


def test_validate_image_urls_ignores_non_markdown(mocker):
    """URLs in code cells are not checked."""
    mock_resp = mock.Mock()
    mock_resp.status_code = 404
    mocker.patch("requests.head", return_value=mock_resp)

    nb = make_notebook(("code", "url = 'https://example.com/img.png'"))

    from notebook_pdf.render._prepare import validate_image_urls
    validate_image_urls(nb)  # should not raise; code cells are ignored


# ---------------------------------------------------------------------------
# Integration tests — require Quarto on PATH
# ---------------------------------------------------------------------------


@pytest.mark.integration
@requires_quarto
def test_prepare_then_render_produces_pdf(tmp_path, simple_notebook):
    """prepare_notebook output can be written to disk and rendered by Quarto."""
    from notebook_pdf.render._config import create_quarto_config
    from notebook_pdf.render._prepare import prepare_notebook
    from notebook_pdf.render._render import render_notebook

    prepared = prepare_notebook(simple_notebook)
    nb_path = tmp_path / "prepared.ipynb"
    nbformat.write(prepared, nb_path.open("w", encoding="utf-8"))

    create_quarto_config(tmp_path)
    render_notebook(tmp_path, "prepared")

    assert (tmp_path / "prepared.pdf").exists()
    assert (tmp_path / "prepared.pdf").stat().st_size > 0


@pytest.mark.integration
@requires_quarto
def test_prepare_strips_markers_before_render(tmp_path, notebook_with_marker):
    """Marker cells are stripped; Quarto still produces a valid PDF."""
    from notebook_pdf.render._config import create_quarto_config
    from notebook_pdf.render._prepare import prepare_notebook
    from notebook_pdf.render._render import render_notebook

    prepared = prepare_notebook(notebook_with_marker)
    sources = [c.source for c in prepared.cells]
    assert not any("--Colab2PDF" in s for s in sources)

    nb_path = tmp_path / "stripped.ipynb"
    nbformat.write(prepared, nb_path.open("w", encoding="utf-8"))

    create_quarto_config(tmp_path)
    render_notebook(tmp_path, "stripped")

    assert (tmp_path / "stripped.pdf").exists()

