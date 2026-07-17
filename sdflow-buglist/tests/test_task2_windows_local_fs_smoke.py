"""Task 5 / tasks.md 7.4 Windows local-disk smoke runner contract.

Run on an actual Windows runner whose pytest tmp path is a local drive:

    py -m pytest -q sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error

Non-Windows hosts skip this module and MUST NOT cite the skip as Windows evidence.
The test deliberately fails when the runner provides a UNC/network temp path.
"""

import importlib.util
import os
from pathlib import Path
import sys

import pytest


pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="requires actual Windows local disk")
ROOT = Path(__file__).parents[2]


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_windows_local_disk_acquire_conflict_replace_cleanup(tmp_path, monkeypatch):
    assert sys.platform == "win32"
    assert not str(tmp_path).startswith("\\\\"), "runner temp path must be a local Windows drive"
    recorder = _load("windows_recorder", "sdflow-buglist/scripts/buglist.py")
    init = _load("windows_init", "sdflow-init/scripts/init.py")
    lock_path = tmp_path / "openspec/issues/.recorder.lock"

    with recorder.recorder_lock(tmp_path, "scan"):
        assert lock_path.exists()
        with pytest.raises(recorder.RecorderLockError, match="lock occupied"):
            with recorder.recorder_lock(tmp_path, "add"):
                pass
    assert not lock_path.exists()

    target = tmp_path / ".gitignore"
    original = b"user\r\n"
    target.write_bytes(original)
    init.merge_runtime_gitignore(tmp_path, b"/openspec/issues/.recorder.lock\n")
    assert target.read_bytes() == original + b"/openspec/issues/.recorder.lock\n"

    stable = target.read_bytes()
    monkeypatch.setattr(init.os, "replace", lambda *_args: (_ for _ in ()).throw(PermissionError("sharing violation")))
    with pytest.raises(PermissionError, match="sharing violation"):
        init.merge_runtime_gitignore(tmp_path, b"/another-runtime-entry\n")
    assert target.read_bytes() == stable
    assert not list(tmp_path.glob("*.tmp"))
