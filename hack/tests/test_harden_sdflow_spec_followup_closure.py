"""逐票锁定 harden-sdflow-spec-followups 的规格与台账闭合语义。"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
TODO_SCRIPT = ROOT / "sdflow-issues/scripts/todolist.py"
TODO_LEDGER = ROOT / "openspec/issues/todolist/2026-07-todolist.md"
INDEX = ROOT / "openspec/issues/INDEX.md"
SPEC_AUTHORING = ROOT / "openspec/specs/spec-authoring/spec.md"
SPEC_WORKFLOW = ROOT / "openspec/specs/spec-workflow/spec.md"
ARCHIVE = ROOT / "openspec/changes/archive/2026-07-26-add-sdflow-spec"


def _todos() -> dict[str, dict[str, object]]:
    proc = subprocess.run(
        ["python3", str(TODO_SCRIPT), "--root", str(ROOT), "scan", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    items = payload if isinstance(payload, list) else payload["items"]
    return {item["id"]: item for item in items}


def _block(item_id: str) -> str:
    ledger = TODO_LEDGER.read_text(encoding="utf-8")
    start = f"<!-- sdflow-issue-block:start id={item_id} -->"
    end = f"<!-- sdflow-issue-block:end id={item_id} -->"
    assert start in ledger and end in ledger, f"{item_id} 缺少可追溯 marker block"
    return ledger.split(start, 1)[1].split(end, 1)[0]


ARCHIVE_CLOSURES = {
    "T232": ("specs/spec-authoring/spec.md", "只覆盖 delta spec"),
    "T238": ("specs/spec-authoring/spec.md", "枚举 `sonnet|opus|haiku|fable`"),
    "T240": ("design.md", "`setup.sh` 无 uninstall 分支"),
    "T241": ("tasks.md", "❌ **回退分支**"),
}


@pytest.mark.parametrize("item_id", sorted(ARCHIVE_CLOSURES))
def test_archived_followup_is_done_only_with_real_artifact(item_id: str) -> None:
    relative, semantic_anchor = ARCHIVE_CLOSURES[item_id]
    assert semantic_anchor in (ARCHIVE / relative).read_text(encoding="utf-8")
    assert _todos()[item_id]["status"] == "DONE"
    block = _block(item_id)
    assert "状态：PROPOSED → DONE" in block
    assert f"archive/2026-07-26-add-sdflow-spec/{relative}" in block


IMPLEMENTED_CLOSURES = {
    "T233": ("test_sdflow_spec_resident_contract.py", "Codex"),
    "T234": ("test_harden_sdflow_spec_followup_closure.py", "checkpoint(sdflow-spec-grill)"),
    "T235": ("test_ff0_branch_guard.py", "command-unverifiable"),
    "T236": ("test_sdflow_spec_resident_contract.py", "change 目录"),
    "T237": ("test_ff0_branch_guard.py", "additionalContext"),
    "T242": ("test_sdflow_spec_resident_contract.py", "18,000"),
}


@pytest.mark.parametrize("item_id", sorted(IMPLEMENTED_CLOSURES))
def test_current_followup_is_done_only_with_implementation_evidence(item_id: str) -> None:
    test_file, semantic_anchor = IMPLEMENTED_CLOSURES[item_id]
    assert _todos()[item_id]["status"] == "DONE"
    block = _block(item_id)
    assert "状态：PROPOSED → DONE" in block
    assert test_file in block
    assert semantic_anchor in block


def test_t132_remains_open_with_corrected_future_ab_contract() -> None:
    item = _todos()["T132"]
    assert item["status"] == "OPEN"
    summary = str(item["summary"])
    for token in (
        "尚未实现",
        "decision-memo.md",
        "checkpoint(sdflow-spec-grill)",
        "checkpoint(grill)",
        "sdflow:grill-done",
    ):
        assert token in summary
    assert "workflow.md:83" not in summary


def test_t239_remains_nonterminal_and_explicitly_unprocessed() -> None:
    item = _todos()["T239"]
    assert item["status"] == "PROPOSED"
    assert "下游" in str(item["summary"])
    assert "sdflow-init update" in str(item["summary"])
    assert "PROPOSED" in INDEX.read_text(encoding="utf-8")


def test_main_specs_carry_ff0_resident_and_ab_contracts() -> None:
    authoring = SPEC_AUTHORING.read_text(encoding="utf-8")
    workflow = SPEC_WORKFLOW.read_text(encoding="utf-8")
    for token in (
        "本 session 没有可供模型调用的 Skill 接口",
        "整个 `openspec/changes/<name>/` 目录",
        "Python Unicode 字符数不超过 18,000",
        "身份、hash 与必填节有效的 `decision-memo.md`",
        "checkpoint(sdflow-spec-grill)",
        "checkpoint(grill)",
        "T132 台账 SHALL 保持 OPEN",
    ):
        assert token in authoring
    for token in (
        "完整匹配有限的单条直接 literal 创建 grammar",
        "command-unverifiable",
        "MUST NOT 设置任何 `permissionDecision`",
        "stacking deny",
    ):
        assert token in workflow


def test_generated_index_matches_each_ticket_terminal_state() -> None:
    index = INDEX.read_text(encoding="utf-8")
    todos = _todos()
    for item_id in (*ARCHIVE_CLOSURES, *IMPLEMENTED_CLOSURES):
        assert todos[item_id]["status"] == "DONE"
        assert f"| {item_id} |" not in index
    assert todos["T132"]["status"] == "OPEN"
    assert todos["T239"]["status"] == "PROPOSED"
    assert "| T132 | todo | OPEN |" in index
    assert "| T239 | todo | PROPOSED |" in index
