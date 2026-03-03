"""PDF generation utilities for Colab notebooks."""

from .download_pdf import colab2pdf, colab2pdf_widget
from .magic import register_magic
from .notebook_retrieval import (
    GetIpynbTimeoutError,
    get_notebook_content,
    get_notebook_name,
)

# Auto-register magic on import
register_magic()

__all__ = [
    'colab2pdf',
    'colab2pdf_widget',
    'get_notebook_content',
    'get_notebook_name',
    'GetIpynbTimeoutError',
]
