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

ship-gate frontmatter 字段（下划线命名，防与旧 inline 锚字面连字符漂移；校验见 FIELD_VALIDATORS）:
    design_approved: true|false   spec-review-report.md（sdflow-spec-review 拍板回写，头部 prepend）
    verify: PASS|FAIL             verify-report.md（sdflow-done verify 模板，头部 prepend）
    code_review: pass|blocked     code-review-report.md（sdflow-code-review 模板，头部 prepend）
    reviewed_sha: <40 位 hex>     三个报告**各自**必带〔harden-gate-git-layer ADR-1〕，与结论
        字段同层（顶层 `ship-gate:` 的直接子键）。语义 = 「**被批准的是哪一份盘面**」，不是
        「写报告的时刻」；失鲜判定以它为唯一真相源，缺失 / 非法 / 不解析为 commit ⇒ UNKNOWN(6)
        fail-closed，**MUST NOT** 回退任何反推式锚（旧 `report_last_sha` 已退役）。

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
    锚一律取报告自录的 `reviewed_sha`〔harden-gate-git-layer ADR-1〕；原「报告从未提交 →
        freshness=uncommitted」语义随反推锚一并退役——锚是录下来的常量，报告有没有进过提交
        与「被批准的是哪个盘面」无关（未提交的报告照样带得出有效锚）。

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
import os
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


# [harden-gate-git-layer Task1 · ADR-1/3.5] 判定不能的结构化信号。
# 复用仓内 `_fail_closed_on_bad` 的 (cause, category) 二元组模式：category 供 main() 机械分派，
# cause 供人读。**唯一映射点在 main()** —— 抛出方 MUST NOT 自行 emit/exit，否则退出码映射
# 会散成多处、各处措辞漂移（design.md「五类原因各给可行动诊断」的前提是单一映射点）。
CAUSE_GIT_UNAVAILABLE = "git-unavailable"     # git 不在 PATH / 不可执行（Task2 接入）
CAUSE_GIT_TIMEOUT = "git-timeout"             # 调用超时（Task2 接入）
CAUSE_ANCHOR_MISSING = "anchor-missing"       # reviewed_sha 字段缺失（含报告本身读不到）
CAUSE_ANCHOR_INVALID = "anchor-invalid"       # reviewed_sha 语法非法（缩写 SHA / HEAD / 坏 hex）
CAUSE_ANCHOR_UNRESOLVABLE = "anchor-unresolvable"   # 对象不存在 / 不是 commit（blob/tree）
CAUSE_READ_FAILED = "read-failed"             # 仓损坏 / 权限（Task3/4 接入）


class GateIndeterminate(Exception):
    """判定不能 → main() 统一映射 UNKNOWN(6)。

    cause: 人读原因串（含具体字段值 / 路径，供撞门者直接行动）
    category: 上列 CAUSE_* 之一，main() 按它选可行动诊断（MUST NOT 用一句「git 调用失败」打天下）
    """

    def __init__(self, cause, category):
        super().__init__(f"[{category}] {cause}")
        self.cause = cause
        self.category = category


# [harden-gate-git-layer Task2 · ADR-6 · tasks 3.4] `_GIT_HARDEN` 的职责 =
# **中和一切能改变判定输入的外部可控态**，而不只是「中和 core.quotePath」。外部可控态有两个面，
# 两面都必须扫，缺一即判定输入仍可被外部翻转：
#   **config 面**（本常量，`-c` 注入）：
#   ① -c core.quotePath=false：git 默认把非 ASCII 路径 C-quote（八进制+首尾引号），
#      裸 f.startswith(base)/startswith("openspec/") 对中文文件名路径全失配 → design 域假鲜
#      （拍板后偷改中文名 spec 静默放行=假✅）/ code 域假陈旧。本项目中文文件名密集，realistic。
#   ② errors="replace"：报告内容/subject/文件名非 UTF-8 时 strict 解码抛 UnicodeDecodeError
#      → 退出码 1 逸出契约集 {0,3,4,5,6}；与头注释「非 UTF-8 以 replace 解码」及本地 read_text
#      路径的既有加固对齐（archived verify 走 git show 是首个用 subprocess 读报告内容的路径）。
#   **环境面**（`_git_env()`，denylist 清理）：见该函数注释。
# MUST NOT 以「我们碰巧没用到 diff / pathspec」当安全论据——那是拿现状当保证（基准 3）。
_GIT_HARDEN = ("-c", "core.quotePath=false")

# [harden-gate-git-layer Task2 · ADR-5 · tasks 3.2] 三个 helper 统一上界。
# 判据来源 = 仓内既有先例 `sdflow-buglist/scripts/buglist.py::repo_root` 的 `git_timeout = 30`：
# 这些都是**纯本地元数据查询**（正常毫秒级），30 秒是**文件系统卡死 / 网络文件系统挂起**的
# 判定线，**不是性能预算**。MUST NOT 按「最慢的仓要多久」来调大——那会把它误当性能预算，
# 从而让真正的挂起拖到无限久（而 gate 是同步阻塞在链序里的）。
# 聚合上界的数量级：design 域一次 decide() 约 4 次 git 调用（与提交数无关）
# ⇒ 最坏情形（文件系统级挂起）约 2 分钟落进 UNKNOWN(6)。**有界 ≠ 短**，此处写明免各自心算。
GIT_TIMEOUT_SECONDS = 30


def _git_env():
    """子进程 env：复制当前环境 → **剔除 `GIT_` 前缀键** → **本进程回填两个禁读键**。

    [harden-gate-git-layer Task2 · ADR-6 · tasks 3.3] MUST 用 denylist，**MUST NOT 用 allowlist**
    （只显式构造 PATH/HOME 等几个键）——allowlist 在 Windows 会漏 `SYSTEMROOT`/`COMSPEC` 等
    `CreateProcess` 依赖变量，导致子进程启动本身失败；这与本仓已踩过的跨平台坑同类：
    **本地 macOS 测不出，只有真实 Windows runner 才暴露**。

    剔除面 = 全部 `GIT_*`，非只剔已知的几个（`GIT_ICASE_PATHSPECS` / `GIT_DIR` / `GIT_WORK_TREE`…）：
    已知集是会增长的，逐个点名等于承诺「git 不再新增能改变输出的环境变量」——那是拿现状当保证。

    [fix1 F1] **剔 `GIT_*` 不等于封死环境面**：global/system gitconfig 的**位置**由
    `HOME` / `XDG_CONFIG_HOME` 决定，而这两个键非 `GIT_` 前缀、按 denylist 必须透传
    ⇒ 外部仍能经一份 global gitconfig 改判定输入。已实测：global 置
    `i18n.logOutputEncoding=GBK` 后 `run_git("log", "--format=%s")` 的 subject 由
    `主题中文` 变成 `����`，而该 subject 正是 `done_task_ids` 的判定输入。
    ∴ 在 denylist **之后**回填 `GIT_CONFIG_GLOBAL` / `GIT_CONFIG_SYSTEM` = `/dev/null`：
    **本进程注入 ≠ 外部可控**，不破坏 denylist 口径（先剔干净，再由我们自己写死）。
      · 空设备是 git **官方文档给的**跳过写法（git(1)：「Can be set to /dev/null to
        skip reading configuration files of the respective level.」），非平台巧合。
        取 `os.devnull` 而非字面量 `"/dev/null"`：Windows 上它是原生 `nul`（Git for
        Windows 的 compat 层两种写法都认，用平台原生值免赌 compat 映射）。
      · MUST NOT 改用 `-c i18n.logOutputEncoding=UTF-8 -c log.showSignature=false` 之类的
        **逐项覆盖**：那是点名已知 knob，与本函数剔除面选全前缀的理由同构地错（config 键集
        只会增长，点名 = 承诺「不再新增能改变输出的配置项」）。整片禁读才是面治。
      · **未封 repo-local `.git/config`——理由是能力等价，不是「有别的东西守着」。**
        能写 `.git/config` 的人，同样能写 `.git/objects` / `.git/refs`，或直接
        `git commit --amend` 伪造 subject——所需权限 ≤ 已足以击穿本 gate 的权限，
        ∴ 被判仓按构造就在信任边界内，封它无净收益（且 env 层无干净关法）。
        🔴 **此项无机械覆盖，是登记在案的残余**：`.git/config` 置
        `i18n.logOutputEncoding=GBK` 确实能翻转判定输入（实测 subject 变乱码）。
        MUST NOT 声称它被 `test_verdict_is_identical_under_polluted_git_env` 守住——
        那条只污染 `diff.ignoreSubmodules` 这一个良性 knob，覆盖不到本面。

    [fix1 M1] **与先例的差异登记**：`sdflow-buglist/scripts/buglist.py::repo_root`（:613-618）
    只剔 discovery 类（`GIT_DIR`/`GIT_WORK_TREE`/`GIT_CONFIG_*`…）并**刻意保留执行类**
    （`GIT_EXEC_PATH` 等）；本函数剔全前缀，故连 `GIT_EXEC_PATH` 一并剔掉。
    理由：本文件只调 builtin 子命令（`log`/`rev-parse`/`ls-tree`/`show`/`cat-file`），
    不依赖外部 `git-*` 可执行文件的查找路径，∴ 保留执行类无收益、而枚举「哪些算执行类」
    要长期跟 git 版本（正是本函数拒绝的那种承诺）。**代价**（显式登记，非未知）：日后若
    引入非 builtin 的 git 子命令，剔掉 `GIT_EXEC_PATH` 可能令 git 找不到它而 rc≠0，
    `run_git` 返 `""` ⇒ **静默降级而非 UNKNOWN**。届时 MUST 改为按 buglist 口径分类剔除，
    而不是给这里打一个特例补丁。
    """
    env = os.environ.copy()
    for key in [k for k in env if k.startswith("GIT_")]:
        del env[key]
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    return env


def _git_run(root, args, text):
    """三个 helper 唯一的 subprocess 出口：统一 timeout + env 清理 + 环境级失败映射。

    [harden-gate-git-layer Task2 · tasks 3.1/3.2/3.3] 单出口而非三处复制——三份拷贝必然漂移
    （历史上 `_GIT_HARDEN` 就是靠单点注入才没漏），且「新增一个 git 调用点忘了加固」这条
    失效模式在单出口下不存在。三个 helper 的语义差异（text/strip vs 原始字节）留在各自壳里。

    环境级失败 MUST 收敛进退出码契约集 `{0,3,4,5,6}`：裸 `OSError`（git 不在 PATH /
    不可执行 / 权限不足）与 `TimeoutExpired`（文件系统挂起）逸出后是 Python 默认退出码 1，
    对 `/sdflow-ship` 链序而言是**契约外**取值 ⇒ 无处置路径。二者各自 category 不同，
    因为补救动作完全不同（装 git vs 查磁盘），MUST NOT 合并成一句「git 调用失败」。
    """
    cmd = ["git", "-C", str(root), *_GIT_HARDEN, *args]
    kwargs = {"capture_output": True, "timeout": GIT_TIMEOUT_SECONDS, "env": _git_env()}
    if text:
        kwargs["text"] = True
        kwargs["errors"] = "replace"
    shown = " ".join(str(x) for x in cmd)
    try:
        return subprocess.run(cmd, **kwargs)
    except subprocess.TimeoutExpired:
        raise GateIndeterminate(
            f"git 调用超过 {GIT_TIMEOUT_SECONDS}s 未返回：{shown}", CAUSE_GIT_TIMEOUT)
    except OSError as exc:
        raise GateIndeterminate(
            f"git 子进程无法启动（{type(exc).__name__}: {exc}）：{shown}",
            CAUSE_GIT_UNAVAILABLE)


def run_git(root, *args):
    r = _git_run(root, args, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def run_git_rc(root, *args):
    # [spec-review-amendment H3] 返回码可见版：run_git 把 git 错误与「路径不在树/空输出」
    # 都折叠成空串，base_ref 的 None 性据此驱动「base 不存在→UNKNOWN」vs「归档缺→REFUSE」分岔。
    r = _git_run(root, args, text=True)
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


# [harden-gate-git-layer Task1 · tasks 1.9] `report_last_sha`（`git log -1 -- <report>` 反推锚）
# 已退役：任何后续提交顺带碰一下报告文件（空行 / CI reformat / 措辞回填）都会把锚无声前移，
# 埋掉锚前的未审改动，且该提交无需改动任何结论字段（design.md 缺陷 9）。
# 取代者 = 下方 `read_reviewed_sha`：producer 落结论时把「被批准的盘面」录进 frontmatter，
# reader 只读不推。**MUST NOT** 在锚缺失/非法时回退本函数或任何反推式锚（Compliance 硬约束）。


def read_reviewed_sha(root, rel):
    """读报告 frontmatter 的 `reviewed_sha` 锚（语义级校验）。返回 40 位 OID 字符串。

    [harden-gate-git-layer Task1 · ADR-1 · tasks 1.3] 两层校验显式分层：
      - **语法级**在纯文本函数 `parse_ship_gate_frontmatter`（`_is_full_oid`）——40 位 hex，
        拒缩写 SHA / `HEAD` / 坏 SHA。live 读与归档 git-show 文本读共用同一核心。
      - **语义级**在本函数（需 `root` 才做得了）：`git cat-file -e <sha>^{commit}` 确认该对象
        **存在且是 commit**——`^{commit}` 后缀使指向 blob / tree 的锚同样落进 rc≠0。

    四种形态各抛 `GateIndeterminate`（→ main() 映射 UNKNOWN(6)），category 各不相同以便
    诊断点名具体是哪一种：字段缺失 / 语法非法 / 对象不存在或非 commit。
    **MUST NOT** 在任一形态下回退 `report_last_sha` 或任何反推式锚。
    """
    path = root / rel
    if not path.is_file():
        raise GateIndeterminate(
            f"报告 {rel} 读不到（文件不存在），无从取 reviewed_sha 锚", CAUSE_ANCHOR_MISSING)
    text = path.read_text(encoding="utf-8", errors="replace")
    state, err = parse_ship_gate_frontmatter(text)
    if err is not None:
        field, cat = err
        # 语法级校验不过（含 reviewed_sha 自身 out-of-domain，也含同块内其它字段的坏形态——
        # 坏块整体不可信，MUST NOT 从坏块里挑一个字段出来采信）。
        raise GateIndeterminate(
            f"报告 {rel} 的 ship-gate frontmatter 坏（字段={field} 类别={cat}）",
            CAUSE_ANCHOR_INVALID)
    if "reviewed_sha" not in state:
        raise GateIndeterminate(
            f"报告 {rel} 的 ship-gate frontmatter 缺 reviewed_sha 字段", CAUSE_ANCHOR_MISSING)
    sha = state["reviewed_sha"]
    rc, _ = run_git_rc(root, "cat-file", "-e", f"{sha}^{{commit}}")
    if rc != 0:
        raise GateIndeterminate(
            f"报告 {rel} 的 reviewed_sha={sha} 在本仓解析不到 commit 对象"
            "（对象不存在，或指向 blob/tree 而非 commit）", CAUSE_ANCHOR_UNRESOLVABLE)
    return sha


DESIGN_WATCHED_NAMES = ("proposal.md", "design.md", "tasks.md")   # D9〔design.md 决策源〕四件套


def run_git_bytes(root, *args):
    """保真读取：返回 (returncode, stdout **原始字节**)。

    [fix-design-gate-freshness-proxy Task1 · tasks 1.1d] MUST NOT 复用 run_git/run_git_rc——
    那条路径 text=True + errors="replace" + .strip()，四者各自可造假等值：
    吞首尾空白、吞末尾换行、CRLF↔LF 不可分辨、非 UTF-8 字节被替换成 U+FFFD 后两版趋同。
    本函数只做 subprocess 原样取字节，解码与归一化留给调用方按判据自行决定。

    [harden-gate-git-layer Task2] 「MUST NOT 复用 run_git/run_git_rc」约束的是**文本层语义**
    （text/errors/strip 四者各自可造假等值），不是 subprocess 调用本身：三者共用 `_git_run`
    取 timeout + env 清理 + 环境级失败映射，本函数仍走 text=False 拿原始字节，语义无损。
    """
    r = _git_run(root, args, text=False)
    return r.returncode, r.stdout


DESIGN_WATCHED_SUBTREE = "specs/"      # 监视集里唯一的子树（其余三项是固定文件名）


def design_pathspecs(base):
    """design 域监视集的 pathspec 列表（供 `ls-tree -- <pathspec>...`）。

    [harden-gate-git-layer Task3 · tasks 2.1] 单一源：监视集成员判据只此一处。
    `tasks.md` **也在其中**——它的存在性判定由此统一走 `ls-tree` 的干净语义
    （rc=0+不在结果里 = 缺失），而不是交给 `git show` 的 rc=128（与仓损坏不可区分）。
    """
    return [base + n for n in DESIGN_WATCHED_NAMES] + [base + DESIGN_WATCHED_SUBTREE]


def ls_tree_map(root, ref, pathspecs):
    """`git ls-tree -r -z <ref> -- <pathspecs>` → `{path_bytes: (mode, type, oid)}`。

    [harden-gate-git-layer Task3 · ADR-2 · tasks 2.1/2.1b/2.4] 判据本体的取数口径。

    **`-z` MUST NOT 省略**：它不只是换分隔符——**它同时关闭 git 默认的路径 C-quote**，
    而 C-quote 正是本 change 缺陷 6（控制字符 / 非 ASCII 路径被弄花后逃出监视集）的成因。
    省掉 `-z` ⇒ 新代码路径原样踩回该缺陷。

    **解析口径**（`ls-tree -z` 的输出格式有界、良定义，∴ 可正确手写解析，不撞基准 5）：
    按 `\\0` 切记录，每条记录按**首个 `\\t`** 切分为 `<mode> <type> <oid>` 与 path；
    **path 部分保持原始字节，不解码、不反转义**（解码会让不同字节序列在 U+FFFD 处趋同）。

    **rc≠0 = 真读失败** ⇒ `GateIndeterminate`（仓损坏 / 权限 / ref 不可达）。
    **rc=0 + 某路径不在结果里 = 合法的「缺失」信号**，由调用方按「映射不等 ⇒ stale」处理，
    **MUST NOT** 混作读取失败——二者是不同的事，前者可判（判 stale），后者不可判。
    """
    rc, out = run_git_bytes(root, "ls-tree", "-r", "-z", ref, "--", *pathspecs)
    if rc != 0:
        raise GateIndeterminate(
            f"git ls-tree 读 {ref} 的监视集失败（rc={rc}）——仓损坏 / 权限 / ref 不可达",
            CAUSE_READ_FAILED)
    entries = {}
    for record in out.split(b"\0"):
        if not record:
            continue                       # 末尾 NUL 切出的空 token
        meta, sep, path = record.partition(b"\t")
        fields = meta.split()
        if not sep or len(fields) != 3:
            # 协议外形态 ⇒ 看不清 ⇒ 不可判（MUST NOT 当空集：空集会与另一侧比出假等值）
            raise GateIndeterminate(
                f"git ls-tree 输出形态不可解析（ref={ref}）", CAUSE_READ_FAILED)
        entries[path] = tuple(fields)
    return entries


def read_blob_bytes(root, ref, path, label):
    """取 `<ref>:<path>` 的 blob 原始字节。rc≠0 ⇒ `GateIndeterminate`。

    [harden-gate-git-layer Task3 · tasks 2.2/2.4] **调用前提**：`ls_tree_map` 已确认该路径
    在该 ref 下存在。∴ 此处的 rc≠0 恒为**真读失败**（仓损坏 / 权限），可以放心映射成
    不可判——存在性判定 MUST NOT 落到这里（对「路径不存在」与「仓损坏」它返回同一个
    rc=128，机械上不可区分，会让「文件被删」的诊断误导撞门者去查仓完整性）。

    用 `cat-file blob` 而非 `show`：前者是**契约级**的原始字节原语（plumbing，定义上不做
    任何工作树转换）；后者输出原始字节只是**默认行为**——`git show --textconv <rev>:<path>`
    可以翻转它（已实测，git 2.50.1：`.gitattributes` 配 `diff=fake` + `diff.fake.textconv`
    后，`show HEAD:a.md` 仍是原始字节，`show --textconv HEAD:a.md` 则被转换）。
    ∴ 选前者是**缩小可翻转面**（判定输入不依赖「没人加那个 flag」这一约定），
    **不是**在修补一个现存的洞。二者对本函数的**契约面**（rc=0 取字节 / rc≠0 不可判）
    完全一致，∴ 这是同契约下更保守的取法。

    🔴 **推论（防后人据错理由去修不存在的洞）**：`archived_verify_state`（:337）用
    `git show <ref>:<path>` 读归档 verify-report，依同一实测口径**不受 textconv/smudge
    影响、无需改动**。早先版本的本段曾声称「`show` 的输出受这些 config 影响」——该前提
    实测为假，已订正（`openspec/rules/premise-verification.md`：写断言前先验证外部事实）。

    **MUST NOT** 把失败折成 `b""`：两侧都失败会比出 `b"" == b""` ⇒ 判等值 ⇒ 放行真实
    设计改动（design.md「读失败 ≠ 内容为空」的头号自噬风险，与缺陷 3/10 同一失效模式）。
    """
    rc, raw = run_git_bytes(root, "cat-file", "blob", f"{ref}:{path}")
    if rc != 0:
        raise GateIndeterminate(
            f"读 {label} 的 {path}@{ref} 内容失败（rc={rc}）——该路径已确认存在，"
            "故此为真读失败（仓损坏 / 权限）", CAUSE_READ_FAILED)
    return raw


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

    [harden-gate-git-layer Task3 · tasks 2.9] **保留复用**：帧比较整簇退役后，本函数与
    `_normalize_checkbox_lines` / `DESIGN_WATCHED_NAMES` 是仅有的三处保留件。现役调用点 =
    `is_stale` 的 design 分支（映射差异仅在 tasks.md 且两侧 mode/type 相同时的唯一豁免闸门）。
    🔴 承重升格已登记（design.md 残余面 T189）：旧设计里它只是众多判据之一，新设计下它是
    design 域**唯一**的放行闸门。
    """
    nb = _normalize_checkbox_lines(before)
    na = _normalize_checkbox_lines(after)
    if nb is None or na is None:
        return False                       # 围栏未闭合 ⇒ 保守
    if len(nb) != len(na):
        return False                       # 行数变化（段落增删 / 末尾换行增删）⇒ 失鲜
    return all(x == y for x, y in zip(nb, na))


def is_stale(root, rel, scope, change):
    """D9 分域〔Q1=B/Q3=A〕。scope: 'design'|'code'。返回 `(stale, freshness)` 二元组。

    design 域仅盯本 change 四件套路径（proposal/design/tasks.md 与 specs/）——
    不可套用整个 openspec/changes/{change}/：该目录还装着 cr/verify/hand-off 等
    正常尾流产物，套用整目录会让收尾提交把 design-approved 误判陈旧（链自锁）。
    """
    # [harden-gate-git-layer Task1 · ADR-1] 锚 = 报告自己录下的 `reviewed_sha`（被批准的盘面），
    # 不再从 `git log -1 -- <report>` 反推「写报告的时刻」。缺失 / 非法 / 不解析为 commit ⇒
    # `GateIndeterminate` 上抛（→ UNKNOWN(6)），**MUST NOT** 回退旧锚、MUST NOT 静默判 fresh。
    sha = read_reviewed_sha(root, rel)
    base = f"openspec/changes/{change}/"
    if scope == "design":
        # [harden-gate-git-layer Task3 · ADR-2 · tasks 2.1/2.2] **比内容，不枚举路径**：
        # 把锚与 HEAD 两侧的被审内容直接摆在一起比。比较单位 = `path → (mode, type, oid)`
        # 映射，∴ **新增 / 删除 / 改名 / 修改 / mode 变更 / 类型变更天然全覆盖**，
        # 且不需要另做双侧并集（映射比较本身就是并集语义）。
        #
        # 🔴 这取代的是「顺着 git 管道推断哪些路径动过」的整簇帧比较（design.md 缺陷 1–8 同源）。
        # MUST NOT 为凑诊断 / 兼容旧行为把任何路径枚举通路加回来——那是把刚砍掉的推断面
        # 从后门放回来（ADR-4）。
        specs = design_pathspecs(base)
        anchor_map = ls_tree_map(root, sha, specs)
        head_map = ls_tree_map(root, "HEAD", specs)
        if anchor_map == head_map:
            return False, "fresh"          # 映射完全相等 ⇒ fresh，**0 次内容读取**
        # 唯一豁免：任务清单的**纯复选框翻转**。〔ADR-3〕勾选框的写入方是 agent 的自由行为、
        # 不是流程契约，∴ 该豁免 **MUST 常开、按内容切**——**MUST NOT 按阶段切**
        # （按阶段切会让非该阶段的正常勾选立刻假失鲜，前序 change 已实测证伪）。
        diff = {p for p in set(anchor_map) | set(head_map)
                if anchor_map.get(p) != head_map.get(p)}
        # [fix1 F1] `os.fsencode`，**MUST NOT `.encode("utf-8")`**：`change` 来自 argv，
        # CPython 用 **surrogateescape** 把原始字节解成 str，非 UTF-8 字节变 lone surrogate
        # （`\udcff`）——`.encode("utf-8")` 对它抛 `UnicodeEncodeError`，而 `main()` 只捕
        # `GateIndeterminate` ⇒ 异常逸出 ⇒ **退出码 1，落在契约集 `{0,3,4,5,6}` 之外**。
        # `os.fsencode` 是那次解码的**逆运算**，∴ 还原出的正是 git 在 `ls-tree -z` 里吐的
        # 原始路径字节，与映射的 key 口径天然对齐（不是「换个更宽容的编码」，是对称性）。
        # MUST NOT 改用 `except Exception` 兜底——那会把编程错误一并吞成 UNKNOWN。
        tasks_path = os.fsencode(base + "tasks.md")
        before_entry, after_entry = anchor_map.get(tasks_path), head_map.get(tasks_path)
        if (diff == {tasks_path}
                and before_entry is not None and after_entry is not None
                and before_entry[:2] == after_entry[:2]
                # [fix1 F2] type **是 blob**，非只「两侧相等」：`ls-tree -r` 会输出 gitlink
                # （`160000 commit <oid>\t<path>`，已实测）⇒ 两侧同为 commit、oid 不同时
                # 会落进本豁免分支，随后 `cat-file blob` rc=128 → UNKNOWN(6)，诊断说
                # 「该路径已确认存在，故此为真读失败（仓损坏 / 权限）」——**正是
                # `read_blob_bytes` docstring 自己禁止的误导口径**。方向虽 fail-closed，
                # 但把「tasks.md 变成了 submodule」讲成「仓坏了」，会把撞门者送错方向。
                and after_entry[1] == b"blob"):
            # 两侧均存在（单侧缺失 = 被删 / rename 出监视集 ⇒ 落下面的 stale，**不是**读失败）
            # 且 mode/type 相同（仅 oid 变 = 纯内容改动）⇒ 才值得取字节判豁免。
            # mode/type 变了却内容相同（chmod / regular↔symlink）⇒ 字节判据必说「等值」，
            # ∴ MUST 先在这里拦掉，否则状态位变更被静默放行。
            rel_tasks = base + "tasks.md"
            before = read_blob_bytes(root, sha, rel_tasks, "锚侧")
            after = read_blob_bytes(root, "HEAD", rel_tasks, "HEAD 侧")
            if _tasks_content_exempt(before, after):
                return False, "fresh"
        return True, "stale"
    # scope == "code"：行为逐字不变（Task5 改顶层条目比较）
    files = run_git(root, "log", f"{sha}..HEAD", "--name-only", "--format=")
    for f in filter(None, files.splitlines()):
        if not f.startswith("openspec/"):
            return True, "stale"
    return False, "fresh"



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

# [harden-gate-git-layer Task1 · tasks 1.1/1.2] 字段校验从「有限枚举」升级为「字段 → 校验函数」。
# 理由：`reviewed_sha` 的值域是「任意 40 位 hex」，装不进 FIELD_ENUMS 的元组——直接往
# FIELD_ENUMS 加字段会让每个真 sha 都判 out-of-domain（= 新锚永远读不到）。
# FIELD_ENUMS 保留为枚举字段的数据源（三 producer 模板契约测试仍按它比对定义域）。
_FULL_OID_CHARS = frozenset("0123456789abcdef")


def _is_full_oid(val):
    """完整 40 位小写 hex OID。

    拒：缩写 SHA（长度不足）、`HEAD` 及一切符号式 revision、大写 / 非 hex 字符。
    只认小写是有意的单一规范形——三个 producer 的锚一律取自 `git rev-parse`（恒小写），
    人手写出别的形态时宁可 fail-closed 报「格式非法」，也不留两种字面表示同一锚。
    ⚠ 40 位 = SHA-1 仓形态；SHA-256 object-format 仓（64 位 OID）会被判非法（design.md
    ADR-1 明文取 40 位，此处照办，作为已知边界登记在 impl-report Concerns）。
    """
    return isinstance(val, str) and len(val) == 40 and set(val) <= _FULL_OID_CHARS


def _enum_validator(allowed):
    def check(val):
        return val in allowed
    return check


# 「本 schema 认识哪些字段」的单一注册表（parse 用它判 field 是否本 schema、并做值校验）。
FIELD_VALIDATORS = {field: _enum_validator(vals) for field, vals in FIELD_ENUMS.items()}
FIELD_VALIDATORS["reviewed_sha"] = _is_full_oid


def parse_ship_gate_frontmatter(text):
    """解析报告 frontmatter 的 ship-gate 状态。返回 (state, error)：
      state: {field: value}（已过 FIELD_VALIDATORS 校验）；{} = absent（无 frontmatter / 无 ship-gate 键）
      error: None（干净）或 (field|'frontmatter', category)
             category ∈ duplicate-key|out-of-domain|bad-type|tab-indent
    D2 只认文件首块：首行须 '---'（去 BOM）；正文 --- 横线不参与。
    D3 坏≠无：absent(state={},error=None) vs 坏(error!=None) 由调用方分流退出码。
    D5 重复键→duplicate-key（枚举全部同名键计数，非取最后一个）。
    [impl-review-fix FIX-1] 只认 ship-gate 直接子键（首个非空子行的缩进层级）；深于该层级的行
    是嵌套子树，跳过不扫（不参与 FIELD_VALIDATORS 匹配）——杜绝 `note:` 下嵌套 design_approved 假过门。
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
    # 缩进深于该层级的行是嵌套子树，跳过不扫（不参与 FIELD_VALIDATORS 匹配，杜绝嵌套字段假过门）。
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
        if field not in FIELD_VALIDATORS:
            continue                         # 非本 schema 字段（外来 metadata），忽略
        seen[field] = seen.get(field, 0) + 1
        if seen[field] > 1:
            return {}, (field, "duplicate-key")
        val = _coerce_ship_gate_value(field, raw)
        if val is _BAD_TYPE:
            return {}, (field, "bad-type")
        if not FIELD_VALIDATORS[field](val):
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


# [harden-gate-git-layer Task3 · ADR-4 · tasks 2.8] `_stale_trigger_hint` / `StaleResult.trigger`
# 已随帧比较整簇退役：触发点诊断原本**依附于帧遍历**（要 sha + subject），帧遍历没了之后，
# 为凑齐这段诊断而保留一条枚举通路，等于把刚砍掉的推断面从后门放回来。且该能力在 code 域
# 从未真正接通过（两个 code 域调用点本就二元解包丢弃 trigger）。
# 取代者 = `emit` 输出 `reviewed_sha`（录下来的常量，打印零推断成本）+ reason 拼出可执行的
# `git diff <reviewed_sha> HEAD -- …`（Task4 接入）。


# [mlh-p5 Task2/D3；Task6 退役 live inline] live 读点分流：frontmatter 有效→state；坏→UNKNOWN(6)；
# absent→None 交调用方走既有无锚语义（**不再回退 inline**）。坏 frontmatter 的退出码映射集中于此
# （越域/重复键/坏语法/类型不符→UNKNOWN，歧义须人裁、防 exit0 重跑死循环）。
def _fail_closed_on_bad(err, label):
    field, cat = err
    # [harden-gate-git-layer Task1 fix1 · F1] 锚字段自身语法非法 ⇒ 走 ANCHOR_INVALID 专属诊断。
    # 背景：三个 live 读点都先经 live_ship_gate_state，坏 frontmatter 在此就 emit 了通用 UNKNOWN，
    # 于是 read_reviewed_sha 里的 CAUSE_ANCHOR_INVALID 分支在生产路径上永不执行——撞门者拿到的是
    # 「坏 frontmatter」这句通用话，没有 cause_category、没有「订正为完整 commit OID」的指引，
    # 直接违反 Compliance「五类失败原因各给可行动诊断」。抛 GateIndeterminate 由 main() 唯一映射点
    # 统一转 UNKNOWN(6)+cause_category（MUST NOT 在此自行 emit，否则退出码映射散成多处）。
    if field == "reviewed_sha":
        raise GateIndeterminate(
            f"{label} 报告的 ship-gate frontmatter 中 reviewed_sha 值非法（类别={cat}）",
            CAUSE_ANCHOR_INVALID)
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
    design_stale, _design_freshness = is_stale(
        root, str(report.relative_to(root)), "design", change)
    if design_stale:
        # 默认处置**只**推荐重跑设计门——MUST NOT 在此提 `checkpoint(impl-review)`：
        # 该 subject 豁免已随帧比较退役，写进指引等于教撞门者做一件不起作用的事。
        # [Task3] 结构化触发点随帧遍历退役（ADR-4）；锚值可见性由 Task4 的 emit 补 `reviewed_sha`。
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
    # [mlh-p5 Task6 D1] live 只读 frontmatter（inline 回退已退役）：verify 优先（PASS→'pos'/
    # FAIL→'neg'）；坏→UNKNOWN(6) 已在 verify 早检 emit；absent→None→STEP_IN_PROGRESS（无锚语义）。
    vf_front = live_ship_gate_state(vf, "verify")
    if vf_front is not None:
        vv = vf_front.get("verify")
        v_state = "pos" if vv == "PASS" else "neg" if vv == "FAIL" else None
    else:
        v_state = None                           # absent → 无锚 → STEP_IN_PROGRESS
    # [harden-gate-git-layer Task1 · ADR-1] 无结论 ⇒ 不求失鲜：`reviewed_sha` 与结论字段
    # **同一次写入落盘**，故「报告在但无结论」这一合法中间态本就没有锚可读——若仍先跑 is_stale，
    # 该态会被判「缺锚 → UNKNOWN(6)」，把一个正常的 STEP_IN_PROGRESS 变成判定不能。
    # 次序改为与上方 code-review 读点一致（先定结论、再求失鲜）。原 OV-2 关心的「未闭合结构
    # 提示不被 stale 分支吞掉」由下面 STEP_IN_PROGRESS 分支自带的 hint 承载，语义不丢。
    if v_state is None:
        emit("STEP_IN_PROGRESS", EXIT_OK, "sdflow-done",
             "verify-report.md 在但无锚行 → 该步进行中，重跑"
             + _unclosed_frontmatter_hint(vf))
    v_stale, v_fresh = is_stale(root, str(vf.relative_to(root)), "code", change)
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
    # ── final：active 存在 + verify PASS → 收尾未完（绝不 SHIPPED）─────
    # [spec-review-amendment H1/HRTG-1] active 目录仍在 = archive 尚未发生（真 archive 移走
    # active）→ 本态至多「待收尾」。真 SHIPPED（归档后）由 decide 开头的 D3 短路识别
    # （active 缺席 + base 树可达 + archived verify=PASS 锚）。旧逻辑凭 archive glob 存在性
    # 判 SHIPPED 会被旧/同名 archive 误触发（HRTG-1 假 SHIPPED），故 active 存在时不判 SHIPPED。
    handoff = (cdir / "hand-off.md").is_file()
    emit("RUN_VERIFY", EXIT_OK, "sdflow-done",
         f"verify PASS，收尾未完（hand-off={handoff}；archive+merge 由 sdflow-done，"
         "归档后 SHIPPED 由 gate 短路识别）", freshness=v_fresh)


# [harden-gate-git-layer Task1 · tasks 3.6 · design.md 五行表] 每类原因给**各自可行动**的补救动作。
# MUST NOT 用一句「git 调用失败」打天下——五者的补救动作完全不同，而 UNKNOWN 在 /sdflow-ship
# 链序里的处置正是「停并转述 reason」，reason 空洞 = 撞门者被裸退出码打发。
_INDETERMINATE_ADVICE = {
    CAUSE_GIT_UNAVAILABLE: "git 不在 PATH 或不可执行 → 检查环境、安装 git 后重跑",
    # [T194] 上界值**插值引用同一常量**，MUST NOT 硬编码字面量——两者天然漂移
    # （改 GIT_TIMEOUT_SECONDS 而忘了改文案 ⇒ 撞门者按错误的秒数去判断是不是真挂起）。
    CAUSE_GIT_TIMEOUT: f"git 调用超时（>{GIT_TIMEOUT_SECONDS}s）→ 检查磁盘或网络文件系统是否挂起",
    CAUSE_ANCHOR_MISSING: "该报告产出于本次门禁硬化之前（无 reviewed_sha 锚）"
                          " → 重跑对应评审补锚（结论字段与 reviewed_sha 须同一次写入落盘）",
    CAUSE_ANCHOR_INVALID: "reviewed_sha 不是完整 40 位小写 hex（缩写 SHA / HEAD / 坏值均不接受）"
                          " → 人工订正为被批准盘面的完整 commit OID",
    CAUSE_ANCHOR_UNRESOLVABLE: "reviewed_sha 在本仓解析不到 commit 对象"
                               " → 可能 force-push 改写了历史，需人工排查该锚指向何处",
    CAUSE_READ_FAILED: "读取失败（仓损坏 / 权限）→ 检查仓完整性",
}


def _indeterminate_reason(exc):
    advice = _INDETERMINATE_ADVICE.get(exc.category, "原因未分类 → 人工排查")
    return f"判定不能：{exc.cause}。{advice}"


def main(argv=None):
    p = argparse.ArgumentParser(description="sdflow-ship 盘面判官（只读）")
    p.add_argument("--change", required=True)
    p.add_argument("--root", default=None)
    a = p.parse_args(argv)
    # [harden-gate-git-layer Task1 · tasks 3.6] `GateIndeterminate` → UNKNOWN(6) 的**唯一**映射点，
    # 且捕获范围是 **main() 整个函数体**（判定不能可发生在任何一步，不只锚读取那一步）。
    # [Task2] `--root` 缺省时的仓根解析**本身就是一次 git 调用** ⇒ MUST 在 try 内：
    # 放在 try 外时「git 不在 PATH」这条最常见的失败会从第一行就逸出成退出码 1，
    # 恰好绕过为它准备的整套诊断（守卫写了、但主路径够不着 = 假绿的经典形态）。
    try:
        root = Path(a.root) if a.root else Path(
            run_git(Path.cwd(), "rev-parse", "--show-toplevel") or Path.cwd())
        decide(root, a.change)
    except GateIndeterminate as exc:
        emit("UNKNOWN", EXIT_UNKNOWN, None, _indeterminate_reason(exc),
             cause_category=exc.category)


if __name__ == "__main__":
    main()
