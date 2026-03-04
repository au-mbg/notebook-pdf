"""Main entry point for notebook-to-PDF conversion."""

import locale
import pathlib
import warnings
from typing import Literal

import nbformat

from ._colab import notebook2pdf_colab
from ._env import is_colab
from ._local import notebook2pdf_local
from .render import ensure_quarto


RetrievalMethod = Literal["drive", "blocking"]


def notebook2pdf(
    name: str | None = None,
    path: str | pathlib.Path | None = None,
    retrieval_method: RetrievalMethod = "drive",
    **kwargs,
) -> str | None:
    """Convert the current notebook to PDF and deliver it.

    In Colab, the PDF is rendered in ``/content/pdfs/`` and automatically
    downloaded to the browser.  Outside Colab, the PDF is written next to the
    source notebook and a clickable ``FileLink`` is displayed.

    Args:
        name:             (Colab only) Custom stem for the output filename.
        path:             (Local only) Path to the ``.ipynb`` file.  If omitted,
                          the path is inferred from the running kernel.
        retrieval_method: (Colab only) How to fetch the notebook content.
                          One of ``'drive'`` (default) or ``'blocking'``.
        **kwargs:         Additional arguments forwarded to the retrieval function.

    Returns:
        Absolute path to the generated PDF, or ``None`` if conversion failed.
    """
    warnings.filterwarnings("ignore", category=nbformat.validator.MissingIDFieldWarning)
    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

    print("🚀 Starting PDF conversion...")
    ensure_quarto()

    if is_colab():
        return notebook2pdf_colab(name=name, retrieval_method=retrieval_method, **kwargs)
    else:
        return notebook2pdf_local(path=path, **kwargs)

