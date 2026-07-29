"""计划文件名共享 resolver 的测试(harden-implement-review-loop Task 3, D5/adr-0033)。

覆盖两层:
1. 单元层——`ship_gate.resolve_plan_path` 本身:新名优先探测/旧名向后兼容/双存在
   fail-closed(`PlanNameConflict`)/都不存在返回 None。
2. gate 端到端层(经 `decide()` 全流程)——证明:
   a. 仅新名 `tickets.md` 存在时,gate 完整判据链路(RUN_PLAN→CONTINUE_IMPL→
      RUN_CODE_REVIEW)与旧名行为等价(向前兼容,新管线不需要借旧名外衣)。
   b. 两个文件名同时存在 ⇒ UNKNOWN(不猜哪个有效,提示人工删除其一)。
   c. 〔5.10 · 🔴 在途 plan MUST NOT 被重命名 · impl-review-fix FIX-1〕改名前有 task1
      checkpoint、改名后跑 gate 的 fixture:断言该场景被 **显式拒绝**(UNKNOWN),而非静默
      漏数放行。判据 = `stray_done_tag_commits`——**不检测「有没有发生过改名」(原因),
      直接检测「危害有没有发生」(结果)**:本 change 是否有完成标签提交落在完成判据窗口
      `[plan_first_sha, HEAD]` **之外**。旧启发式(`--follow` 相似度改名检测)已被本文件
      下方三个 fixture 实测证伪(一误报两漏报),整体撤除。
"""
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import commit_all, mkchange, write_report
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2, PLAN2_TICKETS

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
    # [harden-implement-review-loop Task5] 新名受第四道校验约束——用 PLAN2_TICKETS（含合法
    # 收尾 ticket）而非裸 PLAN2，否则会在第四道被拦成 UNKNOWN，测不到本用例要验的 CONTINUE_IMPL。
    _approved_change_with_new_name(repo, PLAN2_TICKETS)
    commit_all(repo, "checkpoint(task1-foo): done A")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]


def test_new_plan_name_all_tasks_done_advances_to_code_review(repo):
    _approved_change_with_new_name(repo, PLAN2_TICKETS)
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


# ═════════════════════════════════════════════════════════════════════════
# 5.10 · 在途 plan 窗口起点自校验（impl-review-fix FIX-1）
#
# 【判据换代】旧实现 `plan_was_renamed` 比较 `git log --diff-filter=A` 带/不带 `--follow`
# 的首行 sha，用 git 的**内容相似度**重命名检测去回答「有没有发生过改名」。三种失效模式
# 均在本节 fixture 里实测：① 误报（永久自锁，无原名可改回）② 两步改名漏报 ③ mv+大幅编辑
# 漏报。两个修法互斥（调低 `-M` 阈值救 ③ 却加重 ①）⇒ 启发式路线被证伪（CLAUDE.md 基准 5）。
#
# 新判据 = `stray_done_tag_commits`：本 change 是否有 `checkpoint(<change>:task<N>-` 提交
# 落在完成判据窗口 `[plan_first_sha, HEAD]` **之外**。有 ⇒ 窗口起点错 ⇒ fail-closed UNKNOWN。
#
# 🔴 每个用例都带一条**非空锚断言**（`_old_heuristic_would_flag`）——它复算旧判据，
# 钉死「这个 fixture 确实处在旧判据会误判的那一格」。没有它，三个用例可能全是恒真绿
# （vacuous-anchor：needle 被别的门满足 / 压根没走到那条路径）。
# ═════════════════════════════════════════════════════════════════════════

# 迁移期的真实 plan 形态：新名 plan 每票带 Blocked-by/R-ID（gate 第四道校验要求），
# 且体量足以让「mv + 整体重写」把相似度打到阈值以下（模式 ③ 的天然触发路径）。
PLAN_TICKETS_RICH = (
    "### Task 1: 建立骨架\n**Blocked-by:** none\n**R-ID:** R1\n"
    "- [ ] 建目录\n- [ ] 写入口\n- [ ] 补单测\n"
    "### Task 2: 实现验证\n**Blocked-by:** 1\n**R-ID:** all\n"
    "- [ ] 按聚合套件发现契约跑单元+集成+e2e\n- [ ] 证据 schema 落 impl-report\n"
)
PLAN_OLDNAME_RICH = (
    "### Task 1: 老计划第一步\n- [ ] 甲\n- [ ] 乙\n- [ ] 丙\n- [ ] 丁\n"
    "### Task 2: 老计划第二步\n- [ ] 戊\n- [ ] 己\n- [ ] 庚\n- [ ] 辛\n"
)


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args],
                          check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def _old_heuristic_would_flag(repo, plan_rel):
    """复算**已撤除**的旧判据（`--follow` 相似度改名检测），供非空锚断言使用。

    MUST NOT 被读成「生产代码还在用它」——生产判据已换成 `stray_done_tag_commits`；
    这里只是把「本 fixture 落在旧判据的哪一格」钉成断言，防三个用例变成恒真绿。
    """
    no_follow = _git(repo, "log", "--diff-filter=A", "--format=%H", "--", plan_rel).split()
    follow = _git(repo, "log", "--follow", "--diff-filter=A", "--format=%H",
                  "--", plan_rel).split()
    if not no_follow or not follow:
        return False
    return no_follow[0] != follow[0]


def test_mode1_lookalike_plan_in_another_change_is_not_flagged(repo):
    """模式 ①（旧判据**误报** → 新判据 MUST 绿）。

    同一 commit 里「删掉 change A 的 tickets.md + 新建 change B 的 tickets.md」——因为本
    change 强制所有 tickets.md 用同一套 `### Task N:` / `Blocked-by:` / `R-ID:` 模板，
    相似度天然过线，git 把两者配对成改名。旧判据据此判 B 那个**从未被改过名**的新 plan
    为「曾被重命名」，而错误提示「请改回原文件名」**无原名可改回** ⇒ 用户唯一出路是历史
    重写（本仓明禁 `git rebase -i`，且会击穿 `reviewed_sha` 审计锚）= 永久自锁。

    新判据不误报：change B 是全新 change，其命名空间下不存在早于 plan 创建的完成标签。
    """
    other = mkchange(repo, name="change-a")
    (other / "tickets.md").write_text(PLAN_TICKETS_RICH, encoding="utf-8")
    commit_all(repo, "seed: change A 的 tickets.md")

    d = mkchange(repo)                       # change B = "demo"（gate 的目标）
    (d / "proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    (d / "tickets.md").write_text(PLAN_TICKETS_RICH, encoding="utf-8")
    (other / "tickets.md").unlink()          # 同一 commit：A 的 plan 消失、B 的 plan 出现
    commit_all(repo, "change A 收尾、change B 开工（同一提交）")
    from conftest import head_sha
    write_report(d, "spec-review-report.md", head_sha(repo),
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report (approved)")

    plan_rel = str((d / "tickets.md").relative_to(repo))
    # 非空锚：证实 git 确实把两者配对成了改名（否则本用例测不到误报面）
    assert _old_heuristic_would_flag(repo, plan_rel), \
        "fixture 失效：git 未把 A→B 的同模板 tickets.md 配对成改名，测不到旧判据的误报面"

    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL", f"新判据误报了从未改名的新 plan：{js}"
    assert js["done_tasks"] == []


def test_mode2_two_step_rename_is_detected(repo):
    """模式 ②（旧判据**漏报** → 新判据 MUST 红）。

    改名拆成两次提交（先 `git rm` 一次提交、后新建一次提交）——git 的重命名配对**只在单个
    commit 的 diff 内**做，跨 commit 的两步改名 `--follow` 无从判断 ⇒ 旧判据 False，
    而这正是设计要防的场景本身，静默放行。
    """
    d = approved_change(repo, plan=PLAN_OLDNAME_RICH)     # 旧名落盘
    commit_all(repo, "checkpoint(demo:task1-a): 改名前完成 task1")
    old_rel = str((d / "superpowers-plan.md").relative_to(repo))
    _git(repo, "rm", "-q", old_rel)
    commit_all(repo, "chore: 删掉旧名 plan（两步改名 · 第一步）")
    d.mkdir(parents=True, exist_ok=True)                   # git rm 会带走空目录
    (d / "tickets.md").write_text(PLAN_TICKETS_RICH, encoding="utf-8")
    commit_all(repo, "chore: 以新名重建 plan（两步改名 · 第二步）")

    plan_rel = str((d / "tickets.md").relative_to(repo))
    # 非空锚：证实旧判据在此确实漏报（否则本用例证明不了新判据更强）
    assert not _old_heuristic_would_flag(repo, plan_rel), \
        "fixture 失效：旧判据在两步改名下竟命中，测不到它的漏报面"

    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN", f"两步改名未被检出：{js}"
    assert "窗口" in js["reason"] and "重命名" in js["reason"]


def test_mode3_rename_with_heavy_edit_is_detected(repo):
    """模式 ③（旧判据**漏报** → 新判据 MUST 红）。

    `git mv` + **同提交大幅编辑** ⇒ 相似度跌破默认阈值（~50%），旧判据 False。而这正是
    `superpowers-plan.md` → `tickets.md` 迁移的天然形态：迁移**正需要**给每个 Task 段补
    `R-ID:` / `Blocked-by:`（本 change 新引入的格式要求）= 改名 + 大幅编辑同提交。
    """
    d = approved_change(repo, plan=PLAN_OLDNAME_RICH)
    commit_all(repo, "checkpoint(demo:task1-a): 改名前完成 task1")
    old_rel = str((d / "superpowers-plan.md").relative_to(repo))
    new_rel = str((d / "tickets.md").relative_to(repo))
    _git(repo, "mv", old_rel, new_rel)
    (d / "tickets.md").write_text(PLAN_TICKETS_RICH, encoding="utf-8")   # 同提交整体重写
    commit_all(repo, "chore: 迁 tickets.md 并补 R-ID/Blocked-by（改名+大幅编辑同提交）")

    plan_rel = new_rel
    assert not _old_heuristic_would_flag(repo, plan_rel), \
        "fixture 失效：相似度未跌破阈值，测不到旧判据在 mv+大幅编辑下的漏报面"

    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN", f"mv+大幅编辑改名未被检出：{js}"
    assert "窗口" in js["reason"] and "重命名" in js["reason"]


def test_normal_inflight_change_not_flagged(repo):
    """正常在途 change（从未改名、完成标签全在窗口内）——MUST NOT 触发窗口起点校验。"""
    approved_change(repo, plan=PLAN2)
    commit_all(repo, "checkpoint(demo:task1-a): 正常完成 task1（无改名）")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL"
    assert js["done_tasks"] == ["1"]


def test_legacy_bare_tags_outside_window_do_not_trigger(repo):
    """🔴 防大面积误报：窗口外的**裸**标签（`checkpoint(task<N>-`，无命名空间）无从归属，
    MUST NOT 被当作本 change 的窗口外完成信号——本仓 main 上大量存在别的 change 的遗留裸
    标签，认它即每个 change 全数误报（对照 test_window_excludes_legacy_and_merge）。"""
    (repo / "seed.txt").write_text("x", encoding="utf-8")
    commit_all(repo, "checkpoint(task1-legacy): 旧 change 遗留（裸标签，窗口外）")
    commit_all(repo, "checkpoint(task2-legacy): 旧 change 遗留（裸标签，窗口外）")
    approved_change(repo, plan=PLAN2)
    commit_all(repo, "checkpoint(demo:task1-a): 本 change 窗口内完成 task1")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL", f"窗口外裸标签被误当本 change 信号：{js}"
    assert js["done_tasks"] == ["1"]


def test_other_change_namespaced_tags_outside_window_do_not_trigger(repo):
    """同上，另一维度：窗口外**别的 change 的命名标签**归属明确不属本 change，MUST NOT 触发。"""
    (repo / "seed.txt").write_text("x", encoding="utf-8")
    commit_all(repo, "checkpoint(other-change:task1-x): 别的 change（窗口外）")
    approved_change(repo, plan=PLAN2)
    commit_all(repo, "checkpoint(demo:task1-a): 本 change 窗口内完成 task1")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL", f"他 change 的命名标签被误算：{js}"
    assert js["done_tasks"] == ["1"]
