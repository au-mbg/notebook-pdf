"""Tests for notebook_pdf._env."""

import sys

import pytest


def test_is_colab_true(monkeypatch):
    """is_colab() returns True when google.colab is importable."""
    import types
    fake_colab = types.ModuleType("google.colab")
    fake_google = types.ModuleType("google")
    fake_google.colab = fake_colab
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.colab", fake_colab)

    # Re-import after patching
    from notebook_pdf._env import is_colab
    assert is_colab() is True


def test_is_colab_false(monkeypatch):
    """is_colab() returns False when google.colab is not importable."""
    monkeypatch.setitem(sys.modules, "google.colab", None)

    from notebook_pdf._env import is_colab
    assert is_colab() is False


def test_is_ipython_true(monkeypatch):
    """is_ipython() returns True when IPython.get_ipython() is not None."""
    import unittest.mock as mock
    import IPython
    monkeypatch.setattr(IPython, "get_ipython", lambda: mock.MagicMock())

    from notebook_pdf._env import is_ipython
    assert is_ipython() is True


def test_is_ipython_false(monkeypatch):
    """is_ipython() returns False when IPython.get_ipython() returns None."""
    import IPython
    monkeypatch.setattr(IPython, "get_ipython", lambda: None)

    from notebook_pdf._env import is_ipython
    assert is_ipython() is False
