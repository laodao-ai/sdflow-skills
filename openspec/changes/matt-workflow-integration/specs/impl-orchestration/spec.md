# impl-orchestration Specification (Delta)

## ADDED Requirements

### Requirement: 管线路由为手动确定值，零模型自动判断

实现管线选择 SHALL 仅由手改/落盘的确定值决定，路由三跳为：① `openspec/config.yaml` 可选键 `impl-pipeline`（人手编辑，仅在新出 ticket 时刻读一次）；② plan 文件头 frontmatter 管线 marker（出 ticket 落盘后只读，锁定在途 change 归属）；③ 键缺失或值不识别 → 一律 superpowers 管线。MUST NOT 引入任何模型自由裁量的管线判断；改 config MUST NOT 影响任何已出 ticket 在途 change 的续跑。ship_gate MUST NOT 读取 config（保零依赖不变量）。

#### Scenario: 缺省与非法值 fail 向旧管线

- **WHEN** config 无 `impl-pipeline` 键、键值拼错、或键值为 `superpowers`
- **THEN** RUN_PLAN 路由到 superpowers:writing-plans，行为与本变更前完全一致

#### Scenario: 在途 change 不受 config 切换影响

- **WHEN** 某 change 已以 tickets 管线出 ticket（marker 在盘面），随后 config 键被改回 superpowers
- **THEN** 该 change 的 CONTINUE_IMPL 续跑仍路由 sdflow-implement 执行模式（只认 marker），新出 ticket 的 change 才走新 config 值

#### Scenario: 对在途强制换管线属显式越权

- **WHEN** 操作者人工修改在途 change 的 plan 文件 marker
- **THEN** 视为显式越权通道（git 留痕、产物一致性自担）；skill MUST NOT 主动建议此操作

### Requirement: 出 ticket 模式产出 tracer-bullet ticket 并落盘即返回

sdflow-implement 出 ticket 模式 SHALL 从 design.md 与 tasks.md 产出 3-6 张 tracer-bullet 垂直切片 ticket：每 ticket 为打穿全层、可独立验证的行为级描述，MUST NOT 预写实现代码或具体文件路径；每 ticket SHALL 声明显式 Blocked-by 阻塞边与 R-ID 需求标注；宽重构（单一机械改动 blast radius 扫全仓）SHALL 走 expand–contract 序列例外而非强行垂直切片。ticket 文件头部 SHALL 逐字携带 design 领域约束为 Global Constraints 节。出 ticket SHALL 落盘即返回编排层（ship），MUST NOT 在同一调用内直通执行——保 ship_gate 在出 ticket 后/执行前的校验插入点。原版 to-tickets 的 quiz-the-user 人类步 SHALL 删除（阶段三无人类门），粒度争议按 T10 三级决策协议处理。

#### Scenario: 出 ticket 后 gate 先行校验再执行

- **WHEN** 出 ticket 模式完成落盘并返回
- **THEN** ship 重跑 ship_gate，plan 文件经 fence/标题/重号三道校验后才发出 CONTINUE_IMPL，执行模式才被派发

#### Scenario: 宽重构走 expand–contract

- **WHEN** 某 tasks.md 条目是重命名共享符号类宽重构
- **THEN** 出 ticket 为 expand ticket → 迁移批次 ticket（各自 Blocked-by expand）→ contract ticket（Blocked-by 全部迁移批次），不产出「一 ticket 打穿全仓」的伪垂直切片

### Requirement: ticket 文件兼容 ship_gate 既有完成判据契约

ticket 文件 SHALL 写入 change 目录的 `superpowers-plan.md`（试验期外衣文件名），每 ticket 以 `### Task N: <ticket 名>` 为标题、ticket 内含验收标准复选框；实现完成信号 SHALL 双写：checkpoint 标签 `checkpoint(<change>:task<N>-<slug>)`（由 implementer 子代理自己执行 checkpoint-commit.sh）与该 ticket 验收复选框全勾，MUST NOT 只落单边（防勾框未打标签或反之的半态假完成）。plan 文件 frontmatter SHALL 含管线 marker。ship_gate.py SHALL 零改动。

#### Scenario: gate 以既有双通道判定 ticket 完成

- **WHEN** 某 ticket 的 implementer 完成实现、按契约双写完成信号
- **THEN** 既有 ship_gate（未改动）经 checkpoint 标签 ∪ 复选框双通道判定该 Task 号 done，CONTINUE_IMPL 的 done_tasks 集合正确携带

### Requirement: 执行模式串行工作 frontier 并以文件交接

执行模式 SHALL 按 Blocked-by 拓扑串行工作 frontier（首版 MUST NOT 并行派发 implementer）；每 ticket 派发 fresh implementer 子代理，契约为 TDD at pre-agreed seams、定期 typecheck、结束跑全套件、完成信号双写；implementer 状态词表为 DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED——NEEDS_CONTEXT SHALL 由编排层从盘面（design.md/specs/ticket 文本）自答，答不出走 defer 或停，MUST NOT 编造；BLOCKED 无法消解 SHALL 停并上抛。子代理产物 SHALL 以文件交接：implementer 全量报告写 report file（按 ticket 名命名）只返回状态摘要；reviewer 输入 diff 经 review-package 式文件传递，MUST NOT 把大产物粘贴进 dispatch prompt。审出的 cannot-verify-from-diff 项（需求活在未改动代码或跨 ticket）SHALL 由编排层亲自消解，确认为真缺口则按失败评审送回 implementer。

#### Scenario: frontier 串行推进

- **WHEN** ticket 2、ticket 3 均 Blocked-by ticket 1 且 ticket 1 完成
- **THEN** 编排层按 ticket 号序先派 ticket 2，完成后再派 ticket 3，同一时刻至多一个 implementer 在工作

#### Scenario: NEEDS_CONTEXT 从盘面自答

- **WHEN** implementer 返回 NEEDS_CONTEXT 询问某接口约定
- **THEN** 编排层从 design.md/ticket 文本中定位答案回填再派发；盘面无答案时按 T10 处理（defer 或停），不编造

### Requirement: 每 ticket 双轴审加修复环，领域清单注入 Standards 轴

每 ticket 实现完成后 SHALL 并行派发两个评审子代理：Standards 轴（仓内文档化标准 + Fowler smell 基线，且 SHALL 把 code-checklists/domains/<命中栈>（经 resolve-workflow.sh 解析）作为标准源注入 = 注入点 B）与 Spec 轴（对照 ticket 文本验收标准与 R-ID 溯源需求）；两轴输出各 SHALL 封顶（<400 词量级）。Critical/Important 发现 SHALL 派 fix 子代理修复并 re-review 直至通过；Minor 发现 SHALL defer 进 todolist（显式带 change 字段）。执行模式 MUST NOT 追加 warm final whole-branch review（冷层 sdflow-code-review 紧随其后承担全分支审）。

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

新管线 SHALL 以试点方式启用（逐仓/逐 change 翻 config 键），缺省路径（不翻键）SHALL 与本变更前行为一致。试点期 SHALL 以冷层 code-review Critical/严重 findings 相对同类型基线为熔断哨兵：恶化即停试点（config 回缺省），在途 tickets change 按 marker 跑完或人工越权处置。

#### Scenario: 哨兵触发回退

- **WHEN** 某试点 change 的冷层报告出现应被每 ticket 双轴审拦住的严重缺陷且相对基线明显上升
- **THEN** 停止新试点（config 键回缺省），恶化实证记入判赢材料，ticket 粒度/审深度回炉再议
