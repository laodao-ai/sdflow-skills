"""执行级单测：直接调用 `anchor_writeback.main()`（非文本层字符串断言）。

`test_anchor_contract.py` 只做文本层契约（SKILL.md 是否指示调用脚本），此前**无任何测试
真跑过** `anchor_writeback.main()` 本身——本文件补齐 brief 第 8 条 MUST 的执行级覆盖：
正例写入 round-trip、脏树守卫、`--allow-dirty` 逃生口、空监视域拒写、`--set` 同批原子写。
"""
import base64
import hashlib
import sys
from pathlib import Path

import pytest

from conftest import commit_all, mkchange

REPO = Path(__file__).resolve().parents[2]
_scripts = str(REPO / "sdflow-ship" / "scripts")
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)
import anchor_writeback as aw  # noqa: E402
import ship_gate as sg  # noqa: E402


def _write_design_change(repo, name="demo"):
    d = mkchange(repo, name)
    (d / "proposal.md").write_text("# proposal\n", encoding="utf-8")
    (d / "design.md").write_text("# design\n", encoding="utf-8")
    (d / "spec-review-report.md").write_text("# report\n", encoding="utf-8")
    return d


def _read_state(path):
    text = path.read_text(encoding="utf-8")
    state, err = sg.parse_ship_gate_frontmatter(text)
    assert err is None, f"frontmatter 解析失败：{err}"
    return state


def test_clean_tree_write_anchor_roundtrip(repo):
    d = _write_design_change(repo)
    commit_all(repo, "seed change")
    aw.main(["--root", str(repo), "--change", "demo",
             "--report", "spec-review-report.md", "--domain", "design"])
    state = _read_state(d / "spec-review-report.md")
    assert "reviewed_sha" in state and len(state["reviewed_sha"]) == 64
    assert "reviewed_manifest" in state
    manifest_bytes = base64.b64decode(state["reviewed_manifest"])
    assert hashlib.sha256(manifest_bytes).hexdigest() == state["reviewed_sha"]


def test_dirty_watch_set_rejects_write(repo, capsys):
    d = _write_design_change(repo)
    commit_all(repo, "seed change")
    (d / "design.md").write_text("# design changed uncommitted\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        aw.main(["--root", str(repo), "--change", "demo",
                 "--report", "spec-review-report.md", "--domain", "design"])
    assert exc.value.code != 0
    assert "未提交改动" in capsys.readouterr().err
    # 报告文件未被改写（拒写是真拒写，非"写了坏值"）
    assert "reviewed_sha" not in (d / "spec-review-report.md").read_text(encoding="utf-8")


def test_allow_dirty_escape_hatch_permits_write(repo):
    d = _write_design_change(repo)
    commit_all(repo, "seed change")
    (d / "design.md").write_text("# design changed uncommitted\n", encoding="utf-8")
    aw.main(["--root", str(repo), "--change", "demo",
             "--report", "spec-review-report.md", "--domain", "design", "--allow-dirty"])
    state = _read_state(d / "spec-review-report.md")
    assert "reviewed_sha" in state and len(state["reviewed_sha"]) == 64


def test_empty_watch_domain_rejects_write(repo, capsys):
    # 仓内只有 openspec/ 一个顶层条目：--domain code 排除 openspec 后监视域为空集。
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text("# report\n", encoding="utf-8")
    commit_all(repo, "seed change, only openspec at top level")
    with pytest.raises(SystemExit) as exc:
        aw.main(["--root", str(repo), "--change", "demo",
                 "--report", "spec-review-report.md", "--domain", "code"])
    assert exc.value.code != 0
    assert "空集" in capsys.readouterr().err


def test_set_flag_writes_conclusion_and_anchor_atomically(repo):
    d = _write_design_change(repo)
    commit_all(repo, "seed change")
    aw.main(["--root", str(repo), "--change", "demo",
             "--report", "spec-review-report.md", "--domain", "design",
             "--set", "design_approved=true"])
    state = _read_state(d / "spec-review-report.md")
    assert state.get("design_approved") is True
    assert "reviewed_sha" in state and len(state["reviewed_sha"]) == 64
    assert "reviewed_manifest" in state


# ══ 〔impl-review-fix C2/H3〕脏树守卫的 git 调用失败 MUST fail-loud，MUST NOT 折空串放行 ══

def test_dirty_guard_fails_loud_when_git_status_returns_nonzero(repo, capsys, monkeypatch):
    """[C2] `git status --porcelain` 非零退出（模拟仓损坏/锁/权限）之前会被折成空串 →
    脏树守卫误判"无脏改动"→ 放行写锚。红先于绿：本用例在修复前会看到写锚**成功**
    （报告被写入 reviewed_sha），修复后 MUST fail-loud 拒写、报告不被改写。"""
    d = _write_design_change(repo)
    commit_all(repo, "seed change")

    class _FakeCompleted:
        returncode = 128
        stdout = ""
        stderr = "fatal: not a git repository (fake failure)"

    real_git_run = sg._git_run

    def _fake_git_run(root, args, text):
        # 只在真实脏树守卫会发出的 `status` 调用上注入故障，其余（`rev-parse` 等
        # main() 起手的 git 可用性探测）仍走真实实现，避免探测本身先被误伤而掩盖本用例。
        if args and args[0] == "status":
            return _FakeCompleted()
        return real_git_run(root, args, text)

    monkeypatch.setattr(aw.sg, "_git_run", _fake_git_run)
    with pytest.raises(SystemExit) as exc:
        aw.main(["--root", str(repo), "--change", "demo",
                 "--report", "spec-review-report.md", "--domain", "design"])
    assert exc.value.code != 0
    err = capsys.readouterr().err
    assert "非零退出码" in err or "拒绝写锚" in err
    assert "reviewed_sha" not in (d / "spec-review-report.md").read_text(encoding="utf-8")


def test_dirty_guard_fails_loud_when_git_status_times_out(repo, capsys, monkeypatch):
    """[H3] `_git_status_porcelain_raw` 原走裸 `subprocess.run`，无 timeout/OSError 处理，
    git 挂起/不可用时未捕获异常会直接逸出（非 fail-loud `_fail` 风格）。修复后改走
    `ship_gate._git_run` 单出口，超时/不可用统一映射为 `GateIndeterminate` 并被
    `_git_status_porcelain_raw` 捕获转 `_fail`（SystemExit，非裸 traceback）。"""
    d = _write_design_change(repo)
    commit_all(repo, "seed change")

    real_git_run = sg._git_run

    def _fake_git_run(root, args, text):
        if args and args[0] == "status":
            raise sg.GateIndeterminate("git 调用超过 30s 未返回（模拟）", "git-timeout")
        return real_git_run(root, args, text)

    monkeypatch.setattr(aw.sg, "_git_run", _fake_git_run)
    with pytest.raises(SystemExit) as exc:
        aw.main(["--root", str(repo), "--change", "demo",
                 "--report", "spec-review-report.md", "--domain", "design"])
    assert exc.value.code != 0
    assert "无法判定脏树守卫" in capsys.readouterr().err
    assert "reviewed_sha" not in (d / "spec-review-report.md").read_text(encoding="utf-8")


# ══ 〔impl-review-fix H4〕main() 中裸 `sg.run_git(...rev-parse...)` 未捕获 GateIndeterminate ══

def test_git_dir_probe_failure_fails_loud_not_uncaught_traceback(capsys, monkeypatch):
    """红先于绿：修复前，`sg.run_git` 内部若抛 `GateIndeterminate`（git 超时/不可用），
    `main()` 没有 try/except 包裹这两处调用 —— 异常会原样向上逸出成裸 traceback，
    而不是本文件其余分支统一的 `_fail`（SystemExit + 清晰诊断）。"""
    def _raise_timeout(root, *args):
        raise sg.GateIndeterminate("git 子进程无法启动（模拟）", "git-unavailable")

    monkeypatch.setattr(aw.sg, "run_git", _raise_timeout)
    with pytest.raises(SystemExit) as exc:
        aw.main(["--root", "/tmp/does-not-matter", "--change", "demo",
                 "--report", "spec-review-report.md", "--domain", "design"])
    assert exc.value.code != 0
    assert "git 调用失败" in capsys.readouterr().err


# ══ 〔impl-review-fix H5〕合并写入 MUST 保留块内其它既有顶层字段 ══════════════════

def test_writeback_preserves_other_top_level_frontmatter_fields(repo):
    """报告首块 frontmatter 除 `ship-gate:` 外还有一个同级字段（如 `title:`）时，
    写锚后该字段 MUST 仍在——红先于绿：修复前整块重建为 `["---", "ship-gate:", ...]`，
    `title:` 会被静默丢弃。"""
    d = mkchange(repo, "demo")
    (d / "proposal.md").write_text("# proposal\n", encoding="utf-8")
    (d / "design.md").write_text("# design\n", encoding="utf-8")
    (d / "spec-review-report.md").write_text(
        "---\ntitle: 一份带标题的报告\nship-gate:\n  verify: PASS\n---\n# report\n",
        encoding="utf-8")
    commit_all(repo, "seed change with extra frontmatter field")
    aw.main(["--root", str(repo), "--change", "demo",
             "--report", "spec-review-report.md", "--domain", "design"])
    text = (d / "spec-review-report.md").read_text(encoding="utf-8")
    assert "title: 一份带标题的报告" in text, "同级顶层字段被写锚静默丢弃（H5）"
    state = _read_state(d / "spec-review-report.md")
    assert "reviewed_sha" in state and len(state["reviewed_sha"]) == 64


# ══ 〔impl-review-fix H6〕--change / --report 路径穿越防护 ══════════════════════

def test_report_path_traversal_rejected(repo, capsys):
    """`--report ../../../evil.md` 试图逃出 change 目录写任意文件，MUST fail-loud 拒绝。"""
    d = _write_design_change(repo)
    commit_all(repo, "seed change")
    target = repo / "evil.md"
    with pytest.raises(SystemExit) as exc:
        aw.main(["--root", str(repo), "--change", "demo",
                 "--report", "../../../evil.md", "--domain", "design"])
    assert exc.value.code != 0
    assert "逃逸" in capsys.readouterr().err
    assert not target.exists()
    assert "reviewed_sha" not in (d / "spec-review-report.md").read_text(encoding="utf-8")


def test_change_argument_with_path_separator_rejected(repo, capsys):
    """`--change` 含路径分隔符（如 `../other`）MUST fail-loud 拒绝，不得被拼进路径。"""
    _write_design_change(repo)
    commit_all(repo, "seed change")
    with pytest.raises(SystemExit) as exc:
        aw.main(["--root", str(repo), "--change", "../other",
                 "--report", "spec-review-report.md", "--domain", "design"])
    assert exc.value.code != 0
    assert "非法" in capsys.readouterr().err


# ══ 〔impl-review-fix M7〕脏树守卫的 rename 行按目的路径判 domain 排除 ══════════════

def test_dirty_paths_rename_out_of_openspec_is_not_excluded(monkeypatch):
    """rename 源在 openspec/、目的落在 code 域 → MUST 被判为 code 域脏改动
    （红先于绿：修复前整行以 `openspec/` 打头就被整条跳过，漏判）。"""
    monkeypatch.setattr(aw, "_git_status_porcelain_raw",
                         lambda root, pathspecs: "R  openspec/foo.md -> foo.md\n")
    dirty = aw._dirty_paths(Path("/nonexistent"), "code", None)
    assert dirty == ["openspec/foo.md -> foo.md"], \
        "目的路径落在 code 域的 rename 被误当 openspec 域内改动跳过（M7）"


def test_dirty_paths_rename_into_openspec_is_excluded(monkeypatch):
    """反方向：rename 源在 code 域、目的落进 openspec/ → 仍应被排除（code 域视角看，
    结果已不在 code 域内），同一判据两个方向都要对。"""
    monkeypatch.setattr(aw, "_git_status_porcelain_raw",
                         lambda root, pathspecs: "R  foo.md -> openspec/foo.md\n")
    dirty = aw._dirty_paths(Path("/nonexistent"), "code", None)
    assert dirty == []
