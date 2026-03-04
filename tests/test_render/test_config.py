"""Tests for notebook_pdf.render._config (create_quarto_config)."""

import shutil

import nbformat
import pytest
import yaml

requires_quarto = pytest.mark.skipif(
    not shutil.which("quarto"), reason="Quarto not on PATH"
)


def test_creates_quarto_yml(tmp_path):
    """_quarto.yml is written with the expected Typst margin keys."""
    from notebook_pdf.render._config import create_quarto_config

    create_quarto_config(tmp_path)

    config_path = tmp_path / "_quarto.yml"
    assert config_path.exists()

    config = yaml.safe_load(config_path.read_text())
    margins = config["format"]["typst"]["margin"]
    assert margins["left"] == "2cm"
    assert margins["right"] == "2cm"
    assert margins["top"] == "2.5cm"
    assert margins["bottom"] == "2.5cm"


def test_overwrites_existing_config(tmp_path):
    """Calling create_quarto_config twice overwrites the previous file."""
    from notebook_pdf.render._config import create_quarto_config

    (tmp_path / "_quarto.yml").write_text("old: content")
    create_quarto_config(tmp_path)

    config = yaml.safe_load((tmp_path / "_quarto.yml").read_text())
    assert "format" in config


# ---------------------------------------------------------------------------
# Integration tests — require Quarto on PATH
# ---------------------------------------------------------------------------


@pytest.mark.integration
@requires_quarto
def test_config_accepted_by_quarto(tmp_path):
    """Quarto renders without error when using the generated _quarto.yml."""
    from notebook_pdf.render._config import create_quarto_config
    from notebook_pdf.render._render import render_notebook

    nb = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("x = 1")])
    nbformat.validator.normalize(nb)
    nbformat.write(nb, (tmp_path / "cfg_test.ipynb").open("w", encoding="utf-8"))

    create_quarto_config(tmp_path)
    render_notebook(tmp_path, "cfg_test")  # raises if Quarto rejects the config

    pdf = tmp_path / "cfg_test.pdf"
    assert pdf.exists() and pdf.stat().st_size > 0

