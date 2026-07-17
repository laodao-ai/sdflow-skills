"""mlh-p6 Task 5 delivery/cleanup contracts."""

import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


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


def test_repository_legacy_corpus_matches_dual_reader_item_by_item():
    """Compare every legacy row with the effective dual-reader projection.

    This intentionally derives the corpus at runtime; it never freezes a
    repository-wide item count that would become stale as the issue pool grows.
    Overlay items are compared to their frozen row only when not shadowed.
    """
    fields_by_pool = {
        "bug": (BUG, ROOT / "openspec/issues/buglist", "priority"),
        "todo": (TODO, ROOT / "openspec/issues/todolist", "type"),
    }
    compared = []
    for pool, (module, directory, specific) in fields_by_pool.items():
        for path in sorted(directory.glob("*.md")):
            document = module.read_recorder_document(str(path), pool)
            effective = document["effective_items"]
            owned = set(document["model"]["items"]) if document["model"] else set()
            for raw_id, row in document["rows"].items():
                canonical = module._canonical_from_key(module._legacy_semantic_id_key(raw_id))
                if canonical in owned:
                    continue
                item = effective[raw_id]
                expected = module._legacy_item_from_row(raw_id, row, pool)
                for field in ("module", "summary", specific, "status", "time", "change", "batch"):
                    assert item[field] == expected[field], f"{path}:{raw_id}:{field}"
                compared.append((path, raw_id))
    assert compared, "dogfood corpus must contain at least one unpromoted legacy item"


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
