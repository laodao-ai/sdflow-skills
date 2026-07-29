import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import migrate_legacy as migrate  # noqa: E402
from sdflow_issues_core import parse_recorder_document, render_recorder_namespace  # noqa: E402


SCRIPT = str(Path(__file__).parent.parent / "scripts" / "migrate_legacy.py")


def _legacy_bug():
    return (
        "# Bugs\n\n"
        "## 状态总览\n\n"
        "| ID | 模块 | 问题摘要 | 优先级 | 状态 | 时间 | 关联Change | 批次 |\n"
        "|----|------|----------|--------|------|------|------------|------|\n"
        "| B1 | core | old bug | P2 | OPEN | 10:00 |  | — |\n\n"
        "---\n\n"
        "## B1: old bug\n\n"
        "**现象**：legacy bytes stay\n"
    ).encode("utf-8")


def _legacy_todo():
    return (
        "# Todos\n\n"
        "## 状态总览\n\n"
        "| ID | 模块 | 改进项 | 类型 | 状态 | 记录时间 | 来源Change | 批次 |\n"
        "|----|------|--------|------|------|----------|------------|------|\n"
        "| T1 | tests | improve | 技术债 | wontfix | 2026-01-01 10:00 |  |  |\n"
    ).encode("utf-8")


def _write_legacy_repo(root):
    bug_path = root / "openspec/issues/buglist/2026-01-01-buglist.md"
    todo_path = root / "openspec/issues/todolist/2026-01-todolist.md"
    bug_path.parent.mkdir(parents=True)
    todo_path.parent.mkdir(parents=True)
    bug_path.write_bytes(_legacy_bug())
    todo_path.write_bytes(_legacy_todo())
    return bug_path, todo_path


def _maps():
    return {"todo": {"技术债": "代码质量"}}, {"todo": {"wontfix": "WONTDO"}}


def test_audit_requires_explicit_enum_mappings_and_preserves_bytes(tmp_path):
    bug_path, todo_path = _write_legacy_repo(tmp_path)
    before = {bug_path: bug_path.read_bytes(), todo_path: todo_path.read_bytes()}

    migration = migrate.build_migration(str(tmp_path))

    assert migration["items_changed"] == 2
    assert migration["files_changed"] == 2
    assert {(item["id"], item["field"]) for item in migration["unresolved"]} == {
        ("T1", "type"),
        ("T1", "status"),
    }
    assert bug_path.read_bytes() == before[bug_path]
    assert todo_path.read_bytes() == before[todo_path]
    with pytest.raises(ValueError, match="未解析字段"):
        migrate.apply_migration(migration)
    assert bug_path.read_bytes() == before[bug_path]
    assert todo_path.read_bytes() == before[todo_path]


def test_apply_promotes_only_invalid_rows_and_is_idempotent(tmp_path):
    bug_path, todo_path = _write_legacy_repo(tmp_path)
    bug_legacy_row = b"| B1 | core | old bug | P2 | OPEN | 10:00 |  | \xe2\x80\x94 |\n"
    todo_legacy_row = (
        "| T1 | tests | improve | 技术债 | wontfix | 2026-01-01 10:00 |  |  |\n"
    ).encode("utf-8")
    specific_map, status_map = _maps()

    migration = migrate.build_migration(str(tmp_path), specific_map, status_map)
    assert migration["items_changed"] == 2
    assert migration["files_changed"] == 2
    assert migration["unresolved"] == []
    migrate.apply_migration(migration)

    bug_written = bug_path.read_bytes()
    todo_written = todo_path.read_bytes()
    assert bug_legacy_row in bug_written
    assert b"**\xe7\x8e\xb0\xe8\xb1\xa1**\xef\xbc\x9alegacy bytes stay\n" in bug_written
    assert todo_legacy_row in todo_written
    bug = parse_recorder_document(bug_written, "bug")
    todo = parse_recorder_document(todo_written, "todo")
    assert bug["model"]["mode"] == "overlay"
    assert bug["model"]["items"]["B1"]["change"] is None
    assert bug["model"]["items"]["B1"]["batch"] is None
    assert "B1" in bug["marker_blocks"]
    assert todo["model"]["items"]["T1"]["type"] == "代码质量"
    assert todo["model"]["items"]["T1"]["status"] == "WONTDO"
    assert todo["model"]["items"]["T1"]["change"] is None
    assert todo["marker_blocks"] == {}

    second = migrate.build_migration(str(tmp_path), specific_map, status_map)
    assert second["items_changed"] == 0
    assert second["files_changed"] == 0
    assert second["unresolved"] == []


def test_cli_audit_is_read_only_json_report(tmp_path):
    bug_path, todo_path = _write_legacy_repo(tmp_path)
    before = {bug_path: bug_path.read_bytes(), todo_path: todo_path.read_bytes()}

    proc = subprocess.run(
        [sys.executable, SCRIPT, "--root", str(tmp_path), "audit"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["mode"] == "audit"
    assert report["items_changed"] == 2
    assert len(report["unresolved"]) == 2
    assert bug_path.read_bytes() == before[bug_path]
    assert todo_path.read_bytes() == before[todo_path]


def test_cli_apply_refuses_unresolved_before_any_write(tmp_path):
    bug_path, todo_path = _write_legacy_repo(tmp_path)
    before = {bug_path: bug_path.read_bytes(), todo_path: todo_path.read_bytes()}

    proc = subprocess.run(
        [sys.executable, SCRIPT, "--root", str(tmp_path), "apply", "--no-reindex"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert proc.returncode == 2
    assert "未解析字段" in proc.stderr
    assert bug_path.read_bytes() == before[bug_path]
    assert todo_path.read_bytes() == before[todo_path]


def test_apply_normalizes_placeholder_already_in_frontmatter(tmp_path):
    path = tmp_path / "openspec/issues/todolist/2026-02-todolist.md"
    path.parent.mkdir(parents=True)
    model = {
        "schema": 1,
        "pool": "todo",
        "mode": "canonical",
        "items": {
            "T2": {
                "module": "docs",
                "summary": "frontmatter placeholder",
                "type": "代码质量",
                "status": "OPEN",
                "time": "2026-02-01 10:00",
                "change": None,
                "batch": "—",
            }
        },
    }
    path.write_bytes(
        b"---\n" + render_recorder_namespace(model) + b"---\n# canonical\n"
    )

    migration = migrate.build_migration(str(tmp_path))

    assert migration["items_changed"] == 1
    assert migration["changes"][0]["source"] == "frontmatter"
    assert migration["changes"][0]["fields"]["batch"] == {"from": "—", "to": None}
    migrate.apply_migration(migration)
    written = parse_recorder_document(path.read_bytes(), "todo")
    assert written["model"]["items"]["T2"]["batch"] is None
    assert written["body"] == b"# canonical\n"


@pytest.mark.parametrize(
    ("argument", "mapping", "needle"),
    [
        ("--specific-map-json", '{"todo":{"old":"未知类型"}}', "specific mapping"),
        ("--status-map-json", '{"todo":{"old":"UNKNOWN"}}', "status mapping"),
    ],
)
def test_cli_rejects_mapping_targets_outside_current_schema(tmp_path, argument, mapping, needle):
    _write_legacy_repo(tmp_path)

    proc = subprocess.run(
        [sys.executable, SCRIPT, "--root", str(tmp_path), argument, mapping, "audit"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert proc.returncode == 2
    assert needle in proc.stderr
