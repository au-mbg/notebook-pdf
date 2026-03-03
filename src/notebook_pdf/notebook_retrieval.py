"""Functions for retrieving notebook content from Colab."""

import json
import os
import pathlib
import queue
import threading
import urllib

import nbformat
import requests


class GetIpynbTimeoutError(TimeoutError):
    """Raised when notebook retrieval times out."""
    pass


def get_notebook_name():
    import werkzeug.utils

    """Retrieve the current notebook name from Colab."""
    response = requests.get(
        f"http://{os.environ['COLAB_JUPYTER_IP']}:{os.environ['KMP_TARGET_PORT']}/api/sessions"
    )
    notebook_name = response.json()[0]["name"]
    return pathlib.Path(werkzeug.utils.secure_filename(urllib.parse.unquote(notebook_name)))


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


def get_notebook_content_from_drive():
    """Retrieve notebook content from Google Drive.
    
    This method saves the notebook to Drive first, then reads it back.
    It's more reliable for notebooks that are experiencing timeout issues.
    
    Returns:
        nbformat.NotebookNode
        
    Raises:
        ImportError: If not running in Colab
        FileNotFoundError: If notebook cannot be found after saving
    """
    import google.colab
    from google.colab import drive
    
    # Ensure Drive is mounted
    if not pathlib.Path('/content/drive').exists():
        print("   📂 Mounting Google Drive...")
        drive.mount('/content/drive', force_remount=False)
    
    # Save the notebook
    print("   💾 Saving notebook to Drive...")
    google.colab._message.blocking_request('save_notebook', timeout_sec=30)
    
    # Get notebook name and try common Drive locations
    notebook_name = get_notebook_name()
    
    possible_paths = [
        pathlib.Path(f'/content/drive/MyDrive/Colab Notebooks/{notebook_name}'),
        pathlib.Path(f'/content/drive/MyDrive/Colab Notebooks/{notebook_name}.ipynb'),
        pathlib.Path(f'/content/drive/MyDrive/{notebook_name}'),
        pathlib.Path(f'/content/drive/MyDrive/{notebook_name}.ipynb'),
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"   📖 Reading notebook from: {path}")
            with path.open('r', encoding='utf-8') as f:
                return nbformat.read(f, as_version=4)
    
    notebook_name = str(notebook_name).replace('.ipynb', '')
    paths = pathlib.Path('/content/drive/').glob(f'**/{notebook_name}')
    for path in paths:
      print(f"   📖 Reading notebook from: {path}")
      with path.open('r', encoding='utf-8') as f:
          return nbformat.read(f, as_version=4)
    
    raise FileNotFoundError(
        f"Could not find notebook '{notebook_name}' in Google Drive after saving. "
        f"Tried: {[str(p) for p in possible_paths]}"
    )


def get_notebook_content(method='timeout', **kwargs):
    """Retrieve notebook content using the specified method.
    
    Args:
        method: One of 'timeout', 'blocking', or 'drive'
        **kwargs: Additional arguments passed to the specific retrieval method
        
    Returns:
        nbformat.NotebookNode
        
    Raises:
        ValueError: If method is not recognized
        Various exceptions depending on the method used
    """
    if method == 'timeout':
        return get_notebook_content_with_timeout(**kwargs)
    elif method == 'blocking':
        return get_notebook_content_blocking(**kwargs)
    elif method == 'drive':
        return get_notebook_content_from_drive(**kwargs)
    else:
        raise ValueError(
            f"Unknown method '{method}'. "
            f"Choose from: 'timeout', 'blocking', or 'drive'"
        )
