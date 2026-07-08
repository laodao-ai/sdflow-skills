#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ship_gate.py — sdflow-ship 确定性台账（盘面即状态：只读、零副作用）

契约（与三个 SKILL.md 报告模板双向钉死；tests/test_anchor_contract.py 断言两侧同组字面）:

机判锚形态〔mlh-p5 迁 frontmatter；Task6 退役 live inline 读半场〕:
    live 读（active change 报告）: **只读**报告**头部** frontmatter `ship-gate.{field}`；absent
        （无 frontmatter / 无 ship-gate 键）→ 既有无锚语义（design→REFUSE_START、verify /
        code-review→STEP_IN_PROGRESS），**不回退 inline**（Task6 退役：三 producer 已全写
        frontmatter，live 正文残留 inline 锚被完全忽略）；frontmatter 存在但坏（越域/重复键/
        tab 缩进等）→ UNKNOWN(6) fail-closed（防坏 frontmatter 悄悄放行）。
    归档读（archived change 报告）: 与 live 共用同一严格 helper `parse_ship_gate_frontmatter`，
        但**保留 inline dual-read**（`_line_scoped_hits` 归档读半场永久，冷审 F2）——frontmatter
        优先（新归档）；absent（迁移前旧归档，永久保留）→ 回退 inline；坏 frontmatter → fail-safe
        判无 pass（归档不可变、无人可修，不回退 inline 掩盖假 SHIPPED）。

ship-gate frontmatter 字段（三字段，下划线命名，防与旧 inline 锚字面连字符漂移，取值域见 FIELD_ENUMS）:
    design_approved: true|false   spec-review-report.md（sdflow-spec-review 拍板回写，头部 prepend）
    verify: PASS|FAIL             verify-report.md（sdflow-done verify 模板，头部 prepend）
    code_review: pass|blocked     code-review-report.md（sdflow-code-review 模板，头部 prepend）

inline 锚行字面集（grep -F 语义，零正则；Task6 后**仅归档读半场**用于旧归档兜底，live 不再读；三 SKILL 新产出报告不再落）:
    <!-- ship-gate: design-approved -->        spec-review-report.md（旧格式）
    <!-- ship-gate: verify=PASS -->            verify-report.md（旧格式）
    <!-- ship-gate: verify=FAIL -->
    <!-- ship-gate: code-review=pass -->       code-review-report.md（旧格式）
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
    checkpoint(<change>:task<k>- 命名空间标签去重任务号集 done_ids〔ship-gate-hardening-2 T32：
        gate 只认当前 change 的命名标签，跨 change stacking 不互相污染；裸 checkpoint(task<k>-
        旧格式向后兼容仍计入窗口；startswith 前缀过滤放宽为 "checkpoint("〕；
    复选框辅通道按 `### Task <n>:` 分段绑定并入 done_ids〔T34：行锚定+忽略代码块，非全局全勾放行〕；
    plan `### Task <n>:` 号集 plan_ids；plan_ids ⊆ done_ids 判完成〔B4 集合归属,非基数〕；
    标题命中 0 → UNKNOWN；重号 Task 段 → UNKNOWN〔T34：set 折叠掩盖假✅〕。

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
        同名 change 尚未建 active 目录时，D3 短路按旧档报 SHIPPED——change 重名属反模式，接受〔B3〕；
    〔ship-gate-hardening-2 T32〕命名空间隔离对**裸格式污染方**不免疫：stacking（feat/A 上再建
        change B，FF-0 不拦）+ B 用旧裸格式 + 撞 plan 号 → 裸标签走窗口计入仍污染 A 的完成集。
        新格式 change 对命名污染全免疫；残留仅"裸污染方 stacking + 撞号"。MUST NOT 用"每 change
        独立分支纪律"作缓解——纪律成立则污染不可达、隔离自否（防御纵深立场，见 adr/0008）；
    〔gate-checkpoint-hardening T33/T35 定夺，正式化原 ship-gate-hardening-2 T33 停置〕新鲜度
        MUST 只看已提交盘面（committed 产物与结论锚行），MUST NOT 纳入工作树 staged/unstaged/
        untracked 的非 openspec 代码改动——与「盘面即状态=committed 产物」地基一致，越过 committed
        边界会让 gate 判定随未提交、可撤销的工作树状态摇摆；`sdflow-ship` MAY 在收尾以非门禁软
        提示告知工作树有未提交改动、gate 判定不含它们，MUST NOT 改变退出码。merge 前 untracked
        硬检查〔spec-review-amendment SR-2〕落在 `sdflow-done` 的 merge 步（非交互 halt+报告上抛，
        复用既有"ff 不可行→停下报告"惯用法），MUST NOT 上移进 gate 本身——本文件逻辑不变。
    〔gate-anchor-line-scoped〕机判锚 MUST 独占一行（strip 后行级等值 + 忽略 ``` 代码块内），
        两处解析点 anchors_in（读文件）/ archived_verify_state（git-show 文本）共用同一文本级
        核心 `_line_scoped_hits`，杜绝两路径各判各的漂移〔ADR-1/2/4〕；
    〔ADR-5〕互斥锚对（verify PASS/FAIL、code-review pass/blocked）若遇未闭合 ``` fence 吞掉负锚，
        不得因此误判 pass——保守判 UNKNOWN（active，pick_exclusive）/ none（archived，
        archived_verify_state），宁可判定不能也不假阳；
    〔ADR-6〕tg02_hit 触发检测 = 声明式匹配全角括号头注 `〔TG-02`（ff 强制格式），非裸子串——
        描述性提及/代码引用/否定句（如提及 "TG-01/02/03"）不再误触发 RUN_SOP；
    多行 HTML 注释内嵌锚不解析：不判断锚是否落在更大的 `<!-- ... -->` 多行注释块「内部」被
        整体注释掉——模板锚本身即单行注释，独占一行等值已足；多行嵌套锚属人为构造，归
        「显式越权同权级」（git 留痕可审计）；
    `~~~` 围栏 / 带语言标签围栏（如 ```python）导致的围栏识别误判不特判——仅认 ``` 前缀翻转，
        非本仓现实语料出现的变体不收，且方向 = 安全侧假阴（漏判不覆盖 ≠ 假阳）。
    〔mlh-p5 Q4；Task6 退役 live inline 后收敛〕live 读**只认 frontmatter**：好 frontmatter
        判定后不看正文任何 inline 锚，absent 亦不回退 inline（正文残留 inline 锚被完全忽略，
        无假过风险，B4/B5 根治）。归档读 dual-read 侧仍保留旧语义：好 frontmatter 判定后不再
        交叉扫同文件残留 inline 锚（frontmatter 有效即唯一真相源；旧归档 absent 才回退 inline）。
        此盲区随 live 退役彻底收敛，仅归档 dual-read 保留"好 frontmatter 不交叉扫 inline"，接受。
    〔impl-review-fix A1 多块 stale-first-block〕D2「只认 frontmatter 首块」为自指免疫**有意**
        牺牲全文冲突检测：本仓报告正文常讨论 ship-gate frontmatter（含 body 内示例块），若报告
        顶部残旧首块 + 下方追加新块，只读首块。缓解=producer MUST 覆写首块 + verify-report 每次
        fresh 写。MUST NOT 改为「第二块存在→fail」（会重开自指陷阱，误崩讨论 frontmatter 的合法
        报告）。断言钉死：test_second_frontmatter_block_ignored_by_design。
    〔impl-review-fix 引号值严格〕`verify: "PASS"`（带引号）→ out-of-domain（有意，enum 严格
        字面匹配，不做 YAML 引号剥离）。断言钉死：test_quoted_value_is_strict。
    〔impl-review-fix B3 归档 encoding〕run_git/run_git_rc 用 subprocess 默认 locale 解码
        （errors="replace"），与 live 本地读 `read_text(encoding="utf-8")` 不对称（pre-existing
        惯例）；非 UTF-8 locale + 归档报告含 BOM/非 ASCII frontmatter 时，git-show 文本解码差异
        可能令 parse 判 false absent → 归档回退 inline（方向安全：假阴漏判，非假阳假过）。仅登记，
        不改 subprocess（pre-existing，超本 change scope）。
"""  # [impl-review-fix]
# [T74/grill-amendment Q2] 已知不覆盖（登记越权盲区，非正常可达）：
#   「首行 --- 无闭合 × 归档 verify-report 正文独占一行 inline PASS 锚」杂交形态——
#   改判 absent 后 archived_verify_state 会回退 inline 扫到独占行 PASS → 判 pass。
#   但此形态**无 producer 产出**：目标态 producer 写 frontmatter 不写 inline，旧 producer
#   首行恒 '#' 非 '---'。须手工伪造归档才能构造 = 显式越权（git 留痕可审计，adr/0008/0011）。
#   目标态论证：迁移期评估安全锚 producer 契约而非现存语料快照（见 design ADR-4）。
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
    # [mlh-p5 Task3 D4/G2] frontmatter 优先（新归档），共用同一严格 helper（防漂移）——
    # 与 live 侧的区别：live 坏→UNKNOWN(6) 停；归档坏→fail-safe 'none'（不 emit、不 exit，
    # 归档不可变、无人可修，只能保守判无 verify pass，不回退 inline 掩盖假 SHIPPED）。
    state, err = parse_ship_gate_frontmatter(out)
    if err is not None:
        return "none"                        # 坏 frontmatter → fail-safe（不回退 inline 掩盖）
    if "verify" in state:                     # Q4：frontmatter 有效即采信，不再交叉扫 inline
        return "pass" if state["verify"] == "PASS" else "none"
    # absent（迁移前旧归档，无 ship-gate frontmatter 键）→ 回退旧 inline 读半场，永久保留
    hits, unbalanced = _line_scoped_hits(out, [ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL])  # [ADR-4] 行级，非子串
    if unbalanced:   # [ADR-5] 保守：未闭合 fence 不判 SHIPPED
        return "none"
    has_pass, has_fail = ANCHOR_VERIFY_PASS in hits, ANCHOR_VERIFY_FAIL in hits
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


def _line_scoped_hits(text, candidates):
    """文本级行锚定核心（零正则）：候选须独占一行（strip 后等值），忽略 fenced code block。
    返回 (hits[按 candidates 原序去重], unbalanced[EOF 时围栏未闭合])。
    [impl-review-fix FIX-5] 现役唯一调用方 = archived_verify_state（归档 dual-read 兜底旧 inline）；
    anchors_in / pick_exclusive 已从 live decide() 退役（Task6 迁 frontmatter 后），现仅 test-
    referenced 孤儿，不再是本核心的运行时共用方。fence 翻转口径同 _parse_plan
    （line.lstrip().startswith("```")）。"""
    cand = set(candidates)
    hit = set()
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        s = line.strip()
        if s in cand:
            hit.add(s)
    return [a for a in candidates if a in hit], in_fence


# [mlh-p5] frontmatter 状态解析（手写 stdlib，不 import yaml——保零依赖不变量）。
# live 读与归档 git-show 文本读共用此单一核心（防漂移，D4）。
FIELD_ENUMS = {
    "design_approved": (True, False),   # bool
    "verify": ("PASS", "FAIL"),
    "code_review": ("pass", "blocked"),
}


def parse_ship_gate_frontmatter(text):
    """解析报告 frontmatter 的 ship-gate 状态。返回 (state, error)：
      state: {field: value}（已枚举校验）；{} = absent（无 frontmatter / 无 ship-gate 键）
      error: None（干净）或 (field|'frontmatter', category)
             category ∈ duplicate-key|out-of-domain|bad-type|tab-indent
    D2 只认文件首块：首行须 '---'（去 BOM）；正文 --- 横线不参与。
    D3 坏≠无：absent(state={},error=None) vs 坏(error!=None) 由调用方分流退出码。
    D5 重复键→duplicate-key（枚举全部同名键计数，非取最后一个）。
    [impl-review-fix FIX-1] 只认 ship-gate 直接子键（首个非空子行的缩进层级）；深于该层级的行
    是嵌套子树，跳过不扫（不参与 FIELD_ENUMS 匹配）——杜绝 `note:` 下嵌套 design_approved 假过门。
    [impl-review-fix FIX-2] 顶层 `ship-gate:` 后带非空内容（内联标量/inline map）→ bad-type（非
    absent），防归档路径把它当 absent 回退 inline 造成假 SHIPPED。
    [impl-review-fix FIX-3] 支持 YAML `#` 注释：块内独占注释行整行跳过；值行尾部 ` #` 注释剥离。"""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.splitlines()               # 统一 \r\n/\n（值不残留 \r）
    if not lines or lines[0].strip() != "---":
        return {}, None                     # absent：无首块 frontmatter
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        # [T74] 首行 --- 但全文无第二个 --- → 首块不闭合 → 不构成 frontmatter block，
        # 首行 --- 视作正文/markdown 水平线 → absent（走既有无锚语义），非坏、非 fail-closed。
        # 与「D2 只认文件首块」定义统一：无闭合 --- 不成块。
        return {}, None
    block = lines[1:end]
    # 找顶层 ship-gate: 键，统计出现次数（重复→坏）。
    # [impl-review-fix FIX-2/FIX-4] 顶层探测识别**任何以 ship-gate: 起始的行**（不再只认整行
    # == "ship-gate:" 的规范空 map 头）：tab 缩进 → tab-indent 坏（FIX-4，与字段行 tab 检测对称）；
    # 空格缩进 = 嵌套键（非顶层），忽略；0 缩进 = 真顶层键——若其后 rstrip 还有非空内容（内联标量/
    # inline map，如 `ship-gate: []`/`ship-gate: true`）→ bad-type（FIX-2，杜绝归档误回退 inline）。
    top_hdrs = []                            # [(index, line)]，0 缩进的顶层 ship-gate: 行
    for i, ln in enumerate(block):
        if not ln.lstrip().startswith("ship-gate:"):
            continue
        indent_ws = ln[:len(ln) - len(ln.lstrip())]
        if "\t" in indent_ws:
            return {}, ("frontmatter", "tab-indent")   # FIX-4：tab 缩进顶层键
        if indent_ws:
            continue                         # 空格缩进 = 嵌套键，非顶层，忽略
        top_hdrs.append((i, ln))
    if len(top_hdrs) == 0:
        return {}, None                     # absent：有 frontmatter 但无 ship-gate 键
    if len(top_hdrs) > 1:
        return {}, ("ship-gate", "duplicate-key")
    header_idx, header = top_hdrs[0]
    if header.rstrip() != "ship-gate:":     # FIX-2：非规范空 map 头（带内联标量值）→ 坏
        return {}, ("ship-gate", "bad-type")
    # 收集 ship-gate: 下方缩进的 field: value（下一个 0 缩进非空行为界）。
    # [impl-review-fix FIX-1] 只认 ship-gate 直接子键：首个非空子行的缩进 = 直接子键层级；
    # 缩进深于该层级的行是嵌套子树，跳过不扫（不参与 FIELD_ENUMS 匹配，杜绝嵌套字段假过门）。
    start = header_idx + 1
    state, seen = {}, {}
    direct_indent = None
    for ln in block[start:]:
        if ln.strip() == "":
            continue
        if not ln[:1].isspace():
            break                           # 回到 0 缩进 = ship-gate 块结束
        # [impl-review-fix FIX-3a] 块内独占注释行（strip 后以 # 起始）跳过——放在 tab/冒号检测之前
        if ln.strip().startswith("#"):
            continue
        indent_ws = ln[:len(ln) - len(ln.lstrip())]
        indent = len(indent_ws)
        if direct_indent is None:
            direct_indent = indent          # 首个非空非注释子行定直接子键层级
        if indent > direct_indent:
            continue                         # FIX-1：嵌套子树（深于直接层级），跳过不扫
        if "\t" in indent_ws:
            return {}, ("frontmatter", "tab-indent")
        body = ln.strip()
        if ":" not in body:
            return {}, ("frontmatter", "bad-type")
        field, _, raw = body.partition(":")
        field = field.strip()
        # [impl-review-fix FIX-3b] 值行尾部 # 注释在枚举比对前剥离（enum 值均不含 #，安全）
        raw = raw.split(" #", 1)[0].strip()
        if field not in FIELD_ENUMS:
            continue                         # 非本 schema 字段（外来 metadata），忽略
        seen[field] = seen.get(field, 0) + 1
        if seen[field] > 1:
            return {}, (field, "duplicate-key")
        val = _coerce_ship_gate_value(field, raw)
        if val is _BAD_TYPE:
            return {}, (field, "bad-type")
        if val not in FIELD_ENUMS[field]:
            return {}, (field, "out-of-domain")
        state[field] = val
    return state, None


_BAD_TYPE = object()


def _coerce_ship_gate_value(field, raw):
    if field == "design_approved":
        if raw == "true":
            return True
        if raw == "false":
            return False
        return _BAD_TYPE                     # yes/1/True 等非规范 bool → 坏
    return raw                               # verify/code_review：字符串，交枚举校验


def anchors_in(path, candidates):
    """行级字面查找（零正则）：机判锚 MUST 独占一行（strip 后等值）、忽略 ``` 代码块——
    描述性提及/文档示例不触发〔B4/ADR-1/2〕。文件不存在返回 []。"""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")  # 非 UTF-8 防崩
    return _line_scoped_hits(text, candidates)[0]


# [T26/SR-1；mlh-p5 Task6 D11] 熔断状态集合判据：判据 = 该步 ship-gate **frontmatter 状态集合**
# 是否变化（非 HEAD/mtime、非 inline 锚行）。两个纯函数/无状态 helper：不落地文件、无副作用，
# 供上层熔断逻辑（人工/skill 层，非本文件）对比"上一次快照"与"本次重跑"的状态集，判有无实质进展。
def anchor_set(text):
    """返回该报告 frontmatter 的 ship-gate 状态集合（frozenset of (field, value) 对）。
    [mlh-p5 Task6 D11] 迁 frontmatter：复用 parse_ship_gate_frontmatter 提取状态 dict（与 live
    读点单核一致，防漂移），键值对集合作快照；坏 frontmatter → 空集（保守，无净变化倾向判无进展）。
    inline 锚已随 live 读点退役，不再参与熔断进展判据（正文残留 inline 锚被忽略）。"""
    state, err = parse_ship_gate_frontmatter(text)
    if err is not None:
        return frozenset()
    return frozenset(state.items())


def breaker_no_progress(before, after):
    """熔断纯函数：before/after 为两次 anchor_set() 快照（frozenset）。集合无净变化
    （before == after）→ True=无进展，判熔断。fail-safe：**任一快照缺失**（before 或
    after is None，如 context 压缩丢记录、或重跑后报告不存在/不可读）→ 保守返 True（宁可
    误判无进展停上抛，不放行假免疫）〔impl-review-fix CR-2：原只护 before，after=None 时对
    非空 before 返 False=假放行，正是要防的漏网〕。HEAD 移动/mtime 变化 MUST NOT 作为免疫
    信号——本函数不接收、不比较它们。"""
    if before is None or after is None:
        return True
    return before == after


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
    """互斥锚对解析：两者并存 / 未闭合 fence → UNKNOWN（不猜）。返回 'pos'/'neg'/None。"""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    found, unbalanced = _line_scoped_hits(text, [positive, negative])
    if unbalanced:   # [ADR-5] 未闭合 fence 可吞负锚 → 保守不判 pass
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             f"{label} 报告含未闭合 fence（``` 悬空），无法可靠判定互斥锚，请人工修复围栏后重试")
    if positive in found and negative in found:
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             f"{label} 报告并存冲突锚行（{positive} 与 {negative}），请人工裁决删除其一")
    if positive in found:
        return "pos"
    if negative in found:
        return "neg"
    return None


# [mlh-p5 Task2/D3；Task6 退役 live inline] live 读点分流：frontmatter 有效→state；坏→UNKNOWN(6)；
# absent→None 交调用方走既有无锚语义（**不再回退 inline**）。坏 frontmatter 的退出码映射集中于此
# （越域/重复键/坏语法/类型不符→UNKNOWN，歧义须人裁、防 exit0 重跑死循环）。
def _fail_closed_on_bad(err, label):
    field, cat = err
    emit("UNKNOWN", EXIT_UNKNOWN, None,
         f"{label} frontmatter 坏（字段={field} 类别={cat}）→ fail-closed 无有效状态，请人工修复")  # D12 reason 点名 field+category


def live_ship_gate_state(path, label):
    """live 读某报告的 ship-gate 状态 dict。frontmatter 有效→state；坏→UNKNOWN(6) 停（不回退）；
    absent（无 frontmatter / 无 ship-gate 键）→返回 None，调用方走既有无锚语义（Task6 退役 live
    inline 回退，live 只读 frontmatter）。与归档 git-show 文本读共用 parse_ship_gate_frontmatter
    单核（防漂移，D4；归档侧仍 dual-read inline，live 侧不）。"""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    state, err = parse_ship_gate_frontmatter(text)
    if err is not None:
        _fail_closed_on_bad(err, label)      # 坏永不回退，直接 fail-closed（emit 不返回）
    if state:
        return state                         # 有效键
    return None                              # absent → 调用方回退 inline


def _unclosed_frontmatter_hint(path):
    """[T74 1.5/spec-review Q1=A；design ADR-5] live 读点上层**独立轻量结构诊断**：
    报告首行为 '---' 但全文无第二个 '---'（首块不闭合，parse 判 absent）→ 返回结构提示串
    供 emit reason 追加。纯诊断——MUST NOT 改 parse 返回签名、MUST NOT 改 verdict/退出码、
    MUST NOT 探测意图（≠candidate②）。文件不存在 / 首行非 '---' / 已闭合 → 返回 ''（无提示）。
    与 parse 首块判据同口径（去 BOM、strip 后等值、只认第 2 行起首个 '---'），防诊断与解析漂移。"""
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    if any(lines[i].strip() == "---" for i in range(1, len(lines))):
        return ""                            # 已闭合 → 非本诊断场景（坏/有效由 parse 处置）
    return "（结构提示：首行为 `---` 但未见闭合 `---`，已按正文处理；欲声明状态请补闭合行）"


TASK_TITLE_RE = re.compile(r"^### Task (\d+):", re.M)   # 计数用；锚行才禁正则
# [T36/SR-4] canonical shape 权威源 = 本 TAG_RE。**parser 契约实际只执行到 `task<N>-` 前缀**
# （命名空间组可选、向后兼容裸 task<N>- 旧格式）；`<slug>` 是**建议性**约定（可读性/去重），
# TAG_RE 不校验其存在或形状〔impl-review-fix CR-3：勿把 <slug> 读成 parser 强制契约〕。
# workflow.md 的格式串样例、sdflow-ship/SKILL.md
# 的引用式派发句均须与此正则保持一致；test_producer_parser_contract 钉死 producer(checkpoint-commit.sh
# 落的标签串) ↔ parser(本 TAG_RE) 的一致性。checkpoint-commit.sh 本身 format-agnostic（只裹
# `checkpoint($step)`，不校验形状），**非格式源**。
# SR-4 checklist：改此正则前先 grep workflow.md 里的格式串样例是否需要同步更新。
TAG_RE = re.compile(r"checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-")  # [T32] 可选命名空间组


def tg02_hit(cdir):
    p = cdir / "proposal.md"
    if not p.is_file():
        return False
    text = p.read_text(encoding="utf-8", errors="replace")  # 非 UTF-8 防崩
    # [ADR-6] 声明式匹配（全角括号头注 〔TG-NN：，ff 强制格式），非裸子串——
    # 描述性提及/代码引用/否定句(TG-01/02/03)不触发假 RUN_SOP（dogfood B4 类）
    # [ADR-6/A3] 只在头部声明区（开头→首个 "## " 前）找声明式 〔TG-02——
    # 正文对 TG-02 的文档性提及不触发假 RUN_SOP（dogfood：讨论 tg02 的 proposal 正文含示例声明串）
    # [impl-review-fix] 头部声明区检测须 fence-aware（对齐 _line_scoped_hits/_parse_plan 口径）+ 声明行匹配：
    # ①fenced 块（```）内的 `## ` 不算头部边界、内容不计（对抗镜1 假阴/假阳）；
    # ②只认 strip 后以「〔TG」起始的声明行（排除「技术栈…均不命中」描述行/反引号提及，codex OV-code-2）。
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("## "):   # 真 H2 标题（非 fence 内）= 头部区结束
            break
        s = line.strip()
        if s.startswith("〔TG") and "〔TG-02" in s:   # 声明行（非描述散文）且含 TG-02
            return True
    return False


def plan_task_ids(plan):
    # [spec-review-amendment B4/D5] plan 声明的任务号集（去重）。完成判据按**集合归属**
    # （plan_ids ⊆ done_ids）而非基数（len(done) < n）——否则计划外任务号（遗留/错号/
    # merge 内提交的 checkpoint(task9-)）会顶替缺失的计划内号让基数达标而假齐（假✅）。
    # [impl-review-fix CR-F2] fence-aware：fenced 代码块内的 `### Task N:` 示例标题不算任务
    # （与复选框同 fence 口径，经共享 _parse_plan——前向引用，运行时已定义，模块级合法）。
    text = plan.read_text(encoding="utf-8", errors="replace")
    return set(_parse_plan(text)[0])


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


# [ship-gate-hardening-2 T34 + impl-review-fix CR-F1/F2] 复选框辅通道按 Task 分段绑定。
# 旧全局 checkboxes_all 全文子串判"无任何 - [ ]"即放行所有 task——无复选框的 task（仅散文）
# 会被全局放行（假✅）。CR-F1/F2〔代码审对抗镜+outside-voice 两声共识〕：Task 标题与复选框
# MUST 共享**同一个全文 fence 状态**（单遍 _parse_plan）——旧版"先切段、每段各自重置 in_fence"
# 会让悬空/跨段围栏泄漏（段内未闭合 ``` 吞掉真实未勾项 → 假✅）、且标题正则对围栏无感知
# （fenced 示例标题被当真 task/误判重号）。二者统一到一次带 fence 状态的整文扫描。
CHECKBOX_RE = re.compile(r"^\s*-\s+\[([ xX])\]")   # 行锚定复选框（非全文子串）


def _parse_plan(text):
    # [T34/impl-review-fix] fence-aware 单遍解析（Task 标题与复选框统一围栏口径）。
    # fenced code block（``` 围栏）内的行对 Task 标题与复选框**均不可见**（CR-F1/F2）。
    # 返回 (task_order[出现序,含重号], boxes_by_task{num:[checked_bool]}, any_checkbox, unbalanced)。
    # unbalanced=True 表示 EOF 时围栏未闭合（悬空 ```）——plan 无法可靠解析（CR-F1）。
    task_order = []
    boxes_by_task = {}
    any_checkbox = False
    cur = None
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        tm = TASK_TITLE_RE.match(line)
        if tm:
            cur = tm.group(1)
            task_order.append(cur)
            boxes_by_task.setdefault(cur, [])
            continue
        cm = CHECKBOX_RE.match(line)
        if cm:
            any_checkbox = True
            if cur is not None:   # 前言段（首个 Task 前）的框不归任何 task，忽略
                boxes_by_task[cur].append(cm.group(1) in ("x", "X"))
    return task_order, boxes_by_task, any_checkbox, in_fence


def checkbox_done_ids(plan):
    # [T34] 复选框完成集：某 task 号计入 当且仅当其段内有复选框且全部已勾（行锚定 + 忽略代码块）。
    text = plan.read_text(encoding="utf-8", errors="replace")
    _, boxes, _, _ = _parse_plan(text)
    return {num for num, states in boxes.items() if states and all(states)}


def plan_has_any_checkbox(plan):
    # [T34] 全 plan 有无（行锚定、非代码块内）复选框——供"双通道皆不可判"分支用。
    text = plan.read_text(encoding="utf-8", errors="replace")
    return _parse_plan(text)[2]


def plan_has_duplicate_task(plan):
    # [T34/codex#3+对抗B-1c] 重号 `### Task <n>:` 检测（fence-aware）：set 折叠重号会掩盖
    # "一段全勾一段未勾"的假✅；fenced 里的示例标题不算（CR-F2）。
    text = plan.read_text(encoding="utf-8", errors="replace")
    order = _parse_plan(text)[0]
    return len(order) != len(set(order))


def plan_unbalanced_fence(plan):
    # [impl-review-fix CR-F1] EOF 时围栏未闭合（悬空 ```）→ 悬空围栏吞真实项 → fail-safe UNKNOWN。
    text = plan.read_text(encoding="utf-8", errors="replace")
    return _parse_plan(text)[3]


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
    # [mlh-p5 Task6 D1] live 只读 frontmatter（inline 回退已退役）：design_approved 优先；
    # absent（无 frontmatter / 无 ship-gate 键）→ sr_state=None → design_ok=False → REFUSE_START
    # （既有无锚语义，不回退 inline）；坏 frontmatter → live_ship_gate_state 内 UNKNOWN(6) 已 emit。
    report = cdir / "spec-review-report.md"
    sr_state = live_ship_gate_state(report, "spec-review")   # 坏→UNKNOWN(6) 已 emit；absent→None
    design_ok = sr_state is not None and sr_state.get("design_approved") is True
    if not design_ok:
        emit("REFUSE_START", EXIT_REFUSE, None,
             "未过设计门：spec-review-report.md 缺失或无 design-approved 锚行；"
             "先完成设计门；若拍板已发生请人工补锚（显式越权留痕）"
             + _unclosed_frontmatter_hint(report))
    design_stale, _design_fresh = is_stale(
        root, str(report.relative_to(root)), "design", change)
    if design_stale:
        emit("REFUSE_START", EXIT_REFUSE, None,
             "design-approved 之后四件套被改动 → 拍板失鲜，改设计须重审"
             "（重跑 sdflow-spec-review 后重新拍板补锚）")
    # ── verify 冲突锚早检（坏 frontmatter → UNKNOWN，保步序早停）──
    # [mlh-p5 Task6 D1] live 只读 frontmatter（inline 回退已退役）：坏 frontmatter（含重复
    # verify 键=冲突的等价形态 duplicate-key）→ live_ship_gate_state 内 UNKNOWN(6) emit 早停；
    # 有效单值 / absent 不早停（absent = 无锚语义，留待 step9 判 STEP_IN_PROGRESS）。此调用仅
    # 为副作用（触发坏→UNKNOWN 早检以保步序），返回值有意丢弃。
    vfile = cdir / "verify-report.md"
    if vfile.is_file():
        live_ship_gate_state(vfile, "verify")   # 坏→UNKNOWN(6) 早停；live 只读 frontmatter
    # ── step 5.5：条件步（TG-02 声明式 〔TG-02 匹配，非裸子串；细判归模型）──
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
    # [impl-review-fix CR-F1] 未闭合 fenced code block（悬空 ```）→ 悬空围栏会吞掉真实
    # 未勾项与 Task 标题（假✅/漏 task）→ plan 无法可靠解析 → fail-safe UNKNOWN（先于其余判据）。
    if plan_unbalanced_fence(plan):
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             "plan 有未闭合的 fenced code block(```)，悬空围栏吞真实项，完成判据无法可靠解析")
    plan_ids = plan_task_ids(plan)
    n = len(plan_ids)
    if n == 0:
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             "plan 无 '### Task <n>:' 标题（上游模板漂移？），完成判据不能")
    # [ship-gate-hardening-2 T34] 重号 Task 段 → UNKNOWN（set 折叠掩盖一段全勾一段未勾的假✅）
    if plan_has_duplicate_task(plan):
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             "plan 出现重号 '### Task <n>:' 段（手改/复制粘贴），完成判据不可判"
             "——重号折叠会掩盖某段未完成的假✅")
    sha = plan_first_sha(root, str(plan.relative_to(root)))
    # [ship-gate-hardening-2 T34] 两通道完成集并集：checkpoint 主锚 ∪ 复选框分段辅通道
    checkpoint_done = done_task_ids(root, sha, change) if sha else set()
    checkbox_done = checkbox_done_ids(plan)   # 按 Task 分段绑定（非全局全勾放行）
    done = checkpoint_done | checkbox_done
    done_in_plan = done & plan_ids            # [spec-review-amendment B4] 只认计划内号
    if plan_ids - done:                       # 计划内有未完成号 → 未齐（集合归属,非基数）
        # 双通道皆不可判：plan 未提交（checkpoint 空）且全 plan 无复选框（辅通道空判）
        if not sha and not plan_has_any_checkbox(plan):
            emit("UNKNOWN", EXIT_UNKNOWN, None, "plan 未提交且无复选框，双通道皆不可判")
        emit("CONTINUE_IMPL", EXIT_OK, "subagent-dev",
             f"实现进度 {len(done_in_plan)}/{n}（窗口 [{sha[:7] or '-'}, HEAD] 闭区间，集合归属）",
             done_tasks=sorted(done_in_plan, key=int))
    # ── step 8：code-review 门 ─────────────────────────────────
    cr = cdir / "code-review-report.md"
    if not cr.is_file():
        emit("RUN_CODE_REVIEW", EXIT_OK, "sdflow-code-review", "实现完成，进入代码审")
    # [mlh-p5 Task6 D1] live 只读 frontmatter（inline 回退已退役）：code_review 优先
    # （pass→'pos'/blocked→'neg'）；坏→UNKNOWN(6) 已 emit；absent→None→STEP_IN_PROGRESS（无锚语义）。
    cr_front = live_ship_gate_state(cr, "code_review")   # [impl-review-fix FIX-5] label 用下划线，与字段名一致
    if cr_front is not None:
        cv = cr_front.get("code_review")
        cr_state = "pos" if cv == "pass" else "neg" if cv == "blocked" else None
    else:
        cr_state = None                          # absent → 无锚 → STEP_IN_PROGRESS
    if cr_state == "neg":
        emit("BLOCKED_UPSTREAM", EXIT_BLOCKED, None,
             "code-review 判 blocked：先解 blocker（见报告），gate 不蒙头跑")
    if cr_state is None:
        emit("STEP_IN_PROGRESS", EXIT_OK, "sdflow-code-review",
             "code-review-report.md 在但无锚行 → 该步进行中，重跑"
             + _unclosed_frontmatter_hint(cr))
    cr_stale, cr_fresh = is_stale(root, str(cr.relative_to(root)), "code", change)
    cr_stale_note = None
    if cr_stale:
        # 陈旧判定优先级须让位于「verify=FAIL 之后修代码重验」链路：verify 已判 FAIL
        # 时不要求先重跑 code-review（否则陈旧 FAIL 卡死），留给 step9 判 RERUN_STALE。
        # [mlh-p5 Task6 D1] live 只读 frontmatter（inline 回退已退役）：frontmatter verify==FAIL
        # 优先；坏→UNKNOWN(6) 已在上方 verify 早检 emit（此处同文件不会再遇坏）；absent→非 FAIL。
        vf_peek = cdir / "verify-report.md"
        vp_front = live_ship_gate_state(vf_peek, "verify")
        verify_already_failed = vp_front is not None and vp_front.get("verify") == "FAIL"
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
    # [mlh-p5 Task6 D1] live 只读 frontmatter（inline 回退已退役）：verify 优先（PASS→'pos'/
    # FAIL→'neg'）；坏→UNKNOWN(6) 已在 verify 早检 emit；absent→None→STEP_IN_PROGRESS（无锚语义）。
    vf_front = live_ship_gate_state(vf, "verify")
    if vf_front is not None:
        vv = vf_front.get("verify")
        v_state = "pos" if vv == "PASS" else "neg" if vv == "FAIL" else None
    else:
        v_state = None                           # absent → 无锚 → STEP_IN_PROGRESS
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
             "verify-report.md 在但无锚行 → 该步进行中，重跑"
             + _unclosed_frontmatter_hint(vf))
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
