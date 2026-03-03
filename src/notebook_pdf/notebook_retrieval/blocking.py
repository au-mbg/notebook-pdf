"""Blocking notebook content retrieval method."""

import json

import nbformat


def get_notebook_content_blocking(timeout=15):
    """Retrieve notebook content using Colab's blocking request (original method).

    Args:
        timeout: Timeout in seconds for the blocking request

    Returns:
        nbformat.NotebookNode

    Raises:
        ImportError: If not running in Colab
        Exception: If retrieval fails
    """
    import google.colab

    ipynb_data = google.colab._message.blocking_request("get_ipynb", timeout_sec=timeout)["ipynb"]
    return nbformat.reads(json.dumps(ipynb_data), as_version=4)
