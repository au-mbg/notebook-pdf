"""IPython magic command registration for colab2pdf."""

import IPython
from IPython.core.magic import Magics, line_magic, magics_class


@magics_class
class Colab2PDFMagics(Magics):
    """IPython magic commands for PDF conversion."""

    @line_magic
    def colab2pdf(self, line):
        """Convert current notebook to PDF.

        Usage:
            %colab2pdf              # Use automatic notebook name
            %colab2pdf myfile.pdf   # Use custom name
        """
        # Import here to avoid circular imports
        from .download_pdf import colab2pdf
        
        name = line.strip() if line.strip() else None
        return colab2pdf(name=name)


def load_ipython_extension(ipython):
    """Load the extension in IPython."""
    ipython.register_magics(Colab2PDFMagics)


def register_magic():
    """Automatically register magic command when module is imported."""
    try:
        ipython = IPython.get_ipython()
        if ipython is not None:
            ipython.register_magics(Colab2PDFMagics)
    except Exception:
        pass  # Not in IPython environment
