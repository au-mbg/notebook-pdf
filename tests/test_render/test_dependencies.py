"""Tests for notebook_pdf.render._dependencies (ensure_quarto)."""

import shutil
import sys

import pytest

requires_quarto = pytest.mark.skipif(
    not shutil.which("quarto"), reason="Quarto not on PATH"
)


def test_ensure_quarto_already_present(mocker):
    """No install attempted when quarto is already on PATH."""
    mocker.patch("shutil.which", return_value="/usr/local/bin/quarto")
    run = mocker.patch("subprocess.run")

    from notebook_pdf.render._dependencies import ensure_quarto
    ensure_quarto()

    run.assert_not_called()


def test_ensure_quarto_missing_non_linux(mocker):
    """RuntimeError raised on non-Linux when quarto is missing."""
    mocker.patch("shutil.which", return_value=None)
    mocker.patch.object(sys, "platform", "darwin")

    from notebook_pdf.render._dependencies import ensure_quarto
    with pytest.raises(RuntimeError, match="quarto.org"):
        ensure_quarto()


def test_ensure_quarto_missing_linux_installs(mocker):
    """Installation attempted on Linux when quarto is missing."""
    mocker.patch("shutil.which", return_value=None)
    mocker.patch.object(sys, "platform", "linux")
    run = mocker.patch("subprocess.run")

    from notebook_pdf.render._dependencies import ensure_quarto
    ensure_quarto()

    run.assert_called_once()
    cmd = run.call_args[0][0]
    assert "quarto" in cmd


# ---------------------------------------------------------------------------
# Integration tests — require Quarto on PATH
# ---------------------------------------------------------------------------


@pytest.mark.integration
@requires_quarto
def test_ensure_quarto_finds_real_binary():
    """ensure_quarto() completes without error when Quarto is actually installed."""
    from notebook_pdf.render._dependencies import ensure_quarto
    ensure_quarto()  # should not raise or attempt install

