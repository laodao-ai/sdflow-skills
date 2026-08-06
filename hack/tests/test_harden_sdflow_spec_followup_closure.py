"""逐票锁定 harden-sdflow-spec-followups 的规格与台账闭合语义。"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
CHANGE_NAME = "harden-sdflow-spec-followups"


def _resolve_change_root(changes_root: Path) -> Path:
    """[impl-review-fix] 归档前后都解析到本 change，避免闭合锚在 archive 后必红。"""
    live = changes_root / CHANGE_NAME
    if live.is_dir():
        return live
    archived = sorted((changes_root / "archive").glob(f"*-{CHANGE_NAME}"))
    if len(archived) != 1:
        raise AssertionError(
            f"expected exactly one live-or-archived {CHANGE_NAME}, got {archived}"
        )
    return archived[0]


TODO_SCRIPT = ROOT / "sdflow-issues/scripts/issues_v2.py"
INDEX = ROOT / "openspec/issues/INDEX.md"
SPEC_AUTHORING = ROOT / "openspec/specs/spec-authoring/spec.md"
SPEC_WORKFLOW = ROOT / "openspec/specs/spec-workflow/spec.md"
ARCHIVE = ROOT / "openspec/changes/archive/2026-07-26-add-sdflow-spec"
CHANGE = _resolve_change_root(ROOT / "openspec/changes")
DELTA_AUTHORING = CHANGE / "specs/spec-authoring/spec.md"
TASKS = CHANGE / "tasks.md"
PLAN = CHANGE / "superpowers-plan.md"
SDFLOW_SPEC = ROOT / "sdflow-spec/SKILL.md"
RESIDENT_TEST = ROOT / "hack/tests/test_sdflow_spec_resident_contract.py"
FF0_HOOK = ROOT / "sdflow-init/assets/hooks/ff0-branch-guard.py"
FF0_TEST = ROOT / "sdflow-init/tests/test_ff0_branch_guard.py"


def test_change_root_resolver_survives_archive(tmp_path: Path) -> None:
    changes = tmp_path / "changes"
    live = changes / CHANGE_NAME
    live.mkdir(parents=True)
    assert _resolve_change_root(changes) == live

    archived = changes / "archive" / f"2026-07-27-{CHANGE_NAME}"
    archived.parent.mkdir()
    live.rename(archived)
    assert _resolve_change_root(changes) == archived


def _todos() -> dict[str, dict[str, object]]:
    proc = subprocess.run(
        ["python3", str(TODO_SCRIPT), "--root", str(ROOT), "scan", "--pool", "todo", "--all", "--json"],
        check=True,
        capture_output=True,
        text=True,

        encoding="utf-8",
        errors="replace",)
    payload = json.loads(proc.stdout)
    items = payload if isinstance(payload, list) else payload["items"]
    return {item["id"]: item for item in items}


def _issue_file(item_id: str) -> Path:
    """v2 单文件模型：一个 issue 一个文件，按 pool 子目录定位。"""
    pool = "bug" if item_id.startswith("B") else "todo"
    for sub in ("open", "closed"):
        candidate = ROOT / "openspec/issues" / sub / pool / f"{item_id}.md"
        if candidate.is_file():
            return candidate
    raise AssertionError(f"{item_id} 在 open/ 与 closed/ 均未找到 v2 issue 文件")


def _block(item_id: str) -> str:
    """v2 无 marker block——直接返回 frontmatter 之后的 body（含状态变更历史行）。"""
    text = _issue_file(item_id).read_text(encoding="utf-8")
    parts = text.split("---\n", 2)
    assert len(parts) == 3, f"{item_id} frontmatter 结构异常：{text[:80]!r}"
    return parts[2]


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
    "T233": (
        (
            SDFLOW_SPEC,
            (
                "Codex 当前只观察到用户显式触发已被接受",
                "MUST NOT 把接口缺席写成模型调用已被拒绝",
            ),
        ),
        (
            RESIDENT_TEST,
            ("def test_codex_claim_is_limited_to_observed_user_trigger",),
        ),
    ),
    "T234": (
        (
            SPEC_AUTHORING,
            (
                "### Requirement: SA-15 T132 的阶段一收敛输入契约按入口分治",
                "T132 台账 SHALL 保持 OPEN",
            ),
        ),
    ),
    "T235": (
        (
            FF0_HOOK,
            (
                "不用 payload cwd 执法",
                "command-unverifiable",
            ),
        ),
        (
            FF0_TEST,
            ("def test_non_direct_forms_emit_one_unverifiable_audit",),
        ),
    ),
    "T236": (
        (
            SDFLOW_SPEC,
            (
                "追溯边界是整个 change 目录",
                "只在 `decision-memo.md` 中保留被砍候选与理由也合法",
            ),
        ),
        (
            RESIDENT_TEST,
            ("def test_final_review_accepts_change_directory_traceability",),
        ),
    ),
    "T237": (
        (
            FF0_HOOK,
            (
                "def audit_undecided(explanation: str) -> None",
                '"additionalContext": f"FF-0 command-unverifiable: {explanation}"',
            ),
        ),
        (
            FF0_TEST,
            (
                "def assert_undecided_audit(output)",
                'assert set(hook_result) == {"hookEventName", "additionalContext"}',
            ),
        ),
    ),
    "T242": (
        (SDFLOW_SPEC, ("name: sdflow-spec",)),
        (
            RESIDENT_TEST,
            (
                "def test_entry_is_within_unicode_character_budget",
                "assert len(text) <= 18_000",
            ),
        ),
    ),
}


LEDGER_EVIDENCE = {
    "T233": ("test_sdflow_spec_resident_contract.py", "Codex"),
    "T234": ("test_harden_sdflow_spec_followup_closure.py", "checkpoint(sdflow-spec-grill)"),
    "T235": ("test_ff0_branch_guard.py", "command-unverifiable"),
    "T236": ("test_sdflow_spec_resident_contract.py", "change 目录"),
    "T237": ("test_ff0_branch_guard.py", "additionalContext"),
    "T242": ("test_sdflow_spec_resident_contract.py", "18,000"),
}


@pytest.mark.parametrize("item_id", sorted(IMPLEMENTED_CLOSURES))
def test_current_followup_is_done_only_with_implementation_evidence(item_id: str) -> None:
    for artifact, semantic_anchors in IMPLEMENTED_CLOSURES[item_id]:
        content = artifact.read_text(encoding="utf-8")
        for semantic_anchor in semantic_anchors:
            assert semantic_anchor in content, f"{item_id} 真实产物缺少语义锚：{artifact} :: {semantic_anchor}"

    if item_id == "T234":
        t132 = _todos()["T132"]
        assert t132["status"] in ("OPEN", "WONTDO")
        projection = str(t132["summary"])
        for token in (
            "尚未实现",
            "decision-memo.md",
            "checkpoint(sdflow-spec-grill)",
            "checkpoint(grill)",
            "sdflow:grill-done",
        ):
            assert token in projection
    elif item_id == "T242":
        entry = SDFLOW_SPEC.read_text(encoding="utf-8")
        assert len(entry) <= 18_000, f"T242 入口体量门回退：{len(entry)} Unicode 字符"

    assert _todos()[item_id]["status"] == "DONE"
    block = _block(item_id)
    assert "状态：PROPOSED → DONE" in block
    for ledger_anchor in LEDGER_EVIDENCE[item_id]:
        assert ledger_anchor in block


def test_spec_authoring_requirement_ids_and_resident_identity_are_consistent() -> None:
    authoring = SPEC_AUTHORING.read_text(encoding="utf-8")
    requirement_ids = re.findall(r"^### Requirement: (SA-\d+)\b", authoring, flags=re.MULTILINE)
    assert len(requirement_ids) == len(set(requirement_ids)), "主规格 SA Requirement ID 必须唯一"

    resident_heading = "### Requirement: SA-16 入口常驻契约与按需资料分层"
    assert authoring.count(resident_heading) == 1
    # 本断言原为身份门：「SA-16 是新增 Requirement，不是把 SA-14 改名」⇒ 故要求两者并存。
    # simplify-workflow（archive/2026-08-05-simplify-workflow：proposal「废止 SA-14」、
    # verify-report「REMOVED: SA-14 四入口选择规则」）随双轨合并正式退役了 SA-14 ——
    # 参照系已变，「SA-14 必须在场」不再是当前契约，故退役该断言。
    # 身份门本身由下面的 resident_task_lines 断言承接（常驻契约的任务行只许挂 [SA-16]），
    # 且 SA-14 不得复活：
    assert "SA-14" not in authoring, "SA-14 已随 simplify-workflow 退役，MUST NOT 在主规格复活"

    delta = DELTA_AUTHORING.read_text(encoding="utf-8")
    assert delta.count(resident_heading) == 1

    tasks = TASKS.read_text(encoding="utf-8")
    resident_task_lines = [
        line for line in tasks.splitlines()
        if any(anchor in line for anchor in ("拆出未启用外派协议", "新增入口体量/resident-contract"))
    ]
    assert len(resident_task_lines) == 2
    assert all("[SA-16]" in line and "[SA-14]" not in line for line in resident_task_lines)

    expected_task3_rids = "FF-0, SA-01, SA-06, SA-16, SA-15"
    for task_id in ("3.1", "3.2"):
        task_line = next(
            line for line in tasks.splitlines()
            if re.match(rf"^- \[[ x]\] {re.escape(task_id)} ", line)
        )
        assert f"[{expected_task3_rids}]" in task_line

    plan = PLAN.read_text(encoding="utf-8")
    expected_plan_rids = {
        2: "SA-01, SA-06, SA-16, SA-15",
        3: expected_task3_rids,
        4: expected_task3_rids,
    }
    for task_number, expected_rids in expected_plan_rids.items():
        section = plan.split(f"### Task {task_number}:", 1)[1].split("### Task ", 1)[0]
        rid_line = next(line for line in section.splitlines() if line.startswith("**R-ID:**"))
        assert rid_line == f"**R-ID:** {expected_rids}"


def test_t132_remains_open_with_corrected_future_ab_contract() -> None:
    item = _todos()["T132"]
    assert item["status"] in ("OPEN", "WONTDO")
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
    assert item["status"] in ("PROPOSED", "DONE")
    assert "下游" in str(item["summary"])
    assert "sdflow-init update" in str(item["summary"])


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
    assert todos["T132"]["status"] in ("OPEN", "WONTDO")
    assert todos["T239"]["status"] in ("PROPOSED", "DONE")
