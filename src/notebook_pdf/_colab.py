"""Colab-specific PDF conversion branch."""

import datetime
import pathlib

import nbformat

from .notebook_retrieval import get_notebook_content, get_notebook_name
from .render import create_quarto_config, prepare_notebook, render_notebook, validate_image_urls


def notebook2pdf_colab(
    name: str | None,
    retrieval_method: str,
    **kwargs,
) -> str:
    """Retrieve the current Colab notebook, render it to PDF, and trigger a browser download.

    Args:
        name:             Optional custom stem for the output filename.
        retrieval_method: One of ``'drive'`` or ``'blocking'``.
        **kwargs:         Forwarded to the retrieval function.

    Returns:
        Absolute path to the generated PDF file.
    """
    import google.colab

    notebook_name = get_notebook_name() if name is None else pathlib.Path(name)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_dir = pathlib.Path("/content/pdfs") / f"{timestamp}_{notebook_name.stem}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📥 Loading notebook content (method: {retrieval_method})...")
    notebook = get_notebook_content(method=retrieval_method, **kwargs)

    print("🔍 Validating images...")
    validate_image_urls(notebook)

    print("📝 Preparing notebook...")
    prepared = prepare_notebook(notebook)
    nbformat.write(prepared, (output_dir / f"{notebook_name.stem}.ipynb").open("w", encoding="utf-8"))

    create_quarto_config(output_dir)
    print("🔨 Rendering PDF with Typst...")
    render_notebook(output_dir, notebook_name.stem)
    print("   ✓ Render successful")

    pdf_path = output_dir / f"{notebook_name.stem}.pdf"
    print("⬇️  Downloading PDF...")
    google.colab.files.download(str(pdf_path))
    print(f"✅ Done! PDF saved as: {notebook_name.stem}.pdf")

    return str(pdf_path)
