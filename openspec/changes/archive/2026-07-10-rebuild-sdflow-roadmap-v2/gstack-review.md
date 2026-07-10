<!-- sdflow:step1-broad-review v1 mode="native" -->
# gstack-review — rebuild-sdflow-roadmap-v2（autoplan 广审落盘）

> **native 佐证（侧信道）**：autoplan 双声真实调用事实——本轮 3 次 `codex exec`（CEO/Eng/DX 各一，read-only，`_gstack_codex_timeout_wrapper 600`）全部 EXIT=0 返回实质 findings；3 个 Claude 独立子代理（agentId acc0b0683db8fc1aa / afe67b61f7465e23f / a4c0da4e4e2ee4f04，sonnet，前台阻塞）各返回结构化 findings。Phase 0 preamble 实跑（BRANCH=feat/rebuild-sdflow-roadmap-v2，REPO_MODE=solo，CODEX: available）。
> 评审对象 = `openspec/changes/rebuild-sdflow-roadmap-v2/` 四件套 @ checkpoint(grill) f9753ce。

## Phase 0 — Intake

- **恢复点**：git checkpoint `f9753ce`（盘面即状态，不另存副本）。
- **UI scope**：0 命中 → Phase 2（design review）跳过。**DX scope**：命中（skill/agent 工具类产品，AI agent 为主用户）→ Phase 3.5 跑。
- **系统审计**：无 TODO/FIXME 残留于触达目录；无 stash；30 天热文件（issues 池/ship_gate/两 review SKILL）与本 change 文件面零交集。gstack design doc 不存在——change 自带 design.md 即问题陈述权威源（office-hours 前置 offer 实质已满足，登记决策区 AD-5）。
- **模式**：SELECTIVE EXPANSION（autoplan override；refactor 缺省 HOLD 的审查严格度同样执行）。

## Step 0 — CEO 主审（主 session）

**0A 前提挑战**：三前提（仪式/价值错配、四处同步面漂移、讨论层脆弱）均有仓内实证（壳 52/55 行 vs 1333 行、mlh-p2 F8 漂移实发、explore 蒸发实录）——仓内成立；**但证据面 scope 见 C1/X1（跨仓与因果）**。
**0B 存量杠杆**：wayfinder 复用（拒平行实现 D4）、recorder 直写先例、design.md 文件名保留（9 处归档引用零断链）、回填助手零改动——无重复造轮。
**0C 梦态**：CURRENT（5 阶段/4 文件/讨论蒸发）→ 本计划（3 阶段/3 文件/wayfinder 耐久层）→ 12 月理想（规划成本≈记录成本、可选机械校验、tracker 可插拔 T123）。方向朝理想 ✓。
**0C-bis 实现方案对比（必产出）**：

| 方案 | 概要 | 工作量 | 风险 | 取舍 |
|---|---|---|---|---|
| **A（选中）** | D1-D7 全量：合并+去壳+wayfinder 分档+footage 分流 | M | 低-中 | 三大实证痛点全根治 |
| B（最小可行） | 仅去壳+review 分档 | S | 低 | 留下同步面漂移与讨论蒸发两个最强实证痛点 |
| C（理想架构） | A + 二件套 / 机械校验层 | L | 中 | D1 已否决二件套（考古层/进度层混 diff）；校验层 Non-Goal 2 可证伪假设待触发 |

推荐 A（P1 完备性；D1-D7 已经三镜+grill 决策）。〔G2 登记：AD-2〕
**0D（SELECTIVE）**：复杂度 check——13 文件 >8 阈值，挑战后判正当（多数为术语机械同步，少改=留陈旧文档）。扩张扫描零新增候选（Non-Goals 已带可证伪假设穷举五项）〔AD-3〕。
**0E 时序拷问**：HOUR1 判别措辞（D3 推荐在）、HOUR2-3 三处口径一致（tasks 已约束）、HOUR4-5 drill 未知数（降级路径在）、HOUR6+ 清点表（grill Q3 已定）。残余：判别措辞最终定稿实施期。
**0F**：SELECTIVE EXPANSION 锁定〔AD-4〕。

### 主 session 独立 findings（S 系）

- **S1〔中〕** 失败模式表缺「matt 套件上游升级致 map/票格式或语义漂移」行——检测/降级路径未定义（现表只覆盖未装/被覆盖）。
- **S10a〔低·流程〕** 与 matt-workflow-integration 的归档串行约束（openspec/specs 能力表尾追加冲突）未在本 change 登记（对侧 design Migration step5 已单侧登记）。
- **S10b〔低〕** CONTEXT.md 本分支新增 footage 词条与 matt 分支新增 ticket 词条同位追加 → merge 冲突预告（保留双方即可，后归档者处理）。
- **S-note** gstack 升级可用（1.58.5→1.60.1）——评审中不升级（保工具稳定），留用户会后决定〔AD-6〕。

## Phase 1 — CEO 双声

### CLAUDE SUBAGENT（CEO — strategic independence）：C 系 7 条

- **C1〔CRITICAL〕「零消费者」前提被扫描集外证据反证**：grep 只跑了本仓归档（n=2 自指样本）。子代理实测机器上 3 个消费仓 8+ roadmap 包（10-michi、mqtt-console、zhws_ops_api），其中 `zhws_ops_api/.../staff-review-report.md:62` 对 requirements.md 有实质消费（判 stale 并行动）；`10-michi/.../specs/ppt-standardization-roadmap/spec.md:8` 有 MUST 场景硬编码四文件存在。正中「目标态论证非现状快照」与「dogfood 盲区」两条既有教训。修法：跨消费仓补 grep 或显式披露证据 scope + BREAKING 限定「仅新 roadmap」。〔待接地镜核验〕
- **C2〔HIGH〕review 分档/路由默认值由 n=2 自相似样本外推**：消费仓含产品型 roadmap（admin console/design system），便宜档默认可能对真实使用面调反。修法：采样真实类型分布或在 Risks 显式披露样本偏斜。
- **C3〔HIGH〕Impact/rollout 静默漏掉多数真实使用面**：skill 全局 symlink——升级即时生效于所有消费仓，8+ 外部存量包未迁移未提及（也不在 Non-Goals）。修法：显式决定「外部包冻结在四件套约定/仅新 roadmap 生效」并确认新逻辑续跑旧包不炸，或排后续迁移。
- **C4〔MEDIUM〕wayfinder 依赖零实证且验证排序在其依赖代码之后**：drill(4.1, P1) 在 SKILL 重写(1.2, P0) 之后。修法：drill 前置或作为 1.2 的门。
- **C5〔MEDIUM·reframe〕本 change 自身是它要修的模式的实例**：7 天仓 31 归档 change 多为流程自指精化；建议 gut-check 下一个最高杠杆动作是否应为外部可见交付。
- **C6〔MEDIUM〕prose 锚+人眼警惕与本仓机械固化哲学（adr/0006）冲突**：可用 maintain_scan 或 skill preflight 机械断言 footage 分流句在场，低成本闭合。
- **C7〔LOW〕design.md 增长的接受判据引用了同 design 判为过长的文件**：建议以编辑频率/稳定性为轴而非 WHAT/HOW。

### CODEX SAYS（CEO — strategy challenge）：X 系 11 条

- **X1** 优化的是文档仪式非规划质量：Success Metrics 全为流程段数/同步面/落盘存在，无决策返工/实施偏差/交付价值维度；n=2 不足证根因；真问题或应重构为「不确定条件下的承诺管理」。
- **X2**「单一源」未实现只是 4→2：≤2 处是允许漂移非消除漂移；应先定义每类事实唯一归属+引用规则再定文件数。
- **X3** 去壳去掉唯一明确生命周期边界，用不可执行 checklist 顶替：soft gate 六个月后=可忽略文本；保留状态记录/审核事件比保留壳更关键。
- **X4** 未实测 wayfinder 变 P0 依赖后才 P1 演练=投资顺序错误：失败降级直接击穿「长讨论 100% 可续」核心承诺；应先真实试点验证跨 session 恢复再迁移。〔与 C4 跨模型共识〕
- **X5** 为 roadmap 特判全局 tracker doc=产品策略泄漏进共享基础设施：需要第二锚本身即集成边界错误信号；替代：每个 roadmap 在自身目录声明讨论根目录，或显式本地适配层。〔挑战 D3〕
- **X6** 分档判据忽略不可逆性/依赖度/失败代价等真实成本因子；跨 session 才升级=信息已开始丢失。
- **X7** 禁引 footage=以禁止可追溯性掩盖双写问题：精炼写入无法保留证据/反例/被拒方案；应区分规范正文与可追溯决策证据，允许受控带类型引用。〔挑战规则 3 扩展〕
- **X8** review 按「产品野心」分档=错轴：应按承诺量/不可逆性/受影响面/外部用户分档，且在结晶前介入。
- **X9** 近细远雾把阶段序号误当信息成熟度：长周期依赖（采购/法规/安全架构）需现在定；应用承诺层级+滚动复盘而非禁写第三阶段。
- **X10** 无产品型实例却宣称支持产品型模板=对工程型过宽对产品型不足；要么本次明确只服务工作流型，要么先产品型试点。
- **X11** 存量迁移+全仓清理=过早规模化：先以一个新 roadmap 完成端到端闭环再决定是否迁旧包。〔与 C3 构成 TENSION：一说漏迁、一说缓迁〕

```
CEO DUAL VOICES — CONSENSUS TABLE
═══════════════════════════════════════════════════════════════
  Dimension                          Claude   Codex   Consensus
  ─────────────────────────────────  ───────  ──────  ─────────
  1. Premises valid?                 挑战(C1)  挑战(X1) CONFIRMED-CONCERN
  2. Right problem to solve?         reframe候选(C5) reframe(X1) CONFIRMED-CONCERN
  3. Scope calibration correct?      漏外仓(C3) 迁移过早(X11) DISAGREE→TENSION
  4. Alternatives sufficiently探索?   基本是    D3 替代(X5)  DISAGREE
  5. Competitive/market risks?       N/A 内部   N/A      N/A
  6. 6-month trajectory sound?       锚衰减(C6) 门衰减(X3) CONFIRMED-CONCERN
═══════════════════════════════════════════════════════════════
```

**Phase 1 小结**：Codex 11 条 / Claude 7 条；共识 3 CONFIRMED-CONCERN、2 DISAGREE（进 TENSION/需拍板）。

## Phase 3 — Eng 双声

### CLAUDE SUBAGENT（eng — independent review）：E 系 10 条 + 3 项已核无恙

- **E1〔HIGH〕「四件套」全仓 sweep 撞两概念**：仓内「四件套」还指 change 四件套（proposal/design/specs/tasks）——`openspec/specs/spec-workflow/spec.md:420,423,424`（gate 失鲜逻辑，活规范）绝不能被 6.1 盲扫误改（proposal 自己声明不触碰 spec-workflow）；且漏了真 roadmap 语境命中 `docs/sdflow-fable5/01-goals-and-rationale.md:153`。修法：sweep 加逐命中语境判读 + 显式排除名单 + 补漏。
- **E2〔HIGH〕命名权竞争**：wayfinder chart 第一步自行命名 destination，而 R4 依赖 sdflow-roadmap 的固定 {name} 构造 footage 路径——slug 不一致风险。修法：SKILL 明确 sdflow-roadmap 先定 kebab-case 名并作为固定根传入，wayfinder 命名步只校验不另起。
- **E3〔HIGH〕footage/map.md 单文件名无再入约定**：R7 补细短讨论若二次 chart 同包 → 覆写 map（毁 Decisions-so-far）或票号冲突。修法：tracker doc + SKILL 定义再入约定（map 归档 or 单 map 分批票）。
- **E4〔MED-HIGH〕claimed-未-resolved 票永久掉出 frontier**：无超时/重认领机制；drill 只测 happy path。修法：tracker doc 加 stale claim 约定 + drill 扩中断恢复。
- **E5〔MEDIUM〕结晶不 gate 未决票**：R6 checklist 三项不含 frontier 空检查；footage 不进 triage、maintain_scan 不扫 → 孤儿 open 票零巡检指回。修法：checklist 增「frontier 空或显式放弃留痕」。
- **E6〔MEDIUM〕task-log 历史引用低估且无「修补 vs 保留」规则**：wco task-log 6 处、mlh 4 处未列；历史 DID 条目应按发生时事实保留，只修 design/roadmap 前向结构引用。
- **E7〔MEDIUM〕setup 重跑爆炸半径更大、人在环更弱**：seed 模板基路径是 `.scratch/`（整个 tracker 约定翻转风险，非仅 Wayfinding 节）；其 Explore 步只查 `docs/agents/`——重跑可能根本不检出本仓定制来给人看 diff。修法：Risk 表如实加剧描述 + 锚句提示「重跑须全量 pre-diff」。
- **E8〔MEDIUM〕drill 测错对象**：4.1 预供目的地路径，测的是 wayfinder 成熟六操作，没测本计划真正的新发明（tracker doc 条件路由从裸请求判档落位）。修法：改造/加一个从真实 /sdflow-roadmap 调用起步的 drill。
- **E9〔LOW-MED〕wayfinder Task 票型与规则 5「只规划不实施」未对齐**：Task 票「做而非决」可能在 roadmap 讨论中产生真实副作用。修法：限定 roadmap effort 内 Task 票为可行性验证 scope。
- **E10〔LOW〕proposal 假设 3 表述失准**：writeback 脚本实读 proposal/tasks/verify-report + roadmap.md，从不读 task-log.md（只发指导片段）；结论仍成立，引文需改精确。
- **已核无恙**：maintain_scan 确不扫 roadmaps/、matt/（5.3 声明成立）；writeback 与近细远雾相容（补细时序保证行存在+缺行 fail 人工）；tracker doc「6 条 bullet」计数精确。

### CODEX SAYS（eng — architecture challenge）：XE 系 7 条

- **XE1〔Critical〕条件分流无可恢复的确定性身份字段**：「隶属声明 or skill 发起」两信号都不持久化；恢复会话只拿 map.md 路径 → 可能在 matt/ 新建票而旧票在 footage/（双根分裂）。修法：map.md 写显式 `Tracker root`/`Effort kind` 字段，续跑只从 map 存根目录派生路径；drill 须覆盖「新会话续跑并新建一张票」。
- **XE2〔High〕「压缩后仍未收敛才升级」在最需要时不可判定**：explore 起步 + memo 可选 → 压缩后新 session 恰缺「此前讨论已久未收敛」的持久状态；R3 只保证有 map 后的恢复。修法：首次探测到跨 session 风险即写最小状态检查点，或该分支 memo 转必需。〔直击 grill Q1 修正案的残余面〕
- **XE3〔High〕结晶可在 wayfinder 未闭环时完成**（同 E5，跨模型共识）：收尾必须要求全票 resolved/显式放弃留痕 + map 标 closed。
- **XE4〔High〕frontier 补细绕过质量门**：R5 只在「三件套完成后」review，R7 补细只记 task-log——真正的架构承诺/验收可能恰在补细时首次落地却不触发重审。修法：定义 roadmap 修订门（补细改范围/不可逆承诺/验收/依赖 → 按影响重审+记录审查覆盖版本）。
- **XE5〔High〕可用性检查硬编码 `~/.claude/skills/wayfinder/SKILL.md` 破坏 Codex 宿主**：本仓双 agent 分发（~/.codex/skills 同装）。修法：宿主中立探测 + 任务分别验证两宿主路由。
- **XE6〔Medium〕迁移缺「旧 requirements §X → design §Y」映射表**：活历史引用逐条处理（改锚或保留+考古注记）；proposal Impact 漏列 task-log.md。
- **XE7〔Medium〕直写协议缺包生命周期/幂等性**：同名包已存在=继续/重规划/覆盖/fork 未定义；至少定义 create/continue/replan 三模式 + 冲突 preflight + 重规划快照策略。

```
ENG DUAL VOICES — CONSENSUS TABLE
═══════════════════════════════════════════════════════════════
  Dimension                          Claude    Codex    Consensus
  ─────────────────────────────────  ────────  ───────  ─────────
  1. Architecture sound?             缺口(E2/3) 缺口(XE1/7) CONFIRMED-CONCERN（路由身份/再入）
  2. Test coverage sufficient?       否(E8)    否(XE1尾) CONFIRMED-CONCERN（drill 测错对象）
  3. Performance risks addressed?    N/A       N/A      N/A
  4. Security threats covered?       N/A(纯文档) N/A     N/A
  5. Error paths handled?            缺(E4/5)  缺(XE2/3) CONFIRMED-CONCERN（闭环/恢复）
  6. Deployment risk manageable?     缺(E1/7)  缺(XE5+XD11) CONFIRMED-CONCERN（sweep 误伤/宿主/升级窗）
═══════════════════════════════════════════════════════════════
```

**Phase 3 小结**：Codex 7 条 / Claude 10 条；4 维 CONFIRMED-CONCERN。

## Phase 3.5 — DX 双声

### CLAUDE SUBAGENT（DX — independent review）：D 系 12 条 · 总分 6.5/10

- **D1〔HIGH〕requirements.md 禁令零逃生舱口**：唯一 BREAKING 条款无 override 路径（对比 D5/D6 都留了口子）。修法：R1 加显式覆盖条款（操作者显式要求时遵从+design 头部注明非默认形态）。
- **D2〔HIGH〕「roadmap 类 effort」判别开放问题设计门前未决**：真实落地靠调用语精确复述（自然语言），不满足可观察可执行门槛。修法：调用语钉死字面量标记/固定字符串匹配，或每次调用传绝对路径。
- **D3〔HIGH〕office-hours 分支连带丢失**：现行 SKILL.md 讨论阶段有 explore/office-hours/brainstorming 三路径；新四件套 grep 零命中，且保留的「产品型」轨道恰失去其唯一前置验证入口——看似重写连带丢失非拍板决定。修法：tasks 1.2/1.4 显式决定去留或 Non-Goals 记弃置理由。
- **D4〔MEDIUM〕gate-0「讨论充分度检查」标准未定义**：旧 5 项 checklist 未列入 1.2 范围——本次专为消灭不可观察判据而做，却在流程最前端留了一个。修法：旧 checklist 搬入或给可观察替代。
- **D5〔MEDIUM〕「N 件套视为整体 plan」的 review 调用负重指令无存活保证**：漏掉则 review 退化为单文件审且无测试可抓。修法：task 1.4 加验收项。
- **D6〔MEDIUM〕结晶过早场景零覆盖**（同 E5/XE3，三方共识）。
- **D7〔MEDIUM〕三处分档默认值无「用户显式覆盖」条款**：本仓 gate 类 skill 严格执行 SHALL 惯例下 agent 可能拒绝用户显式要求。修法：两条 Requirement 各加覆盖+记录偏离理由句。
- **D8〔LOW-MED〕footage 术语无面向用户路标**：修法：footage/map.md 顶部留一行去向说明。
- **D9〔LOW〕指标措辞可能被过度解读**：阶段数下降≠长讨论提速（wayfinder 自身两轮 HITL grilling 起步）；卖点是跨 session 生存性。加脚注。
- **D10〔LOW〕直写无等价 archive 的完成边界**：checklist 可选加 commit 软提示（与 recorder 先例对齐）。
- **D11〔LOW〕setup 重跑失败模式描述或不准**：重跑很可能不覆盖 openspec/matt/ 而是在 docs/agents/ 另起不协调副本——「revert 即回」应降级为存疑风险。
- **D12〔LOW〕验收全是文本存在性检查**：低成本改进——1.2 验收加「示例开场白→期望路由」对照表作自检基准。
- **TTHW**：常见轻量场景 11-13 步 → 5-7 步（去壳+降审，证据扎实）；长讨论场景交互量不减、换来的是跨 session 生存性。

### CODEX SAYS（DX — developer experience challenge）：XD 系 11 条

- **XD1〔High〕首次产出前 ≥6 个未收敛判断**（充分度/长档/类型/野心/近期 1 或 2 阶段/跳审）无强制入场问答或记录格式——建议 agent 先展示确认一张 routing card。
- **XD2〔High〕「必须 review」与「作者可跳过」互相抵消**：「作者」可能就是 agent；跳过应仅限 operator 显式授权，产物状态应为 `review-waived` 不与已审混同。
- **XD3〔High〕review 依赖零失败 UX**：失败表覆盖 wayfinder/grilling/tracker/迁移，独漏 plan-eng-review/autoplan 缺失/失败/无输出/中断——operator 无从知道包是「未审待恢复」还是「已完成」。
- **XD4〔High〕「讨论充分→直接结晶」是不可恢复隐式早退**：无判据、无展示、无回退状态；agent 有尽快交付偏置。修法：要求显示「直接结晶依据」+ 定义结晶后发现关键未知的回退与重审。
- **XD5〔Medium〕tracker 覆盖修复建议不安全**：`git checkout openspec/matt/` 会丢目录内其他未提交修改；应给逐步非破坏恢复流程（diff→备份→重应用→验证）。
- **XD6〔Medium〕无雾路径执行顺序冲突**：一条 Scenario 说 chart 生成 map+票、另一条说无雾「不建 map」——中档 agent 会先建后删/遗留空目录/跳过 breadth check。修法：明确 chart 的未持久化预检步 + 已建文件清理留痕规则。
- **XD7〔Medium〕收尾 checklist 非可判定操作契约**：「相互引用完整」未定义必需链接集/方向/允许的历史引用，失败也不要求报文件行号——agent 可宣称通过而 operator 无法验证。修法：定义检查矩阵+失败输出格式。
- **XD8〔Medium〕新 design 头部模板丢失旧 requirements 核心承载槽**：R2 只强制痛点/目标态/Non-Goals——「核心需求表/验收总纲」只在存量迁移清点表出现，新模板无槽位；新用户会得到看似合规实缺可验收需求契约的 design。修法：R2/design-template 补需求清单与验收门槛槽（产品型/复杂工作流必填或显式占位）。
- **XD9〔Medium〕近细远雾对 3 阶段路线图无决定规则**：近期「1-2 阶段」选择标准未说明、示例只覆盖 4+ 阶段——同一输入三种产出。修法：模板要求写 frontier 选择理由 + 每雾区缺什么信息才能细化。
- **XD10〔Medium〕考古注记不可发现**：只写「历史版本见 git」，无旧文件路径/迁移日期/commit/章节映射。修法：注记带四要素。
- **XD11〔High→部署〕升级不兼容窗口**：P0 重写后 skill 禁 requirements.md，两活包 P2 才迁移——中途 operator 调 /sdflow-roadmap 续护四件套包时 agent 无所适从（兼容/先迁/拒绝未规定）。修法：原子切换或显式格式版本过渡规则。

```
DX DUAL VOICES — CONSENSUS TABLE
═══════════════════════════════════════════════════════════════
  Dimension                          Claude     Codex     Consensus
  ─────────────────────────────────  ─────────  ────────  ─────────
  1. Getting started（步数）          改善↓半    6 判断未收敛 PARTIAL
  2. 判断可观察/可执行?               否(D2/D4)  否(XD1/4)  CONFIRMED-CONCERN
  3. Error messages actionable?      部分(D11)  缺(XD3/5)  CONFIRMED-CONCERN
  4. Docs findable & complete?       缺路标(D8)  缺映射(XD10) CONFIRMED-CONCERN(轻)
  5. Upgrade path safe?              存疑(D11)  不兼容窗(XD11) CONFIRMED-CONCERN
  6. Escape hatches?                 缺(D1/D7)  缺(XD2)   CONFIRMED-CONCERN
═══════════════════════════════════════════════════════════════
```

**Phase 3.5 小结**：Codex 11 条 / Claude 12 条 + TTHW 前后对比；5 维 CONFIRMED-CONCERN、1 PARTIAL。

## Cross-Phase Themes（跨阶段独立同击，高置信信号）

1. **T-A 结晶不闭环**：E5 + XE3 + D6 + XD4（+主审 S2 预判）——4 声独立命中。
2. **T-B 路由身份不持久/不可观察**：XE1 + E2 + D2 + XD1。
3. **T-C wayfinder 未实测前置 P0 / drill 排序与对象错**：C4 + X4 + E8。
4. **T-D prose 锚/软门违背机械固化哲学**：C6 + X3 + XD7。
5. **T-E 逃生舱口/授权缺失**：D1 + D7 + XD2。
6. **T-F 跨仓消费面/升级窗**：C1 + C3 + XD11 + XE5（全局 symlink 语义）。

## Decision Audit Trail（autoplan 自动决策登记，G2 适配）

| # | Phase | 决策 | 分类 | 原则 | 理由 |
|---|-------|------|------|------|------|
| AD-1 | 0 | 前提门：三前提仓内实证成立，接受进入评审（证据 scope 问题单列 C1/X1 裁决） | 前提门（非自动决） | — | G2：登记待设计门一并拍板 |
| AD-2 | 0 | 0C-bis 选方案 A（=现设计 D1-D7） | Taste→登记 | P1 完备 | 已经 grill 三镜决策，B/C 劣势明确 |
| AD-3 | 0 | 扩张扫描零新增（Non-Goals 可证伪假设已穷举） | Mechanical | P3 | 无候选可呈 |
| AD-4 | 0 | 模式 SELECTIVE EXPANSION 锁定 | Mechanical | autoplan override | — |
| AD-5 | 0 | office-hours 前置 offer 跳过 | Mechanical | — | change 自带 design.md 即问题陈述（注意：与 D3 发现的 office-hours 分支丢失是两回事） |
| AD-6 | 0 | gstack 1.58.5→1.60.1 升级推迟 | Mechanical | 评审中不动工具链 | 用户会后自决 |
| AD-7 | 1/3/3.5 | 三 phase 双声全跑（codex ready） | Mechanical | P6 | 全部 EXIT=0 |

**User Challenge（双模型同向挑战用户既定方向，绝不自动决）**：
- **UC-1 规则 3 扩展（禁引 footage/memo）被 X7 挑战**（可追溯性 vs 权威源纯净）——用户在 grill Q2 刚拍板两段式禁令；codex 主张受控带类型引用。原方向为缺省，进 Step3 对抗裁决+决策区。
- **UC-2 近细远雾被 X9/XD9 挑战**（阶段序号≠信息成熟度）——D7 为 grill 前定案。进 Step3 裁决。

## Implementation Tasks 聚合

autoplan 的 tasks-*.jsonl 聚合器不适用（本仓工作流以 spec-review-report 裁决表为任务源）；六声 58 条 findings 全量进入 sdflow-spec-review Step 3 合并池，修补以 spec-review-amendment 落四件套，不另维护 JSONL。〔登记：偏离 autoplan 原生产物形态，理由=避免双真相源〕

## Phase 完成度自检

- Phase 1：0A-0F ✓ 双声 ✓ 共识表 ✓ NOT-in-scope（=proposal Non-Goals 五项+AD-3）✓ 存量杠杆 ✓ 梦态 ✓
- Phase 2：跳过（UI scope 0 命中）
- Phase 3：scope challenge ✓ 双声 ✓ 共识表 ✓ 架构图（design 已有 mermaid，验证未过时——E2/E3 指出其序列图缺再入/命名细节，进裁决）✓ 测试审（drill 覆盖缺口 E8/D12）✓
- Phase 3.5：DX scope ✓ 双声 ✓ 共识表 ✓ TTHW ✓ 分数 6.5/10 ✓
- 审计线索 ✓ 跨阶段主题 ✓
