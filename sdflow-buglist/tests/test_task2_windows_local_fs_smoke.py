"""Task 5 / tasks.md 7.4 Windows local-disk smoke runner contract.

Run on an actual Windows runner whose pytest tmp path is a local drive:

    py -m pytest -q sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error

Non-Windows hosts skip this module and MUST NOT cite the skip as Windows evidence.
The test deliberately fails when the runner provides a UNC/network temp path.
"""

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="requires actual Windows local disk")
ROOT = Path(__file__).parents[2]


def _git_bash():
    """定位 Git for Windows 的 bash，跳过 WSL 的 System32\\bash.exe。

    GitHub windows-latest 上裸 "bash" 会解析到 C:\\Windows\\System32\\bash.exe
    （WSL 启动器，未装 distro），无法执行 setup.sh，只会打印 "no installed
    distributions ... <Distro>' to install." 后 exit 1。优先从 git 可执行文件所在的
    Git 安装树推导 git-bash，再退到已知安装路径。找不到即显式报错，不静默回落 WSL。
    """
    git = shutil.which("git")
    if git:
        git_root = Path(git).resolve().parent.parent  # ...\Git\cmd\git.exe -> ...\Git
        for rel in ("bin/bash.exe", "usr/bin/bash.exe"):
            candidate = git_root / rel
            if candidate.is_file():
                return str(candidate)
    for candidate in (
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
    ):
        if os.path.isfile(candidate):
            return candidate
    raise RuntimeError(
        "git-bash 未找到；System32 的 WSL bash 无法执行 setup.sh。请安装 Git for Windows。"
    )


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
        previous_token = recorder._ACTIVE_RECORDER_TOKEN
        previous_chain = recorder._ACTIVE_RECORDER_CHAIN
        try:
            recorder._ACTIVE_RECORDER_TOKEN = owner.token
            recorder._ACTIVE_RECORDER_CHAIN = owner.chain
            participant_env = recorder.recorder_child_env("scan", owner.token)
        finally:
            recorder._ACTIVE_RECORDER_TOKEN = previous_token
            recorder._ACTIVE_RECORDER_CHAIN = previous_chain
        with monkeypatch.context() as participant_patch:
            participant_patch.setattr(os, "environ", participant_env)
            participant = recorder.validate_recorder_participant(tmp_path, owner.token, "scan")
        assert participant.participant and participant.token == owner.token
        assert participant.chain == ("reindex", "scan")
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
        # setup.sh 输出含 UTF-8 非 ASCII（⚠/✓/→/中文）；Windows subprocess text 模式默认走
        # locale 编码（cp1252）会在读管道线程里解码崩 → stdout=None。显式 utf-8 + replace 兜底。
        result = subprocess.run(
            [_git_bash(), str(ROOT / "setup.sh")], env=env,
            text=True, encoding="utf-8", errors="replace",
            capture_output=True, timeout=120,
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
