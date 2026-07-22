import json
import os
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

BUGLIST_SCRIPT = str(Path(__file__).parents[2] / "sdflow-issues" / "scripts" / "buglist.py")
TODOLIST_SCRIPT = str(Path(__file__).parents[2] / "sdflow-issues" / "scripts" / "todolist.py")


# 分派型补桩的单一源在 `conftest.py`（`scan_only_run` fixture）——为什么 MUST NOT
# 整体替换 `issues_mod.subprocess.run`（假绿机理），见该模块的 docstring。


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


def test_validate_scan_envelope_accepts_pure_legacy_ascii_alias():
    item = _valid_bug_item(id="A007")

    items, problems = validate_scan_envelope(
        json.dumps({"bugs": [item], "problems": []}), "bug"
    )

    assert items == [item]
    assert problems == []


@pytest.mark.parametrize("bad_id", ["A٠٠٧", "A00٧", "AA7", "a7", "A"])
def test_validate_scan_envelope_rejects_non_ascii_or_malformed_legacy_id(bad_id):
    with pytest.raises(ValueError, match="ID"):
        validate_scan_envelope(
            json.dumps({"bugs": [_valid_bug_item(id=bad_id)], "problems": []}), "bug"
        )


@pytest.mark.parametrize("bad_id", [None, 7, [], {}])
def test_validate_scan_envelope_rejects_non_string_id_with_controlled_diagnostic(bad_id):
    with pytest.raises(ValueError) as exc_info:
        validate_scan_envelope(
            json.dumps({"bugs": [_valid_bug_item(id=bad_id)], "problems": []}), "bug"
        )

    diagnostic = str(exc_info.value)
    assert diagnostic.startswith("ERROR: ")
    assert "scan item[0].id" in diagnostic
    assert "; cause:" in diagnostic
    assert "; fix:" in diagnostic
    assert "Traceback" not in diagnostic


@pytest.mark.parametrize(
    ("field", "value"),
    [("module", "   "), ("summary", "\t\n"), ("change", ""), ("batch", "")],
)
@pytest.mark.parametrize("pool", ["bug", "todo"])
def test_validate_scan_envelope_rejects_noncanonical_empty_values(pool, field, value):
    item = _valid_bug_item()
    if pool == "todo":
        item.pop("priority")
        item["type"] = "代码质量"
        item["id"] = "T1"
        item["file"] = "openspec/issues/todolist/2026-01-todolist.md"
    item[field] = value
    key = "bugs" if pool == "bug" else "items"

    with pytest.raises(ValueError, match=field):
        validate_scan_envelope(json.dumps({key: [item], "problems": []}), pool)


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
def test_reindex_consumer_drift_preserves_existing_index_and_batches(
    tmp_path, monkeypatch, scan_only_run, payload
):
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

    monkeypatch.setattr(issues_mod.subprocess, "run", scan_only_run(lambda _command: Proc()))

    with pytest.raises(ValueError):
        _reindex_core(str(tmp_path))

    assert index.read_bytes() == b"old-index\n"
    assert batches.read_bytes() == b"old-batches\n"


@pytest.mark.parametrize("bad_id", [None, 7, [], {}])
def test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes(
    tmp_path, monkeypatch, capsys, scan_only_run, bad_id
):
    issues_dir = tmp_path / "openspec" / "issues"
    issues_dir.mkdir(parents=True)
    index = issues_dir / "INDEX.md"
    batches = issues_dir / "batches.md"
    index.write_bytes(b"old-index\n")
    batches.write_bytes(b"old-batches\n")

    class Proc:
        returncode = 0
        stdout = json.dumps({"bugs": [_valid_bug_item(id=bad_id)], "problems": []})
        stderr = ""

    # 按 argv 分派：只拦 recorder 的 scan，`git rev-parse` 透传 ⇒ root 真解析到
    # tmp_path，reindex 真正作用于临时目录。整体替换会让本用例退化成假绿（见
    # `conftest.make_dispatch_run` 的 docstring）。
    monkeypatch.setattr(issues_mod.subprocess, "run", scan_only_run(lambda _command: Proc()))
    monkeypatch.setattr(
        sys, "argv", ["issues.py", "--root", str(tmp_path), "reindex"]
    )
    cwd_before = set(os.listdir("."))

    with pytest.raises(SystemExit) as exc_info:
        issues_mod.main()

    diagnostic = capsys.readouterr().err
    assert exc_info.value.code == 2
    assert diagnostic.startswith("ERROR: ")
    # MUST 断言具体诊断内容：坏 root 与坏 scan id 都产生 exit 2，仅凭退出码无法区分
    # 「测中了目标」与「在更早的关口就崩了」。
    assert "scan item[0].id" in diagnostic
    assert "仓根" not in diagnostic  # 崩在 root 解析关口 = 没测到目标
    assert "; cause:" in diagnostic
    assert "; fix:" in diagnostic
    assert "Traceback" not in diagnostic
    assert index.read_bytes() == b"old-index\n"
    assert batches.read_bytes() == b"old-batches\n"
    assert set(os.listdir(".")) - cwd_before == set()


@pytest.mark.parametrize(
    ("field", "value"),
    [("module", "   "), ("summary", "\t"), ("change", ""), ("batch", "")],
)
@pytest.mark.parametrize("bad_pool", ["bug", "todo"])
def test_reindex_rejects_schema_value_drift_from_each_pool_before_derived_writes(
    tmp_path, monkeypatch, scan_only_run, bad_pool, field, value
):
    issues_dir = tmp_path / "openspec" / "issues"
    issues_dir.mkdir(parents=True)
    index = issues_dir / "INDEX.md"
    batches = issues_dir / "batches.md"
    index.write_bytes(b"old-index\n")
    batches.write_bytes(b"old-batches\n")
    bug = _valid_bug_item()
    todo = {
        "id": "T1", "module": "docs", "summary": "todo", "type": "\u4ee3\u7801\u8d28\u91cf",
        "status": "OPEN", "time": "11:00", "change": "chg", "batch": "batch-old",
        "file": "openspec/issues/todolist/2026-01-todolist.md",
    }
    (bug if bad_pool == "bug" else todo)[field] = value

    class Proc:
        returncode = 0
        stderr = ""

        def __init__(self, stdout):
            self.stdout = stdout

    def scan(command):
        if "buglist.py" in command[1]:
            return Proc(json.dumps({"bugs": [bug], "problems": []}))
        return Proc(json.dumps({"items": [todo], "problems": []}))

    monkeypatch.setattr(issues_mod.subprocess, "run", scan_only_run(scan))

    with pytest.raises(ValueError, match=field):
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


def test_read_rename_snapshot_reads_and_parses_each_dated_file_once(
    tmp_path, monkeypatch, scan_only_run
):
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

    def no_recorder_scan(_command):
        raise AssertionError("direct rename snapshot must not invoke recorder scan subprocess")

    # 只对 recorder scan 断言"不得被调用"（这就是本用例的断言本体）；其余子进程
    # （如 repo_root 的 git 探测）透传，避免劫持被测函数之外的调用。
    monkeypatch.setattr(issues_mod.subprocess, "run", scan_only_run(no_recorder_scan))
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


def _legacy_bug_bytes(eol=b"\n", bom=b"", batch="batch-old"):
    lines = [
        "# Bugs",
        "",
        "## 状态总览",
        "",
        "| ID | 模块 | 问题摘要 | 优先级 | 状态 | 时间 | 关联Change | 批次 |",
        "|----|------|----------|--------|------|------|------------|------|",
        f"| B1 | core | old | P2 | OPEN | 10:00 | chg | {batch} |",
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


def _overlay_document(pool, item_id, current_item, legacy_body):
    model = {"schema": 1, "pool": pool, "mode": "overlay", "items": {item_id: current_item}}
    return b"---\n" + render_recorder_namespace(model) + b"---\n" + legacy_body


def _write_preflight_state(root, dated_path, raw):
    issues_dir = root / "openspec" / "issues"
    issues_dir.mkdir(parents=True, exist_ok=True)
    batches = issues_dir / "batches.md"
    index = issues_dir / "INDEX.md"
    batches.write_bytes(
        b"# registry\n\n### batch-old \xe2\x80\x94 title\n"
        b"\xe7\x8a\xb6\xe6\x80\x81: PLANNED\n\xe6\x88\x90\xe5\x91\x98: (\xe7\x94\x9f\xe6\x88\x90) B1\n"
        b"\xe4\xbc\x98\xe5\x85\x88\xe7\xba\xa7: P2\n\xe8\xae\xa1\xe5\x88\x92: x\n"
    )
    index.write_bytes(b"old-index\n")
    dated_path.parent.mkdir(parents=True, exist_ok=True)
    dated_path.write_bytes(raw)
    return {
        "registry": batches.read_bytes(),
        "dated": dated_path.read_bytes(),
        "INDEX": index.read_bytes(),
    }


def _rename_cli(root):
    return subprocess.run(
        [
            sys.executable,
            str(Path(issues_mod.__file__)),
            "--root",
            str(root),
            "batch",
            "rename",
            "batch-old",
            "batch-new",
        ],
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("shape", ["canonical-missing-marker", "overlay-missing-marker", "legacy-marker-collision", "legacy-duplicate-candidate"])
def test_batch_rename_preflight_rejects_unsafe_target_before_any_write(tmp_path, shape):
    path = tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md"
    item = _valid_bug_item()
    item.pop("id")
    item.pop("file")
    if shape == "canonical-missing-marker":
        raw = _canonical_document("bug", "B1", item).replace(
            b"<!-- sdflow-issue-block:start id=B1 -->\n## B1: fixture\n<!-- sdflow-issue-block:end id=B1 -->\n",
            b"## B1: fixture\n",
        )
    elif shape == "overlay-missing-marker":
        raw = _overlay_document("bug", "B1", item, _legacy_bug_bytes())
    elif shape == "legacy-marker-collision":
        raw = _legacy_bug_bytes().replace(
            b"**\xe7\x8e\xb0\xe8\xb1\xa1**\xef\xbc\x9akeep | unicode \xe9\x9b\xaa\n",
            b"<!-- sdflow-issue-block:start id=B9 -->\n**\xe7\x8e\xb0\xe8\xb1\xa1**\xef\xbc\x9akeep | unicode \xe9\x9b\xaa\n",
        )
    else:
        raw = _legacy_bug_bytes() + b"\n## B1: duplicate\n\nsecond\n"
    before = _write_preflight_state(tmp_path, path, raw)

    with pytest.raises(ValueError) as exc_info:
        issues_mod.cmd_batch_rename(
            types.SimpleNamespace(root=str(tmp_path), old="batch-old", new="batch-new")
        )

    diagnostic = str(exc_info.value)
    assert "stage=preflight" in diagnostic
    assert "batch rename batch-old batch-new" in diagnostic
    assert (tmp_path / "openspec" / "issues" / "batches.md").read_bytes() == before["registry"]
    assert path.read_bytes() == before["dated"]
    assert (tmp_path / "openspec" / "issues" / "INDEX.md").read_bytes() == before["INDEX"]


def test_rename_legacy_block_range_emits_exact_english_fix_text():
    """dedupe fix1 锁：issues 的 rename-path 格式化器逐字保留英文 fix 文案（与 core 的中文
    sibling 只差 prose、不差扫描）。扫描单一源提取后，两分支文案 MUST byte-exact 不变。"""
    # ambiguous 分支：零个匹配的 legacy heading → candidates=0
    ambiguous_doc = {"path": "p.md", "lines": ["# x", "no heading"]}
    with pytest.raises(ValueError) as exc_ambiguous:
        issues_mod._rename_legacy_block_range(ambiguous_doc, "A1")
    assert str(exc_ambiguous.value) == (
        "ERROR: file=p.md legacy block 无法安全包裹; "
        "cause: id=A1 candidates=0; "
        "fix: repair to exactly one legacy block, then rerun the original batch rename command"
    )
    # collision 分支：唯一 heading 内含预存 marker → line 定位
    collision_doc = {
        "path": "p.md",
        "lines": ["## A1: title", "<!-- sdflow-issue-block:start id=A9 -->"],
    }
    with pytest.raises(ValueError) as exc_collision:
        issues_mod._rename_legacy_block_range(collision_doc, "A1")
    assert str(exc_collision.value) == (
        "ERROR: file=p.md legacy marker collision; "
        "cause: id=A1 line=2; "
        "fix: remove or escape the preexisting marker, then rerun the original batch rename command"
    )
    # 扫描已收敛为唯一命名单一源（两侧格式化器均解析到 core）
    assert issues_mod._scan_legacy_block_range.__module__ == "sdflow_issues_core"
    assert issues_mod._legacy_block_range.__module__ == "sdflow_issues_core"


@pytest.mark.parametrize(
    "marker_bytes",
    [
        (
            b"<!-- sdflow-issue-block:start id=B9 -->\n"
            b"inside\n"
            b"<!-- sdflow-issue-block:end id=B9 -->\n"
        ),
        b"<!-- sdflow-issue-block:start id=B9 -->\n",
    ],
    ids=["complete", "partial"],
)
def test_pure_legacy_marker_collision_cli_names_target_file_line_and_preserves_bytes(
    tmp_path, marker_bytes
):
    path = tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md"
    raw = _legacy_bug_bytes().replace(
        b"**\xe7\x8e\xb0\xe8\xb1\xa1**\xef\xbc\x9akeep | unicode \xe9\x9b\xaa\n",
        marker_bytes
        + b"**\xe7\x8e\xb0\xe8\xb1\xa1**\xef\xbc\x9akeep | unicode \xe9\x9b\xaa\n",
    )
    before = _write_preflight_state(tmp_path, path, raw)

    proc = _rename_cli(tmp_path)

    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert "stage=preflight" in proc.stderr
    assert str(path) in proc.stderr
    assert "id=B1" in proc.stderr
    assert "line=" in proc.stderr
    assert "batch rename batch-old batch-new" in proc.stderr
    assert (tmp_path / "openspec" / "issues" / "batches.md").read_bytes() == before["registry"]
    assert path.read_bytes() == before["dated"]
    assert (tmp_path / "openspec" / "issues" / "INDEX.md").read_bytes() == before["INDEX"]


@pytest.mark.parametrize("retry_shape", ["all-new", "mixed"])
@pytest.mark.parametrize("target_shape", ["canonical", "overlay", "pure-legacy"])
def test_provenance_retry_preflights_new_side_owned_target_relations_before_write(
    tmp_path, retry_shape, target_shape
):
    issues_dir = tmp_path / "openspec" / "issues"
    issues_dir.mkdir(parents=True)
    batches = issues_dir / "batches.md"
    index = issues_dir / "INDEX.md"
    batches.write_text(
        "# registry\n\n### batch-new — title\n重命名自: batch-old\n状态: PLANNED\n"
        "成员: (生成)\n优先级: P2\n计划: x\n",
        encoding="utf-8",
    )
    index.write_bytes(b"old-index\n")
    path = issues_dir / "buglist" / "2026-01-01-buglist.md"
    path.parent.mkdir(parents=True)
    item = _valid_bug_item(batch="batch-new")
    item.pop("id")
    item.pop("file")
    if target_shape == "canonical":
        raw = _canonical_document("bug", "B1", item).replace(
            b"<!-- sdflow-issue-block:start id=B1 -->\n## B1: fixture\n"
            b"<!-- sdflow-issue-block:end id=B1 -->\n",
            b"## B1: fixture\n",
        )
    elif target_shape == "overlay":
        raw = _overlay_document("bug", "B1", item, _legacy_bug_bytes(batch="batch-new"))
    else:
        raw = _legacy_bug_bytes(batch="batch-new").replace(
            b"**\xe7\x8e\xb0\xe8\xb1\xa1**\xef\xbc\x9akeep | unicode \xe9\x9b\xaa\n",
            b"<!-- sdflow-issue-block:start id=B9 -->\n"
            b"**\xe7\x8e\xb0\xe8\xb1\xa1**\xef\xbc\x9akeep | unicode \xe9\x9b\xaa\n",
        )
    path.write_bytes(raw)
    other_path = None
    if retry_shape == "mixed":
        other = _valid_bug_item(batch="batch-old")
        other.pop("id")
        other.pop("file")
        other_path = issues_dir / "buglist" / "2026-01-02-buglist.md"
        other_path.write_bytes(_canonical_document("bug", "B2", other))
    before = {
        "registry": batches.read_bytes(),
        "dated": path.read_bytes(),
        "other": other_path.read_bytes() if other_path else None,
        "INDEX": index.read_bytes(),
    }

    proc = _rename_cli(tmp_path)

    assert proc.returncode == 2
    assert "stage=preflight" in proc.stderr
    assert "batch rename batch-old batch-new" in proc.stderr
    assert batches.read_bytes() == before["registry"]
    assert path.read_bytes() == before["dated"]
    assert (other_path.read_bytes() if other_path else None) == before["other"]
    assert index.read_bytes() == before["INDEX"]


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


@pytest.mark.parametrize("shape", ["canonical", "legacy", "overlay"])
@pytest.mark.parametrize("pool", ["bug", "todo"])
def test_direct_snapshot_matches_recorder_scan_contract_for_all_shapes_and_pools(tmp_path, pool, shape):
    """**同源两 code-path 的接线正确性守**（非 rule-omission 守）——DG-M1·R6 诚实降级。

    三脚本合一后，`issues.py` 的 direct rename snapshot 与薄入口 `scan --json` 跑的是**同一个**
    `sdflow_issues_core` parser（core 是解析 rule 的**单一源**）。∴「一方漏某 lexical/marker/
    overlay/ID rule、另一方不漏」在结构上**不可能**（两方同源、要漏一起漏），本 golden 自比自己
    = tautology，**不再宣称抓 rule 遗漏**（该能力已由「core 是 rule 单一源」的结构事实取代）。

    本测试守的是**接线正确性**：direct 路径的 envelope 组装 / 字段投影（`{**found, "pool": pool}`）
    与 scan 契约的输出**逐字段一致**——即两条 code-path 对同一 core 结果的**装配**没接错。
    若要真 rule-完整性守，须 core-parse vs **外部 golden fixture**（外部锚，非 core 自比 core）。
    """
    if pool == "bug":
        item_id = "B1"
        filename = "2026-01-01-buglist.md"
        item = _valid_bug_item()
        item.pop("id")
        item.pop("file")
        legacy = _legacy_bug_bytes()
        if shape == "overlay":
            legacy = legacy.replace(
                b"## B1: old\n",
                b"<!-- sdflow-issue-block:start id=B1 -->\n## B1: old\n",
            ) + b"<!-- sdflow-issue-block:end id=B1 -->\n"
    else:
        item_id = "T1"
        filename = "2026-01-todolist.md"
        item = {
            "module": "docs", "summary": "improve", "type": "\u4ee3\u7801\u8d28\u91cf",
            "status": "OPEN", "time": "2026-01-01 10:00", "change": "chg", "batch": "batch-old",
        }
        legacy = _legacy_todo_bytes()
    directory = tmp_path / "openspec" / "issues" / ("buglist" if pool == "bug" else "todolist")
    directory.mkdir(parents=True)
    path = directory / filename
    if shape == "canonical":
        path.write_bytes(_canonical_document(pool, item_id, item))
    elif shape == "legacy":
        path.write_bytes(legacy)
    else:
        path.write_bytes(_overlay_document(pool, item_id, item, legacy))

    direct = read_rename_snapshot(str(tmp_path))
    script = BUGLIST_SCRIPT if pool == "bug" else TODOLIST_SCRIPT
    key = "bugs" if pool == "bug" else "items"
    scan = subprocess.run(
        [sys.executable, script, "--root", str(tmp_path), "scan", "--json"],
        capture_output=True, text=True, check=True,
    )
    expected = [{**found, "pool": pool} for found in json.loads(scan.stdout)[key]]

    assert direct["items"] == expected
    assert direct["problems"] == []


def test_overlay_retag_preserves_frozen_legacy_bytes_and_reuses_snapshot(tmp_path, monkeypatch):
    bug_item = _valid_bug_item()
    bug_item.pop("id")
    bug_item.pop("file")
    bug_legacy = _legacy_bug_bytes().replace(
        b"## B1: old\n",
        b"<!-- sdflow-issue-block:start id=B1 -->\n## B1: old\n",
    ) + b"<!-- sdflow-issue-block:end id=B1 -->\n"
    bug_dir = tmp_path / "openspec" / "issues" / "buglist"
    bug_dir.mkdir(parents=True)
    bug_path = bug_dir / "2026-01-01-buglist.md"
    bug_path.write_bytes(_overlay_document("bug", "B1", bug_item, bug_legacy))

    todo_item = {
        "module": "docs", "summary": "improve", "type": "\u4ee3\u7801\u8d28\u91cf", "status": "OPEN",
        "time": "2026-01-01 10:00", "change": "chg", "batch": "batch-old",
    }
    todo_dir = tmp_path / "openspec" / "issues" / "todolist"
    todo_dir.mkdir(parents=True)
    todo_path = todo_dir / "2026-01-todolist.md"
    todo_path.write_bytes(_overlay_document("todo", "T1", todo_item, _legacy_todo_bytes()))
    instrumentation = {"reads": {}, "parses": {}}

    snapshot = read_rename_snapshot(str(tmp_path), instrumentation=instrumentation)
    updated = retag_rename_snapshot(snapshot, "batch-old", "batch-new")

    assert all(after["body"] == before["body"] for before, after in zip(snapshot["documents"], updated["documents"]))
    assert b"| B1 | core | old | P2 | OPEN | 10:00 | chg | batch-old |" in updated["documents"][0]["rendered"]
    assert b"| T1 | docs | improve |" in updated["documents"][1]["rendered"]
    assert b'"batch":"batch-new"' in updated["documents"][0]["rendered"]
    assert b'"batch":"batch-new"' in updated["documents"][1]["rendered"]
    assert all(count == 1 for count in instrumentation["reads"].values())
    assert all(count == 1 for count in instrumentation["parses"].values())

    issues_dir = tmp_path / "openspec" / "issues"
    (issues_dir / "batches.md").write_text(
        "# registry\n\n### batch-new \u2014 title\n\u72b6\u6001: PLANNED\n\u6210\u5458: (\u751f\u6210)\n\u4f18\u5148\u7ea7: P2\n\u8ba1\u5212: x\n", encoding="utf-8"
    )
    monkeypatch.setattr(issues_mod, "read_pool", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("snapshot must be reused")))
    _reindex_core(str(tmp_path), snapshot=updated)
    assert "B1" in (issues_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "T1" in (issues_dir / "INDEX.md").read_text(encoding="utf-8")


def test_overlay_shadowed_malformed_legacy_row_does_not_override_frontmatter_batch_truth(tmp_path):
    item = _valid_bug_item()
    item.pop("id")
    item.pop("file")
    legacy = _legacy_bug_bytes().replace(
        b"| B1 | core | old | P2 | OPEN | 10:00 | chg | batch-old |",
        b"| B1 | frozen | row | P2 | OPEN | 10:00 | chg | batch-new | trailing |",
    ).replace(
        b"## B1: old\n",
        b"<!-- sdflow-issue-block:start id=B1 -->\n## B1: old\n",
    ) + b"<!-- sdflow-issue-block:end id=B1 -->\n"
    path = tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md"
    _write_preflight_state(tmp_path, path, _overlay_document("bug", "B1", item, legacy))

    issues_mod.cmd_batch_rename(
        types.SimpleNamespace(root=str(tmp_path), old="batch-old", new="batch-new")
    )

    rendered = path.read_bytes()
    assert b"| B1 | frozen | row | P2 | OPEN | 10:00 | chg | batch-new | trailing |" in rendered
    assert b'"batch":"batch-new"' in rendered


@pytest.mark.parametrize(
    ("row", "should_fail"),
    [
        ("| B1 | core | old | injected | P2 | OPEN | 10:00 | chg | batch-old |", True),
        ("| B1 | core | old | injected | P2 | OPEN | 10:00 | chg | batch-new |", True),
        ("| B1 | core | old | injected | P2 | OPEN | 10:00 | chg | other |", True),
        ("| B1 | core | old | P2 | OPEN | 10:00 | chg | other | batch-old |", True),
        ("| B1 | core | old | P2 | OPEN | 10:00 | chg | other | trailing |", False),
    ],
)
def test_batch_rename_legacy_arity_classification_is_target_aware(tmp_path, capsys, row, should_fail):
    raw = _legacy_bug_bytes().replace(
        b"| B1 | core | old | P2 | OPEN | 10:00 | chg | batch-old |",
        row.encode("utf-8"),
    )
    path = tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md"
    before = _write_preflight_state(tmp_path, path, raw)
    args = types.SimpleNamespace(root=str(tmp_path), old="batch-old", new="batch-new")

    if should_fail:
        with pytest.raises(ValueError, match="stage=preflight"):
            issues_mod.cmd_batch_rename(args)
        assert (tmp_path / "openspec" / "issues" / "batches.md").read_bytes() == before["registry"]
        assert path.read_bytes() == before["dated"]
        assert (tmp_path / "openspec" / "issues" / "INDEX.md").read_bytes() == before["INDEX"]
    else:
        issues_mod.cmd_batch_rename(args)
        captured = capsys.readouterr()
        assert "arity" in captured.err
        assert path.read_bytes() == before["dated"]


def test_batch_rename_cli_rejects_unprovable_middle_cell_before_registry_write(tmp_path):
    raw = _legacy_bug_bytes().replace(
        b"| B1 | core | old | P2 | OPEN | 10:00 | chg | batch-old |",
        b"| B1 | core | old | injected | P2 | OPEN | 10:00 | chg | other |",
    )
    path = tmp_path / "openspec" / "issues" / "buglist" / "2026-01-01-buglist.md"
    before = _write_preflight_state(tmp_path, path, raw)

    proc = _rename_cli(tmp_path)

    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert "stage=preflight" in proc.stderr
    assert "legacy row" in proc.stderr
    assert "batch rename batch-old batch-new" in proc.stderr
    assert (tmp_path / "openspec" / "issues" / "batches.md").read_bytes() == before["registry"]
    assert path.read_bytes() == before["dated"]
    assert (tmp_path / "openspec" / "issues" / "INDEX.md").read_bytes() == before["INDEX"]


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

    first = _rename_cli(tmp_path)
    second = _rename_cli(tmp_path)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert json.loads(first.stdout)["mode"] == "retry"
    assert json.loads(second.stdout)["mode"] == "retry"
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
