"""Tests for notebook_pdf.notebook_retrieval._name.get_notebook_name_local."""

import json
import os
import pathlib
import unittest.mock as mock

import pytest


def test_vscode_strategy(monkeypatch, tmp_path):
    """VS Code __vsc_ipynb_file__ variable is used when present."""
    nb_path = tmp_path / "my_notebook.ipynb"
    nb_path.touch()

    fake_ipython = mock.Mock()
    fake_ipython.user_ns = {"__vsc_ipynb_file__": str(nb_path)}

    import IPython
    monkeypatch.setattr(IPython, "get_ipython", lambda: fake_ipython)

    from notebook_pdf.notebook_retrieval._name import get_notebook_name_local
    result = get_notebook_name_local()
    assert result == nb_path.resolve()


def test_env_var_strategy(monkeypatch, tmp_path):
    """JPY_SESSION_NAME environment variable is used when VS Code var absent."""
    nb_path = tmp_path / "session_notebook.ipynb"
    nb_path.touch()

    import IPython
    monkeypatch.setattr(IPython, "get_ipython", lambda: None)
    monkeypatch.setenv("JPY_SESSION_NAME", str(nb_path))

    from notebook_pdf.notebook_retrieval._name import get_notebook_name_local
    result = get_notebook_name_local()
    assert result == nb_path.resolve()


def test_server_file_strategy(monkeypatch, tmp_path, server_runtime_dir):
    """Server info files in the runtime dir are parsed to find the notebook."""
    kernel_id = "abc-123"
    nb_relative = "notebooks/my_notebook.ipynb"

    # Patch IPython so strategy 1 is skipped
    import IPython
    monkeypatch.setattr(IPython, "get_ipython", lambda: None)
    # Ensure env var strategy is skipped
    monkeypatch.delenv("JPY_SESSION_NAME", raising=False)

    # Patch ipykernel and jupyter_core
    fake_cf = tmp_path / f"kernel-{kernel_id}.json"
    fake_cf.touch()

    import ipykernel
    monkeypatch.setattr(ipykernel, "get_connection_file", lambda: str(fake_cf))

    import notebook_pdf.notebook_retrieval._name as name_mod
    monkeypatch.setattr(
        name_mod,
        "pathlib",
        pathlib,  # keep real pathlib
    )

    # Patch jupyter_core.paths to return our fake runtime dir
    import jupyter_core.paths
    monkeypatch.setattr(jupyter_core.paths, "jupyter_runtime_dir", lambda: str(server_runtime_dir))

    # Patch requests.get to return a fake sessions response
    sessions_payload = [
        {"kernel": {"id": kernel_id}, "notebook": {"path": nb_relative}}
    ]
    fake_resp = mock.Mock()
    fake_resp.json.return_value = sessions_payload
    import requests
    monkeypatch.setattr(requests, "get", lambda *a, **kw: fake_resp)

    from notebook_pdf.notebook_retrieval import _name
    import importlib
    importlib.reload(_name)
    result = _name.get_notebook_name_local()
    expected = (tmp_path / nb_relative).resolve()
    assert result == expected


def test_all_strategies_fail_raises(monkeypatch):
    """RuntimeError raised with helpful message when all strategies fail."""
    import IPython
    monkeypatch.setattr(IPython, "get_ipython", lambda: None)
    monkeypatch.delenv("JPY_SESSION_NAME", raising=False)

    # Make ipykernel raise so strategy 3 is also skipped
    import sys
    monkeypatch.setitem(sys.modules, "ipykernel", None)

    from notebook_pdf.notebook_retrieval._name import get_notebook_name_local
    with pytest.raises(RuntimeError, match="Pass the path explicitly"):
        get_notebook_name_local()
