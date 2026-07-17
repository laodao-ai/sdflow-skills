import json
import importlib.util
import inspect
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
BUG_SCRIPT = REPO_ROOT / "sdflow-buglist" / "scripts" / "buglist.py"
TODO_SCRIPT = REPO_ROOT / "sdflow-todolist" / "scripts" / "todolist.py"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUG = _load_module("_task3_bug", BUG_SCRIPT)
TODO = _load_module("_task3_todo", TODO_SCRIPT)


def _run(script, root, *args, payload=None):
    return subprocess.run(
        [sys.executable, str(script), "--root", str(root), *args],
        input=None if payload is None else json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
    )


def test_bug_add_creates_canonical_frontmatter_without_legacy_row(tmp_path):
    payload = {
        "id": "B1",
        "module": "采集|模块\n第二行",
        "summary": "摘要 | α\n## fake\n---",
        "priority": "P1",
        "status": "OPEN",
        "change": "change|一",
        "batch": "batch|一",
        "source": "人工来源 | α",
        "phenomenon": "现象正文",
        "rootcause": "根因正文",
        "fix": ["修复一"],
        "impact": "影响正文",
    }

    proc = _run(
        BUG_SCRIPT, tmp_path, "add", "--date", "2026-07-17", "--time", "09:30",
        payload=payload,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result == {"id": "B1", "file": "openspec/issues/buglist/2026-07-17-buglist.md",
                      "status": "OPEN", "time": "09:30", "change": "change|一"}
    path = tmp_path / "openspec/issues/buglist/2026-07-17-buglist.md"
    expected = (
        b"---\nsdflow-issues:\n  schema: 1\n  pool: bug\n  mode: canonical\n  items:\n"
        b"    B1: {\"module\":\"\xe9\x87\x87\xe9\x9b\x86|\xe6\xa8\xa1\xe5\x9d\x97\\n\xe7\xac\xac\xe4\xba\x8c\xe8\xa1\x8c\",\"summary\":\"\xe6\x91\x98\xe8\xa6\x81 | \xce\xb1\\n## fake\\n---\",\"priority\":\"P1\",\"status\":\"OPEN\",\"time\":\"09:30\",\"change\":\"change|\xe4\xb8\x80\",\"batch\":\"batch|\xe4\xb8\x80\"}\n"
        b"---\n# 2026-07-17 Buglist\n\n"
        b"> \xe6\x9d\xa5\xe6\xba\x90\xef\xbc\x9a\xe4\xba\xba\xe5\xb7\xa5\xe6\x9d\xa5\xe6\xba\x90 | \xce\xb1\n"
        b"> \xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xa5\xe6\x9c\x9f\xef\xbc\x9a2026-07-17\n\n"
        b"<!-- sdflow-issue-block:start id=B1 -->\n## B1: \xe6\x91\x98\xe8\xa6\x81 | \xce\xb1 ## fake ---\n"
        b"> \xe6\x91\x98\xe8\xa6\x81 | \xce\xb1\n> ## fake\n> ---\n\n"
        b"**\xe7\x8e\xb0\xe8\xb1\xa1**\xef\xbc\x9a\xe7\x8e\xb0\xe8\xb1\xa1\xe6\xad\xa3\xe6\x96\x87\n\n"
        b"**\xe6\xa0\xb9\xe5\x9b\xa0**\xef\xbc\x9a\xe6\xa0\xb9\xe5\x9b\xa0\xe6\xad\xa3\xe6\x96\x87\n\n"
        b"**\xe4\xbf\xae\xe5\xa4\x8d\xe6\x96\xb9\xe6\xa1\x88**\xef\xbc\x9a\n- \xe4\xbf\xae\xe5\xa4\x8d\xe4\xb8\x80\n\n"
        b"**\xe5\xbd\xb1\xe5\x93\x8d\xe8\x8c\x83\xe5\x9b\xb4**\xef\xbc\x9a\xe5\xbd\xb1\xe5\x93\x8d\xe6\xad\xa3\xe6\x96\x87\n"
        b"<!-- sdflow-issue-block:end id=B1 -->\n"
    )
    assert path.read_bytes() == expected


def test_todo_add_creates_canonical_frontmatter_lightweight_item(tmp_path):
    payload = {
        "id": "T1",
        "module": "模块|甲\n模块乙",
        "summary": "待办 | α\n第二行",
        "type": "功能增强",
        "status": "OPEN",
        "change": "change|二",
        "batch": "batch|二",
        "project": "项目 | α",
    }

    proc = _run(
        TODO_SCRIPT, tmp_path, "add", "--month", "2026-07", "--time", "2026-07-17 09:30",
        payload=payload,
    )

    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {
        "id": "T1",
        "file": "openspec/issues/todolist/2026-07-todolist.md",
        "status": "OPEN",
        "block": False,
        "time": "2026-07-17 09:30",
        "change": "change|二",
    }
    path = tmp_path / "openspec/issues/todolist/2026-07-todolist.md"
    assert path.read_bytes() == (
        b"---\n"
        b"sdflow-issues:\n"
        b"  schema: 1\n"
        b"  pool: todo\n"
        b"  mode: canonical\n"
        b"  items:\n"
        b"    T1: {\"module\":\"\xe6\xa8\xa1\xe5\x9d\x97|\xe7\x94\xb2\\n\xe6\xa8\xa1\xe5\x9d\x97\xe4\xb9\x99\",\"summary\":\"\xe5\xbe\x85\xe5\x8a\x9e | \xce\xb1\\n\xe7\xac\xac\xe4\xba\x8c\xe8\xa1\x8c\",\"type\":\"\xe5\x8a\x9f\xe8\x83\xbd\xe5\xa2\x9e\xe5\xbc\xba\",\"status\":\"OPEN\",\"time\":\"2026-07-17 09:30\",\"change\":\"change|\xe4\xba\x8c\",\"batch\":\"batch|\xe4\xba\x8c\"}\n"
        b"---\n"
        b"# 2026-07 TODO\n\n"
        b"> \xe9\xa1\xb9\xe7\x9b\xae\xef\xbc\x9a\xe9\xa1\xb9\xe7\x9b\xae | \xce\xb1\n"
    )


def test_bug_add_to_legacy_file_writes_overlay_and_preserves_legacy_bytes(tmp_path):
    path = tmp_path / "openspec/issues/buglist/2026-07-17-buglist.md"
    path.parent.mkdir(parents=True)
    legacy = (
        b"# legacy\n\n## \xe7\x8a\xb6\xe6\x80\x81\xe6\x80\xbb\xe8\xa7\x88\n\n"
        b"| ID | \xe6\xa8\xa1\xe5\x9d\x97 | \xe9\x97\xae\xe9\xa2\x98\xe6\x91\x98\xe8\xa6\x81 | \xe4\xbc\x98\xe5\x85\x88\xe7\xba\xa7 | \xe7\x8a\xb6\xe6\x80\x81 | \xe6\x97\xb6\xe9\x97\xb4 | \xe5\x85\xb3\xe8\x81\x94Change | \xe6\x89\xb9\xe6\xac\xa1 |\n"
        b"|----|------|----------|--------|------|------|------------|------|\n"
        b"| B1 | old.c | \xe6\x97\xa7\xe9\x97\xae\xe9\xa2\x98 | P2 | OPEN | 08:00 | old-change | |\n\n"
        b"---\n\n## B1: \xe6\x97\xa7\xe9\x97\xae\xe9\xa2\x98\n\n| \xe5\xb1\x9e\xe6\x80\xa7 | \xe5\x80\xbc |\n|------|------|\n| \xe7\x8a\xb6\xe6\x80\x81 | OPEN |\n\n**\xe6\xa0\xb9\xe5\x9b\xa0**\xef\xbc\x9a\xe6\x97\xa7\xe6\xa0\xb9\xe5\x9b\xa0\n"
    )
    path.write_bytes(legacy)
    payload = {
        "id": "B2", "module": "new|m", "summary": "new | issue",
        "priority": "P1", "phenomenon": "new symptom", "change": "new-change",
    }

    proc = _run(BUG_SCRIPT, tmp_path, "add", "--date", "2026-07-17", "--time", "09:31",
                payload=payload)

    assert proc.returncode == 0, proc.stderr
    expected_prefix = (
        b"---\nsdflow-issues:\n  schema: 1\n  pool: bug\n  mode: overlay\n  items:\n"
        b"    B2: {\"module\":\"new|m\",\"summary\":\"new | issue\",\"priority\":\"P1\",\"status\":\"OPEN\",\"time\":\"09:31\",\"change\":\"new-change\",\"batch\":null}\n"
        b"---\n"
    )
    expected_block = (
        b"\n<!-- sdflow-issue-block:start id=B2 -->\n"
        b"## B2: new | issue\n"
        b"> new | issue\n\n"
        b"**\xe7\x8e\xb0\xe8\xb1\xa1**\xef\xbc\x9anew symptom\n\n"
        b"**\xe6\xa0\xb9\xe5\x9b\xa0**\xef\xbc\x9a<\xe5\xbe\x85\xe5\x88\x86\xe6\x9e\x90>\n\n"
        b"**\xe4\xbf\xae\xe5\xa4\x8d\xe6\x96\xb9\xe6\xa1\x88**\xef\xbc\x9a\n- <\xe5\xbe\x85\xe8\xa1\xa5\xe5\x85\x85>\n\n"
        b"**\xe5\xbd\xb1\xe5\x93\x8d\xe8\x8c\x83\xe5\x9b\xb4**\xef\xbc\x9a<\xe5\xbe\x85\xe8\xaf\x84\xe4\xbc\xb0>\n"
        b"<!-- sdflow-issue-block:end id=B2 -->\n"
    )
    assert path.read_bytes() == expected_prefix + legacy + expected_block


def test_bug_set_status_promotes_legacy_item_without_rewriting_old_bytes(tmp_path):
    path = tmp_path / "openspec/issues/buglist/2026-07-17-buglist.md"
    path.parent.mkdir(parents=True)
    before_heading = (
        b"# legacy\n\n## \xe7\x8a\xb6\xe6\x80\x81\xe6\x80\xbb\xe8\xa7\x88\n\n"
        b"| ID | \xe6\xa8\xa1\xe5\x9d\x97 | \xe9\x97\xae\xe9\xa2\x98\xe6\x91\x98\xe8\xa6\x81 | \xe4\xbc\x98\xe5\x85\x88\xe7\xba\xa7 | \xe7\x8a\xb6\xe6\x80\x81 | \xe6\x97\xb6\xe9\x97\xb4 | \xe5\x85\xb3\xe8\x81\x94Change | \xe6\x89\xb9\xe6\xac\xa1 |\n"
        b"|----|------|----------|--------|------|------|------------|------|\n"
        b"| B1 | old.c | old summary | P2 | OPEN | 08:00 | old-change | old-batch |\n\n"
        b"---\n\n"
    )
    legacy_block = (
        b"## B1: old title\n\n| \xe5\xb1\x9e\xe6\x80\xa7 | \xe5\x80\xbc |\n|------|------|\n"
        b"| \xe6\xa8\xa1\xe5\x9d\x97 | `old.c` |\n| \xe7\x8a\xb6\xe6\x80\x81 | OPEN |\n\n"
        b"**\xe6\xa0\xb9\xe5\x9b\xa0**\xef\xbc\x9alegacy rootcause\n"
    )
    path.write_bytes(before_heading + legacy_block)

    proc = _run(BUG_SCRIPT, tmp_path, "set-status", "--id", "B1", "--to", "VERIFIED",
                "--date", "2026-07-18")

    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {
        "id": "B1", "old": "OPEN", "new": "VERIFIED",
        "file": "openspec/issues/buglist/2026-07-17-buglist.md",
    }
    prefix = (
        b"---\nsdflow-issues:\n  schema: 1\n  pool: bug\n  mode: overlay\n  items:\n"
        b"    B1: {\"module\":\"old.c\",\"summary\":\"old summary\",\"priority\":\"P2\",\"status\":\"VERIFIED\",\"time\":\"08:00\",\"change\":\"old-change\",\"batch\":\"old-batch\"}\n"
        b"---\n"
    )
    assert path.read_bytes() == (
        prefix + before_heading
        + b"<!-- sdflow-issue-block:start id=B1 -->\n"
        + legacy_block
        + b"> 2026-07-18 \xe7\x8a\xb6\xe6\x80\x81\xef\xbc\x9aOPEN \xe2\x86\x92 VERIFIED\n"
        + b"<!-- sdflow-issue-block:end id=B1 -->\n"
    )


def test_todo_set_status_promotes_blockless_legacy_item_with_minimal_marker_block(tmp_path):
    path = tmp_path / "openspec/issues/todolist/2026-07-todolist.md"
    path.parent.mkdir(parents=True)
    legacy = (
        b"# legacy todo\n\n## \xe7\x8a\xb6\xe6\x80\x81\xe6\x80\xbb\xe8\xa7\x88\n\n"
        b"| ID | \xe6\xa8\xa1\xe5\x9d\x97 | \xe6\x8f\x8f\xe8\xbf\xb0 | \xe7\xb1\xbb\xe5\x9e\x8b | \xe7\x8a\xb6\xe6\x80\x81 | \xe6\x97\xb6\xe9\x97\xb4 | \xe5\x85\xb3\xe8\x81\x94Change | \xe6\x89\xb9\xe6\xac\xa1 |\n"
        b"|----|------|------|------|------|------|------------|------|\n"
        b"| T1 | todo.c | old summary | \xe5\x8a\x9f\xe8\x83\xbd\xe5\xa2\x9e\xe5\xbc\xba | OPEN | 2026-07-17 08:00 | old-change | |\n"
    )
    path.write_bytes(legacy)

    proc = _run(TODO_SCRIPT, tmp_path, "set-status", "--id", "T1", "--to", "WONTDO",
                "--reason", "later | no budget", "--month", "2026-08")

    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {
        "id": "T1", "old": "OPEN", "new": "WONTDO",
        "file": "openspec/issues/todolist/2026-07-todolist.md",
    }
    prefix = (
        b"---\nsdflow-issues:\n  schema: 1\n  pool: todo\n  mode: overlay\n  items:\n"
        b"    T1: {\"module\":\"todo.c\",\"summary\":\"old summary\",\"type\":\"\xe5\x8a\x9f\xe8\x83\xbd\xe5\xa2\x9e\xe5\xbc\xba\",\"status\":\"WONTDO\",\"time\":\"2026-07-17 08:00\",\"change\":\"old-change\",\"batch\":null}\n"
        b"---\n"
    )
    block = (
        b"\n<!-- sdflow-issue-block:start id=T1 -->\n"
        b"## T1: old summary\n> old summary\n"
        b"> 2026-08 \xe7\x8a\xb6\xe6\x80\x81\xef\xbc\x9aOPEN \xe2\x86\x92 WONTDO\xef\xbc\x88later | no budget\xef\xbc\x89\n"
        b"<!-- sdflow-issue-block:end id=T1 -->\n"
    )
    assert path.read_bytes() == prefix + legacy + block


def test_bug_triage_promotes_legacy_alias_to_canonical_overlay_and_marker(tmp_path):
    path = tmp_path / "openspec/issues/buglist/2026-07-17-buglist.md"
    path.parent.mkdir(parents=True)
    legacy_row = b"| A007 | old.c | alias summary | P2 | OPEN | 08:00 | old-change | |\n"
    raw = (
        b"# legacy\n\n## \xe7\x8a\xb6\xe6\x80\x81\xe6\x80\xbb\xe8\xa7\x88\n\n"
        b"| ID | \xe6\xa8\xa1\xe5\x9d\x97 | \xe9\x97\xae\xe9\xa2\x98\xe6\x91\x98\xe8\xa6\x81 | \xe4\xbc\x98\xe5\x85\x88\xe7\xba\xa7 | \xe7\x8a\xb6\xe6\x80\x81 | \xe6\x97\xb6\xe9\x97\xb4 | \xe5\x85\xb3\xe8\x81\x94Change | \xe6\x89\xb9\xe6\xac\xa1 |\n"
        b"|----|------|----------|--------|------|------|------------|------|\n"
        + legacy_row
        + b"\n---\n\n## A007: alias title\n\n**\xe6\xa0\xb9\xe5\x9b\xa0**\xef\xbc\x9alegacy rootcause\n"
    )
    path.write_bytes(raw)

    proc = _run(BUG_SCRIPT, tmp_path, "triage", "--id", "A007", "--批次", "batch | x")

    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {
        "id": "A7", "old_status": "OPEN", "new_status": "PROPOSED",
        "batch": "batch | x", "file": "openspec/issues/buglist/2026-07-17-buglist.md",
    }
    written = path.read_bytes()
    assert legacy_row in written
    assert b"    A7: {\"module\":\"old.c\",\"summary\":\"alias summary\",\"priority\":\"P2\",\"status\":\"PROPOSED\",\"time\":\"08:00\",\"change\":\"old-change\",\"batch\":\"batch | x\"}" in written
    assert b"<!-- sdflow-issue-block:start id=A7 -->\n## A007: alias title" in written
    assert b"> 2026-07-17 \xe7\x8a\xb6\xe6\x80\x81\xef\xbc\x9aOPEN \xe2\x86\x92 PROPOSED\n<!-- sdflow-issue-block:end id=A7 -->" in written


def test_legacy_promotion_rejects_preexisting_marker_collision_without_writing(tmp_path):
    path = tmp_path / "openspec/issues/buglist/2026-07-17-buglist.md"
    path.parent.mkdir(parents=True)
    raw = (
        b"# legacy\n\n## \xe7\x8a\xb6\xe6\x80\x81\xe6\x80\xbb\xe8\xa7\x88\n\n"
        b"| ID | M | S | P | X | T | C | B |\n|---|---|---|---|---|---|---|---|\n"
        b"| B1 | old.c | old summary | P2 | OPEN | 08:00 | old-change | |\n\n"
        b"---\n\n## B1: old title\n"
        b"<!-- sdflow-issue-block:start id=B9 -->\ninside\n"
        b"<!-- sdflow-issue-block:end id=B9 -->\n"
        b"**\xe6\xa0\xb9\xe5\x9b\xa0**\xef\xbc\x9alegacy rootcause\n"
    )
    path.write_bytes(raw)

    proc = _run(BUG_SCRIPT, tmp_path, "set-status", "--id", "B1", "--to", "VERIFIED")

    assert proc.returncode != 0
    assert proc.stdout == ""
    assert "marker" in proc.stderr
    assert path.read_bytes() == raw


def test_todo_add_to_legacy_file_creates_overlay_without_table_row(tmp_path):
    path = tmp_path / "openspec/issues/todolist/2026-07-todolist.md"
    path.parent.mkdir(parents=True)
    raw = (
        b"# legacy todo\n\n## \xe7\x8a\xb6\xe6\x80\x81\xe6\x80\xbb\xe8\xa7\x88\n\n"
        b"| ID | M | S | K | X | T | C | B |\n|---|---|---|---|---|---|---|---|\n"
        b"| T1 | old.c | old summary | \xe5\x8a\x9f\xe8\x83\xbd\xe5\xa2\x9e\xe5\xbc\xba | OPEN | 08:00 | old-change | |\n"
    )
    path.write_bytes(raw)
    payload = {
        "id": "T2", "module": "new|todo", "summary": "new | todo", "type": "功能增强",
        "change": "new-change",
    }

    proc = _run(TODO_SCRIPT, tmp_path, "add", "--month", "2026-07", "--time", "09:00",
                payload=payload)

    assert proc.returncode == 0, proc.stderr
    written = path.read_bytes()
    assert written.endswith(raw)
    assert b"  mode: overlay\n" in written
    assert b"    T2: {\"module\":\"new|todo\",\"summary\":\"new | todo\"" in written
    assert b"| T2 |" not in written


def test_todo_triage_mutates_canonical_index_and_creates_history_block(tmp_path):
    add = _run(
        TODO_SCRIPT, tmp_path, "add", "--month", "2026-07", "--time", "09:00",
        payload={"id": "T1", "module": "todo.c", "summary": "light item",
                 "type": "功能增强", "change": "change-a"},
    )
    assert add.returncode == 0, add.stderr

    proc = _run(TODO_SCRIPT, tmp_path, "triage", "--id", "T1", "--批次", "batch | y")

    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {
        "id": "T1", "old_status": "OPEN", "new_status": "PROPOSED",
        "batch": "batch | y", "file": "openspec/issues/todolist/2026-07-todolist.md",
    }
    raw = (tmp_path / "openspec/issues/todolist/2026-07-todolist.md").read_bytes()
    assert b'"status":"PROPOSED"' in raw and b'"batch":"batch | y"' in raw
    assert b"| T1 |" not in raw
    assert b"<!-- sdflow-issue-block:start id=T1 -->\n## T1: light item\n> light item\n" in raw
    assert b"OPEN \xe2\x86\x92 PROPOSED" in raw


def test_marker_prose_display_title_and_line_safety_helpers_have_golden_behavior():
    for module in (BUG, TODO):
        assert module._display_title("  first\tsecond\n---  ") == "first second ---"
        assert module._summary_blockquote("a\n\nb") == "> a\n> \n> b"
        assert module._summary_blockquote("a\r\nb\rc\n") == "> a\n> b\n> c\n> "
        assert module._escape_user_markers(
            "before\n<!-- sdflow-issue-block:start id=A7 -->\nafter"
        ) == "before\n&lt;!-- sdflow-issue-block:start id=A7 --&gt;\nafter"
        assert module._escape_user_markers(
            "before\r<!-- sdflow-issue-block:end id=A7 -->\rafter"
        ) == "before\n&lt;!-- sdflow-issue-block:end id=A7 --&gt;\nafter"
        module._reject_line_unsafe("legal | value", "field")
        with pytest.raises(ValueError, match=r"ERROR: .*; cause: .*; fix: "):
            module._reject_line_unsafe("bad\nvalue", "field")
        with pytest.raises(ValueError, match=r"ERROR: .*; cause: .*; fix: "):
            module._reject_line_unsafe("bad\0value", "field")


def test_dated_writer_call_graph_has_no_legacy_table_or_text_writer_calls():
    for module in (BUG, TODO):
        for name in ("cmd_add", "cmd_set_status", "cmd_triage"):
            source = inspect.getsource(getattr(module, name))
            assert "atomic_write(" not in source
            assert "_reject_cell_unsafe" not in source
            assert "parse_table_rows(" not in source
            assert "split_sections(" not in source
            assert "atomic_write_bytes(" in source


def test_overlay_writer_preserves_bom_crlf_and_external_namespace_bytes(tmp_path):
    path = tmp_path / "openspec/issues/buglist/2026-07-17-buglist.md"
    path.parent.mkdir(parents=True)
    external = b"external: |\r\n  exact: \xce\xb1\r\n# keep-comment\r\n"
    body = (
        b"# legacy\r\n\r\n## \xe7\x8a\xb6\xe6\x80\x81\xe6\x80\xbb\xe8\xa7\x88\r\n\r\n"
        b"| ID | M | S | P | X | T | C | B |\r\n|---|---|---|---|---|---|---|---|\r\n"
        b"| B1 | old.c | old | P2 | OPEN | 08:00 | old-change | |\r\n\r\n"
        b"---\r\n\r\n## B1: old\r\n\r\n**\xe6\xa0\xb9\xe5\x9b\xa0**\xef\xbc\x9aold root\r\n"
    )
    raw = b"\xef\xbb\xbf---\r\n" + external + b"---\r\n" + body
    path.write_bytes(raw)

    proc = _run(
        BUG_SCRIPT, tmp_path, "add", "--date", "2026-07-17", "--time", "09:31",
        payload={"id": "B2", "module": "new.c", "summary": "new",
                 "priority": "P1", "phenomenon": "new symptom"},
    )

    assert proc.returncode == 0, proc.stderr
    written = path.read_bytes()
    assert written.startswith(b"\xef\xbb\xbf---\r\n" + external + b"sdflow-issues:\r\n")
    assert body in written
    assert written.count(b"\n") == written.count(b"\r\n"), "writer introduced lone LF into CRLF file"


def _legacy_bug_bytes(item_id="B1", status="OPEN", block_suffix=b"\n"):
    return (
        b"# legacy\n\n## \xe7\x8a\xb6\xe6\x80\x81\xe6\x80\xbb\xe8\xa7\x88\n\n"
        b"| ID | M | S | P | X | T | C | B |\n|---|---|---|---|---|---|---|---|\n"
        + f"| {item_id} | old.c | old summary | P2 | {status} | 08:00 | old-change | |\n\n".encode()
        + b"---\n\n" + f"## {item_id}: old title\n\n".encode()
        + b"**\xe6\xa0\xb9\xe5\x9b\xa0**\xef\xbc\x9alegacy rootcause" + block_suffix
    )


def _legacy_todo_bytes(item_id="T1", status="OPEN"):
    return (
        b"# legacy todo\n\n## \xe7\x8a\xb6\xe6\x80\x81\xe6\x80\xbb\xe8\xa7\x88\n\n"
        b"| ID | M | S | K | X | T | C | B |\n|---|---|---|---|---|---|---|---|\n"
        + f"| {item_id} | todo.c | old summary | 功能增强 | {status} | 08:00 | old-change | |\n".encode()
    )


def test_marker_line_grammar_escapes_trailing_space_user_marker(tmp_path):
    proc = _run(
        BUG_SCRIPT, tmp_path, "add", "--date", "2026-07-17", "--time", "09:00",
        payload={"id": "B1", "module": "m", "summary": "s", "priority": "P1",
                 "phenomenon": "<!-- sdflow-issue-block:start id=A7 -->   "},
    )
    assert proc.returncode == 0, proc.stderr
    path = tmp_path / "openspec/issues/buglist/2026-07-17-buglist.md"
    raw = path.read_bytes()
    assert b"&lt;!-- sdflow-issue-block:start id=A7 --&gt;   " in raw
    assert BUG.parse_recorder_document(raw, "bug")["marker_problems"] == []


def test_existing_broken_marker_document_rejects_add_without_writing(tmp_path):
    path = tmp_path / "openspec/issues/buglist/2026-07-17-buglist.md"
    add = _run(
        BUG_SCRIPT, tmp_path, "add", "--date", "2026-07-17", "--time", "08:00",
        payload={"id": "B1", "module": "m", "summary": "old", "priority": "P1",
                 "phenomenon": "old"},
    )
    assert add.returncode == 0, add.stderr
    raw = path.read_bytes().replace(b"<!-- sdflow-issue-block:end id=B1 -->\n", b"")
    path.write_bytes(raw)
    proc = _run(
        BUG_SCRIPT, tmp_path, "add", "--date", "2026-07-17", "--time", "09:00",
        payload={"id": "B2", "module": "m", "summary": "s", "priority": "P1",
                 "phenomenon": "p"},
    )
    assert proc.returncode != 0
    assert "marker" in proc.stderr
    assert path.read_bytes() == raw


def test_legacy_promotion_rejects_trailing_space_marker_collision_without_writing(tmp_path):
    path = tmp_path / "openspec/issues/buglist/2026-07-17-buglist.md"
    path.parent.mkdir(parents=True)
    raw = _legacy_bug_bytes(block_suffix=(
        b"\n<!-- sdflow-issue-block:start id=A7 -->   \ninside\n"
        b"<!-- sdflow-issue-block:end id=A7 -->\t\n"
    ))
    path.write_bytes(raw)
    proc = _run(BUG_SCRIPT, tmp_path, "set-status", "--id", "B1", "--to", "VERIFIED")
    assert proc.returncode != 0
    assert "marker" in proc.stderr
    assert path.read_bytes() == raw


@pytest.mark.parametrize("raw_id", ["A7"])
def test_noncanonical_request_does_not_alias_canonical_or_legacy_spelling(tmp_path, raw_id):
    legacy_path = tmp_path / "openspec/issues/buglist/2026-07-17-buglist.md"
    legacy_path.parent.mkdir(parents=True)
    legacy = _legacy_bug_bytes(item_id=raw_id)
    legacy_path.write_bytes(legacy)
    proc = _run(BUG_SCRIPT, tmp_path, "triage", "--id", "A007", "--批次", "b")
    assert proc.returncode != 0
    assert legacy_path.read_bytes() == legacy

    canonical_root = tmp_path / "canonical"
    add = _run(
        BUG_SCRIPT, canonical_root, "add", "--date", "2026-07-17", "--time", "09:00",
        payload={"id": "A7", "module": "m", "summary": "s", "priority": "P1",
                 "phenomenon": "p"},
    )
    assert add.returncode == 0, add.stderr
    canonical_path = canonical_root / "openspec/issues/buglist/2026-07-17-buglist.md"
    canonical = canonical_path.read_bytes()
    proc = _run(BUG_SCRIPT, canonical_root, "triage", "--id", "A007", "--批次", "b")
    assert proc.returncode != 0
    assert canonical_path.read_bytes() == canonical


def test_todo_batch_only_legacy_promotion_creates_minimal_marker_without_history(tmp_path):
    path = tmp_path / "openspec/issues/todolist/2026-07-todolist.md"
    path.parent.mkdir(parents=True)
    raw = _legacy_todo_bytes(status="PROPOSED")
    path.write_bytes(raw)
    proc = _run(TODO_SCRIPT, tmp_path, "triage", "--id", "T1", "--批次", "batch-1")
    assert proc.returncode == 0, proc.stderr
    written = path.read_bytes()
    assert b"<!-- sdflow-issue-block:start id=T1 -->\n## T1: old summary\n> old summary\n" in written
    assert b"<!-- sdflow-issue-block:end id=T1 -->\n" in written
    assert b"\xe7\x8a\xb6\xe6\x80\x81\xef\xbc\x9aPROPOSED \xe2\x86\x92 PROPOSED" not in written
    assert TODO.parse_recorder_document(written, "todo")["problems"] == []


@pytest.mark.parametrize(
    ("command", "status", "expected_history", "trailing_eol"),
    [
        ("set-status", "OPEN", True, False),
        ("set-status", "OPEN", True, True),
        ("triage", "FIXED", False, False),
        ("triage", "FIXED", False, True),
    ],
)
def test_legacy_bug_eof_boundary_matrix_preserves_lines_before_history_or_end(
        tmp_path, command, status, expected_history, trailing_eol):
    path = tmp_path / "openspec/issues/buglist/2026-07-17-buglist.md"
    path.parent.mkdir(parents=True)
    raw = _legacy_bug_bytes(status=status, block_suffix=b"\n" if trailing_eol else b"")
    path.write_bytes(raw)
    if command == "set-status":
        proc = _run(BUG_SCRIPT, tmp_path, command, "--id", "B1", "--to", "VERIFIED")
    else:
        proc = _run(BUG_SCRIPT, tmp_path, command, "--id", "B1", "--批次", "b")
    assert proc.returncode == 0, proc.stderr
    written = path.read_bytes()
    block_start = raw.index(b"## B1: old title")
    assert raw[:block_start] in written
    marker_and_old_block = (
        b"<!-- sdflow-issue-block:start id=B1 -->\n" + raw[block_start:]
    )
    assert marker_and_old_block in written
    suffix = written.split(marker_and_old_block, 1)[1]
    assert suffix.startswith(b"\n") is (not trailing_eol)
    assert (b"OPEN \xe2\x86\x92 VERIFIED" in suffix) is expected_history
    assert b"<!-- sdflow-issue-block:end id=B1 -->\n" in suffix
    parsed = BUG.parse_recorder_document(written, "bug")
    assert parsed["marker_problems"] == []
    assert not [problem for problem in parsed["problems"] if "marker" in problem]
