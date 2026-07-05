import subprocess, sys, json
from pathlib import Path
from conftest import commit_all, mkchange
from test_gate_preflight import run_gate

# Load ship_gate module for direct function testing
_scripts_path = str(Path(__file__).parent.parent / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)
import ship_gate as _sg

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
    # 9 是计划外号（plan={1,2}）：仍进 done_ids（窗口机制不变，--no-merges 只滤 merge 本身），
    # 但〔B4 集合归属〕计划外号不计入完成、不上报——done_tasks 只报计划内已完成（此处空）；
    # 仍是 CONTINUE_IMPL（plan_ids={1,2} 未被覆盖）
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == []

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

def test_offplan_task_no_false_complete(repo):
    # 〔B4 集合归属〕plan=task1/task2，只完成 task1 + 一个计划外 task9（遗留/错号/merge 内）
    # → 基数判齐会假齐(len={1,9}=2=N)；集合归属须判 CONTINUE_IMPL（task2 未完不放行）
    approved_change(repo, plan=PLAN2)
    commit_all(repo, "checkpoint(task1-a): A")
    commit_all(repo, "checkpoint(task9-stray): 计划外/遗留")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL"     # 非假齐
    assert js["done_tasks"] == ["1"]            # 只报计划内已完成，不含计划外 9

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

def test_t34_no_checkbox_task_not_globally_passed(repo):
    # 〔T34〕task1 段全勾、task2 段无复选框(仅散文) → 旧全局 checkboxes_all 会因"全文无 - [ ]"
    # 假齐放行(假✅)；分段绑定后 task2 无框不计入 → CONTINUE_IMPL done_tasks==["1"]
    d = approved_change(repo, plan="### Task 1: A\n- [x] done\n### Task 2: B\n还没做（无复选框）\n")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]

def test_t34_checkbox_union_with_checkpoint(repo):
    # 〔T34〕task1 由 checkpoint、task2 由其段复选框全勾 → 两通道并集齐 → RUN_CODE_REVIEW
    approved_change(repo, plan="### Task 1: A\n(无框,靠 checkpoint)\n### Task 2: B\n- [x] done\n")
    commit_all(repo, "checkpoint(task1-a): A")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"

def test_t34_fenced_checkbox_not_counted(repo):
    # 〔T34/codex#4〕task1 段只有 fenced code block 里的伪 [x]、无真实清单行 → 忽略代码块后
    # task1 不算完成（若不忽略则假✅ 齐）；task2 真勾 → 仅 task1 未完 → CONTINUE_IMPL
    plan = ("### Task 1: A\n实现说明\n```\n- [x] 这是代码块里的示例，不是真勾\n```\n"
            "### Task 2: B\n- [x] real\n")
    approved_change(repo, plan=plan)
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["2"]

def test_t34_duplicate_task_number_unknown(repo):
    # 〔T34/codex#3+对抗B-1c〕重号 ### Task 1: 两段(一段全勾一段未勾) → set 折叠会掩盖假✅
    # → 必须判 UNKNOWN
    plan = ("### Task 1: 占位\n- [x] 无关小项\n### Task 1: 真实\n- [ ] 真活未做\n"
            "### Task 2: B\n- [x] d\n")
    approved_change(repo, plan=plan)
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"

def test_t34_unclosed_fence_unknown(repo):
    # 〔impl-review-fix CR-F1〕未闭合 fenced block（笔误漏闭合）→ 全文 fence 状态不平衡、
    # 悬空围栏会吞掉后续真实未勾项 + Task 标题 → 无法可靠解析完成判据 → UNKNOWN(fail-safe)。
    # 旧版分段各自重置 in_fence → 段1[x]被当完成、段2 done2 也当完成 → 假✅ RUN_CODE_REVIEW。
    plan = ("### Task 1: A\n- [x] done1\n```\n- [ ] 真实未完成(被悬空fence吞)\n"
            "### Task 2: B\n- [x] done2\n")
    approved_change(repo, plan=plan)
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"

def test_t34_task_header_in_fence_not_counted(repo):
    # 〔impl-review-fix CR-F2/对抗B场景4〕fenced 代码块内的 `### Task N:` 是模板/格式示例、
    # 非真任务 → 不得计入 plan_ids、不得误判重号 UNKNOWN（标题正则须与复选框同 fence 口径）。
    plan = ("### Task 1: 真实任务\n- [x] done\n模板示例:\n```\n### Task 1: <替换标题>\n"
            "- [ ] <替换>\n```\n### Task 2: B\n- [x] d\n")
    approved_change(repo, plan=plan)
    commit_all(repo, "checkpoint(task1-a): A")
    commit_all(repo, "checkpoint(task2-b): B")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"   # fence 内示例标题不算重号/task

def test_t34_fence_any_checkbox_consistent(repo):
    # 〔impl-review-fix 场景3〕plan_has_any_checkbox 与 checkbox_done_ids 对同一 fence 口径
    # 一致（统一 _parse_plan 后不再矛盾）：task1 段仅代码块内伪框(忽略)、task2 真勾。
    plan = ("### Task 1: A\n```\n- [x] 代码块示例\n```\n真实无框\n### Task 2: B\n- [x] real\n")
    approved_change(repo, plan=plan)
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["2"]

def test_non_git_root_unknown(tmp_path_factory):
    # 独立于 repo fixture：必须是真正孤立的非 git 目录（不能是 repo 的子目录，
    # 子目录会被 git 沿父级发现 .git，反而通过健全性检查）
    non_git = tmp_path_factory.mktemp("non-git-root")
    code, js, _ = run_gate(non_git)
    assert code == 6 and js["verdict"] == "UNKNOWN"


# [Task 4: tg02_hit 声明式匹配] —— 防止描述性提及/代码引用/否定句触发假 RUN_SOP
def test_tg02_descriptive_mention_not_hit(tmp_path):
    """描述性提及 / 代码引用 / 否定句，无 〔TG-02 声明 → tg02_hit False"""
    d = mkchange(tmp_path, "demo")
    # 讨论 `"TG-02" in` 检测；技术栈 TG-01/02/03 均不命中。无 〔TG-02 声明
    d.joinpath("proposal.md").write_text(
        '讨论 `"TG-02" in` 检测；技术栈 TG-01/02/03 均不命中。\n', encoding="utf-8")
    assert _sg.tg02_hit(d) is False


def test_tg02_declaration_hit(tmp_path):
    """声明式 〔TG-02：…〕 格式 → tg02_hit True"""
    d = mkchange(tmp_path, "demo")
    d.joinpath("proposal.md").write_text("〔TG-02：嵌入式固件变更〕\n", encoding="utf-8")
    assert _sg.tg02_hit(d) is True


# [Task 6/A3: tg02_hit 头部区域限定] —— 正文（首个 "## " 之后）文档性提及声明串不触发假 RUN_SOP
def test_tg02_body_mention_not_hit(tmp_path):
    """正文 `## ` 段内含 〔TG-02： 声明串（文档性提及/示例引用）→ tg02_hit False

    活体复现：本 change（gate-anchor-line-scoped）proposal.md 正文
    「正例（`〔TG-02：` 头注）」讨论示例，整体子串匹配会误命中。
    """
    d = mkchange(tmp_path, "demo")
    d.joinpath("proposal.md").write_text(
        "# t\n\n〔TG-25：契约〕\n\n## What\n正例（`〔TG-02：` 头注）示例\n",
        encoding="utf-8")
    assert _sg.tg02_hit(d) is False


def test_tg02_header_declaration_hit(tmp_path):
    """头部（首个 `## ` 之前）声明式 〔TG-02：…〕 → tg02_hit True"""
    d = mkchange(tmp_path, "demo")
    d.joinpath("proposal.md").write_text(
        "# t\n\n〔TG-02：嵌入式固件变更〕\n\n## What\n正文无关内容\n",
        encoding="utf-8")
    assert _sg.tg02_hit(d) is True
