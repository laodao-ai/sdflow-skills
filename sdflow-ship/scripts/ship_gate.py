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
        例外一〔B2/BR-7〕: subject 精确 `checkpoint(impl-review)` 或 `checkpoint(impl-review):…`
        的提交豁免（阶段三合法尾流修订，code-review 回填措辞/勾选），只认 subject 不认 hunk；
        例外二〔fix-design-gate-freshness-proxy · 内容判据〕: **纯勾选框翻转**豁免——
        任何 subject 的提交，若帧内落在监视集的路径**恰为** {tasks.md}、变更形态是普通
        内容修改（非 A/D/R/C/T、无 mode 变更）、且勾选框标记归一化后**逐行等值**，则不失鲜。
        归一化只认行首 task-list 标记（CHECKBOX_RE_PATTERN），且 fenced code block /
        缩进代码块（缩进 ≥4 列）/ HTML 注释块内的行一律不参与。merge 提交须**对每个
        parent** 都成立。任何读不到 / 形态不合格 / 围栏未闭合 ⇒ 一律回落判失鲜。
        帧枚举协议〔impl-review-fix F1〕= `git diff-tree -m -r --raw --no-renames -z --root`
        （merge 逐 parent、改名分解 A+D、NUL 原始路径）；枚举失败 ⇒ 判失鲜（F2）
    verify / code-review: 其后触及 openspec/ 之外路径的提交 → 陈旧
        （verify=FAIL 陈旧优先于 code-review 陈旧判定，保重验不因陈旧 CR 卡死）
    报告从未提交: fresh（freshness=uncommitted，人机同权）

已知不覆盖（接受并记录）:
    openspec/workflow/ 规则漂移不触发陈旧；rebase/--amend 历史改写可伪造保鲜；
    提交遍历不加 --first-parent（merge 内部提交逐一枚举）；
        〔impl-review-fix F1，已修〕原「evil-merge 漏检」（仅存在于 merge commit 自身、
        两 parent 都没碰过的改动，因 --name-only 不产 merge diff）已随 design 域枚举协议
        换成 `diff-tree -m -r --raw --no-renames -z --root` 修复；**code 域仍走 --name-only**
        （本轮判据逐字不动），故 code 域的 evil-merge 漏检**依旧存在**，登记待后续；
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
    〔gate-anchor-line-scoped〕机判锚 MUST 独占一行（strip 后行级等值 + 忽略 ``` 代码块内）——
        `archived_verify_state`（git-show 文本，归档 dual-read 现役唯一调用方）经由 `_line_scoped_hits`
        核心判定，杜绝子串/行级两路径各判各的漂移〔ADR-1/2/4；T75 起 live 侧 inline 读半场已退役〕；
    〔ADR-5〕互斥锚对（verify PASS/FAIL）若遇未闭合 ``` fence 吞掉负锚，
        不得因此误判 pass——保守判 none（archived，
        archived_verify_state），宁可判定不能也不假阳；
    〔ADR-6〕tg02_hit 触发检测 = 声明式匹配全角括号头注 `〔TG-02`（ff 强制格式），非裸子串——
        描述性提及/代码引用/否定句（如提及 "TG-01/02/03"）不再误触发 RUN_SOP；
    多行 HTML 注释内嵌锚不解析：不判断锚是否落在更大的 `<!-- ... -->` 多行注释块「内部」被
        整体注释掉——模板锚本身即单行注释，独占一行等值已足；多行嵌套锚属人为构造，归
        「显式越权同权级」（git 留痕可审计）；
    〔fix1 Important-1〕fenced code block 的围栏识别收敛到**单一源** `fence_delim`（str）+
        `fence_delim_bytes`（bytes 委派），口径按 CommonMark 的**有界**词法写全：开启符 =
        连续 ≥3 个同种 `` ` `` 或 `~`；闭合符须**同种**且长度 ≥ 开启符、其后仅空白。故
        `~~~` 块与四 backtick 块内的内容一律不可见，`~~~` 不能被 ``` 关掉（反之亦然）。
        MUST NOT 由此扩到 markdown 其它结构（表格/嵌套列表/引用块）——那是无界面，禁手搓。
    〔impl-review-fix F3〕勾选框归一化另加两道**超集**闸门：行首缩进 ≥4 列（CommonMark
        缩进代码块的必要条件）与 HTML 注释块（`<!--`…`-->`）内的行不参与归一化。取超集
        是因为 CommonMark 缩进代码块的精确判定依赖段落/列表上下文（无界，禁手搓）；
        代价 = 缩进 ≥4 列的**真嵌套任务项**翻转也判失鲜（假失鲜，保守方向，接受）。
        本闸门只加在 `_normalize_checkbox_lines`（豁免面），MUST NOT 顺手推到 `_parse_plan`
        / `tg02_hit` / `_line_scoped_hits`——那三处的安全方向各不相同，改动须各自论证。
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

# [T75] design/code-review inline 锚常量已随 Task6 live inline 读半场退役而删除；
# 仅 verify 锚保留——archived_verify_state 的归档 dual-read 兜底旧 inline 现役唯一在用。
ANCHOR_VERIFY_PASS = "<!-- ship-gate: verify=PASS -->"
ANCHOR_VERIFY_FAIL = "<!-- ship-gate: verify=FAIL -->"
ALL_ANCHORS = [ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL]

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
    # [impl-review-fix] tri-state（CV-1/HRTG-c2 三声）：D3 短路须与 active 侧冲突锚判 UNKNOWN
    # 同等互斥——PASS+FAIL 并存 = 'conflict'（→UNKNOWN），非只查 PASS in。
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


def run_git_bytes(root, *args):
    """保真读取：返回 (returncode, stdout **原始字节**)。

    [fix-design-gate-freshness-proxy Task1 · tasks 1.1d] MUST NOT 复用 run_git/run_git_rc——
    那条路径 text=True + errors="replace" + .strip()，四者各自可造假等值：
    吞首尾空白、吞末尾换行、CRLF↔LF 不可分辨、非 UTF-8 字节被替换成 U+FFFD 后两版趋同。
    本函数只做 subprocess 原样取字节，解码与归一化留给调用方按判据自行决定。
    """
    r = subprocess.run(["git", "-C", str(root), *_GIT_HARDEN, *args], capture_output=True)
    return r.returncode, r.stdout


def design_watched_subs(frame_files, base):
    """帧内**落在 design 域监视集内**的触及路径集（相对 change 目录）。

    [Task1] 这与「该提交的完整文件列表」是两个不同的量：checkpoint 走 `git add -A`，
    真实提交必然打包源码；按整 commit 求值 ⇒ 任何以此为前提的判据永不触发。
    """
    subs = set()
    for f in frame_files:
        if not f or not f.startswith(base):
            continue
        sub = f[len(base):]
        if sub in DESIGN_WATCHED_NAMES or sub.startswith("specs/"):
            subs.add(sub)
    return subs


def frame_touched_paths(root, sha):
    """该提交触及的路径列表；**读不到/形态看不清 → None**（调用方 MUST 保守判失鲜）。

    [impl-review-fix F1] 取代旧的 `git log --name-only`。旧协议有三个 fail-open 洞，
    同属一个面（枚举协议），故一次扫全：

      F1-a **merge 提交恒空**：`git log --name-only` 不带 -m/--cc 时对 merge commit
        **不输出任何文件** ⇒ 上游 `if not subs: continue` 在触及豁免判据**之前**就跳过
        整帧 ⇒ evil-merge（改动只存在于 merge 自身 resolve 出的树、两 parent 都没碰）
        对 design 域整体判 fresh。且 Task1 的逐 parent 校验在生产路径上成了死代码。
      F1-b **rename 检测吞源路径**：默认开 rename 检测，`git mv tasks.md x.md` 只输出
        目标路径 ⇒ 监视集看不到源 `tasks.md` ⇒ 跳过整帧判 fresh（直接违反本 change 的
        delta spec「`git mv` 迁走 ⇒ 失鲜」）。
      F1-c **文本行协议承载文件名**：含换行/Tab 的路径按行切会拆碎、且被 C-quote 包裹
        ⇒ 逃出 `startswith(base)` 监视集。

    ⇒ 协议改为 `git diff-tree -m -r --raw --no-renames -z --root`：
      `-m`          merge 输出**相对每个 parent** 的 diff（补 F1-a）；
      `--no-renames` 改名分解成 A+D，源路径与目标路径**都**进枚举（补 F1-b）；
      `-z`          NUL 分隔的原始路径，零引号零转义（补 F1-c）；
      `--root`      根提交也能枚举出文件（否则空集 ⇒ 又一处静默跳过）。

    🔴 **与 BR-6 护栏的关系**（防后人误读）：BR-6 禁的是 `--no-merges` / `--first-parent`
    ——那两个开关会**少枚举提交**。`-m` 是**多输出** merge 的 per-parent diff，不删任何
    提交、不改变遍历的提交集合，与 BR-6「merge 内部提交逐一枚举不漏检」方向一致。
    """
    rc, out = run_git_rc(root, "diff-tree", "-m", "-r", "--raw", "--no-renames",
                         "-z", "--no-commit-id", "--root", sha)
    if rc != 0:
        return None
    toks = out.split("\0")
    paths, i = [], 0
    while i < len(toks):
        meta = toks[i]
        if not meta:
            i += 1                         # 末尾 NUL 切出的空 token
            continue
        if not meta.startswith(":") or i + 1 >= len(toks):
            return None                    # 协议外形态 ⇒ 看不清 ⇒ 保守
        paths.append(toks[i + 1])
        i += 2
    return paths


def commit_parents(root, sha):
    """该提交的 parent sha 列表。根提交 → []；解析失败 → None。

    [Task1 · BR-6 护栏] merge 提交下「前版」相对**每个** parent 各自定义——
    调用方须逐 parent 求值，MUST NOT 只看 first parent。
    """
    rc, out = run_git_rc(root, "rev-list", "--parents", "-n", "1", sha)
    if rc != 0 or not out:
        return None
    return out.split()[1:]


def _plain_modification_from_raw(line):
    """`git diff --raw` 单行 → 该行是否表示**普通内容修改**。纯函数（可对合成行直接测）。

    行形：`:<srcmode> <dstmode> <srcsha> <dstsha> <status>\\t<path>`
    [Task1] 新建(A)/删除(D)/改名(R)/复制(C)/类型变更(T)/仅权限位(mode 变) 一律 False——
    此类形态下前后两版 blob 字节可能**完全相同**（chmod、regular↔symlink），拿字节等值
    当「没实质改动」会放行真实的状态位变更。
    """
    if not line.startswith(":"):
        return False                       # 非 raw 行形 ⇒ 下面的定位全不可信，保守
    fields = line.split("\t", 1)[0].split()
    if len(fields) < 5:
        return False
    src_mode, dst_mode, status = fields[0][1:], fields[1], fields[4]
    return status == "M" and src_mode == dst_mode


def _parent_path_status(root, parent, sha, path):
    """该提交相对某 parent 对 path 的变更形态。四态：

        "unchanged" — 该 parent 侧与本提交在此路径上**逐字节同一** blob（无改动可审）
        "plain"     — 普通内容修改（status=M 且 mode 不变）
        "unfit"     — 形态不合格（A/D/R/C/T 或仅权限位变更）
        "error"     — git 读取失败 ⇒ 看不清

    [impl-review-fix F1] 从旧的二值 `_plain_content_modification` 拆开。旧版把
    "unchanged" 与 "unfit"/"error" 一起折叠成 False ⇒ 一旦 merge 帧被真正枚举出来
    （F1-a 修复后），「side 分支改了 tasks.md、main 侧没改」这类**普通 merge** 会因
    「相对 side parent 无改动」被误判 shape-unfit ⇒ 假失鲜。unchanged 的正确语义 =
    该 parent 侧**没有引入任何设计改动**，与豁免判定无关，跳过即可。

    --no-renames：让改名分解成 A+D，不依赖 diff.renames 的仓库级 config（确定性）。
    """
    rc, out = run_git_rc(root, "diff", "--raw", "--no-renames", parent, sha, "--", path)
    if rc != 0:
        return "error"
    if not out:
        return "unchanged"
    return "plain" if _plain_modification_from_raw(out.splitlines()[0]) else "unfit"


def _plain_content_modification(root, parent, sha, path):
    """`_parent_path_status` 的 bool 视图（单一源）：仅 "plain" 为真。"""
    return _parent_path_status(root, parent, sha, path) == "plain"


def blob_pair(root, parent, sha, path):
    """取该提交相对某 parent 的前后两版 blob 原始字节。

    返回 (ok, before_bytes, after_bytes)。**ok=False ⇒ 调用方 MUST 保守判失鲜**——
    取不到、读不准、形态不合格一律归此侧，绝不因读取失败而放行。

    [tasks 1.1c] 两侧读取各自显式判 returncode，MUST NOT 依赖空串巧合：
    双侧失败会得 b"" == b"" ⇒ 判等值 ⇒ 放行真实设计改动（假绿方向）。
    """
    if not _plain_content_modification(root, parent, sha, path):
        return False, b"", b""
    # 用 cat-file blob 而非 show：前者输出 object 的**原始字节**，绕开 smudge/textconv
    # 等工作树转换；show 的输出受这些过滤器影响，同一 blob 在不同 config 下可读出不同字节。
    rc_before, before = run_git_bytes(root, "cat-file", "blob", f"{parent}:{path}")
    rc_after, after = run_git_bytes(root, "cat-file", "blob", f"{sha}:{path}")
    if rc_before != 0 or rc_after != 0:
        return False, b"", b""
    return True, before, after


# ────────────────────────────── fenced code block 围栏识别（单一源） ──────────────────────────
# [fix1 Important-1] 本仓四个 fence 追踪点（_normalize_checkbox_lines / _line_scoped_hits /
# tg02_hit / _parse_plan）**全部**经由下面这一组函数 + FenceTracker 判定围栏，MUST NOT 再各自
# 手抄 `line.lstrip().startswith("```")`——旧手抄口径只认 ``` ⇒ `~~~` 块内的实质改动被当成
# 「块外普通行」，在勾选框豁免侧是 fail-open（放行未批准的设计改动），在归档锚读侧是假 SHIPPED。
#
# 口径 = CommonMark fenced code block 的**有界**词法（数得完，故可手写；见 CLAUDE.md 基准 5）：
#   开启符：行首（去 ASCII 空白后）连续 ≥3 个同种字符，`` ` `` 或 `~`；
#   闭合符：与开启符**同种**、长度 **≥** 开启符长度、其后只余空白（故 ```` ``` ```` 关不掉
#           `~~~`，三 backtick 也关不掉四 backtick 开的块）；
#   info string（如 ```python）只出现在开启行，不影响识别。
# MUST NOT 在此之上再解析 markdown 的其它结构（表格 / 嵌套列表 / 引用块）——那是无界语法面。
_ASCII_WS = " \t\v\f\r\n"
_FENCE_CHARS = ("`", "~")


def fence_delim(line):
    """一行 str → 围栏符 (char, count, tail) 或 None（不是围栏形状）。

    tail = 围栏字符游程之后的剩余内容（判闭合时须 strip 后为空）。
    """
    s = line.lstrip(_ASCII_WS)
    if not s or s[0] not in _FENCE_CHARS:
        return None
    ch = s[0]
    n = len(s) - len(s.lstrip(ch))
    if n < 3:
        return None
    return ch, n, s[n:]


def fence_delim_bytes(line):
    """一行 bytes → 同 `fence_delim`。**单一源就是 `fence_delim`**——本函数只做形态转换。

    latin-1 是字节保序映射：任意字节都能解码、且 ASCII 区语义不变 ⇒ 转换零信息损失，
    两个形态不可能口径分叉（不是手抄副本，是同一份实现的两个入口）。
    """
    return fence_delim(line.decode("latin-1"))


class FenceTracker:
    """逐行喂入的围栏状态机。`inside` = 当前行是否落在 fenced code block 内部。

    `feed(line)` 返回该行是否**是围栏行本身**（开启或闭合）；围栏行既不在块内也不是普通内容，
    各调用点按自己的语义决定保留还是丢弃。EOF 时 `inside` 为真 = 围栏未闭合（调用方保守）。
    """

    def __init__(self):
        self.open = None                   # None=块外；(char, count)=块内，记开启符

    @property
    def inside(self):
        return self.open is not None

    def feed(self, line, is_bytes=False):
        d = fence_delim_bytes(line) if is_bytes else fence_delim(line)
        if d is None:
            return False
        ch, n, tail = d
        if self.open is None:
            self.open = (ch, n)            # 开启：任意 info string 均可
            return True
        och, on = self.open
        if ch == och and n >= on and not tail.strip():
            self.open = None               # 闭合：同种 + 不短于开启符 + 尾部只余空白
            return True
        return False                       # 块内出现的异种/过短围栏形状 ⇒ 只是普通内容行


# ── [impl-review-fix F3] CommonMark 的**第三支**代码块：缩进代码块 ──────────────────────
# 基准 5 把「``` / ~~~ / 四 backtick / **缩进 fence**」并列为 CommonMark 的**有界**变体。
# 前三支已由 fence_delim/FenceTracker 覆盖，缩进这一支此前漏网 ⇒ 四空格缩进代码块内的
# `- [ ] → - [x]` 仍被归一化 ⇒ 判豁免 = fail-open（放行未批准的设计改动）。
#
# 口径 = **超集** 判据（有意）：凡行首缩进 ≥4 列（tab 按 4 列制表位展开）的行，一律
# 不参与勾选框归一化。CommonMark 的缩进代码块判定本身依赖段落连续性 / 列表上下文
# （无界，MUST NOT 手搓）；取「缩进 ≥4 列」这个**必要条件**做超集，方向恒 fail-closed：
#   - 真缩进代码块内的翻转 ⇒ 不归一化 ⇒ 判失鲜 ✅（本条要修的洞）
#   - 深缩进的真嵌套任务项翻转 ⇒ 也判失鲜（假失鲜，**保守方向**，可接受）
# MUST NOT 为消掉后一类而引入列表上下文推断——那正是无界解析面。
_INDENT_CODE_COLUMNS = 4
_TAB_STOP = 4


def indent_columns(line, is_bytes=False):
    """行首空格/tab 展开后的列数（tab 跳到下一个 4 列制表位）。非空白字符即停。"""
    sp, tab = (b" ", b"\t") if is_bytes else (" ", "\t")
    col = 0
    for i in range(len(line)):
        ch = line[i:i + 1] if is_bytes else line[i]
        if ch == sp:
            col += 1
        elif ch == tab:
            col += _TAB_STOP - (col % _TAB_STOP)
        else:
            break
    return col


def is_indented_code_line(line, is_bytes=False):
    return indent_columns(line, is_bytes=is_bytes) >= _INDENT_CODE_COLUMNS


# ── [impl-review-fix F3] HTML 注释块（`<!--` … `-->`）────────────────────────────────
# 同属 fail-open 面：多行 HTML 注释内的勾选框翻转此前被归一化 ⇒ 判豁免。
# 该词法**有界**（两个固定 token 配对，无嵌套——CommonMark/HTML 里 `<!--` 不嵌套），
# 故可手写。方向也恒 fail-closed：误判「在注释内」只会少归一化 ⇒ 多判失鲜。
class HtmlCommentTracker:
    """逐行喂入的 HTML 注释块状态机。`feed` 返回**该行行首**是否已落在注释内部。

    行首锚定的勾选框只关心行首状态，故 feed 的返回值即调用点所需的全部信息。
    """

    def __init__(self):
        self.open = False

    def feed(self, line, is_bytes=False):
        start_inside = self.open
        o, c = (b"<!--", b"-->") if is_bytes else ("<!--", "-->")
        i = 0
        while True:
            if not self.open:
                j = line.find(o, i)
                if j < 0:
                    break
                self.open, i = True, j + len(o)
            else:
                j = line.find(c, i)
                if j < 0:
                    break
                self.open, i = False, j + len(c)
        return start_inside


# [fix1 Important-2] 行锚定复选框的**单一源**：str 版 CHECKBOX_RE（见下文 _parse_plan 处）与
# bytes 版 CHECKBOX_BYTES_RE 都从这一个 pattern 串派生，MUST NOT 再手抄字节副本（口径分叉即
# 下一个 bug）。test_checkbox_re_bytes_derived_from_single_source 机械守这条派生关系。
#
# ⚠️ 两个形态**并非行为逐字相同**——`\s` 在 str 模式下认 Unicode 空白（NBSP U+00A0 等），
# 在 bytes 模式下**只认 ASCII 空白**（tab 认、NBSP 不认）。故 NBSP 缩进的复选框行：
# CHECKBOX_RE 认（plan 解析把它当复选框），CHECKBOX_BYTES_RE 不认（勾选框归一化不动它）。
# 该差异的方向 = bytes 侧**少归一化** ⇒ 这类行的翻转不被豁免 ⇒ 判失鲜 ⇒ **保守**，可接受。
CHECKBOX_RE_PATTERN = r"^\s*-\s+\[([ xX])\]"
CHECKBOX_BYTES_RE = re.compile(CHECKBOX_RE_PATTERN.encode())


def _normalize_checkbox_lines(raw):
    """原始字节 → 勾选框标记归一化后的行列表；围栏未闭合返回 None（调用方保守）。

    [Task2] 归一化**只**把 task-list 行首那一个标记里的 ` `/`x`/`X` 换成 ` `：
    - 行首锚定（CHECKBOX_BYTES_RE），故表格单元格、行内反引号、散文字面量、
      以及同一行第二个之后的标记**一律不动**；
    - fenced code block 内的行不参与（口径同 _line_scoped_hits/_parse_plan——四处共用
      单一源 fence_delim/FenceTracker，`` ``` `` 与 `~~~` 两族围栏均识别）；
    - [impl-review-fix F3] **缩进代码块**（行首缩进 ≥4 列）与 **HTML 注释块**
      （`<!--` … `-->`）内的行同样不参与——二者此前漏网，是 fail-open（块内翻转被
      归一化 ⇒ 误判豁免 ⇒ 放行未批准的设计改动）；
    - 缩进 / 空白 / 其余字符逐字节保留——MUST NOT strip、MUST NOT 解码转换。

    切行用 split(b"\\n") 而非 splitlines()：后者还会在 \\r 处切开，CRLF↔LF
    差异会被抹平；前者把 CR 留在行尾，行尾与末尾换行的增删都保持可区分。
    """
    lines = raw.split(b"\n")
    out = []
    fence = FenceTracker()
    comment = HtmlCommentTracker()         # [impl-review-fix F3]
    for line in lines:
        if fence.feed(line, is_bytes=True) or fence.inside:
            out.append(line)               # 围栏行本身 / 块内行：逐字节原样保留，不归一化
            continue
        # [impl-review-fix F3] 注释状态只在围栏外推进（围栏内的 `<!--` 是代码文本，不开注释）。
        in_comment = comment.feed(line, is_bytes=True)
        if in_comment or is_indented_code_line(line, is_bytes=True):
            out.append(line)               # 注释块内 / 缩进代码块：同样不归一化
            continue
        m = CHECKBOX_BYTES_RE.match(line)
        if m:
            i = m.start(1)
            line = line[:i] + b" " + line[i + 1:]
        out.append(line)
    if fence.inside:
        return None                        # 围栏未闭合 ⇒ 「哪些行在 fence 内」不可信
    return out


def _tasks_content_exempt(before, after):
    """前后两版 tasks.md 原始字节 → 是否属于「零设计信息量」的改动，可豁免失鲜。

    [Task2 · ADR-1 求值口径] 判据 = **勾选框标记归一化后逐行等值**，仅此一种形态。
    MUST NOT 做语义 diff、MUST NOT 解析 markdown 结构、MUST NOT 把豁免面扩到勾选框
    以外的任何差异（措辞 / 格式化 / 错别字一律照判失鲜）。

    🔴 比较**按行号位置对齐**（zip），MUST NOT 用 LCS / difflib：LCS 下纯行重排的
    删除行与插入行逐字节相同，会被判等值而放行。行数不等 ⇒ 直接判不等值。

    抽成独立函数是为了把「保守回落」与「等值判据」分成两个可各自证伪的面：
    上游 design_frame_exempt 的每道回落分支都能在本函数被替身为恒 True 时单独证伪。
    """
    nb = _normalize_checkbox_lines(before)
    na = _normalize_checkbox_lines(after)
    if nb is None or na is None:
        return False                       # 围栏未闭合 ⇒ 保守
    if len(nb) != len(na):
        return False                       # 行数变化（段落增删 / 末尾换行增删）⇒ 失鲜
    return all(x == y for x, y in zip(nb, na))


# [Task4 · SW-1] 失鲜分类原因的**枚举全集**（机读取值）与人读标签。四条各对应
# 判据里一条**实际存在**的保守回落分支——不是凭空归类，改分支必须同步改这里。
STALE_CATEGORIES = {
    "mixed-paths": "帧内触及 tasks.md 以外的设计工件",
    "content-changed": "tasks.md 出现勾选框以外的改动",
    "blob-unreadable": "tasks.md 前后两版内容读取失败",
    "shape-unfit": "tasks.md 变更形态不合格（新建/删除/改名/类型或权限位变更，或根提交）",
    # [impl-review-fix F2] 枚举本身失败（git log / diff-tree 非零退出或输出形态看不清）。
    # 它不是"某帧不豁免"，而是"盘面读不清" ⇒ 按方向铁律一律判失鲜。
    "frame-enum-failed": "提交枚举失败（git 读取错误或输出形态不可解析）",
}


def design_frame_exempt_reason(root, sha, frame_files, base):
    """该帧不豁免的**分类原因**；豁免则返回 None。取值 ∈ STALE_CATEGORIES 的键。

    [Task4] 纯诊断细分：判定本身（豁免 / 不豁免）与 Task2 逐字相同——本函数只是把
    「为什么不豁免」这个此前被丢弃的信息留下来。MUST NOT 借分类之名改变任何一格判定。

    [Task2] 豁免资格三连，缺一即失鲜：① 帧内**落在 design 监视集内**的路径集恰为
    {tasks.md}（🔴 不是整个 commit 的文件列表——checkpoint 走 `git add -A`，真实完成
    提交必然打包源码；按整 commit 求值 ⇒ 豁免永不触发）② 形态是普通内容修改
    ③ 勾选框归一化后逐行等值。merge 提交须**对每个 parent** 都成立。
    """
    if design_watched_subs(frame_files, base) != {"tasks.md"}:
        return "mixed-paths"               # 帧内还触及其他监视路径 ⇒ 照判失鲜
    parents = commit_parents(root, sha)
    if not parents:
        return "shape-unfit"               # 根提交 / parent 解析失败 ⇒ 保守
    path = base + "tasks.md"
    for parent in parents:                 # merge：与**每个** parent 各自成立才算
        # [impl-review-fix F1] 形态先分四态再决策：unchanged ⇒ 该 parent 侧无改动可审，
        # 跳过（MUST NOT 当 shape-unfit——那会把普通 merge 全判失鲜）；error/unfit ⇒ 保守。
        st = _parent_path_status(root, parent, sha, path)
        if st == "unchanged":
            continue
        if st == "error":
            return "blob-unreadable"
        if st == "unfit":
            return "shape-unfit"
        ok, before, after = blob_pair(root, parent, sha, path)
        if not ok:
            return "blob-unreadable"       # blob 读取失败（形态已确认 plain）
        if not _tasks_content_exempt(before, after):
            return "content-changed"       # 勾选框以外的改动 ⇒ 照判失鲜
    return None


def design_frame_exempt(root, sha, frame_files, base):
    """该帧是否豁免失鲜判定。任何「看不清」一律 False（保守判失鲜）。

    判据本体在 design_frame_exempt_reason——本函数是它的 bool 视图（单一源）。

    〔impl-review-fix〕**测试专用**：Task4 拆出 _reason 变体后，生产路径（is_stale）
    只调 _reason（它要拿分类原因填诊断触发点），本函数已无生产调用者，仅供只关心
    「豁不豁免」而不关心「为什么」的用例读。保留是因为那批用例读它更直白；
    MUST NOT 据此以为它在热路径上——改判据一律改 _reason，本函数自动跟随。
    """
    return design_frame_exempt_reason(root, sha, frame_files, base) is None


class StaleResult(tuple):
    """(stale, freshness) + 结构化触发点 trigger（**纯诊断**，不参与判定）。

    [Task4] 刻意做成 2-tuple 的子类、而非 3 字段 NamedTuple：既有调用点与用例都按
    `stale, freshness = is_stale(...)` 解包、按 `== (False, "fresh")` 等值比较。
    触发点是**附加**诊断物，MUST NOT 改变判定值本身的形状，否则本票（纯诊断）就
    从后门改了既有契约。

    trigger: None（无触发点：不失鲜，或 code 域——其行为逐字不变）或 dict
             {sha: 短 sha, subject: commit subject, paths: 排序后的触发路径列表,
              category: STALE_CATEGORIES 的键}
    """

    def __new__(cls, stale, freshness, trigger=None):
        obj = super().__new__(cls, (stale, freshness))
        obj.trigger = trigger
        return obj

    @property
    def stale(self):
        return self[0]

    @property
    def freshness(self):
        return self[1]


def is_stale(root, rel, scope, change):
    """D9 分域〔Q1=B/Q3=A〕。scope: 'design'|'code'。返回 StaleResult（二元组兼容）。

    design 域仅盯本 change 四件套路径（proposal/design/tasks.md 与 specs/）——
    不可套用整个 openspec/changes/{change}/：该目录还装着 cr/verify/hand-off 等
    正常尾流产物，套用整目录会让收尾提交把 design-approved 误判陈旧（链自锁）。
    """
    sha = report_last_sha(root, rel)
    if not sha:
        return StaleResult(False, "uncommitted")   # Q3=A：人机同权，手写产物合法
    base = f"openspec/changes/{change}/"
    if scope == "design":
        # [spec-review-amendment B2] 带 subject 分帧遍历，checkpoint(impl-review) 精确式豁免。
        # [impl-review-fix F1] 分帧与「帧内触及路径」拆成两跳：本跳只取 (sha, subject)
        # 列表，路径由 frame_touched_paths 逐帧取（协议不同、不能塞进同一次 log：`-z`
        # 的 NUL 与 --format 的帧分隔符会互相污染）。subject 保证单行 ⇒ 按行切无歧义。
        # [Task1 · tasks 1.1b] format 携带 %H：不带 sha 就取不到该提交前后两版 blob。
        # 分隔符用 \x1f（unit separator）而非空格/冒号——subject 可含空格与冒号，须无歧义。
        # MUST NOT 加 --no-merges/--first-parent〔BR-6 护栏〕
        # ——头注释承诺 merge 内部提交逐一枚举不漏检；--no-merges 会改变 merge 场景失鲜语义。
        # [impl-review-fix F2] 枚举**显式判 returncode**：run_git 把非零退出折叠成空串
        # ⇒ 零帧 ⇒ 旧路径 return (False,"fresh") = 枚举失败被当成"没有可疑提交"（fail-open）。
        rc_log, out = run_git_rc(root, "log", f"{sha}..HEAD", "--format=%H%x1f%s")
        if rc_log != 0:
            return StaleResult(True, "stale", {
                "sha": "-", "subject": "", "paths": [],
                "category": "frame-enum-failed",
            })
        for frame in out.splitlines():
            if not frame:
                continue
            frame_sha, _, subject = frame.partition("\x1f")
            # [spec-review-amendment BR-7] 精确式：裸 checkpoint(impl-review) 或带冒号描述；
            # 裸 startswith 闭合前缀仍收 `checkpoint(impl-review)evil` 尾串垃圾，故用精确式。
            #
            # [Task3 · SW-1] 🔴 两条豁免通道的优先级：本判定 MUST 留在此处——即**读取任何
            # blob 之前**短路。次序是硬要求，不只是效率：短路保证精确 subject 帧的判定
            # 不受任何读取失败 / 形态不合格的影响。MUST NOT 把内容读取挪到它前面。
            #
            # BR-7 的语义 = 「变体**不因 subject** 获豁免」，**不是**「变体必然失鲜」：
            # 落到下面的任何 subject（BR-7 要拒的变体、空 subject、普通 subject）都仍
            # **可以**凭内容判据（勾选框归一化后逐行等值）获豁免。这不是放松 BR-7——
            # 豁免面取自内容本身，∴ 被监管方书写 subject 拿不到任何额外豁免面。
            # 真值表 8 格（{精确/变体/空/普通} × {纯勾选/语义改动}）逐格锁在
            # test_gate_freshness.py ⑧a；短路次序锁在 ⑧b。
            if subject == "checkpoint(impl-review)" or subject.startswith("checkpoint(impl-review):"):
                continue                      # 阶段三合法尾流修订，豁免不失鲜
            # [impl-review-fix F1] 监视集成员判据**只有一处**——`design_watched_subs`。
            # 此处 MUST NOT 再内联一份 `sub in DESIGN_WATCHED_NAMES or ...`：两份判据
            # 将来只改一处时，design_frame_exempt 会把「帧内路径集」误算成 {tasks.md}
            # ⇒ 豁免误开（fail-open）。新增一类监视路径只改 design_watched_subs 即可。
            # [impl-review-fix F1/F2] 帧内触及路径：取不到 ⇒ 保守判失鲜，MUST NOT 当空集
            # （空集会走下面的 `continue` 静默跳过整帧 = fail-open）。
            frame_files = frame_touched_paths(root, frame_sha)
            if frame_files is None:
                return StaleResult(True, "stale", {
                    "sha": frame_sha[:7], "subject": subject, "paths": [],
                    "category": "frame-enum-failed",
                })
            subs = design_watched_subs(frame_files, base)
            if not subs:
                continue                      # 本帧未触及任何监视路径 ⇒ 与设计门无关
            # [Task4 · SW-1] 触发点诊断：判定沿用 Task2/Task3 的分支，只是把「为什么」
            # 留下来交给 emit。分类原因取自 design_frame_exempt_reason 的**实际分支**
            # （单一源），MUST NOT 在此另拼一套归类。
            reason = design_frame_exempt_reason(root, frame_sha, frame_files, base)
            if reason is not None:
                return StaleResult(True, "stale", {
                    "sha": frame_sha[:7],
                    "subject": subject,
                    "paths": sorted(subs),
                    "category": reason,
                })
        return StaleResult(False, "fresh")
    # scope == "code"：行为逐字不变（无 subject、无豁免、无 --no-merges、无触发点诊断）
    files = run_git(root, "log", f"{sha}..HEAD", "--name-only", "--format=")
    for f in filter(None, files.splitlines()):
        if not f.startswith("openspec/"):
            return StaleResult(True, "stale")
    return StaleResult(False, "fresh")


def _line_scoped_hits(text, candidates):
    """文本级行锚定核心（零正则）：候选须独占一行（strip 后等值），忽略 fenced code block。
    返回 (hits[按 candidates 原序去重], unbalanced[EOF 时围栏未闭合])。
    [impl-review-fix FIX-5；T75] 现役唯一调用方 = archived_verify_state（归档 dual-read 兜底旧
    inline）；live decide() 侧的 inline 读半场已随 Task6 迁 frontmatter 退役，其专属读点函数
    随 T75 一并删除（不再留孤儿）。fence 翻转口径同 _parse_plan
    （共用单一源 fence_delim/FenceTracker，``` 与 ~~~ 两族均识别）。"""
    cand = set(candidates)
    hit = set()
    fence = FenceTracker()
    for line in text.splitlines():
        if fence.feed(line) or fence.inside:
            continue
        s = line.strip()
        if s in cand:
            hit.add(s)
    return [a for a in candidates if a in hit], fence.inside


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


def _stale_trigger_hint(trigger):
    """结构化触发点 → 人读串。与 JSON `stale_trigger` **同一数据源**（两侧不各拼各的）。

    [Task4] 纯诊断串：无触发点返回空串（拼接后文案逐字不变）。
    """
    if not trigger:
        return ""
    paths = "、".join(trigger["paths"]) or "(无)"
    label = STALE_CATEGORIES.get(trigger["category"], trigger["category"])
    return (f"；触发点：提交 {trigger['sha']} \"{trigger['subject']}\" "
            f"触及 {paths}（{label}）")


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
    fence = FenceTracker()
    for line in text.splitlines():
        if fence.feed(line) or fence.inside:
            continue
        if line.startswith("## "):   # 真 H2 标题（非 fence 内）= 头部区结束
            break
        s = line.strip()
        if s.startswith("〔TG") and "〔TG-02" in s:   # 声明行（非描述散文）且含 TG-02
            return True
    # [fix2 Important] 围栏未闭合 ⇒ 头部声明区的可见性判定不可信（悬空围栏会吞掉声明行，
    # 方向是 fail-open：静默跳过 embedded-test-sop 门）。与另三个 fence 调用点
    # （_normalize_checkbox_lines / _parse_plan / _line_scoped_hits「看不清就保守」）方向对齐：
    # 看不清 ⇒ 保守要求跑 SOP。
    if fence.inside:
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
CHECKBOX_RE = re.compile(CHECKBOX_RE_PATTERN)   # 行锚定复选框（非全文子串）；单一源见上文常量


def _parse_plan(text):
    # [T34/impl-review-fix] fence-aware 单遍解析（Task 标题与复选框统一围栏口径）。
    # fenced code block（``` 围栏）内的行对 Task 标题与复选框**均不可见**（CR-F1/F2）。
    # 返回 (task_order[出现序,含重号], boxes_by_task{num:[checked_bool]}, any_checkbox, unbalanced)。
    # unbalanced=True 表示 EOF 时围栏未闭合（悬空 ```）——plan 无法可靠解析（CR-F1）。
    task_order = []
    boxes_by_task = {}
    any_checkbox = False
    cur = None
    fence = FenceTracker()
    for line in text.splitlines():
        if fence.feed(line) or fence.inside:
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
    return task_order, boxes_by_task, any_checkbox, fence.inside


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
            # 归档 verify-report 并存 PASS/FAIL 冲突锚 → 同 active 路径冲突锚判 UNKNOWN 语义〔CV-1〕
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
    design_res = is_stale(root, str(report.relative_to(root)), "design", change)
    if design_res.stale:
        # [Task4 · SW-1] 纯诊断：附结构化触发点（人读串 + JSON `stale_trigger` 同源，
        # 见 _stale_trigger_hint）。默认处置**只**推荐重跑设计门——MUST NOT 在此提
        # `checkpoint(impl-review)`：豁免逐提交求值，已触发失鲜的那个提交不会因**后补**
        # 一个 checkpoint 提交而被追溯赦免，写进指引等于教撞门者做一件不起作用的事。
        extra = {"stale_trigger": design_res.trigger} if design_res.trigger else {}
        emit("REFUSE_START", EXIT_REFUSE, None,
             "design-approved 之后四件套被改动 → 拍板失鲜，改设计须重审"
             "（重跑 sdflow-spec-review 后重新拍板补锚）"
             + _stale_trigger_hint(design_res.trigger), **extra)
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
        # [impl-review-fix OV-2] verify 读点 stale 判定先于 absent 分支（L~812）——若报告同时是
        # 「首行 --- 无闭合」absent 态，stale 会先 emit 而吞掉未闭合结构提示、且「结论陈旧」措辞对
        # 无有效结论的报告失准。附加纯结构提示（非空才追加，同三读点口径），不改 verdict/退出码/next。
        emit("RERUN_STALE", EXIT_OK, "sdflow-done",
             "verify 结论后存在 openspec/ 外提交 → 结论陈旧（FAIL 修复后重验不卡死 / PASS 不背书新代码）"
             + _unclosed_frontmatter_hint(vf),
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
