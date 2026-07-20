---
ship-gate:
  code_review: pass
---

## code-review 报告 — fix-design-gate-freshness-proxy

2026-07-20 · 主 session 强档裁决 · host=claude · DIFF_BASE=`a92347b`

**一句话**：冷层挖出 **6 条 fail-open**（放行未批准设计改动），全部当场修完并经复审逐条独立复现验证；3 条超出本 change 已批准边界的 defer 入 buglist/todolist。

### 命中范围

栈：Python 确定性脚本。清单：`code-review-base.md` CR-01~09。
⚠️ **领域清单未覆盖**：`code-checklists/domains/` 下仅 `backend*`(DB/HTTP) 与 `embedded*`，对本栈**均不适用** ⇒ 无对应领域 delta 清单。本轮仅覆盖 base + Fowler + 仓内标准，**不宣称「领域标准已通过」**（F13）。

`trivial_shape` → **NOT_EXEMPT**（`behavior-path:sdflow-ship/scripts/ship_gate.py`）⇒ 照常 fan-out。

<!-- sdflow:step1-broad-review v1 mode="native" -->

**gstack/review（Step1，原生）**：scope-drift 命中 1 条（评审 diff 包入库，见 F-K）；完成度无缺口——tasks.md 五组 → 6 票全覆盖，无「建的≠计划的」。

<!-- sdflow:hr-tg v1 hit="TG-17" declared="TG-12,TG-15,TG-17,TG-18,TG-19,TG-25" evidence="设计门本身是信任边界，本 change 扩大其准入面（spec-review 已改判为「门禁放松，非兼容性补丁」）" -->

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

镜阵：领域 1 + **对抗 3**（TG-17 命中 ⇒ 高风险档）+ 历史 1。`mirrors=` 的第三 token `grounding` 按跨层固定词表借用记「第三个 fan-out 镜跑了」，本层该镜实为**历史镜**（其精确身份由下方 `lens="history"` 记录）。

<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="1" truncated="false" -->

<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="5" truncated="false" -->

两站点走 **async 分支**（host=claude ∧ 后台探针 `PROBE_OK` ∧ 主 session 确证），内层 900s（config 缺 `outside-voice.async-timeout-seconds` 键 → 回落默认）。退出码经 `.rc` sidecar 取回，两站点均 `0`。
**context 范围声明（已收窄，非全量 `git diff`）**：`code-voice` 的 context 含代码本体 + delta specs，**排除** `impl-reports/*.md`（implementer 自述，协议明定不可当证据）与 `*review-package.diff`（本 diff 自身片段的副本）——全量含这两类为 281KB，绝大部分是叙述与重复，收窄后 139KB。

### Findings（置信 ≥80；outside-voice 跨模型条目免同族数值滤）

**🔴 致命 1 — 全部已修**

| # | 问题 | 证据 | 处置 |
|---|---|---|---|
| F-A | **merge 帧盲区 fail-open**：`git log --name-only`（无 `-m`）对 merge 提交**不输出任何文件** ⇒ `subs=∅` ⇒ `if not subs: continue` 在触及豁免判据**之前**跳过整帧。把未批准的 `design.md` 改动**只**写进 merge 自身 resolve 出的树，`is_stale` 整体判 `fresh`。附带：Task1 的逐 parent 校验在生产路径上是**死代码** | `ship_gate.py:545,570-572`；对抗镜 A 用**真实 `is_stale`（非 mock）**复现，置信 92；hr-tg voice 独立命中 | **已修**〔impl-review-fix F1-a〕 |

**高 5 — 全部已修**

| # | 问题 | 证据 | 处置 |
|---|---|---|---|
| F-B | **rename 盲区**：`git log --name-only` 默认开 rename 检测，`git mv tasks.md x.md` 只输出目标路径 ⇒ 源路径不进监视集 ⇒ 判 fresh。**直接违反本 change 自己的 delta spec**（明写「`git mv` 迁走 ⇒ 失鲜」），而既有 rename 用例只直调 `blob_pair`、未覆盖 `is_stale` 前置 ⇒ **我们自己的新测试是假绿** | code-voice；仓内 `a92347b` 可复证 | **已修**〔F1-b〕 |
| F-C | **帧枚举失败判 fresh**：枚举仍走 `run_git`（失败返空串）⇒ `git log` 失败 ⇒ 零帧 ⇒ `fresh`。Task1 只把 **blob 读取**换成 `run_git_rc`，**枚举这一半漏了** | hr-tg voice；`ship_gate.py:545-584` | **已修**〔F2〕 |
| F-D | **路径含控制字符逃出监视集**：按行切文件名，含换行/Tab 的 `specs/` 路径被 C-quote 或拆行 ⇒ `startswith(base)` 不命中 | hr-tg voice；`ship_gate.py:545-550,237-250` | **已修**〔F1-c〕 |
| F-F | **单一源没同步到姊妹解析器**：`impl_route.py:parse_blocked_by` 头注释**明写**「口径与 `ship_gate._parse_plan` 一致」，但本次把 gate 收敛进 `FenceTracker` 后未同步 ⇒ **那句注释现在是假的**，两解析器对同一 plan 给出不同段落边界（被隐藏行若恰是唯一未勾项 ⇒ 完成判据侧**假 ✅**） | 对抗镜 C 用仓内真实归档 plan（`archive/2026-07-03-sdflow-ship/superpowers-plan.md:879-922`）实测两版输出不同（task 6 复选框 5→3），置信 80 | **已修**〔F4，改 import 单一源，引不到即 fail-closed〕 |
| F-G | **文件头 D9 契约未同步**：`ship_gate.py:55-62` 仍只写 subject 精确式豁免，未提本次新增的勾选框豁免。该文件头是本文件契约的唯一真相源，既有惯例是每条例外都在「已知不覆盖」区带号登记 | 历史镜，置信 95 | **已修**〔F5〕 |

**中 1 — 已修**

| # | 问题 | 处置 |
|---|---|---|
| F-E | **归一化漏了 CommonMark 缩进代码块与 HTML 注释**：四空格缩进代码块内的 `- [ ]→- [x]` 仍被判豁免。🔴 **同一个面的第三次**——基准 5 把「``` / `~~~` / 四 backtick / **缩进 fence**」并列为有界变体，上一轮补了 `~~~`、漏了缩进这一支 | **已修**〔F3，取**超集口径**（缩进 ≥4 列）而非精确 CommonMark 判定：精确判定依赖段落/列表上下文属无界面。代价「深缩进真嵌套任务项假失鲜」方向保守，已显式登记〕 |

**修复中暴露的连带缺陷（自发现，非镜报）**：修好 merge 枚举后，merge 帧第一次被真正枚举出来，旧的二值 `_plain_content_modification` 把「该 parent 侧无改动」与「形态不合格」折叠成同一个 `False` ⇒ **普通 merge 假失鲜**（反向）。拆成四态 `_parent_path_status` 解决。这是**唯一转红的既有用例**（`test_merge_commit_pure_flip_not_stale`）——**断言逐字未动，改的是代码**（复审已核 `git diff` 中 tests 的删除行仅 5 行注释、零 assert 被删改）。

### 已裁掉（反静默压制 · 连理由留档）

| # | 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | hr-tg voice #1 判 **critical**：精确 `checkpoint(impl-review)` subject 可完全绕过内容检查，任意修改四件套均可过门 | **已登记的接受取舍，非本次引入**。见 `ship_gate.py` 头注释「已知不覆盖」+ delta spec「由此『经豁免的语义级四件套改动不经二次批准即随档 ship』属**已登记的接受取舍**〔grill Q2〕；伪造/手工 subject 绕过属显式越权同权级（git 留痕可审计）」。本 change 的 Compliance 明定「既有 BR-7 精确式豁免 MUST 不受影响」⇒ 动它超出已批准边界。**voice 的判断本身没错，是范围问题**——若要收紧，须另开 change 重新拍板 |
| X2 | 对抗镜 A 低置信项（置信 20）：`design_watched_subs` 按精确字符串匹配，大小写/`./`前缀/子目录同名理论可绕 | 镜自己声明「未构造出与 merge 空帧正交且能实际触发的独立复现（POSIX git 输出天然规整路径）」。**一行带过，可审计不静默丢**；且 F1 的 `-z` 原始字节协议已顺带收紧该面 |

**<80 置信滤除**：本轮无（跨模型 voice 免滤；各镜条目均 ≥80 或已如实归入上表）。

### 修复 / defer 台账

**自动修 7 项**〔impl-review-fix〕：F-A / F-B / F-C / F-D / F-E / F-F / F-G + 连带的四态拆分 + `impl_route` ImportError 原因串（诊断质量）。

**defer 3 项**（超出本 change 已批准边界或纯环境健壮性）：

| ID | 项 | 为什么 defer 而非 fold |
|---|---|---|
| **B19** | `code` 域仍走 `--name-only` ⇒ **evil-merge 漏检**（复审隔离构造实测：merge 自身改 `src.py` ⇒ `is_stale(...,"code")` 返回 `fresh`，代码审后的改动被判新鲜） | 修它要动 code 域失鲜判据，而 design.md 的 **Non-Goals 明写**「改动 code 域失鲜判据（本 change 只动 design 域）」。阶段三无人类门管的是修复与裁决，**不含推翻已批准的设计边界**。按基准 3（面治）应在下一 change 与本次枚举协议一并治 |
| **B20** | git 二进制缺失 ⇒ `FileNotFoundError` 逸出，退出码脱离契约集 `{0,3,4,5,6}` | 全文件级既有缺口，非本 diff 引入 |
| **T190** | `run_git*` 系列无 timeout（挂起风险，非误判） | 同上；置信 40，需先定 timeout 值 |
| **T191** | 评审 diff 包被 `add -A` 带进版本库（~1600 行纯派生内容，随 archive 永久留存） | 仓库卫生，跨 change 的约定问题 |
| **T189** | 🔴 **基准 5 警号**：`_normalize_checkbox_lines` 已**第 4 轮**往同一函数补语法分支（``` → `~~~` → 四 backtick → 缩进 + HTML 注释） | 当前靠「超集口径 + fail-closed + 只加在豁免面」三重围栏止损，方向保守可接受；但复审给出的正解（口径**反转为白名单**：只归一化「缩进 ≤3 列且不在任何 fence/注释内的行首标记」）是结构性改动，宜独立评估 |

**T10 复核**：本轮无「无客观判据的 ≥2 方案」——F1 的枚举协议选型（`diff-tree -m -r --raw --no-renames -z` vs `git log -m`）有客观判据（端到端用例可判），自动选后由复审独立复现验证；F3 的超集 vs 精确口径同样由「精确判定是否需要无界上下文」这一客观判据定夺。

### 复审独立性说明

修复后的复审**每条都在 `HEAD~1` 旧码上跑同一构造做对照**，证明这些洞是真的、不是自证：F-A 旧码 `fresh`/新码 `stale`；F-B 旧码 `fresh`/新码 `stale, shape-unfit`；F-D 旧码 `fresh`/新码 `stale`；F-E 三形态旧码全 `True`（fail-open）/新码全 `False`。**正向未被一刀切**：merge 提交只做纯勾选翻转 ⇒ 新旧码均 `fresh`。

全套件：**2036 passed, 8 skipped, 3 xfailed**，零 failure、零新增 warning。

### 度量锚

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="6" 采纳="3" 裁掉="0" defer="3" 独立="2" sev="致1/高1/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="1" 采纳="0" 裁掉="0" defer="1" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="5" 采纳="4" 裁掉="1" defer="0" 独立="3" sev="致1/高2/中1/低0" -->

**信任边界声明**：数值一致性（`findings`/`采纳`/`独立` 是否与合并池实收数吻合）、分类正确性、roster 完备性、findings JSON 誊写准确，均是主 session 信任边界、**非机械可验**；emitter 只保证给定输入的确定性归约。

### 元观察

**领域镜零发现、两个 outside-voice 出了 6 条中的 4 条。** 这不是领域镜失职——CR-01~09 确实没被违反，代码在清单口径下是干净的。**这批洞全在「git 命令的默认行为」这一层**：`--name-only` 对 merge 不输出、rename 检测吞源路径、文本行协议装不下含控制字符的路径。清单查的是「代码写得对不对」，而这些是「你以为 git 会给你什么、它实际给你什么」。

**同一个面被补了三轮才补全**（`~~~` → `tg02` → 缩进/HTML 注释），且**每一轮都是冷层发现的、没有一次是自查发现的**。基准 5 的警号已经响了，T189 记着正解。

---

### 结论

- ☑ **建议进 `/sdflow-done`**（verify → hand-off → archive → commit → merge）
- ☑ defer 残差已入 buglist（B19/B20）与 todolist（T189/T190/T191），hand-off 会引用
