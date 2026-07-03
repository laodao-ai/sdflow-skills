#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ship_gate.py — sdflow-ship 确定性台账（盘面即状态：只读、零副作用）

契约（与三个 SKILL.md 报告模板双向钉死；tests/test_anchor_contract.py 断言两侧同组字面）:

锚行字面集（grep -F 语义，零正则）:
    <!-- ship-gate: design-approved -->        spec-review-report.md（sdflow-spec-review 拍板回写）
    <!-- ship-gate: verify=PASS -->            verify-report.md（sdflow-done verify 模板）
    <!-- ship-gate: verify=FAIL -->
    <!-- ship-gate: code-review=pass -->       code-review-report.md（sdflow-code-review 模板）
    <!-- ship-gate: code-review=blocked -->

退出码: 0=可推进(含 SHIPPED/SKIP) 3=REFUSE_START 4=BLOCKED_UPSTREAM 5=VERIFY_FAIL 6=UNKNOWN

verdict × exit × next 契约表:
    REFUSE_START     3  -                  未过设计门（若拍板已发生请人工补锚——显式越权留痕）
    RUN_SOP          0  embedded-test-sop  TG-02 命中且 {change}-sop.md 缺
    RUN_PLAN         0  writing-plans      superpowers-plan.md 缺
    CONTINUE_IMPL    0  subagent-dev       标签集未齐 N（JSON done_tasks=已完成任务号集，SDD 勿重派）
    RUN_CODE_REVIEW  0  sdflow-code-review code-review-report.md 缺
    BLOCKED_UPSTREAM 4  -                  code-review=blocked
    RUN_VERIFY       0  sdflow-done        verify-report.md 缺
    VERIFY_FAIL      5  -                  verify=FAIL 且未陈旧
    RERUN_STALE      0  <该步 skill>        D9 陈旧结论 → 重跑该步
    STEP_IN_PROGRESS 0  <该步 skill>        产物在但无锚行
    SHIPPED          0  -                  final 全通（hand-off+archive+分支已并）
    UNKNOWN          6  -                  多锚冲突/双通道不可判/标题0/detached HEAD

完成判据窗口〔设计门拍板 Q2〕: superpowers-plan.md 首次提交 sha 起
    `git log <sha>..HEAD --no-merges` 收集 checkpoint(task<k>- 去重任务号集；
    plan `### Task <n>:` 计数 N；齐 N 判完成；标题命中 0 → UNKNOWN。

D9 新鲜度按锚分域〔设计门拍板 Q1=B / Q3=A〕:
    design-approved: 其后触及 openspec/changes/{change}/ 的提交 → 失鲜（改设计须重审）
    verify / code-review: 其后触及 openspec/ 之外路径的提交 → 陈旧
    报告从未提交: fresh（freshness=uncommitted，人机同权）

已知不覆盖（接受并记录）:
    openspec/workflow/ 规则漂移不触发陈旧；rebase/--amend 历史改写可伪造保鲜；
    提交遍历不加 --first-parent（merge 内部提交逐一枚举，不漏检）。
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ANCHOR_DESIGN = "<!-- ship-gate: design-approved -->"
ANCHOR_VERIFY_PASS = "<!-- ship-gate: verify=PASS -->"
ANCHOR_VERIFY_FAIL = "<!-- ship-gate: verify=FAIL -->"
ANCHOR_CR_PASS = "<!-- ship-gate: code-review=pass -->"
ANCHOR_CR_BLOCKED = "<!-- ship-gate: code-review=blocked -->"
ALL_ANCHORS = [ANCHOR_DESIGN, ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL,
               ANCHOR_CR_PASS, ANCHOR_CR_BLOCKED]

EXIT_OK, EXIT_REFUSE, EXIT_BLOCKED, EXIT_VFAIL, EXIT_UNKNOWN = 0, 3, 4, 5, 6


def run_git(root, *args):
    r = subprocess.run(["git", "-C", str(root), *args],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def anchors_in(path, candidates):
    """字面查找（零正则）。文件不存在返回 []。"""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    return [a for a in candidates if a in text]


def emit(verdict, exit_code, next_step, reason, **extra):
    human = f"[ship-gate] {verdict}"
    if next_step:
        human += f" → next={next_step}"
    human += f" — {reason}"
    print(human)
    print(json.dumps({"verdict": verdict, "next": next_step,
                      "reason": reason, **extra}, ensure_ascii=False))
    sys.exit(exit_code)


def pick_exclusive(path, positive, negative, label):
    """互斥锚对解析：两者并存 → UNKNOWN（不猜优先级）。返回 'pos'/'neg'/None。"""
    found = anchors_in(path, [positive, negative])
    if positive in found and negative in found:
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             f"{label} 报告并存冲突锚行（{positive} 与 {negative}），请人工裁决删除其一")
    if positive in found:
        return "pos"
    if negative in found:
        return "neg"
    return None


TASK_TITLE_RE = re.compile(r"^### Task (\d+):", re.M)   # 计数用；锚行才禁正则
TAG_RE = re.compile(r"checkpoint\(task(\d+)-")


def tg02_hit(cdir):
    p = cdir / "proposal.md"
    return p.is_file() and "TG-02" in p.read_text(encoding="utf-8")  # 字面子串（归档实例为全角括号混用）


def plan_task_count(plan):
    return len(TASK_TITLE_RE.findall(plan.read_text(encoding="utf-8")))


def plan_first_sha(root, plan_rel):
    out = run_git(root, "log", "--diff-filter=A", "--format=%H", "--", plan_rel)
    return out.splitlines()[-1] if out else ""


def done_task_ids(root, sha):
    msgs = run_git(root, "log", f"{sha}..HEAD", "--no-merges", "--format=%s")
    return {m.group(1) for line in msgs.splitlines() if (m := TAG_RE.search(line))}


def checkboxes_all(plan):
    text = plan.read_text(encoding="utf-8")
    unchecked, checked = "- [ ]" in text, "- [x]" in text
    if not unchecked and not checked:
        return None
    return not unchecked


def branch_state(root):
    """已并判定〔spec-review-amendment D6〕。"""
    head = run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if head == "HEAD":
        return "unknown"          # detached HEAD
    for base in ("main", "master"):
        if run_git(root, "rev-parse", "--verify", base):
            if head == base:
                return "merged"   # 已在 base 上（分支已删/已并场景）
            return "merged" if not run_git(root, "log", f"{base}..HEAD",
                                           "--oneline") else "pending"
    return "unknown"


def decide(root, change):
    cdir = root / "openspec" / "changes" / change
    # ── pre-flight：设计门（D7 起跑不越门）─────────────────────────
    report = cdir / "spec-review-report.md"
    if ANCHOR_DESIGN not in anchors_in(report, [ANCHOR_DESIGN]):
        emit("REFUSE_START", EXIT_REFUSE, None,
             "未过设计门：spec-review-report.md 缺失或无 design-approved 锚行；"
             "先完成设计门；若拍板已发生请人工补锚（显式越权留痕）")
    # ── verify 冲突锚早检（多锚冲突 → UNKNOWN，任务3 完整接管步序）──
    vfile = cdir / "verify-report.md"
    if vfile.is_file():
        pick_exclusive(vfile, ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL, "verify")
    # ── step 5.5：条件步（TG-02 字面子串；细判归模型）────────────
    sop_note = ""
    if tg02_hit(cdir):
        if not (cdir / f"{change}-sop.md").is_file():
            emit("RUN_SOP", EXIT_OK, "embedded-test-sop", "TG-02 命中且 sop 产物缺")
    else:
        sop_note = "SKIP_SOP(非嵌入式不触发); "
    # ── step 6/7：plan 与完成判据〔Q2 窗口主锚〕──────────────────
    plan = cdir / "superpowers-plan.md"
    if not plan.is_file():
        emit("RUN_PLAN", EXIT_OK, "writing-plans", sop_note + "superpowers-plan.md 缺")
    n = plan_task_count(plan)
    if n == 0:
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             "plan 无 '### Task <n>:' 标题（上游模板漂移？），完成判据不能")
    sha = plan_first_sha(root, str(plan.relative_to(root)))
    done = done_task_ids(root, sha) if sha else set()
    if len(done) < n:
        boxes = checkboxes_all(plan)
        if boxes is True:
            pass  # 辅通道：复选框全勾（回勾型执行器）
        elif not sha and boxes is None:
            emit("UNKNOWN", EXIT_UNKNOWN, None, "plan 未提交且无复选框，双通道皆不可判")
        else:
            emit("CONTINUE_IMPL", EXIT_OK, "subagent-dev",
                 f"实现进度 {len(done)}/{n}（窗口 {sha[:7] or '-'}..HEAD --no-merges）",
                 done_tasks=sorted(done, key=int))
    # ── step 8：code-review 门 ─────────────────────────────────
    cr = cdir / "code-review-report.md"
    if not cr.is_file():
        emit("RUN_CODE_REVIEW", EXIT_OK, "sdflow-code-review", "实现完成，进入代码审")
    cr_state = pick_exclusive(cr, ANCHOR_CR_PASS, ANCHOR_CR_BLOCKED, "code-review")
    if cr_state == "neg":
        emit("BLOCKED_UPSTREAM", EXIT_BLOCKED, None,
             "code-review 判 blocked：先解 blocker（见报告），gate 不蒙头跑")
    if cr_state is None:
        emit("STEP_IN_PROGRESS", EXIT_OK, "sdflow-code-review",
             "code-review-report.md 在但无锚行 → 该步进行中，重跑")
    # ── step 9：verify 终门 ────────────────────────────────────
    vf = cdir / "verify-report.md"
    if not vf.is_file():
        emit("RUN_VERIFY", EXIT_OK, "sdflow-done", "进入收尾（verify→hand-off→archive→merge）")
    v_state = pick_exclusive(vf, ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL, "verify")
    if v_state == "neg":
        emit("VERIFY_FAIL", EXIT_VFAIL, None, "verify FAIL：停并上抛缺口清单（报告内）")
    if v_state is None:
        emit("STEP_IN_PROGRESS", EXIT_OK, "sdflow-done",
             "verify-report.md 在但无锚行 → 该步进行中，重跑")
    # ── final：SHIPPED 判定 ────────────────────────────────────
    handoff = (cdir / "hand-off.md").is_file()
    archived = any((root / "openspec" / "changes" / "archive").glob(f"*-{change}"))
    bstate = branch_state(root)
    if bstate == "unknown":
        emit("UNKNOWN", EXIT_UNKNOWN, None, "detached HEAD，分支态判定不能")
    if handoff and archived and bstate == "merged":
        emit("SHIPPED", EXIT_OK, None,
             "全通：verify PASS + hand-off + 已归档 + 分支已并。"
             "未 push（手动控制）；toolkit 源仓请 push 后新会话 /sdflow-upgrade 激活")
    emit("RUN_VERIFY", EXIT_OK, "sdflow-done",
         f"verify PASS 但收尾未完（hand-off={handoff} archive={archived} branch={bstate}）")


def main(argv=None):
    p = argparse.ArgumentParser(description="sdflow-ship 盘面判官（只读）")
    p.add_argument("--change", required=True)
    p.add_argument("--root", default=None)
    a = p.parse_args(argv)
    root = Path(a.root) if a.root else Path(
        run_git(Path.cwd(), "rev-parse", "--show-toplevel") or Path.cwd())
    decide(root, a.change)


if __name__ == "__main__":
    main()
