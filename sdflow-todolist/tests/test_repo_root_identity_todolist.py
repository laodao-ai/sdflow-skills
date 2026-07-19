"""repo_root 六步身份校验（change harden-repo-root-fail-closed · Task 2）。

被测契约：`repo_root(start=None|str) -> str`，在把任何值当作可写仓根返回之前，必须证明
它是**起点所属仓库的根**；任一判据不满足即 `raise ValueError`。唯一的回落分支是
「git 抛 OSError 或以非 0 退出」（非 git 仓库 / bare repo / `.git/` 目录内等正常场景）。

本文件与 sdflow-issues/tests · sdflow-buglist/tests 下的同名文件逐条对应（三份 recorder 各自内联一份 `repo_root`，
D4 红线禁止互相 import，故测试也各自一份）。

方法论约束（design ADR-2 / Risks）：负例 **MUST NOT** mock `os.path.isabs` /
`isdir` / `realpath` —— mock 掉判据本身等于没测。除「git 输出内容」与「git 挂死」这两个
外部依赖行为外，一切都用 `tmp_path` 下真实存在/不存在的路径构造。

Run with: python3 -m pytest sdflow-todolist/tests/test_repo_root_identity_todolist.py -v
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import todolist as rec_mod
from todolist import repo_root

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "todolist.py")

# 仓库/工作树发现类变量——测试前一律清空，确保用例断言的是 repo_root 自身的判据，
# 而不是宿主环境残留（CI 的 git hook 场景会真的导出它们）。
GIT_DISCOVERY_ENV = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_CEILING_DIRECTORIES",
    "GIT_INDEX_FILE", "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_CONFIG_COUNT", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM",
)


@pytest.fixture(autouse=True)
def _clean_git_env(monkeypatch):
    for name in GIT_DISCOVERY_ENV:
        monkeypatch.delenv(name, raising=False)
    for name in list(os.environ):
        if name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            monkeypatch.delenv(name, raising=False)


def _git(*args, cwd):
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True,
    )


def _init_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    _git("init", "-q", cwd=path)
    _git("config", "user.email", "t@example.com", cwd=path)
    _git("config", "user.name", "t", cwd=path)
    return path


def _commit_empty(path):
    _git("commit", "-q", "--allow-empty", "-m", "init", cwd=path)


def _fake_git_stdout(monkeypatch, stdout):
    """把 git 的 **stdout 内容**换掉（rc=0），其余一切判据仍走真实文件系统。

    只替换外部依赖的输出，不碰 `os.path.*` 判据——后者正是被测对象。
    """
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout, "")

    monkeypatch.setattr(rec_mod.subprocess, "run", fake_run)
    return calls


def _forbid_subprocess(monkeypatch):
    """任何子进程调用都判定为失败——用于证明「起点校验发生在调 git 之前」。"""

    def boom(cmd, **kwargs):
        raise AssertionError(f"git 不该被调用，但收到了: {cmd!r}")

    monkeypatch.setattr(rec_mod.subprocess, "run", boom)


def _entries(path):
    return sorted(p.name for p in Path(path).iterdir())


# ── ① 起点可信性（调 git 之前） ──────────────────────────────────────────────

def test_missing_start_directory_is_rejected_before_calling_git(tmp_path, monkeypatch):
    _forbid_subprocess(monkeypatch)
    missing = tmp_path / "no-such-dir"

    with pytest.raises(ValueError) as exc:
        repo_root(str(missing))

    assert "起点不是既存目录" in str(exc.value)
    assert str(exc.value).startswith("ERROR: ")
    assert not missing.exists(), "被拒的起点路径 MUST NOT 被创建"
    assert _entries(tmp_path) == []


def test_file_as_start_is_rejected_before_calling_git(tmp_path, monkeypatch):
    _forbid_subprocess(monkeypatch)
    target = tmp_path / "a-file.txt"
    target.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError):
        repo_root(str(target))

    assert target.is_file(), "普通文件不该被改成目录"
    assert _entries(tmp_path) == ["a-file.txt"]


def test_empty_string_start_is_rejected_before_calling_git(monkeypatch):
    _forbid_subprocess(monkeypatch)
    with pytest.raises(ValueError):
        repo_root("")


def test_deleted_process_cwd_yields_controlled_failure(tmp_path):
    """进程 cwd 在运行期被删除（ADR-7）。

    实测依据：此时 `os.path.isdir(".")` 仍返回 `True`，而 `os.getcwd()` 抛
    `FileNotFoundError` —— 所以起点 MUST 走 `os.getcwd()`。本用例在子进程里做
    （删除自身 cwd 会污染 pytest 进程），断言拿到受控 `ValueError` 而非裸 traceback。
    """
    doomed = tmp_path / "doomed"
    doomed.mkdir()
    program = (
        "import os, sys\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "from todolist import repo_root\n"
        "os.chdir(sys.argv[2])\n"
        "os.rmdir(sys.argv[2])\n"
        "assert os.path.isdir('.') is True, 'premise: isdir(\\'.\\') 仍为 True'\n"
        "try:\n"
        "    repo_root()\n"
        "except ValueError as exc:\n"
        "    print('CONTROLLED:' + str(exc))\n"
        "    sys.exit(0)\n"
        "sys.exit('repo_root 未受控失败')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", program,
         str(Path(SCRIPT).parent), str(doomed)],
        capture_output=True, text=True, cwd=str(tmp_path),
    )

    assert proc.returncode == 0, proc.stderr
    assert "CONTROLLED:ERROR: 无法确定仓根探测起点" in proc.stdout
    assert "Traceback" not in proc.stderr


# ── ③ 形状校验 ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad", [
    "",
    "   ",
    "\n",
    "relative/path",
    "./relative",
    "/definitely/not/here/at/all",
])
def test_shape_negatives_are_rejected(tmp_path, monkeypatch, bad):
    repo = _init_repo(tmp_path / "repo")
    _fake_git_stdout(monkeypatch, bad)

    with pytest.raises(ValueError) as exc:
        repo_root(str(repo))

    assert "仓根不可用" in str(exc.value)
    assert not (tmp_path / "relative").exists()
    assert not (repo / "relative").exists()
    assert _entries(repo) == [".git"]


def test_multiline_stdout_is_rejected(tmp_path, monkeypatch):
    """`git rev-parse` 对未知选项不报错、原样回显再继续（rc=0）⇒ stdout 变多行、
    首行是垃圾。整段多行文本不是既存目录，形状校验拦下。"""
    repo = _init_repo(tmp_path / "repo")
    _fake_git_stdout(monkeypatch, f"--bogus-option\n{repo}\n")

    with pytest.raises(ValueError) as exc:
        repo_root(str(repo))

    assert "仓根不可用" in str(exc.value)


def test_trailing_space_is_preserved_not_stripped(tmp_path, monkeypatch):
    """`rstrip("\\r\\n")` 只剥行结束符：末尾的合法空格 MUST 保留。

    若改用 `strip()`，`"<repo> "` 会被截短成一个**真实存在**的目录而静默放行——
    本用例正是那条判据的守卫：被拒值里必须还带着那个空格。
    """
    repo = _init_repo(tmp_path / "repo")
    _fake_git_stdout(monkeypatch, str(repo) + " \n")

    with pytest.raises(ValueError) as exc:
        repo_root(str(repo))

    assert "仓根不可用" in str(exc.value)
    assert repr(str(repo) + " ")[1:-1] in str(exc.value), "被拒值应原样保留末尾空格"


def test_rejected_value_is_ascii_escaped(tmp_path, monkeypatch):
    """诊断里的被拒值用 `ascii(value)[:N]` 生成：多字节不卡边界、控制字符不伪造多行。"""
    repo = _init_repo(tmp_path / "repo")
    _fake_git_stdout(monkeypatch, "a" * 78 + "雪茄\tX")

    with pytest.raises(ValueError) as exc:
        repo_root(str(repo))

    message = str(exc.value)
    # 被拒值段落 MUST 是 ascii() 的产物：原始的多字节字符与制表符都不得原样出现，
    # 否则说明走的是字节截断（会在多字节边界抛 UnicodeDecodeError，fail-closed 自身先崩）。
    assert "雪茄" not in message, "被拒值 MUST 经 ascii() 转义，不得原样嵌入多字节字符"
    assert "\t" not in message, "控制字符 MUST 被转义，不得原样嵌入"
    assert "\\u96ea" in message or "\\x" in message, f"被拒值应为 ascii() 转义形式: {message}"
    assert message.count("\n") == 0, "诊断 MUST 是单行，控制字符不得伪造多行日志"


def test_bad_relative_value_rejected_regardless_of_cwd(tmp_path, monkeypatch):
    """「坏值恰好命中 cwd 下的既存目录」—— `isabs` 拦下，且**与 cwd 无关**。

    双态对照跑（tasks 1.3b）：在「坏值能被 cwd 解析成真实目录」的 cwd 与「解析不到」的
    cwd 各跑一次，断言两次结果一致。单态跑无法证伪「结论其实依赖 cwd」。
    """
    repo = _init_repo(tmp_path / "repo")
    (repo / "lure").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    results = {}
    for label, cwd in (("cwd 内有同名目录", repo), ("cwd 内无同名目录", outside)):
        monkeypatch.chdir(cwd)
        assert (Path(cwd) / "lure").is_dir() == (label == "cwd 内有同名目录")
        _fake_git_stdout(monkeypatch, "lure")
        with pytest.raises(ValueError) as exc:
            repo_root(str(repo))
        results[label] = "仓根不可用" in str(exc.value)

    assert results == {"cwd 内有同名目录": True, "cwd 内无同名目录": True}
    assert _entries(outside) == [], "被拒值 MUST NOT 在任何 cwd 下具现出目录"


# ── ④ 祖先校验（主防线） ────────────────────────────────────────────────────

def test_core_worktree_redirect_is_rejected(tmp_path):
    """主防线用例（ADR-2）：`core.worktree` 是写在 `.git/config` 里的 **on-disk**
    重定向，环境净化对它零效果、形状校验会放行——**祖先校验是唯一防线**。

    删掉祖先校验，本用例必须变红（变异确认见 impl-report）。
    """
    repo = _init_repo(tmp_path / "repo")
    outside = tmp_path / "outside"
    outside.mkdir()
    _git("config", "core.worktree", str(outside), cwd=repo)

    # 前提核验：不假设，真跑一遍确认 git 确实 rc=0 返回那个仓外目录。
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
    assert _entries(outside) == [], "仓外目录 MUST NOT 出现任何 openspec/ 产物"
    assert not (outside / "openspec").exists()


def test_git_dir_and_work_tree_env_are_sanitized(tmp_path, monkeypatch):
    """第一层防御：环境净化后 git 忽略 GIT_DIR/GIT_WORK_TREE，返回真实仓根。"""
    repo = _init_repo(tmp_path / "repo")
    other = _init_repo(tmp_path / "other")
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))

    assert repo_root(str(repo)) == os.path.realpath(str(repo))


def test_ancestor_check_independently_catches_unsanitized_env(tmp_path, monkeypatch):
    """第二层防御独立有效：即便环境净化被绕过（将来新增未被剔除的等价变量），
    祖先校验仍拦得住。

    做法：先用**未净化**的环境真跑一次 git，拿到它会返回的 top（= 另一个仓）；
    再把该值当作 git 的输出喂给 `repo_root`，断言祖先校验把它拒了。
    这样两层防御各自被独立证明，而不是靠「另一层反正会兜住」。
    """
    repo = _init_repo(tmp_path / "repo")
    other = _init_repo(tmp_path / "other")
    polluted = dict(os.environ)
    polluted["GIT_DIR"] = str(other / ".git")
    polluted["GIT_WORK_TREE"] = str(other)
    probe = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(repo), capture_output=True, text=True, env=polluted,
    )
    assert probe.returncode == 0, probe.stderr
    leaked = probe.stdout.rstrip("\r\n")
    assert Path(leaked).resolve() == other.resolve(), (
        f"前提不成立：未净化环境下 git 未被重定向，实得 {leaked!r}"
    )

    _fake_git_stdout(monkeypatch, leaked)
    with pytest.raises(ValueError) as exc:
        repo_root(str(repo))

    assert "不包含探测起点" in str(exc.value)


# ── ⑤ worktree marker + 正向回归 ────────────────────────────────────────────

def test_returns_root_from_nested_subdirectory(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    sub = repo / "a" / "b"
    sub.mkdir(parents=True)

    assert repo_root(str(sub)) == os.path.realpath(str(repo))


def test_symlinked_start_resolves_to_real_root(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    sub = repo / "pkg"
    sub.mkdir()
    link = tmp_path / "link-to-pkg"
    link.symlink_to(sub, target_is_directory=True)

    assert repo_root(str(link)) == os.path.realpath(str(repo))


def test_linked_worktree_dot_git_is_a_file(tmp_path):
    """linked worktree 下 `top/.git` 是**文件**——marker 判定 MUST 用 exists 而非 isdir。"""
    repo = _init_repo(tmp_path / "repo")
    _commit_empty(repo)
    wt = tmp_path / "wt"
    _git("worktree", "add", "-q", str(wt), "-b", "side", cwd=repo)

    assert (wt / ".git").is_file(), "前提不成立：linked worktree 的 .git 应为文件"
    assert repo_root(str(wt)) == os.path.realpath(str(wt))


def test_submodule_dot_git_is_a_file(tmp_path):
    inner = _init_repo(tmp_path / "inner")
    (inner / "f.txt").write_text("x", encoding="utf-8")
    _git("add", "f.txt", cwd=inner)
    _commit_empty(inner)
    outer = _init_repo(tmp_path / "outer")
    _commit_empty(outer)
    _git("-c", "protocol.file.allow=always", "submodule", "add", "-q",
         str(inner), "sub", cwd=outer)
    sub = outer / "sub"

    assert (sub / ".git").is_file(), "前提不成立：submodule 的 .git 应为文件"
    assert repo_root(str(sub)) == os.path.realpath(str(sub))


def test_falls_back_outside_any_git_repo(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()

    assert repo_root(str(plain)) == os.path.abspath(str(plain))


def test_bare_repo_falls_back(tmp_path):
    bare = tmp_path / "bare.git"
    bare.mkdir()
    _git("init", "-q", "--bare", cwd=bare)

    assert repo_root(str(bare)) == os.path.abspath(str(bare))


def test_inside_dot_git_directory_falls_back(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    dot_git = repo / ".git"

    assert repo_root(str(dot_git)) == os.path.abspath(str(dot_git))


def test_cli_still_exits_zero_outside_any_git_repo(tmp_path):
    """回落分支的 CLI 级回归：非 git 仓库下 recorder 命令仍正常完成（exit 0）。"""
    plain = tmp_path / "plain"
    plain.mkdir()

    proc = subprocess.run(
        [sys.executable, SCRIPT, "--root", str(plain), "scan"],
        capture_output=True, text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert "Traceback" not in proc.stderr


# ── ② 超时（不回落） ────────────────────────────────────────────────────────

def test_timeout_raises_and_does_not_fall_back(tmp_path, monkeypatch):
    """超时 ≠「不在仓库里」：MUST 抛 ValueError，MUST NOT 回落 abspath(start)。

    同时断言 `subprocess.run` 真的收到了 `timeout` kwarg —— 没有它，挂死的 git
    会无限阻塞、既不失败也不可观测（失败模式表）。
    """
    repo = _init_repo(tmp_path / "repo")
    seen = {}

    def hang(cmd, **kwargs):
        seen.update(kwargs)
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout"))

    monkeypatch.setattr(rec_mod.subprocess, "run", hang)

    with pytest.raises(ValueError) as exc:
        repo_root(str(repo))

    assert "超时" in str(exc.value)
    assert isinstance(seen.get("timeout"), (int, float)) and seen["timeout"] > 0


def test_timeout_with_real_hanging_git(tmp_path, monkeypatch):
    """真注入一个不返回的 fake git（PATH 注入），让 subprocess 自己触发超时。

    完整的 30s 等待在单测里不可接受，故这里只证明「PATH 上的 git 会被真正执行、
    且挂死时走的是 TimeoutExpired 路径」：把 `subprocess.run` 的 timeout 交给真实
    实现处理，用一个 sleep 很久的 shim + 极短的外层等待来观察。
    """
    if sys.platform == "win32":
        pytest.skip("POSIX shell shim；Windows 泳道另行覆盖")
    repo = _init_repo(tmp_path / "repo")
    binx = tmp_path / "bin"
    binx.mkdir()
    shim = binx / "git"
    shim.write_text("#!/bin/sh\nexec /bin/sleep 120\n", encoding="utf-8")
    shim.chmod(0o755)
    monkeypatch.setenv("PATH", str(binx) + os.pathsep + os.environ.get("PATH", ""))

    real_run = subprocess.run

    def short_timeout(cmd, **kwargs):
        if kwargs.get("timeout"):
            kwargs["timeout"] = 1.0
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(rec_mod.subprocess, "run", short_timeout)

    with pytest.raises(ValueError) as exc:
        repo_root(str(repo))

    assert "超时" in str(exc.value)
    assert repo_root.__name__ == "repo_root"
