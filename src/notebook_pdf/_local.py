"""Local PDF conversion branch."""

import pathlib
import shutil
import tempfile

import IPython
import IPython.display
import nbformat

from .notebook_retrieval import get_notebook_content, get_notebook_name_local
from .render import create_quarto_config, prepare_notebook, render_notebook, validate_image_urls


def notebook2pdf_local(path: pathlib.Path | str | None, **kwargs) -> str:
    """Render a local notebook to PDF and display a FileLink to the result.

    The source ``.ipynb`` file is never modified.  All intermediate files are
    written to a temporary directory that is cleaned up automatically.  The
    finished PDF is copied next to the source notebook.

    Args:
        path:     Path to the ``.ipynb`` file.  If ``None``, the path is
                  inferred from the running kernel.
        **kwargs: Currently unused; reserved for future options.

    Returns:
        Absolute path to the generated PDF file.
    """
    if path is None:
        print("🔍 Detecting notebook path...")
        path = get_notebook_name_local()
    path = pathlib.Path(path).resolve()

    notebook_stem = path.stem

    print(f"📥 Loading notebook from: {path}")
    notebook = get_notebook_content(method="local", path=path)

    print("🔍 Validating images...")
    validate_image_urls(notebook)

    print("📝 Preparing notebook...")
    prepared = prepare_notebook(notebook)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = pathlib.Path(tmp)
        nbformat.write(prepared, (tmp_dir / f"{notebook_stem}.ipynb").open("w", encoding="utf-8"))
        create_quarto_config(tmp_dir)
        print("🔨 Rendering PDF with Typst...")
        render_notebook(tmp_dir, notebook_stem)
        print("   ✓ Render successful")

        pdf_path = path.parent / f"{notebook_stem}.pdf"
        shutil.copy2(tmp_dir / f"{notebook_stem}.pdf", pdf_path)

    print(f"✅ Done! PDF saved as: {pdf_path}")
    if IPython.get_ipython() is not None:
        IPython.display.display(IPython.display.FileLink(str(pdf_path)))

    return str(pdf_path)
