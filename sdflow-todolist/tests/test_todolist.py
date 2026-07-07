"""
Tests for todolist.py's `doc`（关联文档）field: normalization, soft validation,
detail-block rendering, and change-based auto-default.
Run with: python3 -m pytest sdflow-todolist/tests/ -v
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import todolist as todolist_mod
from todolist import (
    normalize_doc_paths, auto_default_doc, validate_doc_paths, atomic_write,
    list_files, next_id, id_conflicts,
)

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "todolist.py")


def run_add(root, payload):
    return subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), "add"],
        input=json.dumps(payload), capture_output=True, text=True,
    )


def base_payload(**overrides):
    payload = {
        "module": "meter_collect.c",
        "summary": "温度采样改 DMA 批量读取",
        "type": "性能优化",
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
        content = _todolist_content(tmp_path)
        assert "**关联文档**：`openspec/changes/foo/design.md`、`openspec/rules/database.md`" in content

    def test_no_doc_line_when_doc_absent(self, tmp_path):
        payload = base_payload(change="no-such-change")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        content = _todolist_content(tmp_path)
        assert "**关联文档**" not in content

    def test_doc_alone_builds_a_block_even_without_narrative_fields(self, tmp_path):
        """轻量项默认不建块；但一旦有 doc，必须建块才能承载 doc 行（doc 是 block-only 特性）。"""
        payload = base_payload(doc="rules/database.md")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        result = json.loads(proc.stdout)
        assert result["block"] is True
        content = _todolist_content(tmp_path)
        assert "**关联文档**：`openspec/rules/database.md`" in content


class TestSoftValidation:
    def test_warns_but_still_records_nonexistent_doc(self, tmp_path):
        payload = base_payload(doc="changes/ghost/design.md")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        assert "WARNING" in proc.stderr
        assert "openspec/changes/ghost/design.md" in proc.stderr
        content = _todolist_content(tmp_path)
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

    def test_add_auto_default_enriches_block_created_for_other_reason(self, tmp_path):
        """auto-default 探测到 doc，但只有在块已经因为别的理由（这里是 motivation）要建时，
        才把这个 doc 塞进去——不是 auto-default 自己触发建块。"""
        d = tmp_path / "openspec" / "changes" / "foo"
        d.mkdir(parents=True)
        (d / "design.md").write_text("x", encoding="utf-8")
        payload = base_payload(change="foo", motivation="降低采样耗时")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        result = json.loads(proc.stdout)
        assert result["block"] is True
        content = _todolist_content(tmp_path)
        assert "**关联文档**：`openspec/changes/foo/design.md`" in content
        assert "**动机**：降低采样耗时" in content

    def test_explicit_doc_not_overridden_by_auto_default(self, tmp_path):
        d = tmp_path / "openspec" / "changes" / "foo"
        d.mkdir(parents=True)
        (d / "design.md").write_text("x", encoding="utf-8")
        payload = base_payload(change="foo", doc="rules/other.md")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        content = _todolist_content(tmp_path)
        assert "**关联文档**：`openspec/rules/other.md`" in content
        assert "changes/foo/design.md" not in content

    def test_auto_default_alone_does_not_force_a_block(self, tmp_path):
        """回归 Finding 2：change 能解出已存在的 design.md，但没有显式 doc、也没有
        motivation/approach/note 时，auto-default 不应单独把一个轻量项升级成带块的项——
        条目应仍是总览表里的一行，不出现块，也不出现『关联文档』行。"""
        d = tmp_path / "openspec" / "changes" / "foo"
        d.mkdir(parents=True)
        (d / "design.md").write_text("x", encoding="utf-8")
        payload = base_payload(change="foo")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        result = json.loads(proc.stdout)
        assert result["block"] is False
        content = _todolist_content(tmp_path)
        assert "**关联文档**" not in content
        assert f"## {result['id']}:" not in content  # 没有该项的详细块标题
        assert "\n---\n" not in content  # 没有块分隔线（表头分隔行 |----| 不受影响）

    def test_explicit_doc_alone_still_forces_a_block(self, tmp_path):
        """回归护栏：显式传 doc（没有 motivation/approach/note）必须仍然强制建块并带上 doc 行，
        这是 Finding 2 修复前就有的行为，不应被这次改动破坏。"""
        payload = base_payload(doc="rules/other.md")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        result = json.loads(proc.stdout)
        assert result["block"] is True
        content = _todolist_content(tmp_path)
        assert "**关联文档**：`openspec/rules/other.md`" in content


class TestBatchColumn:
    def test_add_writes_批次_column_at_end(self, tmp_path):
        payload = base_payload()
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        content = _todolist_content(tmp_path)
        header = [l for l in content.splitlines() if l.startswith("| ID |")][0]
        assert header.rstrip().endswith("| 批次 |")
        row = [l for l in content.splitlines() if l.startswith("| T1 ")][0]
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        assert len(cells) == 8 and cells[7] == ""

    def test_scan_old_7col_file_batch_none(self, tmp_path):
        """旧格式（无批次列，7 列）文件 scan 不报错，batch 读为 None（I8 向后兼容）。"""
        todolists_dir = tmp_path / "openspec" / "issues" / "todolist"
        todolists_dir.mkdir(parents=True)
        old_content = (
            "# 2026-01 TODO\n\n"
            "> 项目：<未注明>\n\n"
            "## 状态总览\n\n"
            "| ID | 模块 | 描述 | 类型 | 状态 | 时间 | 关联Change |\n"
            "|----|------|------|------|------|------|------------|\n"
            "| T1 | `foo.c` | 旧数据 | 性能优化 | OPEN | 10:00 | - |\n"
        )
        (todolists_dir / "2026-01-todolist.md").write_text(old_content, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "scan", "--json"],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
        result = json.loads(proc.stdout)
        t1 = [b for b in result["items"] if b["id"] == "T1"][0]
        assert t1["batch"] is None
        assert result["problems"] == []

    def test_scan_reads_batch_when_present(self, tmp_path):
        payload = base_payload()
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        # 手动把批次列写入刚新增的行（cmd_add 默认留空）
        path = tmp_path / "openspec" / "issues" / "todolist"
        files = list(path.glob("*-todolist.md"))
        content = files[0].read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        for i, ln in enumerate(lines):
            if ln.startswith("| T1 "):
                cells = [c.strip() for c in ln.strip().strip("|").split("|")]
                cells[7] = "batch-1"
                lines[i] = "| " + " | ".join(cells) + " |\n"
        files[0].write_text("".join(lines), encoding="utf-8")
        scan_proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "scan", "--json"],
            capture_output=True, text=True,
        )
        assert scan_proc.returncode == 0, scan_proc.stderr
        result = json.loads(scan_proc.stdout)
        t1 = [b for b in result["items"] if b["id"] == "T1"][0]
        assert t1["batch"] == "batch-1"


class TestCellSafety:
    """T2：状态总览表按 `|` 切列，字段值含 ASCII `|` 或换行会破坏列对齐（静默腐蚀）。
    cmd_add 入口必须在写盘前 fail-closed 拒绝——不能只在 `" | ".join(cells)` 拼接后的
    行字符串上检测（那时 `|` 已被 split 消费，测不出用户传入的原始违规字符，是假覆盖）。"""

    def test_add_rejects_pipe_in_summary(self, tmp_path):
        payload = base_payload(summary="A | B 都坏了")
        proc = run_add(tmp_path, payload)
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        d = tmp_path / "openspec" / "issues" / "todolist"
        if d.exists():
            for f in d.glob("*-todolist.md"):
                assert "A | B" not in f.read_text(encoding="utf-8")

    def test_add_rejects_newline_in_module(self, tmp_path):
        payload = base_payload(module="foo.c:1\n| EVIL | ROW |")
        proc = run_add(tmp_path, payload)
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        d = tmp_path / "openspec" / "issues" / "todolist"
        if d.exists():
            for f in d.glob("*-todolist.md"):
                assert "EVIL" not in f.read_text(encoding="utf-8")

    def test_add_rejects_newline_in_title(self, tmp_path):
        """[impl-review-fix] FIX-6（C7 amendment + 领域镜 F4，镜像 buglist）：显式 title 会
        原样拼进块头 `## {id}: {title}`（`_build_block`），此前未挂 `_reject_cell_unsafe`——
        含换行的 title 会在块头行里造出孤儿行，污染 block_ranges() 的解析。用 motivation 触发
        建块，确保守卫在真正拼块头前就已 fail-closed。"""
        payload = base_payload(title="正常标题\n## EVIL: 注入块头", motivation="x")
        proc = run_add(tmp_path, payload)
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        d = tmp_path / "openspec" / "issues" / "todolist"
        if d.exists():
            for f in d.glob("*-todolist.md"):
                assert "EVIL" not in f.read_text(encoding="utf-8")

    def test_add_rejects_newline_in_project(self, tmp_path):
        """[impl-review-fix] FIX-6：project 会原样拼进新建文件头部 `> 项目：{project}` 行
        （HEADER_TMPL，仅当月文件不存在时才建），此前未挂 `_reject_cell_unsafe`——含换行的
        project 会在头部注入额外行，污染文件头结构。"""
        payload = base_payload(project="正常项目\n> 项目：EVIL")
        proc = run_add(tmp_path, payload)
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        d = tmp_path / "openspec" / "issues" / "todolist"
        if d.exists():
            for f in d.glob("*-todolist.md"):
                assert "EVIL" not in f.read_text(encoding="utf-8")

    def test_triage_rejects_pipe_in_batch(self, tmp_path):
        """C1 BLOCKER 补漏：triage 也把批次写进总览管道表 cells[7]，同款守卫必须覆盖，
        不能只在 add 入口挡。传入含 `|` 的批次值应 fail-closed，且该行 cells[7] 不被腐蚀。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "triage",
             "--id", "T1", "--批次", "evil|key"],
            capture_output=True, text=True,
        )
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        content = (tmp_path / "openspec" / "issues" / "todolist" / "2026-01-todolist.md").read_text(encoding="utf-8")
        assert "evil|key" not in content


class TestExplicitIdGuard:
    """OV-3：add 允许 JSON payload 显式传 `id`（`tid = data.get("id") or next_id(...)`），
    但显式 id 此前无语法校验、无查重——非 `[A-Z]+\\d+` 的 id 会破 block_ranges 的正则匹配，
    重复 id 会被 parse_table_rows 的按 ID 建 dict 静默丢掉一整行。两者都必须在写盘前 fail-closed。"""

    def test_add_rejects_malformed_explicit_id(self, tmp_path):
        payload = base_payload(id="bad id")
        proc = run_add(tmp_path, payload)
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        d = tmp_path / "openspec" / "issues" / "todolist"
        if d.exists():
            for f in d.glob("*-todolist.md"):
                assert "bad id" not in f.read_text(encoding="utf-8")

    def test_add_rejects_duplicate_explicit_id(self, tmp_path):
        proc1 = run_add(tmp_path, base_payload())
        assert proc1.returncode == 0, proc1.stderr
        assert json.loads(proc1.stdout)["id"] == "T1"
        proc2 = run_add(tmp_path, base_payload(id="T1"))
        assert proc2.returncode != 0
        assert "ERROR" in proc2.stderr
        content = _todolist_content(tmp_path)
        assert content.count("| T1 ") == 1

    def test_add_rejects_multiletter_prefix_id(self, tmp_path):
        """代码库 ID 识别（`_ids_in_files` 的 `\\| *([A-Z]\\d+) *\\|`、`ID_RE = \\b([A-Z])(\\d+)\\b`）
        全部只认单字母前缀，`TT12` 这类多字母前缀语法上就该被拒——否则会破 block_ranges 匹配，
        且 all_ids() 认不出它，导致查重对多字母 id 静默失效（两次 add 同一个 TT12 都会 returncode 0）。"""
        payload = base_payload(id="TT12")
        proc = run_add(tmp_path, payload)
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr
        d = tmp_path / "openspec" / "issues" / "todolist"
        if d.exists():
            for f in d.glob("*-todolist.md"):
                assert "TT12" not in f.read_text(encoding="utf-8")

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
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": ""},
            {"id": "T1", "status": "OPEN", "change": "y", "batch": ""},
        ])
        result = _scan_json(tmp_path, [])
        assert any("重复" in p and "T1" in p for p in result["problems"])


class TestScanRowArity:
    """OV-1（镜像 buglist.py）：无块坏行——数据行本身列数与标准 7/8 不符（例如描述字段
    意外含裸 `|`，把一行拆多了列），`parse_table_rows` 只要求 `len(cells) >= 5` 就照单
    按固定列位读（列错位不会自己报错）。scan 必须显式核对行 arity 并报出来。"""

    def test_scan_flags_arity_corrupted_row(self, tmp_path):
        todolist_dir = tmp_path / "openspec" / "issues" / "todolist"
        todolist_dir.mkdir(parents=True)
        content = (
            "# 2026-01 TODO\n\n"
            "> 项目：test\n\n"
            "## 状态总览\n\n"
            "| ID | 模块 | 描述 | 类型 | 状态 | 时间 | 关联Change | 批次 |\n"
            "|----|------|------|------|------|------|------------|------|\n"
            "| T1 | `foo.c` | A | B 有问题 | 性能优化 | OPEN | 2026-01-01 10:00 | x | |\n"
        )
        (todolist_dir / "2026-01-todolist.md").write_text(content, encoding="utf-8")
        result = _scan_json(tmp_path, [])
        assert any("arity" in p and "T1" in p for p in result["problems"])

    def test_scan_does_not_flag_valid_7_or_8_col_rows(self, tmp_path):
        """7 列（旧格式，无批次列）/8 列（新格式）都是合法 arity，不应误报。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": ""},
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

    def test_overwrite_preserves_original_file_permissions(self, tmp_path):
        """回归：tempfile.mkstemp 固定以 0600 创建临时文件，os.replace 是纯 rename，
        若不显式对齐权限，覆写会让已存在文件的权限被静默从 0644 收紧到 0600。"""
        target = tmp_path / "file.md"
        target.write_text("old", encoding="utf-8")
        os.chmod(target, 0o644)
        atomic_write(str(target), "new")
        assert (os.stat(target).st_mode & 0o777) == 0o644

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

        monkeypatch.setattr(todolist_mod.os, "replace", boom)

        with pytest.raises(OSError):
            atomic_write(str(target), "new content that must not land")

        assert target.read_text(encoding="utf-8") == "original content"
        leftovers = [p for p in tmp_path.iterdir() if p.name != "file.md"]
        assert leftovers == []


class TestDualRead:
    """过渡期加固（Phase B Q1，镜像 buglist Task 4）：list_files/all_ids/next_id 同时扫新
    `openspec/issues/todolist/` + 旧 `openspec/todolists/` 两目录（新在前=写落新，旧只读兼容），
    避免下游只 update 未迁移旧数据时 ID 从新目录重数、撞旧目录已有的号。"""

    def test_next_id_takes_max_across_old_and_new(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "todolists", "2026-01", ["T1"])
        _write_dated_file(tmp_path / "openspec" / "issues" / "todolist", "2026-02", ["T2"])
        assert next_id(str(tmp_path)) == "T3"

    def test_list_files_includes_both_paths(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "todolists", "2026-01", ["T1"])
        _write_dated_file(tmp_path / "openspec" / "issues" / "todolist", "2026-02", ["T2"])
        files = [f.replace(os.sep, "/") for f in list_files(str(tmp_path))]
        assert len(files) == 2
        assert any("openspec/todolists/" in f for f in files)
        assert any("openspec/issues/todolist/" in f for f in files)

    def test_list_files_new_dir_sorts_before_old_dir_even_if_dated_later(self, tmp_path):
        """正向断言（非 Task 4-fix 那个 whole-path-sort bug 的判别测试）：验证当前实现下，
        即使旧目录 `openspec/todolists/` 里的文件月份更早、新目录 `openspec/issues/todolist/`
        月份更晚，list_files 仍输出新目录在前。

        注意：对 todolist 这组目录名，`'i'`（issues）< `'t'`（todolists），所以『按 _dated_dirs
        目录序分别收集』与『对拼接后全路径整体 sorted()』这两种实现在本场景下输出完全相同
        （都是新目录在前）——本测试无法区分二者，起不到 buglist 侧 Task 4-fix 那个回归守卫的
        作用（buglist 侧才真实存在该 bug：旧路径 'b'（buglists）< 新路径 'i'（issues），整体
        sorted 会让旧目录排到新目录前面）。保留本测试是因为它对当前实现仍是有效的正向断言。"""
        _write_dated_file(tmp_path / "openspec" / "todolists", "2026-01", ["T1"])
        _write_dated_file(tmp_path / "openspec" / "issues" / "todolist", "2026-02", ["T2"])
        files = [f.replace(os.sep, "/") for f in list_files(str(tmp_path))]
        assert "openspec/issues/todolist" in files[0]

    def test_list_files_new_dir_only_unchanged_behavior(self, tmp_path):
        """旧目录不存在时行为与现状一致（不破坏现有行为）。"""
        _write_dated_file(tmp_path / "openspec" / "issues" / "todolist", "2026-02", ["T2"])
        files = list_files(str(tmp_path))
        assert len(files) == 1
        assert "issues" in files[0].replace(os.sep, "/")

    def test_id_conflicts_detects_same_id_across_paths(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "todolists", "2026-01", ["T1", "T2"])
        _write_dated_file(tmp_path / "openspec" / "issues" / "todolist", "2026-02", ["T2", "T3"])
        assert id_conflicts(str(tmp_path)) == ["T2"]

    def test_id_conflicts_empty_when_no_overlap(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "todolists", "2026-01", ["T1"])
        _write_dated_file(tmp_path / "openspec" / "issues" / "todolist", "2026-02", ["T2"])
        assert id_conflicts(str(tmp_path)) == []

    def test_id_conflicts_empty_when_only_one_path_exists(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "issues" / "todolist", "2026-02", ["T1"])
        assert id_conflicts(str(tmp_path)) == []

    def test_next_id_cli_warns_stderr_on_conflict_but_does_not_block(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "todolists", "2026-01", ["T1"])
        _write_dated_file(tmp_path / "openspec" / "issues" / "todolist", "2026-02", ["T1"])
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "next-id"],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == "T2"
        assert "WARNING" in proc.stderr
        assert "T1" in proc.stderr

    def test_next_id_cli_silent_when_no_conflict(self, tmp_path):
        _write_dated_file(tmp_path / "openspec" / "issues" / "todolist", "2026-02", ["T1"])
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "next-id"],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == "T2"
        assert proc.stderr == ""


class TestScanFilters:
    """Task 6：scan 新增 --change / --批次 / --open-ungrouped 三个过滤维度，
    支撑 Phase B 后续 sweep。todolist 的非终态集与 buglist 不同——STATUS_CODES 只有
    OPEN/PROPOSED/DONE/WONTDO，终态是 DONE/WONTDO，非终态 = {OPEN, PROPOSED}，
    不能硬套 buglist 的 5 值非终态集。三者与既有 --status/--type 都是 AND 叠加。"""

    def test_change_filters_by_source(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "change-a", "batch": ""},
            {"id": "T2", "status": "OPEN", "change": "change-b", "batch": ""},
        ])
        result = _scan_json(tmp_path, ["--change", "change-a"])
        assert [b["id"] for b in result["items"]] == ["T1"]

    def test_batch_filters_by_batch(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": "batch-1"},
            {"id": "T2", "status": "OPEN", "change": "x", "batch": "batch-2"},
            {"id": "T3", "status": "OPEN", "change": "x", "batch": ""},
        ])
        result = _scan_json(tmp_path, ["--批次", "batch-1"])
        assert [b["id"] for b in result["items"]] == ["T1"]

    def test_open_ungrouped_matches_only_open_and_proposed(self, tmp_path):
        """todolist 非终态只有 OPEN/PROPOSED（不是 buglist 那 5 个）：T1/T2 命中；
        T3（DONE）、T5（WONTDO）是终态不该命中；T4 虽 OPEN 但已有批次不该命中。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": ""},
            {"id": "T2", "status": "PROPOSED", "change": "x", "batch": ""},
            {"id": "T3", "status": "DONE", "change": "x", "batch": ""},
            {"id": "T4", "status": "OPEN", "change": "x", "batch": "batch-1"},
            {"id": "T5", "status": "WONTDO", "change": "x", "batch": ""},
        ])
        result = _scan_json(tmp_path, ["--open-ungrouped"])
        assert sorted(b["id"] for b in result["items"]) == ["T1", "T2"]

    def test_filters_combine_with_and(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "change-a", "batch": ""},
            {"id": "T2", "status": "OPEN", "change": "change-b", "batch": ""},
            {"id": "T3", "status": "DONE", "change": "change-a", "batch": ""},
        ])
        result = _scan_json(tmp_path, ["--change", "change-a", "--open-ungrouped"])
        assert [b["id"] for b in result["items"]] == ["T1"]

    def test_status_and_batch_combine(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": "batch-1"},
            {"id": "T2", "status": "DONE", "change": "x", "batch": "batch-1"},
            {"id": "T3", "status": "OPEN", "change": "x", "batch": "batch-2"},
        ])
        result = _scan_json(tmp_path, ["--status", "OPEN", "--批次", "batch-1"])
        assert [b["id"] for b in result["items"]] == ["T1"]

    def test_no_filters_returns_everything(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": ""},
            {"id": "T2", "status": "DONE", "change": "y", "batch": "batch-1"},
        ])
        result = _scan_json(tmp_path, [])
        assert sorted(b["id"] for b in result["items"]) == ["T1", "T2"]


class TestTriage:
    """Task 7：triage 命令给指定 item 赋批次 + 未分诊开放态 → PROPOSED，幂等（D7）。
    镜像 buglist 的 TestTriage；todolist 未分诊开放态只有 {OPEN}（终态 DONE/WONTDO 不同于 buglist）。"""

    def test_open_item_triage_sets_proposed_and_batch(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        result = _triage(tmp_path, "T1", "clear-foo")
        assert result["old_status"] == "OPEN"
        assert result["new_status"] == "PROPOSED"
        assert result["batch"] == "clear-foo"
        scanned = _scan_json(tmp_path, [])
        t1 = [b for b in scanned["items"] if b["id"] == "T1"][0]
        assert t1["status"] == "PROPOSED"
        assert t1["batch"] == "clear-foo"

    def test_already_proposed_item_triage_is_idempotent_noop_on_status(self, tmp_path):
        """D7：已 PROPOSED 的 item 再 triage → status 仍 PROPOSED（不报错、不跳变），只更新批次列。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "PROPOSED", "change": "x", "batch": "old-batch"},
        ])
        result = _triage(tmp_path, "T1", "new-batch")
        assert result["old_status"] == "PROPOSED"
        assert result["new_status"] == "PROPOSED"
        assert result["batch"] == "new-batch"
        scanned = _scan_json(tmp_path, [])
        t1 = [b for b in scanned["items"] if b["id"] == "T1"][0]
        assert t1["status"] == "PROPOSED"
        assert t1["batch"] == "new-batch"

    def test_terminal_status_not_reverted_to_proposed(self, tmp_path):
        """终态（DONE/WONTDO）triage 不倒回 PROPOSED，只更新批次列，不报错。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "DONE", "change": "x", "batch": ""},
            {"id": "T2", "status": "WONTDO", "change": "x", "batch": ""},
        ])
        for tid in ("T1", "T2"):
            old = "DONE" if tid == "T1" else "WONTDO"
            result = _triage(tmp_path, tid, "clear-foo")
            assert result["old_status"] == old
            assert result["new_status"] == old
            assert result["batch"] == "clear-foo"

    def test_status_change_syncs_detail_block_when_block_exists(self, tmp_path):
        """todolist 块可选：给 motivation 强制建块，triage 状态变化时块的『状态』行同步，
        scan 不报表↔块不一致。"""
        payload = base_payload(motivation="降低采样耗时")
        proc = run_add(tmp_path, payload)
        assert proc.returncode == 0, proc.stderr
        result = _triage(tmp_path, "T1", "clear-foo")
        assert result["new_status"] == "PROPOSED"
        content = _todolist_content(tmp_path)
        assert "| 状态 | PROPOSED |" in content
        scanned = _scan_json(tmp_path, [])
        assert scanned["problems"] == []

    def test_not_found_id_errors(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path), "triage",
             "--id", "T99", "--批次", "clear-foo"],
            capture_output=True, text=True,
        )
        assert proc.returncode != 0
        assert "ERROR" in proc.stderr


class TestSetStatus:
    """T5（本次任务）补测：cmd_set_status 此前无任何测试覆盖——补 WONTDO 门禁分支
    （必须 --reason）+ 基本回归网，确保 `_find_row_file` 抽取（消 set-status/triage
    重复的『遍历 list_files 找含该 ID 的表行』逻辑）不改变 set-status 的定位/门禁/双写行为。"""

    def test_not_found_id_errors(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        result = _set_status_raw(tmp_path, "T99", "WONTDO", "--reason", "x")
        assert result.returncode != 0
        assert "ERROR" in result.stderr

    def test_wontdo_without_reason_dies(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        result = _set_status_raw(tmp_path, "T1", "WONTDO")
        assert result.returncode != 0
        assert "WONTDO" in result.stderr

    def test_wontdo_with_reason_updates_table_and_appends_minimal_block(self, tmp_path):
        """todolist 详细块可选：base_payload 默认不建块（无 motivation/approach/note/doc），
        WONTDO + --reason 走 `_minimal_block` 留痕分支——补块 + 状态 + 历史一次写入。"""
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        result = _set_status(tmp_path, "T1", "WONTDO", "--reason", "优先级太低，不做了")
        assert result["old"] == "OPEN"
        assert result["new"] == "WONTDO"
        content = _todolist_content(tmp_path)
        assert "| 状态 | WONTDO |" in content
        assert "优先级太低，不做了" in content

    def test_non_terminal_transition_without_block_updates_table_only(self, tmp_path):
        """回归网：无详细块、无 evidence/reason 的普通转换只改表行，不强行建块——
        同时验证 `_find_row_file` 抽取后仍能正确定位到该 ID 所在文件/表行。"""
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        result = _set_status(tmp_path, "T1", "PROPOSED")
        assert result["old"] == "OPEN"
        assert result["new"] == "PROPOSED"
        content = _todolist_content(tmp_path)
        assert "| T1 | " in content
        assert "## T1:" not in content  # 无块场景不该被顺带建块


class TestSetStatusCellSafety:
    """[impl-review-fix] FIX-1（A-F1 PoC，镜像 buglist.py）：cmd_set_status 把
    evidence/reason/month 原样拼进历史行 `> {month} 状态：{old} → {new}（{note}）`，
    此前未挂 `_reject_cell_unsafe` 守卫——含换行的 reason/evidence 会被 `block_ranges()`
    在注入点截断真实块（或在 `_minimal_block` 场景下伪装出新的 `---`/`## ID:` 行），
    `scan` 完全测不出（静默腐蚀）。入口必须 fail-closed，写盘前不留任何腐蚀。"""

    def test_set_status_rejects_newline_in_reason(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        before = _todolist_content(tmp_path)
        result = _set_status_raw(tmp_path, "T1", "WONTDO", "--reason", "x\n\n---\n\ny")
        assert result.returncode != 0
        assert "ERROR" in result.stderr
        assert _todolist_content(tmp_path) == before

    def test_set_status_rejects_pipe_in_reason(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        result = _set_status_raw(tmp_path, "T1", "WONTDO", "--reason", "a | b")
        assert result.returncode != 0
        assert "ERROR" in result.stderr

    def test_set_status_rejects_newline_in_evidence(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        before = _todolist_content(tmp_path)
        result = _set_status_raw(tmp_path, "T1", "PROPOSED", "--evidence", "abc\n---\ndef")
        assert result.returncode != 0
        assert "ERROR" in result.stderr
        assert _todolist_content(tmp_path) == before

    def test_set_status_rejects_newline_in_month(self, tmp_path):
        proc = run_add(tmp_path, base_payload())
        assert proc.returncode == 0, proc.stderr
        result = _set_status_raw(tmp_path, "T1", "PROPOSED", "--month", "2026-01\nEVIL")
        assert result.returncode != 0
        assert "ERROR" in result.stderr


class TestScanDuplicateIdCrossFile:
    """[impl-review-fix] FIX-2（CV-1+A-F2 双镜 PoC，镜像 buglist.py）：重复 ID 检测
    语义上应是全池（跨全部 dated 文件）唯一性检查。此前 `cmd_scan` 的 Counter 在 for
    循环体内逐文件重建，只测得出单文件内重复，漏检跨文件同 ID（例如
    2026-01/2026-02 两个月度文件都出现 T1）。"""

    def test_scan_reports_duplicate_id_across_two_dated_files(self, tmp_path):
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": ""},
        ])
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-02", [
            {"id": "T1", "status": "OPEN", "change": "y", "batch": ""},
        ])
        result = _scan_json(tmp_path, [])
        assert any("重复" in p and "T1" in p for p in result["problems"])

    def test_scan_still_reports_duplicate_id_within_single_file(self, tmp_path):
        """回归：单文件内重复检测（既有覆盖）不因改成全池维度而失效。"""
        _write_mixed_file(tmp_path / "openspec" / "issues" / "todolist", "2026-01", [
            {"id": "T1", "status": "OPEN", "change": "x", "batch": ""},
            {"id": "T1", "status": "OPEN", "change": "y", "batch": ""},
        ])
        result = _scan_json(tmp_path, [])
        assert any("重复" in p and "T1" in p for p in result["problems"])


def _set_status(root, item_id, to, *extra_args):
    result = _set_status_raw(root, item_id, to, *extra_args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _set_status_raw(root, item_id, to, *extra_args):
    return subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), "set-status",
         "--id", item_id, "--to", to, *extra_args],
        capture_output=True, text=True,
    )


def _triage(root, item_id, batch):
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), "triage", "--id", item_id, "--批次", batch],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _scan_json(root, extra_args):
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), "scan", "--json", *extra_args],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _write_mixed_file(dir_path, month, rows):
    """镜像 _write_dated_file，但每行的 status/change/batch 可独立指定
    （scan 过滤测试需要混合数据，不能像 _write_dated_file 那样固定 OPEN/无批次）。"""
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
            f"| {r['id']} | `foo.c` | fixture | 性能优化 | {r['status']} | 2026-01-01 10:00 | "
            f"{r.get('change') or '-'} | {r.get('batch', '')} |\n"
        )
    (dir_path / f"{month}-todolist.md").write_text("".join(lines), encoding="utf-8")


def _write_dated_file(dir_path, month, ids):
    """写一个最小合法的月度 todolist 文件（只含状态总览表，够 list_files/all_ids/id_conflicts
    解析），用于 dual-read 测试在指定目录（新或旧）铸出 fixture 数据。"""
    dir_path.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {month} TODO\n\n",
        "> 项目：test\n\n",
        "## 状态总览\n\n",
        "| ID | 模块 | 描述 | 类型 | 状态 | 时间 | 关联Change | 批次 |\n",
        "|----|------|------|------|------|------|------------|------|\n",
    ]
    for tid in ids:
        lines.append(f"| {tid} | `foo.c` | fixture | 性能优化 | OPEN | 2026-01-01 10:00 | - |  |\n")
    (dir_path / f"{month}-todolist.md").write_text("".join(lines), encoding="utf-8")


def _todolist_content(root):
    d = root / "openspec" / "issues" / "todolist"
    files = list(d.glob("*-todolist.md"))
    assert len(files) == 1
    return files[0].read_text(encoding="utf-8")
