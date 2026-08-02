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

from test_support.windows import bash_executable, bash_path


ROOT = Path(__file__).parents[2]
BUG_PATH = ROOT / "sdflow-issues/scripts/buglist.py"
TODO_PATH = ROOT / "sdflow-issues/scripts/todolist.py"
ISSUES_PATH = ROOT / "sdflow-issues/scripts/issues.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUG = _load("_task5_bug", BUG_PATH)
TODO = _load("_task5_todo", TODO_PATH)
ISSUES = _load("_task5_issues", ISSUES_PATH)


def test_legacy_table_is_read_promotion_only_and_cell_guard_left_batch_only():
    bug_source = BUG_PATH.read_text(encoding="utf-8")
    todo_source = TODO_PATH.read_text(encoding="utf-8")
    issues_source = ISSUES_PATH.read_text(encoding="utf-8")

    assert "def _reject_cell_unsafe" not in bug_source
    assert "def _reject_cell_unsafe" not in todo_source
    assert "def _reject_cell_unsafe" not in issues_source
    assert "def _reject_batch_line_unsafe" in issues_source

    # 单一源化（adr/0027）：dual-read/promotion 的 legacy 表解析现居 core（薄入口不含）。
    core_source = (BUG_PATH.parent / "sdflow_issues_core" / "__init__.py").read_text(encoding="utf-8")
    assert "parse_table_rows" in core_source
    assert "_legacy_item_from_row" in core_source
    assert "_render_item_table" not in core_source
    assert "rows[item_id][" not in core_source
    assert "rows[raw_id][" not in core_source


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
        # 单一源化（adr/0027）：薄入口 MUST 只依赖唯一共享源 sdflow_issues_core；
        # 其它 sdflow_*/sdflow-* 跨 skill import 仍禁止。
        assert not any(
            (name.startswith("sdflow_") or name.startswith("sdflow-")) and name != "sdflow_issues_core"
            for name in imports
        )


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


def _reference_canonical_rows(path, pool):
    """Project frontmatter items without calling any recorder parser.

    与 `_reference_legacy_rows` 对偶：legacy 文件的独立投影对象是 `## 状态总览` 表，
    canonical 文件的独立投影对象是 frontmatter 的 `items:` 块。目标态下新建文件全部是
    canonical（`buglist.py:1320`）⇒ 若 canonical 分支没有独立投影，本测试的覆盖面会随
    时间归零（存量 legacy 文件不再新增）。本函数用最朴素的逐行 + json.loads 重实现，
    刻意不 import recorder 的任何解析函数，保持「独立对拍」的语义。

    返回 None 表示本文件没有 canonical frontmatter（即 legacy-only 文件）。
    """
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    assert end is not None, f"{path}: unterminated frontmatter"
    front = lines[1:end]
    assert front and front[0].strip() == "sdflow-issues:", f"{path}: unexpected frontmatter root"
    assert f"pool: {pool}" in "\n".join(front), f"{path}: frontmatter pool mismatch"
    items_at = next((index for index, line in enumerate(front)
                     if re.fullmatch(r"\s+items:", line)), None)
    if items_at is None:
        return None
    rows = {}
    for line in front[items_at + 1:]:
        match = re.fullmatch(r"\s+([A-Z]\d+): (\{.*\})", line)
        if not match:
            break
        item_id, payload = match.group(1), json.loads(match.group(2))
        assert item_id not in rows, f"{path}: duplicate canonical ID {item_id}"
        rows[item_id] = {
            "module": payload["module"],
            "summary": payload["summary"],
            "priority" if pool == "bug" else "type": payload["priority" if pool == "bug" else "type"],
            "status": payload["status"],
            "time": payload.get("time") or None,
            "change": payload.get("change") or None,
            "batch": payload.get("batch") or None,
        }
    assert rows, f"{path}: canonical items block must not be empty"
    return rows


DOGFOOD_OVERLAY_DELTAS = {
    "T2": {},
    "T8": {"status": ("PROPOSED", "WONTDO")},
    "T19": {"status": ("PROPOSED", "WONTDO")},
    "T27": {"status": ("PROPOSED", "WONTDO")},
    "T28": {"status": ("PROPOSED", "WONTDO")},
    "T30": {"status": ("PROPOSED", "DONE")},
    "T47": {"status": ("PROPOSED", "WONTDO")},
    "T50": {"status": ("PROPOSED", "WONTDO")},
    "T66": {"status": ("PROPOSED", "DONE")},
    "T67": {"status": ("PROPOSED", "DONE")},
    "T70": {"status": ("PROPOSED", "DONE")},
    "T71": {"status": ("PROPOSED", "DONE")},
    "T73": {"status": ("PROPOSED", "DONE")},
    "T77": {"status": ("OPEN", "WONTDO")},
    "T85": {"status": ("PROPOSED", "DONE")},
    "T87": {"status": ("PROPOSED", "DONE")},
    "T88": {"status": ("PROPOSED", "DONE")},
    "T97": {"status": ("PROPOSED", "WONTDO")},
    "T98": {"status": ("PROPOSED", "WONTDO")},
    "T99": {"status": ("PROPOSED", "WONTDO")},
    "T100": {"status": ("PROPOSED", "WONTDO")},
    "T101": {"status": ("PROPOSED", "WONTDO")},
    "T102": {"status": ("PROPOSED", "WONTDO")},
    "T118": {"status": ("PROPOSED", "DONE")},
    "T120": {"status": ("PROPOSED", "WONTDO")},
    "T125": {"status": ("PROPOSED", "WONTDO")},
    "T126": {"status": ("PROPOSED", "DONE")},
    "T127": {"status": ("PROPOSED", "WONTDO")},
    "T132": {
        "status": ("OPEN", "WONTDO"),
        "summary": (
            "grill 相位防静默跳过：spec-review 起手机械核验『grill 已收敛』信号（workflow.md:83 已强制的 grill checkpoint-commit，或 design.md 内补 <!-- sdflow:grill-done --> 锚），无信号→REFUSE_START 提示先跑 grill。grill 本身是人类对话岛不能自动跑，但『跑没跑』可机械断言——同 ship_gate 设计门新鲜度 fail-closed 先例，把判断从模型记性挪到脚本。属 mechanical-layer-hardening 家族。关联 T19（T19 定何时可跳；本条定跳了就机械拦）。信号载体（commit-tag vs design.md 锚）待其自身 design 定。",
            "未来 spec-review 起手 grill 收敛门（尚未实现）：分支 A 需要身份、hash 与必填节有效的 decision-memo.md 加 checkpoint(sdflow-spec-grill)；分支 B 需要既有 checkpoint(grill) 或未来 gate 明确认可的 sdflow:grill-done 锚；无信号才 REFUSE_START。T132 保持 OPEN。",
        ),
    },
    "T133": {"status": ("OPEN", "WONTDO")},
    "T135": {"status": ("OPEN", "DONE")},
    "T136": {"status": ("PROPOSED", "DONE")},
    "T138": {"status": ("PROPOSED", "DONE")},
    "T146": {"status": ("PROPOSED", "DONE")},
}


def test_repository_legacy_corpus_matches_independent_projection_item_by_item():
    """Compare every frozen legacy row with the new dual-reader projection."""
    fields_by_pool = {
        "bug": (BUG, ROOT / "openspec/issues/buglist", "priority"),
        "todo": (TODO, ROOT / "openspec/issues/todolist", "type"),
    }
    compared = set()
    canonical_compared = set()
    shadowed = set()
    for pool, (module, directory, specific) in fields_by_pool.items():
        for path in sorted(directory.glob("*.md")):
            baseline = _reference_legacy_rows(path, pool)
            if baseline is None:
                # canonical-only 文件：没有 legacy 表可对拍，改用 frontmatter 的独立投影对拍。
                # MUST NOT 直接 continue —— 目标态下新文件全是 canonical，continue 会让本测试
                # 的覆盖面随时间归零（这正是它自己诊断出的 dogfood 盲区的镜像）。
                canonical_baseline = _reference_canonical_rows(path, pool)
                assert canonical_baseline is not None, f"{path}: neither legacy table nor canonical items"
                document = module.read_recorder_document(str(path), pool)
                effective = document["effective_items"]
                for item_id, expected in canonical_baseline.items():
                    item = effective[item_id]
                    for field in ("module", "summary", specific, "status", "time", "change", "batch"):
                        assert item[field] == expected[field], f"{path}:{item_id}:{field}"
                    canonical_compared.add((pool, path.name, item_id))
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
    assert canonical_compared, "dogfood corpus must contain canonical items to project"
    assert shadowed == set(DOGFOOD_OVERLAY_DELTAS)


def test_reindex_to_scan_delegation_contract_runs_before_windows_smoke(tmp_path, monkeypatch):
    (tmp_path / "openspec/issues").mkdir(parents=True)
    with BUG.recorder_lock(tmp_path, "reindex") as owner:
        previous_token = BUG._core._ACTIVE_RECORDER_TOKEN
        previous_chain = BUG._core._ACTIVE_RECORDER_CHAIN
        try:
            BUG._core._ACTIVE_RECORDER_TOKEN = owner.token
            BUG._core._ACTIVE_RECORDER_CHAIN = owner.chain
            participant_env = BUG.recorder_child_env("scan")
        finally:
            BUG._core._ACTIVE_RECORDER_TOKEN = previous_token
            BUG._core._ACTIVE_RECORDER_CHAIN = previous_chain
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
    assert "py -m pytest -q sdflow-issues/tests/test_task2_windows_local_fs_smoke.py -W error" in workflow
    init_probe = 'python3 sdflow-init/scripts/init.py init --root "$probe"'
    update_probe = 'PYTHONIOENCODING=gbk python3 sdflow-init/scripts/init.py update --root "$probe"'
    assert init_probe in workflow
    assert update_probe in workflow
    assert workflow.index(init_probe) < workflow.index(update_probe)
    workflow_lines = {line.strip() for line in workflow.splitlines()}
    assert "env -u PYTHONIOENCODING python3 hack/check_encoding_hygiene.py" in workflow_lines
    assert 'env -u PYTHONIOENCODING bash setup.sh > "$RUNNER_TEMP/setup-cp936.log" 2>&1' in workflow_lines
    assert "! grep -Eq 'UnicodeEncodeError|Traceback' \"$RUNNER_TEMP/setup-cp936.log\"" in workflow_lines
    cp936_step = """\
        shell: bash
        run: |
          chcp.com 936
          env -u PYTHONIOENCODING python3 hack/check_encoding_hygiene.py
          env -u PYTHONIOENCODING bash setup.sh > "$RUNNER_TEMP/setup-cp936.log" 2>&1
          ! grep -Eq 'UnicodeEncodeError|Traceback' "$RUNNER_TEMP/setup-cp936.log"""
    assert cp936_step in workflow
    assert (
        "PYTHONIOENCODING=gbk py -m pytest -q "
        "sdflow-issues/tests/test_task5_delivery_contract.py::"
        "test_sweep_cli_executes_all_four_utf8_subprocess_sites -W error"
    ) in workflow


def test_sweep_cli_executes_all_four_utf8_subprocess_sites(tmp_path, monkeypatch):
    """A controlled fixture must take sweep through scan, triage, batch-add and reindex."""
    payload = json.dumps({
        "module": "windows-smoke",
        "summary": "exercise sweep call graph",
        "priority": "P2",
        "phenomenon": "controlled fixture",
        "change": "windows-sweep-smoke",
    })
    seeded = subprocess.run(
        [sys.executable, str(BUG_PATH), "--root", str(tmp_path), "add"],
        input=payload,
        capture_output=True,
        text=True,

        encoding="utf-8",
        errors="replace",)
    assert seeded.returncode == 0, seeded.stderr

    real_run = ISSUES.subprocess.run
    calls = []

    def recording_run(command, *args, **kwargs):
        calls.append((command, kwargs))
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(ISSUES.subprocess, "run", recording_run)
    monkeypatch.setattr(sys, "argv", [
        "issues.py", "--root", str(tmp_path), "sweep", "--change", "windows-sweep-smoke",
    ])
    ISSUES.main()

    sweep_calls = [
        (command, kwargs)
        for command, kwargs in calls
        if len(command) > 1 and str(command[1]) in {str(BUG_PATH), str(TODO_PATH), str(ISSUES_PATH)}
    ]
    stages = [
        "batch-add" if "batch" in command else
        "scan" if "scan" in command else
        "triage" if "triage" in command else
        "reindex"
        for command, _kwargs in sweep_calls
    ]
    assert stages == ["scan", "triage", "scan", "batch-add", "reindex"]
    for _command, kwargs in sweep_calls:
        assert kwargs["text"] is True
        assert kwargs["encoding"] == "utf-8"
        assert kwargs["errors"] == "replace"
    assert (tmp_path / "openspec/issues/INDEX.md").exists()
    assert "windows-sweep-smoke" in (tmp_path / "openspec/issues/batches.md").read_text(encoding="utf-8")


def test_reindex_nested_scan_decodes_child_json_as_utf8(tmp_path, monkeypatch):
    """The reindex -> scan subprocess must not fall back to the Windows locale codec."""
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, '{"bugs": [], "problems": []}', "")

    monkeypatch.setattr(ISSUES.subprocess, "run", fake_run)
    assert ISSUES._scan_pool(str(BUG_PATH), tmp_path, "bug") == []
    assert len(calls) == 1
    _command, kwargs = calls[0]
    assert kwargs["text"] is True
    assert kwargs["encoding"] == "utf-8"
    assert kwargs["errors"] == "replace"


def test_delivery_docs_name_operational_boundaries():
    adr = (ROOT / "openspec/adr/0025-recorder-versioned-frontmatter-overlay-and-snapshot-lock.md").read_text(encoding="utf-8")
    context = (ROOT / "openspec/CONTEXT.md").read_text(encoding="utf-8")
    # 三合一（adr/0027）：两池 + 跨池的交付/操作边界叙述现全居唯一 sdflow-issues/SKILL.md。
    skills = (ROOT / "sdflow-issues/SKILL.md").read_text(encoding="utf-8")
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
    # 单一源化：human scan 输出字串现居 core（薄入口不含）。
    core_source = (BUG_PATH.parent / "sdflow_issues_core" / "__init__.py").read_text(encoding="utf-8")
    assert "✓ 表↔块一致" not in core_source
    assert "✓ frontmatter/marker/legacy 关系一致" in core_source


def test_upgraded_install_known_consumer_smoke(tmp_path):
    """Exercise installed paths, not repository script paths."""
    home = tmp_path / "home"
    consumer = tmp_path / "consumer"
    home.mkdir()
    (consumer / "openspec/issues/buglist").mkdir(parents=True)
    (consumer / "openspec/issues/todolist").mkdir(parents=True)
    (consumer / "openspec/issues/batches.md").write_text("# batches\n", encoding="utf-8")
    env = dict(os.environ, HOME=bash_path(home), SDFLOW_HOME=bash_path(home / ".sdflow"))
    setup = subprocess.run([bash_executable(), bash_path(ROOT / "setup.sh")], env=env, text=True, capture_output=True, encoding="utf-8", errors="replace")
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

            encoding="utf-8",
            errors="replace",)

    bug = run("sdflow-issues/scripts/buglist.py", "scan", "--json")
    todo = run("sdflow-issues/scripts/todolist.py", "scan", "--json")
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
