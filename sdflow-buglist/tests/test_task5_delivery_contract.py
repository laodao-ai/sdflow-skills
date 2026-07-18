"""mlh-p6 Task 5 delivery/cleanup contracts."""

import ast
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).parents[2]
BUG_PATH = ROOT / "sdflow-buglist/scripts/buglist.py"
TODO_PATH = ROOT / "sdflow-todolist/scripts/todolist.py"
ISSUES_PATH = ROOT / "sdflow-issues/scripts/issues.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUG = _load("_task5_bug", BUG_PATH)
TODO = _load("_task5_todo", TODO_PATH)


def test_legacy_table_is_read_promotion_only_and_cell_guard_left_batch_only():
    bug_source = BUG_PATH.read_text(encoding="utf-8")
    todo_source = TODO_PATH.read_text(encoding="utf-8")
    issues_source = ISSUES_PATH.read_text(encoding="utf-8")

    assert "def _reject_cell_unsafe" not in bug_source
    assert "def _reject_cell_unsafe" not in todo_source
    assert "def _reject_cell_unsafe" not in issues_source
    assert "def _reject_batch_line_unsafe" in issues_source

    # Legacy cells are still parsed for dual-read/promotion, but no writer may
    # assign through a parsed row or render a new recorder overview table.
    for source in (bug_source, todo_source):
        assert "parse_table_rows" in source
        assert "_legacy_item_from_row" in source
        assert "_render_item_table" not in source
        assert "rows[item_id][" not in source
        assert "rows[raw_id][" not in source


def test_recorders_stay_self_contained_without_yaml_or_cross_skill_imports():
    for path in (BUG_PATH, TODO_PATH, ISSUES_PATH):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert not any(name in {"yaml", "ruamel", "ruamel.yaml"} for name in imports)
        assert not any(name.startswith("sdflow_") or name.startswith("sdflow-") for name in imports)


def _reference_legacy_rows(path, pool):
    """Project frozen Markdown rows without calling any recorder parser.

    返回 None 表示「本文件没有 legacy 总览表可投影」——即 canonical-only 文件（写入方对
    mode=canonical 的自检就是 `expected_count = 0`，见 buglist.py:550）。本函数只负责
    legacy 表的独立投影，canonical-only 文件没有可投影对象，由调用方跳过；**不是放宽校验**：
    legacy 文件仍必须恰好 1 个总览表、表体仍必须非空。
    """
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    headings = [index for index, line in enumerate(lines) if re.fullmatch(r"##\s+状态总览", line)]
    if not headings:
        return None
    assert len(headings) == 1, f"{path}: expected one legacy overview"
    header = next(
        index
        for index in range(headings[0] + 1, min(len(lines), headings[0] + 7))
        if re.match(r"\|\s*ID\s*\|", lines[index])
    )
    rows = {}
    for line in lines[header + 2:]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == 8, f"{path}:{line}"
        item_id = cells[0]
        assert item_id not in rows, f"{path}: duplicate legacy ID {item_id}"
        rows[item_id] = {
            "module": cells[1],
            "summary": cells[2],
            "priority" if pool == "bug" else "type": cells[3],
            "status": cells[4],
            "time": cells[5] or None,
            "change": None if cells[6] == "-" else cells[6],
            "batch": cells[7] or None,
        }
    assert rows, f"{path}: frozen legacy table must not be empty"
    return rows


DOGFOOD_OVERLAY_DELTAS = {
    "T2": {},
    "T66": {"status": ("PROPOSED", "DONE")},
    "T67": {"status": ("PROPOSED", "DONE")},
    "T85": {"status": ("PROPOSED", "DONE")},
    "T146": {"status": ("PROPOSED", "DONE")},
}


def test_repository_legacy_corpus_matches_independent_projection_item_by_item():
    """Compare every frozen legacy row with the new dual-reader projection."""
    fields_by_pool = {
        "bug": (BUG, ROOT / "openspec/issues/buglist", "priority"),
        "todo": (TODO, ROOT / "openspec/issues/todolist", "type"),
    }
    compared = set()
    shadowed = set()
    for pool, (module, directory, specific) in fields_by_pool.items():
        for path in sorted(directory.glob("*.md")):
            baseline = _reference_legacy_rows(path, pool)
            if baseline is None:        # canonical-only 文件：无 legacy 表可对拍，跳过
                continue
            document = module.read_recorder_document(str(path), pool)
            effective = document["effective_items"]
            owned = set(document["model"]["items"]) if document["model"] else set()
            for item_id, expected in baseline.items():
                item = effective[item_id]
                if item_id in owned:
                    shadowed.add(item_id)
                    deltas = DOGFOOD_OVERLAY_DELTAS[item_id]
                else:
                    deltas = {}
                for field in ("module", "summary", specific, "status", "time", "change", "batch"):
                    baseline_value, effective_value = expected[field], item[field]
                    if field in deltas:
                        assert (baseline_value, effective_value) == deltas[field], f"{path}:{item_id}:{field}"
                    else:
                        assert effective_value == baseline_value, f"{path}:{item_id}:{field}"
                compared.add((pool, path.name, item_id))
    assert compared, "dogfood corpus must contain frozen legacy rows"
    assert shadowed == set(DOGFOOD_OVERLAY_DELTAS)


def test_reindex_to_scan_delegation_contract_runs_before_windows_smoke(tmp_path, monkeypatch):
    (tmp_path / "openspec/issues").mkdir(parents=True)
    with BUG.recorder_lock(tmp_path, "reindex") as owner:
        previous_token = BUG._ACTIVE_RECORDER_TOKEN
        previous_chain = BUG._ACTIVE_RECORDER_CHAIN
        try:
            BUG._ACTIVE_RECORDER_TOKEN = owner.token
            BUG._ACTIVE_RECORDER_CHAIN = owner.chain
            participant_env = BUG.recorder_child_env("scan")
        finally:
            BUG._ACTIVE_RECORDER_TOKEN = previous_token
            BUG._ACTIVE_RECORDER_CHAIN = previous_chain
        with monkeypatch.context() as participant_patch:
            participant_patch.setattr(os, "environ", participant_env)
            participant = BUG.validate_recorder_participant(tmp_path, owner.token, "scan")
        assert participant.participant
        assert participant.chain == ("reindex", "scan")


def test_windows_smoke_workflow_is_persistent_and_branch_agnostic():
    workflow = (ROOT / ".github/workflows/windows-recorder-smoke.yml").read_text(encoding="utf-8")
    for trigger in ("push:", "pull_request:", "workflow_dispatch:"):
        assert trigger in workflow
    assert "branches:" not in workflow
    assert "runs-on: windows-latest" in workflow
    assert "py -m pytest -q sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error" in workflow


def test_delivery_docs_name_operational_boundaries():
    adr = (ROOT / "openspec/adr/0025-recorder-versioned-frontmatter-overlay-and-snapshot-lock.md").read_text(encoding="utf-8")
    context = (ROOT / "openspec/CONTEXT.md").read_text(encoding="utf-8")
    skills = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8")
        for relative in (
            "sdflow-buglist/SKILL.md",
            "sdflow-todolist/SKILL.md",
            "sdflow-issues/SKILL.md",
        )
    )
    contract = adr + context + skills
    for phrase in (
        "Shared Frontmatter Envelope",
        "snapshot lock",
        "重跑原命令",
        "Windows 本地盘",
        "network FS",
        "power-loss",
        "TOCTOU",
        "break-glass",
    ):
        assert phrase in contract
    assert "状态：**Accepted**" in adr


def test_delivery_docs_and_human_scan_output_reject_retired_contracts():
    issues_skill = (ROOT / "sdflow-issues/SKILL.md").read_text(encoding="utf-8")
    for retired in (
        "需要自己把\n  \"报错信息含'已存在'\" 当成幂等成功处理",
        "与 `batch rename` 的 warn-only 不同",
        "并发安全未焊接",
        "调用方 MUST 串行（D6）",
    ):
        assert retired not in issues_skill
    for path in (BUG_PATH, TODO_PATH):
        source = path.read_text(encoding="utf-8")
        assert "✓ 表↔块一致" not in source
        assert "✓ frontmatter/marker/legacy 关系一致" in source


def test_upgraded_install_known_consumer_smoke(tmp_path):
    """Exercise installed paths, not repository script paths."""
    home = tmp_path / "home"
    consumer = tmp_path / "consumer"
    home.mkdir()
    (consumer / "openspec/issues/buglist").mkdir(parents=True)
    (consumer / "openspec/issues/todolist").mkdir(parents=True)
    (consumer / "openspec/issues/batches.md").write_text("# batches\n", encoding="utf-8")
    env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
    setup = subprocess.run(["bash", str(ROOT / "setup.sh")], env=env, text=True, capture_output=True)
    assert setup.returncode == 0, setup.stderr

    legacy_bug = (
        "# bugs\n\n## 状态总览\n\n"
        "| ID | 模块 | 摘要 | 优先级 | 状态 | 时间 | Change | 批次 |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| B1 | core | old | P2 | OPEN | 10:00 | - | |\n\n"
        "---\n\n## B1: old\n\n| 状态 | OPEN |\n"
    )
    (consumer / "openspec/issues/buglist/2026-07-16-buglist.md").write_text(legacy_bug, encoding="utf-8")
    canonical_item = {
        "module": "core", "summary": "new|line\n二", "priority": "P1", "status": "OPEN",
        "time": "11:00", "change": None, "batch": None,
    }
    ns = BUG.render_recorder_namespace(
        {"schema": 1, "pool": "bug", "mode": "canonical", "items": {"B2": canonical_item}}
    )
    (consumer / "openspec/issues/buglist/2026-07-17-buglist.md").write_bytes(
        b"---\n" + ns + b"---\n<!-- sdflow-issue-block:start id=B2 -->\n"
        b"## B2: new\n<!-- sdflow-issue-block:end id=B2 -->\n"
    )
    legacy_todo = (
        "# todos\n\n## 状态总览\n\n"
        "| ID | 模块 | 描述 | 类型 | 状态 | 时间 | 关联Change | 批次 |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| T1 | flow | old | 代码质量 | OPEN | 2026-07-17 10:00 | - | |\n"
    )
    overlay_item = {
        "module": "flow", "summary": "overlay wins", "type": "代码质量", "status": "PROPOSED",
        "time": "2026-07-17 10:00", "change": "prior", "batch": None,
    }
    ns = TODO.render_recorder_namespace(
        {"schema": 1, "pool": "todo", "mode": "overlay", "items": {"T1": overlay_item}}
    )
    (consumer / "openspec/issues/todolist/2026-07-todolist.md").write_bytes(
        b"---\n" + ns + b"---\n" + legacy_todo.encode()
    )

    installed = home / ".codex/skills"

    def run(relative, *args):
        return subprocess.run(
            [sys.executable, str(installed / relative), "--root", str(consumer), *args],
            env=env, text=True, capture_output=True,
        )

    bug = run("sdflow-buglist/scripts/buglist.py", "scan", "--json")
    todo = run("sdflow-todolist/scripts/todolist.py", "scan", "--json")
    assert bug.returncode == todo.returncode == 0, bug.stderr + todo.stderr
    bug_payload, todo_payload = json.loads(bug.stdout), json.loads(todo.stdout)
    assert set(bug_payload) == {"bugs", "problems"}
    assert {item["id"] for item in bug_payload["bugs"]} == {"B1", "B2"}
    assert set(todo_payload) == {"items", "problems"}
    assert todo_payload["items"][0]["summary"] == "overlay wins"

    reindex = run("sdflow-issues/scripts/issues.py", "reindex", "--strict")
    sweep = run("sdflow-issues/scripts/issues.py", "sweep", "--change", "consumer-empty")
    assert reindex.returncode == sweep.returncode == 0, reindex.stderr + sweep.stderr
    index = (consumer / "openspec/issues/INDEX.md").read_text(encoding="utf-8")
    assert index.startswith("<!-- GENERATED by issues.py reindex — DO NOT EDIT -->")
    assert all(item_id in index for item_id in ("B1", "B2", "T1"))
    assert (consumer / "openspec/issues/batches.md").read_text(encoding="utf-8") == "# batches\n"
