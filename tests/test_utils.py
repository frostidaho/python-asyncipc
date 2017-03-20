import pytest
from asyncipc import _utils as utils

def test_runtime_dir(monkeypatch):
    import os
    monkeypatch.setattr(os, 'getenv', lambda x: '/a/b/c')
    assert utils._runtime_dir() == '/a/b/c'
    monkeypatch.setattr(os, 'getenv', lambda x: '')
    assert utils._runtime_dir() == '/run/user/{}'.format(os.getuid())

