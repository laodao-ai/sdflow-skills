# Issues 合批路线图（按目标功能重切 + fold-vs-defer 合批建议）

> **定位**：`batches.md` 按「哪个 change 发现的」切批；本文件把待处理项按**目标功能域**重新聚拢，
> 找出「一个 change 清 2-3 批」的合批机会。判据 = BASE-18 fold-vs-defer 防吸积 AND 门
> （`同 capability ∧ 高耦合 ∧ 低增量` 三者皆满足才 fold）。
> 生成于 2026-07-05；数据源 = `todolist.py scan` + `batches.md`。待处理 38 项（bug: B1-B4 FIXED，
> B5 OPEN——存疑→单开，见 §5.2）〔impl-review-fix〕。
>
> **2026-07-07 重划说明（batch-triage-strategy）**：本次重划是**增维度，不是重构**——下方
> 「二、合批建议（AND 门）」的 REC-1/2/3 既有框架**保持不动**（已验证，不重 litigate 其设计），
> 新增「大扫除批候选维度」与之**并列**，并对全部待处理项补做**三元标注**（相关批 / 大扫除批候选 /
> 单开）。三元分类的判据源见 `batch-triage-rules.md`（本仓-local）。同时借这次重划顺手订正两处
> stale 状态（见下）。

## 一、当前待处理 38 项 · 按目标功能

| 功能域 | 项 | 数 | 现所在批 |
|---|---|---|---|
| **G1 记录三件套**（issues.py/recorder） | T1 T2 T3 T4 T5 | 5 | issues-pool-batch-mgmt |
| **G2 Toolkit 安装/解析**（setup.sh/resolver/hook/跨平台/软链） | T6 T12 T13 T14 T15 T16 T17 T18 · T23 T24 | 10 | minimize-repo-footprint · sdflow-rebrand |
| **G3 评审规则层**（spec/code-review/grill 规则） | T7 T8 T9 · T19 | 4 | minimize-repo-footprint · sdflow-rebrand |
| **G4 Gate & checkpoint 契约**（ship_gate.py + 标签） | T26 · T35 T36 · T37 T38 · T43 | 6 | sdflow-ship · ship-gate-hardening-2 · checkpoint-tag-single-source · gate-anchor-line-scoped |
| **G5 Outside-voice 层**（outside-voice.sh） | T30 T31 | 2 | cross-model-outside-voice |
| **G6 观测 & 人读体验**（阶段提示/时长/链接/图表/cosmetic） | T28 T29 · T41 T42 · T50 · T27 | 6 | cross-model-outside-voice · gate-anchor-line-scoped · three-lens-decision-framework · 无批 |
| **G7 init.py 健壮性** ✅**已 ship** | T21 T22 T48 T49 | 4 | sdflow-init-hardening（=`2026-07-06-sdflow-init-hardening`，已归档） |
| **G8 前端 viewer**（engine.js） | T47 | 1 | review-tool-followups |

关键观察：**G4、G6 各横跨 3-4 个来源批**——合批机会所在（批按发现来源切，功能域把同类活重新聚拢）。

## 二、合批建议（fold-vs-defer AND 门）

| 建议 change | 吃掉的批 | 项 | AND 门 | 优先级 | 净效果 |
|---|---|---|---|---|---|
| ★**REC-1 gate & checkpoint 硬化**（=G4）✅**已 ship** | sdflow-ship + ship-gate-hardening-2 + checkpoint-tag-single-source **(3 整批)** + gate-anchor 的 T43 | 6 | 同cap(gate+标签契约)✓ 高耦合(同 ship_gate.py)✓ 低增量(6小项机械)✓ | **P1** | **一 change 清 3 批**（成员批已全部归档：`2026-07-03-sdflow-ship`、`2026-07-04-ship-gate-hardening(-2)`、`2026-07-05-checkpoint-tag-single-source`，T43/T26/T35/T36 收口于 `2026-07-05-gate-checkpoint-hardening`） |
| ★**REC-2 观测 & 人读体验**（=G6） | three-lens-decision-framework **(整批)** + cross-model 的 T28/T29 + gate-anchor 的 T41/T42 + 无批 T27 | 6 | 同cap(人读/观测输出)✓ 高耦合(跨 skill 收尾段)△ 低增量(UX)✓ | P3 | 清 1 整批 + 收编 3 批残片 |
| **REC-3 Toolkit 安装/解析硬化**（=G2） | minimize-repo-footprint(setup 8项) + sdflow-rebrand 的 T23/T24 | 10 | 同cap✓ 高耦合(T18/T24 同 install_into·T14/T23 同 Windows 分支)✓ 低增量✗(10项偏大) | P2 | 清 2 批(残)，**增量大建议再切两半** |

> 注：T13 已按大扫除批判据单拉（见「五、大扫除批候选维度」5.1/5.2，`consolidation-plan.md` 本次重划新增），REC-3 实剩 9 项。本行「10」为原判据未拆分前的历史计数，设计建议本身（AND 门判定、切两半建议）不改。

REC-1+REC-2 联手把 **gate-anchor-line-scoped 整批拆干净**（T43→REC-1，T41/T42→REC-2）、**cross-model-outside-voice 拆两半**（T28/29→REC-2，T30/31 留 G5）。

### 自足、不合（各一个小 change 或随手带）

- **G1 记录三件套**（issues-pool-batch-mgmt，P2·自足）
- **G7 init.py 健壮性**（sdflow-init-hardening，P2·刚建自足）✅**已 ship**（`2026-07-06-sdflow-init-hardening` 已归档；T63/T64 是该批之后新冒出的后续项，非重开）
- **G3 评审规则层**（T7 T8 T9 T19，P3·跨 2 批规则微调，可单开小 change）
- **G5 outside-voice**（T30 T31，P3·自足小）
- **G8 viewer**（T47，单项·随任何前端触碰带）

## 三、主次 + 执行次序

**主 = REC-1**：①最高正确性优先级（含 checkpoint-tag 的 B4 元 bug 上下文 + T43 防 gate 误判，系统镜 silent 失效）②合批收益最大（一 change 清 3 整批）③AND 门三条最干净。

推荐次序（**2026-07-07 状态刷新**：REC-1、G7 均已 ship，下方序号保留作历史记录，非待办）：

1. ~~**REC-1**（P1）— gate & checkpoint 硬化 ← 本轮起~~ ✅**已 ship**
2. **G1 / ~~G7~~** 两个自足正确性批（P2）——G7 ✅**已 ship**（`2026-07-06-sdflow-init-hardening`），G1 仍待
3. **REC-3**（P2）— 但先只做 T18/T24、T14/T23 两对强耦合，其余按 observability vs 所有权/跨平台安全再切
4. **REC-2 + G3 + G5**（P3）— 体验 / 规则 / voice 打磨

## 四、REC-1 成员明细（本轮起的四件套 scope；✅已 ship，明细保留作历史记录）

| 项 | 落点 | 摘要 |
|---|---|---|
| T26 | `sdflow-ship/SKILL.md` | 熔断重试计数脚本化方案探索（gate 零副作用约束下的计数下沉） |
| T35 | `ship_gate.py` | 新鲜度可选纳入工作树 dirty 状态（T33 停置延续） |
| T36 | `workflow.md + sdflow-ship/SKILL.md` | checkpoint 派发指令文案收敛为单一真相源（broad-F2） |
| T37 | spec-workflow delta | Scenario prose 复述标签形状——又一份需人工与 workflow.md/SKILL.md 保持一致的 doc 副本 |
| T38 | spec-workflow delta | Scenario 用词 `<当前change>` 易被误读为须用真实 slug，实际用任意占位 demo |
| T43 | gate producer 模板 | 机器锚收紧为独占 bare line（现带反引号/同行尾注），防未来报告照抄模板致 gate 误判 |

## 五、大扫除批候选维度（新增；cross-ref `batch-triage-rules.md`）

> 本节是本次重划**新增的维度，不是对上方「二、合批建议（AND 门）」的重构**——REC-1/2/3 三条
> 建议、AND 门判据、主次排序**原样保留**（已验证过，不重 litigate）。本节做的事是：在"相关合批"
> 之外，再补一层筛子——把与其余待处理项**正交**、且经 issue 级判据判为**无逻辑面 ∧ 低危 ∧
> 非行为面路径**的项挑出来，走「大扫除批」（一 change 一轮评审、item 粒度一项一 commit）。
> 判据全文见 `openspec/issues/batch-triage-rules.md`（三元分类定义、issue 级判据、行为面路径
> 硬排除、聚合上限、结构化判定记录格式、一项一 commit 协议，均由该文件统一定义，本节只做
> 应用与落盘）。

### 5.1 三元标注速览（按现有分组）

| 功能域/项 | 三元归属 | 依据（对齐 `batch-triage-rules.md` 判据流） |
|---|---|---|
| G1 记录三件套 T1-T5 | **相关批** | 自成一个自足批（`issues-pool-batch-mgmt`），同 capability(issues.py/recorder)∧高耦合∧低增量，AND 门内部自洽，不需要再拆给大扫除批 |
| G2 Toolkit 安装/解析（REC-3 候选，除 T13 外） | **相关批**（REC-3，低增量腿已在「二」标 ✗，须再切两半——沿用既有订正，非本节新判） | 同 capability(setup.sh/resolver)∧高耦合；T14/T23、T18/T24 强耦合成对 |
| **T13**（`opsx-project-init/tests/` → 现路径 `sdflow-init/tests/`） | **大扫除批候选**（详见 5.2 正例） | 与 G2 其余「安装期生产逻辑」项低耦合（纯测试断言补强，不改 install_into/resolver 行为）；落点 `tests/`，非行为面路径 |
| G3 评审规则层 T7 T8 T9 T19 | **相关批**（自足小批，P3） | 同 capability(spec/code-review 规则)，可单开一个小 change 处理，不进大扫除批（规则改动即行为面） |
| G4 Gate & checkpoint 契约（T26/T35/T36/T37/T38/T43） | **相关批**（REC-1，✅已 ship） | 已验证过 AND 门三腿；已归档，不再是待处理项 |
| G5 Outside-voice T30 T31 | **相关批**（自足小批，P3） | 同 capability(outside-voice.sh)∧高耦合∧低增量 |
| G6 观测&人读体验 T27 T28 T29 T41 T42 T50 | **排除**（归相关批 REC-2 或单开，MUST NOT 进大扫除批） | 落点均命中 `BEHAVIOR_PATH_PATTERNS`（`SKILL.md` / `*/assets/workflow/*` / `workflow.md`），详见 5.2 反例 |
| G7 init.py 健壮性 T21 T22 T48 T49 | **相关批**（✅已 ship） | 已归档，不再是待处理项 |
| **T63 / T64**（G7 之后新冒出的 init.py 后续项） | **排除**（逻辑面，归单开——延迟绑定：等下次触碰 `init.py` 时顺手带） | 见 5.2 反例（逻辑面项） |
| **T51 / T52**（`sdflow-done/SKILL.md` gate-checkpoint-hardening 残差） | **排除**（逻辑面，归单开——延迟绑定：等下次触碰 `sdflow-done/SKILL.md` 时顺手带） | 见 5.2 反例（逻辑面项） |
| G8 viewer T47 | **排除**（行为面路径硬排除）〔impl-review-fix〕 | 落点 `sdflow-init/assets/workflow/tools/engine.js`，精确命中 `*/assets/workflow/*`——与 T50/T41/T42 同类硬排除理由，非"存疑从严"弱框架；归属结论不变（单开，随任何前端触碰带） |
| **T54**（`workflow 度量/grill amendment 存活率`，2026-07-06 新增） | **排除**（逻辑面，归单开——延迟绑定：等下次触碰 workflow 度量口径时顺手带） | 新增度量口径本身即新逻辑面（非纯记录），非纯 docs/tests，MUST NOT 入大扫除批 |
| **T55**（`lens_metric_aggregate.py` 聚合器健壮性，2026-07-06 新增） | **排除**（逻辑面，归单开） | 落 `sdflow-retro/` 脚本代码，改「glob 空表 vs archive 不存在」的区分逻辑 + site 值截断分组，均是解析/判定逻辑变更，非纯 tests |
| **T58**（`sdflow-retro/lens_metric_aggregate` fence-aware tilde fence，2026-07-06 新增） | **排除**（逻辑面，归单开） | 落 `sdflow-retro/` 脚本代码，新增 fence 解析分支（CommonMark `~~~`），是解析逻辑扩展 |
| **T59**（`sdflow-retro/retro_report+lens_metric_aggregate` 阈值硬编码提共享常量，2026-07-06 新增） | **排除**（存疑→单开，fail-closed） | 触 `sdflow-retro/` 脚本代码，虽形态是 refactor（提取共享常量），但触碰两处判定阈值的读取路径，边界存疑，按 fail-closed 默认排除，MUST NOT 标候选 |
| **T60**（`sdflow-retro/retro_report` `_run_git` returncode 检查，2026-07-06 新增） | **排除**（逻辑面，归单开） | 落 `sdflow-retro/` 脚本代码，新增 returncode 判定分支（区分 git 失败 vs 真无提交），是逻辑面变更 |
| **T61**（`sdflow-retro/retro_report` 死 except 移除+注释订正，2026-07-06 新增） | **排除**（存疑→单开，fail-closed） | 触 `sdflow-retro/` 脚本代码，移除 except 分支牵动错误处理路径，边界存疑，按 fail-closed 默认排除，MUST NOT 标候选 |
| **T62**（`sdflow-retro/retro_report._run_git` 失败节流去重，2026-07-06 新增） | **排除**（逻辑面，归单开） | 落 `sdflow-retro/` 脚本代码，新增去重/节流逻辑（同一 subcmd 失败去重或按 sha 聚合），是逻辑面变更 |
| **T56**（`trivial_shape.py` / workflow-cost-opt Leg1 判器残余，2026-07-06 新增，OPEN） | **排除**（双重命中：行为面路径+逻辑面）〔impl-review-fix〕 | 落点 `*trivial_shape.py`，精确命中 `BEHAVIOR_PATH_PATTERNS`；且内容是判器逻辑补强（tests/ 免检范围收紧、盖 conftest/`__init__`/`tests/plugins/*`），属逻辑面变更，双重排除 |
| **T57**（`workflow/model-tiers` 档位矩阵新增「升级档」，2026-07-06 新增，OPEN） | **排除**（双重命中：行为面路径+逻辑面）〔impl-review-fix〕 | 落点 `sdflow-init/assets/workflow/model-tiers.md`，命中 `*/assets/workflow/*`；且内容是新增档位矩阵设计（功能增强），属逻辑面变更，双重排除 |

### 5.2 Worked example（正反齐全，Q1 路径守卫落地）

**反例 A——行为面路径硬排除（内容 cosmetic 但落点命中 `BEHAVIOR_PATH_PATTERNS`）**：

- `{T50 · sdflow-spec-review/SKILL.md 决策登记区 ASCII 框 · 为何无逻辑面：纯排版对齐，无分支/无契约变化 · 低危证据：单文件、改动范围 6 行以内 · 生成物/CI/目录跨度检查：无生成物、无重型 CI、单文件 · 归属：排除——落点是 `SKILL.md`，命中 `BEHAVIOR_PATH_PATTERNS`，即便内容纯 cosmetic 也硬排除}`
- `{T41 · sdflow-spec-review/SKILL.md + sdflow-code-review/SKILL.md（评审结束输出可点击链接） · 为何看似无逻辑面：纯输出格式增强 · 低危证据：不改判定逻辑 · 检查结果：跨 2 个 SKILL.md，目录跨度已算宽 · 归属：排除——落点是 `SKILL.md`，命中硬排除；且跨 2 文件已不算"个体琐碎"}`
- `{T42 · workflow bundle（generation-process.md / design-diagrams.md / 产物模版） · 为何看似无逻辑面：文档呈现形式增强（加图表） · 低危证据：不改结论 · 检查结果：订正〔impl-review-fix〕——原文实列 2 个精确文件（`generation-process.md`、`design-diagrams.md`），仅第三项"产物模版"是笼统提法，非"完全未列精确文件" · 归属：排除——落点（含精确列出的两个文件）命中 `*/assets/workflow/*`（硬排除即已足够，不依赖"未列精确文件"这条不准确的补充理由）}`

**反例 B——逻辑面项（无论描述多琐碎都排除）**：

- `{T51 · sdflow-done/SKILL.md commit 步 + merge 检查 · 为何有逻辑面：改「暂存策略与 merge 卫生检查对齐」需要新判断分支（tracked 非-openspec 改动的处理时机），非纯文案 · 低危证据：不适用（有逻辑面即排除，不再看低危） · 检查结果：落点 `SKILL.md`，双重命中（逻辑面 + 行为面路径） · 归属：排除——逻辑面项，归单开（延迟绑定，等下次碰 `sdflow-done/SKILL.md`）}`
- `{T52 · sdflow-done/SKILL.md merge untracked 检查 · 为何有逻辑面：baseline 快照+diff 精确区分「本 change 新产 vs 既有 debris」是新判定逻辑，非文案调整 · 低危证据：不适用 · 检查结果：落点 `SKILL.md`，双重命中 · 归属：排除——逻辑面项，归单开（延迟绑定）}`
- `{T63 · sdflow-init/scripts/init.py:inject/_find_all_marker_lines · 为何有逻辑面：fence-aware + start/end 配对校验是新解析逻辑（naive collapse 已因坏case回退，说明此处逻辑真实存在风险） · 低危证据：不适用 · 检查结果：落点 `*.py` 生产脚本，非 `BEHAVIOR_PATH_PATTERNS` 字面命中但含逻辑面已经足够排除 · 归属：排除——逻辑面项，归单开（延迟绑定，等下次碰 `init.py`）}`
- `{T64 · sdflow-init/scripts/init.py:_atomic_write_settings · 为何有逻辑面：原子写唯一名关闭无锁降级路径撕裂，是并发安全逻辑变更 · 低危证据：不适用 · 检查结果：同 T63 · 归属：排除——逻辑面项，归单开（延迟绑定）}`

**正例——真候选（非行为面路径 ∧ 无逻辑面 ∧ 低危）**：

- `{T13 · 精确落点（`sdflow-init/tests/` 下 resolver/setup/init 三个测试文件，4 子项全覆盖）：
  sdflow-init/tests/test_resolve_workflow.py（补 test_unreadable_pointer_degrades_not_crashes 的
  stdout 空断言、test_root_missing_value_exits_64 的 stderr 文案断言）+
  sdflow-init/tests/test_setup_sdflow.py（test_idempotent_rerun 补 hack 脚本/软链目标断言）+
  sdflow-init/tests/test_init.py（`--dev` + `_die` 补 subprocess 测试，对应
  `test_dev_pointing_elsewhere_dies` 一类用例）· 为何无逻辑面：只对既有测试补充断言/覆盖分支，
  不新增任何生产代码路径或判定逻辑，测试本身对错只影响 CI 红绿、不影响运行期用户行为 · 低危证据：
  改动局限于 tests/ 目录，最坏情况是断言写错导致该测试误红/误绿，不会静默改变工具实际行为 ·
  **诚实注（口径不等同 Leg1，非简单同源）〔impl-review-fix〕**：Leg1 `trivial_shape.py` 的
  「无逻辑面」白名单只豁免**新增**的 tests 文件（`git diff` 里全新路径）；T13 改的是**既有**
  test_*.py（补充断言/覆盖分支），字面落在 Leg1 判据里会归入 logic-line 判定、不享受"仅新增
  tests"豁免——这一维度比 Leg1 **更宽**。仍判候选的理由是 batch-triage 自身定义（非机械照搬
  Leg1 形状）：①只动断言/覆盖分支，不新增任何生产代码路径或判定逻辑；②不碰任何生产代码路径
  （install_into/resolver 等）；③坏断言有 CI 兜底（既有 pytest 套件跑红即发现，不会静默改变
  工具实际行为）——三条共同支撑"无逻辑面 ∧ 低危"，但这是本判据下的独立论证，不是"同 Leg1
  仅新增 tests 同源理由"的字面套用 · 生成物/CI/目录跨度检查：
  无生成物、无重型 CI 新增触发面（复用既有 pytest 套件）、目录跨度 3 个文件、同目录
  `sdflow-init/tests/` · 归属：候选——非行为面路径（`tests/` 不在 `BEHAVIOR_PATH_PATTERNS`），
  且与 G2 其余"改安装期生产逻辑"的项（T14/T18/T23/T24 等）低耦合，可独立拉出}`

**存疑→单开的边界示例（fail-closed，非 T13 的反例但同样重要）**：`buglist` `B5`
（`sdflow-ship/tests/test_gate_anchor_scope.py` 契约测试过严致既存红）虽同样落 `tests/` 路径，
但根因栏标「`<待分析>`」——尚未确认改动范围与是否牵动生产判定逻辑，按 fail-closed MUST 纪律
默认排除、标「存疑→单开」，不因为"也是 tests/ 路径"就比照 T13 直接放行。这说明"落点在
`tests/`"是候选的**必要不充分条件**——仍须逐项核对"证据是否充分"，不能路径匹配就自动候选。

### 5.3 诚实标注：本仓大扫除批候选池薄

扫过 `openspec/issues/todolist/` 现存 PROPOSED + OPEN 待处理项全量（含 2026-07-06 新增的
T54/T55/T56/T57/T58/T59/T60/T61/T62，已补标于上方 5.1 表，全部排除——理由见各行；其中
T56/T57 为 OPEN 状态、非 PROPOSED，同样纳入本次扫描并双重命中行为面路径+逻辑面）〔impl-review-fix〕与
`openspec/issues/buglist/` 现存 OPEN 项后，**严格按上方判据（正交 ∧ 无逻辑面 ∧ 低危 ∧ 非行为面
路径，fail-closed 存疑即排除）逐项核对，本仓当前只筛出 1 个真候选（T13）**——候选池薄，这个
数现已有全量表逐项归属背书（非扫了但未落表的口头声明）。原因：本仓多数 debt 落点
天然是 `SKILL.md`（评审/编排规则）、`sdflow-*/scripts/*.py`（工具脚本，几乎都带判定/解析逻辑）
或 `sdflow-init/assets/workflow/*`（bundle 规则），这三类恰是判据要么硬排除（行为面路径）
要么大概率排除（脚本类描述一沾"解析/校验/并发/精确区分"字样即判定含逻辑面）。**这个薄度本身
就是关键信号**——`batch-triage-strategy` 的 proposal 已把"发布判据给下游"排在"本仓 dogfood
验证之后"，而 dogfood 要验证的正是"大扫除批在本仓值不值"；候选池个位数（目前=1）意味着即便
真跑一次大扫除批，规模也撑不起"一 change 清一片"的合批收益叙事——这条实证应当直接喂给未来
判断"要不要发布这套判据给下游仓库"的决策，而不是被这次重划悄悄掩盖。

### 5.4 dogfood 实测注记（T13, N=1, 2026-07-07）

对唯一候选 **T13** 真跑了一次分诊→修复，实测判据。因 N=1，**未套 batch change 仪式**（1 个
todo ID = 1 个 commit，"合批"与"item 粒度串行"无从演练，套仪式属范畴错误），走普通平改。

**关键结论：N=1 结构性触不到发布门。** spec「发布 deferred」Requirement 的发布门 = 两条证据
AND（① 省评审轮次 ∧ ② 未掉安全）。① 需 N≥2（batch 价值全在"合"），T13 单项**结构性无法
产出**——故 T13 dogfood **只能触达 spec 已明确祝福的降级分支**（"候选池太薄/价值边际→退化为
不发布、记本仓注记，亦为有效结论"），触不到发布分支。**据此关掉发布门悬念：判据保留
本仓-local，向下游发布维持 deferred（当前证据指向"退化为不发布"）。**

**实测到的三条（只有"真跑"才得到）**：

1. **pre-diff 判据把 T13 的 scope 高估了一个子项**：接地核对 T13 的 4 子项——1a（`test_resolve_workflow.py`
   降级路径补 stdout 空断言）、1b（`--root` 缺值补 stderr 文案断言）、2（`test_setup_sdflow.py`
   `test_idempotent_rerun` 补重跑后链目标+hack 脚本断言）为**真缺**、纯断言补强、已修；子项 3
   （`--dev`+`_die` 补 subprocess 测试）经查**行为已被 `test_init.py::test_dev_pointing_elsewhere_dies`
   (in-process monkeypatch+capsys) 覆盖**，subprocess 变体冗余，**未做**。→ pre-diff（凭描述+落点）
   判候选时会略高估工作量，接地后须逐子项复核。
2. **安全腿（生成物越界防线）实测守住**：T13 是"改测试→跑 pytest"项，正是 impl-review-fix 那条
   `git add -A` 越界防线针对的精确场景。跑 pytest 后 `.pytest_cache/` 确被生成（`git status --ignored`
   显 `!!`），但 `git status --porcelain`（checkpoint 的 `git add -A` 纳入面）**只含 2 个手写 test
   文件、无任何字节码缓存**——`.gitignore` 的 `__pycache__/`/`*.pyc`/`.pytest_cache/` 三条实测拦下。
3. **N=1 下"一项一 commit"退化为普通单 commit**：无多 item 可串，串行 checkpoint 协议/聚合上限
   均无从演练——再次印证候选池薄使 batch 机制在本仓无实质价值。

**未掉安全 ✓（可测的那半已验），省评审轮次 ✗（N=1 结构性测不了）** → 发布门 AND 不成立，
维持 deferred/退化不发布。此注记 + git log（T13 平改 commit）即 dogfood 可追溯痕迹，未来"发不发布"
的 change 引用本节即可。
