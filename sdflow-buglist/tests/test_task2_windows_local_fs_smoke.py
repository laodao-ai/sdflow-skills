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


# ── repo_root 的 Windows 泳道覆盖（change harden-repo-root-fail-closed · tasks 4.6 / CF-6） ──
#
# 为什么这些用例落在**本文件**而不是 test_repo_root_identity_buglist.py：
# `windows-recorder-smoke.yml` 只跑本文件，主矩阵 `mechanical-gates.yml` 只有 ubuntu/macos
# ⇒ repo_root 的六步判据（isabs 对 "C:\\…" / normcase 对盘符与大小写 / commonpath 跨盘符 /
# realpath 对 SUBST）此前**从未在 Windows 上真跑过**。本文件此前的两个用例直传 tmp_path 给
# recorder_lock，绕开 repo_root。

_GIT_DISCOVERY_ENV = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_CEILING_DIRECTORIES",
    "GIT_INDEX_FILE", "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_CONFIG_COUNT", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM",
)


@pytest.fixture
def _clean_git_env(monkeypatch):
    """清空仓库/工作树发现类变量，确保断言的是 repo_root 自身的判据而非宿主残留。"""
    for name in _GIT_DISCOVERY_ENV:
        monkeypatch.delenv(name, raising=False)
    for name in list(os.environ):
        if name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            monkeypatch.delenv(name, raising=False)


def _repo_root_fn():
    return _load("buglist_win_repo_root", "sdflow-buglist/scripts/buglist.py").repo_root


def _git(*args, cwd):
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True,
    )


def _init_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    _git("init", "-q", cwd=path)
    return path


def test_windows_repo_root_positive_regression(tmp_path, _clean_git_env):
    """正向回归：真实 git 仓库下 repo_root 不抛异常，且仓根/子目录起点都解析到同一个根。

    这条同时是 design Open Questions 前两问的实测答案——`os.path.isabs("C:\\…")` 与
    `normcase` + `commonpath` 在盘符与大小写下的行为，全部经由真实调用而非推理确认。
    """
    assert sys.platform == "win32"
    repo_root = _repo_root_fn()
    repo = _init_repo(tmp_path / "repo")
    sub = repo / "pkg" / "mod"
    sub.mkdir(parents=True)

    expected = os.path.realpath(str(repo))
    assert repo_root(str(repo)) == expected
    assert repo_root(str(sub)) == expected, "子目录起点 MUST 解析到同一个仓根"

    # 大小写不敏感的盘符路径同样必须过（normcase 的实测锚，非推理）。
    swapped = str(repo)
    swapped = swapped[0].swapcase() + swapped[1:]
    assert repo_root(swapped) == expected


def test_windows_repo_root_rejects_nonexistent_start(tmp_path, _clean_git_env):
    """负例①：起点不是既存目录 ⇒ 在调 git 之前受控 ValueError，且该路径 MUST NOT 被创建。"""
    assert sys.platform == "win32"
    repo_root = _repo_root_fn()
    missing = tmp_path / "no-such-start"

    with pytest.raises(ValueError) as exc:
        repo_root(str(missing))

    message = str(exc.value)
    assert "仓根探测起点不是既存目录" in message
    assert message.startswith("ERROR: ") and "; cause: " in message and "; fix: " in message
    assert not missing.exists(), "被拒起点 MUST NOT 在校验过程中被具现"


def test_windows_repo_root_rejects_core_worktree_redirect(tmp_path, _clean_git_env):
    """负例②（主防线）：`core.worktree` on-disk 重定向到起点之外 ⇒ 祖先校验拦下。

    这条在 Windows 上真跑 `realpath` + `normcase` + `commonpath` 三件组合——同盘符路径，
    故走的是 commonpath 的正常返回路径（跨盘符降级另见下一条 CF-6 用例）。
    """
    assert sys.platform == "win32"
    repo_root = _repo_root_fn()
    repo = _init_repo(tmp_path / "repo")
    outside = tmp_path / "outside"
    outside.mkdir()
    _git("config", "core.worktree", str(outside), cwd=repo)

    # 前提核验：不假设，真跑一遍确认 git 确实 rc=0 且返回那个仓外目录。
    probe = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(repo), capture_output=True, text=True,
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    )
    assert probe.returncode == 0, f"前提不成立: {probe.stderr}"
    assert Path(probe.stdout.strip()).resolve() == outside.resolve(), (
        f"前提不成立：core.worktree 未重定向 toplevel，实得 {probe.stdout!r}"
    )

    with pytest.raises(ValueError) as exc:
        repo_root(str(repo))

    assert "不包含探测起点" in str(exc.value)
    assert list(outside.iterdir()) == [], "仓外目录 MUST NOT 出现任何产物"
    assert not (outside / "openspec").exists()


def test_windows_commonpath_cross_drive_raises_without_recorder_format():
    """CF-6（判据层，无条件运行）：跨盘符时 `os.path.commonpath` **自行**抛 ValueError。

    后果：repo_root 步骤⑤在跨盘符输入下抛的是 **stdlib 的** ValueError ⇒ 行为仍 fail-closed
    （`main()` 的 `except ValueError` 照样接住 → exit 2、无 traceback），但消息**不带** recorder
    的 `ERROR: …; cause: …; fix: …` 三段式 ⇒ **可观测性降级**。本用例把这一事实钉成机械锚，
    将来若换 `PurePath.is_relative_to`（跨盘符返回 False 而非抛异常）会当场变红、逼走设计门。
    """
    assert sys.platform == "win32"
    with pytest.raises(ValueError) as exc:
        os.path.commonpath([os.path.normcase(r"C:\alpha"), os.path.normcase(r"D:\beta")])
    message = str(exc.value)
    assert not message.startswith("ERROR: "), "若 stdlib 消息形态变了，须重新评估降级结论"
    assert "cause:" not in message and "fix:" not in message


def _second_drive_probe():
    """返回一个位于**非 tmp 盘符**的可写探针目录；找不到返回 None（用例据此诚实 skip）。"""
    primary = os.path.splitdrive(os.path.abspath(os.sep))[0].upper()
    for letter in "DEFGHIJ":
        drive = f"{letter}:"
        if drive == primary or not os.path.isdir(drive + os.sep):
            continue
        probe = Path(drive + os.sep) / f"sdflow-cf6-{os.getpid()}"
        try:
            probe.mkdir()
        except OSError:
            continue
        return probe
    return None


def test_windows_repo_root_cross_drive_redirect_is_fail_closed(tmp_path, _clean_git_env):
    """CF-6（端到端）：core.worktree 指向**另一个盘符** ⇒ 仍 fail-closed，但消息降级。

    需要 runner 上真有第二个可写盘符；没有就诚实 skip —— 上一条判据层用例无条件覆盖同一事实。
    """
    assert sys.platform == "win32"
    probe = _second_drive_probe()
    if probe is None:
        pytest.skip("runner 上没有第二个可写盘符，跨盘符端到端路径无法构造")
    try:
        repo_root = _repo_root_fn()
        repo = _init_repo(tmp_path / "repo")
        assert os.path.splitdrive(str(repo))[0].upper() != os.path.splitdrive(str(probe))[0].upper()
        _git("config", "core.worktree", str(probe), cwd=repo)

        with pytest.raises(ValueError):
            repo_root(str(repo))

        assert list(probe.iterdir()) == [], "跨盘符重定向目标 MUST NOT 出现任何产物"
    finally:
        shutil.rmtree(probe, ignore_errors=True)
