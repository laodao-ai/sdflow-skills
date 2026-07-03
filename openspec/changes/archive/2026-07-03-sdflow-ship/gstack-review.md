# gstack-review — sdflow-ship（autoplan 原生运行）

> 2026-07-04 · autoplan 原生执行于主 session（Codex dual-voice 可用）· mode=SELECTIVE EXPANSION（autoplan 固定）
> 偏离声明：①无 gstack 侧 design doc——本仓 OpenSpec design.md（已过 6 分支 grill）即设计文档等价物，跳过 /office-hours 邀约；②G2 批量决策纪律与原生逐问 AUQ 的调和 = 除「前提门」外全部按 autoplan 6 原则自动决策并入审计轨，taste/挑战项集中终门。

## Phase 1 · CEO Review（Step 0 全深度）

### 0A 前提挑战
- **P1「编排层空白是真实痛点」**：成立——本 session 两个 change（footprint/rebrand）均由主 session 人工逐步驱动 5.5→9（约 15 次步进/change），git 历史可证。do-nothing 成本 = 每 change 持续人工步进 + 弱模型漏步风险敞口。
- **P2「确定性台账能兜弱模型漏步」**（adr/0006(b)）：合理假设，有 resolver 先例背书（同模式已在消费仓真实跑通）；残余=弱模型无视 gate 判定（design §七已列，verify 终门兜底）。
- **P3「窄 scope 不越两人类点」**：adr/0004 已完整辩过 wide/narrow/不做三案，不重开。
- **P4（隐含）「chain 不重写子 skill」**：DRY 正确——writing-plans/subagent-dev 是外部资产，重写=接管维护。
- 判定：无明显错误前提；P1/P2 提交前提门供用户确认（唯一非自动决策问）。

### 0B 既有代码杠杆
| 子问题 | 既有资产 | 复用方式 |
|---|---|---|
| 确定性脚本模式 | resolve-workflow.sh（契约头注释/退出码/env 隔离/pytest 沙箱） | ship_gate.py 同构照抄模式 |
| 逐步提交 | checkpoint-commit.sh + `task<N>-` 标签实践 | 完成判据主锚（Q2=B） |
| sibling 脚本调用 | recorder scripts 先例（skill 目录内 scripts/） | ship_gate 同法，不进 ~/.sdflow/hack（非跨 skill 共享） |
| 盘面状态 | reindex「item 池即 ground truth」哲学 | D1 盘面即状态直接承袭 |
| 报告机判 | opsx-init token 先例 | D5 锚行同模式 |
- 无重复建设：编排层确为空白，不存在已有编排器。

### 0C 梦想态映射
```
CURRENT: 人工逐步驱动阶段三     THIS PLAN: /sdflow-ship 一键 5.5→9      12mo IDEAL: 全管线智能编排
(15 步/change, prose 记忆)  →  (gate 确定性台账+门禁传播)        →  (阶段一二半自动+metrics-loop 反馈)
```
朝理想态推进 ✓；gate 契约可被未来宽版复用，不制造反向路径依赖。

### 0C-bis 实现方案对比（autoplan 覆写：自动决策）
```
A[最小可行] prose-only SKILL chain（无 gate 脚本）  S/High  违 adr/0006(b) 硬约束 → 排除
B[选中]     SKILL + ship_gate.py 盘面判官          M/Low   完整+显式+可测（P1/P5）
C[理想架构] python 全状态机 runner（skill 仅壳）    L/Med   排除：chain 子步是模型技能，宿主无 python→Skill 调用通道
```
**AUTO-DECIDED：B**（P1+P5；A 违硬约束、C 有硬不可行点——非 close call，非 taste 项）。

### 0D SELECTIVE EXPANSION 分析
- 复杂度检查：触及 ~9 文件（>8 阈值）→ 挑战成立但豁免有据：超出部分 = T10/T11/T20 债务闭环（设计门/ROADMAP 明示认领），拆出 = 两个 mini-change 流程开销 > 捆绑成本。
- 扩展候选（cherry-pick，中性，终门决）：
  - **E1 dry-run 模式**（只输出 gate 逐步判定与将执行链，不动手）——S；用户预检 + 弱模型演练 + 真实盘面自检。
  - **E2 SHIPPED 摘要附 review readiness 汇总**——S；锦上添花，倾向 defer。
  - E3 resume 播报横幅——XS，属应有文案 → 并入 tasks 2.1 不单列。
- 0E 时序审问：HOUR1 需知=锚行字面单一源（gate 头注释）；HOUR2-3 歧义=「四 SKILL 模型节」边界需 grep 判据（tasks 3.3 补）；HOUR4-5 惊讶=sdflow-spec-review 同段将被 T20（本次）与 T25（已拍板未实施）先后触及，T20 措辞勿预设 T25 结论；HOUR6 愿望=gate 测试 fixture builder（make_change_dir helper）。
- 0F 模式：SELECTIVE EXPANSION 确认。

### 决策审计轨（增量）
| # | Phase | 决策 | 分类 | 原则 | 理由 | 弃项 |
|---|---|---|---|---|---|---|
| 1 | CEO | 实现方案取 B | Mechanical | P1/P5 | A 违 adr/0006；C 宿主不可行 | A、C |
| 2 | CEO | T10/T11/T20 捆绑不拆 | Mechanical | P3/P6 | 明示认领；拆分开销更大 | 三个 mini-change |
| 3 | CEO | E3 并入 2.1 | Mechanical | P5 | 应有文案非扩展 | 单列 |

## 附录：模拟运行备考（降级模式，2026-07-03 子代理产出）

## gstack-review — sdflow-ship（autoplan 广审·自动决策模式）

> 日期：2026-07-03 · 对象：`openspec/changes/sdflow-ship/`（proposal / design / tasks / specs/spec-workflow/spec.md，grill 收敛后版本）
> 模式：**[subagent-only]** 四镜 = plan-ceo / plan-design / plan-eng / plan-devex 各一个 fresh Claude 独立声部 + 主审在场全深度接地审（读 setup.sh / sdflow-done / sdflow-code-review / sdflow-spec-review / checkpoint-commit.sh / workflow.md / 两份真实归档 + git log ground truth）。
> 改动建议均标注落点（文件/任务号），供 spec-review Step3 以 `[gstack-amendment]` 回流；本报告不直接改四件套。

### 0. 偏离声明（自动决策替代无人交互步骤）

| 偏离 | 理由 |
|---|---|
| Codex 双声部未跑（各 phase 标 [subagent-only]） | 环境无 codex 会话预算（4×10min 超时窗）；autoplan 降级矩阵允许 subagent-only；且 Phase C（跨模型镜）本就是本仓待建能力 |
| 四声部并行而非逐 phase 串行 | autoplan 规定 Claude 声部 "NO prior-phase context, truly independent"；串行的唯一意义是给 Codex prompt 注入前 phase 摘要——Codex 缺席则串行无增量。主审自身的合成按 CEO→Design→Eng→DX 顺序完成 |
| 前提门（Premise Gate）自动通过 | 本代理被禁 AskUserQuestion；前提逐条评估见 §1，存疑前提转为 finding（H8/M10）而非阻塞；最终拍板归设计 HARD-GATE（本报告决策登记区） |
| 不调 gstack bin（restore-point / review-log / telemetry） | adr/0002 边界：写 `gstack-review.md` = 复用产出物（合法）；调 gstack 内部 bin = 依赖内部（非法） |
| Phase 2（design）未因"无 UI"跳过 | 调用方指定四镜全跑；将"UI 面"映射为开发者可见信息面（gate 双输出/退出码/停机文案/SHIPPED 摘要），与 DX 镜分工：design 审信息结构，DX 审旅程与误路由 |

### 1. Phase 1 — CEO（战略与 scope）

**前提挑战**（0A）：
- P1 编排层空白是真实摩擦 → **有效但未量化**；方向由 adr/0004+adr/0006 双 ADR 撑，弱模型漏步是结构性风险类别，不苛求量化。
- P2 机器注释锚点 > 自然语言结论行 → **有效，有实证**（本审核验：`结论：**PASS**`、`☑ **建议进 \`/opsx-done\`**` 两份真实存档均带加粗/反引号，正则 miss 为已发生事实）。
- P3 checkpoint 标签可作完成判据主锚 → **有效但有两个残余洞**（→ C2 窗口污染、M10 prose 遵从张力）。
- P4 盘面即状态 → **有效**（reindex 同构先例）；D9 以 git 历史推状态是新增复杂度，边界须钉死（→ C1/DR-3）。
- P5 编排必要性的真实验证时点 → proposal Success Metric #2 **已要求**沙箱演练驱动（同 rebrand 先例，CEO 镜此处误读），但 **tasks 无任何任务承接该 metric**（→ H8）。

**存量杠杆图**（0B，节选）：拒跑/门禁传播 ≈ resolver 的"显式降级不静默"模式；锚行 ≈ sdflow-init marker token 先例（rebrand 已实证 token 抗漂移）；台账单测 ≈ recorder 系 pytest 惯例；`--change/--root` 入参 ≈ buglist.py 契约惯例。复用充分，无重复造轮。
**Dream delta**（0C）：本 change 后阶段三三层皆备（设计层连续✅→编排层连续✅→跨模型镜❌Phase C）；12 个月理想差的只剩 Phase C 与 metrics-loop，路线健康。
**NOT in scope**（确认合规）：不越 grill/设计门（D7 = adr/0004 红线机判化，本审确认无越界条款）；不改 superpowers 本体；无宽版管线。
**CEO 声部 findings**：1 critical（裁定后降级转 H8，见已裁掉区 X1）、1 high（→M10）、1 medium（→L4 附近，MVP 取舍记录 →L7）、1 low。

```
CEO 六维（Claude 声部 / 主审 / 共识）[subagent-only]
  前提有效?          部分   部分   CONFIRMED(P1 未量化,P5 任务缺口)
  对的问题?          是     是     CONFIRMED
  scope 校准?        窄内偏大 合规  CONFIRMED(红线合规;一次性交付量由 H8 演练任务对冲)
  替代方案充分?      不足   够用   DISAGREE→L7(D1/D2/D4/D5 各局部有对比,缺整体 MVP 取舍一句)
  生态/依赖风险?     中     中     CONFIRMED(外部 skill prose 遵从→M10 机械加固)
  6 个月走向?        有条件 健康   CONFIRMED(条件=C1/C2 修掉)
```

### 2. Phase 2 — Design（开发者可见信息面）

声部 findings 3 high / 3 medium / 1 low，与主审合并后主要归入 H3/H6/M6/M8。评分（声部）：状态完备 6 · 文案可行动性 4 · 信息层级 6 · 具体性 4 · 歧义风险 5 —— 一句话：**报告锚行做到了字面级钉死（D5），gate 自身输出却未享受同等严谨度**，这是本 change 内部的不对称。

```
Design 共识表 [subagent-only]
  失败态枚举完备?      否(缺 UNKNOWN 退出码/ERROR 态)   → H3/H6
  文案钉死到模板?      否(3/4/5 态零示例、UNKNOWN 零文案) → H3/H6
  JSON 契约有枚举/类型? 否                              → H6
  陈旧判定可解释?      否(reason 未强制带 sha/path)      → M6
  SHIPPED 摘要有清单?  否(与 done 摘要关系未定义)        → M8
```

### 3. Phase 3 — Eng（架构/边界/测试）

主审接地事实（本审实测）：
- git log 同时含 rebrand 的 `checkpoint(task1-…)..task9` 与 footprint 的 `task1..task11` —— **跨 change 任务号复用已是既成事实**；
- 两份真实 plan `### Task N:` 格式吻合 tasks 1.2 的正则、复选框 0 勾（Q2=B 取证复核通过）；
- 两轮设计门拍板措辞不一致（`设计门拍板（2026-07-03）` vs `拍板（2026-07-03 设计门）`）——proposal OQ2"两轮实践均含'设计门拍板'字样"**为假**，恰好反证 D5 弃措辞锚是对的（→M3 顺带修 proposal 注记）；
- `sdflow-done/SKILL.md:61` `派发 Agent（model: sonnet）`、`:206`（haiku）、frontmatter L7-9、L21、L57-59（P3h 注）均在"模型选择"节外——tasks 3.3 的断言范围盖不到（→H1）；且现状 verify=sonnet 与 adr/0006(c)"sonnet 中档不合格跑 verify"直接冲突，本 change 是修复载体；
- `sdflow-code-review/SKILL.md:7,30,95` 三处"≥2 方案有把握自动选"旧协议残留，tasks 无任务触及（→H2）；
- `~/.sdflow/hack/resolve-workflow.sh` 在位，D4 机制可用；`sdflow-spec-review` Step2 现无串行句（T20 目标确认存在）、Step1.4 有 `spec-review-autoplan` checkpoint 可作串行锚（D6 可落地）。

组件拓扑（design §四）与 chain 关系核对无误；D8 与 sdflow-done 0.1 merge 意图捕获逐字兼容（opt-out 短语透传可行）。Eng 声部 2 critical / 3 high / 2 medium，与主审独立重合率高（C1/C2/H1/H3/H4/M1 双确认）。

```
Eng 共识表 [subagent-only]
  架构合理?      是(台账+meta-orchestrator)  CONFIRMED；D9 边界未想清 → C1
  测试足够?      否                          CONFIRMED → C2(沙箱测不出历史污染)/M1/H4 缺态
  性能风险?      可忽略                      CONFIRMED(每步全量 git log,大仓秒级,不立项)
  安全面?        可信(只读+零 git,D8)         CONFIRMED
  错误路径?      3/4/5 扎实;UNKNOWN/SHIPPED/ERROR 缺 CONFIRMED → H3/H6
  部署风险?      archive 重入/同名重开误诊    CONFIRMED → H4/L3
```

### 4. Phase 3.5 — DX

声部 findings 2 严重 / 4 中 / 2 低。记分卡：TTHW 6 · 错误信息 5 · 命名 8 · 文档 7 · 升级 6 · 逃生舱 4 · **误路由 3** · resume 9。TTHW：已过门 change = 1 次调用（wall-clock 15-60min 属链内工作量，非 ship 引入）。

```
DX 共识表 [subagent-only]
  触发消歧?        否(gstack /ship、/land-and-deploy 撞车) → H7
  错误信息可行动?   REFUSE_START 混两根因               → H5
  照抄友好?        stdout 混排需现成解析命令            → H6 并入
  逃生舱可发现?    merge opt-out 无官方短语/flag        → M5
  升级路径完整?    hand-off 未点名消费仓还需 update     → L5
  resume 体验?     9/10(D9 人机同权是亮点)              CONFIRMED
```

---

### 5. 合并 Findings（去重 + 对抗裁决后）

**严重度统计：2 CRITICAL + 8 HIGH + 8 MEDIUM + 7 LOW。** 每条附自动决策（6 原则）与落点。

#### CRITICAL

- **C1｜D9 新鲜度无差别套用 design-approved 锚 → 正常链路自锁死**〔主审+Eng 镜双独立命中〕
  D5 把 `design-approved` 列为三锚之一；D9 写"对**每份**门禁报告"套时点法（design.md §五 D9），staleness 判据 = 报告提交后存在触及 `openspec/` 之外的提交。而阶段三 step 6/7 的实现 checkpoint **必然**触及代码路径——首个实现提交后，任何一次 gate 调用的 pre-flight 都会把设计门拍板判陈旧 → NEXT=重跑 spec-review → 撞 HARD-GATE，违反"阶段三无阻塞人类门"与 D7 自身。tasks 1.3 的 D9 四态测试与 spec 三个陈旧 Scenario 全部只举 verify/code-review 例，若按现文实现，测试甚至会把死锁编码为"正确行为"。
  **自动决策（P1 完整性 + P5 显式）**：新鲜度**按锚分域**——`design-approved` 仅对"拍板提交之后、`openspec/changes/{change}/`（proposal/design/specs/tasks 四件套路径）被再次修改"失鲜（设计变了才要求重过门）；`verify=*` / `code-review=*` 维持对非 `openspec/` 提交失鲜。落点：design.md D9 补一句分域规则；spec ADDED R-SS-1 陈旧句加"（design-approved 锚除外，其失鲜域=设计四件套路径）"；tasks 1.3 增反例测试"实现提交后 design-approved 仍有效 / 四件套改动后失鲜"。方案分叉（豁免 vs 分域）→ **DR-1 留门**，推荐分域。

- **C2｜checkpoint 标签收集无 git log 窗口 → 跨 change 任务号污染判假"齐 N"**〔主审+Eng 镜双独立命中，git 实证〕
  本仓 main 历史此刻同时存在 rebrand 的 task1..task9 与 footprint 的 task1..task11 标签。design §三 / tasks 1.2 的"收集 `checkpoint(task<k>-` 去重任务号集"未指定扫描下界：新 change 计划 N≤11 个任务时，全历史扫描当场判"已完成"→ 跳过实现 → 链直进 code-review/verify。verify 终门大概率兜住，但台账自身产出假绿判定，正面违背 adr/0006(b) 建台账的初衷；tmp_path+git init 的全新沙箱测试（tasks 1.3）结构上测不出此病。
  **自动决策（P1+P3，判据客观）**：窗口下界 = `superpowers-plan.md` 的**首次提交 sha**（`git log <sha>..HEAD` 内收集标签；plan 都没提交则完成集=∅）。落点：design §三 step 6/7 补窗口句；tasks 1.2 改写判据、1.3 增"历史含旧 change task 标签"的 fixture（先造伪历史再建 plan）。机械可判 → 直接采纳。

#### HIGH

- **H1｜T11 断言范围盖不住真正派发行 → "零内联模型名"落空，verify 仍钉死 sonnet 与 adr/0006(c) 冲突**
  证据：sdflow-done/SKILL.md:61/206 派发行、frontmatter L7-9、L21、L57-59 全在"模型选择"节外；sdflow-spec-review:93、sdflow-code-review:128 模型节内 "(Opus/Sonnet)" 亦为内联。tasks 3.3/5.2 只 grep"模型节"。
  **自动决策（P1）**：3.3 扩为"全文件模型名清零（指向 model-tiers.md 的引用句除外）"，派发行改为"model: 按规则根 model-tiers.md 强/中/弱档解析（config 可覆盖）"；**verify 派发升强档**（adr/0006(c) 既定合规修正）。5.2 断言范围同步扩为全文件。成本可感 → **DR-4 留门确认**（推荐执行）。

- **H2｜T10 决策协议没落到实际执行方 sdflow-code-review**
  ≥2 方案自动选的执行现场是 sdflow-code-review Step4（阶段三步 8），其 frontmatter:7、L30、L95 三处"有把握自动选"旧协议残留；tasks 4.x 无任务、5.2 断言只查 workflow.md。**自动决策（P1+P4）**：tasks §4 增 4.2——sdflow-code-review 三处按 D3 三级协议改写；5.2 断言加"sdflow-code-review 无'有把握自动选'残留"。

- **H3｜UNKNOWN 态无退出码、无文案模板**〔Eng+Design+DX 三镜命中〕
  design D2 只列 0/3/4/5；UNKNOWN（双通道不可判）是第五个终态，未分配 exit code 极易被实现落到 0（=继续跑，恰是最该停的态）；且零用户文案——UNKNOWN 正是弱模型最易糊弄过去的态。**自动决策（P5）**：exit 6 = UNKNOWN；文案模板钉进 tasks 1.1/2.1：「无法判定实现完成：plan {N} 任务 vs 标签集 {k}/{N}，复选框 {m}/{N}——请人工确认或补齐后重跑」。

- **H4｜archive 后重入被误诊为 REFUSE_START**〔Eng+主审〕
  决策图自上而下求值，SHIPPED 判定在末格；archive 后 `openspec/changes/{change}/` 不存在 → pre-flight 判"先过设计门"，误导。**自动决策（P3）**：终态短路——gate 第一步先查 `openspec/changes/archive/*-{change}/` 存在即出 SHIPPED（含"已归档于 {path}"），再进 pre-flight。落点：design §三 + tasks 1.2/1.3 增态。

- **H5｜design-approved 锚行的写入者错位 + REFUSE_START 根因不分**〔主审+DX〕
  拍板动作发生在 spec-review skill **结束之后**的人类门时刻（由 workflow.md 驱动，ground truth：`checkpoint(gate)` 独立提交、两轮拍板措辞已各写各的），tasks 1.4 却把回写约定只放 sdflow-spec-review/SKILL.md——执行拍板的会话根本不在读它。且 REFUSE_START 把"真没过门"与"过了门但报告是存量旧格式（无锚行）"混为一句。**自动决策（P1+P5）**：①1.4 增补 workflow.md 设计门检查清单行（"拍板回写时 MUST 落 `<!-- ship-gate: design-approved -->`"）+ spec-review 报告模板"[需拍板]区"预置注释占位；②gate reason 二分 `report_missing` / `report_no_anchor`，后者文案直接给出可执行修法（"确认已拍板则补一行 `<!-- ship-gate: design-approved -->` 重跑"——把 D9 的"手改锚行=显式越权通道"从设计文档搬进报错文案）。

- **H6｜gate 自身输出契约缺枚举/类型/ERROR 态/SHIPPED-next 语义**〔Design+DX+Eng 汇流〕
  verdict 取值集、missing/reason 类型、SHIPPED 时 next=null、脚本运行时错误（--change 不存在/非 git 仓）的输出形态均未钉；stdout"首行+JSON"混排对照抄型弱模型不傻瓜。**自动决策（P5，D5 同药）**：tasks 1.1 契约头补"verdict 枚举 × exit code × 首行模板"对照表（含 ERROR=exit 2 保留给 argparse/运行错，与 3/4/5/6 不冲突）+ `--json-only` 开关；SKILL.md 每步给现成解析命令与"verdict=SHIPPED 即停止调 gate"句；单测按枚举断言。

- **H7｜触发词与 gstack /ship、/land-and-deploy 撞车**〔DX 镜，主审复核成立〕
  同机双装是本仓用户常态（adr/0002 前提）；"ship 这个 change / 跑起来"类短语两可。**自动决策（P5）**：tasks 2.1 的 description 首句显式排他（"OpenSpec 阶段三编排器，非 gstack /ship（PR 工作流）"），触发词堆"change / 设计门 / spec-review-report"等专属锚词，弃裸"ship"；沿 rebrand trigger-map 先例在 change 目录留触发消歧记录。

- **H8｜Success Metric #2（沙箱演练驱动）无任务承接**〔CEO 镜裁定后转化〕
  metric 要求"一次 /sdflow-ship 调用在演练 change 上从过门态驱动到 merge 建议"，tasks §5 只有 pytest+grep。**自动决策（P1）**：tasks §5 增 5.3——实现期沙箱演练（可用本 change 自身或构造 fixture change 干跑，人工在场逐 gate 核对输出），留档 `rehearsal-log.md`；真实激活仍归 hand-off（沿 rebrand 模式，不动）。

#### MEDIUM

- **M1｜未提交盘面的新鲜度未定义**〔Eng+主审〕：报告已写盘未提交（done 第三步写、第四步才 commit）时 `git log -1 -- path` 为空，时点法无输入；反向：代码有未提交改动时旧 PASS 不该保鲜。**自动决策（P5）→ DR-3 留门**：推荐 A——带锚未提交报告=最新（时间上晚于一切提交）；工作区存在非 `openspec/` 未提交改动 → 等同陈旧触发重跑（盘面含工作区，`git status --porcelain` 一次查清）。tasks 1.3/1.5 补两态测试。
- **M2｜TG-02 命中判定 = 裸 grep proposal，否定句/引用即误报**：如"TG-02 不命中"字面同样命中。D5 对结论行的教训同构适用。**自动决策 → DR-2 留门**：推荐钉"命中触发（TG）表"的表行格式为机判契约（`| TG-02 |` 行存在才算命中，design §二已有此表先例），零新锚行。
- **M3｜proposal.md T11 段仍是 grill 前口径**：`proposal.md:15` "映射进 config…（缺省值内联保底）"与 D4/spec"规则文件真相源、零内联、config 仅覆盖"矛盾；OQ2 所据事实（两轮均含"设计门拍板"字样）经查为假。**自动决策（P3 机械同步）**：proposal T11 段与 OQ2 补 grill-amendment 注记，四件套口径归一（verify/archive 子代理都会读 proposal，留矛盾=给冷启动子代理埋雷）。
- **M4｜resolver 不可用时 model-tiers 零内联名 → 档位无定义**〔主审+DX〕：D4 删了内联保底，resolve-workflow.sh exit 2 / 未安装时四 skill 无模型可依。**自动决策（P1，反静默守卫）**：引用句补显式降级半句——"resolver 不可用 → 显式告警 + 门禁步（verify/裁决）由主 session 同档执行，MUST NOT 静默降弱档"；tasks 3.3 措辞同步。
- **M5｜merge opt-out 只认自然语言、无官方短语/flag**〔DX〕：**自动决策（P5）**：tasks 2.1 SKILL 模板列 2-3 条官方 opt-out 短语；起跑摘要主动回显"全绿后将自动 merge，如需在 merge 前停请说 X"。
- **M6｜陈旧判定 reason 未强制携带触发依据**〔Design〕：用户视角"昨天 PASS 为何重跑"。**自动决策（P5）**：JSON 契约加 `stale_cause: {commit, path}`，首行人读含"因 {sha} 触及 {path} 判陈旧"。落 tasks 1.1/1.5。
- **M7｜SHIPPED 摘要与 done 摘要关系未定义**〔Design〕：**自动决策（P5）**：ship 摘要=包裹 done 摘要 + 编排层增量字段（5.5 跑/跳、gate 调用次数、D3 自动选/对抗复核/defer 计数、重跑次数）；落 tasks 2.1 模板字段清单。
- **M8｜checkpoint 标签契约对 subagent-dev 的 prose 遵从缺机械加固**〔CEO，Q2 残余非重开〕：主锚成立依赖外部执行器照 prompt 打标签。**自动决策（P2 爆炸半径内）**：workflow.md 步 6 prompt 明确"逐任务提交必须经 `checkpoint-commit.sh task<N>-<slug>`"；checkpoint-commit.sh 加 3 行软校验（step 参数非 `task<N>-`/已知步名时 stderr warn 不阻断）；漏标签的兜底已有（UNKNOWN 停上抛，不猜）。

#### LOW

- **L1** workflow.md 步 8 prompt checkpoint 名 `sdflow-code-review` vs SKILL 实际 `impl-review`（:104）不一致——非 gate 判据，顺路对齐或记 todolist。
- **L2** Codex 侧 `/sdflow-ship` 行为未声明：gate 可跑但 chain 目标（superpowers/gstack）是 Claude 侧资产——SKILL 补一句"Codex 侧仅支持 gate 查询/断点续跑指引"。
- **L3** 同名 change 多次归档时 `archive/*-{change}` glob 取最新目录，语义在 H4 落点顺带钉死。
- **L4** grep 断言是字面检查不验证语义（CEO）——H1/H2 扩范围后接受残余，verify 终门兜底。
- **L5** tasks 6.3 hand-off 未重申"消费仓要用 sdflow-ship 还需 `sdflow-init update`"（新文件 model-tiers.md/workflow.md 行不随 skill 安装走）——补一句，与 sdflow-upgrade 步骤 4 措辞对齐。
- **L6** "重调即续、无需参数"未进用户可见文案——并入 H6 首行模板与停机话术。
- **L7** 缺整体"为何一次性全量而非 MVP 分期"的一句显式记录（CEO）——design §五 补一句即可（实质理由存在：gate 各判定共享盘面读取，拆期反造两次契约）。

### 6. 决策登记区（留设计 HARD-GATE 拍板）

| ID | 问题 | 选项 | 推荐 | 两方后果 |
|---|---|---|---|---|
| DR-1 | C1 修法 | A) design-approved 完全豁免新鲜度 B) 分域失鲜（仅四件套路径变更失鲜） | **B** | A 简单但"拍板后改设计"漏检；B 多一条路径过滤，语义完整 |
| DR-2 | TG-02 机判锚 | A) 钉 TG 表行格式 B) proposal 加 `<!-- ship-gate: tg=… -->` 锚行 C) 维持裸 grep | **A** | A 零新锚复用现结构；B 多一处锚行同步面；C 留误报（"不命中"字样即假阳性） |
| DR-3 | 未提交盘面语义 | A) 带锚未提交报告=最新 + 非 openspec/ 脏区=触发重跑 B) 未提交一律"进行中" | **A** | B 会把 done 正常写盘-提交窗口误判进行中（中断恢复时重跑刚 PASS 的 verify）；A 需一次 porcelain 查询 |
| DR-4 | verify 派发升强档（H1 连带） | A) 本 change 内升（tier 引用落到派发行） B) 只改文档层，派发行另开 change | **A** | A 一步到位但 verify 成本↑（强档缺省 opus）；B 保留 adr/0006(c) 违规现状，T11 白做一半 |

### 7. 已裁掉 / 降级区（反静默压制）

- **X1** CEO 镜 [critical]"门禁机制合并前从未跑真实链路"→ **部分裁掉**：Success Metric #2 已含沙箱演练要求（同 rebrand 先例，非纯事后）；成立的残余="metric 无任务承接"，降级转 **H8**。
- **X2** Eng 性能维度 → 不立项：每步全量 git log 在本类仓库毫秒-秒级；超大仓属消费仓边界，接受。
- **X3** DX TTHW wall-clock 30-90min → 不立项：是链内子步（TDD 实现/评审/verify）的固有工作量，非 ship 引入的摩擦。
- **X4** CEO"scope 内一次性交付量偏大"→ 不改拆期（理由见 L7 落点），以 H8 演练任务对冲风险。

### 8. 决策审计轨（Decision Audit Trail）

| # | Phase | 决策 | 分类 | 原则 | 理由摘要 |
|---|---|---|---|---|---|
| 1 | Eng | C1 采分域方案并留 DR-1 | Taste | P1/P5 | 完整性优先；死锁是客观的，修法有两条 |
| 2 | Eng | C2 窗口=plan 首提交 sha | Mechanical | P1/P3 | git 实证污染，判据客观唯一 |
| 3 | Eng | H1 断言扩全文件+派发行接 tier | Mechanical | P1 | "零内联"承诺 vs 断言范围的字面矛盾 |
| 4 | Eng | H2 补 sdflow-code-review 改写任务 | Mechanical | P1/P4 | T10 落点漏了真正执行方 |
| 5 | Eng | H3 exit 6 + UNKNOWN 文案模板 | Mechanical | P5 | 缺态必须显式，UNKNOWN 落 0 即事故 |
| 6 | Eng | H4 终态短路先于 pre-flight | Mechanical | P3 | 求值顺序问题，一处判断 |
| 7 | Eng | H5 锚行写入者补 workflow.md + reason 二分 | Mechanical | P1/P5 | 执行拍板的会话不读 spec-review SKILL |
| 8 | Design | H6 verdict×exit×模板对照表 | Mechanical | P5 | D5 手法对称施加于 gate 自身 |
| 9 | DX | H7 description 排他+专属锚词 | Mechanical | P5 | rebrand trigger-map 先例直接复用 |
| 10 | CEO | H8 增沙箱演练任务 | Mechanical | P1 | metric 无承接任务=可预见的 verify gap |
| 11 | Eng | M1 推荐 A 并留 DR-3 | Taste | P5 | 两方案各有误判面，A 误判面更小 |
| 12 | Eng | M2 推荐表行契约并留 DR-2 | Taste | P4/P5 | 复用现有结构优先 |
| 13 | CEO | M3 proposal 口径归一 | Mechanical | P3 | 四件套自相矛盾，机械同步 |
| 14 | Eng | M4 resolver 降级句 | Mechanical | P1 | 反静默守卫既有原则的适用 |
| 15 | DX | M5 官方 opt-out 短语+回显 | Mechanical | P5 | 逃生舱可发现性 |
| 16 | Design | M6 stale_cause 进契约 | Mechanical | P5 | 可解释性字段，成本≈0 |
| 17 | Design | M7 SHIPPED 摘要=done 摘要+编排增量 | Mechanical | P5 | 显式优于隐式 |
| 18 | CEO | M8 步6 prompt 强制走脚本+软校验 | Mechanical | P2 | 爆炸半径内、<5 文件 |
| 19 | 全 | X1-X4 裁掉连理由留档 | — | — | 反静默压制 |

### 9. 跨 Phase 主题（高置信信号）

1. **"gate 输出契约未受 D5 同等钉死"**——Design（枚举/类型）、Eng（UNKNOWN/SHIPPED/ERROR 缺态）、DX（照抄友好/循环调用）三镜独立命中 → H3/H6 为本报告修复优先级仅次于两条 CRITICAL 的项。
2. **"新鲜度时点法的边界态"**——主审与 Eng 镜独立命中 C1，Eng/主审命中 M1，Design 命中 M6：D9 内核正确，但**每一个输入边界（锚域/未提交/可解释性）都还差一次钉死**。
3. **"断言范围窄于承诺"**——H1/H2/L4 同构：grep 断言写在哪、真正承重的行在哪，三处都错位。建议实现期把 5.2 断言清单当契约测试对待。

### 10. 结论

机制内核（盘面即状态台账 + 机器锚行 + checkpoint 标签主锚 + 零 git 纯读编排）经四镜对抗**未被击穿**，grill 六分支拍板全部经 ground truth 复核站得住（含 OQ2 依据为假但结论反而更成立的意外收获）。被击穿的是**两处判定输入的边界**（C1 锚域、C2 扫描窗——均为 D9/Q2 拍板产物的残余漏洞，非方案本身）与**gate 自身输出面的契约留白**（H3/H6）。全部 findings 均有明确落点，无需重开任何 grill 分支。**建议：C1/C2/H1-H8 以 [gstack-amendment] 回流四件套后进设计门；DR-1~4 随门一次拍板。**
