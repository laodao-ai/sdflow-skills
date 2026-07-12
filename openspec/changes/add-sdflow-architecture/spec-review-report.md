---
ship-gate:
  design_approved: true
---
<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="TG-06,TG-08,TG-09" declared="TG-05,TG-06,TG-08,TG-09,TG-10,TG-12,TG-14,TG-18,TG-19,TG-20,TG-21,TG-22,TG-23,TG-24,TG-25" evidence="sad.md 格式为 schema/scaffold/lint 三方共享契约；codex 为可选外部依赖带降级链；文档级+contract 级双层状态机" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="none" findings="21" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="claude-fallback" reason_code="exec-error" findings="8" truncated="false" -->

# spec-review-report · add-sdflow-architecture

> 评审形态：Step1 autoplan **native** 广审（CEO/Eng/DX 三阶段双声全跑，Phase 2 Design skipped——无 UI scope；
> 复用守卫 `outside_voice_guard` reason_code=`none`，复用 autoplan codex outside voice 21 条——其中 broad-eng
> 首条尾部截断不纳池，实入 20）。Step2 规划镜头：领域镜 0（栈不命中 backend/embedded/frontend）、对抗镜 3
> （HR-TG 命中→高风险档：异构宿主 / 契约自洽 / 生态集成）、接地镜 1（弱档机械核验）。HR-TG hit ≠ ∅ →
> 单开领域 cross-model：codex exec 于 hr-tg 位点自爆上下文（exit 1，213k tokens），按协议回落
> claude-fallback（render-prompt 同源、只读），产 8 条含 1 条独家（schema 版本演进）。
> Step3 合并池 79 条原始 → 去重 48 条 canonical → 采纳 36 / 裁掉 8 / defer 4。

## 决策登记区

### [自动决策]（高置信共识自动采纳，默认接受、设计门可覆盖；改动全标 [spec-review-amendment]）

| # | 决策 | 依据 | 落点 |
|---|---|---|---|
| D1 | 状态机重构：文档级去 frozen、显式迁移表、文档×contract 组合不变式（planned 豁免）、validated 回落、回写豁免分流 | 本轮最强共识（双层双声+hr-tg 独立命中） | design 状态机节 / REQ-6 / REQ-9 / tasks 1.3 |
| D2 | 解析层强化：解析函数同置 sad_schema、fence-aware 全正文、假设**集合**对账、facts YAML 子集+坏形态清单、门禁正文实扫、全序与 N/A 文本形态锚、CRLF/BOM 用例 | ship_gate 7 修实证 + 三镜独立命中 | DEC-1/2/3 / 数据模型节 / REQ-1/5/6 / tasks 1.1/1.3/2.2/2.3/1.5/2.5 |
| D3 | `sad_schema` 版本字段 + 版本不匹配独立 reason_code（hr-tg fallback 独家） | 长寿 live 文档 × 全局升级脚本 | frontmatter / REQ-6 / tasks 1.1/2.3 |
| D4 | 分家机械化：scaffold `adr-new`（编号 max+1/fail-closed）、CONTEXT 并入语义、preflight 两级（adr//CONTEXT.md 非 init 保证产物） | 分家原为全 skill 唯一无脚本写入路径 | DEC-7 / REQ-9 / tasks 1.6/4.4 |
| D5 | 宿主中立：Codex 宿主无 fresh 子代理原语 → 显式降级 `walkthrough=self-review-degraded`；走查留痕带执行者字段；wrapper 缺失独立分支 | 对抗镜 critical：setup 双宿主分发无 opt-out 而 spec 零 Codex 提及 | REQ-7 / REQ-12 / tasks 4.2 |
| D6 | 操作者反馈链：人门位置钉死（走查后迁移前，固定议程）、假设处置把手 `--assumption`、reason_code 带 next-step、断点 sad-log（step=N/候选快照）、交棒对话收尾行、拍板一轮打包+方案上限 3、指路句带前置条件 | DX 双声全维 CONFIRMED | REQ-1/4/5/8/10/11/12 / design 序列图 / tasks 4.2 |
| D7 | 幽灵 delta 补正：roadmap-planning 入 Modified Capabilities + ADDED delta spec | archive 对码核验将漏掉真实改动（双镜命中） | proposal / specs/roadmap-planning/spec.md |
| D8 | SM-4 试点 outcome 指标 + OQ4 消费挂点 + OQ5 维护期修订门 | CEO 双声共识：机制级指标可全绿零价值 | proposal |
| D9 | 失鲜矛盾面 sweep：proposal Modified 注 / design D-6 行 / 失败模式行 / design:5 路径 | grill 修订残留旧表述（双镜独立命中同三处） | proposal / design ×3 |
| D10 | 诚实边界补：codex read-only 防写不防读不防出境（升档前提示消费仓敏感明文）；候选真实性归人门；建议节 lint 分支断言 | hr-tg#4 / 镜B F9/F10 | design 失败模式表 / REQ-4/8 |
| D11 | autoplan premise 门（G2 转登记）：前提「AI 模块级质量已保证、瓶颈上移」受理——codex 质疑其无证据锚已由 SM-4 落地为可测指标 | CEO 双声 | 本区 + proposal SM-4 |

### [需拍板]（设计 HARD-GATE 勾选）

- **Q1 试点项目提名**：SM-4 与 Non-Goals 1–5 的证伪钟需要一个已承诺的真实试点。选项：a) mqtt-console 下一阶段（brownfield，需先按 R3/存量形态适配——但 v1 Non-Goal 5 排除了 brownfield 编排，仅可做半绿地用法）；b) 下一个全新项目（时点不可控）；c) 暂缓提名、试点出现时回填（SM-4 保持占位）。**推荐 c**（诚实占位优于虚假承诺；三面后果：系统——证伪钟延迟启动；用户——无额外负担；开发循环——SM-4 在 verify 时以「试点未启动」状态豁免，主判据 = SM-1/2/3）。

### [TENSION]（voice 与主审分歧，绝不静默采纳）

- **T1 monorepo 单例**（codex 标 critical vs 主审裁掉）：codex 认为 v1 拒绝一仓多系统会在 6 个月内阻塞 monorepo；主审立场 = grill Q3 已拍板（A4 假设显式声明 + `architecture/{system}/` 加法演进预留 + fail-closed 提示不硬造），且现有消费仓全部单系统——为不存在场景预建层级违反「刚好够」。**推荐维持主审**（三面：系统——演进无破坏性；用户——单系统仓零噪音；开发循环——多系统需求出现即触发 A4 失效钟，有显式回路）。主次判定：主 = 目标态导向下的「刚好够」，次 = codex 的前瞻布局。
- **T2 outside-voice 单机路径耦合**（codex 标 critical vs 主审裁掉）：codex 建议抽象 review adapter；主审立场 = `~/.sdflow/hack/` 即本生态的标准部署路径（setup.sh 全局安装 + preflight 探测 + 降级链完备），「非标准化托管」前提不适用；wrapper 缺失分支已由 D5 补。**推荐维持主审**。

### [已裁掉]（原始发现 + 理由，可审计）

| # | 原始发现（源） | 裁掉理由 |
|---|---|---|
| X1 | monorepo 单例拒绝过早（codex CEO#1，critical） | → T1（登记 TENSION，推荐维持） |
| X2 | outside-voice 单机耦合（codex CEO#4，critical） | → T2 |
| X3 | facts 答案证据双闸（codex CEO#2） | grill Q4 已拍板诚实边界（质量归人门）；微采纳：问卷追问提示引导证据指针（外部系统问已含文档指针） |
| X4 | DEC-10 建议节移除失溯源（codex CEO#7） | git 即历史 + 骨架 change 自身 proposal 承载内容（Q2c 已拍板 live 层当前态原则） |
| X5 | R9 固定带 3–7 反自适应（codex CEO#8） | R9 自带双向逃逸 + A1 缓解（带值可调参）；微采纳：转写时补「带外需记 ADR 理由」（已入 tasks 3.2） |
| X6 | 首值过晚（codex DX#1） | 三问后 scaffold 即落 draft 骨架文件——首值锚已存在于流程① |
| X7 | 新手模式/延迟露出（codex DX#4） | 深度分层注释 + 价值后置已覆盖主负担；新手模式属 v1 过度工程 |
| X8 | secret-hit 口径矛盾（hr-tg fallback#6） | 矛盾存在于评审 context 摘要笔误，design 本体口径正确（拒发报人工）；SKILL 落笔时以 design 为准 |
| X9 | broad-eng codex 首条（截断） | 输出尾部截断无全文，不猜测不纳池（诚实记录；主题「命名同步」由 D9 失鲜 sweep 旁路覆盖） |

### [defer]（转 todo/开放问题，不入本 change）

- F-D1 共享镜阵编排核（CEO-C6 + codex CEO#6 共识）：三套多镜编排 prose 并存的漂移隐忧——**证伪条件**：出现一次三处同修 → 提取共享编排核（done 阶段 sweep 落 todolist）。
- F-D2 JSON schema 生成工件（codex CEO#5）：跨语言消费方出现时从 sad_schema 常量单向生成（tasks 5.4 已含登记义务）。
- F-D3 试点提名（→ Q1）。
- F-D4 复述检测硬槽全面化（镜B F6 残余）：建议节穿越点引用集断言已覆盖最痛处；其余复述检测列 S1–S11 完整投影目标态。

### 拍板记录

设计门已拍板批准，日期 2026-07-12。Q1 = c（暂缓提名，SM-4 保持占位、试点出现时回填）；T1/T2 确认维持主审；自动决策 D1–D11 全部确认采纳，无覆盖。机判锚见文件头部 frontmatter `ship-gate.design_approved: true`。

## canonical 合并池（48 条，按面分组；全文见 gstack-review.md + 对话审查记录）

| 面 | 条目数 | 命中镜 | 裁决 |
|---|---|---|---|
| 状态机完备性 | 7→1 组 | broad×4 + adversarial + codex×2 + hr-tg | 采纳（D1） |
| 解析层与反假绿锁 | 9→6 | broad×6 + codex×3 + hr-tg×3 | 采纳（D2/D3） |
| 分家与 preflight | 4→3 | broad + adversarial×3 | 采纳（D4） |
| 宿主与执行者 | 3→3 | adversarial×3（含 critical） | 采纳（D5） |
| 操作者反馈链 | 8→7 | broad×6 + codex×4 + adversarial | 采纳（D6） |
| 治理与追溯（幽灵 delta/SM/OQ） | 6→5 | broad×3 + adversarial×2 + codex | 采纳（D7/D8） |
| 失鲜矛盾 | 4→1 组 | broad×2 + adversarial + hr-tg | 采纳（D9） |
| 诚实边界补强 | 3→3 | hr-tg + adversarial×2 | 采纳（D10） |
| 裁掉/张力 | 9 | codex×7 + hr-tg + 截断 1 | 已裁掉区（X1–X9，T1/T2） |
| defer | 4 | 混合 | defer 区 |

低置信项处置（不静默滤除）：镜A#4（CRLF universal-newlines，低置信）→ 已并入 D2 用例族一行；接地镜唯一不符（design:5 路径写法）→ 已修（D9）。

## 图验证（design-diagrams 触发核对）

- 状态机图（TG-09）：本轮重构为**迁移表 + 组合不变式**（表优于图承载完备性）——存在、正确、未过时；
- 序列图（TG-10/12）：已补人门步——存在、正确；
- 组件/依赖图（TG-14）：存在、未过时（sad_schema 新增解析函数职责已在 DEC-1 文字覆盖，图形拓扑不变）；
- 测试覆盖图（TG-18）：tasks 内存在，随修订更新。

## lens-metric（metrics.enabled=true；emitter exit 0）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="18" 采纳="17" 裁掉="0" defer="1" 独立="9" sev="致1/高6/中6/低4" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="23" 采纳="21" 裁掉="0" defer="2" 独立="4" sev="致0/高12/中9/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="claude-fallback" site="hr-tg" findings="8" 采纳="7" 裁掉="1" defer="0" 独立="2" sev="致0/高6/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="19" 采纳="10" 裁掉="7" defer="2" 独立="2" sev="致0/高5/中5/低0" -->

**残余信任边界声明**：分类正确性（finding 归镜）、roster 完备性、findings JSON 誊写准确仍是主 session 信任边界——emitter 只保证给定输入的确定性归约。〔SR-M〕锚已随拍板最终化（2026-07-12）：设计门未翻改任何裁决（Q1=c 不涉 finding 去向、T1/T2 维持裁掉、D1–D11 确认采纳），上方锚行原地确认为最终值，无需重算。

## 收敛口

四件套已按 36 条采纳项全部回流修订（标 [spec-review-amendment]），残余 = 1 项需拍板（Q1 试点提名，推荐 c）+ 2 项 TENSION（T1/T2，均推荐维持主审）。**建议进设计 HARD-GATE**：人工过本报告，拍 Q1 + 确认/覆盖 T1/T2 与自动决策 D1–D11，批准后由主 session 写入 `ship-gate.design_approved` frontmatter。
