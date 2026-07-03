import subprocess, sys, json
from pathlib import Path
from conftest import commit_all, mkchange
from test_gate_preflight import run_gate

PLAN2 = "### Task 1: A\n- [ ] s\n### Task 2: B\n- [ ] s\n"

def approved_change(repo, plan=None, sop=False, tg02=False):
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text(
        "<!-- ship-gate: design-approved -->\n", encoding="utf-8")
    prop = "# p\n〔TG-02：嵌入式〕\n" if tg02 else "# p\n〔TG-01：工具链〕\n"
    (d / "proposal.md").write_text(prop, encoding="utf-8")
    if sop:
        (d / "demo-sop.md").write_text("sop\n", encoding="utf-8")
    if plan is not None:
        (d / "superpowers-plan.md").write_text(plan, encoding="utf-8")
    commit_all(repo, "seed change")
    return d

def test_tg02_hit_sop_missing(repo):
    approved_change(repo, tg02=True)
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_SOP" and js["next"] == "embedded-test-sop"

def test_no_tg02_plan_missing_run_plan(repo):
    approved_change(repo, tg02=False)
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_PLAN" and "SKIP_SOP" in js["reason"]

def test_continue_impl_with_done_set(repo):
    approved_change(repo, plan=PLAN2)
    commit_all(repo, "checkpoint(task1-foo): done A")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]

def test_all_tags_present_advances(repo):
    approved_change(repo, plan=PLAN2)
    commit_all(repo, "checkpoint(task1-foo): A")
    commit_all(repo, "checkpoint(task2-bar): B")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"

def test_window_excludes_legacy_and_merge(repo):
    # 污染①：plan 提交前 main 已有遗留标签（C2 实证态）
    (repo / "seed.txt").write_text("x", encoding="utf-8")
    commit_all(repo, "checkpoint(task1-legacy): 旧 change 遗留")
    commit_all(repo, "checkpoint(task2-legacy): 旧 change 遗留")
    approved_change(repo, plan=PLAN2)
    # 污染②：merge 带入的外部标签（--no-merges 只滤 merge commit 本身，
    # 分支内普通提交仍在窗口——用 merge commit message 携带标签验证滤除）
    subprocess.run(["git", "-C", str(repo), "merge", "--allow-unrelated-histories",
                    "-s", "ours", "-m", "checkpoint(task2-external): merge携带",
                    "HEAD"], capture_output=True, text=True)
    code, js, _ = run_gate(repo)
    # 窗口内无任何 task 标签 → 0/2 完成，辅通道复选框未全勾 → CONTINUE_IMPL
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == []

def test_plan_zero_titles_unknown(repo):
    approved_change(repo, plan="# 空计划，无任务标题\n")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"

def test_checkbox_fallback_advances(repo):
    plan = "### Task 1: A\n- [x] s\n### Task 2: B\n- [x] s\n"
    approved_change(repo, plan=plan)  # 无标签但复选框全勾（回勾型执行器）
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"
