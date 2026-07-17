import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("relative", [
    "sdflow-buglist/scripts/buglist.py",
    "sdflow-todolist/scripts/todolist.py",
    "sdflow-issues/scripts/issues.py",
])
def test_canonical_id_rejects_alias_and_unicode_digits(relative):
    module = load(relative.replace("/", "_"), relative)
    assert module.canonical_id("A7") == "A7"
    for invalid in ("A007", "A1٢", "A1２", "AA7", "a7"):
        with pytest.raises(ValueError, match="canonical ASCII"):
            module.canonical_id(invalid)


def test_repository_lock_is_exclusive_and_token_safe(tmp_path):
    module = load("bug_lock", "sdflow-buglist/scripts/buglist.py")
    root = tmp_path
    (root / "openspec/issues").mkdir(parents=True)
    with module.recorder_lock(root, "scan") as owner:
        with pytest.raises(module.RecorderLockError, match="lock occupied"):
            with module.recorder_lock(root, "add"):
                pass
        participant = module.validate_recorder_participant(root, owner.token, "scan")
        assert participant.token == owner.token
        with pytest.raises(module.RecorderLockError):
            module.validate_recorder_participant(root, "forged", "scan")
        with pytest.raises(module.RecorderLockError, match="not allowlisted"):
            module.validate_recorder_participant(root, owner.token, "shell")
        other = tmp_path / "other"
        (other / "openspec/issues").mkdir(parents=True)
        with pytest.raises(module.RecorderLockError, match="cross-repo"):
            module.validate_recorder_participant(other, owner.token, "scan")
        assert module.RECORDER_LOCK_ENV in module.recorder_child_env("scan", owner.token)
        assert module.RECORDER_LOCK_ENV not in module.recorder_child_env("git", token=False)
    assert not (root / "openspec/issues/.recorder.lock").exists()


def test_twenty_process_adds_are_unique_or_fail_loud(tmp_path):
    script = ROOT / "sdflow-buglist/scripts/buglist.py"
    payload = tmp_path / "bug.json"
    payload.write_text(json.dumps({
        "module": "lock", "summary": "race", "priority": "P2", "phenomenon": "race",
    }))
    command = [sys.executable, str(script), "--root", str(tmp_path), "add", "--json", str(payload), "--prefix", "A"]
    processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(20)]
    results = [process.communicate(timeout=20) + (process.returncode,) for process in processes]
    successful = [json.loads(stdout)["id"] for stdout, _stderr, code in results if code == 0]
    failures = [stderr for _stdout, stderr, code in results if code != 0]
    assert successful
    assert len(successful) == len(set(successful))
    assert all("recorder lock occupied" in stderr for stderr in failures)
    assert not (tmp_path / "openspec/issues/.recorder.lock").exists()


def test_partial_lock_and_ownership_lost_are_fail_closed(tmp_path):
    module = load("bug_lock_faults", "sdflow-buglist/scripts/buglist.py")
    lock = tmp_path / "openspec/issues/.recorder.lock"
    lock.parent.mkdir(parents=True)
    lock.write_bytes(b"")
    with pytest.raises(module.RecorderLockError, match="metadata unavailable"):
        with module.recorder_lock(tmp_path, "scan"):
            pass
    lock.unlink()
    replacement = {"repo": os.path.realpath(tmp_path), "pid": 999, "command": "add", "started": 0, "token": "replacement"}
    with pytest.raises(module.RecorderLockError, match="ownership lost"):
        with module.recorder_lock(tmp_path, "scan"):
            lock.unlink()
            lock.write_text(json.dumps(replacement))
    assert json.loads(lock.read_text())["token"] == "replacement"


def test_custom_prefix_is_repository_wide_across_pools(tmp_path):
    bug_script = ROOT / "sdflow-buglist/scripts/buglist.py"
    todo_script = ROOT / "sdflow-todolist/scripts/todolist.py"
    bug = tmp_path / "bug.json"
    todo = tmp_path / "todo.json"
    bug.write_text(json.dumps({"id": "A1", "module": "m", "summary": "bug", "priority": "P2", "phenomenon": "x"}))
    todo.write_text(json.dumps({"id": "A1", "module": "m", "summary": "todo", "type": "代码质量"}))
    first = subprocess.run([sys.executable, bug_script, "--root", tmp_path, "add", "--json", bug], capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    second = subprocess.run([sys.executable, todo_script, "--root", tmp_path, "add", "--json", todo], capture_output=True, text=True)
    assert second.returncode != 0
    assert "仓级既有 semantic ID 重复" in second.stderr
