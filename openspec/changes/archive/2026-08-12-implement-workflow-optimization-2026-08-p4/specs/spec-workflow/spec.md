# spec-workflow · delta（implement-workflow-optimization-2026-08-p4）

## ADDED Requirements

### Requirement: 评审镜 dispatch prompt 按三段组装序构造，稳定前缀为脚本输出原文

两评审编排 SKILL 的镜 dispatch prompt SHALL 按固定三段序构造：段① 稳定前缀（跨轮跨镜
byte-stable）= `render-review-prefix.sh --layer <layer>` 的输出**原文**（按固定序含：通则
区块全文 + 评审子代理通用契约〔结构化 findings schema、引文纪律、输出封顶句「回传目标
≤2k token，超出按严重度截优先」、不问人〕+ 该层 base checklist 全文）；段② 半稳定
（per-镜，change 内稳定）= 镜角色与领域清单/对抗角度/历史镜指令；段③ 动态 = change 目录、
diff 范围与 diff。脚本任一源文件缺失 SHALL fail-loud 非零退出，评审 SKILL 按既有降级条款
处置，MUST NOT 以半段前缀继续。大部头/高频演进规则（trigger-catalog、lens-metric-contract
等）保持引用 + anchor_lint；「SKILL.md 禁静态内联」不变——通用契约段唯一源在脚本，SKILL
正文只保留一句引用。

#### Scenario: 稳定前缀 byte-stable

- **WHEN** 同一规则集状态下对同一 layer 连续两次运行 render-review-prefix.sh
- **THEN** 两次 stdout 逐字节相同（golden 测试断言）

#### Scenario: 前缀源缺失 fail-loud

- **WHEN** base checklist 在规则根不可达
- **THEN** 脚本非零退出且 stderr 说明缺失源并含修复动作指引（与既有 hack 脚本同风格，
  如「回运行 checkout 跑 bash setup.sh」——problem+cause+fix 三段俱全 `[spec-review-amendment]`），
  MUST NOT 输出部分前缀

### Requirement: 评审镜派发按档位 × effort 二维，空值回落现行为

两评审编排 SKILL 的镜派发 SHALL 在 model 档位之外按 `$SDFLOW_EFFORT_<档位>` 选
`subagent_type: sdflow-effort-<值>`；`$SDFLOW_EFFORT_*` 为空（codex/unknown 宿主、
resolver 未升级、agent 定义未铺设）时 SHALL 不带 subagent_type 派发，行为与 effort 维
引入前完全相同（前向兼容，pull/setup 窗口零破坏）。主 session 综合裁决与 verify 终门
等门禁步 MUST NOT 以低于 high 的 effort 执行。四个编排 SKILL 的 tier-resolution 托管块
unset 清脏清单 SHALL 同步扩含 `SDFLOW_EFFORT_STRONG/MID/LIGHT` 三变量——否则旧 resolver
不导出 effort 时，同 shell 上一轮残留的脏值会击穿空值回落（与既有 V1 清脏条款同因
`[spec-review-amendment]`）。

#### Scenario: 脏 effort 残留被清脏拦截 `[spec-review-amendment]`

- **WHEN** 同 shell 预置脏 `SDFLOW_EFFORT_MID=xhigh` 后 eval 一个不导出 effort 的旧版
  resolver 输出
- **THEN** 清脏步已 unset 该变量，派发不带 subagent_type（空值回落），MUST NOT 误用陈旧值

#### Scenario: effort 空值时派发不带 subagent_type

- **WHEN** `$SDFLOW_EFFORT_MID` 为空串
- **THEN** 领域镜/对抗镜派发调用不含 subagent_type 字段，其余参数与现行为一致

#### Scenario: 门禁步不降 effort

- **WHEN** 构造 verify 终门或 Step3 主审裁决的执行档
- **THEN** effort 取值 ≥ high，MUST NOT 因成本优化降至 medium/low

### Requirement: code-review defer 残差当场入池并携 id 台账

sdflow-code-review 的 Step4 defer 处置 SHALL 当场调用 recorder add（显式携带
`source_change` 为当前 change 名）并把返回的 issue id 写入报告「修复 / defer 台账」
对应行；报告 MUST NOT 出现无 id 的 defer 声明（「已入 / 待入 todolist」类散文承诺）。
台账行 id 与池文件的对账由 gate 侧机械门执行（见 impl-orchestration delta）。
台账 SHALL 采用与 gate 提取规则对齐的机读结构（表格行 + 专用 id 列，单元格全部内容 =
单个 id）；现有报告模板的聚合摘要句（含 "defer" 字面、无 id）SHALL 同步改写至不落入
gate 检测范围 `[spec-review-amendment]`。Step3 机械引用核结果 SHALL 以结构化锚行
`sdflow:ref-check`（status + pass/fail/uncheckable 计数）落盘报告——包括全部通过与
零 findings 的轮次，作为锚存在门 ① 的机读对象 `[spec-review-amendment]`。

#### Scenario: defer 行携真实 id

- **WHEN** 一条 finding 裁决为 defer
- **THEN** 报告台账行含 recorder 返回的 `T<n>`/`B<n>` id，且
  `openspec/issues/open/**/<id>.md` 在报告写入时已存在

#### Scenario: recorder 调用失败不静默

- **WHEN** recorder add 非零退出
- **THEN** 该 defer MUST NOT 记为已入池；SKILL 按 fail-loud 处置（报告如实记录失败与
  待人工补录项），MUST NOT 写「已入 todolist」
