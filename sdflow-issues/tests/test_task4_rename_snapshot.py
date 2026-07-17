import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import issues as issues_mod
from issues import (
    _reindex_core,
    classify_batch_rename,
    read_rename_snapshot,
    render_recorder_namespace,
    retag_rename_snapshot,
    validate_scan_envelope,
)

BUGLIST_SCRIPT = str(Path(__file__).parents[2] / "sdflow-buglist" / "scripts" / "buglist.py")
TODOLIST_SCRIPT = str(Path(__file__).parents[2] / "sdflow-todolist" / "scripts" / "todolist.py")


def _valid_bug_item(**overrides):
    item = {
        "id": "B1",
        "module": "core",
        "summary": "summary",
        "priority": "P2",
        "status": "OPEN",
        "time": "10:00",
        "change": "chg",
        "batch": "batch-old",
        "file": "openspec/issues/buglist/2026-01-01-buglist.md",
    }
    item.update(overrides)
    return item


@pytest.mark.parametrize(
    ("payload", "needle"),
    [
        ("{", "JSON"),
        (json.dumps({"bugs": []}), "problems"),
        (json.dumps({"bugs": {}, "problems": []}), "bugs"),
        (json.dumps({"bugs": [_valid_bug_item(file=None)], "problems": []}), "file"),
        (json.dumps({"bugs": [_valid_bug_item(priority="P9")], "problems": []}), "priority"),
    ],
)
def test_validate_scan_envelope_rejects_protocol_drift(payload, needle):
    with pytest.raises(ValueError, match=needle):
        validate_scan_envelope(payload, "bug")


def test_validate_scan_envelope_returns_items_and_problems():
    payload = json.dumps({"bugs": [_valid_bug_item()], "problems": ["visible"]})

    items, problems = validate_scan_envelope(payload, "bug")

    assert items == [_valid_bug_item()]
    assert problems == ["visible"]


@pytest.mark.parametrize(
    "payload",
    [
        "{",
        json.dumps({"bugs": []}),
        json.dumps({"bugs": {}, "problems": []}),
        json.dumps({"bugs": [_valid_bug_item(file=None)], "problems": []}),
        json.dumps({"bugs": [_valid_bug_item(status="NEW_ENUM")], "problems": []}),
    ],
)
def test_reindex_consumer_drift_preserves_existing_index_and_batches(tmp_path, monkeypatch, payload):
    issues_dir = tmp_path / "openspec" / "issues"
    issues_dir.mkdir(parents=True)
    index = issues_dir / "INDEX.md"
    batches = issues_dir / "batches.md"
    index.write_bytes(b"old-index\n")
    batches.write_bytes(b"old-batches\n")

    class Proc:
        returncode = 0
        stdout = payload
        stderr = ""

    monkeypatch.setattr(issues_mod.subprocess, "run", lambda *_args, **_kwargs: Proc())

    with pytest.raises(ValueError):
        _reindex_core(str(tmp_path))

    assert index.read_bytes() == b"old-index\n"
    assert batches.read_bytes() == b"old-batches\n"


def _canonical_document(pool, item_id, item):
    model = {"schema": 1, "pool": pool, "mode": "canonical", "items": {item_id: item}}
    block = b""
    if pool == "bug":
        block = (
            f"<!-- sdflow-issue-block:start id={item_id} -->\n"
            f"## {item_id}: fixture\n"
            f"<!-- sdflow-issue-block:end id={item_id} -->\n"
        ).encode()
    return b"---\n" + render_recorder_namespace(model) + b"---\n" + block


def _write_canonical(root, pool, filename, item_id, item):
    directory = root / "openspec" / "issues" / ("buglist" if pool == "bug" else "todolist")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_bytes(_canonical_document(pool, item_id, item))
    return path


def test_read_rename_snapshot_reads_and_parses_each_dated_file_once(tmp_path, monkeypatch):
    bug = _valid_bug_item()
    bug.pop("id")
    bug.pop("file")
    todo = {
        "module": "docs",
        "summary": "todo",
        "type": "代码质量",
        "status": "OPEN",
        "time": "11:00",
        "change": "chg",
        "batch": "batch-old",
    }
    bug_path = _write_canonical(tmp_path, "bug", "2026-01-01-buglist.md", "B1", bug)
    todo_path = _write_canonical(tmp_path, "todo", "2026-01-todolist.md", "T1", todo)
    instrumentation = {"reads": {}, "parses": {}}

    def no_subprocess(*_args, **_kwargs):
        raise AssertionError("direct rename snapshot must not invoke recorder scan subprocess")

    monkeypatch.setattr(issues_mod.subprocess, "run", no_subprocess)
    snapshot = read_rename_snapshot(str(tmp_path), instrumentation=instrumentation)

    assert {item["id"] for item in snapshot["items"]} == {"B1", "T1"}
    assert snapshot["problems"] == []
    assert {document["path"] for document in snapshot["documents"]} == {str(bug_path), str(todo_path)}
    assert all(isinstance(document["raw"], bytes) for document in snapshot["documents"])
    assert all("namespace_span" in document and "model" in document for document in snapshot["documents"])
    expected_rel = {
        "openspec/issues/buglist/2026-01-01-buglist.md",
        "openspec/issues/todolist/2026-01-todolist.md",
    }
    assert instrumentation == {
        "reads": {path: 1 for path in expected_rel},
        "parses": {path: 1 for path in expected_rel},
    }


@pytest.mark.parametrize("item_batches", [["batch-old"], [], ["other"]])
def test_classify_batch_rename_accepts_first_execution_without_new_orphans(item_batches):
    items = [{"id": f"B{index + 1}", "batch": batch} for index, batch in enumerate(item_batches)]
    assert classify_batch_rename(
        {"batch-old": {"renamed_from": None}}, items, "batch-old", "batch-new"
    ) == "first"


@pytest.mark.parametrize(
    "item_batches",
    [["batch-old"], ["batch-old", "batch-new"], ["batch-new"], []],
)
def test_classify_batch_rename_accepts_provenance_matched_retry(item_batches):
    items = [{"id": f"B{index + 1}", "batch": batch} for index, batch in enumerate(item_batches)]
    assert classify_batch_rename(
        {"batch-new": {"renamed_from": "batch-old"}}, items, "batch-old", "batch-new"
    ) == "retry"


@pytest.mark.parametrize(
    ("registry", "item_batches", "needle"),
    [
        ({"batch-old": {}, "batch-new": {}}, ["batch-old"], "同时存在"),
        ({}, ["batch-old"], "不存在"),
        ({"batch-new": {}}, ["batch-new"], "unknown source"),
        ({"batch-new": {"renamed_from": "somewhere-else"}}, ["batch-new"], "unknown source"),
        ({"batch-old": {}}, ["batch-new"], "orphan"),
    ],
)
def test_classify_batch_rename_rejects_ambiguous_or_orphan_state(registry, item_batches, needle):
    items = [{"id": f"B{index + 1}", "batch": batch} for index, batch in enumerate(item_batches)]
    with pytest.raises(ValueError, match=needle):
        classify_batch_rename(registry, items, "batch-old", "batch-new")


def _legacy_bug_bytes(eol=b"\n", bom=b""):
    lines = [
        "# Bugs",
        "",
        "## 状态总览",
        "",
        "| ID | 模块 | 问题摘要 | 优先级 | 状态 | 时间 | 关联Change | 批次 |",
        "|----|------|----------|--------|------|------|------------|------|",
        "| B1 | core | old | P2 | OPEN | 10:00 | chg | batch-old |",
        "",
        "## B1: old",
        "",
        "**现象**：keep | unicode 雪",
    ]
    return bom + eol.join(line.encode() for line in lines) + eol


def _legacy_todo_bytes(item_id="T1", batch="batch-old"):
    return (
        "# Todos\n\n"
        "## 状态总览\n\n"
        "| ID | 模块 | 改进项 | 类型 | 状态 | 记录时间 | 来源Change | 批次 |\n"
        "|----|------|--------|------|------|----------|------------|------|\n"
        f"| {item_id} | docs | improve | 代码质量 | OPEN | 2026-01-01 10:00 | chg | {batch} |\n"
    ).encode("utf-8")


def test_retag_rename_snapshot_promotes_legacy_without_patching_table_and_preserves_envelope(tmp_path):
    directory = tmp_path / "openspec" / "issues" / "buglist"
    directory.mkdir(parents=True)
    path = directory / "2026-01-01-buglist.md"
    body = _legacy_bug_bytes(eol=b"\r\n")
    raw = (
        b"\xef\xbb\xbf---\r\n"
        b"foreign:\r\n  opaque: keep\r\n"
        b"---\r\n" + body[len(b"\xef\xbb\xbf") :]
    )
    path.write_bytes(raw)
    snapshot = read_rename_snapshot(str(tmp_path))

    updated = retag_rename_snapshot(snapshot, "batch-old", "batch-new")

    document = updated["documents"][0]
    rendered = document["rendered"]
    assert rendered.startswith(b"\xef\xbb\xbf---\r\nforeign:\r\n  opaque: keep\r\n")
    assert b"| B1 | core | old | P2 | OPEN | 10:00 | chg | batch-old |\r\n" in rendered
    assert b'"batch":"batch-new"' in rendered
    assert b"<!-- sdflow-issue-block:start id=B1 -->\r\n## B1: old" in rendered
    assert next(item for item in updated["items"] if item["id"] == "B1")["batch"] == "batch-new"


def test_retag_rename_snapshot_canonicalizes_legacy_alias_without_rewriting_row(tmp_path):
    directory = tmp_path / "openspec" / "issues" / "todolist"
    directory.mkdir(parents=True)
    path = directory / "2026-01-todolist.md"
    path.write_bytes(_legacy_todo_bytes(item_id="A007"))

    updated = retag_rename_snapshot(
        read_rename_snapshot(str(tmp_path)), "batch-old", "batch-new"
    )

    rendered = updated["documents"][0]["rendered"]
    assert b"| A007 | docs | improve |" in rendered
    assert b"    A7:" in rendered
    assert {item["id"] for item in updated["items"]} == {"A7"}


def test_direct_snapshot_matches_recorder_scan_contract_for_canonical_and_legacy(tmp_path):
    bug = _valid_bug_item()
    bug.pop("id")
    bug.pop("file")
    _write_canonical(tmp_path, "bug", "2026-01-01-buglist.md", "B1", bug)
    todo_dir = tmp_path / "openspec" / "issues" / "todolist"
    todo_dir.mkdir(parents=True)
    (todo_dir / "2026-01-todolist.md").write_bytes(_legacy_todo_bytes())

    direct = read_rename_snapshot(str(tmp_path))
    bug_scan = subprocess.run(
        [sys.executable, BUGLIST_SCRIPT, "--root", str(tmp_path), "scan", "--json"],
        capture_output=True, text=True, check=True,
    )
    todo_scan = subprocess.run(
        [sys.executable, TODOLIST_SCRIPT, "--root", str(tmp_path), "scan", "--json"],
        capture_output=True, text=True, check=True,
    )
    expected = []
    for pool, payload, key in (
        ("bug", json.loads(bug_scan.stdout), "bugs"),
        ("todo", json.loads(todo_scan.stdout), "items"),
    ):
        expected.extend([{**item, "pool": pool} for item in payload[key]])

    assert sorted(direct["items"], key=lambda item: item["id"]) == sorted(
        expected, key=lambda item: item["id"]
    )
    assert direct["problems"] == []


def test_reindex_core_uses_supplied_snapshot_without_rescanning(tmp_path, monkeypatch):
    (tmp_path / "openspec" / "issues").mkdir(parents=True)
    (tmp_path / "openspec" / "issues" / "batches.md").write_text(
        "# registry\n\n### batch-new — title\n状态: PLANNED\n成员: (生成)\n优先级: P2\n计划: x\n",
        encoding="utf-8",
    )
    snapshot = {"items": [{**_valid_bug_item(batch="batch-new"), "pool": "bug"}], "problems": []}

    def no_rescan(*_args, **_kwargs):
        raise AssertionError("snapshot reindex must not call read_pool")

    monkeypatch.setattr(issues_mod, "read_pool", no_rescan)
    items, problems = _reindex_core(str(tmp_path), snapshot=snapshot)

    assert items == snapshot["items"]
    assert problems == []
    assert "批次：batch-new" in (tmp_path / "openspec" / "issues" / "INDEX.md").read_text()


def test_batch_rename_uses_direct_snapshot_zero_recorder_scans_and_writes_provenance(
    tmp_path, monkeypatch, capsys
):
    issues_dir = tmp_path / "openspec" / "issues"
    issues_dir.mkdir(parents=True)
    batches = issues_dir / "batches.md"
    batches.write_text(
        "# registry\n\n### batch-old — title\n状态: PLANNED\n成员: (生成) B1\n优先级: P2\n计划: x\n",
        encoding="utf-8",
    )
    bug = _valid_bug_item()
    bug.pop("id")
    bug.pop("file")
    dated = _write_canonical(tmp_path, "bug", "2026-01-01-buglist.md", "B1", bug)
    real_run = issues_mod.subprocess.run
    real_parse = issues_mod.parse_recorder_document
    recorder_scans = []
    parse_calls = []

    def observe_run(command, *args, **kwargs):
        if "scan" in command:
            recorder_scans.append(command)
        return real_run(command, *args, **kwargs)

    def observe_parse(raw, pool):
        parse_calls.append(pool)
        return real_parse(raw, pool)

    monkeypatch.setattr(issues_mod.subprocess, "run", observe_run)
    monkeypatch.setattr(issues_mod, "parse_recorder_document", observe_parse)
    args = types.SimpleNamespace(root=str(tmp_path), old="batch-old", new="batch-new")

    issues_mod.cmd_batch_rename(args)

    assert recorder_scans == []
    assert parse_calls == ["bug"]
    registry = batches.read_text(encoding="utf-8")
    assert "### batch-new — title" in registry
    assert "重命名自: batch-old" in registry
    assert b'"batch":"batch-new"' in dated.read_bytes()
    assert "批次：batch-new" in (issues_dir / "INDEX.md").read_text(encoding="utf-8")
    assert json.loads(capsys.readouterr().out)["items_changed"] == 1


@pytest.mark.parametrize(
    "item_batches",
    [["batch-old", "batch-old"], ["batch-old", "batch-new"], ["batch-new", "batch-new"]],
)
def test_batch_rename_retry_converges_all_old_mixed_and_all_new(tmp_path, item_batches):
    issues_dir = tmp_path / "openspec" / "issues"
    issues_dir.mkdir(parents=True)
    (issues_dir / "batches.md").write_text(
        "# registry\n\n### batch-new — title\n重命名自: batch-old\n状态: PLANNED\n成员: (生成)\n优先级: P2\n计划: x\n",
        encoding="utf-8",
    )
    for index, batch in enumerate(item_batches, start=1):
        bug = _valid_bug_item(batch=batch)
        bug.pop("id")
        bug.pop("file")
        _write_canonical(tmp_path, "bug", f"2026-01-0{index}-buglist.md", f"B{index}", bug)

    issues_mod.cmd_batch_rename(
        types.SimpleNamespace(root=str(tmp_path), old="batch-old", new="batch-new")
    )

    snapshot = read_rename_snapshot(str(tmp_path))
    assert {item["batch"] for item in snapshot["items"]} == {"batch-new"}
    assert "批次：batch-new" in (issues_dir / "INDEX.md").read_text(encoding="utf-8")


def _seed_fault_repo(root):
    issues_dir = root / "openspec" / "issues"
    issues_dir.mkdir(parents=True)
    (issues_dir / "batches.md").write_text(
        "# registry\n\n### batch-old — title\n状态: PLANNED\n成员: (生成) B1\n优先级: P2\n计划: x\n",
        encoding="utf-8",
    )
    bug = _valid_bug_item()
    bug.pop("id")
    bug.pop("file")
    _write_canonical(root, "bug", "2026-01-01-buglist.md", "B1", bug)


@pytest.mark.parametrize("fault_stage", ["registry", "dated", "INDEX", "batches"])
def test_batch_rename_stage_fault_is_nonzero_and_original_command_recovers(
    tmp_path, monkeypatch, fault_stage
):
    _seed_fault_repo(tmp_path)
    original_text_write = issues_mod.atomic_write
    original_bytes_write = issues_mod.atomic_write_bytes
    batch_write_count = 0

    def fault_text_write(path, content):
        nonlocal batch_write_count
        if Path(path).name == "batches.md":
            batch_write_count += 1
            if fault_stage == "registry" and batch_write_count == 1:
                raise OSError("registry injected")
            if fault_stage == "batches" and batch_write_count == 2:
                raise OSError("batches injected")
        if fault_stage == "INDEX" and Path(path).name == "INDEX.md":
            raise OSError("INDEX injected")
        return original_text_write(path, content)

    def fault_bytes_write(path, content):
        if fault_stage == "dated":
            raise OSError("dated injected")
        return original_bytes_write(path, content)

    monkeypatch.setattr(issues_mod, "atomic_write", fault_text_write)
    monkeypatch.setattr(issues_mod, "atomic_write_bytes", fault_bytes_write)
    args = types.SimpleNamespace(root=str(tmp_path), old="batch-old", new="batch-new")

    with pytest.raises(ValueError) as exc_info:
        issues_mod.cmd_batch_rename(args)

    diagnostic = str(exc_info.value)
    assert f"stage={fault_stage}" in diagnostic
    assert "batch rename batch-old batch-new" in diagnostic

    monkeypatch.setattr(issues_mod, "atomic_write", original_text_write)
    monkeypatch.setattr(issues_mod, "atomic_write_bytes", original_bytes_write)
    issues_mod.cmd_batch_rename(args)
    assert {item["batch"] for item in read_rename_snapshot(str(tmp_path))["items"]} == {"batch-new"}
    assert "批次：batch-new" in (
        tmp_path / "openspec" / "issues" / "INDEX.md"
    ).read_text(encoding="utf-8")
