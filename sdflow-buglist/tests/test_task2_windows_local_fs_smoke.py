"""Task 5 / tasks.md 7.4 Windows local-disk smoke runner contract.

Run on an actual Windows runner whose pytest tmp path is a local drive:

    py -m pytest -q sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error

Non-Windows hosts skip this module and MUST NOT cite the skip as Windows evidence.
The test deliberately fails when the runner provides a UNC/network temp path.
"""

import importlib.util
import os
from pathlib import Path
import subprocess
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

    with recorder.recorder_lock(tmp_path, "reindex") as owner:
        assert lock_path.exists()
        participant_env = recorder.recorder_child_env("scan", owner.token)
        monkeypatch.setattr(os, "environ", participant_env)
        participant = recorder.validate_recorder_participant(tmp_path, owner.token, "scan")
        assert participant.participant and participant.token == owner.token
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


def test_windows_setup_uses_owned_copies_and_refreshes_them(tmp_path):
    assert sys.platform == "win32"
    home = tmp_path / "home"
    home.mkdir()
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), SDFLOW_HOME=str(home / ".sdflow"))

    for _ in range(2):
        result = subprocess.run(
            ["bash", str(ROOT / "setup.sh")], env=env, text=True, capture_output=True, timeout=120
        )
        assert result.returncode == 0, result.stderr
        assert "mode: copy (Windows)" in result.stdout

    for host in (".claude", ".codex"):
        installed = home / host / "skills" / "sdflow-buglist"
        assert installed.is_dir() and not installed.is_symlink()
        assert (installed / ".sdflow-skills").is_file()
        assert (installed / "scripts/buglist.py").read_bytes() == (
            ROOT / "sdflow-buglist/scripts/buglist.py"
        ).read_bytes()
