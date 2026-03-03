"""Main PDF conversion functionality for Colab notebooks."""

import datetime
import locale
import pathlib
import re
import subprocess
import warnings

import IPython
import IPython.display
import ipywidgets
import nbformat
import requests
import yaml

from .notebook_retrieval import get_notebook_content, get_notebook_name


def _install_dependencies():
    """Install required system dependencies for PDF conversion."""
    if not pathlib.Path("/usr/local/bin/quarto").exists():
        print("📦 Installing Quarto...")
        subprocess.run(
            "wget -q 'https://quarto.org/download/latest/quarto-linux-amd64.deb' && "
            "dpkg -i quarto-linux-amd64.deb>/dev/null && "
            "rm quarto-linux-amd64.deb",
            shell=True,
            check=True,
        )
        print("✅ Installation complete!")


def _validate_image_urls(notebook):
    """Validate that all image URLs in markdown cells are accessible."""
    bad_urls = [
        url
        for cell in notebook.cells
        if cell.get("cell_type") == "markdown"
        for url in re.findall(r"!\[.*?\]\((https?://.*?)\)", cell["source"])
        if requests.head(url, timeout=5).status_code != 200
    ]
    if bad_urls:
        raise Exception(f"Bad Image URLs: {','.join(bad_urls)}")


def _prepare_notebook(notebook):
    """Remove Colab2PDF cells and normalize notebook structure."""
    notebook.cells = [cell for cell in notebook.cells if "--Colab2PDF" not in cell.source]
    prepared_nb = nbformat.v4.new_notebook(cells=notebook.cells or [nbformat.v4.new_code_cell("#")])
    nbformat.validator.normalize(prepared_nb)
    return prepared_nb


def _create_quarto_config(output_dir):
    """Create Quarto configuration file with Typst settings."""
    config = {
        "format": {
            "typst": {
                "margin": {
                    "left": "2cm",
                    "right": "2cm",
                    "top": "2.5cm",
                    "bottom": "2.5cm"
                }
            }
        }
    }
    with (output_dir / "_quarto.yml").open("w", encoding="utf-8") as f:
        yaml.dump(config, f)


def _render_pdf(output_dir, notebook_stem):
    """Render the notebook to PDF using Quarto and Typst."""
    render_cmd = f"quarto render {notebook_stem}.ipynb --to typst"
    result = subprocess.run(
        render_cmd, 
        shell=True, 
        capture_output=True, 
        text=True, 
        cwd=str(output_dir)
    )

    if result.returncode != 0:
        print("❌ Render failed!")
        print(f"   STDOUT: {result.stdout}")
        print(f"   STDERR: {result.stderr}")
        raise subprocess.CalledProcessError(
            result.returncode, render_cmd, result.stdout, result.stderr
        )


def colab2pdf(name: str | None = None, retrieval_method: str = 'drive') -> str | None:
    """Convert current Colab notebook to PDF and download it.
    
    Args:
        name: Optional custom name for the PDF file
        retrieval_method: Method to retrieve notebook content. 
                         Options: 'timeout' (default), 'blocking', 'drive'
    
    Returns:
        Path to the generated PDF file, or None if not in Colab
        
    Raises:
        Various exceptions depending on what goes wrong during conversion
    """
    # Check if running in Colab
    try:
        import google.colab
    except ImportError:
        print("⚠️  This function is only available in Google Colab environments.")
        return None

    print("🚀 Starting PDF conversion...")
    _install_dependencies()
    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    warnings.filterwarnings("ignore", category=nbformat.validator.MissingIDFieldWarning)
    IPython.get_ipython().run_line_magic("matplotlib", "inline")

    # Get notebook name and create output directory
    print("📓 Retrieving notebook...")
    notebook_name = get_notebook_name() if name is None else pathlib.Path(name)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_dir = pathlib.Path("/content/pdfs") / f"{timestamp}_{notebook_name.stem}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get and validate notebook content
    print(f"📥 Loading notebook content (method: {retrieval_method})...")
    notebook = get_notebook_content(method=retrieval_method)

    print("🔍 Validating images...")
    _validate_image_urls(notebook)

    # Prepare and write notebook
    print("📝 Preparing notebook...")
    prepared_notebook = _prepare_notebook(notebook)
    notebook_path = output_dir / f"{notebook_name.stem}.ipynb"
    nbformat.write(prepared_notebook, notebook_path.open("w", encoding="utf-8"))

    # Create config and render
    _create_quarto_config(output_dir)
    print("🔨 Rendering PDF with Typst...")
    _render_pdf(output_dir, notebook_name.stem)
    print("   ✓ Render successful")

    # Download PDF
    print("⬇️  Downloading PDF...")
    pdf_path = output_dir / f"{notebook_name.stem}.pdf"
    google.colab.files.download(str(pdf_path))
    print(f"✅ Done! PDF saved as: {notebook_name.stem}.pdf")

    return str(pdf_path)


def colab2pdf_widget():
    """Display an interactive widget to convert and download the current notebook as PDF."""
    # @title Download Notebook in PDF Format{display-mode:'form'}

    def convert(b):
        try:
            s.value = "🔄 Converting"
            b.disabled = True
            pdf_path = colab2pdf()
            if pdf_path:
                s.value = f"✅ Downloaded: {pathlib.Path(pdf_path).name}"
        except Exception as e:
            s.value = f"❌ {str(e)}"
        finally:
            b.disabled = False

    b = ipywidgets.widgets.Button(description="⬇️ Download")
    s = ipywidgets.widgets.Label()
    b.on_click(lambda b: convert(b))
    IPython.display.display(ipywidgets.widgets.HBox([b, s]))
