"""Utility for retrieving the current notebook name."""

import os
import pathlib
import urllib


def _fetch_notebook_name() -> str:
    """Return the raw URL-decoded notebook name as reported by the Colab sessions API."""
    import requests

    response = requests.get(
        f"http://{os.environ['COLAB_JUPYTER_IP']}:{os.environ['KMP_TARGET_PORT']}/api/sessions"
    )
    return urllib.parse.unquote(response.json()[0]["name"])


def get_notebook_name() -> pathlib.Path:
    """Retrieve the current notebook name from Colab, sanitised for local filesystem use."""
    import werkzeug.utils

    return pathlib.Path(werkzeug.utils.secure_filename(_fetch_notebook_name()))


def get_notebook_raw_name() -> pathlib.Path:
    """Retrieve the current notebook name from Colab without sanitisation.

    Use this when looking up the file on Google Drive, where the filename
    preserves spaces and special characters exactly as Colab stores it.
    """
    return pathlib.Path(_fetch_notebook_name())
