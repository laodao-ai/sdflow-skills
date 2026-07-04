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
    REFUSE_START     3  -                  未过设计门（补锚）｜change 不存在（active 与 archive 均无）〔B3〕
    RUN_SOP          0  embedded-test-sop  TG-02 命中且 {change}-sop.md 缺
    RUN_PLAN         0  writing-plans      superpowers-plan.md 缺
    CONTINUE_IMPL    0  subagent-dev       plan_ids⊄done_ids〔B4 集合归属〕（JSON done_tasks=计划内已完成号集，SDD 勿重派）
    RUN_CODE_REVIEW  0  sdflow-code-review code-review-report.md 缺
    BLOCKED_UPSTREAM 4  -                  code-review=blocked
    RUN_VERIFY       0  sdflow-done        verify-report.md 缺｜active 存在 verify=PASS 待收尾｜归档未并 base 待 merge 收尾〔B3/BR-10〕
    VERIFY_FAIL      5  -                  verify=FAIL 且未陈旧
    RERUN_STALE      0  <该步 skill>        D9 陈旧结论 → 重跑该步
    STEP_IN_PROGRESS 0  <该步 skill>        产物在但无锚行
    SHIPPED          0  -                  归档已并 base + archived verify=PASS 锚〔B3+D3硬化,含归档后重跑识别；active 缺席才判,detached 无关〕
    UNKNOWN          6  -                  多锚冲突/双通道不可判/标题0/归档在 base 缺 verify 锚(空壳 fail-safe)/无 base 判不能

完成判据窗口〔B1 闭区间〕: superpowers-plan.md 首次提交 sha 起，窗口 [sha, HEAD] 闭区间
    `git log <sha>..HEAD --no-merges` 加 sha 自身 subject（同前缀+TAG_RE 规则）收集
    checkpoint(task<k>- 去重任务号集 done_ids；plan `### Task <n>:` 号集 plan_ids；
    plan_ids ⊆ done_ids 判完成〔B4 集合归属,非基数〕；标题命中 0 → UNKNOWN。

D9 新鲜度按锚分域〔设计门拍板 Q1=B / Q3=A〕:
    design-approved: 其后触及本 change 四件套路径（proposal/design/tasks.md 与 specs/）
        的提交 → 失鲜（改设计须重审）；cr/verify/hand-off 等尾流产物不算，实现提交更不算；
        例外〔B2〕: subject 精确 `checkpoint(impl-review)` 或 `checkpoint(impl-review):…`
        的提交豁免（阶段三合法尾流修订，code-review 回填措辞/勾选），只认 subject 不认 hunk
    verify / code-review: 其后触及 openspec/ 之外路径的提交 → 陈旧
        （verify=FAIL 陈旧优先于 code-review 陈旧判定，保重验不因陈旧 CR 卡死）
    报告从未提交: fresh（freshness=uncommitted，人机同权）

已知不覆盖（接受并记录）:
    openspec/workflow/ 规则漂移不触发陈旧；rebase/--amend 历史改写可伪造保鲜；
    提交遍历不加 --first-parent（merge 内部提交逐一枚举）；但 evil-merge——仅存在于 merge
        commit 自身、两 parent 提交都没碰过的改动——因 --name-only 默认不产 merge diff 而漏检
        （对抗镜 Adv-B；普通冲突解决 merge 多被 side 分支内碰同名文件的提交顺带判陈旧，暴露面偏对抗）；
    非 UTF-8 报告以 replace 解码（ASCII 锚行不受影响，中文正文可能乱码不影响机判）；
    伪造/手工 checkpoint(impl-review) subject 可绕过 design 域失鲜——gate 不核验生产者
        （显式越权同权级，git 留痕可审计）；
    经 impl-review 豁免的四件套编辑不经二次批准即随档 ship（安全边界=约定级「仅装饰性
        改动」，gate 不做 hunk 分析；若某次措辞修正实际改动设计语义会静默 merge，设计门 Q2 接受）；
    精确同名 change 历史归档过（archive 有真同名旧档 + 已并 base + 带 verify=PASS 锚）而新一轮
        同名 change 尚未建 active 目录时，D3 短路按旧档报 SHIPPED——change 重名属反模式，接受〔B3〕。
"""  # [impl-review-fix]
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


# [impl-review-fix] git 调用统一注入两道加固（对抗镜 Adv-A + 正确性/历史镜 F1）：
#   ① -c core.quotePath=false：git 默认把非 ASCII 路径 C-quote（八进制+首尾引号），
#      裸 f.startswith(base)/startswith("openspec/") 对中文文件名路径全失配 → design 域假鲜
#      （拍板后偷改中文名 spec 静默放行=假✅）/ code 域假陈旧。本项目中文文件名密集，realistic。
#   ② errors="replace"：报告内容/subject/文件名非 UTF-8 时 strict 解码抛 UnicodeDecodeError
#      → 退出码 1 逸出契约集 {0,3,4,5,6}；与头注释「非 UTF-8 以 replace 解码」及本地 read_text
#      路径的既有加固对齐（archived verify 走 git show 是首个用 subprocess 读报告内容的路径）。
_GIT_HARDEN = ("-c", "core.quotePath=false")


def run_git(root, *args):
    r = subprocess.run(["git", "-C", str(root), *_GIT_HARDEN, *args],
                       capture_output=True, text=True, errors="replace")
    return r.stdout.strip() if r.returncode == 0 else ""


def run_git_rc(root, *args):
    # [spec-review-amendment H3] 返回码可见版：run_git 把 git 错误与「路径不在树/空输出」
    # 都折叠成空串，base_ref 的 None 性据此驱动「base 不存在→UNKNOWN」vs「归档缺→REFUSE」分岔。
    r = subprocess.run(["git", "-C", str(root), *_GIT_HARDEN, *args],
                       capture_output=True, text=True, errors="replace")
    return r.returncode, r.stdout.strip()


def base_ref(root):
    # [spec-review-amendment H3] 单一 base 解析：main 优先 master 次，皆无→None（→UNKNOWN）。
    # [impl-review-fix] 限定 refs/heads/（CV-2）：裸 `rev-parse --verify main` 会把名为 main/
    # master 的 tag 误当 base 分支；D3 判据须锚在分支语义，返回完整 ref 传给 ls-tree/show。
    for base in ("main", "master"):
        rc, _ = run_git_rc(root, "rev-parse", "--verify", f"refs/heads/{base}")
        if rc == 0:
            return f"refs/heads/{base}"
    return None


def archived_dirs_in_tree(root, ref, change):
    # [spec-review-amendment H2/H5] 纯 git 域发现（非文件系统 glob，工作树无关、忽略未跟踪
    # 垃圾目录）：列 ref 树里 archive/ 的直接子项，以 re.escape(change) 套日期前缀 fullmatch
    # （H5 注入防御：--change 的 * ? [] 不当 glob 元字符）。返回匹配的 archive 目录名 set。
    rc, out = run_git_rc(root, "ls-tree", "--name-only", ref,
                         "openspec/changes/archive/")
    if rc != 0 or not out:
        return set()
    pat = re.compile(r"\d{4}-\d\d-\d\d-" + re.escape(change) + r"$")
    return {line.rsplit("/", 1)[-1] for line in out.splitlines()
            if pat.fullmatch(line.rsplit("/", 1)[-1])}


def archived_verify_state(root, ref, archive_dir):
    # [spec-review-amendment H1/BR-2] SHIPPED 前追读归档目录内 verify-report.md 的 verify 锚
    # （从 ref 树）——不把「归档⟹已验」当无条件蕴含（手工空壳归档目录不得假 SHIPPED）。
    # [impl-review-fix] tri-state（CV-1/HRTG-c2 三声）：active 路径靠 pick_exclusive 对冲突锚
    # 判 UNKNOWN，D3 短路须同等互斥——PASS+FAIL 并存 = 'conflict'（→UNKNOWN），非只查 PASS in。
    rc, out = run_git_rc(root, "show",
                         f"{ref}:openspec/changes/archive/{archive_dir}/verify-report.md")
    if rc != 0:
        return "none"
    has_pass, has_fail = ANCHOR_VERIFY_PASS in out, ANCHOR_VERIFY_FAIL in out
    if has_pass and has_fail:
        return "conflict"
    return "pass" if has_pass else "none"


def report_last_sha(root, rel):
    return run_git(root, "log", "-1", "--format=%H", "--", rel)


DESIGN_WATCHED_NAMES = ("proposal.md", "design.md", "tasks.md")   # D9〔design.md 决策源〕四件套


def is_stale(root, rel, scope, change):
    """D9 分域〔Q1=B/Q3=A〕。scope: 'design'|'code'。返回 (stale, freshness)。

    design 域仅盯本 change 四件套路径（proposal/design/tasks.md 与 specs/）——
    不可套用整个 openspec/changes/{change}/：该目录还装着 cr/verify/hand-off 等
    正常尾流产物，套用整目录会让收尾提交把 design-approved 误判陈旧（链自锁）。
    """
    sha = report_last_sha(root, rel)
    if not sha:
        return False, "uncommitted"          # Q3=A：人机同权，手写产物合法
    base = f"openspec/changes/{change}/"
    if scope == "design":
        # [spec-review-amendment B2] 带 subject 分帧遍历，checkpoint(impl-review) 精确式豁免。
        # 帧形（--format=%x00%s --name-only）：`\x00<subject>\n\n<file>\n<file>…`，按 \x00 切帧，
        # 帧首行=subject、余非空行=触及文件。MUST NOT 加 --no-merges/--first-parent〔BR-6 护栏〕
        # ——头注释承诺 merge 内部提交逐一枚举不漏检；--no-merges 会改变 merge 场景失鲜语义。
        out = run_git(root, "log", f"{sha}..HEAD", "--name-only", "--format=%x00%s")
        for frame in out.split("\x00"):
            if not frame:
                continue
            lines = frame.split("\n")
            subject = lines[0]
            # [spec-review-amendment BR-7] 精确式：裸 checkpoint(impl-review) 或带冒号描述；
            # 裸 startswith 闭合前缀仍收 `checkpoint(impl-review)evil` 尾串垃圾，故用精确式。
            if subject == "checkpoint(impl-review)" or subject.startswith("checkpoint(impl-review):"):
                continue                      # 阶段三合法尾流修订，豁免不失鲜
            for f in lines[1:]:
                if not f:
                    continue
                if f.startswith(base):
                    sub = f[len(base):]
                    if sub in DESIGN_WATCHED_NAMES or sub.startswith("specs/"):
                        return True, "stale"
        return False, "fresh"
    # scope == "code"：行为逐字不变（无 subject、无豁免、无 --no-merges）
    files = run_git(root, "log", f"{sha}..HEAD", "--name-only", "--format=")
    for f in filter(None, files.splitlines()):
        if not f.startswith("openspec/"):
            return True, "stale"
    return False, "fresh"


def anchors_in(path, candidates):
    """字面查找（零正则）。文件不存在返回 []。"""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")  # [impl-review-fix] 非 UTF-8 防崩
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
TAG_RE = re.compile(r"checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-")  # [T32] 可选命名空间组


def tg02_hit(cdir):
    p = cdir / "proposal.md"
    # [impl-review-fix] errors="replace" 防非 UTF-8 报告崩溃
    return p.is_file() and "TG-02" in p.read_text(encoding="utf-8", errors="replace")  # 字面子串（归档实例为全角括号混用）


def plan_task_ids(plan):
    # [spec-review-amendment B4/D5] plan 声明的任务号集（去重）。完成判据按**集合归属**
    # （plan_ids ⊆ done_ids）而非基数（len(done) < n）——否则计划外任务号（遗留/错号/
    # merge 内提交的 checkpoint(task9-)）会顶替缺失的计划内号让基数达标而假齐（假✅）。
    text = plan.read_text(encoding="utf-8", errors="replace")
    return set(TASK_TITLE_RE.findall(text))


def plan_task_count(plan):
    return len(plan_task_ids(plan))


def plan_first_sha(root, plan_rel):
    out = run_git(root, "log", "--diff-filter=A", "--format=%H", "--", plan_rel)
    # [impl-review-fix] 取首行（最新一次新增记录，git log 默认新→旧序）而非末行：
    # plan 被删后重建场景，重建视为该 plan 的新生命周期，窗口应锚定最新一次 A 记录，
    # 否则窗口会回溯到已作废的旧生命周期首次新增点，混入重建前的历史提交。
    return out.splitlines()[0] if out else ""


def done_task_ids(root, sha, change):
    # [spec-review-amendment B1] 窗口闭区间 [sha, HEAD]：{sha}..HEAD 排他 + sha 自身 subject。
    # checkpoint 的 add -A 会把未提交的 superpowers-plan.md 与 task1 锚打进同一 commit（即 sha），
    # 排他 {sha}..HEAD 会漏数 task1；追加解析 sha 自身 subject（同前缀+TAG_RE 规则）补齐。
    # [ship-gate-hardening-2 T32] change 命名空间归属：命名标签 checkpoint(<ns>:task<N>-)
    # 仅当 ns==change（精确==，非前缀）计入；裸标签 checkpoint(task<N>-) 走窗口计入（A1 兼容）。
    msgs = run_git(root, "log", f"{sha}..HEAD", "--no-merges", "--format=%s")
    lines = msgs.splitlines()
    self_subject = run_git(root, "log", "-1", "--format=%s", sha)
    if self_subject:
        lines.append(self_subject)
    ids = set()
    for line in lines:
        # [impl-review-fix] 先判字面前缀再锚定匹配：`Revert "checkpoint(task2-b): y"`
        # 这类 revert 提交消息里 checkpoint( 子串不在行首，不应计入完成集
        # （TAG_RE.search 不锚位置会把它误计，match 从位置 0 锚定则天然排除）。
        # [ship-gate-hardening-2 T32/A-F1] 前缀过滤 MUST 放宽为 "checkpoint("——旧硬前缀
        # "checkpoint(task" 会把命名标签 checkpoint(<ns>:task 在 TAG_RE.match 前整条跳过，
        # 令 T32 静默失效并吞掉本 change 自己的命名完成号。
        if not line.startswith("checkpoint("):
            continue
        m = TAG_RE.match(line)
        if not m:
            continue
        ns, num = m.group(1), m.group(2)
        if ns is not None and ns != change:
            continue  # 命名空间不匹配当前 change → 排除（假阴安全，不新增假阳）
        ids.add(num)
    return ids


def checkboxes_all(plan):
    text = plan.read_text(encoding="utf-8", errors="replace")
    unchecked, checked = "- [ ]" in text, "- [x]" in text
    if not unchecked and not checked:
        return None
    return not unchecked


# [spec-review-amendment H4] branch_state() 已移除：D3 终态判据改 change 域可达性
# （archived_dirs_in_tree + base 树），不再用「当前 HEAD 分支是否并进 base」这一全局近似；
# final 路径（active 存在）恒 RUN_VERIFY 不判 SHIPPED，故也无需 branch_state。detached HEAD
# 对 D3 判定无关（凭 base 树可达仍可 SHIPPED）——旧「detached→UNKNOWN」契约随之废止。


def decide(root, change):
    # ── git 健全性前置：run_git 吞错会让下游静默失效（D9 等判定悄悄全假）──
    # [impl-review-fix] 先验 git 可用且 --root 确为 git 仓，防止后续所有 run_git
    # 调用因非仓/git 缺失而返回空串，被误判为"文件未提交"等正常态。
    if not run_git(root, "rev-parse", "--git-dir"):
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             "git 不可用或 --root 非 git 仓，无法读盘面")
    cdir = root / "openspec" / "changes" / change
    # ── D3 归档终态短路〔B3 + D3 硬化 H1-H6〕: active 缺席时纯 git 域查归档 ──
    # 顺序关键：短路必须在设计门 pre-flight 与 freshness 之前——归档 commit 的 --name-only
    # 会列出 active 路径删除记录，若先跑 freshness 会引入新误报；短路后该路径天然不可达。
    if not cdir.exists():
        base = base_ref(root)
        head_dirs = archived_dirs_in_tree(root, "HEAD", change)   # H2 纯 git 域(工作树无关)
        base_dirs = archived_dirs_in_tree(root, base, change) if base else set()
        if base is None:
            if head_dirs:
                emit("UNKNOWN", EXIT_UNKNOWN, None,
                     "归档存在于 HEAD 树但仓无 base(main/master)，无法判是否已并 → 判定不能")
            emit("REFUSE_START", EXIT_REFUSE, None,
                 "change 不存在（active 与 archive 均无）")
        # H1/BR-2: SHIPPED 须归档在 base 树 且 archived verify 锚 tri-state 判定
        base_states = [archived_verify_state(root, base, d) for d in base_dirs]
        if "conflict" in base_states:
            # 归档 verify-report 并存 PASS/FAIL 冲突锚 → 同 active 路径 pick_exclusive 语义〔CV-1〕
            emit("UNKNOWN", EXIT_UNKNOWN, None,
                 "归档 verify-report 并存 PASS/FAIL 冲突锚 → 判定不能，请人工裁决删其一")
        if "pass" in base_states:
            emit("SHIPPED", EXIT_OK, None,
                 "全通（归档后重跑识别）：归档已并 base + verify=PASS 锚。"
                 "未 push（手动控制）；toolkit 源仓请 push 后新会话 /sdflow-upgrade 激活")
        if base_dirs:
            # 归档已并 base 但无 verify=PASS 锚（空壳/未验/仅 FAIL）→ fail-safe 不判 SHIPPED〔H1/Q3〕
            emit("UNKNOWN", EXIT_UNKNOWN, None,
                 "归档已并 base 但缺 verify=PASS 锚（空壳/未验）→ fail-safe 不判 SHIPPED，请人工核验")
        if head_dirs:
            # H4: detached 无关，凭 base 树可达；仅在 HEAD 树=归档未并 base
            emit("RUN_VERIFY", EXIT_OK, "sdflow-done",
                 "已归档但未并 base，完成 merge 收尾")
        emit("REFUSE_START", EXIT_REFUSE, None,
             "change 不存在（active 与 archive 均无）")
    # ── pre-flight：设计门（D7 起跑不越门）─────────────────────────
    report = cdir / "spec-review-report.md"
    if ANCHOR_DESIGN not in anchors_in(report, [ANCHOR_DESIGN]):
        emit("REFUSE_START", EXIT_REFUSE, None,
             "未过设计门：spec-review-report.md 缺失或无 design-approved 锚行；"
             "先完成设计门；若拍板已发生请人工补锚（显式越权留痕）")
    design_stale, _design_fresh = is_stale(
        root, str(report.relative_to(root)), "design", change)
    if design_stale:
        emit("REFUSE_START", EXIT_REFUSE, None,
             "design-approved 之后四件套被改动 → 拍板失鲜，改设计须重审"
             "（重跑 sdflow-spec-review 后重新拍板补锚）")
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
    plan_ids = plan_task_ids(plan)
    n = len(plan_ids)
    if n == 0:
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             "plan 无 '### Task <n>:' 标题（上游模板漂移？），完成判据不能")
    sha = plan_first_sha(root, str(plan.relative_to(root)))
    done = done_task_ids(root, sha, change) if sha else set()
    done_in_plan = done & plan_ids            # [spec-review-amendment B4] 只认计划内号
    if plan_ids - done:                       # 计划内有未完成号 → 未齐（集合归属,非基数）
        boxes = checkboxes_all(plan)
        if boxes is True:
            pass  # 辅通道：复选框全勾（回勾型执行器）
        elif not sha and boxes is None:
            emit("UNKNOWN", EXIT_UNKNOWN, None, "plan 未提交且无复选框，双通道皆不可判")
        else:
            emit("CONTINUE_IMPL", EXIT_OK, "subagent-dev",
                 f"实现进度 {len(done_in_plan)}/{n}（窗口 [{sha[:7] or '-'}, HEAD] 闭区间，集合归属）",
                 done_tasks=sorted(done_in_plan, key=int))
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
    cr_stale, cr_fresh = is_stale(root, str(cr.relative_to(root)), "code", change)
    cr_stale_note = None
    if cr_stale:
        # 陈旧判定优先级须让位于「verify=FAIL 之后修代码重验」链路：verify 已判 FAIL
        # 时不要求先重跑 code-review（否则陈旧 FAIL 卡死），留给 step9 判 RERUN_STALE。
        vf_peek = cdir / "verify-report.md"
        verify_already_failed = ANCHOR_VERIFY_FAIL in anchors_in(vf_peek, [ANCHOR_VERIFY_FAIL])
        if not verify_already_failed:
            emit("RERUN_STALE", EXIT_OK, "sdflow-code-review",
                 "code-review 结论后存在 openspec/ 外提交 → 结论陈旧，重审", freshness=cr_fresh)
        # verify 已 FAIL：本轮不在此处抢跳，但把 cr 陈旧状态记下，
        # 传给 step9 的 VERIFY_FAIL 输出（〔任务4 fix 轮 F1〕，避免陈旧信息在此处丢失）。
        cr_stale_note = "（注意：code-review 结论亦已陈旧，修复后需重跑代码审）"
    # ── step 9：verify 终门 ────────────────────────────────────
    vf = cdir / "verify-report.md"
    if not vf.is_file():
        emit("RUN_VERIFY", EXIT_OK, "sdflow-done", "进入收尾（verify→hand-off→archive→merge）")
    v_stale, v_fresh = is_stale(root, str(vf.relative_to(root)), "code", change)
    v_state = pick_exclusive(vf, ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL, "verify")
    if v_stale:
        emit("RERUN_STALE", EXIT_OK, "sdflow-done",
             "verify 结论后存在 openspec/ 外提交 → 结论陈旧（FAIL 修复后重验不卡死 / PASS 不背书新代码）",
             freshness=v_fresh)
    if v_state == "neg":
        reason = "verify FAIL：停并上抛缺口清单（报告内）"
        extra = {}
        if cr_stale_note:
            reason += cr_stale_note
            extra["cr_freshness"] = "stale"
        emit("VERIFY_FAIL", EXIT_VFAIL, None, reason, **extra)
    if v_state is None:
        emit("STEP_IN_PROGRESS", EXIT_OK, "sdflow-done",
             "verify-report.md 在但无锚行 → 该步进行中，重跑")
    # ── final：active 存在 + verify PASS → 收尾未完（绝不 SHIPPED）─────
    # [spec-review-amendment H1/HRTG-1] active 目录仍在 = archive 尚未发生（真 archive 移走
    # active）→ 本态至多「待收尾」。真 SHIPPED（归档后）由 decide 开头的 D3 短路识别
    # （active 缺席 + base 树可达 + archived verify=PASS 锚）。旧逻辑凭 archive glob 存在性
    # 判 SHIPPED 会被旧/同名 archive 误触发（HRTG-1 假 SHIPPED），故 active 存在时不判 SHIPPED。
    handoff = (cdir / "hand-off.md").is_file()
    emit("RUN_VERIFY", EXIT_OK, "sdflow-done",
         f"verify PASS，收尾未完（hand-off={handoff}；archive+merge 由 sdflow-done，"
         "归档后 SHIPPED 由 gate 短路识别）", freshness=v_fresh)


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
