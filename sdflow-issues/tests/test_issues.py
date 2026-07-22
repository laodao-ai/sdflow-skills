"""
Tests for issues.py's Task 8 skeleton: cross-pool `read_pool` join (bug + todo)
and D9 cross-pool ID conflict detection.
Run with: python3 -m pytest sdflow-issues/tests/ -v
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import issues as issues_mod
from issues import (
    atomic_write, cross_pool_id_conflicts, read_pool, repo_root, CrossPoolIDConflict,
)

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "issues.py")

# Task 16：端到端一致性自检要用真实 buglist.py/todolist.py CLI 子进程（不借道 issues.py
# 内部函数）造数据，定位方式镜像 issues.py 自身的 SKILLS_ROOT 探测（tests 目录上三级
# 是 sdflow-skills 根，sdflow-buglist/sdflow-todolist 与本 skill 是同级 sibling）。
BUGLIST_SCRIPT = str(Path(__file__).parent.parent.parent / "sdflow-issues" / "scripts" / "buglist.py")
TODOLIST_SCRIPT = str(Path(__file__).parent.parent.parent / "sdflow-issues" / "scripts" / "todolist.py")


def _load_module_from_path(name, path):
    """按文件路径 import 一个独立脚本模块（buglist.py/todolist.py 不是包，无法
    `import buglist`）——用 importlib.util.spec_from_file_location 直接从文件路径加载，
    只为读它们的模块级常量（如 `STATUS_CODES`），不依赖它们互相 import（三脚本子进程
    解耦的既定风格，见 issues.py 模块 docstring）。两脚本都用 `if __name__ == "__main__"`
    守卫入口，import 不会触发 argparse/执行。"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


buglist_mod = _load_module_from_path("buglist_for_test", BUGLIST_SCRIPT)
todolist_mod = _load_module_from_path("todolist_for_test", TODOLIST_SCRIPT)


class TestReadPoolJoin:
    """Step 1/3：read_pool join buglist + todolist 两池，断言含两池项 + pool 标记。"""

    def test_joins_both_pools_with_pool_tag(self, tmp_path):
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "change-a", "batch": "batch-1"},
            {"id": "B2", "status": "FIXED", "change": "change-a", "batch": ""},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "change-a", "batch": ""},
        ])

        items = read_pool(str(tmp_path))

        assert len(items) == 3
        by_id = {it["id"]: it for it in items}
        assert by_id["B1"]["pool"] == "bug"
        assert by_id["B2"]["pool"] == "bug"
        assert by_id["T1"]["pool"] == "todo"
        # 每项至少含 id/status/change/batch/pool 五个字段
        for it in items:
            for key in ("id", "status", "change", "batch", "pool"):
                assert key in it
        assert by_id["B1"]["status"] == "OPEN"
        assert by_id["B1"]["change"] == "change-a"
        assert by_id["B1"]["batch"] == "batch-1"
        assert by_id["T1"]["status"] == "OPEN"
        assert by_id["T1"]["change"] == "change-a"

    def test_empty_when_no_files_in_either_pool(self, tmp_path):
        assert read_pool(str(tmp_path)) == []

    def test_only_bug_pool_present(self, tmp_path):
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        items = read_pool(str(tmp_path))
        assert [it["id"] for it in items] == ["B1"]
        assert items[0]["pool"] == "bug"

    def test_only_todo_pool_present(self, tmp_path):
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        items = read_pool(str(tmp_path))
        assert [it["id"] for it in items] == ["T1"]
        assert items[0]["pool"] == "todo"


class TestCrossPoolIdConflicts:
    """人造 B/T 撞号，纯函数层面测 cross_pool_id_conflicts。"""

    def test_no_conflict_when_prefixes_normal(self):
        items = [
            {"id": "B1", "pool": "bug"},
            {"id": "B2", "pool": "bug"},
            {"id": "T1", "pool": "todo"},
        ]
        assert cross_pool_id_conflicts(items) == []

    def test_detects_single_collision_across_pools(self):
        items = [
            {"id": "X1", "pool": "bug"},
            {"id": "X1", "pool": "todo"},
            {"id": "B2", "pool": "bug"},
        ]
        assert cross_pool_id_conflicts(items) == ["X1"]

    def test_detects_multiple_collisions_sorted(self):
        items = [
            {"id": "X2", "pool": "bug"},
            {"id": "X1", "pool": "bug"},
            {"id": "X2", "pool": "todo"},
            {"id": "X1", "pool": "todo"},
        ]
        assert cross_pool_id_conflicts(items) == ["X1", "X2"]

    def test_same_id_within_one_pool_is_not_a_cross_pool_conflict(self):
        """同池内重复不属于 D9 范畴（跨池才算），本函数不该误报。"""
        items = [
            {"id": "B1", "pool": "bug"},
            {"id": "B1", "pool": "bug"},
        ]
        assert cross_pool_id_conflicts(items) == []

    def test_empty_items_returns_empty(self):
        assert cross_pool_id_conflicts([]) == []


class TestReadPoolConflictGuard:
    """Step 4：read_pool 撞到跨池 ID 冲突时报错非静默（D9 防护网接入 join）。"""

    def test_read_pool_raises_on_cross_pool_id_collision(self, tmp_path):
        # 正常 B/T 前缀不会撞号；这里用显式自定义 id 人为制造撞号场景（防护网兜底）。
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "X1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "X1", "status": "OPEN", "change": "x", "batch": ""},
        ])

        with pytest.raises(CrossPoolIDConflict) as exc_info:
            read_pool(str(tmp_path))
        assert "X1" in str(exc_info.value)

    def test_read_pool_conflict_does_not_silently_return_partial_join(self, tmp_path):
        """报错必须是真报错（异常），不能退化成打印警告后仍返回一份撞号数据。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "X1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "X1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        try:
            read_pool(str(tmp_path))
        except CrossPoolIDConflict:
            pass
        else:
            pytest.fail("expected CrossPoolIDConflict to be raised, join returned normally")


class TestTerminalStatusesCrossScriptConsistency:
    """终态集一致性守卫。单一源化（adr/0027）后：bug 终态集 {FIXED,WONTFIX}、todo 终态集
    {DONE,WONTDO} 不再多处内联，唯一源 = `core.POOL_SPEC[pool].terminal_set`，`issues.py`
    的 `TERMINAL_STATUSES` 由其派生、`core` 的 `cmd_scan`/`cmd_triage` 减法表达式也从
    `spec.terminal_set` 取值——故「多处独立硬编码、改一处忘另一处静默漂移」的旧风险已消失。

    本类护住的是派生链两端与外部锚：

    （a）**外部字面锚**：`{"FIXED","WONTFIX"} == TERMINAL_STATUSES["bug"]`（todo 同理）——
    在测试里独立复写字面量，防单一源被整体改错值（同源断言两侧同源、恒真、护力为零，
    真正抓漂移的是这条外部锚）。

    （b）**⊆ 独立 STATUS_CODES**：`TERMINAL_STATUSES[pool] <= set(<recorder>.STATUS_CODES)`
    ——终态词必须真实存在于该 recorder 独立维护的合法状态码表里。

    （c）**派生用法源锚**：`core` 源码里 cmd_scan 的
    `nonterminal = set(spec.status_values) - set(spec.terminal_set)` 字面串在场——守 cmd_scan
    确实走派生（而非回退内联字面量）。
    """

    def test_terminal_sets_are_subset_of_recorder_status_codes(self):
        assert issues_mod.TERMINAL_STATUSES["bug"] <= set(buglist_mod.STATUS_CODES)
        assert issues_mod.TERMINAL_STATUSES["todo"] <= set(todolist_mod.STATUS_CODES)

    def test_terminal_sets_match_expected_literal_values(self):
        assert {"FIXED", "WONTFIX"} == issues_mod.TERMINAL_STATUSES["bug"]
        assert {"DONE", "WONTDO"} == issues_mod.TERMINAL_STATUSES["todo"]

    def test_buglist_inline_terminal_literals_match_issues_constant(self):
        # 单一源化（adr/0027）：bug 终态不再是三份内联字面量——唯一源 = core.POOL_SPEC。
        # 守 core 的 terminal_set 与 issues.TERMINAL_STATUSES 同源一致（后者由前者派生）。
        assert set(buglist_mod._core.POOL_SPEC["bug"].terminal_set) == issues_mod.TERMINAL_STATUSES["bug"]

    def test_todolist_inline_terminal_literals_match_issues_constant(self):
        # 单一源化：见 bug 版注释。
        assert set(todolist_mod._core.POOL_SPEC["todo"].terminal_set) == issues_mod.TERMINAL_STATUSES["todo"]

    def test_buglist_cmd_scan_exclusion_set_strictly_equals_terminal_statuses(self):
        """严格 ==（区别于上面两条测『覆盖』的用例）：cmd_scan 的排除字面量集合
        必须与 issues.TERMINAL_STATUSES['bug'] 严格相等，不能只是超集——防止误把
        非终态码（如 BLOCKED）也塞进这条排除集，导致 nonterminal 计算漏项。"""
        # 单一源化：cmd_scan 的 nonterminal 排除集现由 spec.terminal_set 派生（非内联字面量）。
        core_src = Path(buglist_mod._core.__file__).read_text(encoding="utf-8")
        assert "nonterminal = set(spec.status_values) - set(spec.terminal_set)" in core_src
        assert set(buglist_mod._core.POOL_SPEC["bug"].terminal_set) == issues_mod.TERMINAL_STATUSES["bug"]

    def test_todolist_cmd_scan_exclusion_set_strictly_equals_terminal_statuses(self):
        # 单一源化：见 bug 版注释。
        core_src = Path(todolist_mod._core.__file__).read_text(encoding="utf-8")
        assert "nonterminal = set(spec.status_values) - set(spec.terminal_set)" in core_src
        assert set(todolist_mod._core.POOL_SPEC["todo"].terminal_set) == issues_mod.TERMINAL_STATUSES["todo"]


class TestAtomicWrite:
    """同款原子写 helper（供后续任务写 issues/INDEX.md / issues/batches.md 用）。"""

    def test_writes_content_and_creates_parent_dir(self, tmp_path):
        target = tmp_path / "sub" / "dir" / "file.md"
        atomic_write(str(target), "hello\n")
        assert target.read_text(encoding="utf-8") == "hello\n"

    def test_overwrites_existing_file(self, tmp_path):
        target = tmp_path / "file.md"
        target.write_text("old", encoding="utf-8")
        atomic_write(str(target), "new")
        assert target.read_text(encoding="utf-8") == "new"

    def test_overwrite_preserves_original_file_permissions(self, tmp_path):
        target = tmp_path / "file.md"
        target.write_text("old", encoding="utf-8")
        os.chmod(target, 0o644)
        atomic_write(str(target), "new")
        assert (os.stat(target).st_mode & 0o777) == 0o644

    def test_no_leftover_tmp_file_after_success(self, tmp_path):
        target = tmp_path / "file.md"
        atomic_write(str(target), "content")
        leftovers = [p for p in tmp_path.iterdir() if p.name != "file.md"]
        assert leftovers == []

    def test_original_file_unchanged_when_replace_fails(self, tmp_path, monkeypatch):
        target = tmp_path / "file.md"
        target.write_text("original content", encoding="utf-8")

        def boom(src, dst):
            raise OSError("simulated os.replace failure")

        monkeypatch.setattr(issues_mod.os, "replace", boom)

        with pytest.raises(OSError):
            atomic_write(str(target), "new content that must not land")

        assert target.read_text(encoding="utf-8") == "original content"
        leftovers = [p for p in tmp_path.iterdir() if p.name != "file.md"]
        assert leftovers == []


class TestRepoRoot:
    """Important fix：4 个 cmd_*（reindex / batch add / batch set-status / batch rename）
    此前直接用裸 `args.root`（默认 "."）拼路径，不像 buglist.py/todolist.py 那样探测 git
    根——从非仓库根的子目录调用 issues.py 时会把 `openspec/issues/...` 错误地写到 cwd
    （子目录）而非 git 根，三脚本定位从此不一致。`repo_root` 镜像 buglist.py 的同名实现：
    优先用 git 仓库根，非 git 仓库/git 命令失败时退化为 `os.path.abspath(start)`。"""

    def test_returns_git_toplevel_from_nested_subdirectory(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, text=True, check=True)
        sub = repo / "a" / "b"
        sub.mkdir(parents=True)

        result = repo_root(str(sub))

        assert Path(result).resolve() == repo.resolve()

    def test_returns_git_toplevel_when_start_is_the_root_itself(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, text=True, check=True)

        result = repo_root(str(repo))

        assert Path(result).resolve() == repo.resolve()

    def test_falls_back_to_abspath_when_git_command_raises(self, tmp_path, monkeypatch):
        # `**kwargs`：repo_root 现在还会传 env= / timeout=，写死签名会 TypeError。
        # 只补桩签名，不改被测行为（回落分支仍应返回 abspath(start)）。
        def boom(cmd, **kwargs):
            raise subprocess.CalledProcessError(128, cmd)

        monkeypatch.setattr(issues_mod.subprocess, "run", boom)

        result = repo_root(str(tmp_path))

        assert result == os.path.abspath(str(tmp_path))

    def test_falls_back_to_abspath_outside_any_git_repo(self, tmp_path):
        """非 mock 版本：pytest 的 tmp_path 本身不在任何 git 仓库树内，应直接退化为
        abspath，不抛异常——与既有测试套件（直接把 tmp_path 传给 cmd_reindex 等命令，
        断言 `openspec/issues/...` 落在 tmp_path 下）隐含的前提一致。"""
        result = repo_root(str(tmp_path))
        assert result == os.path.abspath(str(tmp_path))


class TestRepoRootIntegrationAcrossSubcommands:
    """CLI 级验证（不只测 repo_root 纯函数本身）：`--root` 指向 git 仓库内的子目录时，
    reindex / batch add 等命令应把 `openspec/issues/...` 落到 git 根，而不是落在调用时
    传入的子目录（回归 Important finding：三脚本定位不一致）。"""

    def test_reindex_writes_index_to_git_root_not_passed_subdir(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, text=True, check=True)
        _write_bug_file(repo, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        sub = repo / "nested" / "dir"
        sub.mkdir(parents=True)

        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(sub), "reindex"],
            capture_output=True, text=True,
        )

        assert proc.returncode == 0, proc.stderr
        assert (repo / "openspec" / "issues" / "INDEX.md").exists()
        assert not (sub / "openspec").exists()

    def test_batch_add_writes_batches_md_to_git_root_not_passed_subdir(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, text=True, check=True)
        sub = repo / "nested" / "dir"
        sub.mkdir(parents=True)

        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(sub), "batch", "add", "batch-1"],
            capture_output=True, text=True,
        )

        assert proc.returncode == 0, proc.stderr
        assert (repo / "openspec" / "issues" / "batches.md").exists()
        assert not (sub / "openspec").exists()


class TestReadPoolSubprocessFailure:
    """carry-over（Task 8 遗留）：某子进程（buglist.py/todolist.py）scan --json 返回
    非零退出码时，read_pool 必须抛 RuntimeError（不静默吞掉、不返回半截 join 结果）。"""

    def test_read_pool_raises_runtime_error_when_subprocess_exits_nonzero(
        self, tmp_path, monkeypatch, scan_only_run
    ):
        class _FakeProc:
            returncode = 1
            stdout = ""
            stderr = "simulated subprocess failure"

        # 按 argv 分派（单一源见 conftest）：只拦 recorder 的 scan 子进程，其余
        # （含 repo_root 的 `git rev-parse`）透传真实行为——整体替换会连带劫持被测
        # 函数之外的调用，用例退化为假绿。
        monkeypatch.setattr(
            issues_mod.subprocess, "run", scan_only_run(lambda _command: _FakeProc())
        )

        with pytest.raises(RuntimeError) as exc_info:
            read_pool(str(tmp_path))
        assert "simulated subprocess failure" in str(exc_info.value)


class TestReindexGeneratesIndexMd:
    """Task 9：reindex 生成 issues/INDEX.md（banner + 原子写 + open×批次 board + 幂等）。"""

    def test_index_first_line_is_generated_banner(self, tmp_path):
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "change-a", "batch": "batch-1"},
        ])
        _run_reindex(tmp_path)
        content = _read_index(tmp_path)
        assert content.splitlines()[0] == (
            "<!-- GENERATED by issues.py reindex — DO NOT EDIT -->"
        )

    def test_open_items_grouped_by_batch_and_unbatched_group_separate(self, tmp_path):
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "change-a", "batch": "batch-1"},
            {"id": "B2", "status": "OPEN", "change": "change-a", "batch": ""},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "change-a", "batch": "batch-1"},
        ])
        _run_reindex(tmp_path)
        content = _read_index(tmp_path)

        assert "batch-1" in content
        assert "| B1 |" in content
        assert "| T1 |" in content
        assert "| B2 |" in content
        assert "未分组" in content

        # B1/T1 (batch-1) 应出现在 B2（未分组）之前的分组段落里
        batch_idx = content.index("batch-1")
        unbatched_idx = content.index("未分组")
        assert batch_idx < unbatched_idx

    def test_terminal_items_excluded_from_open_board_but_counted_in_closed_summary(
        self, tmp_path
    ):
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "change-a", "batch": "batch-1"},
            {"id": "B2", "status": "FIXED", "change": "change-a", "batch": "batch-1"},
            {"id": "B3", "status": "WONTFIX", "change": "change-a", "batch": ""},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "T1", "status": "DONE", "change": "change-a", "batch": ""},
            {"id": "T2", "status": "OPEN", "change": "change-a", "batch": ""},
        ])
        _run_reindex(tmp_path)
        content = _read_index(tmp_path)

        open_section, _, closed_section = content.partition("已闭合")
        assert "B1" in open_section
        assert "T2" in open_section
        # 终态项不出现在 open 板段落里
        assert "B2" not in open_section
        assert "B3" not in open_section
        assert "T1" not in open_section
        # 已闭合摘要含总数（3 项：B2/B3/T1）
        assert "3" in closed_section

    def test_reindex_is_idempotent_byte_identical_on_rerun(self, tmp_path):
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "change-a", "batch": "batch-1"},
            {"id": "B2", "status": "FIXED", "change": "change-a", "batch": "batch-1"},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "change-a", "batch": ""},
        ])
        _run_reindex(tmp_path)
        first = _read_index_bytes(tmp_path)
        _run_reindex(tmp_path)
        second = _read_index_bytes(tmp_path)
        assert first == second

    def test_reindex_raises_on_cross_pool_id_conflict(self, tmp_path):
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "X1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "X1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "reindex"],
            capture_output=True, text=True,
        )
        assert proc.returncode != 0
        assert proc.stderr.strip() != ""
        assert not (tmp_path / "openspec" / "issues" / "INDEX.md").exists()


class TestReindexProblemsEcho:
    """Task 5（T1）：`_scan_pool` 此前静默丢弃两池 `scan --json` 各自的 `problems`
    （表↔块不一致等一致性自检结果）——reindex 应把它们回显到 stderr，默认仍 exit 0
    （problems 不阻断 reindex 本该做的重建），只有显式 `--strict` 时才让存在 problems
    的这次调用以非 0 退出。"""

    def test_reindex_echoes_problems_to_stderr_exit0(self, tmp_path):
        # _write_bug_file 只写总览表行、不写对应的 "## B1:" 详细块——buglist.py 的
        # scan 会把这判成"表有 B1 但缺详细块"问题（见 buglist.py cmd_scan），这条
        # problem 此前在 issues.py 的 read_pool/_scan_pool 里被静默丢弃。
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        fixture = tmp_path / "openspec/issues/buglist/2026-01-01-buglist.md"
        fixture.write_text(fixture.read_text(encoding="utf-8").split("\n---\n", 1)[0] + "\n",
                           encoding="utf-8")

        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "reindex"],
            capture_output=True, text=True,
        )

        assert proc.returncode == 0, proc.stderr
        assert "B1" in proc.stderr
        assert "缺详细块" in proc.stderr
        # problems 回显不影响 reindex 本该完成的重建
        assert (tmp_path / "openspec" / "issues" / "INDEX.md").exists()

    def test_reindex_strict_exits_nonzero_on_problems(self, tmp_path):
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        fixture = tmp_path / "openspec/issues/buglist/2026-01-01-buglist.md"
        fixture.write_text(fixture.read_text(encoding="utf-8").split("\n---\n", 1)[0] + "\n",
                           encoding="utf-8")

        # 无 --strict：exit 0（沿用默认口径）
        proc_default = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "reindex"],
            capture_output=True, text=True,
        )
        assert proc_default.returncode == 0, proc_default.stderr

        # 有 --strict + 仍存在 problems：exit 非 0
        proc_strict = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "reindex", "--strict"],
            capture_output=True, text=True,
        )
        assert proc_strict.returncode != 0
        assert "B1" in proc_strict.stderr
        # INDEX.md 仍应已被重建（--strict 只影响退出码，不影响重建本身）
        assert (tmp_path / "openspec" / "issues" / "INDEX.md").exists()

    def test_reindex_strict_exits_zero_when_no_problems(self, tmp_path):
        """--strict 只在存在 problems 时才收紧退出码——干净数据不受影响。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        # 补上 B1 的详细块，避免"表↔块不一致"这条 problem 触发。
        path = tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md"
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n---\n\n## B1: fixture\n\n| 字段 | 值 |\n|------|----|\n| 状态 | OPEN |\n")

        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "reindex", "--strict"],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
        assert proc.stderr.strip() == ""


class TestArgparseSkeleton:
    """argparse 骨架含 reindex/batch 两子命令（reindex 真实现见 Task 9；batch 真实现见 Task 10——
    仅 `batch` 不带任何子操作时仍应非静默报错，见 test_batch_subcommand_without_action_errors_non_silently）。"""

    def test_help_lists_reindex_and_batch(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--help"], capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
        assert "reindex" in proc.stdout
        assert "batch" in proc.stdout

    def test_reindex_subcommand_runs_on_empty_root_and_creates_index(self, tmp_path):
        """Task 9：reindex 不再是占位——空 root（两池都无 dated 文件）应成功生成一份
        只含 banner + 空板 + 0 已闭合的 INDEX.md（非报错，占位行为已被真实现取代）。
        真正的报错场景（跨池 ID 冲突）见 TestReindexGeneratesIndexMd。"""
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "reindex"],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
        assert (tmp_path / "openspec" / "issues" / "INDEX.md").exists()

    def test_batch_subcommand_without_action_errors_non_silently(self, tmp_path):
        """`batch` 缺子操作（add/set-status/rename 三选一，Task 10 起为必填的嵌套 subparser）
        仍要非静默报错——不是 Task 8 那种"整条 batch 都占位"了，而是 argparse 层面的必填校验。"""
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "batch"],
            capture_output=True, text=True,
        )
        assert proc.returncode != 0
        assert proc.stderr.strip() != ""

    def test_missing_subcommand_errors(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT], capture_output=True, text=True,
        )
        assert proc.returncode != 0


class TestBatchAdd:
    """Task 10：`batch add {key}` 新建 PLANNED 条目，成员空；人写字段按参数写，缺省留占位。"""

    def test_add_creates_planned_entry_with_empty_members_and_given_fields(self, tmp_path):
        _run_batch(tmp_path, ["add", "batch-1", "--title", "清理项",
                               "--优先级", "P1", "--计划", "先清 P0/P1"])
        content = _read_batches(tmp_path)
        assert "### batch-1 — 清理项" in content
        assert "状态: PLANNED" in content
        assert "成员: (生成)" in content
        assert "优先级: P1" in content
        assert "计划: 先清 P0/P1" in content

    def test_add_without_optional_fields_uses_placeholder_and_key_as_title(self, tmp_path):
        _run_batch(tmp_path, ["add", "batch-2"])
        content = _read_batches(tmp_path)
        assert "### batch-2 — batch-2" in content
        assert "状态: PLANNED" in content
        assert "优先级: <待填>" in content
        assert "计划: <待填>" in content

    def test_add_duplicate_key_errors_non_silently(self, tmp_path):
        _run_batch(tmp_path, ["add", "batch-1"])
        proc = _run_batch_raw(tmp_path, ["add", "batch-1"])
        assert proc.returncode != 0
        assert proc.stderr.strip() != ""
        # 不覆写——原条目仍在、只出现一次
        content = _read_batches(tmp_path)
        assert content.count("### batch-1") == 1

    def test_add_two_entries_both_present(self, tmp_path):
        _run_batch(tmp_path, ["add", "batch-1"])
        _run_batch(tmp_path, ["add", "batch-2"])
        content = _read_batches(tmp_path)
        assert "### batch-1 — batch-1" in content
        assert "### batch-2 — batch-2" in content

    def test_batch_add_rejects_emdash_delimiter_in_key(self, tmp_path):
        """OV-2：header 是 `### {key} — {title}`（em dash U+2014 分隔）——key 本身若含
        ` — `，`_BATCH_HEADER_RE` 会把它切坏（key 被截断成分隔符之前的部分），
        `_find_batch_entry_range` 之后再也找不到完整原 key。必须 fail-closed，而不是
        静默写入一个会腐蚀后续解析的条目。"""
        proc = _run_batch_raw(tmp_path, ["add", "a — b"])
        assert proc.returncode != 0
        assert proc.stderr.strip() != ""
        assert not _batches_path(tmp_path).exists()

    def test_batch_add_rejects_leading_trailing_space_in_key(self, tmp_path):
        proc = _run_batch_raw(tmp_path, ["add", " batch-1 "])
        assert proc.returncode != 0
        assert proc.stderr.strip() != ""

    def test_batch_add_rejects_newline_in_title(self, tmp_path):
        proc = _run_batch_raw(tmp_path, ["add", "batch-1", "--title", "evil\ntitle"])
        assert proc.returncode != 0
        assert proc.stderr.strip() != ""
        assert not _batches_path(tmp_path).exists()


class TestBatchAddKeyEmptyGuard:
    """[impl-review-fix] FIX-3（领域 F1 PoC）：`_reject_batch_key_unsafe` 此前的
    `str(key) != str(key).strip()` 检查对空字符串恒为 False（`"".strip() == ""`），
    空/纯空白 key 会被放行，写出 `###  — title` 这种 key 位置是空白的 header——
    `_BATCH_HEADER_RE` 的 `(?P<key>.+?)` 要求至少一个字符，永远解析不回这个 key，
    是个从写入那一刻起就读不回来的僵尸条目。add/rename 两个写 header 的入口都要挡。"""

    def test_batch_add_rejects_empty_key(self, tmp_path):
        proc = _run_batch_raw(tmp_path, ["add", ""])
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        assert not _batches_path(tmp_path).exists()

    def test_batch_add_rejects_whitespace_only_key(self, tmp_path):
        proc = _run_batch_raw(tmp_path, ["add", "   "])
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr

    def test_batch_rename_rejects_empty_new_key(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### real — 标题\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        proc = _run_batch_raw(tmp_path, ["rename", "real", ""])
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        # 未被腐蚀：原条目仍在
        content = _read_batches(tmp_path)
        assert "### real — 标题" in content


class TestBatchAddCellSafety:
    """[impl-review-fix] FIX-5（CV-2 codex PoC）：`cmd_batch_add` 把 优先级/计划 原样
    写进 `f"优先级: {priority}\\n"`/`f"计划: {plan}\\n"` 单行，此前未挂
    batch line guard——含换行的值能在 batches.md 里注入一整条伪造的
    `### … — …` header 行，被 `_BATCH_HEADER_RE` 当成新批次条目解析出来。"""

    def test_batch_add_rejects_newline_in_priority(self, tmp_path):
        proc = _run_batch_raw(
            tmp_path, ["add", "k", "--优先级", "P1\n### evil — x"]
        )
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        path = _batches_path(tmp_path)
        if path.exists():
            assert "evil" not in path.read_text(encoding="utf-8")

    def test_batch_add_rejects_newline_in_plan(self, tmp_path):
        proc = _run_batch_raw(
            tmp_path, ["add", "k", "--计划", "一句话\n### evil — x"]
        )
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        path = _batches_path(tmp_path)
        if path.exists():
            assert "evil" not in path.read_text(encoding="utf-8")

    def test_batch_add_rejects_pipe_in_priority(self, tmp_path):
        proc = _run_batch_raw(tmp_path, ["add", "k", "--优先级", "P1 | evil"])
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr


class TestBatchAddIfExistsSkip:
    """Task 7（T4）：`batch add --if-exists skip` = skip-with-warn——遇已存在同 key
    直接 no-op + exit 0 + stderr 警告，**不做字段比较、不解析人写行**（match-or-error
    方案已被 spec-review 否掉：placeholder `<待填>` vs 补填会造 UX 死胡同）。skip 是
    opt-in，忽略字段是其声明语义，不是缺陷。"""

    def test_batch_add_if_exists_skip_warns_and_noops(self, tmp_path):
        _run_batch(tmp_path, ["add", "batch-1", "--title", "原标题"])
        proc = _run_batch_raw(tmp_path, ["add", "batch-1", "--if-exists", "skip"])
        assert proc.returncode == 0, proc.stderr
        assert "已存在" in proc.stderr
        assert "忽略" in proc.stderr
        content = _read_batches(tmp_path)
        # no-op：原条目未变，未被重复写入
        assert content.count("### batch-1") == 1
        assert "### batch-1 — 原标题" in content

    def test_batch_add_if_exists_skip_ignores_fields_no_die(self, tmp_path):
        _run_batch(tmp_path, ["add", "batch-1"])
        proc = _run_batch_raw(
            tmp_path,
            ["add", "batch-1", "--优先级", "P1", "--if-exists", "skip"],
        )
        assert proc.returncode == 0, proc.stderr
        assert proc.stderr.strip() != ""
        content = _read_batches(tmp_path)
        # 字段参数被忽略（声明语义，不是比较后判定"无变化"）：原占位符未被 P1 覆盖
        assert "优先级: <待填>" in content
        assert "优先级: P1" not in content

    def test_batch_add_without_if_exists_still_dies(self, tmp_path):
        """未传 --if-exists 时保原行为（撞 key 报错，非 no-op）——skip 是 opt-in。"""
        _run_batch(tmp_path, ["add", "batch-1"])
        proc = _run_batch_raw(tmp_path, ["add", "batch-1"])
        assert proc.returncode != 0
        assert proc.stderr.strip() != ""
        content = _read_batches(tmp_path)
        assert content.count("### batch-1") == 1


class TestBatchSetStatus:
    """Task 10：`batch set-status {key} {S}` 只改该条目的 `状态:` 生成行，不动人写行/成员行。"""

    def test_set_status_changes_status_line(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n",
            "状态: PLANNED\n",
            "成员: (生成) B1, T2\n",
            "优先级: P1\n",
            "计划: 先清 P0/P1\n",
        ])
        _run_batch(tmp_path, ["set-status", "batch-1", "IN_PROGRESS"])
        content = _read_batches(tmp_path)
        assert "状态: IN_PROGRESS" in content
        assert "状态: PLANNED" not in content

    def test_set_status_does_not_touch_members_generated_line(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n",
            "状态: PLANNED\n",
            "成员: (生成) B1, T2\n",
            "优先级: P1\n",
            "计划: 先清 P0/P1\n",
        ])
        _run_batch(tmp_path, ["set-status", "batch-1", "DONE"])
        content = _read_batches(tmp_path)
        # 成员行是另一条生成行，set-status（Task 10）不该碰它——那是 reindex（Task 11）的职责
        assert "成员: (生成) B1, T2" in content

    def test_set_status_unknown_key_errors(self, tmp_path):
        _write_batches_md(tmp_path, ["### batch-1 — x\n", "状态: PLANNED\n"])
        proc = _run_batch_raw(tmp_path, ["set-status", "nope", "DONE"])
        assert proc.returncode != 0
        assert proc.stderr.strip() != ""

    def test_set_status_invalid_status_code_errors(self, tmp_path):
        _write_batches_md(tmp_path, ["### batch-1 — x\n", "状态: PLANNED\n"])
        proc = _run_batch_raw(tmp_path, ["set-status", "batch-1", "WEIRD"])
        assert proc.returncode != 0


class TestBatchSetStatusPreservesHandwrittenLines:
    """Step 4（Q3 载重约束核心）：预置含 `优先级:`/`计划:` 的 batches.md，跑 `batch set-status`，
    断言人写行逐字保留——包括含中文标点、括号、# 等"看起来像会被误解析"的内容。"""

    def test_handwritten_lines_survive_set_status_verbatim(self, tmp_path):
        handwritten_priority = "优先级: P0（阻断发布，本周必须清）\n"
        handwritten_plan = "计划: 只清 B/T 里 P0/P1，其它挪到下个批次；备注见 #123，含冒号: 不能被拆坏\n"
        _write_batches_md(tmp_path, [
            "### batch-1 — 紧急清理\n",
            "状态: PLANNED\n",
            "成员: (生成) B1\n",
            handwritten_priority,
            handwritten_plan,
        ])
        _run_batch(tmp_path, ["set-status", "batch-1", "DONE"])
        content = _read_batches(tmp_path)
        assert handwritten_priority in content
        assert handwritten_plan in content
        assert "状态: DONE" in content

    def test_handwritten_lines_survive_two_consecutive_set_status_calls(self, tmp_path):
        """连续两次 set-status（PLANNED→IN_PROGRESS→DONE），人写行全程逐字未变。"""
        handwritten_priority = "优先级: P2\n"
        handwritten_plan = "计划: 一句范围，别改我\n"
        _write_batches_md(tmp_path, [
            "### batch-1 — 常规清理\n",
            "状态: PLANNED\n",
            "成员: (生成)\n",
            handwritten_priority,
            handwritten_plan,
        ])
        _run_batch(tmp_path, ["set-status", "batch-1", "IN_PROGRESS"])
        _run_batch(tmp_path, ["set-status", "batch-1", "DONE"])
        content = _read_batches(tmp_path)
        assert handwritten_priority in content
        assert handwritten_plan in content
        assert "状态: DONE" in content


class TestBatchRename:
    """Task 10：`batch rename {old} {new}` 改条目 key + 同步 item 池里所有 批次==old 的 tag（跨两池）。"""

    def test_rename_changes_key_and_preserves_handwritten_lines(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### old-batch — 清理项\n",
            "状态: PLANNED\n",
            "成员: (生成) B1\n",
            "优先级: P1\n",
            "计划: 一句范围\n",
        ])
        _run_batch(tmp_path, ["rename", "old-batch", "new-batch"])
        content = _read_batches(tmp_path)
        assert "### new-batch — 清理项" in content
        assert "### old-batch —" not in content
        assert "重命名自: old-batch" in content
        assert "优先级: P1" in content
        assert "计划: 一句范围" in content

    def test_rename_syncs_item_batch_tag_in_bug_pool_only_matching_items(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### old-batch — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "old-batch"},
            {"id": "B2", "status": "OPEN", "change": "x", "batch": "other-batch"},
        ])
        _run_batch(tmp_path, ["rename", "old-batch", "new-batch"])
        text = (tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md").read_text(
            encoding="utf-8")
        b1_line = next(l for l in text.splitlines() if l.strip().startswith("| B1"))
        b2_line = next(l for l in text.splitlines() if l.strip().startswith("| B2"))
        assert "old-batch" in b1_line  # frozen legacy snapshot 永不 patch
        assert _item_batch(tmp_path, "B1") == "new-batch"  # overlay 是当前值
        assert "other-batch" in b2_line  # 不同批次的项不受影响

    def test_rename_syncs_item_batch_tag_in_todo_pool(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### old-batch — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": "old-batch"},
        ])
        _run_batch(tmp_path, ["rename", "old-batch", "new-batch"])
        text = (tmp_path / "openspec" / "issues" / "todolist" / "2026-01-todolist.md").read_text(
            encoding="utf-8")
        t1_line = next(l for l in text.splitlines() if l.strip().startswith("| T1"))
        assert "old-batch" in t1_line  # frozen legacy snapshot 永不 patch
        assert _item_batch(tmp_path, "T1") == "new-batch"

    def test_rename_syncs_across_both_pools_in_one_call(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### old-batch — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "old-batch"},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": "old-batch"},
        ])
        _run_batch(tmp_path, ["rename", "old-batch", "new-batch"])
        bug_text = (tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md").read_text(
            encoding="utf-8")
        todo_text = (tmp_path / "openspec" / "issues" / "todolist" / "2026-01-todolist.md").read_text(
            encoding="utf-8")
        assert "old-batch" in next(l for l in bug_text.splitlines() if l.strip().startswith("| B1"))
        assert "old-batch" in next(l for l in todo_text.splitlines() if l.strip().startswith("| T1"))
        assert _item_batch(tmp_path, "B1") == "new-batch"
        assert _item_batch(tmp_path, "T1") == "new-batch"

    def test_rename_does_not_flip_item_status(self, tmp_path):
        """rename 只改批次 tag，不该像 triage 那样顺带把未分诊开放态推成 PROPOSED——
        这是 rename 不复用 triage 子命令的原因（区别于其状态推进副作用）。"""
        _write_batches_md(tmp_path, [
            "### old-batch — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "old-batch"},
        ])
        _run_batch(tmp_path, ["rename", "old-batch", "new-batch"])
        text = (tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md").read_text(
            encoding="utf-8")
        b1_line = next(l for l in text.splitlines() if l.strip().startswith("| B1"))
        assert "| OPEN |" in b1_line

    def test_rename_unknown_old_key_errors_non_silently(self, tmp_path):
        _write_batches_md(tmp_path, ["### batch-1 — x\n", "状态: PLANNED\n"])
        proc = _run_batch_raw(tmp_path, ["rename", "nope", "new"])
        assert proc.returncode != 0
        assert proc.stderr.strip() != ""

    def test_rename_to_already_existing_key_errors_does_not_merge(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### a — A\n", "状态: PLANNED\n", "成员: (生成)\n", "优先级: P1\n", "计划: x\n",
            "### b — B\n", "状态: PLANNED\n", "成员: (生成)\n", "优先级: P1\n", "计划: x\n",
        ])
        proc = _run_batch_raw(tmp_path, ["rename", "a", "b"])
        assert proc.returncode != 0
        content = _read_batches(tmp_path)
        # 两条目都还在，未被合并
        assert "### a — A" in content
        assert "### b — B" in content

    def test_batch_rename_rejects_pipe_in_new_key(self, tmp_path):
        """batch key 仍写 Markdown registry header，含 `|` 必须在任何 registry/frontmatter
        写盘前 fail-closed；legacy row 作为 frozen snapshot 保持不变。"""
        _write_batches_md(tmp_path, [
            "### old-batch — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "old-batch"},
        ])
        proc = _run_batch_raw(tmp_path, ["rename", "old-batch", "evil|key"])
        assert proc.returncode != 0
        assert proc.stderr.strip() != ""
        text = (tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md").read_text(
            encoding="utf-8")
        b1_line = next(l for l in text.splitlines() if l.strip().startswith("| B1"))
        assert "evil|key" not in b1_line
        assert "old-batch" in b1_line

    def test_batch_rename_rejects_newline_in_new_key(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### old-batch — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "old-batch"},
        ])
        proc = _run_batch_raw(tmp_path, ["rename", "old-batch", "evil\n| EVIL | ROW |"])
        assert proc.returncode != 0
        text = (tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md").read_text(
            encoding="utf-8")
        assert "EVIL" not in text

    def test_batch_rename_rejects_emdash_delimiter_in_new_key(self, tmp_path):
        """OV-2：new_key 含 ` — `（em dash 分隔符）会破坏 batches.md header 解析
        （同 test_batch_add_rejects_emdash_delimiter_in_key 的理由）。必须在写盘
        （改 batches.md header / 同步 dated 文件批次列）之前 fail-closed，
        且不能有任何部分写入（old-batch 原样保留、dated 文件不被同步改动）。"""
        _write_batches_md(tmp_path, [
            "### old-batch — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "old-batch"},
        ])
        proc = _run_batch_raw(tmp_path, ["rename", "old-batch", "a — b"])
        assert proc.returncode != 0
        assert proc.stderr.strip() != ""
        content = _read_batches(tmp_path)
        assert "### old-batch — 清理项" in content
        text = (tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md").read_text(
            encoding="utf-8")
        b1_line = next(l for l in text.splitlines() if l.strip().startswith("| B1"))
        assert "old-batch" in b1_line


class TestBatchRenameAutoReindex:
    """`batch rename` 必须复用 updated snapshot 刷新 INDEX/batches；完全收敛前任何
    reindex failure 都 non-zero，并携带原命令恢复信息。"""

    def test_batch_rename_auto_reindex_refreshes_index(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### old-batch — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "old-batch"},
        ])

        _run_batch(tmp_path, ["rename", "old-batch", "new-batch"])

        content = _read_index(tmp_path)
        assert "批次：new-batch" in content
        assert "| B1 |" in content
        assert "批次：old-batch" not in content

    def test_batch_rename_reindex_failure_is_nonzero_with_recovery_command(
        self, tmp_path, monkeypatch
    ):
        """完全收敛前 reindex failure 必须 fail-closed，并给原命令恢复信息。"""
        _write_batches_md(tmp_path, [
            "### old-batch — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "old-batch"},
        ])

        def boom(root, snapshot=None):
            raise RuntimeError("simulated reindex failure")

        monkeypatch.setattr(issues_mod, "_reindex_core", boom)

        args = types.SimpleNamespace(root=str(tmp_path), old="old-batch", new="new-batch")
        with pytest.raises(ValueError) as exc_info:
            issues_mod.cmd_batch_rename(args)
        diagnostic = str(exc_info.value)
        assert "stage=reindex" in diagnostic
        assert "batch rename old-batch new-batch" in diagnostic

        # rename 本体已生效（写盘发生在 reindex 调用之前）
        content = _read_batches(tmp_path)
        assert "### new-batch — 清理项" in content


class TestBatchRenameAutoReindexProblemsEcho:
    """[impl-review-fix] FIX-4（领域 F2 + 对抗 B-F1 PoC）：`cmd_batch_rename` 的
    auto-reindex 此前 `try: _reindex_core(root)` 丢弃返回的 `(items, problems)`——
    reindex 成功但两池 scan 测出 problems（如 OV-1 行 arity 异常）非空时，rename
    完全不吐这个信号（静默蒸发）。现在必须把 problems 逐条回显到 stderr。"""

    def test_batch_rename_echoes_reindex_problems_to_stderr(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### old-batch — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        dir_path = tmp_path / "openspec" / "issues" / "buglist"
        dir_path.mkdir(parents=True)
        content = (
            "# 2026-01-01 Buglist\n\n"
            "> 来源：test\n"
            "> 创建日期：2026-01-01\n\n"
            "## 状态总览\n\n"
            "| ID | 模块 | 问题摘要 | 优先级 | 状态 | 时间 | 关联Change | 批次 |\n"
            "|----|------|----------|--------|------|------|------------|------|\n"
            "| B1 | `foo.c:1` | fixture | P2 | OPEN | 10:00 | x | old-batch |\n"
            "| B2 | `foo.c:1` | unrelated | P2 | OPEN | 10:00 | x | other-batch | trailing |\n"
            "\n## B1: fixture\n\n**现象**：target block is valid\n"
        )
        (dir_path / "2026-01-01-buglist.md").write_text(content, encoding="utf-8")

        proc = _run_batch_raw(tmp_path, ["rename", "old-batch", "new-batch"])
        assert proc.returncode == 0, proc.stderr
        assert "arity" in proc.stderr
        assert "B2" in proc.stderr


class TestReindexSyncBatchesMembers:
    """Task 11 载重约束 1（成员填充）：reindex 按 item 的批次 tag 聚合成员，
    填 batches.md 每批的 `成员:` 生成行，成员 id 排序确定。"""

    def test_reindex_fills_members_line_sorted_by_id_across_both_pools(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "batch-1"},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "T2", "status": "OPEN", "change": "x", "batch": "batch-1"},
        ])
        _run_reindex(tmp_path)
        content = _read_batches(tmp_path)
        assert "成员: (生成) B1, T2" in content


class TestReindexBatchDoneCriterion:
    """Task 11 载重约束 2（D1 关键判据）：成员数 ≥1 且全部进入各自 pool 终态集
    （bug: FIXED/WONTFIX；todo: DONE/WONTDO）→ `状态:` 生成行同步为 DONE。"""

    def test_all_members_fixed_or_done_marks_batch_done(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "FIXED", "change": "x", "batch": "batch-1"},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "T1", "status": "DONE", "change": "x", "batch": "batch-1"},
        ])
        _run_reindex(tmp_path)
        content = _read_batches(tmp_path)
        assert "状态: DONE" in content
        assert "状态: PLANNED" not in content


class TestReindexBatchDoneCriterionIncludesWontVariants:
    """Task 11 载重约束 3：成员全是 FIXED/WONTFIX/DONE/WONTDO（含 WONT*）也算
    完成 → DONE（WONT* 是合法闭合）。"""

    def test_all_members_terminal_via_wont_variants_marks_done(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "WONTFIX", "change": "x", "batch": "batch-1"},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "T1", "status": "WONTDO", "change": "x", "batch": "batch-1"},
        ])
        _run_reindex(tmp_path)
        content = _read_batches(tmp_path)
        assert "状态: DONE" in content


class TestReindexZeroMemberBatchStaysPlanned:
    """Task 11 载重约束 2（D1 反例）：0 成员批次 MUST 保持 PLANNED——防 vacuous-truth
    假 DONE（全称量词对空集永真，必须显式排除成员数=0）。"""

    def test_zero_member_batch_not_marked_done(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        # 无任何 item 引用 batch-1（两池都不写 dated 文件）
        _run_reindex(tmp_path)
        content = _read_batches(tmp_path)
        assert "状态: PLANNED" in content
        assert "状态: DONE" not in content
        assert "成员: (生成)" in content


class TestReindexZeroMemberBatchHumanInProgressStaysInProgress:
    """T5（本次任务）补测：0 成员批次若人工用 `batch set-status` 标为 IN_PROGRESS（既非
    DONE 也非完成判据要求的 PLANNED），reindex 不该动它——`_sync_one_entry` 对
    `is_complete=False` 分支只在 `status_val == "DONE"` 时才追加 ⚠️ 警告，其余任何人写
    状态值（含 IN_PROGRESS）原样保留。这与 TestReindexZeroMemberBatchStaysPlanned
    是同一条代码路径（该测试只覆盖了 PLANNED 这一个具体值），此处换一个状态值补证
    "不特判某个字面状态"，不是新分支。"""

    def test_zero_member_batch_marked_in_progress_by_human_not_reset_by_reindex(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _run_batch(tmp_path, ["set-status", "batch-1", "IN_PROGRESS"])
        # 无任何 item 引用 batch-1（两池都不写 dated 文件）——0 成员
        _run_reindex(tmp_path)
        content = _read_batches(tmp_path)
        assert "状态: IN_PROGRESS" in content
        assert "状态: DONE" not in content
        assert "状态: PLANNED" not in content
        assert "⚠️ 不一致" not in content
        assert "成员: (生成)" in content


class TestReindexDoesNotOverrideHumanDoneStatus:
    """Task 11 载重约束 4（Q3 不越权纠正）：批次 batches.md 里标了 DONE 但成员未全进
    终态（有 OPEN 等）→ reindex 只追加 `⚠️ 不一致` 警告，绝不改人写的 `状态:` 值。"""

    def test_appends_warning_but_keeps_human_done_value_unchanged(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n", "状态: DONE\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "batch-1"},
        ])
        _run_reindex(tmp_path)
        content = _read_batches(tmp_path)
        assert "状态: DONE" in content  # 人写值不被改回 PLANNED/其它
        assert "⚠️ 不一致" in content


class TestReindexOrphanBatchTag:
    """Task 11 载重约束 5（Q2/D5 orphan）：item 有批次 tag 但 batches.md 无此 key →
    reindex stderr 显式报警、不静默生成 ghost 批次条目。"""

    def test_orphan_batch_tag_warns_on_stderr_without_creating_ghost_entry(self, tmp_path):
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "ghost-batch"},
        ])
        proc = _run_reindex(tmp_path)
        assert "ghost-batch" in proc.stderr
        assert "orphan" in proc.stderr
        # 不静默生成 ghost 条目：batches.md 压根不该被凭空建出来
        assert not (tmp_path / "openspec" / "issues" / "batches.md").exists()

    def test_orphan_batch_tag_when_batches_md_has_other_entries_does_not_add_ghost_key(
        self, tmp_path
    ):
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n", "状态: PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "ghost-batch"},
        ])
        proc = _run_reindex(tmp_path)
        assert "ghost-batch" in proc.stderr
        content = _read_batches(tmp_path)
        assert "ghost-batch" not in content
        assert "### batch-1" in content


class TestReindexBatchesSyncIdempotent:
    """Task 11 载重约束 6：整体 reindex 幂等——连跑两次 batches.md 逐字节稳定，
    ⚠️ 不一致 行不累积重复。"""

    def test_warning_line_not_duplicated_and_batches_md_byte_stable_on_rerun(self, tmp_path):
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n", "状态: DONE\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "batch-1"},
        ])
        _run_reindex(tmp_path)
        first = _read_batches(tmp_path)
        _run_reindex(tmp_path)
        second = _read_batches(tmp_path)
        assert first == second
        assert first.count("⚠️ 不一致") == 1


class TestReindexStatusLineFullwidthColonCarry:
    """Task 11 载重约束 7（Task 10 carry）：`状态：`（全角冒号）人手误按也要被解析
    识别（放宽正则兼容全/半角），不静默留僵尸行（不会额外插入第二条状态行）。"""

    def test_fullwidth_colon_status_line_recognized_and_normalized_no_duplicate(
        self, tmp_path
    ):
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n", "状态： PLANNED\n", "成员: (生成)\n",
            "优先级: P1\n", "计划: x\n",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "FIXED", "change": "x", "batch": "batch-1"},
        ])
        _run_reindex(tmp_path)
        content = _read_batches(tmp_path)
        status_lines = [l for l in content.splitlines() if l.startswith("状态")]
        assert len(status_lines) == 1
        assert status_lines[0] == "状态: DONE"


class TestReindexBatchesMdMissingTrailingNewline:
    """Critical fix 回归：`batches.md` 文件末尾缺尾随换行（半手维护文件常见——
    `readlines()` 会让最后一行不以 `\\n` 结尾）时，`⚠️ 不一致` 警告行的插入不得
    粘连到人写行——粘连既腐蚀人写行内容（违 Q3 不覆写人写行），又让粘连后的 ⚠️ 行
    不再以 `⚠️ 不一致:` 开头，`_BATCH_WARN_LINE_RE` 认不出它，导致每跑一次 reindex
    再插一条新 ⚠️（破幂等，数据腐蚀不自愈）。见 `_read_batches_lines` 的规范化修复。"""

    def test_warning_line_does_not_glue_to_handwritten_line_without_trailing_newline(
        self, tmp_path
    ):
        # 末行 `计划: x` 故意不带 `\n`，模拟半手维护文件缺尾随换行的真实情况；
        # 状态标 DONE 但成员（B1）未终态 → 触发 ⚠️ 不一致 追加。
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n",
            "状态: DONE\n",
            "成员: (生成)\n",
            "优先级: P1\n",
            "计划: x",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "batch-1"},
        ])
        _run_reindex(tmp_path)
        content = _read_batches(tmp_path)
        lines = content.splitlines()

        # 人写行逐字保留（未被 ⚠️ 粘连覆写）
        plan_line = next(l for l in lines if l.startswith("计划:"))
        assert plan_line == "计划: x"

        # ⚠️ 行独立成行，且以规范前缀开头（能被 _BATCH_WARN_LINE_RE 识别）
        warn_lines = [l for l in lines if l.startswith("⚠️ 不一致:")]
        assert len(warn_lines) == 1
        assert not any(l.startswith("计划: x⚠️") for l in lines)

    def test_idempotent_across_two_reindex_runs_when_file_lacks_trailing_newline(
        self, tmp_path
    ):
        _write_batches_md(tmp_path, [
            "### batch-1 — 清理项\n",
            "状态: DONE\n",
            "成员: (生成)\n",
            "优先级: P1\n",
            "计划: x",
        ])
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "batch-1"},
        ])
        _run_reindex(tmp_path)
        first = _read_batches(tmp_path)
        _run_reindex(tmp_path)
        second = _read_batches(tmp_path)

        assert first == second  # batches.md 逐字节稳定
        assert first.count("⚠️ 不一致") == 1  # 不累积


class TestEndToEndConsistency:
    """Task 16（§8.2）：端到端一致性自检——真实 buglist.py add / todolist.py add /
    triage → issues.py batch add → issues.py reindex 全流程串起来（不借道任何
    issues.py 内部函数造数据，只走三脚本各自的 CLI），断言三处物化视图互相一致：
      1) INDEX.md 的 open×批次板 == 直接拿 buglist.py/todolist.py `scan --json`
         现场扫出的 open 项（按批次分组正确）；
      2) batches.md 该批次的 `成员:` 生成行 == 直接拿 `scan --批次 {key} --json`
         现场扫出的、实际打了该批次 tag 的 item id 集合；
      3) 把该批次成员全部 set-status 到各自 pool 的终态后再 reindex → batches.md
         该批次 `状态:` 生成行同步为 DONE、INDEX open 板不再含这些项，且末尾重跑
         reindex 逐字节幂等（INDEX.md + batches.md 两个文件都稳定）。
    """

    BATCH_KEY = "e2e-batch"

    def _seed_and_first_reindex(self, tmp_path):
        """造 3 bug + 3 todo（各含 open 与终态），把各池一个 open 项 triage 进
        BATCH_KEY，注册该批次（PLANNED）后跑首次 reindex。返回 {逻辑名: id} 供
        各测试断言用——B1/T1 落批次，B2/T2 保持未分组，B3/T3 从一开始就是终态。"""
        ids = {}
        ids["B1"] = _buglist_add(
            tmp_path, module="a.c", summary="crash on startup", priority="P1",
            phenomenon="启动即崩", rootcause="init() 空指针",
        )
        ids["B2"] = _buglist_add(
            tmp_path, module="b.c", summary="off by one", priority="P2",
            phenomenon="循环多算一次",
        )
        ids["B3"] = _buglist_add(
            tmp_path, module="c.c", summary="already-fixed bug", priority="P3",
            phenomenon="旧问题", status="FIXED",
        )
        ids["T1"] = _todolist_add(tmp_path, module="a.c", summary="refactor init", type="代码质量")
        ids["T2"] = _todolist_add(tmp_path, module="b.c", summary="add caching", type="性能优化")
        ids["T3"] = _todolist_add(
            tmp_path, module="c.c", summary="old idea", type="代码质量", status="DONE",
        )

        _buglist_triage(tmp_path, ids["B1"], self.BATCH_KEY)
        _todolist_triage(tmp_path, ids["T1"], self.BATCH_KEY)

        _run_batch(tmp_path, ["add", self.BATCH_KEY, "--title", "端到端清理批次"])
        _run_reindex(tmp_path)
        return ids

    def test_index_open_board_matches_live_scan_grouped_by_batch(self, tmp_path):
        ids = self._seed_and_first_reindex(tmp_path)

        # 地面真值：不借道 issues.py，直接现场 scan 两个 recorder 自己的 dated 文件。
        bugs = _buglist_scan_json(tmp_path)
        todos = _todolist_scan_json(tmp_path)
        open_bugs = [b for b in bugs if b["status"] not in ("FIXED", "WONTFIX")]
        open_todos = [t for t in todos if t["status"] not in ("DONE", "WONTDO")]

        assert {b["id"] for b in open_bugs} == {ids["B1"], ids["B2"]}
        assert {t["id"] for t in open_todos} == {ids["T1"], ids["T2"]}
        assert next(b for b in open_bugs if b["id"] == ids["B1"])["batch"] == self.BATCH_KEY
        assert next(t for t in open_todos if t["id"] == ids["T1"])["batch"] == self.BATCH_KEY
        assert next(b for b in open_bugs if b["id"] == ids["B2"])["batch"] is None
        assert next(t for t in open_todos if t["id"] == ids["T2"])["batch"] is None

        content = _read_index(tmp_path)
        open_section, _, closed_section = content.partition("已闭合")

        batch_header = f"批次：{self.BATCH_KEY}"
        assert batch_header in open_section
        assert f"| {ids['B1']} |" in open_section
        assert f"| {ids['T1']} |" in open_section
        assert f"| {ids['B2']} |" in open_section
        assert f"| {ids['T2']} |" in open_section
        # 批次分组段落排在未分组段落之前（generate_index_md 的确定性顺序）
        assert open_section.index(batch_header) < open_section.index("未分组")

        # 终态项（B3/T3）从不出现在 open 板；已闭合摘要计数与地面真值一致
        assert f"| {ids['B3']} |" not in open_section
        assert f"| {ids['T3']} |" not in open_section
        assert "共 2 项已闭合" in closed_section

    def test_batches_md_members_line_matches_live_scan_by_batch_tag(self, tmp_path):
        ids = self._seed_and_first_reindex(tmp_path)

        tagged_bugs = _buglist_scan_json(tmp_path, batch=self.BATCH_KEY)
        tagged_todos = _todolist_scan_json(tmp_path, batch=self.BATCH_KEY)
        actual_members = {b["id"] for b in tagged_bugs} | {t["id"] for t in tagged_todos}
        # 只有 B1/T1 被 triage 进该批次；B2/T2 批次列为空，不该被扫出来
        assert actual_members == {ids["B1"], ids["T1"]}

        content = _read_batches(tmp_path)
        expected_line = "成员: (生成) " + ", ".join(sorted(actual_members))
        assert expected_line in content
        assert f"### {self.BATCH_KEY} —" in content
        assert "状态: PLANNED" in content  # 成员尚未全部终态，不该被判 DONE

    def test_batch_converges_to_done_and_index_excludes_terminal_members_then_idempotent(
        self, tmp_path
    ):
        ids = self._seed_and_first_reindex(tmp_path)

        # 把该批次仅有的两名成员（B1/T1）全部推进到各自 pool 的终态
        _buglist_set_status(tmp_path, ids["B1"], "FIXED", evidence="e2e-test-commit")
        _todolist_set_status(tmp_path, ids["T1"], "DONE", evidence="e2e-test-commit")
        _run_reindex(tmp_path)

        batches_content = _read_batches(tmp_path)
        assert f"### {self.BATCH_KEY} —" in batches_content
        assert "状态: DONE" in batches_content
        assert "状态: PLANNED" not in batches_content
        # 真实收敛（成员确已全终态），不是「人写 DONE 但实际没收敛」那种不一致告警场景
        assert "⚠️ 不一致" not in batches_content

        index_content = _read_index(tmp_path)
        open_section, _, closed_section = index_content.partition("已闭合")
        # B1/T1 已终态：该批次已无 open 成员，分组段落整体消失（不留空标题）
        assert f"批次：{self.BATCH_KEY}" not in open_section
        assert f"| {ids['B1']} |" not in open_section
        assert f"| {ids['T1']} |" not in open_section
        # B2/T2 从未变动过，仍是 open、仍在未分组段落
        assert f"| {ids['B2']} |" in open_section
        assert f"| {ids['T2']} |" in open_section
        # 已闭合摘要：B1/B3（bug）+ T1/T3（todo）共 4 项
        assert "共 4 项已闭合" in closed_section

        # 幂等：末尾再 reindex 一次，INDEX.md + batches.md 两个文件都逐字节稳定
        index_first = _read_index_bytes(tmp_path)
        batches_first = _read_batches(tmp_path)
        _run_reindex(tmp_path)
        index_second = _read_index_bytes(tmp_path)
        batches_second = _read_batches(tmp_path)
        assert index_first == index_second
        assert batches_first == batches_second


class TestSweep:
    """Task 1（roadmap 阶段 1 mlh-p1-issues-sweep）：`issues.py sweep --change X` 原子
    子命令——把 sdflow-done §2.1 手跑 4 步 issues 分诊循环固化为一次确定性、非原子、
    fail-closed、可重跑收敛的操作（design.md D1-D6）。全部子步走 subprocess CLI
    （scan --open-ungrouped / triage / batch add --if-exists skip / reindex）。
    """

    def test_sweep_open_ungrouped(self, tmp_path):
        """--open-ungrouped 口径 = 源==X ∧ 非终态 ∧ 批次空——非 OPEN 的非终态项
        （IN_PROGRESS）也要被纳入 triage（不因 --status OPEN 漏掉）。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "chg-x", "batch": ""},
            {"id": "B2", "status": "IN_PROGRESS", "change": "chg-x", "batch": ""},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "chg-x", "batch": ""},
        ])

        proc = _run_sweep(tmp_path, ["--change", "chg-x"])
        assert proc.returncode == 0, proc.stderr

        for iid in ("B1", "B2", "T1"):
            assert _item_batch(tmp_path, iid) == "chg-x"
            assert _item_status(tmp_path, iid) == "PROPOSED"

        batches_content = _read_batches(tmp_path)
        assert "### chg-x —" in batches_content  # batches.md 有该批次条目
        assert "chg-x" in _read_index(tmp_path)  # INDEX.md 已刷新

    def test_sweep_idempotent(self, tmp_path):
        """同 change 连跑两次：第二次 rc==0，triage/batch add 均 no-op，无净变化。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "chg-y", "batch": ""},
        ])
        _write_todo_file(tmp_path, "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "chg-y", "batch": ""},
        ])

        _run_sweep(tmp_path, ["--change", "chg-y"])
        batches_first = _read_batches(tmp_path)
        index_first = _read_index_bytes(tmp_path)

        proc2 = _run_sweep_raw(tmp_path, ["--change", "chg-y"])
        assert proc2.returncode == 0, proc2.stderr

        batches_second = _read_batches(tmp_path)
        index_second = _read_index_bytes(tmp_path)
        assert batches_first == batches_second
        assert index_first == index_second
        assert batches_second.count("### chg-y") == 1

    def test_sweep_rejects_empty_change(self, tmp_path):
        """空/纯空白/含 em-dash/含 pipe/含换行的 --change 一律在任何写盘前被拒；
        源为空的孤儿项不受影响（未进任何批次、状态不变）。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "", "batch": ""},  # 孤儿（源为空）
        ])

        for bad_change in ("", "   ", "a — b", "a|b", "a\nb"):
            proc = _run_sweep_raw(tmp_path, ["--change", bad_change])
            assert proc.returncode != 0, f"bad_change={bad_change!r} 应被拒但 rc==0"
            assert proc.stderr.strip() != ""

        # 孤儿未被误纳、状态/批次未被改动；batches.md 不该被凭空建出来
        assert _item_batch(tmp_path, "B1") == ""
        assert _item_status(tmp_path, "B1") == "OPEN"
        assert not _batches_path(tmp_path).exists()

    def test_sweep_excludes_orphans(self, tmp_path):
        """合法非空 change 下，源为空的孤儿项天然不匹配 --change 过滤，不被纳入。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "chg-z", "batch": ""},
            {"id": "B2", "status": "OPEN", "change": "", "batch": ""},  # 孤儿
        ])

        _run_sweep(tmp_path, ["--change", "chg-z"])

        assert _item_batch(tmp_path, "B1") == "chg-z"
        assert _item_batch(tmp_path, "B2") == ""
        assert _item_status(tmp_path, "B2") == "OPEN"

    def test_sweep_zero_items(self, tmp_path):
        """[impl-review-fix] FIX-2：0 命中（无匹配本 change 的 open-ungrouped 项）时，
        sweep 退出码 0，但不建批次条目——0 成员批次因 D1 vacuous-truth 排除永远不会被
        reindex 判 DONE，逐 change 累积会变成僵尸 PLANNED 条目，源头直接不建。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "other-chg", "batch": ""},
        ])
        proc = _run_sweep_raw(tmp_path, ["--change", "chg-empty"])
        assert proc.returncode == 0, proc.stderr
        assert not _batches_path(tmp_path).exists()
        assert _item_batch(tmp_path, "B1") == ""  # 未匹配的项不受影响

    def test_sweep_rejects_whitespace_change(self, tmp_path):
        """[impl-review-fix] FIX-5：首尾含空白的 change（strip 后非空）也必须被拒——
        此前会被静默 `.strip()` 后当合法 change 使用，违反"含空白即拒"的契约。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "chg", "batch": ""},
        ])
        for bad_change in (" chg", "chg "):
            proc = _run_sweep_raw(tmp_path, ["--change", bad_change])
            assert proc.returncode != 0, f"bad_change={bad_change!r} 应被拒但 rc==0"
            assert proc.stderr.strip() != ""

        assert _item_batch(tmp_path, "B1") == ""  # 未被误纳
        assert not _batches_path(tmp_path).exists()  # 未曾写盘

    def test_sweep_scan_fail_closed(
        self, tmp_path, monkeypatch, capsys, dispatch_run, argv_contains
    ):
        """[impl-review-fix] FIX-4：scan 子进程非零退出 → sweep 整体非零退出，stderr
        报明 pool/步；此前完全没测过这个分支。此时还没跑到 triage，不应有任何写盘。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "chg-scan", "batch": ""},
        ])
        class _FakeFailProc:
            returncode = 1
            stdout = ""
            stderr = "simulated scan failure"

        monkeypatch.setattr(
            issues_mod.subprocess,
            "run",
            dispatch_run(argv_contains("scan"), lambda _command: _FakeFailProc()),
        )

        args = types.SimpleNamespace(root=str(tmp_path), change="chg-scan")
        with pytest.raises(SystemExit) as exc_info:
            issues_mod.cmd_sweep(args)
        assert exc_info.value.code != 0

        err = capsys.readouterr().err
        assert "scan" in err
        assert "bug" in err

        assert _item_batch(tmp_path, "B1") == ""  # 未被 tag，scan 就已失败
        assert not _batches_path(tmp_path).exists()  # 完全没写盘

    def test_sweep_batch_add_fail_closed(
        self, tmp_path, monkeypatch, capsys, dispatch_run, argv_contains
    ):
        """[impl-review-fix] FIX-4：batch add 子进程非零退出 → sweep 整体非零退出，
        stderr 报明 batch add 步；此时 triage 已成功落盘（tag 已写），但 batches.md
        未建成——此前完全没测过这个分支。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "chg-ba", "batch": ""},
        ])
        class _FakeFailProc:
            returncode = 1
            stdout = ""
            stderr = "simulated batch add failure"

        monkeypatch.setattr(
            issues_mod.subprocess,
            "run",
            dispatch_run(argv_contains("batch", "add"), lambda _command: _FakeFailProc()),
        )

        args = types.SimpleNamespace(root=str(tmp_path), change="chg-ba")
        with pytest.raises(SystemExit) as exc_info:
            issues_mod.cmd_sweep(args)
        assert exc_info.value.code != 0

        err = capsys.readouterr().err
        assert "batch add" in err

        assert _item_batch(tmp_path, "B1") == "chg-ba"  # triage 已成功落盘
        assert not _batches_path(tmp_path).exists()  # batch add 未成功，未建成

    def test_sweep_triage_fail_closed(
        self, tmp_path, monkeypatch, capsys, dispatch_run, argv_contains
    ):
        """逐项 triage 第 i 项非零退出 → sweep 整体非零退出，stderr 报明失败点位
        （pool/id/已 tag 的 id 列表）；前面已成功的项保持已 tag。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "chg-f", "batch": ""},
            {"id": "B2", "status": "OPEN", "change": "chg-f", "batch": ""},
        ])
        class _FakeFailProc:
            returncode = 1
            stdout = ""
            stderr = "simulated triage failure"

        monkeypatch.setattr(
            issues_mod.subprocess,
            "run",
            dispatch_run(argv_contains("triage", "B2"), lambda _command: _FakeFailProc()),
        )

        args = types.SimpleNamespace(root=str(tmp_path), change="chg-f")
        with pytest.raises(SystemExit) as exc_info:
            issues_mod.cmd_sweep(args)
        assert exc_info.value.code != 0

        err = capsys.readouterr().err
        assert "B2" in err  # 失败点位含失败的 id
        assert "bug" in err  # 失败点位含 pool
        assert "B1" in err  # 已 tag 列表含 B1

        assert _item_batch(tmp_path, "B1") == "chg-f"  # 前 i-1 项已 tag
        assert _item_batch(tmp_path, "B2") == ""  # 失败项未被 tag
        assert not _batches_path(tmp_path).exists()  # 还没跑到 batch add 步

    def test_sweep_rerun_converges(self, tmp_path, monkeypatch, dispatch_run, argv_contains):
        """部分失败（B2 triage 注入失败）后移除注入重跑：全部收敛 tag，batches.md
        建成、INDEX 刷新；已 tag 项（B1）不受重跑影响（幂等）。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "chg-g", "batch": ""},
            {"id": "B2", "status": "OPEN", "change": "chg-g", "batch": ""},
        ])
        class _FakeFailProc:
            returncode = 1
            stdout = ""
            stderr = "simulated triage failure"

        monkeypatch.setattr(
            issues_mod.subprocess,
            "run",
            dispatch_run(argv_contains("triage", "B2"), lambda _command: _FakeFailProc()),
        )
        args = types.SimpleNamespace(root=str(tmp_path), change="chg-g")
        with pytest.raises(SystemExit):
            issues_mod.cmd_sweep(args)

        assert _item_batch(tmp_path, "B1") == "chg-g"
        assert _item_batch(tmp_path, "B2") == ""

        # 重跑走真实 CLI 子进程（不共享父进程内 monkeypatch 状态，天然不受影响）
        proc = _run_sweep_raw(tmp_path, ["--change", "chg-g"])
        assert proc.returncode == 0, proc.stderr

        assert _item_batch(tmp_path, "B1") == "chg-g"
        assert _item_batch(tmp_path, "B2") == "chg-g"
        assert _item_status(tmp_path, "B1") == "PROPOSED"
        assert _item_status(tmp_path, "B2") == "PROPOSED"
        assert "### chg-g —" in _read_batches(tmp_path)
        assert "chg-g" in _read_index(tmp_path)

    def test_sweep_reindex_fail_closed(
        self, tmp_path, monkeypatch, capsys, dispatch_run, argv_contains
    ):
        """末步 reindex 非零退出也判 sweep 整体失败（fail-closed，区别 rename 的
        warn-only）；此时 triage/batch add 均已成功落盘。

        [impl-review-fix] FIX-6：注入的 fake stderr 故意不含字面 "reindex"（改用
        "boom"）——此前用 "simulated reindex failure" 会让下面
        `assert "reindex" in err` 巧合通过（哪怕代码自身完全没标注是 reindex 步失败，
        断言也会因为注入的假 stderr 本身含这个词而通过）。现在 err 里的 "reindex" 只能
        来自被测代码自己格式化的 `sweep: reindex 失败 (...)` 前缀，断言才是真的在验证
        代码的失败点位标注。"""
        _write_bug_file(tmp_path, "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "chg-h", "batch": ""},
        ])
        class _FakeFailProc:
            returncode = 1
            stdout = ""
            stderr = "boom"

        monkeypatch.setattr(
            issues_mod.subprocess,
            "run",
            dispatch_run(argv_contains("reindex"), lambda _command: _FakeFailProc()),
        )
        args = types.SimpleNamespace(root=str(tmp_path), change="chg-h")
        with pytest.raises(SystemExit) as exc_info:
            issues_mod.cmd_sweep(args)
        assert exc_info.value.code != 0

        err = capsys.readouterr().err
        assert "reindex" in err  # 只能来自代码自身的 "sweep: reindex 失败" 标注
        assert "boom" in err  # 且确实透传了子进程的失败原因

        assert _item_batch(tmp_path, "B1") == "chg-h"
        assert "### chg-h —" in _read_batches(tmp_path)


# ── fixtures ─────────────────────────────────────────────────────────────────

def _run_cli(script, root, args, input_json=None):
    """通过真实 CLI 子进程调 buglist.py/todolist.py（stdin 喂 JSON，镜像
    sdflow-buglist/tests/test_buglist.py 的 run_add 写法：不传 --json，
    默认走 stdin，`input=None` 时等价于不喂 stdin JSON 的命令，如 triage/scan/set-status）。"""
    return subprocess.run(
        [sys.executable, script, "--root", str(root)] + args,
        input=json.dumps(input_json) if input_json is not None else None,
        capture_output=True, text=True,
    )


def _buglist_add(root, **fields):
    data = {"priority": "P2", "phenomenon": "e2e phenomenon"}
    data.update(fields)
    proc = _run_cli(BUGLIST_SCRIPT, root, ["add"], input_json=data)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["id"]


def _todolist_add(root, **fields):
    data = {"type": "代码质量"}
    data.update(fields)
    proc = _run_cli(TODOLIST_SCRIPT, root, ["add"], input_json=data)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["id"]


def _buglist_triage(root, id_, batch):
    proc = _run_cli(BUGLIST_SCRIPT, root, ["triage", "--id", id_, "--批次", batch])
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _todolist_triage(root, id_, batch):
    proc = _run_cli(TODOLIST_SCRIPT, root, ["triage", "--id", id_, "--批次", batch])
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _buglist_set_status(root, id_, to, evidence=None, reason=None):
    args = ["set-status", "--id", id_, "--to", to]
    if evidence:
        args += ["--evidence", evidence]
    if reason:
        args += ["--reason", reason]
    proc = _run_cli(BUGLIST_SCRIPT, root, args)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _todolist_set_status(root, id_, to, evidence=None, reason=None):
    args = ["set-status", "--id", id_, "--to", to]
    if evidence:
        args += ["--evidence", evidence]
    if reason:
        args += ["--reason", reason]
    proc = _run_cli(TODOLIST_SCRIPT, root, args)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _buglist_scan_json(root, batch=None):
    args = ["scan", "--json"]
    if batch is not None:
        args += ["--批次", batch]
    proc = _run_cli(BUGLIST_SCRIPT, root, args)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["bugs"]


def _todolist_scan_json(root, batch=None):
    args = ["scan", "--json"]
    if batch is not None:
        args += ["--批次", batch]
    proc = _run_cli(TODOLIST_SCRIPT, root, args)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["items"]


def _run_reindex(root):
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), "reindex"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return proc


def _index_path(root):
    return Path(root) / "openspec" / "issues" / "INDEX.md"


def _read_index(root):
    return _index_path(root).read_text(encoding="utf-8")


def _read_index_bytes(root):
    return _index_path(root).read_bytes()


def _write_bug_file(root, date, rows):
    """写一个最小合法的 dated buglist 文件（新路径 openspec/issues/buglist/），
    格式镜像 sdflow-buglist/tests/test_buglist.py 的 _write_mixed_file。"""
    dir_path = Path(root) / "openspec" / "issues" / "buglist"
    dir_path.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {date} Buglist\n\n",
        "> 来源：test\n",
        f"> 创建日期：{date}\n\n",
        "## 状态总览\n\n",
        "| ID | 模块 | 问题摘要 | 优先级 | 状态 | 时间 | 关联Change | 批次 |\n",
        "|----|------|----------|--------|------|------|------------|------|\n",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | `foo.c:1` | fixture | P2 | {r['status']} | 10:00 | "
            f"{r.get('change') or '-'} | {r.get('batch', '')} |\n"
        )
    for r in rows:
        lines.extend([
            f"\n---\n\n## {r['id']}: fixture\n\n",
            "| 属性 | 值 |\n|------|------|\n",
            f"| 状态 | {r['status']} |\n\n",
            "**根因**：fixture rootcause\n",
        ])
    (dir_path / f"{date}-buglist.md").write_text("".join(lines), encoding="utf-8")


def _write_todo_file(root, month, rows):
    """写一个最小合法的月度 todolist 文件（新路径 openspec/issues/todolist/），
    格式镜像 todolist.py 的 HEADER_TMPL + 表行。"""
    dir_path = Path(root) / "openspec" / "issues" / "todolist"
    dir_path.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {month} TODO\n\n",
        "> 项目：test\n\n",
        "## 状态总览\n\n",
        "| ID | 模块 | 描述 | 类型 | 状态 | 时间 | 关联Change | 批次 |\n",
        "|----|------|------|------|------|------|------------|------|\n",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | `foo.c:1` | fixture | 代码质量 | {r['status']} | "
            f"2026-01-01 10:00 | {r.get('change') or '-'} | {r.get('batch', '')} |\n"
        )
    (dir_path / f"{month}-todolist.md").write_text("".join(lines), encoding="utf-8")


def _run_batch_raw(root, extra_args):
    return subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), "batch"] + extra_args,
        capture_output=True, text=True,
    )


def _run_batch(root, extra_args):
    proc = _run_batch_raw(root, extra_args)
    assert proc.returncode == 0, proc.stderr
    return proc


def _batches_path(root):
    return Path(root) / "openspec" / "issues" / "batches.md"


def _read_batches(root):
    return _batches_path(root).read_text(encoding="utf-8")


def _write_batches_md(root, lines):
    path = _batches_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def _run_sweep_raw(root, extra_args):
    return subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), "sweep"] + extra_args,
        capture_output=True, text=True,
    )


def _run_sweep(root, extra_args):
    proc = _run_sweep_raw(root, extra_args)
    assert proc.returncode == 0, proc.stderr
    return proc


def _find_item_line(root, item_id):
    """跨 buglist/todolist 两池 dated 文件找含 item_id 的总览表行（用于断言 sweep
    落盘后的状态/批次列）——不依赖调用方知道该 id 属于哪个 pool。"""
    for sub in ("buglist", "todolist"):
        dir_path = Path(root) / "openspec" / "issues" / sub
        if not dir_path.exists():
            continue
        for f in sorted(dir_path.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            for line in text.splitlines():
                if re.match(rf"^\|\s*{re.escape(item_id)}\s*\|", line.strip()):
                    return line
    return None


def _item_cells(root, item_id):
    line = _find_item_line(root, item_id)
    assert line is not None, f"item {item_id} 未在任何 dated 文件里找到"
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _item_status(root, item_id):
    return _scan_item(root, item_id)["status"]


def _item_batch(root, item_id):
    return _scan_item(root, item_id).get("batch") or ""


def _scan_item(root, item_id):
    module = buglist_mod if item_id.startswith("B") else todolist_mod
    pool = "bug" if item_id.startswith("B") else "todo"
    for path in module.list_files(str(root)):
        document = module.read_recorder_document(path, pool)
        if item_id in document["effective_items"]:
            return {"id": item_id, **document["effective_items"][item_id]}
    raise AssertionError(f"item {item_id} 未在 recorder snapshot 中找到")
