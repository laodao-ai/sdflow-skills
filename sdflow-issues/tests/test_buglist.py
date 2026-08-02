"""
Tests for buglist.py's `doc`（关联文档）field: normalization, soft validation,
detail-block rendering, and change-based auto-default.
Run with: python3 -m pytest sdflow-issues/tests/ -v
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import buglist as buglist_mod
from buglist import (
    normalize_doc_paths, auto_default_doc, validate_doc_paths, atomic_write,
    list_files, next_id, id_conflicts,
)

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "buglist.py")


def run_add(root, payload):
    """通过真实 CLI 调 add 子命令（stdin 喂 JSON），返回 CompletedProcess。"""
    return subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), "add"],
        input=json.dumps(payload), capture_output=True, text=True,

        encoding="utf-8",
        errors="replace",)


def base_payload(**overrides):
    payload = {
        "module": "data_publish.c:120",
        "summary": "envelope type 为空",
        "priority": "P1",
        "phenomenon": "服务端收到的 envelope.type 恒为空字符串",
    }
    payload.update(overrides)
    return payload


class TestNormalizeDocPaths:
    def test_bare_path_gets_prefix(self):
        assert normalize_doc_paths("changes/foo/design.md") == ["openspec/changes/foo/design.md"]

    def test_already_prefixed_path_unchanged(self):
        assert normalize_doc_paths("openspec/changes/foo/design.md") == ["openspec/changes/foo/design.md"]

    def test_list_input_normalizes_each(self):
        result = normalize_doc_paths(["changes/foo/design.md", "openspec/rules/database.md"])
        assert result == ["openspec/changes/foo/design.md", "openspec/rules/database.md"]

    def test_empty_or_none_returns_empty_list(self):
        assert normalize_doc_paths(None) == []
        assert normalize_doc_paths("") == []
        assert normalize_doc_paths([]) == []

    def test_non_md_path_kept_as_is_but_prefixed(self):
        assert normalize_doc_paths("rules/database.yaml") == ["openspec/rules/database.yaml"]


class TestDetailBlockRendering:
    def test_block_contains_doc_line_when_doc_given(self, tmp_path):
        payload = base_payload(doc=["changes/foo/design.md", "rules/database.md"])
        (tmp_path / "openspec" / "changes" / "foo").mkdir(parents=True)
        (tmp_path / "openspec" / "changes" / "foo" / "design.md").write_text("x", encoding="utf-8")
        (tmp_path / "openspec" / "rules").mkdir(parents=True)
        (tmp_path / "openspec" / "rules" / "database.md").write_text("x", encoding="utf-8")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        content = _buglist_content(tmp_path)
        assert "**关联文档**：`openspec/changes/foo/design.md`、`openspec/rules/database.md`" in content

    def test_no_doc_line_when_doc_absent(self, tmp_path):
        payload = base_payload(change="no-such-change")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        content = _buglist_content(tmp_path)
        assert "**关联文档**" not in content


class TestSoftValidation:
    def test_warns_but_still_records_nonexistent_doc(self, tmp_path):
        payload = base_payload(doc="changes/ghost/design.md")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        assert "WARNING" in proc.stderr
        assert "openspec/changes/ghost/design.md" in proc.stderr
        content = _buglist_content(tmp_path)
        assert "**关联文档**：`openspec/changes/ghost/design.md`" in content


class TestAutoDefaultDoc:
    def test_picks_design_over_proposal(self, tmp_path):
        d = tmp_path / "openspec" / "changes" / "foo"
        d.mkdir(parents=True)
        (d / "design.md").write_text("x", encoding="utf-8")
        (d / "proposal.md").write_text("x", encoding="utf-8")
        assert auto_default_doc(str(tmp_path), "foo") == ["openspec/changes/foo/design.md"]

    def test_finds_proposal_when_no_design(self, tmp_path):
        d = tmp_path / "openspec" / "changes" / "foo"
        d.mkdir(parents=True)
        (d / "proposal.md").write_text("x", encoding="utf-8")
        assert auto_default_doc(str(tmp_path), "foo") == ["openspec/changes/foo/proposal.md"]

    def test_finds_archived_change_via_glob(self, tmp_path):
        d = tmp_path / "openspec" / "changes" / "archive" / "2026-01-01-foo"
        d.mkdir(parents=True)
        (d / "design.md").write_text("x", encoding="utf-8")
        result = auto_default_doc(str(tmp_path), "foo")
        assert result == ["openspec/changes/archive/2026-01-01-foo/design.md"]

    def test_skips_when_multiple_archived_matches(self, tmp_path):
        for datestamp in ("2026-01-01", "2026-02-02"):
            d = tmp_path / "openspec" / "changes" / "archive" / f"{datestamp}-foo"
            d.mkdir(parents=True)
            (d / "design.md").write_text("x", encoding="utf-8")
        assert auto_default_doc(str(tmp_path), "foo") == []

    def test_empty_when_nothing_matches(self, tmp_path):
        assert auto_default_doc(str(tmp_path), "foo") == []

    def test_ambiguous_archive_dirs_skip_even_if_only_one_has_proposal(self, tmp_path):
        """回归 Finding 1：两个归档目录都匹配 `*-{change}`（目录级本就歧义），
        只有其中一个恰好带 proposal.md（另一个只有 design.md）。修复前的 bug：per-filename
        分别判断『唯一匹配』，导致 design.md 判定歧义（2 个）但 proposal.md 判定不歧义（1 个），
        从而错误地悄悄采用了那个歧义目录的 proposal.md。歧义检查必须在『目录』这一级只做一次：
        `*-{change}` glob 命中 2 个目录就该整层跳过，返回 []。"""
        d1 = tmp_path / "openspec" / "changes" / "archive" / "2026-01-01-foo"
        d1.mkdir(parents=True)
        (d1 / "design.md").write_text("x", encoding="utf-8")
        (d1 / "proposal.md").write_text("x", encoding="utf-8")
        d2 = tmp_path / "openspec" / "changes" / "archive" / "2026-02-02-foo"
        d2.mkdir(parents=True)
        (d2 / "design.md").write_text("x", encoding="utf-8")
        assert auto_default_doc(str(tmp_path), "foo") == []

    def test_empty_when_no_change(self, tmp_path):
        assert auto_default_doc(str(tmp_path), "") == []
        assert auto_default_doc(str(tmp_path), None) == []

    def test_add_auto_defaults_from_change_when_doc_missing(self, tmp_path):
        d = tmp_path / "openspec" / "changes" / "foo"
        d.mkdir(parents=True)
        (d / "design.md").write_text("x", encoding="utf-8")
        payload = base_payload(change="foo")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        content = _buglist_content(tmp_path)
        assert "**关联文档**：`openspec/changes/foo/design.md`" in content

    def test_explicit_doc_not_overridden_by_auto_default(self, tmp_path):
        d = tmp_path / "openspec" / "changes" / "foo"
        d.mkdir(parents=True)
        (d / "design.md").write_text("x", encoding="utf-8")
        payload = base_payload(change="foo", doc="rules/other.md")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        content = _buglist_content(tmp_path)
        assert "**关联文档**：`openspec/rules/other.md`" in content
        assert "changes/foo/design.md" not in content


class TestBatchColumn:
    def test_add_writes_批次_column_at_end(self, tmp_path):
        payload = base_payload(batch="batch-1")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        content = _buglist_content(tmp_path)
        assert '"batch":"batch-1"' in content
        assert "| ID |" not in content and "| B1 |" not in content

    def test_scan_old_7col_file_batch_none(self, tmp_path):
        """旧格式（无批次列，7 列）文件 scan 不报错，batch 读为 None（I8 向后兼容）。"""
        buglists_dir = tmp_path / "openspec" / "issues" / "buglist"
        buglists_dir.mkdir(parents=True)
        old_content = (
            "# 2026-01-01 Buglist\n\n"
            "> 来源：<未注明>\n"
            "> 创建日期：2026-01-01\n\n"
            "## 状态总览\n\n"
            "| ID | 模块 | 问题摘要 | 优先级 | 状态 | 时间 | 关联Change |\n"
            "|----|------|----------|--------|------|------|------------|\n"
            "| B1 | `foo.c:10` | 旧数据 | P1 | OPEN | 10:00 | - |\n\n"
            "---\n\n"
            "## B1: 旧数据\n\n"
            "| 属性 | 值 |\n"
            "|------|------|\n"
            "| 模块 | `foo.c:10` |\n"
            "| 优先级 | P1 |\n"
            "| 状态 | OPEN |\n\n"
            "**现象**：占位\n\n"
            "**根因**：<待分析>\n\n"
            "**修复方案**：\n- <待补充>\n\n"
            "**影响范围**：<待评估>\n"
        )
        (buglists_dir / "2026-01-01-buglist.md").write_text(old_content, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "scan", "--json"],
            capture_output=True, text=True,

            encoding="utf-8",
            errors="replace",)
        assert proc.returncode == 0, proc.stderr
        result = json.loads(proc.stdout)
        b1 = [b for b in result["bugs"] if b["id"] == "B1"][0]
        assert b1["batch"] is None
        assert result["problems"] == []

    def test_scan_reads_batch_when_present(self, tmp_path):
        payload = base_payload(batch="batch-1")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        scan_proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "scan", "--json"],
            capture_output=True, text=True,

            encoding="utf-8",
            errors="replace",)
        assert scan_proc.returncode == 0, scan_proc.stderr
        result = json.loads(scan_proc.stdout)
        b1 = [b for b in result["bugs"] if b["id"] == "B1"][0]
        assert b1["batch"] == "batch-1"


class TestCellSafety:
    """frontmatter JSON 索引允许 pipe/换行；Markdown 单行结构仍 fail-closed。"""

    def test_add_round_trips_pipe_in_summary(self, tmp_path):
        payload = base_payload(summary="A | B 都坏了")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        assert _scan_json(tmp_path, [])["bugs"][0]["summary"] == "A | B 都坏了"

    def test_add_round_trips_newline_in_module(self, tmp_path):
        payload = base_payload(module="foo.c:1\n| EVIL | ROW |")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        assert _scan_json(tmp_path, [])["bugs"][0]["module"] == "foo.c:1\n| EVIL | ROW |"

    def test_triage_round_trips_pipe_in_batch(self, tmp_path):
        """C1 BLOCKER 补漏：triage 也把批次写进总览管道表 cells[7]，同款守卫必须覆盖，
        不能只在 add 入口挡。传入含 `|` 的批次值应 fail-closed，且该行 cells[7] 不被腐蚀。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "triage",
             "--id", "B1", "--批次", "evil|key"],
            capture_output=True, text=True,

            encoding="utf-8",
            errors="replace",)
        assert proc.returncode == 0, proc.stderr
        assert _scan_json(tmp_path, [])["bugs"][0]["batch"] == "evil|key"
        content = (tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md").read_text(encoding="utf-8")
        assert '"batch":"evil|key"' in content
        assert "| B1 | `foo.c:1` | fixture | P2 | OPEN | 10:00 | x |  |" in content

    def test_add_rejects_newline_in_title(self, tmp_path):
        """[impl-review-fix] FIX-6（C7 amendment + 领域镜 F4）：显式 title 会原样拼进块头
        `## {id}: {title}`（BLOCK_TMPL），此前未挂 `_reject_cell_unsafe`——含换行的 title
        会在块头行里造出孤儿行，block_ranges() 的 `##\\s+[A-Z]\\d+\\s*:` 正则可能被腐蚀成
        另一个"块"，静默污染文档结构。"""
        payload = base_payload(title="正常标题\n## EVIL: 注入块头")
        proc = run_add(tmp_path, payload)
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        d = tmp_path / "openspec" / "issues" / "buglist"
        if d.exists():
            for f in d.glob("*-buglist.md"):
                assert "EVIL" not in f.read_text(encoding="utf-8")

    def test_add_rejects_newline_in_source(self, tmp_path):
        """[impl-review-fix] FIX-6：source 会原样拼进新建文件头部 `> 来源：{source}` 行
        （HEADER_TMPL，仅当日文件不存在时才建），此前未挂 `_reject_cell_unsafe`——含换行的
        source 会在头部注入额外行，污染文件头结构。"""
        payload = base_payload(source="正常来源\n> 来源：EVIL")
        proc = run_add(tmp_path, payload)
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        d = tmp_path / "openspec" / "issues" / "buglist"
        if d.exists():
            for f in d.glob("*-buglist.md"):
                assert "EVIL" not in f.read_text(encoding="utf-8")


class TestExplicitIdGuard:
    """OV-3：add 允许 JSON payload 显式传 `id`（`bid = data.get("id") or next_id(...)`），
    但显式 id 此前无语法校验、无查重——非 `[A-Z]+\\d+` 的 id 会破 block_ranges 的正则匹配，
    重复 id 会被 parse_table_rows 的按 ID 建 dict 静默丢掉一整行。两者都必须在写盘前 fail-closed。"""

    def test_add_rejects_malformed_explicit_id(self, tmp_path):
        payload = base_payload(id="bad id")
        proc = run_add(tmp_path, payload)
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        d = tmp_path / "openspec" / "issues" / "buglist"
        if d.exists():
            for f in d.glob("*-buglist.md"):
                assert "bad id" not in f.read_text(encoding="utf-8")

    def test_add_rejects_duplicate_explicit_id(self, tmp_path):
        proc1 = run_add(tmp_path, base_payload())
        assert proc1.returncode == 0, proc1.stderr
        assert json.loads(proc1.stdout)["id"] == "B1"
        proc2 = run_add(tmp_path, base_payload(id="B1"))
        assert proc2.returncode != 0
        assert "ERROR" in proc2.stderr
        content = _buglist_content(tmp_path)
        assert content.count("    B1: ") == 1

    def test_add_rejects_multiletter_prefix_id(self, tmp_path):
        """代码库 ID 识别（`_ids_in_files` 的 `\\| *([A-Z]\\d+) *\\|`、`ID_RE = \\b([A-Z])(\\d+)\\b`）
        全部只认单字母前缀，`BB12` 这类多字母前缀语法上就该被拒——否则会破 block_ranges 匹配，
        且 all_ids() 认不出它，导致查重对多字母 id 静默失效（两次 add 同一个 BB12 都会 returncode 0）。"""
        payload = base_payload(id="BB12")
        proc = run_add(tmp_path, payload)
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        d = tmp_path / "openspec" / "issues" / "buglist"
        if d.exists():
            for f in d.glob("*-buglist.md"):
                assert "BB12" not in f.read_text(encoding="utf-8")

    def test_add_rejects_nonstring_id(self, tmp_path):
        """id 若是 JSON 数字（如 123）而非字符串，`re.fullmatch(pattern, 123)` 会抛裸 TypeError，
        破坏 `_die` 的 `ERROR:` 契约——非字符串 id 必须走优雅 _die，不能是未捕获异常栈。"""
        payload = base_payload(id=123)
        proc = run_add(tmp_path, payload)
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        assert "Traceback" not in proc.stderr


class TestScanDuplicateId:
    """OV-3：即便重复 ID 绕过了 add 的查重（例如手工编辑池文件），scan 也必须把它报出来——
    parse_table_rows 按 ID 建 dict，重复 ID 会静默丢一行，不报的话用户完全无感知。"""

    def test_scan_reports_duplicate_id(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
            {"id": "B1", "status": "OPEN", "change": "y", "batch": ""},
        ])
        proc = _scan_proc(tmp_path, [])
        assert proc.returncode != 0
        assert proc.stdout == ""
        assert "semantic ID 重复" in proc.stderr and "B1" in proc.stderr


class TestScanRowArity:
    """OV-1：无块坏行——数据行本身列数与标准 7/8 不符（例如摘要字段意外含裸 `|`，把一行
    拆多了列），`parse_table_rows` 只要求 `len(cells) >= 5` 就照单按固定列位读（列错位
    不会自己报错）。scan 必须显式核对行 arity 并报出来。"""

    def test_scan_flags_arity_corrupted_row(self, tmp_path):
        buglists_dir = tmp_path / "openspec" / "issues" / "buglist"
        buglists_dir.mkdir(parents=True)
        content = (
            "# 2026-01-01 Buglist\n\n"
            "> 来源：test\n"
            "> 创建日期：2026-01-01\n\n"
            "## 状态总览\n\n"
            "| ID | 模块 | 问题摘要 | 优先级 | 状态 | 时间 | 关联Change | 批次 |\n"
            "|----|------|----------|--------|------|------|------------|------|\n"
            "| B1 | `foo.c:1` | A | B 都坏了 | P2 | OPEN | 10:00 | x | |\n"
        )
        (buglists_dir / "2026-01-01-buglist.md").write_text(content, encoding="utf-8")
        result = _scan_json(tmp_path, [])
        assert any("arity" in p and "B1" in p for p in result["problems"])

    def test_scan_does_not_flag_valid_7_or_8_col_rows(self, tmp_path):
        """7 列（旧格式，无批次列）/8 列（新格式）都是合法 arity，不应误报。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        result = _scan_json(tmp_path, [])
        assert not any("arity" in p for p in result["problems"])


class TestAtomicWrite:
    def test_writes_content_and_creates_parent_dir(self, tmp_path):
        target = tmp_path / "sub" / "dir" / "file.md"
        atomic_write(str(target), "hello\nworld\n")
        assert target.read_text(encoding="utf-8") == "hello\nworld\n"

    def test_overwrites_existing_file(self, tmp_path):
        target = tmp_path / "file.md"
        target.write_text("old", encoding="utf-8")
        atomic_write(str(target), "new")
        assert target.read_text(encoding="utf-8") == "new"

    @pytest.mark.skipif(os.name == "nt", reason="Windows does not expose POSIX mode bits")
    def test_overwrite_preserves_original_file_permissions(self, tmp_path):
        """回归：tempfile.mkstemp 固定以 0600 创建临时文件，os.replace 是纯 rename，
        若不显式对齐权限，覆写会让已存在文件的权限被静默从 0644 收紧到 0600。"""
        target = tmp_path / "file.md"
        target.write_text("old", encoding="utf-8")
        os.chmod(target, 0o644)
        atomic_write(str(target), "new")
        assert (os.stat(target).st_mode & 0o777) == 0o644

    @pytest.mark.skipif(os.name == "nt", reason="Windows does not expose POSIX mode bits")
    def test_new_file_gets_default_permissions(self, tmp_path):
        target = tmp_path / "brand_new.md"
        atomic_write(str(target), "content")
        assert (os.stat(target).st_mode & 0o777) == 0o644

    def test_no_leftover_tmp_file_after_success(self, tmp_path):
        target = tmp_path / "file.md"
        atomic_write(str(target), "content")
        leftovers = [p for p in tmp_path.iterdir() if p.name != "file.md"]
        assert leftovers == []

    def test_original_file_unchanged_when_replace_fails(self, tmp_path, monkeypatch):
        """中途异常（这里模拟 os.replace 本身失败）：原文件必须原样保留，不能被截断/清空，
        且不留残留 .tmp 文件（finally 兜底清理）。"""
        target = tmp_path / "file.md"
        target.write_text("original content", encoding="utf-8")

        def boom(src, dst):
            raise OSError("simulated os.replace failure")

        monkeypatch.setattr(buglist_mod.os, "replace", boom)

        with pytest.raises(OSError):
            atomic_write(str(target), "new content that must not land")

        assert target.read_text(encoding="utf-8") == "original content"
        leftovers = [p for p in tmp_path.iterdir() if p.name != "file.md"]
        assert leftovers == []


class TestDualRead:
    """过渡期加固（Phase B Q1）：list_files/all_ids/next_id 同时扫新 `openspec/issues/buglist/`
    + 旧 `openspec/buglists/` 两目录（新在前=写落新，旧只读兼容），避免下游只 update 未迁移
    旧数据时 ID 从新目录重数、撞旧目录已有的号。"""

    def test_next_id_takes_max_across_old_and_new(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "buglists", "2026-01-01", ["B1"])
        _write_dated_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-02", ["B2"])
        assert next_id(str(tmp_path)) == "B3"

    def test_list_files_includes_both_paths(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "buglists", "2026-01-01", ["B1"])
        _write_dated_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-02", ["B2"])
        files = [f.replace(os.sep, "/") for f in list_files(str(tmp_path))]
        assert len(files) == 2
        assert any("openspec/buglists/" in f for f in files)
        assert any("openspec/issues/buglist/" in f for f in files)

    def test_list_files_new_dir_sorts_before_old_dir_even_if_dated_later(self, tmp_path):
        """回归：list_files 曾对拼接后的全路径整体 sorted，导致旧目录 `openspec/buglists/`
        （字符串 'b'）永远排在新目录 `openspec/issues/buglist/`（'i'）之前，即使新目录里的
        文件日期更新，也会被字符串序压到后面——违反『新在前』。修复后应按 _dated_dirs 的
        目录顺序（新在前）分别收集、目录内部再按文件名排序，不整体 sorted。"""
        _write_dated_file(tmp_path / "openspec" / "buglists", "2026-01-01", ["B1"])
        _write_dated_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-02", ["B2"])
        files = [f.replace(os.sep, "/") for f in list_files(str(tmp_path))]
        assert "openspec/issues/buglist" in files[0]

    def test_list_files_new_dir_only_unchanged_behavior(self, tmp_path):
        """旧目录不存在时行为与现状一致（不破坏现有行为）。"""
        _write_dated_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-02", ["B2"])
        files = list_files(str(tmp_path))
        assert len(files) == 1
        assert "issues" in files[0].replace(os.sep, "/")

    def test_id_conflicts_detects_same_id_across_paths(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "buglists", "2026-01-01", ["B1", "B2"])
        _write_dated_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-02", ["B2", "B3"])
        assert id_conflicts(str(tmp_path)) == ["B2"]

    def test_id_conflicts_empty_when_no_overlap(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "buglists", "2026-01-01", ["B1"])
        _write_dated_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-02", ["B2"])
        assert id_conflicts(str(tmp_path)) == []

    def test_id_conflicts_empty_when_only_one_path_exists(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-02", ["B1"])
        assert id_conflicts(str(tmp_path)) == []

    def test_next_id_cli_fails_closed_on_semantic_conflict(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "buglists", "2026-01-01", ["B1"])
        _write_dated_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-02", ["B1"])
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "next-id"],
            capture_output=True, text=True,

            encoding="utf-8",
            errors="replace",)
        assert proc.returncode != 0
        assert proc.stdout == ""
        assert "WARNING" in proc.stderr
        assert "B1" in proc.stderr
        assert "repository semantic ID conflict" in proc.stderr

    def test_next_id_cli_silent_when_no_conflict(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-02", ["B1"])
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "next-id"],
            capture_output=True, text=True,

            encoding="utf-8",
            errors="replace",)
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == "B2"
        assert proc.stderr == ""


class TestScanFilters:
    """Task 6：scan 新增 --change / --批次 / --open-ungrouped 三个过滤维度，
    支撑 Phase B 后续 sweep（按源/按批次挑活、找未分批的开放项）。三者与既有 --status
    都是 AND 叠加——scan 收集完 bugs 后逐个过滤链应用，互不影响彼此的判定输入。"""

    def test_change_filters_by_source(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "change-a", "batch": ""},
            {"id": "B2", "status": "OPEN", "change": "change-b", "batch": ""},
        ])
        result = _scan_json(tmp_path, ["--change", "change-a"])
        assert [b["id"] for b in result["bugs"]] == ["B1"]

    def test_batch_filters_by_batch(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "batch-1"},
            {"id": "B2", "status": "OPEN", "change": "x", "batch": "batch-2"},
            {"id": "B3", "status": "OPEN", "change": "x", "batch": ""},
        ])
        result = _scan_json(tmp_path, ["--批次", "batch-1"])
        assert [b["id"] for b in result["bugs"]] == ["B1"]

    def test_open_ungrouped_matches_nonterminal_without_batch(self, tmp_path):
        """非终态 = STATUS_CODES 减 {FIXED, WONTFIX}。B1/B2 命中（非终态 + 无批次）；
        B3/B5 是终态（FIXED/WONTFIX）不该命中；B4 虽非终态但已有批次不该命中。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
            {"id": "B2", "status": "VERIFIED", "change": "x", "batch": ""},
            {"id": "B3", "status": "FIXED", "change": "x", "batch": ""},
            {"id": "B4", "status": "OPEN", "change": "x", "batch": "batch-1"},
            {"id": "B5", "status": "WONTFIX", "change": "x", "batch": ""},
        ])
        result = _scan_json(tmp_path, ["--open-ungrouped"])
        assert sorted(b["id"] for b in result["bugs"]) == ["B1", "B2"]

    def test_open_ungrouped_covers_all_nonterminal_statuses(self, tmp_path):
        """逐一覆盖 buglist 的全部 5 个非终态码（PROPOSED/IN_PROGRESS/BLOCKED 也要命中，
        不只是示例里出现的 OPEN/VERIFIED）。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "PROPOSED", "change": "x", "batch": ""},
            {"id": "B2", "status": "IN_PROGRESS", "change": "x", "batch": ""},
            {"id": "B3", "status": "BLOCKED", "change": "x", "batch": ""},
        ])
        result = _scan_json(tmp_path, ["--open-ungrouped"])
        assert sorted(b["id"] for b in result["bugs"]) == ["B1", "B2", "B3"]

    def test_filters_combine_with_and(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "change-a", "batch": ""},
            {"id": "B2", "status": "OPEN", "change": "change-b", "batch": ""},
            {"id": "B3", "status": "FIXED", "change": "change-a", "batch": ""},
        ])
        result = _scan_json(tmp_path, ["--change", "change-a", "--open-ungrouped"])
        assert [b["id"] for b in result["bugs"]] == ["B1"]

    def test_status_and_batch_combine(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": "batch-1"},
            {"id": "B2", "status": "FIXED", "change": "x", "batch": "batch-1"},
            {"id": "B3", "status": "OPEN", "change": "x", "batch": "batch-2"},
        ])
        result = _scan_json(tmp_path, ["--status", "OPEN", "--批次", "batch-1"])
        assert [b["id"] for b in result["bugs"]] == ["B1"]

    def test_no_filters_returns_everything(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
            {"id": "B2", "status": "FIXED", "change": "y", "batch": "batch-1"},
        ])
        result = _scan_json(tmp_path, [])
        assert sorted(b["id"] for b in result["bugs"]) == ["B1", "B2"]


class TestTriage:
    """Task 7：triage 命令给指定 item 赋批次 + 未分诊开放态 → PROPOSED，幂等（D7）。"""

    def test_open_item_triage_sets_proposed_and_batch(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        result = _triage(tmp_path, "B1", "clear-foo")
        assert result["old_status"] == "OPEN"
        assert result["new_status"] == "PROPOSED"
        assert result["batch"] == "clear-foo"
        scanned = _scan_json(tmp_path, [])
        b1 = [b for b in scanned["bugs"] if b["id"] == "B1"][0]
        assert b1["status"] == "PROPOSED"
        assert b1["batch"] == "clear-foo"

    def test_already_proposed_item_triage_is_idempotent_noop_on_status(self, tmp_path):
        """D7：已 PROPOSED 的 item 再 triage → status 仍 PROPOSED（不报错、不跳变），只更新批次列。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "PROPOSED", "change": "x", "batch": "old-batch"},
        ])
        result = _triage(tmp_path, "B1", "new-batch")
        assert result["old_status"] == "PROPOSED"
        assert result["new_status"] == "PROPOSED"
        assert result["batch"] == "new-batch"
        scanned = _scan_json(tmp_path, [])
        b1 = [b for b in scanned["bugs"] if b["id"] == "B1"][0]
        assert b1["status"] == "PROPOSED"
        assert b1["batch"] == "new-batch"

    def test_terminal_status_not_reverted_to_proposed(self, tmp_path):
        """终态（FIXED/WONTFIX）triage 不倒回 PROPOSED，只更新批次列，不报错。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "FIXED", "change": "x", "batch": ""},
            {"id": "B2", "status": "WONTFIX", "change": "x", "batch": ""},
        ])
        for bid in ("B1", "B2"):
            old = "FIXED" if bid == "B1" else "WONTFIX"
            result = _triage(tmp_path, bid, "clear-foo")
            assert result["old_status"] == old
            assert result["new_status"] == old
            assert result["batch"] == "clear-foo"

    def test_covers_all_open_untriaged_statuses(self, tmp_path):
        """未分诊开放态 = OPEN/VERIFIED/IN_PROGRESS/BLOCKED（PROPOSED、终态排除）均转 PROPOSED。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "VERIFIED", "change": "x", "batch": ""},
            {"id": "B2", "status": "IN_PROGRESS", "change": "x", "batch": ""},
            {"id": "B3", "status": "BLOCKED", "change": "x", "batch": ""},
        ])
        for bid in ("B1", "B2", "B3"):
            result = _triage(tmp_path, bid, "clear-foo")
            assert result["new_status"] == "PROPOSED"

    def test_status_change_syncs_detail_block_and_scan_reports_no_inconsistency(self, tmp_path):
        payload = base_payload()  # cmd_add 默认状态 OPEN，且总会建块
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        result = _triage(tmp_path, "B1", "clear-foo")
        assert result["new_status"] == "PROPOSED"
        content = _buglist_content(tmp_path)
        assert '"status":"PROPOSED"' in content
        assert "| 状态 | PROPOSED |" not in content
        scanned = _scan_json(tmp_path, [])
        assert scanned["problems"] == []

    def test_not_found_id_errors(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "triage",
             "--id", "B99", "--批次", "clear-foo"],
            capture_output=True, text=True,

            encoding="utf-8",
            errors="replace",)
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr

    def test_batch_only_triage_does_not_promote_open_status(self, tmp_path):
        """harden-issues-read-write Task 3：`--batch-only` 只赋批次，不推进
        未分诊开放态→PROPOSED（sweep 复用同一 CLI，须与人工 triage 解耦）。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        result = _triage(tmp_path, "B1", "clear-foo", batch_only=True)
        assert result["old_status"] == "OPEN"
        assert result["new_status"] == "OPEN"
        assert result["batch"] == "clear-foo"
        scanned = _scan_json(tmp_path, [])
        b1 = [b for b in scanned["bugs"] if b["id"] == "B1"][0]
        assert b1["status"] == "OPEN"
        assert b1["batch"] == "clear-foo"


class TestSetStatus:
    """T5（本次任务）补测：cmd_set_status 此前无任何测试覆盖——补 WONTFIX 门禁分支
    （必须 --reason）+ 基本回归网，确保 `_find_row_file` 抽取（消 set-status/triage
    重复的『遍历 list_files 找含该 ID 的表行』逻辑）不改变 set-status 的定位/门禁/双写行为。"""

    def test_not_found_id_errors(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        result = _set_status_raw(tmp_path, "B99", "WONTFIX", "--reason", "x")
        assert result.returncode != 0
        assert "ERROR" in result.stderr

    def test_wontfix_without_reason_dies(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        result = _set_status_raw(tmp_path, "B1", "WONTFIX")
        assert result.returncode != 0
        assert "WONTFIX" in result.stderr

    def test_wontfix_with_reason_updates_table_block_and_history(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        result = _set_status(tmp_path, "B1", "WONTFIX", "--reason", "不复现，不值得修")
        assert result["old"] == "OPEN"
        assert result["new"] == "WONTFIX"
        content = _buglist_content(tmp_path)
        assert '"status":"WONTFIX"' in content
        assert "| 状态 | WONTFIX |" not in content
        assert "不复现，不值得修" in content
        scanned = _scan_json(tmp_path, [])
        assert scanned["problems"] == []

    def test_non_terminal_transition_updates_table_and_block(self, tmp_path):
        """回归网：普通（非门禁）状态转换仍能通过 `_find_row_file` 正确定位到含该 ID 的
        文件/表行/详细块，双写一致。"""
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        result = _set_status(tmp_path, "B1", "IN_PROGRESS")
        assert result["old"] == "OPEN"
        assert result["new"] == "IN_PROGRESS"
        content = _buglist_content(tmp_path)
        assert '"status":"IN_PROGRESS"' in content
        assert "| 状态 | IN_PROGRESS |" not in content
        scanned = _scan_json(tmp_path, [])
        assert scanned["problems"] == []


class TestSetStatusCellSafety:
    """[impl-review-fix] FIX-1（A-F1 PoC）：cmd_set_status 把 evidence/reason/date
    原样拼进历史行 `> {date} 状态：{old} → {new}（{note}）`，此前未挂 `_reject_cell_unsafe`
    守卫——含换行的 reason/evidence（例如恰好含一段独立的 `---` 行）会被 `block_ranges()`
    在注入点截断真实块，`scan` 返回 `problems: []` 完全绕过一致性自检（静默腐蚀）。
    入口必须 fail-closed 拒绝含 `|`/换行的值，写盘前不留任何腐蚀。"""

    def test_set_status_rejects_newline_in_reason(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        before = _buglist_content(tmp_path)
        result = _set_status_raw(tmp_path, "B1", "WONTFIX", "--reason", "x\n\n---\n\ny")
        assert result.returncode != 0
        assert "ERROR" in result.stderr
        assert _buglist_content(tmp_path) == before

    def test_set_status_allows_pipe_in_reason(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        result = _set_status_raw(tmp_path, "B1", "WONTFIX", "--reason", "a | b")
        assert result.returncode == 0, result.stderr
        assert "a | b" in _buglist_content(tmp_path)

    def test_set_status_rejects_newline_in_evidence(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        before = _buglist_content(tmp_path)
        result = _set_status_raw(tmp_path, "B1", "IN_PROGRESS", "--evidence", "abc\n---\ndef")
        assert result.returncode != 0
        assert "ERROR" in result.stderr
        assert _buglist_content(tmp_path) == before

    def test_set_status_rejects_newline_in_date(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        result = _set_status_raw(
            tmp_path, "B1", "IN_PROGRESS", "--date", "2026-01-01\nEVIL"
        )
        assert result.returncode != 0
        assert "ERROR" in result.stderr


class TestScanDuplicateIdCrossFile:
    """[impl-review-fix] FIX-2（CV-1+A-F2 双镜 PoC）：重复 ID 检测语义上应是全池
    （跨全部 dated 文件）唯一性检查。此前 `cmd_scan` 的 Counter 在 for 循环体内逐文件
    重建，只测得出单文件内重复，漏检跨文件同 ID（例如 2026-01-01/2026-01-02 两个
    文件都出现 B1）——ID 应全局唯一，跨文件重复正是要报的腐蚀。"""

    def test_scan_reports_duplicate_id_across_two_dated_files(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-02", [
            {"id": "B1", "status": "OPEN", "change": "y", "batch": ""},
        ])
        proc = _scan_proc(tmp_path, [])
        assert proc.returncode != 0
        assert "semantic ID 重复" in proc.stderr and "B1" in proc.stderr

    def test_scan_still_reports_duplicate_id_within_single_file(self, tmp_path):
        """回归：单文件内重复检测（既有覆盖）不因改成全池维度而失效。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "buglist", "2026-01-01", [
            {"id": "B1", "status": "OPEN", "change": "x", "batch": ""},
            {"id": "B1", "status": "OPEN", "change": "y", "batch": ""},
        ])
        proc = _scan_proc(tmp_path, [])
        assert proc.returncode != 0
        assert "semantic ID 重复" in proc.stderr and "B1" in proc.stderr


def _set_status(root, bug_id, to, *extra_args):
    result = _set_status_raw(root, bug_id, to, *extra_args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _set_status_raw(root, bug_id, to, *extra_args):
    return subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), "set-status",
         "--id", bug_id, "--to", to, *extra_args],
        capture_output=True, text=True,

        encoding="utf-8",
        errors="replace",)


def _triage(root, bug_id, batch, batch_only=False):
    argv = [sys.executable, SCRIPT, "--root", str(root), "triage", "--id", bug_id, "--批次", batch]
    if batch_only:
        argv.append("--batch-only")
    proc = subprocess.run(
        argv,
        capture_output=True, text=True,

        encoding="utf-8",
        errors="replace",)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _scan_json(root, extra_args):
    proc = _scan_proc(root, extra_args)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _scan_proc(root, extra_args):
    return subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), "scan", "--json", *extra_args],
        capture_output=True, text=True,

        encoding="utf-8",
        errors="replace",)


def _write_mixed_file(dir_path, date, rows):
    """镜像 _write_dated_file，但每行的 status/change/batch 可独立指定
    （scan 过滤测试需要混合数据，不能像 _write_dated_file 那样固定 OPEN/无批次）。"""
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


def _write_dated_file(dir_path, date, ids):
    """写一个最小合法的 dated buglist 文件（只含状态总览表，够 list_files/all_ids/id_conflicts
    解析），用于 dual-read 测试在指定目录（新或旧）铸出 fixture 数据。"""
    dir_path.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {date} Buglist\n\n",
        "> 来源：test\n",
        f"> 创建日期：{date}\n\n",
        "## 状态总览\n\n",
        "| ID | 模块 | 问题摘要 | 优先级 | 状态 | 时间 | 关联Change | 批次 |\n",
        "|----|------|----------|--------|------|------|------------|------|\n",
    ]
    for bid in ids:
        lines.append(f"| {bid} | `foo.c:1` | fixture | P2 | OPEN | 10:00 | - |  |\n")
    (dir_path / f"{date}-buglist.md").write_text("".join(lines), encoding="utf-8")


def _buglist_content(root):
    d = root / "openspec" / "issues" / "buglist"
    files = list(d.glob("*-buglist.md"))
    assert len(files) == 1
    return files[0].read_text(encoding="utf-8")
