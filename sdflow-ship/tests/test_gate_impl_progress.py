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
    # 污染②：真实双分支 merge——side 分支上做一个不带 task 标签的普通提交，
    # 切回 main 后 --no-ff 合并，merge commit 自身消息携带外部标签
    # （--no-merges 只滤 merge commit 本身；merge commit 消息携带的标签必须被滤除）
    subprocess.run(["git", "-C", str(repo), "checkout", "-b", "side"],
                    check=True, capture_output=True, text=True)
    (repo / "side.txt").write_text("y", encoding="utf-8")
    commit_all(repo, "docs: 旁支提交（无标签）")
    subprocess.run(["git", "-C", str(repo), "checkout", "main"],
                    check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo), "merge", "--no-ff", "side",
                    "-m", "checkpoint(task2-external): merge携带"],
                    check=True, capture_output=True, text=True)
    code, js, _ = run_gate(repo)
    # 窗口内无任何 task 标签（merge commit 被 --no-merges 滤除，side 分支内提交无标签）
    # → 0/2 完成，辅通道复选框未全勾 → CONTINUE_IMPL
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == []

def test_merged_branch_inner_commits_do_enter_window(repo):
    # 已知不覆盖边界（design-diagrams 已知不覆盖清单固化）：--no-merges 只滤 merge
    # commit 本身，分支内的普通提交仍会随 merge 进入窗口——本用例防止未来误以为
    # --no-merges 能滤除整条分支的贡献。
    (repo / "seed.txt").write_text("x", encoding="utf-8")
    commit_all(repo, "seed")
    approved_change(repo, plan=PLAN2)
    subprocess.run(["git", "-C", str(repo), "checkout", "-b", "side"],
                    check=True, capture_output=True, text=True)
    (repo / "side.txt").write_text("y", encoding="utf-8")
    commit_all(repo, "checkpoint(task9-side): x")
    subprocess.run(["git", "-C", str(repo), "checkout", "main"],
                    check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo), "merge", "--no-ff", "side",
                    "-m", "merge side into main"],
                    check=True, capture_output=True, text=True)
    code, js, _ = run_gate(repo)
    # 9 不在 plan（N=2, task1/2）内，不会误判齐 N；仍应是 CONTINUE_IMPL
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["9"]

def test_plan_task1_same_commit_counts(repo):
    # 〔B1 闭区间〕plan 与 checkpoint(task1-) 同 commit（checkpoint add -A 携带未提交 plan）
    # → task1 锚在窗口起点 sha 自身，排他窗口会漏数；闭区间须计入
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text(
        "<!-- ship-gate: design-approved -->\n", encoding="utf-8")
    (d / "proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    commit_all(repo, "seed change")           # approved base，无 plan
    (d / "superpowers-plan.md").write_text(PLAN2, encoding="utf-8")
    commit_all(repo, "checkpoint(task1-foo): plan+task1 同 commit")  # plan 首次提交 == task1 锚
    commit_all(repo, "checkpoint(task2-bar): B")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"   # done={1,2} 齐（闭区间含 sha 自身）

def test_uncommitted_plan_no_checkbox_unknown(repo):
    # plan 写盘但不提交，且内容无任何复选框 → 双通道（标签窗口 / 复选框）皆不可判
    d = approved_change(repo)  # 不带 plan 提交基底
    (d / "superpowers-plan.md").write_text("### Task 1: A\n正文\n", encoding="utf-8")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN" and "双通道" in js["reason"]

def test_tg02_hit_sop_exists_falls_through(repo):
    # tg02 命中且 sop 产物已在 → 不再 RUN_SOP，继续往下判（plan 缺 → RUN_PLAN）
    approved_change(repo, tg02=True, sop=True)
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_PLAN"

def test_plan_zero_titles_unknown(repo):
    approved_change(repo, plan="# 空计划，无任务标题\n")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"

def test_checkbox_fallback_advances(repo):
    plan = "### Task 1: A\n- [x] s\n### Task 2: B\n- [x] s\n"
    approved_change(repo, plan=plan)  # 无标签但复选框全勾（回勾型执行器）
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"

# [impl-review-fix] 裁决项1/2 回归覆盖
def test_revert_commit_not_counted(repo):
    approved_change(repo, plan=PLAN2)
    commit_all(repo, "checkpoint(task1-a): x")
    commit_all(repo, 'Revert "checkpoint(task2-b): y"')
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]

def test_non_git_root_unknown(tmp_path_factory):
    # 独立于 repo fixture：必须是真正孤立的非 git 目录（不能是 repo 的子目录，
    # 子目录会被 git 沿父级发现 .git，反而通过健全性检查）
    non_git = tmp_path_factory.mktemp("non-git-root")
    code, js, _ = run_gate(non_git)
    assert code == 6 and js["verdict"] == "UNKNOWN"
