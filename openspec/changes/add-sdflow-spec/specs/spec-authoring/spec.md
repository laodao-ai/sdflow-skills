# spec-authoring Delta Specification

## ADDED Requirements

### Requirement: SA-01 单一入口三相位管线，拷问不可跳过

`sdflow-spec` SHALL 以单一入口驱动「澄清（A）→ 拷问（B）→ 生成（C）」三相位管线。相位 A 可在需求已成熟时由主 session 判断提前收束，但相位 B MUST NOT 被跳过——任何进入相位 C 的路径 SHALL 先产出非空决策纪要。skill SHALL 声明 `disable-model-invocation: true`，仅由人触发。

#### Scenario: 需求成熟仍须过拷问
- **WHEN** 用户携带已深思的方案触发 `/sdflow-spec`，主 session 判断澄清可略
- **THEN** 管线直接进入相位 B 拷问；MUST NOT 从对话直接进入相位 C 生成

#### Scenario: 纪要缺失拒绝生成
- **WHEN** 相位 C 起手核验发现决策纪要不存在或必填字段（拍板决策/承重约束）为空
- **THEN** 管线拒绝生成并退回相位 B，向用户说明缺口

### Requirement: SA-02 判断不出主 session，检索与生成外派

主 session SHALL 亲自执行：澄清对话、对抗拷问、决策纪要撰写、终审裁决。检索/调研 SHALL 外派 `sdflow-researcher` 子代理（返回结论 + file:line 出处，原始材料不回传主上下文）；锚点纪要压缩与四件套逐产物生成 SHALL 外派 `sdflow-spec-writer` 子代理。外派 SHALL 遵守阈值：预计读取材料 ≳ 数百行且结论可压缩才派发，其余主 session 直接执行。

#### Scenario: 大材料检索外派
- **WHEN** 拷问需要核验一个横跨多文件、预计数百行以上的代码事实
- **THEN** 主 session 派 `sdflow-researcher`，收到结论与出处；原始文件内容不进入主上下文

#### Scenario: 小查询不外派
- **WHEN** 需要确认单个文件中某常量的值（一次 grep 可得）
- **THEN** 主 session 直接查，不产生子代理派发

#### Scenario: 方案推荐的判断不外派
- **WHEN** 澄清或拷问中出现「≥2 方案需给推荐」
- **THEN** 子代理仅供证据；推荐 + 依据 + 代价 + 备选由主 session 产出

### Requirement: SA-03 拷问技法与停止信号

相位 B SHALL 遵守：一次只问一个问题；每问附主 session 的推荐答案；能自查的事实不问人（先查后给结论）；优先攻击承重约束（其被证伪则依赖它的候选整体重估）。停止信号 SHALL 为「人机共识达成且承重约束清单逐条站稳（有验证方式或证据锚）」，MUST NOT 以「预设问题问完」为停止条件。

#### Scenario: 承重约束优先
- **WHEN** 方案含一个支撑多个候选的前提性约束
- **THEN** 拷问首先核验该约束（派检索供证或要求人确认），后于该约束的派生候选在其站稳前不逐一深究

#### Scenario: 事实类疑问不消耗人的注意力
- **WHEN** 拷问中出现可从仓内/公开资料核验的事实疑问
- **THEN** 主 session 自查或派 researcher，直接给结论；MUST NOT 把该疑问抛给人

### Requirement: SA-04 决策纪要为承重件，/clear 无损

相位 B SHALL 产出主 session 亲笔的决策纪要，字段：目标态一句话、拍板决策（每条含依据 + 砍掉的候选 + 砍的理由）、承重约束清单（每条含验证方式/证据锚）、接受的边角风险；命中 TG-23 的方案选择另含三镜 + 主次判定。纪要 SHALL 作为相位 C 每个生成子代理的输入；生成完成后其内容 SHALL 并入 design.md 决策记录节。验收不变式：`/clear` 后阶段二评审所需的全部 why SHALL 可从落盘产物获得。

#### Scenario: 纪要随派发下发
- **WHEN** 相位 C 派发任一产物的生成子代理
- **THEN** dispatch prompt 含决策纪要全文；子代理 MUST NOT 需要访问阶段一对话历史

#### Scenario: why 落盘完整性
- **WHEN** 阶段一结束、用户执行 `/clear` 后运行 `/sdflow-spec-review`
- **THEN** 评审所需的决策理由、砍掉候选、约束验证均可从 change 目录产物读到，无需回问阶段一对话

### Requirement: SA-05 生成经 openspec CLI，产物契约不变

相位 C SHALL：先执行 FF-0 分支检查（不在 feature 分支则 `git checkout -b feat/{change}`）；经 `openspec new change` 创建 change；按 `openspec status --change <name> --json` 的依赖序**串行**生成产物；每个生成子代理 SHALL 自行调用 `openspec instructions <artifact> --change <name> --json` 获取载荷（MUST NOT 由主 session 转述 instructions 内容）并自行读取依赖产物全文；产物写入 `resolvedOutputPath`。openspec CLI 不可用或报错 SHALL fail-closed 中止并报告，MUST NOT 手工创建 change 目录结构。

#### Scenario: 生成子代理自取载荷
- **WHEN** 派发 tasks.md 生成子代理
- **THEN** 子代理自己执行 `openspec instructions tasks --change <name> --json`，并读取已完成的 design/specs 产物全文，结合下发的决策纪要写出产物

#### Scenario: CLI 缺失 fail-closed
- **WHEN** `openspec` 命令不存在或 `new change` 失败
- **THEN** 管线中止并向人报错；不产生任何手搓的 change 目录

#### Scenario: 产物完成态问 CLI
- **WHEN** 判断某产物是否完成、下一个 ready 产物是哪个
- **THEN** 一律以 `openspec status --json` 输出为准，MUST NOT 自行解析产物内容判断完成态

### Requirement: SA-06 终审只兜判断层

相位 C 生成完毕后，主 session SHALL 读回四件套执行终审：核验产物与决策纪要的一致性（决策遗漏、约束翻转、范围漂移），判断性偏差直接修改；措辞与风格差异 SHALL 放过。终审后 SHALL 按 status 复核全部 `applyRequires` 产物完成。

#### Scenario: 判断性偏差修正
- **WHEN** 终审发现 design.md 遗漏纪要中一条已拍板决策（或与其相反）
- **THEN** 主 session 直接修正该产物并在完成报告中注明

#### Scenario: 风格差异放过
- **WHEN** 终审发现产物措辞风格与主 session 亲写有差异但决策内容一致
- **THEN** 不修改，不进入报告

### Requirement: SA-07 agent 定义承载角色，通则托管，带 fallback

两个 agent 定义 SHALL 位于 `sdflow-spec/agents/`：`sdflow-researcher`（`model: inherit`、`effort: low`、tools 白名单 `Read, Glob, Grep, Bash`）与 `sdflow-spec-writer`（`model: inherit`、`effort: medium`、tools 白名单 `Read, Glob, Grep, Bash, Write`）。定义正文 SHALL 含四条通则托管块，由 `sync_principles.py` 以 skill 味源渲染并由 `hack/tests/` 守卫（MUST NOT 手改块内部）。`setup.sh` SHALL 将其铺设到 `~/.claude/agents/`（含所有权守卫与孤儿清理）。派发 SHALL 优先 `agentType` 引用定义并传 `$SDFLOW_TIER_*` 档位变量；`agentType` 解析失败 SHALL fallback 到 prompt 内联通则路径。SKILL.md 与 agent 定义 MUST NOT 内联具体模型 id。

#### Scenario: agentType 派发携带档位
- **WHEN** Claude 宿主已跑 setup.sh，主 session 派 researcher
- **THEN** 派发使用 `agentType: sdflow-researcher` 且 `model` 参数传 `$SDFLOW_TIER_LIGHT` 或 `$SDFLOW_TIER_MID`（覆盖 frontmatter 的 `inherit`）

#### Scenario: 定义缺失 fallback 内联
- **WHEN** `~/.claude/agents/` 中无 sdflow 定义（未跑 setup 或 Codex 宿主）
- **THEN** 派发退回通用子代理 + prompt 原文内联四条通则；管线继续，完成报告标注该降级

#### Scenario: 投放面机械守卫
- **WHEN** agent 定义正文的通则块与源漂移（或新增 agent 定义未纳入投放面）
- **THEN** `sync_principles.py --check`（setup.sh 每次执行）或 `hack/tests/` 用例变红

### Requirement: SA-08 降级阶梯与如实报告

子代理失败 SHALL 按阶梯降级：researcher 失败 → 主 session 亲查；spec-writer 失败 → 重试一次 → 主 session 亲写该产物。每次降级 SHALL 出现在对人的完成报告中。生成中断时 SHALL 按 `openspec status --json` 如实报告完成/未完成清单，且管线可重入（对 ready 产物继续）。Codex 宿主下整条管线 SHALL 降级为主 session 亲做并在起手时告知用户。MUST NOT 静默降级、MUST NOT 将部分完成报告为完成。

#### Scenario: 生成重试后亲写
- **WHEN** spec-writer 生成 design.md 失败且重试仍失败
- **THEN** 主 session 亲写 design.md，完成报告标注「design.md 经降级亲写」

#### Scenario: 中断可重入
- **WHEN** 管线在生成 specs 后中断，tasks 未生成
- **THEN** 重新触发后按 status 识别 tasks 为 ready，从该产物继续，不重写已完成产物

### Requirement: SA-09 出口序列与衔接

四件套完成并终审通过后，skill SHALL 向用户**原样贴出**出口序列：`/clear` → 切换评审档模型 → `/sdflow-spec-review`，并说明产/审错档理由（一句）。MUST NOT 以转述或省略替代原样贴出。相位完成节点 SHALL 经全局 `checkpoint-commit.sh` 打 checkpoint（slug 含相位标识），拷问多轮中途 MUST NOT 提交。

#### Scenario: 出口提示原样呈现
- **WHEN** 终审完成
- **THEN** 完成报告末尾含可直接照做的三步出口序列文本

#### Scenario: 相位 checkpoint
- **WHEN** 相位 B 收敛（纪要落笔）与相位 C 终审完成
- **THEN** 各产生一次 checkpoint 提交；拷问进行中的任何轮次不产生提交

### Requirement: SA-10 ADR 与术语提议钩子（惰性，只提议不写）

拷问或澄清中命中 ADR 三条件（难以逆转 + 缺乏上下文会令人意外 + 经过真实权衡）的决策，skill SHALL 提议将其落为 `openspec/adr/` 条目，格式锚定同目录既有文件（目录为空时用 SKILL.md 内置最小模板）；发现术语冲突或模糊语言 SHALL 提议更新项目 CONTEXT.md。两者 MUST NOT 未经人确认自动写入。

#### Scenario: ADR 提议
- **WHEN** 拷问中一项决策同时满足三条件
- **THEN** skill 明示「建议落 ADR + 理由」，由人决定；确认后按 `openspec/adr/` 现有格式写入

#### Scenario: 不满足三条件不提议
- **WHEN** 决策可轻易逆转或无真实权衡
- **THEN** 仅记入决策纪要，不产生 ADR 提议
