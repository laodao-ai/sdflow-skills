## ADDED Requirements

### Requirement: sdflow-implement 档位解析与声明

`sdflow-implement` SHALL 在起手执行跟 `sdflow-code-review`/`sdflow-spec-review`/`sdflow-done` 逐字一致的"宿主/档位解析"四步(清脏 unset `SDFLOW_HOST`/`SDFLOW_TIER_STRONG`/`SDFLOW_TIER_MID`/`SDFLOW_TIER_LIGHT` → 预检 `resolve-models.sh` 可执行 → 捕获退出码后 eval → eval 后校验 `$SDFLOW_HOST` 非空且属 `{claude,codex,unknown}`,host≠unknown 时三档非空),不满足任一步 SHALL fail-loud 硬停,MUST NOT 回落当 unknown 处置。implementer、Standards 轴、Spec 轴、fix 子代理派发 SHALL 引用本次解析得到的 `$SDFLOW_TIER_MID`,MUST NOT 内联具体模型名。

#### Scenario: 档位解析成功后派发子代理

- **WHEN** `sdflow-implement` 起手完成宿主/档位解析,`$SDFLOW_HOST` 与三档均非空
- **THEN** 后续 implementer/Standards轴/Spec轴/fix 子代理 dispatch 均引用 `$SDFLOW_TIER_MID`,不内联模型名

#### Scenario: 档位解析失败即硬停

- **WHEN** `resolve-models.sh` 不可执行,或 eval 后 `$SDFLOW_HOST` 非空但三档任一为空
- **THEN** `sdflow-implement` fail-loud 硬停,报告 problem+cause+fix,MUST NOT 用空档位或默认值继续派发

## MODIFIED Requirements

### Requirement: 执行模式串行工作 frontier 并以文件交接

执行模式 SHALL 按 Blocked-by 拓扑串行工作 frontier（首版 MUST NOT 并行派发 implementer）；每 ticket 派发 fresh implementer 子代理，契约为 TDD at pre-agreed seams、定期 typecheck、单元测试 + 本 ticket 声明的 e2e 场景（MUST NOT 跑全量 e2e/集成套件——聚合回归由「实现验证」收尾 ticket 承担，见「出 ticket 模式产出 tracer-bullet ticket 并落盘即返回」需求）、完成信号双写；implementer 状态词表为 DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED——NEEDS_CONTEXT SHALL 由编排层从盘面（design.md/specs/ticket 文本）自答，答不出走 defer 或停，MUST NOT 编造；BLOCKED 无法消解 SHALL 停并上抛。子代理产物 SHALL 以文件交接：implementer 全量报告写 report file（按 ticket 名命名）只返回状态摘要；reviewer 输入 diff 经 review-package 式文件传递，MUST NOT 把大产物粘贴进 dispatch prompt。审出的 cannot-verify-from-diff 项（需求活在未改动代码或跨 ticket）SHALL 由编排层亲自消解，且 SHALL 设预算上界：需触碰超过 3 个文件、或从盘面（design/specs/ticket 文本）不可直接解答时，MUST 按「确认缺口退回 implementer」处理〔spec-review-amendment F7〕。frontier 的 next-ready 判定 SHALL 由确定性 helper 计算（解析 Blocked-by + gate done_tasks 拓扑排序，stdlib-only）〔F8〕。一切停机（BLOCKED/依赖缺失/gate 拒绝）SHALL 以统一 halt envelope 呈现：错误码、ticket 号与名、已核证据、已写盘副作用、精确恢复步骤〔F7〕；BLOCKED 的 blocker 记录 SHALL 落盘 report file（change 目录内、git-tracked，防 compaction 蒸发）〔F7〕。DONE_WITH_CONCERNS SHALL 与 DONE 同路径进双轴审，implementer 所述 concerns 逐字附给两轴〔F7〕。

#### Scenario: frontier 串行推进

- **WHEN** ticket 2、ticket 3 均 Blocked-by ticket 1 且 ticket 1 完成
- **THEN** 编排层按 ticket 号序先派 ticket 2，完成后再派 ticket 3，同一时刻至多一个 implementer 在工作

#### Scenario: NEEDS_CONTEXT 从盘面自答

- **WHEN** implementer 返回 NEEDS_CONTEXT 询问某接口约定
- **THEN** 编排层从 design.md/ticket 文本中定位答案回填再派发；盘面无答案时按 defer 或停处理，不编造

#### Scenario: 功能 ticket 只测本票范围

- **WHEN** 某功能 ticket 的 implementer 即将返回 DONE
- **THEN** 已运行单元测试 + 该 ticket 声明的 e2e 场景（若有）并全部通过，MUST NOT 运行超出本票范围的集成/e2e 套件

### Requirement: 每 ticket 双轴审加修复环，领域清单注入 Standards 轴

每 ticket 实现完成后 SHALL 并行派发两个评审子代理：Standards 轴（仓内文档化标准 + Fowler smell 基线，且 SHALL 把 code-checklists/domains/<命中栈>（经 resolve-workflow.sh 解析）作为标准源注入 = 注入点 B）与 Spec 轴（对照 ticket 文本验收标准与 R-ID 溯源需求）；两轴均按 mid 档派发（见「sdflow-implement 档位解析与声明」需求）；两轴输出各 SHALL 封顶（<400 词量级）。Critical/Important 发现 SHALL 派 fix 子代理（mid 档）修复并 re-review 直至通过；Minor 发现 SHALL defer 进 todolist（显式带 change 字段）。code-checklists/domains 经 resolve-workflow.sh 解析失败、规则根不可达或命中栈无清单时，Standards 轴 MUST NOT 宣称通过——SHALL 显式停或在报告记「领域清单未覆盖」并留降级原因〔spec-review-amendment F13〕。**熔断（本需求独立定义，不引用其它能力的"T10"标签——本场景语义为"同一发现反复未消解"，与阶段三"≥2方案自动选"场景触发条件不同）**：同一发现（同 file:line + 同问题）连续 2 轮 re-review 仍未消解 SHALL 停止循环，按以下三级处置：①有客观判据（测试/断言/基准可判）→ 自动选并记理由；②无客观判据 → 派对抗镜复核该发现是否成立，复核 SHALL 用 strong 档（本场景是低频、需要独立判断力打破同档循环的仲裁点），通过方按复核结论处置；③复核不过或无从复核 → defer 进 buglist 并停上抛。MUST NOT 无限循环。执行模式 MUST NOT 追加 warm final whole-branch review（冷层 sdflow-code-review 紧随其后承担全分支审）。

#### Scenario: 双轴审通过才推进下一 ticket

- **WHEN** 某 ticket Spec 轴报缺失验收项
- **THEN** 派 fix 子代理修复 → re-review → 通过后才标记该 ticket 完成并推进 frontier；MUST NOT 带着未修 Critical/Important 推进

#### Scenario: 实现完成直接交冷层

- **WHEN** 全部 ticket 完成、gate 判定进入 RUN_CODE_REVIEW
- **THEN** 直接触发 sdflow-code-review 冷层主审，中间无 warm 全分支终审步

#### Scenario: 熔断后派 strong 档对抗镜复核

- **WHEN** 同一发现连续 2 轮 re-review 仍未消解，且无客观判据可自动选
- **THEN** 编排层派一个 strong 档对抗镜复核该发现是否成立，不得沿用 mid 档同档互判

### Requirement: 出 ticket 模式产出 tracer-bullet ticket 并落盘即返回

sdflow-implement 出 ticket 模式 SHALL 从 design.md 与 tasks.md 产出 3-6 张 tracer-bullet 垂直切片 ticket（计数仅约束垂直切片；expand–contract 例外序列的迁移批次、以及下述「实现验证」收尾 ticket 均不占该预算〔spec-review-amendment E5〕）：每 ticket 为打穿全层、可独立验证的行为级描述，MUST NOT 预写实现代码或具体文件路径；每 ticket SHALL 声明显式 Blocked-by 阻塞边与 R-ID 需求标注；宽重构（单一机械改动 blast radius 扫全仓）SHALL 走 expand–contract 序列例外而非强行垂直切片。ticket 文件头部 SHALL 逐字携带 design 领域约束为 Global Constraints 节。出 ticket SHALL 落盘即返回编排层（ship），MUST NOT 在同一调用内直通执行——保 ship_gate 在出 ticket 后/执行前的校验插入点。原版 to-tickets 的 quiz-the-user 人类步 SHALL 删除（阶段三无人类门），粒度争议按三级决策协议处理（①有客观判据自动选记理由；②无客观判据派 strong 档对抗镜复核推荐切分方案，通过方自动选；③复核不过或无从复核 defer）。**出 ticket 模式 SHALL 在全部功能垂直切片之后追加一张强制的"实现验证"收尾 ticket**，`Blocked-by` 声明为全部功能 ticket 号，其验收标准 SHALL 为"运行本 change 的聚合测试套件（单元+集成+e2e）并全部通过"；该票 SHALL 走跟普通 ticket 相同的 implementer + 双轴审 + fix 循环（Spec 轴核验聚合套件确实运行且通过，Standards 轴核验修复方式未靠删除/弱化断言蒙混过关）；`sdflow-done` 的 verify 引用该票自身的 commit/报告作为聚合覆盖需求的证据锚，不扩张 verify 自身职责。出票落盘前 SHALL 做一次全 ticket 语义一致性自扫（拓扑之外的语义矛盾，如某票假设的接口形状被另一票废弃）；发现矛盾按三级决策协议处理（①有客观判据自动选记理由；②无客观判据派 strong 档对抗镜复核；③复核不过或无从复核则停并上抛），不批量问人。

#### Scenario: 出 ticket 后 gate 先行校验再执行

- **WHEN** 出 ticket 模式完成落盘并返回
- **THEN** ship 重跑 ship_gate，plan 文件经 fence/标题/重号三道校验后才发出 CONTINUE_IMPL，执行模式才被派发

#### Scenario: 宽重构走 expand–contract

- **WHEN** 某 tasks.md 条目是重命名共享符号类宽重构
- **THEN** 出 ticket 为 expand ticket → 迁移批次 ticket（各自 Blocked-by expand）→ contract ticket（Blocked-by 全部迁移批次），不产出「一 ticket 打穿全仓」的伪垂直切片

#### Scenario: 出票模式恒含实现验证收尾票

- **WHEN** 出 ticket 模式产出 N 张功能垂直切片（3≤N≤6）
- **THEN** plan 文件额外含一张「实现验证」收尾 ticket，`Blocked-by` 全部 N 张功能票号，不计入 3–6 预算计数

#### Scenario: 粒度争议派 strong 档复核

- **WHEN** design.md 无「切片建议」节，编排层需自主决定切分方案且存在 ≥2 个合理候选
- **THEN** 无客观判据可判时派一个 strong 档对抗镜复核推荐的切分方案，不问用户

#### Scenario: 一致性自扫发现矛盾派 strong 档复核

- **WHEN** 全 ticket 语义一致性自扫发现某票假设的接口形状被另一票明确废弃，且无客观判据可自动选
- **THEN** 派一个 strong 档对抗镜复核该矛盾的处置方案，复核不过或无从复核则停并上抛，不批量问人
