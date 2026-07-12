# Proposal: add-sdflow-architecture

## Why

AI 模块级代码质量已可保证，瓶颈上移到系统级：局部最优 ≠ 全局最优。生态已有时间轴规划（sdflow-roadmap）与交付管线（change/ship），但**空间轴缺位**——子系统拆分无规则、contract 无落点、SAD 无载体，新项目起步只能靠散文式讨论。设计方法论已在 `docs/sad/02-sad-skill-design.md` 收敛为自包含蓝本（D1–D5 全部拍定、被否方案留档附录 A），本 change 将其固化为可执行 skill。

## What Changes

- **新增顶层 skill `sdflow-architecture`**（系统架构设计编排器）：输入简单需求 → 五步流程（事实三问采集 → 分歧驱动候选推荐 → 挂产物拍板 → 冷走查 → 交棒）→ 产出 **skeleton-ready SAD**（`openspec/architecture/sad.md`，消费仓项目级单例，**recorder 式直写不经 change 壳**）+ SAD 内嵌**「骨架切片建议」节**（穿越点引用 + 骨架 DoD + 建议 change 名；建议非契约，skill 不代开 change）〔grill-amendment〕。
- **references/ 六件**：`sad-template.md`（十节骨架 + `[假设]`/数值溯源标记语法 + frontmatter 状态机字段）· `decomposition-rules.md`（拆分规则集 R1–R11 + 反模式 AP1–AP4）· `quality-criteria.md`（语义判据 S1–S11 + 机械化拆解表，**真相源**）· `review-lenses.md`（语义残余镜单，投影带 S 编号）· `intake-questionnaire.md`（事实三问）· `checklists/`（横切概念模板 / 质量属性候选库 / 外部依赖典型集 / R4 预期变化类别表）。
- **scripts/ 两件 + tests/**：`sad_lint.py`（v1 最小机械集：十节存在性或显式 N/A、`[假设]` 计数、质量属性排序存在；fail-closed 退出码 + reason_code）· `sad_scaffold.py`（模版脚手架 / 文档状态机 draft→skeleton-ready→validated→frozen / 标记聚合统计）· pytest 测试。
- **README「Skills 列表」同步 + 重跑 `setup.sh`** 建链（新增顶层 skill 纪律）。
- **〔grill-amendment · fold〕`sdflow-roadmap/SKILL.md` description 加一句分工指路**（「新项目起步尚无 SAD 先 `/sdflow-architecture`」）——消解「新项目」入口的现役触发路由冲突；本 skill description 反向指路时间轴。

## Capabilities

### New Capabilities

- `architecture-design`: 系统架构设计能力——SAD 五步生成流程与人机分工、子系统拆分规则（判据流水线 + 反模式黑名单 + 仲裁序）、质量判据三层投影（lint/镜单/人门）、文档状态机与 fail-closed 锁 draft、skeleton-ready 交棒契约（骨架 change proposal）。

### Modified Capabilities

（无——`roadmap-planning` 的 design 模板瘦身列为 Non-Goal 4 延后；`outside-voice-reuse-guard` 三前置校验机制原样复用不改其需求，升档走查复用既有 spec-review 机制、不另造 outside-voice 通道。）

## Impact

- **代码/目录**：新增 `sdflow-architecture/`（SKILL.md + references/ + scripts/ + tests/）；`README.md` Skills 列表；不触 `sdflow-init/assets/workflow/` bundle、不触 `openspec/workflow/`。
- **消费仓布局**：skill 运行时在消费仓创建 `openspec/architecture/`（SAD 单例 live 层）——与 `openspec/adr/`（decision 层）、`openspec/CONTEXT.md`（词汇表）成兄弟；ADR/术语分家写入既有 home，SAD 只引用。
- **技术栈标注（TG-01/02/03 判定）**：Markdown + Python（pytest），**不命中** backend/embedded/frontend 任一领域清单。
- **外部依赖**：codex（**可选**，仅升档多镜时作 outside voice 镜）——调用一律经自制 `~/.sdflow/hack/outside-voice.sh`（自包含、preflight/超时/secret 扫描内建），未装/失败降级 Claude 镜 + 显式提示〔grill-amendment〕。

## Success Metrics

1. **端到端跑通** — 基准 0（无此能力）→ 目标：样例需求走完五步产出 skeleton-ready SAD（含「骨架切片建议」节）— 度量：`sad_lint.py` 退出码 0 且 SAD 含该节（演练记录锚入 tasks 验证）〔grill-amendment 措辞同步〕。
2. **机械断言覆盖** — 基准 0 → 目标：v1 三类断言（节存在性 / 假设计数 / 排序存在）各 ≥2 条 pytest 用例全绿 — 度量：pytest 通过计数。
3. **反假绿锁生效** — 基准无 → 目标：事实三问任一缺失时状态机拒绝 skeleton-ready（锁 draft）— 度量：负路径 pytest 用例（缺项 → 拒绝）通过。

## 需求优先级（TG-19）

- **P0**：SKILL.md 五步流程 + sad-template + decomposition-rules + intake-questionnaire + sad_scaffold（状态机 + 锁 draft）——缺任一 skill 不成立。
- **P1**：sad_lint v1 最小集 + tests + quality-criteria + review-lenses。
- **P2**：checklists/ 领域知识初版（允许薄）+ outside voice 升档调用约定。

## 利益相关方与外部依赖（TG-20）

- **运行 checkout / 消费仓**：经 push → pull → **立即 setup.sh** 生效（新增顶层 skill 的反向窗口纪律）。
- **sdflow-roadmap**：生态位切分已定（design.md=WHY-product / SAD=HOW-structure / roadmap.md=WHEN），其模板瘦身延后（Non-Goal 4）。
- **openspec CLI**：交棒的骨架 proposal 走既有 change 管线。
- **codex CLI**（可选）：升档 outside voice；宿主探测 + 降级不静默。
- **README Skills 列表**：新增条目维护纪律。

## 假设（TG-22）

- **A1** agent 有效 context 预算足以装下「一个子系统完整设计 + 邻居 contract 摘要」（R6 硬约束的常数成立）。失效影响：粒度带 3–7 需重标定。缓解：预算数值放 checklists 可调参。
- **A2** 事实三问对典型项目 owner 约 5 分钟可答。失效影响：采集步卡壳率高。缓解：扩充各问追问提示。
- **A3** 分歧驱动的候选数在真实项目收敛于 1–3 个方案。失效影响：拍板面爆炸。缓解：追加分歧合并规则。
- **A4**〔grill-amendment〕消费仓一仓一系统（SAD 单例路径成立）。失效影响：monorepo 多系统时单例路径冲突。缓解：目录形态天然可演进为 `architecture/{system}/sad.md`（加法演进，不破坏单系统仓）；v1 遇「一仓多系统」声明显式提示不支持并留痕，不硬造布局。

## 开放问题（TG-21）

- **OQ1** L2 子系统设计方法论（步骤二）——负责人：操作者 + 后续 explore；节点：首个 SAD 试点后。
- **OQ2** contract 机械化档位（schema / contract test / fitness function）——节点：骨架 change 落地后。
- **OQ3** S1–S11 完整 lint 投影的排期——由试点数据驱动（「lint 绿但冷走查/人门抓出结构洞」计数）。

## 成本估算（TG-24）

codex outside voice 仅升档多镜时调用：单次约一遍 SAD 全文读 + 结构化输出，粗估 <$1/次，试点期频次低；**默认路径零外部计费**。

## Non-Goals

1. **不做 S1–S11 完整 lint 投影**（仅 v1 最小集）。可证伪假设：最小集足挡结构性假绿——若首个试点 SAD 出现「lint 绿但冷走查/人门抓出结构洞 ≥3 处」即失效 → 追加投影 change。
2. **不做 L2 子系统设计环节**。可证伪假设：skeleton-ready SAD 足以直接起草骨架 proposal——若试点中骨架起草被迫先做子系统内部设计即失效。
3. **不做共变回检仪器脚本**（后验 fitness function）。可证伪假设：阶段边界回检用临时脚本可行——若 ≥2 个项目重复手写同类脚本即失效 → 提为工具 change。
4. **不做 sdflow-roadmap design 模板瘦身**。可证伪假设：SAD 与 roadmap design.md 职责已切（HOW vs WHY）、短期并存无双写——若试点出现同内容双写即失效 → 立即跟进瘦身 change。
5. **不做存量项目迁移编排**（brownfield 共变分析驱动的重构拆分）。可证伪假设：近期试点均为绿地/半绿地项目。

## Compliance

不涉凭证、敏感数据、合规域。遵守仓库 skill 目录约定（`SKILL.md` 为 setup.sh 发现标志）与「新增顶层 skill → README + setup 重跑」纪律。SAD 文档格式为 scaffold（写）/lint（读）/SKILL 指令三方共享 schema，design.md 按 **D-6** 对 `adr/0011`（共享解析器逐消费方语义）、`adr/0018`（机械校验器输出诚实）、`adr/0019`（锚 schema 一致性机械化）、`adr/0002`（边界只复用产出不复用内部）逐条声明合规或豁免。
