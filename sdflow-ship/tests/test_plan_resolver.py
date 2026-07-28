"""计划文件名共享 resolver 的测试(harden-implement-review-loop Task 3, D5/adr-0033)。

覆盖两层:
1. 单元层——`ship_gate.resolve_plan_path` 本身:新名优先探测/旧名向后兼容/双存在
   fail-closed(`PlanNameConflict`)/都不存在返回 None。
2. gate 端到端层(经 `decide()` 全流程)——证明:
   a. 仅新名 `tickets.md` 存在时,gate 完整判据链路(RUN_PLAN→CONTINUE_IMPL→
      RUN_CODE_REVIEW)与旧名行为等价(向前兼容,新管线不需要借旧名外衣)。
   b. 两个文件名同时存在 ⇒ UNKNOWN(不猜哪个有效,提示人工删除其一)。
   c. 〔5.10 · 🔴 在途 plan MUST NOT 被重命名 · fix1〕改名前有 task1 checkpoint、改名后跑
      gate 的 fixture:断言该场景被 **显式拒绝**(UNKNOWN),而非静默漏数放行。判据 =
      `plan_was_renamed`——比较不带 `--follow` 与带 `--follow` 的
      `git log --diff-filter=A` 首行 sha:从未改名的路径两者相同;改过名则 `--follow`
      追溯到改名前的原始创建提交,两者不同 ⇒ fail-closed 拒绝,而非把改名前的完成信号
      静默排除在窗口外。
"""
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import commit_all, mkchange, write_report
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2

_scripts_path = str(Path(__file__).parent.parent / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)
import ship_gate as _sg  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────
# 单元层：resolve_plan_path
# ─────────────────────────────────────────────────────────────────────────

def test_resolve_plan_path_both_absent_returns_none(tmp_path):
    d = mkchange(tmp_path)
    assert _sg.resolve_plan_path(d) is None


def test_resolve_plan_path_new_name_only(tmp_path):
    d = mkchange(tmp_path)
    (d / "tickets.md").write_text("### Task 1: A\n- [ ] s\n", encoding="utf-8")
    assert _sg.resolve_plan_path(d) == d / "tickets.md"


def test_resolve_plan_path_old_name_only_backward_compat(tmp_path):
    d = mkchange(tmp_path)
    (d / "superpowers-plan.md").write_text("### Task 1: A\n- [ ] s\n", encoding="utf-8")
    assert _sg.resolve_plan_path(d) == d / "superpowers-plan.md"


def test_resolve_plan_path_both_present_raises_conflict(tmp_path):
    d = mkchange(tmp_path)
    (d / "tickets.md").write_text("### Task 1: A\n- [ ] s\n", encoding="utf-8")
    (d / "superpowers-plan.md").write_text("### Task 1: A\n- [ ] s\n", encoding="utf-8")
    with pytest.raises(_sg.PlanNameConflict):
        _sg.resolve_plan_path(d)


def test_resolve_plan_path_ignores_directories_named_like_plan(tmp_path):
    # 目录同名不算命中——resolver 只认普通文件（is_file），防目录误判为计划文件。
    d = mkchange(tmp_path)
    (d / "tickets.md").mkdir()
    assert _sg.resolve_plan_path(d) is None


# ─────────────────────────────────────────────────────────────────────────
# gate 端到端层：仅新名存在 ⇒ 全流程与旧名等价
# ─────────────────────────────────────────────────────────────────────────

def _approved_change_with_new_name(repo, plan):
    """同 test_gate_impl_progress.approved_change，但落盘用新名 tickets.md。"""
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    (d / "tickets.md").write_text(plan, encoding="utf-8")
    commit_all(repo, "seed change artifacts (new plan name)")
    from conftest import head_sha
    write_report(d, "spec-review-report.md", head_sha(repo),
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (approved)")
    return d


def test_new_plan_name_reaches_continue_impl(repo):
    _approved_change_with_new_name(repo, PLAN2)
    commit_all(repo, "checkpoint(task1-foo): done A")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]


def test_new_plan_name_all_tasks_done_advances_to_code_review(repo):
    _approved_change_with_new_name(repo, PLAN2)
    commit_all(repo, "checkpoint(task1-foo): A")
    commit_all(repo, "checkpoint(task2-bar): B")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"


def test_neither_plan_name_present_run_plan_mentions_both_names(repo):
    approved_change(repo)  # 不带 plan
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_PLAN"
    assert "tickets.md" in js["reason"] and "superpowers-plan.md" in js["reason"]


# ─────────────────────────────────────────────────────────────────────────
# gate 端到端层：双存在 fail-closed UNKNOWN
# ─────────────────────────────────────────────────────────────────────────

def test_both_plan_names_present_gate_fails_closed_unknown(repo):
    d = approved_change(repo, plan=PLAN2)   # 落盘旧名 superpowers-plan.md
    (d / "tickets.md").write_text(PLAN2, encoding="utf-8")  # 同时落盘新名
    commit_all(repo, "两个计划文件名同时存在（人为冲突态）")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "tickets.md" in js["reason"] and "superpowers-plan.md" in js["reason"]
    assert "删除其一" in js["reason"]


# ─────────────────────────────────────────────────────────────────────────
# 5.10 · 在途 plan 改名 fail-closed 拒绝（fix1：由静默漏数改为显式拒绝）
# ─────────────────────────────────────────────────────────────────────────

def test_inflight_plan_rename_rejected_as_unknown(repo):
    """🔴 违反「MUST NOT 重命名在途 plan」——不是 resolver 要「跟随改名」的缺陷，也不该
    静默漏数放行（旧行为：改名前的 task1 checkpoint 落到窗口外、gate 却仍 CONTINUE_IMPL）。

    正解 = 把「该路径历史上发生过重命名」机械检测出来，fail-closed 判 UNKNOWN，而非让
    改名把 MUST NOT 变得无害（那等于注销这条规范性约束——见 design Migration Plan）。
    """
    d = approved_change(repo, plan=PLAN2)   # 旧名落盘，Task1/Task2
    commit_all(repo, "checkpoint(task1-a): 改名前完成 task1")
    # 违反纪律：在途 plan 被重命名（旧名 → 新名）
    old_rel = str((d / "superpowers-plan.md").relative_to(repo))
    new_rel = str((d / "tickets.md").relative_to(repo))
    subprocess.run(["git", "-C", str(repo), "mv", old_rel, new_rel],
                    check=True, capture_output=True, text=True)
    commit_all(repo, "checkpoint(task2-b)之前的改名提交：违规重命名在途 plan")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "重命名" in js["reason"]


def test_never_renamed_plan_not_flagged(repo):
    """反例（防误报）：多次提交但从未 `git mv` 过的 plan——不应被判为改名。"""
    d = approved_change(repo, plan=PLAN2)
    commit_all(repo, "checkpoint(task1-a): 正常完成 task1（无改名）")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL"
    assert "1" in js["done_tasks"]
