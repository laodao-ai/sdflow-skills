"""repo_root 身份校验（change harden-repo-root-fail-closed · Task 2 + cr-fix1）。

被测契约：`repo_root(start=None|str) -> str`，在把任何值当作可写仓根返回之前，必须证明
它是**起点所属【最近】仓库的根**；任一判据不满足即 `raise ValueError`。

**回落的判据是「自起点上溯一层 `.git` 都没找到」，不是「git 退出码非 0」**（cr-fix1）：
`safe.directory`（dubious ownership）/ 损坏的 `.git/config` / `.git/` 目录内起点同样以
128 退出，而进程**确实在仓内** —— 那些场景 MUST fail-closed，只有真·非 git 仓库、
bare repo、git 不可用才回落。「最近」二字同样是 cr-fix1 加的：祖先校验 + worktree marker
对**外层祖先仓库**（core.worktree 指祖先仓 / PATH 上的 fake git）双双放行。

本文件与 sdflow-issues/tests 下的 test_repo_root_identity_{buglist,issues}.py 逐条对应（三薄入口
经唯一共享源 `sdflow_issues_core` 取同一 `repo_root`；本组测试各自经其入口验证解析身份一致）。

方法论约束（design ADR-2 / Risks）：负例 **MUST NOT** mock `os.path.isabs` /
`isdir` / `realpath` —— mock 掉判据本身等于没测。除「git 输出内容」与「git 挂死」这两个
外部依赖行为外，一切都用 `tmp_path` 下真实存在/不存在的路径构造。

Run with: python3 -m pytest sdflow-issues/tests/test_repo_root_identity_todolist.py -v
"""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import todolist as rec_mod
from todolist import repo_root

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "todolist.py")

# 单点解析用例（Task 3）用的子命令：本 recorder 上一条读路径 + 一条合法委派边。
SINGLE_POINT_CMD = ["scan", "--json"]
SINGLE_POINT_CHILD_COMMAND = "scan"

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


# ── ①b 起点归一化：判据 = 「与非 symlink / 无 `..` 的等价起点结果一致」 ──────────
#
# 步骤①b 把起点归一化为绝对路径（回落分支 fail-closed 的承载点）。归一化改变了**传给
# git 的 cwd 字面量**，因此 symlink 起点与含 `..` 起点这两类形态 MUST 有专属锚：判据是
# 「结果与直接用真实路径进入完全一致」，**不是**「没抛异常」——后者对着一个错误的仓根
# 也能绿。symlink 一律用 tmp_path 下真建，MUST NOT mock os.path.realpath / isdir / isabs。

def test_symlinked_repo_root_start_matches_real_path_result(tmp_path):
    """起点是指向仓根本身的 symlink ⇒ 结果与直接从真实仓根进入一致。"""
    repo = _init_repo(tmp_path / "repo")
    link = tmp_path / "link-to-repo"
    link.symlink_to(repo, target_is_directory=True)

    assert repo_root(str(link)) == repo_root(str(repo))
    assert repo_root(str(link)) == os.path.realpath(str(repo))


def test_dotdot_in_start_matches_real_path_result(tmp_path):
    """起点含 `..`（`<repo>/sub/..`）⇒ 结果与直接传 `<repo>` 一致。"""
    repo = _init_repo(tmp_path / "repo")
    (repo / "sub").mkdir()

    assert repo_root(str(repo / "sub" / "..")) == repo_root(str(repo))
    assert repo_root(str(repo / "sub" / "..")) == os.path.realpath(str(repo))


def test_symlinked_start_with_subdir_matches_real_path_result(tmp_path):
    """起点是 `symlink/子目录` ⇒ 结果与直接从真实子目录进入一致。"""
    repo = _init_repo(tmp_path / "repo")
    (repo / "sub").mkdir()
    link = tmp_path / "link-to-repo"
    link.symlink_to(repo, target_is_directory=True)

    assert repo_root(str(link / "sub")) == repo_root(str(repo / "sub"))
    assert repo_root(str(link / "sub")) == os.path.realpath(str(repo))


def test_dotdot_after_symlinked_dir_follows_kernel_not_lexical(tmp_path):
    """`symlink-to-subdir/..` —— **lexical 归一化与内核语义在此分叉**。

    `link -> <repo>/sub` 时，内核解析 `link/..` = `<repo>`（symlink 目标的父目录），
    而 `os.path.normpath` 是**纯字面**运算，给出 `<tmp>`（link 自身的父目录）——两者指向
    完全不同的目录。∴ 步骤①b MUST NOT 对起点做 lexical 归一化：起点只需被抬成**绝对
    路径**（回落分支不再触 cwd 即达成 fail-closed），路径语义一律交给内核与
    `os.path.realpath` 解释。删掉这条约束会让本用例返回 `<tmp>`（一个非仓库目录，经回落
    分支返回）而不是仓根 —— 静默指向错误的可写根。
    """
    repo = _init_repo(tmp_path / "repo")
    sub = repo / "sub"
    sub.mkdir()
    link = tmp_path / "link-to-sub"
    link.symlink_to(sub, target_is_directory=True)

    assert repo_root(str(link) + os.sep + "..") == repo_root(str(repo))
    assert repo_root(str(link) + os.sep + "..") == os.path.realpath(str(repo))


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


def test_inside_dot_git_directory_fails_closed(tmp_path):
    """`.git/` 内部起点 MUST fail-closed —— **旧行为回落返回 `.git` 自身**。

    git 在此以 128 退出（"this operation must be run in a work tree"），旧实现把整个
    非 0 退出归为回落 ⇒ 返回 `<repo>/.git` ⇒ 下游 makedirs 在 **git 的内部目录**里建出
    `.git/openspec/issues/`。上溯一层即找到 `<repo>/.git` marker ⇒「在仓里 + git 拒答」
    ⇒ raise。行为变更已登记进 impl-report 的「须在设计门回写 spec」条目。
    """
    repo = _init_repo(tmp_path / "repo")
    dot_git = repo / ".git"

    with pytest.raises(ValueError) as exc:
        repo_root(str(dot_git))

    assert "git 拒绝作答" in str(exc.value)
    assert not (dot_git / "openspec").exists()


# ── ⑤ git 拒答但起点在仓内（fail-closed，非回落） ──────────────────────────

def test_git_refusing_inside_repo_fails_closed(tmp_path):
    """**缺陷 B**：git 以非 0 退出 ≠「不在仓库里」。

    目标态下本分支最高频的触发面是 `detected dubious ownership`（`safe.directory`）——
    容器 / CI / 共享 checkout 里 git **常态性**以 128 拒答，而进程确实在仓内。此处用
    损坏的 `.git/config` 构造同一形态（rc=128 + 起点在仓内），MUST NOT 解析 stderr 文案
    （无界、多语言、随版本变——基准 5），只用文件系统信号判定。

    旧实现返回 `<repo>/sub`（**仓库子目录**）⇒ 下游在仓内造出第二套 openspec/issues/。
    删掉「marker_dir is not None ⇒ raise」这一步，本用例必须变红。
    """
    repo = _init_repo(tmp_path / "repo")
    sub = repo / "sub"
    sub.mkdir()
    (repo / ".git" / "config").write_text("[core\nbroken", encoding="utf-8")

    # 前提核验：不假设，真跑一遍确认 git 确实以非 0 退出。
    probe = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(sub), capture_output=True, text=True,
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    )
    assert probe.returncode != 0, f"前提不成立：git 未拒答（rc={probe.returncode}）"

    with pytest.raises(ValueError) as exc:
        repo_root(str(sub))

    assert "git 拒绝作答" in str(exc.value)
    assert _entries(sub) == [], "仓库子目录 MUST NOT 出现任何 openspec/ 产物"


def test_cross_drive_commonpath_gets_diagnostic_triplet(tmp_path, monkeypatch):
    """F3：`os.path.commonpath` 对「没有公共根」的两条路径**自己抛裸 ValueError**
    （Windows 跨盘符：`C:\\repo` vs `D:\\elsewhere`）。裸 ValueError 能被调用方接住，
    但不带 `ERROR/cause/fix` 三元组，诊断质量断崖。

    该条件在 POSIX 上**结构性不可达**（两条路径都是绝对路径，必有 `/` 为公共前缀），
    故这里注入 commonpath 的抛出行为——注入的是**环境条件**（与 `_fake_git_stdout`
    注入 git 输出同性质），不是被测判据本身；`isabs`/`isdir`/`realpath` 一概未 mock。
    """
    repo = _init_repo(tmp_path / "repo")

    def boom(paths):
        raise ValueError("Paths don't have the same drive")

    monkeypatch.setattr(rec_mod.os.path, "commonpath", boom)

    with pytest.raises(ValueError) as exc:
        repo_root(str(repo))

    message = str(exc.value)
    assert message.startswith("ERROR: ")
    assert "; cause: " in message and "; fix: " in message
    assert "无法比较" in message


def test_git_refusing_outside_any_repo_still_falls_back(tmp_path):
    """回落判据的另一半：一层 marker 都找不到 ⇒ 仍正常回落（真·非 git 仓库）。

    与上一条成对——证明新判据是「上溯找不到 marker」而**不是**「git 退出码非 0」，
    没有把合法回落面一起 fail-closed 掉。
    """
    plain = tmp_path / "plain"
    plain.mkdir()

    assert repo_root(str(plain)) == os.path.abspath(str(plain))


# ── ⑨ 最近根一致（外层祖先仓库） ────────────────────────────────────────────

def test_core_worktree_redirect_to_ancestor_repo_is_rejected(tmp_path):
    """**缺陷 A**：`core.worktree` 指向**外层祖先仓库**时，祖先校验与 worktree marker
    **双双放行**——outer 确是 inner 的祖先，且 outer/.git 确实存在。

    既有 core.worktree 用例只覆盖重定向到**兄弟**目录（祖先校验能拦），本用例覆盖
    重定向到**祖先仓库**（祖先校验拦不住）。只有「最近根一致」能证明 git 返回的不是
    起点所属的那个仓。删掉步骤⑨，本用例必须变红。
    """
    outer = _init_repo(tmp_path / "outer")
    inner = _init_repo(outer / "proj")
    _git("config", "core.worktree", str(outer.resolve()), cwd=inner)

    # 前提核验：git 确实 rc=0 且返回了外层仓库（四项旧判据全过）。
    probe = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(inner), capture_output=True, text=True,
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    )
    assert probe.returncode == 0, f"前提不成立: {probe.stderr}"
    assert Path(probe.stdout.strip()).resolve() == outer.resolve(), (
        f"前提不成立：未重定向到祖先仓，实得 {probe.stdout!r}"
    )

    with pytest.raises(ValueError) as exc:
        repo_root(str(inner))

    assert "最近仓库" in str(exc.value)
    assert not (outer / "openspec").exists(), "外层仓库 MUST NOT 出现任何 openspec/ 产物"


def test_fake_git_on_path_returning_outer_repo_is_rejected(tmp_path, monkeypatch):
    """同形变体：PATH 上被替换的 git（rc=0）返回**外层祖先仓库**。

    与 core.worktree 指祖先仓同一形状——四项旧判据全过。证明步骤⑨拦的是「git 的答案
    不是最近仓根」这个**性质**，而不是 core.worktree 这一种成因。
    """
    outer = _init_repo(tmp_path / "outer")
    inner = _init_repo(outer / "inner")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "git"
    fake.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "rev-parse" ]; then echo "%s"; exit 0; fi\n'
        'exec /usr/bin/git "$@"\n' % outer.resolve(),
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])

    with pytest.raises(ValueError) as exc:
        repo_root(str(inner))

    assert "最近仓库" in str(exc.value)
    assert not (outer / "openspec").exists()


# ── ⑨ 最近根一致：合法场景 MUST NOT 被误伤 ────────────────────────────────

def test_nested_inner_repo_resolves_to_inner(tmp_path):
    """嵌套仓库的**正常**情形（outer 与 inner 都是仓、无 core.worktree）：
    从 inner 起 MUST 返回 inner —— 新判据 MUST NOT 把它一起拒掉。"""
    outer = _init_repo(tmp_path / "outer")
    inner = _init_repo(outer / "inner")

    assert repo_root(str(inner)) == os.path.realpath(str(inner))


def test_linked_worktree_resolves_to_worktree(tmp_path):
    """linked worktree 的 `.git` 是**文件**不是目录：上溯用 `exists` 而非 `isdir`。
    把步骤④的 `os.path.exists` 改成 `os.path.isdir`，本用例必须变红。"""
    repo = _init_repo(tmp_path / "repo")
    _commit_empty(repo)
    wt = tmp_path / "wt"
    _git("worktree", "add", "-q", str(wt), "-b", "wtbr", cwd=repo)
    assert (wt / ".git").is_file(), "前提不成立：linked worktree 的 .git 不是文件"

    assert repo_root(str(wt)) == os.path.realpath(str(wt))


def test_repo_subdir_and_symlink_start_resolve_to_repo_root(tmp_path):
    """仓库子目录起点 与 symlink 起点：两者都 MUST 解析到同一个真实仓根。"""
    repo = _init_repo(tmp_path / "repo")
    sub = repo / "a" / "b"
    sub.mkdir(parents=True)
    link = tmp_path / "link-to-sub"
    link.symlink_to(sub)

    assert repo_root(str(sub)) == os.path.realpath(str(repo))
    assert repo_root(str(link)) == os.path.realpath(str(repo))


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


# ── CLI 级 fail-closed 锚（Task 2 双轴审 C1 / C2） ──────────────────────────────

def test_cli_with_deleted_process_cwd_exits_two_without_traceback(tmp_path):
    """C1：cwd 在运行期被删除时，**经 CLI 调用**必须 exit 2 + 受控诊断，MUST NOT 吐 Traceback。

    这是回落分支的裸 `OSError` 逃逸缺陷的真实复现路径：cwd 被删 ⇒ `git rev-parse` 以 128
    退出 ⇒ 落回落分支 ⇒ `os.path.abspath(".")` 内部调 `os.getcwd()` 自己抛
    `FileNotFoundError` ⇒ 逃出 `repo_root` ⇒ 调用方只 `except ValueError` 接不住 ⇒
    RC=1 + Traceback。修复后起点在步骤①b 就归一化为绝对路径，回落分支再也碰不到 cwd。

    **本用例 MUST 走真子进程 CLI**：函数层用例证明不了退出码与 stderr 形态。
    """
    doomed = tmp_path / "doomed"
    doomed.mkdir()
    program = (
        "import os, subprocess, sys\n"
        "os.chdir(sys.argv[2])\n"
        "os.rmdir(sys.argv[2])\n"
        "proc = subprocess.run([sys.executable, sys.argv[1], %r],\n"
        "                      capture_output=True, text=True)\n"
        "sys.stdout.write('RC:%%d\\n' %% proc.returncode)\n"
        "sys.stdout.write('ERR:' + proc.stderr.replace('\\n', '<NL>') + '\\n')\n"
    ) % ('scan',)
    outer = subprocess.run(
        [sys.executable, "-c", program, SCRIPT, str(doomed)],
        capture_output=True, text=True, cwd=str(tmp_path),
    )

    assert outer.returncode == 0, outer.stderr
    assert "RC:2" in outer.stdout, outer.stdout
    err_line = [l for l in outer.stdout.splitlines() if l.startswith("ERR:")][0]
    assert "Traceback" not in err_line, err_line
    assert "ERROR: 无法确定仓根探测起点" in err_line, err_line
    assert "cause:" in err_line and "fix:" in err_line, err_line


def test_getcwd_permission_error_is_controlled_too(monkeypatch):
    """CF-4：`os.getcwd()` 在父目录权限被撤时抛 `PermissionError`——与 `FileNotFoundError`
    同属 `OSError`，同样会裸逃。守护 MUST 捕 `OSError` 而非只捕 `FileNotFoundError`。

    这里 mock 的是 `os.getcwd`（外部环境行为），**不是** `os.path.isabs` / `isdir` /
    `realpath`（判据本身）——后者才是方法论红线禁止的。
    """
    def denied():
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(rec_mod.os, "getcwd", denied)

    with pytest.raises(ValueError) as exc:
        repo_root()

    assert str(exc.value).startswith("ERROR: ")
    assert "无法确定仓根探测起点" in str(exc.value)


def test_cli_bad_root_exits_two_with_diagnostic_on_stderr(tmp_path):
    """C2：spec 要求「坏仓根 → 经 CLI 调用时 exit 2、诊断落 stderr」的**独立绿锚**。

    走的是 `--root` 指向不存在目录这条**现在就能触发**的路径，不依赖任何当前为红的用例。
    退出码 2 在本 CLI 上并非坏仓根独有（坏 scan id 也是 2）⇒ MUST 同时断言 stderr 的
    具体诊断内容，MUST NOT 仅凭退出码判定通过。
    """
    missing = tmp_path / "no-such-root"

    proc = subprocess.run(
        [sys.executable, SCRIPT, "--root", str(missing), 'scan'],
        capture_output=True, text=True, cwd=str(tmp_path),
    )

    assert proc.returncode == 2, (proc.returncode, proc.stdout, proc.stderr)
    assert "Traceback" not in proc.stderr, proc.stderr
    assert proc.stderr.startswith("ERROR: "), proc.stderr
    assert "仓根探测起点不是既存目录" in proc.stderr, proc.stderr
    assert "cause:" in proc.stderr and "fix:" in proc.stderr, proc.stderr
    assert repr(str(missing))[1:-1] in proc.stderr, "被拒值应出现在诊断里"
    assert not missing.exists(), "被拒的仓根 MUST NOT 被下游 makedirs 静默具现"
    assert _entries(tmp_path) == [], "被拒路径下不该留下任何产物"


# ── ADR-5 单点解析（change harden-repo-root-fail-closed · Task 3 · R2） ─────────

def _repo_root_calls(node):
    """数 `repo_root(...)` 的 **Call 节点**。

    MUST NOT 用 grep 代替：`def repo_root(` 与 docstring 里的字面量都会被文本匹配算进来
    （本脚本的 docstring 就含 `root = args.root` 一类字样），得到假红或脆件偏移量。
    """
    return [n for n in ast.walk(node)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "repo_root"]


def _script_ast():
    _core_path = Path(__file__).parent.parent / "scripts" / "sdflow_issues_core" / "__init__.py"
    return ast.parse(_core_path.read_text(encoding="utf-8"))


def test_diagnostics_never_recommend_explicit_root(request):
    """诊断的 `fix:` MUST NOT 把「显式指定 --root」当修复手段（cr-fix2 · F5）。

    **理由是结构性的**：`repo_root` 对显式起点与默认起点走的是**同一条**探测路径——
    步骤③ 不因 `start` 的来源而分叉。∴ 超时 / 坏输出 / marker 缺失 / 最近根不一致这些
    诊断建议用户「改传 --root」时，用户照做只会**原样撞上同一个错误**，而真正的故障面
    （文件系统挂起、PATH 上的 git wrapper、core.worktree 重定向）一个都没被指出来。
    误导性指引比没有指引更贵：它把人送上一条注定失败的路。

    机械判据：剥掉 docstring 后，`repo_root` 函数体内的字符串常量一律 MUST NOT 含
    `--root`（docstring 里描述子进程 `--root <已解析值>` 的传参协议是合法的，故排除）。
    这条守的是**整片诊断面**，不是当场被点穿的那一处 —— 新增诊断分支若照抄旧措辞，
    本用例当场判红。
    """
    fn = next(
        (n for n in ast.walk(_script_ast())
         if isinstance(n, ast.FunctionDef) and n.name == "repo_root"),
        None,
    )
    assert fn is not None, "脚本里找不到 repo_root —— 选择器失效"

    body = fn.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]  # docstring 讲的是子进程传参协议，不是给用户的 fix: 指引

    offenders = [
        (node.lineno, node.value)
        for stmt in body
        for node in ast.walk(stmt)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and "--root" in node.value
    ]
    assert not offenders, (
        "诊断把 --root 当修复手段，但显式 --root 仍走同一次 git 探测 ⇒ 用户照做会拿到"
        "一模一样的错误。请改成针对文件系统 / git wrapper / core.worktree 的可执行排查"
        "步骤。违规字符串：%r" % (offenders,)
    )


def test_repo_root_is_resolved_once_per_process_and_only_in_main():
    """R2：仓根在单次调用（边界=进程）内只解析一次。

    本脚本全文 MUST 只剩 1 个 `repo_root(` Call 节点，且它 MUST 位于 `main()`——
    三份 recorder 合计 3 个（改造前 19 个）。`cmd_*` / `_*_snapshot` 一律直接消费
    `args.root`。理由见 ADR-5：两次解析之间目标若失去 `.git`，第二次会静默爬升到外层
    祖先仓库，于是锁建在一个根、数据写进另一个根。
    """
    tree = _script_ast()
    calls = _repo_root_calls(tree)
    assert len(calls) == 1, [c.lineno for c in calls]

    owners = sorted(fn.name for fn in ast.walk(tree)
                    if isinstance(fn, ast.FunctionDef) and _repo_root_calls(fn))
    assert owners == ["run_cli"], owners


def test_root_argparse_default_is_none():
    """1.2c：`--root` 默认值 MUST 是 `None`，不是 `"."`。

    默认 `"."` 时未指定路径走的是「显式起点」分支，而 `os.path.isdir(".")` 在 cwd 被删除后
    仍返回 `True` ⇒ 起点校验形同虚设（ADR-7）。默认 `None` 才让 `repo_root` 走 `os.getcwd()`。
    """
    defaults = [kw.value
                for call in ast.walk(_script_ast())
                if isinstance(call, ast.Call)
                and getattr(call.func, "attr", None) == "add_argument"
                and call.args
                and isinstance(call.args[0], ast.Constant)
                and call.args[0].value == "--root"
                for kw in call.keywords if kw.arg == "default"]

    assert len(defaults) == 1, defaults
    assert isinstance(defaults[0], ast.Constant), ast.dump(defaults[0])
    assert defaults[0].value is None


def test_unspecified_root_probes_cwd_while_explicit_root_is_validated(tmp_path):
    """1.2c 的行为面：未指定与显式指定是**两条可区分的路径**。

    同一个 cwd 下：未指定 → `os.getcwd()` 探测 → 落到 cwd 所属仓根；
    显式指定一个不存在的路径 → 起点校验在调 git **之前**拦下 → exit 2。
    仅凭退出码不足以判定（坏 scan id 也是 exit 2）⇒ 同时断言 stderr 的具体诊断。
    """
    repo = _init_repo(tmp_path / "repo")
    nested = repo / "a" / "b"
    nested.mkdir(parents=True)

    probed = subprocess.run(
        [sys.executable, SCRIPT, *SINGLE_POINT_CMD],
        capture_output=True, text=True, cwd=str(nested),
    )
    assert probed.returncode == 0, probed.stderr
    assert (repo / "openspec" / "issues").exists(), "未指定 --root 应落到 cwd 所属仓根"
    assert not (nested / "openspec").exists(), "MUST NOT 落到 cwd 自身"

    missing = tmp_path / "no-such-root"
    explicit = subprocess.run(
        [sys.executable, SCRIPT, "--root", str(missing), *SINGLE_POINT_CMD],
        capture_output=True, text=True, cwd=str(nested),
    )
    assert explicit.returncode == 2, (explicit.returncode, explicit.stderr)
    assert "Traceback" not in explicit.stderr, explicit.stderr
    assert "仓根探测起点不是既存目录" in explicit.stderr, explicit.stderr
    assert not missing.exists(), "被拒的起点 MUST NOT 被具现"


def test_child_root_drift_premise_climbs_to_outer(tmp_path):
    """R2 缺口锚（下一个用例）的**前提**核验 —— 刻意**不带 xfail**。

    前提 = 「inner 失去 `.git` 之后，`repo_root(inner)` 确实静默上爬到 outer」。
    它若不成立，下一个用例构造的根本不是目标场景、锚也就不再锚住任何东西。
    而把这条断言放在 xfail 用例体内时**失败也是绿**（计入 xfail），失效永远无声；
    提到这里，前提一烂当场判红。
    """
    outer = _init_repo(tmp_path / "outer")
    inner = _init_repo(outer / "proj")
    subprocess.run(["rm", "-rf", str(inner / ".git")], check=True)

    assert not (inner / ".git").exists(), "前提构造失败：inner/.git 未被删除"
    assert os.path.realpath(repo_root(str(inner))) == os.path.realpath(str(outer)), (
        "repo_root 不再从失去 .git 的 inner 上爬到 outer —— R2 缺口锚的前提已不成立"
    )


@pytest.mark.xfail(strict=True, reason=(
    "R2 Scenario「子进程解析出不同的根时响亮失败」当前**不成立**（实测三份 recorder 一致）。"
    "design ADR-5 假定 validate_recorder_participant 的 path/token 绑定会兜底，但 "
    "recorder_lock 在它抛 RecorderLockError 时 `except RecorderLockError: participant = None` "
    "吞掉异常、回落为 owner 模式 ⇒ 子进程在自己解析出的**外层根**上新建锁、makedirs、rc=0。"
    "堵这个洞须给锁协议增加 owner-root 绑定（把父进程已解析的根随 token 一起下传），"
    "而那会与既有契约测试 test_invalid_participant_env_falls_back_to_owner_or_conflict "
    "（显式断言坏 participant env 回落 owner + exit 0）直接冲突 ⇒ 属设计门议题，"
    "Task 3 不就地改协议。本用例是该缺口的机械锚：绑定一旦补上它会 XPASS，"
    "strict 模式当场变红，强制回来删掉本标记。"
))
def test_child_resolving_a_different_root_must_fail_loudly(tmp_path):
    """1.11：跨进程二次解析的兜底锚定。

    构造：outer 是仓、inner 是 outer 里的嵌套仓。父进程在 inner 上持锁并以
    `--root <inner>` 拉起子进程；两次解析之间 inner 失去 `.git` ⇒ 子进程的
    `repo_root(inner)` 沿目录树上爬、静默返回 **outer**（rc=0、过全部身份校验）。

    此时子进程 MUST 响亮失败，MUST NOT 在 outer 上落任何东西。
    """
    outer = _init_repo(tmp_path / "outer")
    inner = _init_repo(outer / "proj")

    with rec_mod.recorder_lock(str(inner), "sweep") as owner:
        subprocess.run(["rm", "-rf", str(inner / ".git")], check=True)

        # 前提核验**不在这里**——已提到 xfail 之外的
        # test_child_root_drift_premise_climbs_to_outer。写在本函数体内的断言会被
        # xfail 吞成绿：前提烂掉（_init_repo 变形 / rm -rf 失败 / repo_root 不再上爬）时
        # 断言失败 → 计入 xfail → XFAIL 摘要照旧打印 R2 说明，锚已空壳却无人知道。
        # 实测：本函数体首行插 `assert False` ⇒ `1 xfailed`（绿）。

        env = dict(os.environ)
        env[rec_mod.RECORDER_LOCK_ENV] = owner.token
        env[rec_mod.RECORDER_DELEGATION_CHAIN_ENV] = json.dumps(
            ["sweep", SINGLE_POINT_CHILD_COMMAND]
        )
        child = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(inner), *SINGLE_POINT_CMD],
            capture_output=True, text=True, env=env, cwd=str(tmp_path),
        )

    assert child.returncode != 0, (
        "子进程解析出不同的根却静默成功: rc=%d stdout=%r" % (child.returncode, child.stdout)
    )
    assert not (outer / "openspec").exists(), (
        "MUST NOT 在自行解析出的外层根上具现任何目录"
    )


# ── ⑥ 解码：git stdout 不可解码时 MUST 走受控失败路径 ──────────────────────

def test_undecodable_git_stdout_fails_closed_with_controlled_diagnosis(
    tmp_path, monkeypatch
):
    """PATH 上的 git 吐出**不可解码字节**（POSIX 路径是任意字节串，非 UTF-8 文件名合法）。

    MUST 得到带 ERROR/cause/fix 三元组的 **ValueError 本尊**。

    变异：把步骤③的 bytes 捕获改回 `text=True`，`subprocess.run` 在读管道时就抛
    `UnicodeDecodeError` —— 它是 ValueError 的**子类**，`pytest.raises(ValueError)`
    照样接住，∴ 这里 MUST 断言**精确类型**，否则变异不可区分。届时诊断三元组消失；
    Windows 上同样成因会让读管道**线程**崩掉、`out.stdout` 变成 None ⇒ `.rstrip` 抛
    AttributeError（连 ValueError 都不是）⇒ 调用方 `except ValueError` 接不住 ⇒ 裸
    Traceback，正是本 change 要消灭的形态。
    """
    if sys.platform == "win32":
        pytest.skip("POSIX shell shim；Windows 泳道另行覆盖")
    repo = _init_repo(tmp_path / "repo")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "git"
    fake.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"rev-parse\" ]; then printf '/tmp/\\377\\376bad\\n'; exit 0; fi\n"
        'exec /usr/bin/git "$@"\n',
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ.get("PATH", ""))

    with pytest.raises(ValueError) as exc:
        repo_root(str(repo))

    assert type(exc.value) is ValueError, (
        "抛的是 %s —— 解码失败逃出了受控失败路径（诊断三元组随之丢失）"
        % type(exc.value).__name__
    )
    msg = str(exc.value)
    assert msg.startswith("ERROR:"), msg
    assert "cause:" in msg and "fix:" in msg, msg


# ── 守护存活自检：rootdir 被更深处的 ini 抢走 ⇒ 仓根 conftest 出局 ─────────

def test_repo_root_guards_are_actually_loaded(request):
    """守护必须能回答「我现在活着吗」，否则它的失效永远无声。

    仓根 `conftest.py` 的 cwd 泄漏断言只在被 pytest **收集到**时才生效，而收集止于
    confcutdir（默认 = rootdir）。rootdir = 「参数公共祖先向上找到的**第一个** inifile」，
    **先命中者胜**：任一 skill 目录下出现 pytest 配置段（`pyproject.toml` 的
    `[tool.pytest.ini_options]` / `tox.ini` 的 `[pytest]` / `pytest.ini`），以该 skill
    为参数跑测试时 rootdir 就塌到那里，仓根 `pytest.ini` 与 `conftest.py` 双双出局，
    cwd 泄漏断言**静默失效**（实测：泄漏探针 `1 passed`）。
    仓根 `pytest.ini` 的注释只论证了「**无** ini 时 rootdir 塌缩」，不覆盖本形态。

    本仓当前 0 个 `pyproject.toml` 只是**现状**、不是保证 —— 任一 skill 将来加
    ruff / mypy / 打包配置就会踩，且无声。

    覆盖边界（诚实登记）：本自检随三份 recorder 的测试文件分发 ⇒ `pytest <recorder>/tests/`
    这类按 skill 的调用姿势有守；**其余 skill 的 `tests/` 下若出现 ini，以那个 skill 为
    参数单跑时仍无自检**（自检只能落在退化场景里仍被收集的地方，即叶子；集中式落点在
    rootdir 被抢时同样出局，结构上做不到）。全量 `pytest`（参数公共祖先 = 仓根）不受
    影响 —— 仓根 `pytest.ini` 先被命中。
    """
    repo = Path(__file__).resolve().parent.parent.parent
    config = request.config

    assert Path(config.rootpath) == repo, (
        "pytest rootdir=%s，不是仓根 %s —— 多半是某个更深的目录出现了 pytest 配置段抢走了 "
        "rootdir；此时 confcutdir 同步塌陷，仓根 conftest.py 的 cwd 泄漏断言已经不生效了。"
        % (config.rootpath, repo)
    )

    root_conftest = str(repo / "conftest.py")
    assert config.pluginmanager.has_plugin(root_conftest), (
        "仓根 conftest.py 未被注册为插件 —— cwd 泄漏断言此刻是空的"
    )
    plugin = config.pluginmanager.get_plugin(root_conftest)
    assert hasattr(plugin, "pytest_runtest_call"), (
        "仓根 conftest 已加载，但承载 cwd 泄漏断言的 pytest_runtest_call 钩子不见了"
    )
