# Proposal: matt-workflow-integration

## Why

实现段是全流程第二大成本块且近纯 agent 时间：retro 聚合①实证 impl 阶段 1306.6 min、占 31%（30 change / 70.1 hr），而阶段三过设计门后无人类门。现管线 writing-plans → subagent-dev 的成本是结构性「不信任税」（为弱执行模型校准）：计划期预写全量代码（写两遍）、2-5 分钟步长切 8-15 task（派发循环 ≥2N）、重型交接补丁（Interfaces/task-brief/ledger），superpowers 自记翻车账单（42k 字符 dispatch、final-review 修复波贵过全部任务）。2026-07-10 探索会 + 三镜/对抗镜设计评审已裁决混血方案（调研与六问裁决全文：docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md §1-§10），估实现段 token 砍 40-60%，且 ship_gate 零改动兼容（完成判据契约 = 文件名 + `### Task <n>:` 标题 + checkpoint∪复选框，ticket 体不设限，§5 逐行亲验）。

同会产出的两项 mainflow 待议项与本次同属「matt 套件接入主工作流」面，按 fold-vs-defer（workflow 循环固定成本高）圈选并入：T126（wayfinder→ff 衔接契约 + 三段分流入口）、T127（grill 对上游已决分支瘦跑）。另圈 T118（tasks 依赖 DAG 化——阻塞边即其落地，受限并行部分显式移交 Phase C）、T120（expand-contract 宽重构协议——出 ticket 模式的垂直切片唯一例外）、T125（子代理产物落文件交接——新 skill 的 report/review-package 契约即首个实例）。五项批次已赋 `matt-workflow-integration`。

## What Changes

- **新 skill `sdflow-implement`（单 skill 双模式，编排类纯 Markdown）**：
  - **出 ticket 模式**（to-tickets 语义改造）：从 design.md + tasks.md 出 tracer-bullet 垂直切片 ticket（3-6 张，行为级、禁预写代码/文件路径）、显式 Blocked-by 阻塞边〔T118〕、宽重构走 expand–contract 例外〔T120〕；删 matt 原版 quiz-the-user 人类步（阶段三无人类门）；ticket 文件穿 `superpowers-plan.md` 外衣（`### Task N: <ticket 名>` 标题 + ticket 内验收复选框 + 头部 Global Constraints 逐字节 + R-ID 标注 + frontmatter 管线 marker）。**落盘即返回**——不直通执行，保 ship_gate 在出 ticket 后/执行前的三道校验插入点。
  - **执行模式**（subagent-dev 力学 × matt implement TDD 语义）：工作 frontier（首版严格串行）、fresh implementer 子代理/ticket（TDD at pre-agreed seams + checkpoint(`<change>:task<N>-<slug>`) 标签与勾框双写）、每 ticket matt 双轴审（Standards/Spec 并行子代理、各 <400 词封顶；Standards 轴喂 code-checklists/domains = 注入点 B）+ fix→re-review 环、状态词表 DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED（NEEDS_CONTEXT 改从盘面自答）、产物按 report file / review-package 文件交接〔T125〕、Reviewer ⚠️ cannot-verify-from-diff 项由编排层亲自消解。
  - **裁剪**（冗余机制不带入）：无 warm final whole-branch review（冷层 sdflow-code-review 紧随且承重）、无 progress ledger（gate done_tasks resume 结构性覆盖）、无 task-brief 抽取（行为级 ticket 文本即 brief）。
- **ship 原地接入（不 fork）**：sdflow-ship/SKILL.md 链序 RUN_PLAN / CONTINUE_IMPL 两映射改为条件路由（读 config 键 / 盘面 marker）；试验期显式声明「此二态映射以 SKILL.md 链序为权威，gate JSON `next` 提示串（ship_gate.py:724/:750 仍输出 writing-plans/subagent-dev）仅信息性」。**ship_gate.py 零改动**。
- **手动路由，零自动判断（用户显式要求）**：`openspec/config.yaml` 新增可选键 `impl-pipeline: tickets|superpowers`（沿 model-tiers 覆盖段先例，**缺省/非法值一律 superpowers**），仅新出 ticket 时刻读一次；出 ticket 落盘 marker 锁定在途 change，改 config 不影响跑一半的 change；对在途强制换管线属显式越权通道（人工改 marker，git 留痕）。
- **T126 三段分流 + wayfinder→ff 衔接契约**（assets/workflow 规则）：阶段一入口三分——清晰直接 ff / 单 session 模糊 explore / 超单 session 大雾 wayfinder；衔接契约三条 = ff 起手逐区读 map（Destination→proposal 动机+D-5；Decisions-so-far 逐 ticket zoom 决议全文，防 ff「prefer making reasonable decisions」重决歪；Out-of-scope→D-3 假设）+ TG 判命中前置到 chart 写 map Notes + proposal 回链 map。
- **T127 grill 瘦跑**（assets/workflow 规则）：上游 wayfinder 已决分支引 resolution 快速核对即过，新生成/未决部分照常死磕；grill 对象是 ff 烘焙产物 vs 代码 ground truth，与 wayfinder grilling ticket 非冗余，MUST NOT 整跳。
- **试点 A/B（Phase A 判赢材料）**：3-5 个有逻辑面的中型 change 翻 config 键走新管线（implementer 档位钉死 mid，一次只变一个变量），对照同类型历史 change；判据三条结构（retro impl Δ 降 + 冷层 Critical 不升 + 护栏哨兵不恶化），**定性人读拍板、不设数字阈值**；≥1 消费仓验证缺省键路径（dogfood 盲区）。
- **文档同步**：README Skills 列表增行、CLAUDE.md 托管块禁 /clear 句补 sdflow-implement（经 assets 源）；docs/ 历史快照不回改，活文档全量表述同步归 Phase B。

## Capabilities

### New Capabilities

- `impl-orchestration`：tickets 实现管线的规范性行为——手动路由三跳、出 ticket 契约（垂直切片/阻塞边/外衣文件名/双写完成信号）、执行契约（串行 frontier/状态词表/文件交接/双轴审+注入点 B）、机制裁剪边界、试点与回退。

### Modified Capabilities

- `spec-workflow`：「阶段三过设计门后连续自动跑到 merge」需求的实现段从固定 `writing-plans → subagent-dev` 改为可选管线（缺省不变）；新增「阶段一讨论三段分流与 wayfinder→ff 衔接」「grill 对上游已决分支瘦跑」两条需求。

## Success Metrics

| 指标 | 基准 → 目标 | 度量方式 |
|---|---|---|
| 试点 change 实现段墙钟 | 同类型历史 change impl Δ 中位（retro per-change 明细表现成列）→ 明显下降且方向一致（不设数字阈值，n=3-5 定性拍板） | `python3 sdflow-retro/scripts/retro_report.py` 再生后人读对照；change 类型分桶配对 |
| 每 change 派发循环数 | 旧路径估 18-35 次（8-15 task × implementer+reviewer + fix + warm 终审）→ 估 9-20 次（3-6 ticket × implementer+双轴审 + fix） | 试点 change 的执行模式逐 ticket 记录 dispatch 计数进 code-review-report / hand-off |
| 质量护栏（熔断哨兵） | 冷层 code-review Critical/严重 findings 相对同类型基线不升；done verify 不新增 FAIL | 试点期每 change 冷层报告严重度对照；恶化即停试点回退（config 键回缺省） |

## Non-Goals（不在本次范围）

- **不 fork sdflow-ship、不做 sdflow-ship2**。可证伪假设：链序两映射的条件路由足以承载双管线；若实施中发现 ship 主体需要超出两映射的管线分支逻辑，假设证伪 → 重议接入设计（仍不 fork，先看 gate 侧方案）。
- **不改 ship_gate.py（含 :724/:750 emit 提示串）**。可证伪假设：文件名外衣 + `### Task <n>:` 标题 + checkpoint/复选框契约足以零改动兼容，链序权威声明足以压制弱模型照 next 串误路由；若试点实测 gate 对 ticket 体误判（假 UNKNOWN/假✅）或误路由实发，假设证伪 → emit 串小改从 Phase B 提前进本 change。
- **不做 frontier 并行**（T118 的受限并行部分）。gate 完成窗口 = 当前分支 [plan_first_sha, HEAD] 闭区间，每 ticket 分支使 checkpoint 标签合回前不可见、done_tasks 系统性少算——契约级改动，另立 workflow-cost-optimization roadmap 阶段（Phase C），以本 change 判赢为硬前置。
- **不做默认翻转 / 全量文档表述同步 / 终局文件名迁移**（Phase B 毕业清理）。可证伪假设：试验期「文件名说谎」（外衣内是行为级 ticket）不造成排障实害；若试点期间因此误导排障 ≥1 次实发，Phase B 提前。
- **不动 matt / superpowers 任何 skill 内部**（adr/0002 同款边界：复用输出不改内部）。可证伪假设：to-tickets/implement/code-review 语义以「本 skill 内改造重述」方式消费即可，无需上游改动；若发现必须改 matt skill 才能跑通，假设证伪 → 记 issue 与上游沟通，本地以重述覆盖。
- **不做评审编排侧文件交接全面化**（T121 留池——本次只在 sdflow-implement 内落 T125 模式实例）。

## 需求优先级

- **P0**：sdflow-implement 双模式主体 + tickets 契约；ship 链序条件路由 + 权威声明；config.yaml `impl-pipeline` 键 + marker 机制。
- **P1**：T126 三段分流与衔接契约、T127 grill 瘦跑（assets/workflow 规则）；disable-model-invocation harness 语义实测；出 ticket→gate→执行最小演练。
- **P2**：试点 A/B 选样与判赢材料通道；README/CLAUDE.md 托管块同步；setup.sh 重跑。

## 假设（失效影响）

| 假设 | 失效影响 |
|---|---|
| matt tickets 管线（出 ticket/实现/双轴审语义）本仓未实践过，仅约定核读 + 三镜评审 | 试点首 change 即全链实测；跑不通则该 change 改 config 回 superpowers 续跑（在途隔离保证零污染），设计回炉 |
| `disable-model-invocation: true` 的 harness 语义（是否阻断主 session Skill tool 编排调用）未实测 | 若阻断则 sdflow-implement 不写该旗标、只靠 description 收窄触发（对抗镜已判照搬大概率自毁链条，故默认不写，实测仅为确认） |
| 行为级 ticket（无代码可抄）× mid 档 implementer 能产出合格实现 | 失效形态是静默烂实现——由每 ticket 双轴审 + 冷层哨兵暴露；恶化即回退，model-tiers 判据重标另议 |
| ship 主 session 按链序读 config 键/marker 做机械分支足够可靠（gate 不读 config，保零依赖） | marker 兜底在途归属；若首跳误路由实发，考虑把键读取落 resolve 类脚本（机械层固化方向） |

## 开放问题

| 问题 | 负责人 / 截止 |
|---|---|
| 终局文件名迁移取哪案（改 tickets.md + 旧名 fallback + 双存判 UNKNOWN vs 永不改名只改 emit 串） | Phase B 立项时拍板（试点期收集「外衣误导排障」实证） |
| tasks.md 与 tickets 双重分解是否收敛（tasks.md 授权指引向垂直切片靠拢使出 ticket 近机械） | Phase B 议题；本次 tickets 由 tasks.md 派生、tasks.md 仍为需求追溯层 |
| ~~出 ticket 粒度的人工话语权~~ | **已决（grill 拍板）**：A 收窄形制——ff-generation-constraints 独立条款、切片建议节 MAY、消费语义 = 建议非契约（design D9） |

## Impact

- **增**：`sdflow-implement/SKILL.md`（新编排 skill，无 scripts/）。
- **改**：`sdflow-ship/SKILL.md`（链序 RUN_PLAN/CONTINUE_IMPL 条件路由 + next 提示串权威声明）；`openspec/config.yaml`（可选 `impl-pipeline` 键注释段，含 sdflow-init 模板源同步）；`sdflow-init/assets/workflow/workflow.md`（阶段一三段分流行、grill 行瘦跑措辞、阶段三行加 config 键脚注不改默认）；`sdflow-init/assets/workflow/ff-generation-constraints.md`（ff 起手读 map 衔接契约）；CLAUDE.md 托管块禁 /clear 句（经 assets 源）；README Skills 列表。
- **零改动**：`sdflow-ship/scripts/ship_gate.py` 及其测试；matt / superpowers 全部 skill；workflow.md 阶段三默认口径。
- **依赖**：matt 套件（to-tickets/implement/code-review 语义源 + tdd/grilling）运行时已装；superpowers 保留为缺省管线。失败模式与降级见 design.md（D-4）。
- **圈选池项**：T118（DAG 部分落地，并行移交 Phase C）、T120、T125（实例落地）、T126、T127——批次已赋，done 收尾按批次处置。
- **技术栈触发**：TG-01/02/03 不命中（纯 Markdown 编排 + 配置注释，无领域清单选用）；TG-18 未命中（无自动化测试面，gate 零改动故其既有测试不动，验证靠实测演练 + 试点）。

## Compliance（合规声明）

- **adr/0002**（gstack 边界：复用输出不改内部）：遵守并外推——matt / superpowers skill 均只消费语义、不改内部；本地改造（删 quiz-the-user、双轴审注入）以 sdflow-implement 内重述实现。
- **adr/0004**（ship 窄 scope 不越人类门）：遵守——路由不新增人类门，阶段三仍无人类门连续到 merge；config 键为事前人工配置，非流程中人类门。
- **adr/0006(b)**（gate 驱动、禁 prose 记忆步序）：遵守——出 ticket 模式「落盘即返回」保 gate 校验插入点，步序判定全在 gate；试验期 next 提示串与链序映射的不一致以 SKILL.md 显式声明消歧（gate 判定状态不变，仅 skill 名提示失真，Phase B 根治）。
- **adr/0007**（命名整合）：遵守——`sdflow-implement`（否决 impl 缩写与 ship2 版本号后缀，判例引用见 design.md）。
- **adr/0003 / adr/0005**（部署足迹 / dev checkout 纪律）：遵守——规则改在 assets 权威源，tasks 含 dev checkout 重跑 setup.sh 实测步。
- **敏感数据/信任边界（TG-17）**：不适用（N/A）——纯流程/文档变更。
