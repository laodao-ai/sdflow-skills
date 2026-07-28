"""ship_gate 第四道 plan 校验的测试（harden-implement-review-loop Task5，D3/D3b · H12/M17）。

当且仅当计划文件名为 `tickets.md`（tickets 轨新名）时，MUST 恰含一张「实现验证」收尾 ticket
（`R-ID: all`）且其 `Blocked-by` ⊇ 全部功能 ticket 号；文件名为 `superpowers-plan.md`（旧名）时
跳过本校验（grandfather：同时覆盖 superpowers 轨与改名生效前落盘的在途 tickets 轨 plan）。

覆盖（tasks.md §4.10 逐字）：
1. 含收尾票 → 绿（CONTINUE_IMPL / RUN_CODE_REVIEW 均能正常推进）
2. 删掉收尾票（无任一 Task 段 R-ID: all）→ 必红（UNKNOWN）
3. `Blocked-by` 缺一张功能票号 → 必红（UNKNOWN）
4. grandfather 路径（旧名 `superpowers-plan.md`）→ 不红，即使 plan 本身没有收尾票
5. 额外：收尾票不唯一（>1 张 R-ID: all）同样必红——"恰含一张"的另一半

另加两条单元层测试，直接调 `plan_closing_ticket_check` / `_plan_task_r_ids`，覆盖
`ship_gate.py` 内部实现细节（不必每次都绕 subprocess 全流程）。
"""
import sys
from pathlib import Path

from conftest import commit_all, mkchange, head_sha, write_report
from test_gate_preflight import run_gate

_scripts_path = str(Path(__file__).parent.parent / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)
import ship_gate as _sg  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────
# fixtures：新名 tickets.md 下的三种 plan 形状
# ─────────────────────────────────────────────────────────────────────────

PLAN_WITH_CLOSER = (
    "### Task 1: A\n**Blocked-by:** none\n- [ ] s\n"
    "### Task 2: B\n**Blocked-by:** 1\n- [ ] s\n"
    "### Task 3: 实现验证\n**Blocked-by:** 1,2\n**R-ID:** all\n- [ ] s\n"
)

PLAN_MISSING_CLOSER = (
    "### Task 1: A\n**Blocked-by:** none\n- [ ] s\n"
    "### Task 2: B\n**Blocked-by:** 1\n- [ ] s\n"
)

PLAN_CLOSER_MISSING_DEP = (
    "### Task 1: A\n**Blocked-by:** none\n- [ ] s\n"
    "### Task 2: B\n**Blocked-by:** 1\n- [ ] s\n"
    # 收尾票 Blocked-by 漏了功能票 2
    "### Task 3: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n- [ ] s\n"
)

PLAN_DUPLICATE_CLOSER = (
    "### Task 1: A\n**Blocked-by:** none\n- [ ] s\n"
    "### Task 2: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n- [ ] s\n"
    "### Task 3: 实现验证2\n**Blocked-by:** 1\n**R-ID:** all\n- [ ] s\n"
)


def _seed_with_new_name(repo, plan):
    """落盘新名 tickets.md 的已批准 change（同 test_plan_resolver._approved_change_with_new_name）。"""
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    (d / "tickets.md").write_text(plan, encoding="utf-8")
    commit_all(repo, "seed change artifacts (new plan name)")
    write_report(d, "spec-review-report.md", head_sha(repo),
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (approved)")
    return d


def _seed_with_old_name(repo, plan):
    """落盘旧名 superpowers-plan.md 的已批准 change（grandfather 路径）。"""
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    (d / "superpowers-plan.md").write_text(plan, encoding="utf-8")
    commit_all(repo, "seed change artifacts (old plan name)")
    write_report(d, "spec-review-report.md", head_sha(repo),
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (approved)")
    return d


# ─────────────────────────────────────────────────────────────────────────
# 1. 含收尾票 → 绿
# ─────────────────────────────────────────────────────────────────────────

def test_closing_ticket_present_reaches_continue_impl(repo):
    _seed_with_new_name(repo, PLAN_WITH_CLOSER)
    commit_all(repo, "checkpoint(task1-foo): done A")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]


def test_closing_ticket_present_all_done_advances_to_code_review(repo):
    _seed_with_new_name(repo, PLAN_WITH_CLOSER)
    commit_all(repo, "checkpoint(task1-foo): A")
    commit_all(repo, "checkpoint(task2-bar): B")
    commit_all(repo, "checkpoint(task3-verify): 实现验证")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"


# ─────────────────────────────────────────────────────────────────────────
# 2. 删掉收尾票（无任一 R-ID: all）→ 必红
# ─────────────────────────────────────────────────────────────────────────

def test_missing_closing_ticket_is_unknown(repo):
    _seed_with_new_name(repo, PLAN_MISSING_CLOSER)
    commit_all(repo, "checkpoint(task1-foo): A")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "收尾" in js["reason"]


# ─────────────────────────────────────────────────────────────────────────
# 3. Blocked-by 缺一张功能票号 → 必红
# ─────────────────────────────────────────────────────────────────────────

def test_closing_ticket_missing_functional_dependency_is_unknown(repo):
    _seed_with_new_name(repo, PLAN_CLOSER_MISSING_DEP)
    commit_all(repo, "checkpoint(task1-foo): A")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "Blocked-by" in js["reason"] and "2" in js["reason"]


# ─────────────────────────────────────────────────────────────────────────
# 4. grandfather：旧名 superpowers-plan.md 不校验（即使无收尾票）→ 不红
# ─────────────────────────────────────────────────────────────────────────

def test_grandfather_old_name_without_closing_ticket_not_rejected(repo):
    _seed_with_old_name(repo, PLAN_MISSING_CLOSER)   # 旧名，且明确无收尾票
    commit_all(repo, "checkpoint(task1-foo): done A")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]
    assert "grandfather" in js["reason"].lower()


# ─────────────────────────────────────────────────────────────────────────
# 5. 收尾票不唯一（>1 张 R-ID: all）→ 必红（"恰含一张"的另一半）
# ─────────────────────────────────────────────────────────────────────────

def test_duplicate_closing_tickets_is_unknown(repo):
    _seed_with_new_name(repo, PLAN_DUPLICATE_CLOSER)
    commit_all(repo, "checkpoint(task1-foo): A")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "收尾" in js["reason"] and "唯一" in js["reason"]


# ─────────────────────────────────────────────────────────────────────────
# 单元层：plan_closing_ticket_check / _plan_task_r_ids 直调
# ─────────────────────────────────────────────────────────────────────────

def test_plan_task_r_ids_extracts_per_task_value(tmp_path):
    text = ("### Task 1: A\n**R-ID:** R2\n- [ ] s\n"
            "### Task 2: 实现验证\n**R-ID:** all\n- [ ] s\n")
    assert _sg._plan_task_r_ids(text) == {"1": "R2", "2": "all"}


def test_plan_closing_ticket_check_grandfathers_old_name(tmp_path):
    d = mkchange(tmp_path)
    plan = d / "superpowers-plan.md"
    plan.write_text(PLAN_MISSING_CLOSER, encoding="utf-8")
    ok, note = _sg.plan_closing_ticket_check(plan)
    assert ok is True and "grandfather" in note.lower()


def test_plan_closing_ticket_check_passes_new_name_with_closer(tmp_path):
    d = mkchange(tmp_path)
    plan = d / "tickets.md"
    plan.write_text(PLAN_WITH_CLOSER, encoding="utf-8")
    ok, note = _sg.plan_closing_ticket_check(plan)
    assert ok is True and note == ""


def test_plan_closing_ticket_check_rejects_new_name_missing_closer(tmp_path):
    d = mkchange(tmp_path)
    plan = d / "tickets.md"
    plan.write_text(PLAN_MISSING_CLOSER, encoding="utf-8")
    ok, note = _sg.plan_closing_ticket_check(plan)
    assert ok is False and "收尾" in note
