"""issues_v2.py 核心命令测试（issues-v2-single-file-model · Task 1）。

标的：单文件 issue 存储模型的 CLI 单入口——`add` / `set-status` / `scan` / `reindex` /
`next-id` + 支撑函数 `parse_frontmatter` / `read_issue` / `write_issue` / `find_issue`。

本文件自成一体，不 import `sdflow_issues_core`（v2 架构脱钩，见 issues_v2.py 模块 docstring）。
"""

import json
import multiprocessing
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import issues_v2 as v2  # noqa: E402

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "issues_v2.py")


def _git(*args, cwd):
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True,
        encoding="utf-8", errors="replace",
    )


def _init_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    _git("init", "-q", cwd=path)
    _git("config", "user.email", "t@example.com", cwd=path)
    _git("config", "user.name", "t", cwd=path)
    return path


def _run_cli(root, *args):
    return subprocess.run(
        [sys.executable, SCRIPT, "--root", str(root), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ══════════════════════════════════════════════════════════════════════════════
# parse_frontmatter / render_frontmatter / read_issue / write_issue
# ══════════════════════════════════════════════════════════════════════════════

def test_render_frontmatter_quotes_values_and_writes_null_for_none():
    fm = {
        "id": "T1", "pool": "todo", "status": "OPEN", "priority": None,
        "type": "基础设施", "date": "2026-08-03", "source_change": None,
        "module": "sdflow-issues", "summary": "一行摘要", "resolved_by": None,
        "closed_date": None, "closed_reason": None,
    }
    text = v2.render_frontmatter(fm)
    lines = text.splitlines()
    assert lines[0] == 'id: "T1"'
    assert lines[3] == "priority: null"
    assert lines[4] == 'type: "基础设施"'
    assert lines == [
        'id: "T1"', 'pool: "todo"', 'status: "OPEN"', "priority: null",
        'type: "基础设施"', 'date: "2026-08-03"', "source_change: null",
        'module: "sdflow-issues"', 'summary: "一行摘要"', "resolved_by: null",
        "closed_date: null", "closed_reason: null",
    ]


def test_parse_frontmatter_round_trips_quoted_values_and_null():
    fm = {
        "id": "B7", "pool": "bug", "status": "OPEN", "priority": "P1",
        "type": None, "date": "2026-08-03", "source_change": "some-change",
        "module": "m", "summary": "s", "resolved_by": None,
        "closed_date": None, "closed_reason": None,
    }
    rendered = v2.render_frontmatter(fm)
    parsed = v2.parse_frontmatter(rendered)
    assert parsed == fm


def test_parse_frontmatter_unescapes_embedded_double_quote():
    fm = {k: None for k in v2.FRONTMATTER_FIELDS}
    fm.update({"id": "T1", "pool": "todo", "status": "OPEN",
               "date": "2026-08-03", "module": "m",
               "summary": 'true # x: "quoted" bit'})
    rendered = v2.render_frontmatter(fm)
    parsed = v2.parse_frontmatter(rendered)
    assert parsed["summary"] == 'true # x: "quoted" bit'


def test_parse_frontmatter_rejects_illegal_line():
    with pytest.raises(ValueError, match="frontmatter 行非法"):
        v2.parse_frontmatter('id: T1\n')  # missing quotes


def test_write_issue_read_issue_round_trip(tmp_path):
    fm = {k: None for k in v2.FRONTMATTER_FIELDS}
    fm.update({"id": "B1", "pool": "bug", "status": "OPEN",
               "date": "2026-08-03", "module": "m", "summary": "s"})
    path = tmp_path / "B1.md"
    v2.write_issue(str(path), fm, "body text\n", create=True)
    read_fm, read_body = v2.read_issue(str(path))
    assert read_fm == fm
    assert read_body == "body text\n"


def test_write_issue_create_uses_o_creat_excl_and_rejects_existing(tmp_path):
    fm = {k: None for k in v2.FRONTMATTER_FIELDS}
    fm.update({"id": "B1", "pool": "bug", "status": "OPEN",
               "date": "2026-08-03", "module": "m", "summary": "s"})
    path = tmp_path / "B1.md"
    v2.write_issue(str(path), fm, "", create=True)
    with pytest.raises(FileExistsError):
        v2.write_issue(str(path), fm, "", create=True)


def test_write_issue_update_mode_atomically_replaces(tmp_path):
    fm = {k: None for k in v2.FRONTMATTER_FIELDS}
    fm.update({"id": "B1", "pool": "bug", "status": "OPEN",
               "date": "2026-08-03", "module": "m", "summary": "s"})
    path = tmp_path / "B1.md"
    v2.write_issue(str(path), fm, "orig\n", create=True)
    fm["status"] = "FIXED"
    v2.write_issue(str(path), fm, "orig\nupdated\n", create=False)
    read_fm, read_body = v2.read_issue(str(path))
    assert read_fm["status"] == "FIXED"
    assert read_body == "orig\nupdated\n"
    # no leftover .tmp files
    assert sorted(p.name for p in tmp_path.iterdir()) == ["B1.md"]


def _concurrent_writer(args):
    path_str, fm_json = args
    fm = json.loads(fm_json)
    try:
        v2.write_issue(path_str, fm, "", create=True)
        return "created"
    except FileExistsError:
        return "exists"


def test_write_issue_concurrent_o_creat_excl_only_one_winner(tmp_path):
    """并发写同一路径：O_CREAT|O_EXCL 保证只有一个进程真正创建文件，其余收到 FileExistsError。"""
    fm = {k: None for k in v2.FRONTMATTER_FIELDS}
    fm.update({"id": "B9", "pool": "bug", "status": "OPEN",
               "date": "2026-08-03", "module": "m", "summary": "s"})
    path = str(tmp_path / "B9.md")
    fm_json = json.dumps(fm)

    with multiprocessing.Pool(processes=8) as pool:
        results = pool.map(_concurrent_writer, [(path, fm_json)] * 8)

    assert results.count("created") == 1
    assert results.count("exists") == 7
    assert os.path.isfile(path)


# ══════════════════════════════════════════════════════════════════════════════
# find_issue / next_id
# ══════════════════════════════════════════════════════════════════════════════

def test_find_issue_locates_in_open_then_closed(tmp_path):
    open_dir = tmp_path / "openspec" / "issues" / "open"
    closed_dir = tmp_path / "openspec" / "issues" / "closed"
    open_dir.mkdir(parents=True)
    closed_dir.mkdir(parents=True)
    (open_dir / "B1.md").write_text("x", encoding="utf-8")
    (closed_dir / "B2.md").write_text("x", encoding="utf-8")

    path, location = v2.find_issue(str(tmp_path), "B1")
    assert location == "open" and path == str(open_dir / "B1.md")

    path, location = v2.find_issue(str(tmp_path), "B2")
    assert location == "closed" and path == str(closed_dir / "B2.md")

    path, location = v2.find_issue(str(tmp_path), "B999")
    assert path is None and location is None


def test_next_id_scans_across_open_and_closed(tmp_path):
    open_dir = tmp_path / "openspec" / "issues" / "open"
    closed_dir = tmp_path / "openspec" / "issues" / "closed"
    open_dir.mkdir(parents=True)
    closed_dir.mkdir(parents=True)
    (open_dir / "T257.md").write_text("x", encoding="utf-8")
    (closed_dir / "T260.md").write_text("x", encoding="utf-8")

    assert v2.next_id(str(tmp_path), "todo") == "T261"


def test_next_id_starts_at_one_when_no_files(tmp_path):
    assert v2.next_id(str(tmp_path), "bug") == "B1"


# ══════════════════════════════════════════════════════════════════════════════
# cmd_add (CLI integration)
# ══════════════════════════════════════════════════════════════════════════════

def test_cli_add_bug_creates_open_file_with_required_frontmatter(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    proc = _run_cli(
        repo, "add", "--pool", "bug",
        "--json", json.dumps({"module": "m", "summary": "s", "priority": "P1"}),
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["pool"] == "bug" and out["status"] == "OPEN"
    issue_id = out["id"]
    assert issue_id.startswith("B")

    path = repo / "openspec" / "issues" / "open" / f"{issue_id}.md"
    assert path.is_file()
    fm, body = v2.read_issue(str(path))
    assert fm["id"] == issue_id
    assert fm["pool"] == "bug"
    assert fm["status"] == "OPEN"
    assert fm["priority"] == "P1"
    assert fm["type"] is None
    assert fm["module"] == "m"
    assert fm["summary"] == "s"
    assert fm["date"] is not None

    # git add ran (best-effort)
    status = _git("status", "--porcelain", cwd=repo)
    assert f"open/{issue_id}.md" in status.stdout


def test_cli_add_todo_creates_open_file_with_type(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    proc = _run_cli(
        repo, "add", "--pool", "todo",
        "--json", json.dumps({"module": "m", "summary": "s", "type": "基础设施"}),
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    issue_id = out["id"]
    assert issue_id.startswith("T")
    fm, _ = v2.read_issue(str(repo / "openspec" / "issues" / "open" / f"{issue_id}.md"))
    assert fm["pool"] == "todo"
    assert fm["type"] == "基础设施"
    assert fm["priority"] is None


def test_cli_add_detects_source_change_from_unique_change_dir(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    change_dir = repo / "openspec" / "changes" / "my-change"
    change_dir.mkdir(parents=True)

    proc = _run_cli(
        repo, "add", "--pool", "bug",
        "--json", json.dumps({"module": "m", "summary": "s"}),
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["source_change"] == "my-change"


def test_cli_add_explicit_source_change_overrides_detection(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    change_dir = repo / "openspec" / "changes" / "auto-detected"
    change_dir.mkdir(parents=True)

    proc = _run_cli(
        repo, "add", "--pool", "bug",
        "--json", json.dumps({"module": "m", "summary": "s", "source_change": "explicit-change"}),
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["source_change"] == "explicit-change"


def test_cli_add_rejects_missing_summary(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    proc = _run_cli(
        repo, "add", "--pool", "bug", "--json", json.dumps({"module": "m"}),
    )
    assert proc.returncode != 0
    assert "summary" in proc.stderr


def test_cli_add_rejects_mismatched_pool_field(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    proc = _run_cli(
        repo, "add", "--pool", "bug",
        "--json", json.dumps({"module": "m", "summary": "s", "type": "基础设施"}),
    )
    assert proc.returncode != 0
    assert "type" in proc.stderr


def test_cli_add_rejects_unknown_field(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    proc = _run_cli(
        repo, "add", "--pool", "bug",
        "--json", json.dumps({"module": "m", "summary": "s", "bogus": "x"}),
    )
    assert proc.returncode != 0
    assert "bogus" in proc.stderr


def test_cli_add_second_call_gets_incremented_id(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    first = json.loads(_run_cli(
        repo, "add", "--pool", "bug", "--json", json.dumps({"module": "m", "summary": "s1"}),
    ).stdout)
    second = json.loads(_run_cli(
        repo, "add", "--pool", "bug", "--json", json.dumps({"module": "m", "summary": "s2"}),
    ).stdout)
    first_n = int(first["id"][1:])
    second_n = int(second["id"][1:])
    assert second_n == first_n + 1


# ══════════════════════════════════════════════════════════════════════════════
# cmd_set_status (CLI integration)
# ══════════════════════════════════════════════════════════════════════════════

def _add(repo, pool, **fields):
    proc = _run_cli(repo, "add", "--pool", pool, "--json", json.dumps(fields))
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["id"]


def test_cli_set_status_bug_fixed_moves_to_closed_and_fills_fields(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    issue_id = _add(repo, "bug", module="m", summary="s", priority="P1")

    proc = _run_cli(repo, "set-status", "--id", issue_id, "--to", "FIXED",
                     "--evidence", "commit abc123")
    assert proc.returncode == 0, proc.stderr

    open_path = repo / "openspec" / "issues" / "open" / f"{issue_id}.md"
    closed_path = repo / "openspec" / "issues" / "closed" / f"{issue_id}.md"
    assert not open_path.exists()
    assert closed_path.is_file()

    fm, body = v2.read_issue(str(closed_path))
    assert fm["status"] == "FIXED"
    assert fm["closed_date"] is not None
    assert "commit abc123" in body
    assert "状态：OPEN → FIXED" in body

    # git mv actually happened (tracked, in index)
    status = _git("status", "--porcelain", cwd=repo)
    assert f"closed/{issue_id}.md" in status.stdout
    assert f"open/{issue_id}.md" not in status.stdout


def test_cli_set_status_todo_done_requires_evidence(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    issue_id = _add(repo, "todo", module="m", summary="s", type="基础设施")

    proc = _run_cli(repo, "set-status", "--id", issue_id, "--to", "DONE")
    assert proc.returncode != 0
    assert "evidence" in proc.stderr

    proc2 = _run_cli(repo, "set-status", "--id", issue_id, "--to", "DONE",
                      "--evidence", "some-change")
    assert proc2.returncode == 0, proc2.stderr
    fm, _ = v2.read_issue(str(repo / "openspec" / "issues" / "closed" / f"{issue_id}.md"))
    assert fm["status"] == "DONE"


def test_cli_set_status_bug_fixed_requires_evidence(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    issue_id = _add(repo, "bug", module="m", summary="s")
    proc = _run_cli(repo, "set-status", "--id", issue_id, "--to", "FIXED")
    assert proc.returncode != 0
    assert "evidence" in proc.stderr


def test_cli_set_status_wontfix_requires_reason(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    issue_id = _add(repo, "bug", module="m", summary="s")
    proc = _run_cli(repo, "set-status", "--id", issue_id, "--to", "WONTFIX")
    assert proc.returncode != 0
    assert "reason" in proc.stderr

    proc2 = _run_cli(repo, "set-status", "--id", issue_id, "--to", "WONTFIX",
                      "--reason", "ROI 太低")
    assert proc2.returncode == 0, proc2.stderr
    fm, _ = v2.read_issue(str(repo / "openspec" / "issues" / "closed" / f"{issue_id}.md"))
    assert fm["closed_reason"] == "ROI 太低"


def test_cli_set_status_non_terminal_stays_in_open(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    issue_id = _add(repo, "todo", module="m", summary="s")
    proc = _run_cli(repo, "set-status", "--id", issue_id, "--to", "PROPOSED")
    assert proc.returncode == 0, proc.stderr
    open_path = repo / "openspec" / "issues" / "open" / f"{issue_id}.md"
    assert open_path.is_file()
    fm, _ = v2.read_issue(str(open_path))
    assert fm["status"] == "PROPOSED"
    assert fm["closed_date"] is None


def test_cli_set_status_rejects_already_terminal(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    issue_id = _add(repo, "bug", module="m", summary="s")
    proc = _run_cli(repo, "set-status", "--id", issue_id, "--to", "FIXED",
                     "--evidence", "c1")
    assert proc.returncode == 0, proc.stderr

    proc2 = _run_cli(repo, "set-status", "--id", issue_id, "--to", "OPEN")
    assert proc2.returncode != 0
    assert "终态" in proc2.stderr


def test_cli_set_status_non_git_repo_falls_back_to_os_rename(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    open_dir = plain / "openspec" / "issues" / "open"
    open_dir.mkdir(parents=True)
    fm = {k: None for k in v2.FRONTMATTER_FIELDS}
    fm.update({"id": "B1", "pool": "bug", "status": "OPEN",
               "date": "2026-08-03", "module": "m", "summary": "s"})
    v2.write_issue(str(open_dir / "B1.md"), fm, "", create=True)

    proc = _run_cli(plain, "set-status", "--id", "B1", "--to", "FIXED",
                     "--evidence", "commit abc")
    assert proc.returncode == 0, proc.stderr
    assert not (open_dir / "B1.md").exists()
    closed_path = plain / "openspec" / "issues" / "closed" / "B1.md"
    assert closed_path.is_file()


def test_cli_set_status_untracked_file_is_git_added_before_mv(tmp_path):
    """add 的 git add 失败/被跳过时，set-status 到终态前必须自己先 tracked 再 git mv。"""
    repo = _init_repo(tmp_path / "repo")
    open_dir = repo / "openspec" / "issues" / "open"
    open_dir.mkdir(parents=True)
    fm = {k: None for k in v2.FRONTMATTER_FIELDS}
    fm.update({"id": "B5", "pool": "bug", "status": "OPEN",
               "date": "2026-08-03", "module": "m", "summary": "s"})
    v2.write_issue(str(open_dir / "B5.md"), fm, "", create=True)
    # deliberately not git-added — simulate untracked file

    proc = _run_cli(repo, "set-status", "--id", "B5", "--to", "FIXED",
                     "--evidence", "c1")
    assert proc.returncode == 0, proc.stderr
    closed_path = repo / "openspec" / "issues" / "closed" / "B5.md"
    assert closed_path.is_file()
    status = _git("status", "--porcelain", cwd=repo)
    assert "closed/B5.md" in status.stdout


# ══════════════════════════════════════════════════════════════════════════════
# cmd_scan
# ══════════════════════════════════════════════════════════════════════════════

def test_cli_scan_defaults_to_open_only(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    bug_id = _add(repo, "bug", module="m", summary="open-bug")
    fixed_id = _add(repo, "bug", module="m", summary="fixed-bug")
    _run_cli(repo, "set-status", "--id", fixed_id, "--to", "FIXED", "--evidence", "c1")

    proc = _run_cli(repo, "scan", "--json")
    assert proc.returncode == 0, proc.stderr
    items = json.loads(proc.stdout)
    ids = {it["id"] for it in items}
    assert bug_id in ids
    assert fixed_id not in ids


def test_cli_scan_all_includes_closed(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    fixed_id = _add(repo, "bug", module="m", summary="fixed-bug")
    _run_cli(repo, "set-status", "--id", fixed_id, "--to", "FIXED", "--evidence", "c1")

    proc = _run_cli(repo, "scan", "--all", "--json")
    assert proc.returncode == 0, proc.stderr
    items = json.loads(proc.stdout)
    ids = {it["id"] for it in items}
    assert fixed_id in ids


def test_cli_scan_source_change_filters(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    a_id = _add(repo, "bug", module="m", summary="a", source_change="change-a")
    b_id = _add(repo, "bug", module="m", summary="b", source_change="change-b")

    proc = _run_cli(repo, "scan", "--source-change", "change-a", "--json")
    assert proc.returncode == 0, proc.stderr
    items = json.loads(proc.stdout)
    ids = {it["id"] for it in items}
    assert ids == {a_id}
    assert b_id not in ids


def test_cli_scan_status_and_pool_filters(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    bug_id = _add(repo, "bug", module="m", summary="a")
    todo_id = _add(repo, "todo", module="m", summary="b")
    _run_cli(repo, "set-status", "--id", todo_id, "--to", "PROPOSED")

    proc = _run_cli(repo, "scan", "--pool", "todo", "--status", "PROPOSED", "--json")
    assert proc.returncode == 0, proc.stderr
    items = json.loads(proc.stdout)
    ids = {it["id"] for it in items}
    assert ids == {todo_id}
    assert bug_id not in ids


def test_cli_scan_json_outputs_frontmatter_dicts(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    issue_id = _add(repo, "bug", module="m", summary="s", priority="P2")
    proc = _run_cli(repo, "scan", "--json")
    items = json.loads(proc.stdout)
    assert len(items) == 1
    assert items[0]["id"] == issue_id
    assert items[0]["priority"] == "P2"
    assert set(items[0]) == set(v2.FRONTMATTER_FIELDS)


# ══════════════════════════════════════════════════════════════════════════════
# cmd_reindex
# ══════════════════════════════════════════════════════════════════════════════

def test_cli_reindex_generates_index_and_closed_sorted_by_id(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    first_created = _add(repo, "bug", module="m", summary="second")  # gets B1
    second_created = _add(repo, "bug", module="m", summary="first")  # gets B2
    fixed_id = _add(repo, "todo", module="m", summary="closed-one")
    _run_cli(repo, "set-status", "--id", fixed_id, "--to", "DONE", "--evidence", "c1")

    proc = _run_cli(repo, "reindex")
    assert proc.returncode == 0, proc.stderr

    index_text = _read(repo / "openspec" / "issues" / "INDEX.md")
    closed_text = _read(repo / "openspec" / "issues" / "CLOSED.md")

    assert v2.INDEX_BANNER in index_text
    assert "DO NOT EDIT" in index_text
    assert first_created in index_text and second_created in index_text
    # 语义排序：按 (前缀, 数字) 排序，与创建顺序（B1 < B2）恰好一致
    assert index_text.index(first_created) < index_text.index(second_created)
    assert fixed_id not in index_text

    assert fixed_id in closed_text
    assert "resolved_by" not in closed_text  # header uses "Resolved By" not the raw key
    assert "Resolved By" in closed_text


def test_cli_reindex_idempotent_when_rerun(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _add(repo, "bug", module="m", summary="s")
    first = _run_cli(repo, "reindex")
    assert first.returncode == 0
    content1 = _read(repo / "openspec" / "issues" / "INDEX.md")
    second = _run_cli(repo, "reindex")
    assert second.returncode == 0
    content2 = _read(repo / "openspec" / "issues" / "INDEX.md")
    assert content1 == content2


# ══════════════════════════════════════════════════════════════════════════════
# cmd_next_id
# ══════════════════════════════════════════════════════════════════════════════

def test_cli_next_id_cross_directory(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    open_dir = repo / "openspec" / "issues" / "open"
    closed_dir = repo / "openspec" / "issues" / "closed"
    open_dir.mkdir(parents=True)
    closed_dir.mkdir(parents=True)
    (open_dir / "T257.md").write_text("x", encoding="utf-8")
    (closed_dir / "T260.md").write_text("x", encoding="utf-8")

    proc = _run_cli(repo, "next-id", "--pool", "todo")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "T261"


def test_cli_next_id_independent_per_pool(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _add(repo, "bug", module="m", summary="s")
    proc = _run_cli(repo, "next-id", "--pool", "todo")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "T1"


# ══════════════════════════════════════════════════════════════════════════════
# repo_root / detect_change sanity (full edge-case suite deferred to Task 5.3b
# per tasks.md — this only proves the ported function works end-to-end here)
# ══════════════════════════════════════════════════════════════════════════════

def test_repo_root_resolves_git_repo(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    sub = repo / "a" / "b"
    sub.mkdir(parents=True)
    assert v2.repo_root(str(sub)) == os.path.realpath(str(repo))


def test_repo_root_falls_back_outside_git_repo(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert v2.repo_root(str(plain)) == os.path.abspath(str(plain))


def test_detect_change_prefers_unique_change_dir(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    (repo / "openspec" / "changes" / "my-change").mkdir(parents=True)
    assert v2.detect_change(str(repo)) == "my-change"


def test_detect_change_returns_empty_when_ambiguous(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    (repo / "openspec" / "changes" / "change-a").mkdir(parents=True)
    (repo / "openspec" / "changes" / "change-b").mkdir(parents=True)
    assert v2.detect_change(str(repo)) == ""


def test_set_status_rejects_path_traversal_id(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    r = _run_cli(repo, "set-status", "--id", "../../../../etc/hosts", "--to", "FIXED",
                 "--evidence", "x")
    assert r.returncode != 0
    assert "ID 格式非法" in r.stderr
