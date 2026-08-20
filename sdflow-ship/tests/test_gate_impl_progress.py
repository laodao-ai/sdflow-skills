import subprocess, sys
from pathlib import Path
from conftest import commit_all, mkchange, head_sha, write_report
from test_gate_preflight import run_gate

# Load ship_gate module for direct function testing.
# 🔴 `_sg` 是共享 re-export 点：test_gate_freshness.py / test_gate_git_layer.py /
# test_gate_reviewed_sha.py 均经 `from test_gate_impl_progress import ... _sg` 取用，
# 本文件内虽已无 `_sg.` 直接调用（tg02_hit 单测已删），MUST NOT 移除本导入
# （rename-string-consumers-span-file-types 同类教训：改共享导入点先 grep 全部消费方）。
_scripts_path = str(Path(__file__).parent.parent / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)
import ship_gate as _sg

PLAN2 = "### Task 1: A\n- [ ] s\n### Task 2: B\n- [ ] s\n"

# [harden-implement-review-loop Task5 · H12/M17] gate 第四道校验对 tickets.md 无条件生效
# ——同 PLAN2 形状（2 张 task），但 Task 2 兼作「实现验证」收尾 ticket
# （Blocked-by: 1 + R-ID: all），使其在第四道校验下仍合法。
PLAN2_TICKETS = (
    "### Task 1: A\n**Blocked-by:** none\n- [ ] s\n"
    "### Task 2: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n- [ ] 聚合测试套件全部通过\n"
)

def approved_change(repo, plan=None, revise=None, anchor="head"):
    # [mlh-p5 Task5 D6] live fixture 迁 frontmatter（原 inline `<!-- ship-gate: design-approved -->`）。
    # [harden-gate-git-layer Task1 · tasks 4.1/4.1b] 迁**两段提交模型**：报告 frontmatter 现须带
    # `reviewed_sha`（被批准的盘面），而旧单次 commit_all 让报告与其审查对象同属根提交 ⇒ 结构上
    # 没有先于报告的盘面可填。分段：
    #   ① 四件套（+ 可选 plan）落盘提交 → 这就是「被批准的盘面」
    #   ② 可选第三段〔4.1b〕revise=callable(d)：拍板前二次修订，单独提交（ADR-7(b) 场景）
    #   ③ 读出 HEAD → 写携带该 sha 的 spec-review-report → 单独提交
    # anchor: "head"（默认，锚指被批准盘面）｜"pre-revision"（锚指修订**之前**的提交，用于
    #   验 ADR-7(b) 自锁：拍板刚完成即失鲜）｜None（不写 reviewed_sha，缺锚负例）｜显式 sha 串。
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    if plan is not None:
        # 🔴 共享 fixture：`approved_change` 被 7 个测试文件消费（test_gate_git_layer.py /
        # test_gate_freshness.py / test_gate_namespace.py / test_gate_impl_progress.py（本文件）/
        # test_gate_tail.py / test_gate_reviewed_sha.py / test_plan_resolver.py）。
        # [remove-superpowers-pipeline Task2] 单名 resolver 下写入名改 `tickets.md`（原写
        # `superpowers-plan.md`）——resolve_plan_path 只认单名，plan=PLAN2（无收尾 ticket）的
        # 调用点已逐一核验并按需换成 PLAN2_TICKETS（收尾票在单名下无条件校验，改动这个写入名
        # 前先 grep 全部消费点，rename-string-consumers-span-file-types 教训）。
        (d / "tickets.md").write_text(plan, encoding="utf-8")
    commit_all(repo, "seed change artifacts")      # ① 被批准的盘面
    pre_revision = head_sha(repo)
    if revise is not None:                          # ② 拍板前二次修订（单独落盘）
        revise(d)
        commit_all(repo, "pre-approval revision")
    sha = {"head": head_sha(repo), "pre-revision": pre_revision}.get(anchor, anchor)
    write_report(d, "spec-review-report.md", sha,
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (approved)")   # ③ 报告单独提交
    return d

def test_continue_impl_with_done_set(repo):
    approved_change(repo, plan=PLAN2_TICKETS)
    commit_all(repo, "checkpoint(task1-foo): done A")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]

def test_all_tags_present_advances(repo):
    approved_change(repo, plan=PLAN2_TICKETS)
    commit_all(repo, "checkpoint(task1-foo): A")
    commit_all(repo, "checkpoint(task2-bar): B")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"

def test_window_excludes_legacy_and_merge(repo):
    # 污染①：plan 提交前 main 已有遗留标签（C2 实证态）
    (repo / "seed.txt").write_text("x", encoding="utf-8")
    commit_all(repo, "checkpoint(task1-legacy): 旧 change 遗留")
    commit_all(repo, "checkpoint(task2-legacy): 旧 change 遗留")
    approved_change(repo, plan=PLAN2_TICKETS)
    # 污染②：真实双分支 merge——side 分支上做一个不带 task 标签的普通提交，
    # 切回 main 后 --no-ff 合并，merge commit 自身消息携带外部标签
    # （--no-merges 只滤 merge commit 本身；merge commit 消息携带的标签必须被滤除）
    subprocess.run(["git", "-C", str(repo), "checkout", "-b", "side"],
                    check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (repo / "side.txt").write_text("y", encoding="utf-8")
    commit_all(repo, "docs: 旁支提交（无标签）")
    subprocess.run(["git", "-C", str(repo), "checkout", "main"],
                    check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    subprocess.run(["git", "-C", str(repo), "merge", "--no-ff", "side",
                    "-m", "checkpoint(task2-external): merge携带"],
                    check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
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
    approved_change(repo, plan=PLAN2_TICKETS)
    subprocess.run(["git", "-C", str(repo), "checkout", "-b", "side"],
                    check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (repo / "side.txt").write_text("y", encoding="utf-8")
    commit_all(repo, "checkpoint(task9-side): x")
    subprocess.run(["git", "-C", str(repo), "checkout", "main"],
                    check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    subprocess.run(["git", "-C", str(repo), "merge", "--no-ff", "side",
                    "-m", "merge side into main"],
                    check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    code, js, _ = run_gate(repo)
    # 9 是计划外号（plan={1,2}）：仍进 done_ids（窗口机制不变，--no-merges 只滤 merge 本身），
    # 但〔B4 集合归属〕计划外号不计入完成、不上报——done_tasks 只报计划内已完成（此处空）；
    # 仍是 CONTINUE_IMPL（plan_ids={1,2} 未被覆盖）
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == []

def test_plan_task1_same_commit_counts(repo):
    # 〔B1 闭区间〕plan 与 checkpoint(task1-) 同 commit（checkpoint add -A 携带未提交 plan）
    # → task1 锚在窗口起点 sha 自身，排他窗口会漏数；闭区间须计入
    # [harden-gate-git-layer Task1 · tasks 4.1] 两段提交：四件套先落盘 → 报告携锚后落盘
    d = mkchange(repo)
    (d / "proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    commit_all(repo, "seed change artifacts")     # 被批准的盘面（无 plan）
    write_report(d, "spec-review-report.md", head_sha(repo),
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (approved)")
    (d / "tickets.md").write_text(PLAN2_TICKETS, encoding="utf-8")
    commit_all(repo, "checkpoint(task1-foo): plan+task1 同 commit")  # plan 首次提交 == task1 锚
    commit_all(repo, "checkpoint(task2-bar): B")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"   # done={1,2} 齐（闭区间含 sha 自身）

def test_offplan_task_no_false_complete(repo):
    # 〔B4 集合归属〕plan=task1/task2，只完成 task1 + 一个计划外 task9（遗留/错号/merge 内）
    # → 基数判齐会假齐(len={1,9}=2=N)；集合归属须判 CONTINUE_IMPL（task2 未完不放行）
    approved_change(repo, plan=PLAN2_TICKETS)
    commit_all(repo, "checkpoint(task1-a): A")
    commit_all(repo, "checkpoint(task9-stray): 计划外/遗留")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL"     # 非假齐
    assert js["done_tasks"] == ["1"]            # 只报计划内已完成，不含计划外 9

def test_uncommitted_plan_no_checkbox_unknown(repo):
    # plan 写盘但不提交，且内容无任何复选框 → 双通道（标签窗口 / 复选框）皆不可判
    # [harden-implement-review-loop Task5] 含合法收尾 ticket（Task 2, Blocked-by:1, R-ID:all），
    # 使第四道校验先行通过、真正走到本用例要测的"双通道"分支（而非在第四道就先被拦下）。
    d = approved_change(repo)  # 不带 plan 提交基底
    (d / "tickets.md").write_text(
        "### Task 1: A\n**Blocked-by:** none\n正文\n"
        "### Task 2: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n正文（聚合测试套件，无复选框）\n",
        encoding="utf-8")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN" and "双通道" in js["reason"]

def test_plan_zero_titles_unknown(repo):
    approved_change(repo, plan="# 空计划，无任务标题\n")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"

def test_checkbox_fallback_advances(repo):
    # [remove-superpowers-pipeline Task2] 单名 tickets.md 下第四道校验无条件生效——
    # task2 补 Blocked-by:1 + R-ID:all 兼作收尾 ticket（其余语义不变：无标签靠复选框全勾）。
    plan = ("### Task 1: A\n**Blocked-by:** none\n- [x] s\n"
            "### Task 2: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n- [x] 聚合测试套件全部通过\n")
    approved_change(repo, plan=plan)  # 无标签但复选框全勾（回勾型执行器）
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"

# [impl-review-fix] 裁决项1/2 回归覆盖
def test_revert_commit_not_counted(repo):
    approved_change(repo, plan=PLAN2_TICKETS)
    commit_all(repo, "checkpoint(task1-a): x")
    commit_all(repo, 'Revert "checkpoint(task2-b): y"')
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]

def test_t34_no_checkbox_task_not_globally_passed(repo):
    # 〔T34〕task1 段全勾、task2 段无复选框(仅散文) → 旧全局 checkboxes_all 会因"全文无 - [ ]"
    # 假齐放行(假✅)；分段绑定后 task2 无框不计入 → CONTINUE_IMPL done_tasks==["1"]
    # [remove-superpowers-pipeline Task2] task2 补 Blocked-by:1 + R-ID:all 兼作收尾 ticket
    # （第四道校验无条件生效），散文正文与「无复选框」语义不变。
    d = approved_change(repo, plan=(
        "### Task 1: A\n**Blocked-by:** none\n- [x] done\n"
        "### Task 2: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n还没做（无复选框，聚合测试套件未跑）\n"))
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]

def test_t34_checkbox_union_with_checkpoint(repo):
    # 〔T34〕task1 由 checkpoint、task2 由其段复选框全勾 → 两通道并集齐 → RUN_CODE_REVIEW
    # [remove-superpowers-pipeline Task2] task2 补 Blocked-by:1 + R-ID:all 兼作收尾 ticket。
    approved_change(repo, plan=(
        "### Task 1: A\n**Blocked-by:** none\n(无框,靠 checkpoint)\n"
        "### Task 2: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n- [x] done 聚合测试套件\n"))
    commit_all(repo, "checkpoint(task1-a): A")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"

def test_t34_fenced_checkbox_not_counted(repo):
    # 〔T34/codex#4〕task1 段只有 fenced code block 里的伪 [x]、无真实清单行 → 忽略代码块后
    # task1 不算完成（若不忽略则假✅ 齐）；task2 真勾 → 仅 task1 未完 → CONTINUE_IMPL
    # [remove-superpowers-pipeline Task2] task2 补 Blocked-by:1 + R-ID:all 兼作收尾 ticket。
    plan = ("### Task 1: A\n**Blocked-by:** none\n实现说明\n```\n- [x] 这是代码块里的示例，不是真勾\n```\n"
            "### Task 2: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n- [x] real 聚合套件\n")
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
    # [remove-superpowers-pipeline Task2] task2 补 Blocked-by:1 + R-ID:all 兼作收尾 ticket。
    plan = ("### Task 1: 真实任务\n**Blocked-by:** none\n- [x] done\n模板示例:\n```\n### Task 1: <替换标题>\n"
            "- [ ] <替换>\n```\n### Task 2: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n- [x] 聚合 d\n")
    approved_change(repo, plan=plan)
    commit_all(repo, "checkpoint(task1-a): A")
    commit_all(repo, "checkpoint(task2-b): B")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"   # fence 内示例标题不算重号/task

def test_t34_fence_any_checkbox_consistent(repo):
    # 〔impl-review-fix 场景3〕plan_has_any_checkbox 与 checkbox_done_ids 对同一 fence 口径
    # 一致（统一 _parse_plan 后不再矛盾）：task1 段仅代码块内伪框(忽略)、task2 真勾。
    # [remove-superpowers-pipeline Task2] task2 补 Blocked-by:1 + R-ID:all 兼作收尾 ticket。
    plan = ("### Task 1: A\n**Blocked-by:** none\n```\n- [x] 代码块示例\n```\n真实无框\n"
            "### Task 2: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n- [x] real 聚合套件\n")
    approved_change(repo, plan=plan)
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["2"]

def test_non_git_root_unknown(tmp_path_factory):
    # 独立于 repo fixture：必须是真正孤立的非 git 目录（不能是 repo 的子目录，
    # 子目录会被 git 沿父级发现 .git，反而通过健全性检查）
    non_git = tmp_path_factory.mktemp("non-git-root")
    code, js, _ = run_gate(non_git)
    assert code == 6 and js["verdict"] == "UNKNOWN"


# ══════════════════════════════════════════════════════════════════════════
# [fix1 Important-1] fence 单一源在 plan 解析侧（_parse_plan）的举证。
# 旧口径只认 ```，`~~~` 块内的伪复选框/伪 Task 标题会被当真 ⇒ 假✅ / 误判重号。
# ══════════════════════════════════════════════════════════════════════════

def test_t34_tilde_fenced_checkbox_not_counted(repo):
    # `~~~` 代码块内的伪 [x]：不计入 ⇒ task1 未完成 ⇒ CONTINUE_IMPL（旧口径此处假✅齐）
    # [remove-superpowers-pipeline Task2] task2 补 Blocked-by:1 + R-ID:all 兼作收尾 ticket。
    plan = ("### Task 1: A\n**Blocked-by:** none\n实现说明\n~~~\n- [x] 代码块里的示例，不是真勾\n~~~\n"
            "### Task 2: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n- [x] real 聚合套件\n")
    approved_change(repo, plan=plan)
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["2"]


def test_t34_tilde_task_header_in_fence_not_counted(repo):
    # `~~~` 块内的 `### Task 1:` 示例标题不算 task、不误判重号
    # [remove-superpowers-pipeline Task2] task2 补 Blocked-by:1 + R-ID:all 兼作收尾 ticket。
    plan = ("### Task 1: 真实任务\n**Blocked-by:** none\n- [x] done\n模板示例:\n~~~\n### Task 1: <替换标题>\n"
            "- [ ] <替换>\n~~~\n### Task 2: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n- [x] 聚合 d\n")
    approved_change(repo, plan=plan)
    commit_all(repo, "checkpoint(task1-a): A")
    commit_all(repo, "checkpoint(task2-b): B")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"


def test_t34_unclosed_tilde_fence_unknown(repo):
    # `~~~` 悬空围栏 ⇒ 全文 fence 不平衡 ⇒ UNKNOWN(fail-safe)，与 ``` 同口径
    plan = ("### Task 1: A\n- [x] done1\n~~~\n- [ ] 真实未完成(被悬空fence吞)\n"
            "### Task 2: B\n- [x] done2\n")
    approved_change(repo, plan=plan)
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"


def test_t34_backtick_cannot_close_tilde_fence(repo):
    # 异种围栏关不掉：~~~ 开、``` 试图闭合 ⇒ 仍未闭合 ⇒ UNKNOWN
    plan = ("### Task 1: A\n- [x] done1\n~~~\n- [ ] 未完成\n```\n"
            "### Task 2: B\n- [x] done2\n")
    approved_change(repo, plan=plan)
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
