"""Google Drive-based notebook content retrieval method."""

import pathlib

import nbformat

from ._name import get_notebook_raw_name

_CANDIDATE_DIRS = [
    pathlib.Path('/content/drive/MyDrive/Colab Notebooks'),
    pathlib.Path('/content/drive/MyDrive'),
]
_DRIVE_ROOT = pathlib.Path('/content/drive')


def _ensure_drive_mounted() -> None:
    """Mount Google Drive at /content/drive if it is not already mounted."""
    from google.colab import drive
    if not _DRIVE_ROOT.exists():
        print("   📂 Mounting Google Drive...")
        drive.mount('/content/drive', force_remount=False)


def _save_notebook() -> None:
    """Ask Colab to save the current notebook to Drive."""
    import google.colab
    print("   💾 Saving notebook to Drive...")
    google.colab._message.blocking_request('save_notebook', timeout_sec=30)


def _resolve_notebook_filename() -> str:
    """Return the notebook filename (stem + .ipynb) using the raw unsanitised name."""
    raw_name = get_notebook_raw_name()
    suffix = raw_name.suffix or '.ipynb'
    return raw_name.stem + suffix


def _find_notebook_on_drive(
    filename: str,
    candidate_dirs: list[pathlib.Path] = _CANDIDATE_DIRS,
    drive_root: pathlib.Path = _DRIVE_ROOT,
) -> pathlib.Path:
    """Locate a notebook file on Google Drive and return its path.

    Checks ``candidate_dirs`` first (fast path), then falls back to a recursive
    glob of ``drive_root``.

    Args:
        filename:       Exact filename to search for, e.g. ``"My Notebook.ipynb"``.
        candidate_dirs: Directories to check before doing a full search.
        drive_root:     Root of the Drive mount to use for the fallback glob.

    Returns:
        The single matching :class:`pathlib.Path`.

    Raises:
        FileNotFoundError: If no match is found, or if more than one match is
            found (ambiguous).
    """
    for directory in candidate_dirs:
        path = directory / filename
        if path.exists():
            return path

    print(f"   🔍 Searching Drive for '{filename}'...")
    matches = list(drive_root.glob(f'**/{filename}'))

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        paths_str = "\n    ".join(str(p) for p in matches)
        raise FileNotFoundError(
            f"Found {len(matches)} notebooks named '{filename}' on Drive — "
            f"cannot determine which one to use:\n    {paths_str}\n"
            f"Move the target notebook to 'MyDrive/Colab Notebooks/' or "
            f"'MyDrive/' to resolve the ambiguity."
        )

    raise FileNotFoundError(
        f"Could not find '{filename}' anywhere on Google Drive after saving.\n"
        f"Checked: {[str(d / filename) for d in candidate_dirs]}\n"
        f"Tip: if the notebook name contains characters that were stripped by "
        f"Colab, try renaming it to use only letters, numbers, spaces, and hyphens."
    )


def _read_notebook(path: pathlib.Path) -> nbformat.NotebookNode:
    """Read and return a notebook from ``path``."""
    print(f"   📖 Reading notebook from: {path}")
    with path.open('r', encoding='utf-8') as f:
        return nbformat.read(f, as_version=4)


def get_notebook_content_from_drive() -> nbformat.NotebookNode:
    """Retrieve notebook content from Google Drive.

    Saves the notebook to Drive first, then locates and reads it back.
    More reliable than in-memory retrieval for notebooks experiencing timeouts.

    Returns:
        nbformat.NotebookNode

    Raises:
        ImportError: If not running in Colab.
        FileNotFoundError: If the notebook cannot be found, or if multiple
            matches are found and the result would be ambiguous.
    """
    _ensure_drive_mounted()
    _save_notebook()
    filename = _resolve_notebook_filename()
    path = _find_notebook_on_drive(filename)
    return _read_notebook(path)

