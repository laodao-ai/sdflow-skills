# impl-orchestration · delta（implement-workflow-optimization-2026-08-p4）

## ADDED Requirements

### Requirement: ship_gate 评审报告机械层门（lens-metric 锚存在 + defer id 对账）

ship_gate 在消费 code-review 报告的既有判定点 SHALL 增加两道机械门：

① **锚存在门**：消费仓 `metrics.enabled=true` 时，报告 MUST 含 ≥1 行
`sdflow:lens-metric` `layer="code-review"` 锚与**机械引用核落盘锚**（`sdflow:ref-check` 结构化
锚行，含 status + pass/fail/uncheckable 计数——由 sdflow-code-review Step3 随引用核结果落盘，
gate 检测该锚而非段标题/散文，「全部通过/零 findings」时锚同样在场 `[spec-review-amendment]`）；
缺任一 ⇒ 判「该步进行中，重跑」（与既有「报告在但无锚行」同语义）并输出修复指引。
`metrics.enabled` 缺省或 `false` ⇒ 本门放行（消费仓语义不变）；**`openspec/config.yaml`
文件整体不存在，或 `metrics:` 段在而 `enabled` 键缺失，均同缺省 ⇒ 放行**（MUST NOT 落
fail-closed——`_yq()` 对缺文件裸 raise，实现 MUST 先判文件存在性 `[spec-review-amendment]`）；
config 存在但不可解析（yq 非零退出）⇒ fail-closed 报 problem + cause + fix。config 读取复用
ship_gate 既有 `_yq()` 的非 frontmatter file 模式，MUST NOT 引入 yaml import。spec-review 报告
在 design 门读取处 SHALL 执行同款锚存在检查；其失败指引 SHALL 提示转换态（消费仓 `metrics.enabled`
在报告写就后才翻 `true` 的场景 ⇒ 重跑该层评审或按既有人工处置指引）`[spec-review-amendment]`。

② **defer 对账门**：报告 defer 台账的每一行 MUST 含 `T\d+|B\d+` id 且对应
`openspec/issues/open/**/<id>.md` **按文件系统存在性**判定（MUST NOT 走 git 跟踪清单）；
且池文件 frontmatter 的 `change` 字段 MUST 等于当前 change 名（防误抄/复用他 change 既有 id
假绿 `[spec-review-amendment]`）；不满足 ⇒ 同「该步进行中，重跑」处置。
**台账行判别与 id 提取窄化 `[spec-review-amendment]`**：台账行 = defer 台账表格的数据行，id
取自专用 id 列且**该单元格全部内容 = 单个 id**（MUST NOT 全行子串搜索——描述列提及的既有票号、
聚合摘要句的 "defer" 字面均不得触发判定；报告模板的聚合摘要行同步改写使其不落入检测范围，
见 spec-workflow delta）。

两门解析均沿用 ship_gate 既有 fence-aware 行锚定口径：围栏内出现的锚样例/讨论文本
MUST NOT 计入判定。两门的失败输出 SHALL 按根因分诊 cause 文案（缺 lens-metric 锚 / 缺 ref-check
锚 / defer 无 id / 池文件缺失或 change 不符——四类各一句区分性说明，沿用既有 `cause_category`
诊断精度线 `[spec-review-amendment]`）；两门 verdict MUST **字面复用 `STEP_IN_PROGRESS`**、
MUST NOT 新增 verdict 名（sdflow-ship 熔断按 verdict 字面分治，新名会绕开熔断造成无限重跑
`[spec-review-amendment]`）。

#### Scenario: metrics 开启且报告缺锚被拦

- **WHEN** `metrics.enabled=true` 且 code-review 报告 frontmatter 为 pass 但全文无
  `layer="code-review"` 的 lens-metric 锚
- **THEN** gate 不放行进 verify，verdict 语义为「该步进行中，重跑」，输出含修复指引

#### Scenario: metrics 缺省时放行

- **WHEN** 消费仓 config 无 `metrics` 段（或 `enabled: false`），报告无锚
- **THEN** 本门放行，gate 行为与引入前一致

#### Scenario: config 文件整体不存在时放行 `[spec-review-amendment]`

- **WHEN** 消费仓 `openspec/config.yaml` 文件不存在（或存在但 `metrics.enabled` 键缺失）
- **THEN** 本门按缺省放行，MUST NOT 落 fail-closed

#### Scenario: defer id 存在但属于另一 change 被拦 `[spec-review-amendment]`

- **WHEN** 报告 defer 台账行携带的 id 对应池文件存在，但其 frontmatter `change` 字段
  为另一 change 名（误抄/复用既有票号）
- **THEN** 判「该步进行中，重跑」，cause 文案指明 change 不符

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
