# impl-orchestration · delta（implement-workflow-optimization-2026-08-p4）

## ADDED Requirements

### Requirement: ship_gate 评审报告机械层门（lens-metric 锚存在 + defer id 对账）

ship_gate 在消费 code-review 报告的既有判定点 SHALL 增加两道机械门：

① **锚存在门**：消费仓 `metrics.enabled=true` 时，报告 MUST 含 ≥1 行
`sdflow:lens-metric` `layer="code-review"` 锚与机械引用核落盘段；缺任一 ⇒ 判
「该步进行中，重跑」（与既有「报告在但无锚行」同语义）并输出修复指引。
`metrics.enabled` 缺省或 `false` ⇒ 本门放行（消费仓语义不变）；config 存在但不可解析 ⇒
fail-closed 报 problem + cause + fix。spec-review 报告在 design 门读取处 SHALL 执行
同款锚存在检查。

② **defer 对账门**：报告 defer 台账的每一行 MUST 含 `T\d+|B\d+` id 且对应
`openspec/issues/open/**/<id>.md` **按文件系统存在性**判定（MUST NOT 走 git 跟踪清单）；
不满足 ⇒ 同「该步进行中，重跑」处置。

两门解析均沿用 ship_gate 既有 fence-aware 行锚定口径：围栏内出现的锚样例/讨论文本
MUST NOT 计入判定。

#### Scenario: metrics 开启且报告缺锚被拦

- **WHEN** `metrics.enabled=true` 且 code-review 报告 frontmatter 为 pass 但全文无
  `layer="code-review"` 的 lens-metric 锚
- **THEN** gate 不放行进 verify，verdict 语义为「该步进行中，重跑」，输出含修复指引

#### Scenario: metrics 缺省时放行

- **WHEN** 消费仓 config 无 `metrics` 段（或 `enabled: false`），报告无锚
- **THEN** 本门放行，gate 行为与引入前一致

#### Scenario: defer 行无 id 或池文件缺失被拦

- **WHEN** 报告 defer 台账行写「已入 todolist」但无 id，或有 id 而
  `openspec/issues/open/**/<id>.md` 不存在（含已写盘未 git add 的反例：文件存在即通过）
- **THEN** 无 id / 文件缺失 ⇒ 判「该步进行中，重跑」；文件存在（即使未 add）⇒ 本门通过

#### Scenario: fence 内锚样例不触发判定

- **WHEN** 报告围栏代码块内含 lens-metric 锚样例、正文实际无锚
- **THEN** 锚存在门仍判缺锚（fence 内容不计入）

### Requirement: sdflow-implement 与 sdflow-done 派发接 effort 档

sdflow-implement（implementer / Standards 轴 / Spec 轴 / fix 子代理）与 sdflow-done
（verify / archive / commit 步子代理）的派发 SHALL 按各步既有档位对应
`$SDFLOW_EFFORT_<档位>` 选 `subagent_type`，空值回落语义与评审侧一致（不带
subagent_type，行为不变）。verify 终门 MUST NOT 低于 high。

#### Scenario: done 三步各按档位带 effort

- **WHEN** claude 宿主 `$SDFLOW_EFFORT_*` 已导出，sdflow-done 派发 verify/archive/commit
- **THEN** 三步分别以 high/medium/low 档 effort 派发（映射经档位表推导，SKILL 不内联值）

#### Scenario: 空值回落

- **WHEN** `$SDFLOW_EFFORT_LIGHT` 为空
- **THEN** commit 步派发不带 subagent_type，与现行为一致
