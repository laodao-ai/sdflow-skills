import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).parents[2]
BUG_PATH = REPO_ROOT / "sdflow-buglist" / "scripts" / "buglist.py"
TODO_PATH = REPO_ROOT / "sdflow-todolist" / "scripts" / "todolist.py"
ISSUES_PATH = REPO_ROOT / "sdflow-issues" / "scripts" / "issues.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUG = _load("_frontmatter_buglist", BUG_PATH)
TODO = _load("_frontmatter_todolist", TODO_PATH)
ISSUES = _load("_frontmatter_issues", ISSUES_PATH)


def _run(script, root, *args):
    return subprocess.run(
        [sys.executable, str(script), "--root", str(root), *args],
        text=True,
        capture_output=True,
    )


def _legacy_table(pool, item_id, summary="旧摘要"):
    specific = "P2" if pool == "bug" else "性能优化"
    return (
        "# legacy\n\n## 状态总览\n\n"
        "| ID | 模块 | 摘要 | 属性 | 状态 | 时间 | Change | 批次 |\n"
        "|---|---|---|---|---|---|---|---|\n"
        f"| {item_id} | core | {summary} | {specific} | OPEN | 2026-07-17 10:00 | - | |\n"
    )


def test_canonical_renderer_has_unique_golden_bytes_and_round_trips_unicode():
    model = {
        "schema": 1,
        "pool": "todo",
        "mode": "canonical",
        "items": {
            "A10": {
                "module": "后端",
                "summary": "十|行\n下一行\u2028尾",
                "type": "性能优化",
                "status": "OPEN",
                "time": "2026-07-17 10:00",
                "change": "mlh-p6",
                "batch": "",
            },
            "A2": {
                "module": " 前端 ",
                "summary": "二\u0085行",
                "type": "性能优化",
                "status": "OPEN",
                "time": "2026-07-17 09:00",
                "change": None,
                "batch": None,
            },
        },
    }
    expected = (
        b"sdflow-issues:\n"
        b"  schema: 1\n"
        b"  pool: todo\n"
        b"  mode: canonical\n"
        b"  items:\n"
        b'    A2: {"module":" \xe5\x89\x8d\xe7\xab\xaf ","summary":"\xe4\xba\x8c\\u0085\xe8\xa1\x8c",'
        b'"type":"\xe6\x80\xa7\xe8\x83\xbd\xe4\xbc\x98\xe5\x8c\x96","status":"OPEN","time":"2026-07-17 09:00",'
        b'"change":null,"batch":null}\n'
        b'    A10: {"module":"\xe5\x90\x8e\xe7\xab\xaf","summary":"\xe5\x8d\x81|\xe8\xa1\x8c\\n\xe4\xb8\x8b\xe4\xb8\x80\xe8\xa1\x8c\\u2028\xe5\xb0\xbe",'
        b'"type":"\xe6\x80\xa7\xe8\x83\xbd\xe4\xbc\x98\xe5\x8c\x96","status":"OPEN","time":"2026-07-17 10:00",'
        b'"change":"mlh-p6","batch":null}\n'
    )

    rendered = TODO.render_recorder_namespace(model, b"\n")
    assert rendered == expected

    raw = b"---\n" + rendered + b"---\n# Todo\n"
    parsed = TODO.parse_recorder_document(raw, expected_pool="todo")
    assert parsed["format"] == "canonical"
    assert parsed["model"]["items"]["A10"]["summary"] == "十|行\n下一行\u2028尾"
    assert TODO.render_recorder_namespace(parsed["model"], parsed["eol"]) == expected


def test_scan_dual_reads_canonical_overlay_and_legacy(tmp_path):
    bug_dir = tmp_path / "openspec/issues/buglist"
    bug_dir.mkdir(parents=True)
    bug_item = {
        "module": "core",
        "summary": "新|摘要\n第二行",
        "priority": "P1",
        "status": "OPEN",
        "time": "2026-07-17 11:00",
        "change": None,
        "batch": None,
    }
    namespace = BUG.render_recorder_namespace(
        {"schema": 1, "pool": "bug", "mode": "canonical", "items": {"B2": bug_item}}
    )
    (bug_dir / "2026-07-17-buglist.md").write_bytes(
        b"---\n" + namespace + b"---\n"
        b"<!-- sdflow-issue-block:start id=B2 -->\n## B2: display\n"
        b"<!-- sdflow-issue-block:end id=B2 -->\n"
    )
    legacy = _legacy_table("bug", "B1") + "\n---\n\n## B1: old\n\n| 状态 | OPEN |\n"
    (bug_dir / "2026-07-16-buglist.md").write_text(legacy, encoding="utf-8")

    result = _run(BUG_PATH, tmp_path, "scan", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert {item["id"] for item in payload["bugs"]} == {"B1", "B2"}
    assert next(item for item in payload["bugs"] if item["id"] == "B2")["summary"] == "新|摘要\n第二行"
    assert payload["problems"] == []

    todo_dir = tmp_path / "openspec/issues/todolist"
    todo_dir.mkdir(parents=True)
    table = _legacy_table("todo", "T1", "legacy snapshot")
    todo_item = {
        "module": "flow",
        "summary": "frontmatter wins",
        "type": "代码质量",
        "status": "PROPOSED",
        "time": "2026-07-17 12:00",
        "change": "mlh-p6",
        "batch": None,
    }
    overlay = TODO.render_recorder_namespace(
        {"schema": 1, "pool": "todo", "mode": "overlay", "items": {"T1": todo_item}}
    )
    (todo_dir / "2026-07-todolist.md").write_bytes(b"---\n" + overlay + b"---\n" + table.encode())
    result = _run(TODO_PATH, tmp_path, "scan", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["items"] == [{"id": "T1", **todo_item, "file": "openspec/issues/todolist/2026-07-todolist.md"}]
    assert payload["problems"] == []


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        (b"---\nsdflow-issues:\n  schema: 2\n  pool: bug\n  mode: canonical\n  items: {}\n---\n", "schema"),
        (b"---\nsdflow-issues:\n  schema: 1\n  pool: todo\n  mode: canonical\n  items: {}\n---\n", "pool/path"),
        ("---\nsdflow-issues:\n  schema: 1\n  pool: bug\n  mode: canonical\n  items: {}\n---\n## 状态总览\n\n| ID | x |\n".encode(), "mode-structure"),
        (b"---\n\"sdflow-issues\": {}\n---\n" + _legacy_table("bug", "B1").encode(), "ownership"),
        (b"\xff\xfe---\x00", "encoding"),
    ],
)
def test_bad_namespace_is_fail_closed_without_json_stdout(tmp_path, raw, reason):
    target = tmp_path / "openspec/issues/buglist/2026-07-17-buglist.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(raw)
    before = target.read_bytes()
    result = _run(BUG_PATH, tmp_path, "scan", "--json")
    assert result.returncode != 0
    assert result.stdout == ""
    assert "ERROR:" in result.stderr and "cause:" in result.stderr and "fix:" in result.stderr
    assert reason in result.stderr
    assert str(target) in result.stderr
    assert target.read_bytes() == before


def test_read_recorder_document_opens_dated_file_once(tmp_path, monkeypatch):
    target = tmp_path / "2026-07-17-buglist.md"
    target.write_text(_legacy_table("bug", "B1"), encoding="utf-8")
    original_open = open
    calls = []

    def counted_open(path, *args, **kwargs):
        if str(path) == str(target):
            calls.append(args[0] if args else kwargs.get("mode", "r"))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", counted_open)
    document = BUG.read_recorder_document(str(target), "bug")
    assert document["format"] == "legacy"
    assert calls == ["rb"]


def test_shared_envelope_bom_crlf_and_external_namespace_are_preserved():
    model = {
        "schema": 1,
        "pool": "todo",
        "mode": "canonical",
        "items": {},
    }
    namespace = TODO.render_recorder_namespace(model, b"\r\n")
    raw = (
        b"\xef\xbb\xbf---\r\n"
        b"other-tool: |\r\n  opaque: yes\r\n  --- stays opaque\r\n"
        + namespace
        + b"# producer-neutral separator\r\n\r\n---\r\n# body\r\n"
    )
    parsed = TODO.parse_recorder_document(raw, "todo")
    assert parsed["format"] == "canonical"
    assert parsed["bom"] == b"\xef\xbb\xbf"
    assert parsed["eol"] == b"\r\n"
    assert parsed["raw"] == raw
    assert parsed["body"] == b"# body\r\n"
    assert TODO.render_recorder_namespace(parsed["model"], parsed["eol"]) == namespace


@pytest.mark.parametrize(
    "external",
    [
        b"other:\tbad\n",
        b"- top-level-sequence\n",
        b"%YAML 1.2\n",
        b"plain\n",
    ],
)
def test_shared_envelope_rejects_ambiguous_external_lexical_forms(external):
    raw = b"---\n" + external + b"---\n" + _legacy_table("todo", "T1").encode()
    with pytest.raises(ValueError, match="lexical profile"):
        TODO.parse_recorder_document(raw, "todo")


def test_three_recorders_share_canonical_golden_behavior():
    model = {
        "schema": 1,
        "pool": "bug",
        "mode": "canonical",
        "items": {
            "A2": {
                "module": "core",
                "summary": "same|bytes\nnext",
                "priority": "P2",
                "status": "OPEN",
                "time": "2026-07-17 10:00",
                "change": None,
                "batch": None,
            }
        },
    }
    rendered = [module.render_recorder_namespace(model) for module in (BUG, TODO, ISSUES)]
    assert rendered[0] == rendered[1] == rendered[2]
    raw = b"---\n" + rendered[0] + b"---\n<!-- sdflow-issue-block:start id=A2 -->\n<!-- sdflow-issue-block:end id=A2 -->\n"
    snapshots = [module.parse_recorder_document(raw, "bug") for module in (BUG, TODO, ISSUES)]
    assert [snapshot["model"] for snapshot in snapshots] == [model, model, model]
    assert [snapshot["marker_blocks"] for snapshot in snapshots] == [{"A2": (0, 2)}] * 3


def test_overlay_shadows_legacy_alias_by_semantic_id(tmp_path):
    target = tmp_path / "openspec/issues/todolist/2026-07-todolist.md"
    target.parent.mkdir(parents=True)
    table = _legacy_table("todo", "A007", "legacy alias")
    item = {
        "module": "flow",
        "summary": "canonical owner",
        "type": "代码质量",
        "status": "OPEN",
        "time": "2026-07-17 12:00",
        "change": None,
        "batch": None,
    }
    namespace = TODO.render_recorder_namespace(
        {"schema": 1, "pool": "todo", "mode": "overlay", "items": {"A7": item}}
    )
    target.write_bytes(b"---\n" + namespace + b"---\n" + table.encode())
    result = _run(TODO_PATH, tmp_path, "scan", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["items"] == [{"id": "A7", **item, "file": "openspec/issues/todolist/2026-07-todolist.md"}]
    assert payload["problems"] == []


def test_cross_file_semantic_duplicate_is_fatal(tmp_path):
    directory = tmp_path / "openspec/issues/buglist"
    directory.mkdir(parents=True)
    (directory / "2026-07-16-buglist.md").write_text(_legacy_table("bug", "A007"), encoding="utf-8")
    (directory / "2026-07-17-buglist.md").write_text(_legacy_table("bug", "A7"), encoding="utf-8")
    result = _run(BUG_PATH, tmp_path, "scan", "--json")
    assert result.returncode != 0
    assert result.stdout == ""
    assert "semantic ID 重复" in result.stderr
    assert "A007@" in result.stderr and "A7@" in result.stderr


def test_canonical_prose_table_example_is_not_legacy_region(tmp_path):
    directory = tmp_path / "openspec/issues/buglist"
    directory.mkdir(parents=True)
    item = {
        "module": "core",
        "summary": "example",
        "priority": "P2",
        "status": "OPEN",
        "time": "2026-07-17 10:00",
        "change": None,
        "batch": None,
    }
    namespace = BUG.render_recorder_namespace(
        {"schema": 1, "pool": "bug", "mode": "canonical", "items": {"B1": item}}
    )
    (directory / "2026-07-17-buglist.md").write_bytes(
        b"---\n" + namespace + b"---\n"
        b"<!-- sdflow-issue-block:start id=B1 -->\n| ID | prose |\n|---|---|\n| fake | ok |\n"
        b"<!-- sdflow-issue-block:end id=B1 -->\n"
    )
    result = _run(BUG_PATH, tmp_path, "scan", "--json")
    assert result.returncode == 0, result.stderr


def test_real_scan_calls_document_parser_once_per_file(tmp_path, monkeypatch, capsys):
    directory = tmp_path / "openspec/issues/buglist"
    directory.mkdir(parents=True)
    (directory / "2026-07-17-buglist.md").write_text(_legacy_table("bug", "B1"), encoding="utf-8")
    original = BUG.parse_recorder_document
    calls = []

    def counted(raw, pool):
        calls.append(pool)
        return original(raw, pool)

    monkeypatch.setattr(BUG, "parse_recorder_document", counted)
    BUG.cmd_scan(SimpleNamespace(
        root=str(tmp_path), status=None, change=None, 批次=None, open_ungrouped=False, json=True,
    ))
    assert calls == ["bug"]
    json.loads(capsys.readouterr().out)


def test_indented_namespace_ownership_variant_is_fatal():
    raw = b"---\n  sdflow-issues:\n---\n" + _legacy_table("bug", "B1").encode()
    with pytest.raises(ValueError, match="ownership"):
        BUG.parse_recorder_document(raw, "bug")


def test_duplicate_json_key_and_raw_unicode_line_break_are_fatal():
    duplicate = (
        b"---\nsdflow-issues:\n  schema: 1\n  pool: bug\n  mode: canonical\n  items:\n"
        b'    B1: {"module":"x","module":"y","summary":"z","priority":"P2","status":"OPEN","time":"t","change":null,"batch":null}\n'
        b"---\n"
    )
    with pytest.raises(ValueError, match="JSON key 重复"):
        BUG.parse_recorder_document(duplicate, "bug")
    raw_line_break = duplicate.replace(b'"module":"x","module":"y"', '"module":"x\u2028y"'.encode())
    with pytest.raises(ValueError, match="raw Unicode line break"):
        BUG.parse_recorder_document(raw_line_break, "bug")
