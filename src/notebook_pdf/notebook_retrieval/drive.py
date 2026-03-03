"""Google Drive-based notebook content retrieval method."""

import pathlib

import nbformat

from ._name import get_notebook_raw_name


def get_notebook_content_from_drive():
    """Retrieve notebook content from Google Drive.

    This method saves the notebook to Drive first, then reads it back.
    It's more reliable for notebooks that are experiencing timeout issues.

    The notebook name is looked up without sanitisation so that filenames
    containing spaces or special characters are matched correctly.  If more
    than one file with the same stem is found across the Drive tree, a
    ``FileNotFoundError`` is raised listing the conflicting paths so you can
    resolve the ambiguity manually.

    Returns:
        nbformat.NotebookNode

    Raises:
        ImportError: If not running in Colab
        FileNotFoundError: If the notebook cannot be found, or if multiple
            matches are found and the result would be ambiguous.
    """
    import google.colab
    from google.colab import drive

    # Ensure Drive is mounted
    if not pathlib.Path('/content/drive').exists():
        print("   📂 Mounting Google Drive...")
        drive.mount('/content/drive', force_remount=False)

    # Save the notebook so Drive has the latest version
    print("   💾 Saving notebook to Drive...")
    google.colab._message.blocking_request('save_notebook', timeout_sec=30)

    # Use the raw (unsanitised) name so spaces / special chars are preserved
    raw_name = get_notebook_raw_name()
    stem = raw_name.stem          # name without .ipynb
    suffix = raw_name.suffix or '.ipynb'
    filename = stem + suffix

    # Check the most common locations first (fast path)
    candidate_dirs = [
        pathlib.Path('/content/drive/MyDrive/Colab Notebooks'),
        pathlib.Path('/content/drive/MyDrive'),
    ]
    for directory in candidate_dirs:
        path = directory / filename
        if path.exists():
            print(f"   📖 Reading notebook from: {path}")
            with path.open('r', encoding='utf-8') as f:
                return nbformat.read(f, as_version=4)

    # Fall back to a full Drive search, collecting *all* matches
    print(f"   🔍 Searching Drive for '{filename}'...")
    matches = list(pathlib.Path('/content/drive/').glob(f'**/{filename}'))

    if len(matches) == 1:
        path = matches[0]
        print(f"   📖 Reading notebook from: {path}")
        with path.open('r', encoding='utf-8') as f:
            return nbformat.read(f, as_version=4)

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
