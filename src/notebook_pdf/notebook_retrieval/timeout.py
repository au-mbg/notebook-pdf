"""Timeout-safe notebook content retrieval method."""

import json
import queue
import threading

import nbformat

from ._errors import GetIpynbTimeoutError


def get_notebook_content_with_timeout(inner_timeout=5, outer_timeout=10):
    """Retrieve notebook content with hard timeout to keep kernel responsive.

    Uses a separate thread to avoid blocking the kernel indefinitely.

    Args:
        inner_timeout: Timeout passed to Colab's blocking_request (seconds)
        outer_timeout: Maximum time we wait before giving up (seconds)

    Returns:
        nbformat.NotebookNode

    Raises:
        GetIpynbTimeoutError: If notebook not retrieved within outer_timeout
        ImportError: If not running in Colab
        RuntimeError: If response is malformed
    """
    from google.colab import _message

    q = queue.Queue()

    def worker():
        try:
            reply = _message.blocking_request(
                "get_ipynb",
                timeout_sec=inner_timeout,
            )
            q.put((True, reply))
        except Exception as e:
            q.put((False, e))

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    try:
        ok, payload = q.get(timeout=outer_timeout)
    except queue.Empty:
        # Worker thread is still blocked, but we choose to walk away
        raise GetIpynbTimeoutError(
            f"get_ipynb did not respond within {outer_timeout} seconds"
        )

    if not ok:
        # Re-raise the exception from blocking_request
        raise payload

    reply = payload
    ipynb_data = reply.get("ipynb")
    if ipynb_data is None:
        raise RuntimeError("get_ipynb reply missing 'ipynb' field")

    return nbformat.reads(json.dumps(ipynb_data), as_version=4)
