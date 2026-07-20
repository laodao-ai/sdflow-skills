# impl-orchestration Specification

## Purpose
TBD - created by archiving change matt-workflow-integration. Update Purpose after archive.
## Requirements
### Requirement: 管线路由为手动确定值，零模型自动判断

实现管线选择 SHALL 仅由手改/落盘的确定值决定，路由三跳为：① `openspec/config.yaml` 可选键 `impl-pipeline`（人手编辑，仅在新出 ticket 时刻读一次）；② plan 文件头 frontmatter 管线 marker（出 ticket 落盘后只读，锁定在途 change 归属）；③ 键缺失或值不识别 → 一律 superpowers 管线。MUST NOT 引入任何模型自由裁量的管线判断；改 config MUST NOT 影响任何已出 ticket 在途 change 的续跑。ship_gate MUST NOT 读取 config（保零依赖不变量）。键与 marker 的读取 SHALL 落确定性脚本（stdlib-only enum reader / route helper，不触 gate）〔spec-review-amendment F4〕；ship 派发 sdflow-implement 时 SHALL 以显式字面 args 传递模式与 done_tasks（SKILL.md 与 ship 链序两处共享同一契约串）〔F4〕。marker **存在但非法/重复/损坏** SHALL 停（UNKNOWN 语义）并留痕，MUST NOT 静默回退旧管线（防两管线混跑）——静默回退仅适用「键/marker 缺席」的缺省态〔F4〕。路由结果 SHALL 产出一行 PIPELINE_RECEIPT（读到的键值/选定管线/marker/plan sha）进当轮输出与判赢材料〔F3a〕。

#### Scenario: 缺省与非法值 fail 向旧管线

- **WHEN** config 无 `impl-pipeline` 键、键值拼错、或键值为 `superpowers`
- **THEN** RUN_PLAN 路由到 superpowers:writing-plans，行为与本变更前完全一致；键**存在而值不识别**时另回显一行提示（区别于缺省缺席）〔spec-review-amendment F12〕

#### Scenario: 在途 change 不受 config 切换影响

- **WHEN** 某 change 已以 tickets 管线出 ticket（marker 在盘面），随后 config 键被改回 superpowers
- **THEN** 该 change 的 CONTINUE_IMPL 续跑仍路由 sdflow-implement 执行模式（只认 marker），新出 ticket 的 change 才走新 config 值

#### Scenario: 对在途强制换管线属显式越权

- **WHEN** 操作者人工修改在途 change 的 plan 文件 marker
- **THEN** 视为显式越权通道（git 留痕、产物一致性自担）；skill MUST NOT 主动建议此操作

### Requirement: 出 ticket 模式产出 tracer-bullet ticket 并落盘即返回

sdflow-implement 出 ticket 模式 SHALL 从 design.md 与 tasks.md 产出 3-6 张 tracer-bullet 垂直切片 ticket（计数仅约束垂直切片；expand–contract 例外序列的迁移批次不占该预算〔spec-review-amendment E5〕）：每 ticket 为打穿全层、可独立验证的行为级描述，MUST NOT 预写实现代码或具体文件路径；每 ticket SHALL 声明显式 Blocked-by 阻塞边与 R-ID 需求标注；宽重构（单一机械改动 blast radius 扫全仓）SHALL 走 expand–contract 序列例外而非强行垂直切片。ticket 文件头部 SHALL 逐字携带 design 领域约束为 Global Constraints 节。出 ticket SHALL 落盘即返回编排层（ship），MUST NOT 在同一调用内直通执行——保 ship_gate 在出 ticket 后/执行前的校验插入点。原版 to-tickets 的 quiz-the-user 人类步 SHALL 删除（阶段三无人类门），粒度争议按 T10 三级决策协议处理。

#### Scenario: 出 ticket 后 gate 先行校验再执行

- **WHEN** 出 ticket 模式完成落盘并返回
- **THEN** ship 重跑 ship_gate，plan 文件经 fence/标题/重号三道校验后才发出 CONTINUE_IMPL，执行模式才被派发

#### Scenario: 宽重构走 expand–contract

- **WHEN** 某 tasks.md 条目是重命名共享符号类宽重构
- **THEN** 出 ticket 为 expand ticket → 迁移批次 ticket（各自 Blocked-by expand）→ contract ticket（Blocked-by 全部迁移批次），不产出「一 ticket 打穿全仓」的伪垂直切片

### Requirement: ticket 文件兼容 ship_gate 既有完成判据契约

ticket 文件 SHALL 写入 change 目录的 `superpowers-plan.md`（试验期外衣文件名），每 ticket 以 `### Task N: <ticket 名>` 为标题、ticket 内含验收标准复选框；出 ticket 收尾 SHALL 显式 checkpoint（plan 单独提交建立完成窗口锚）〔grill-amendment〕。完成信号 SHALL **后置双写**〔spec-review-amendment F1；设计门 2026-07-10 拍板定稿（方案甲）〕：implementer 实现期提交 MUST NOT 带 `task<N>-` 完成标签；该 ticket 双轴审 + 修复环通过后，由执行模式补打 `checkpoint(<change>:task<N>-<slug>)` 完成标签并勾全验收复选框——**审过才算 done**；resume 发现「实现提交在、完成标签缺」SHALL 进入续审而非重实现。plan 首次提交后结构 SHALL 不可变：MUST NOT 重号/重排/删除/复用 Task 号，重规划只可追加新号〔F1〕。plan 文件 frontmatter SHALL 含且仅含 `impl-pipeline` 单键（无注释/示例/第二块——marker 块内杂行会被 gate 计为幻影任务）〔F5〕。ship_gate.py SHALL 零改动。

#### Scenario: gate 以既有双通道判定 ticket 完成

- **WHEN** 某 ticket 双轴审通过、执行模式按契约补打完成标签并勾框
- **THEN** 既有 ship_gate（未改动）经 checkpoint 标签 ∪ 复选框双通道判定该 Task 号 done，CONTINUE_IMPL 的 done_tasks 集合正确携带；审前中断 resume 时该 ticket 不在 done_tasks 中、进入续审〔spec-review-amendment F1〕

### Requirement: 执行模式串行工作 frontier 并以文件交接

执行模式 SHALL 按 Blocked-by 拓扑串行工作 frontier（首版 MUST NOT 并行派发 implementer）；每 ticket 派发 fresh implementer 子代理，契约为 TDD at pre-agreed seams、定期 typecheck、结束跑全套件、完成信号双写；implementer 状态词表为 DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED——NEEDS_CONTEXT SHALL 由编排层从盘面（design.md/specs/ticket 文本）自答，答不出走 defer 或停，MUST NOT 编造；BLOCKED 无法消解 SHALL 停并上抛。子代理产物 SHALL 以文件交接：implementer 全量报告写 report file（按 ticket 名命名）只返回状态摘要；reviewer 输入 diff 经 review-package 式文件传递，MUST NOT 把大产物粘贴进 dispatch prompt。审出的 cannot-verify-from-diff 项（需求活在未改动代码或跨 ticket）SHALL 由编排层亲自消解，且 SHALL 设预算上界：需触碰超过 3 个文件、或从盘面（design/specs/ticket 文本）不可直接解答时，MUST 按「确认缺口退回 implementer」处理〔spec-review-amendment F7〕。frontier 的 next-ready 判定 SHALL 由确定性 helper 计算（解析 Blocked-by + gate done_tasks 拓扑排序，stdlib-only）〔F8〕。一切停机（BLOCKED/依赖缺失/gate 拒绝）SHALL 以统一 halt envelope 呈现：错误码、ticket 号与名、已核证据、已写盘副作用、精确恢复步骤〔F7〕；BLOCKED 的 blocker 记录 SHALL 落盘 report file（change 目录内、git-tracked，防 compaction 蒸发）〔F7〕。DONE_WITH_CONCERNS SHALL 与 DONE 同路径进双轴审，implementer 所述 concerns 逐字附给两轴〔F7〕。

#### Scenario: frontier 串行推进

- **WHEN** ticket 2、ticket 3 均 Blocked-by ticket 1 且 ticket 1 完成
- **THEN** 编排层按 ticket 号序先派 ticket 2，完成后再派 ticket 3，同一时刻至多一个 implementer 在工作

#### Scenario: NEEDS_CONTEXT 从盘面自答

- **WHEN** implementer 返回 NEEDS_CONTEXT 询问某接口约定
- **THEN** 编排层从 design.md/ticket 文本中定位答案回填再派发；盘面无答案时按 T10 处理（defer 或停），不编造

### Requirement: 每 ticket 双轴审加修复环，领域清单注入 Standards 轴

每 ticket 实现完成后 SHALL 并行派发两个评审子代理：Standards 轴（仓内文档化标准 + Fowler smell 基线，且 SHALL 把 code-checklists/domains/<命中栈>（经 resolve-workflow.sh 解析）作为标准源注入 = 注入点 B）与 Spec 轴（对照 ticket 文本验收标准与 R-ID 溯源需求）；两轴输出各 SHALL 封顶（<400 词量级）。Critical/Important 发现 SHALL 派 fix 子代理修复并 re-review 直至通过；Minor 发现 SHALL defer 进 todolist（显式带 change 字段）。code-checklists/domains 经 resolve-workflow.sh 解析失败、规则根不可达或命中栈无清单时，Standards 轴 MUST NOT 宣称通过——SHALL 显式停或在报告记「领域清单未覆盖」并留降级原因〔spec-review-amendment F13〕。执行模式 MUST NOT 追加 warm final whole-branch review（冷层 sdflow-code-review 紧随其后承担全分支审）。

#### Scenario: 双轴审通过才推进下一 ticket

- **WHEN** 某 ticket Spec 轴报缺失验收项
- **THEN** 派 fix 子代理修复 → re-review → 通过后才标记该 ticket 完成并推进 frontier；MUST NOT 带着未修 Critical/Important 推进

#### Scenario: 实现完成直接交冷层

- **WHEN** 全部 ticket 完成、gate 判定进入 RUN_CODE_REVIEW
- **THEN** 直接触发 sdflow-code-review 冷层主审，中间无 warm 全分支终审步

### Requirement: 不引入 ledger 与 task-brief 层

执行模式 MUST NOT 维护 progress ledger 类跨会话状态文件（完成态唯一真相源 = gate 的 checkpoint∪复选框双通道，resume 经 CONTINUE_IMPL done_tasks）；MUST NOT 引入 task-brief 抽取层（行为级 ticket 文本即 brief，dispatch 直携 ticket 文本）。

#### Scenario: 中断后 resume 不重派

- **WHEN** 执行中途会话中断，重调 /sdflow-ship
- **THEN** gate 从盘面输出 done_tasks 已完成 ticket 号集，编排层跳过已完成 ticket 从 frontier 续跑，全程无 ledger 参与

### Requirement: 试点回退与熔断哨兵

新管线 SHALL 以试点方式启用（逐仓/逐 change 翻 config 键），缺省路径（不翻键）SHALL 与本变更前行为一致。试点期 SHALL 以冷层 code-review Critical/严重 findings 相对同类型基线为熔断哨兵：恶化即停试点（config 回缺省），在途 tickets change 按 marker 跑完或人工越权处置。每个试点 change SHIPPED 后、选定下一试点前 SHALL 再生 retro 报告核对哨兵〔spec-review-amendment F3a〕；试点样本计入判赢集前 SHALL 核对 PIPELINE_RECEIPT/marker 与 config 意图一致（误路由 change 剔除样本）〔F3a〕；选样拒绝条件：跨模块宽重构、接口高度不确定、纯文档/琐碎类 MUST NOT 入样〔F3a〕。

#### Scenario: 哨兵触发回退

- **WHEN** 某试点 change 的冷层报告出现应被每 ticket 双轴审拦住的严重缺陷且相对基线明显上升
- **THEN** 停止新试点（config 键回缺省），恶化实证记入判赢材料，ticket 粒度/审深度回炉再议

### Requirement: implementer dispatch 携带信号权威归属声明

`sdflow-implement` 派发 implementer / fix 子代理时，dispatch prompt SHALL 携带一份**信号权威表**，正面声明「完成信号写哪里」与「设计工件不可碰」——子代理跑在 fresh context，看不见 SKILL.md 与 CLAUDE.md，未声明即等同未约束。

声明 SHALL 为正面陈述（列出权威归属），MUST NOT 仅写成禁令清单——禁令只挡列举到的那一种越界，权威表挡的是整个范畴。

本要求的适用面 SHALL 限于本仓自有的 `sdflow-implement`；第三方实现 skill（superpowers `subagent-driven-development`、matt `implement`）不受本要求约束，故本要求 MUST NOT 被当作设计门失鲜问题的唯一防线（机械防线在 `spec-workflow` 的设计门新鲜度内容判据）。

#### Scenario: dispatch prompt 含信号权威表

- **WHEN** `sdflow-implement` 执行模式派发 implementer 或 fix 子代理
- **THEN** prompt MUST 含信号权威表，至少覆盖两行归属：完成信号 = `superpowers-plan.md` 验收复选框 + `checkpoint(<change>:task<N>-<slug>)` 标签；设计工件 = `proposal.md` / `design.md` / `tasks.md` / `specs/`，实现期不修改
- **AND** 该表 MUST 与 `ship_gate.py` 实际消费的完成判据一致（plan 复选框 + checkpoint 标签），MUST NOT 声明 gate 并不读取的信号源

#### Scenario: 权威表缺席不得静默降级

- **WHEN** 因 SKILL 裁剪或模板漂移导致 dispatch prompt 未携带信号权威表
- **THEN** 该缺席 MUST NOT 被当作「已由 gate 兜住所以无所谓」——gate 的监视集分流只消解失鲜误判，不阻止 implementer 写脏设计工件；本要求与 gate 侧要求 SHALL 各自独立成立

