## MODIFIED Requirements

### Requirement: 模型档位映射（model-tiers）

模型档位定义、职责清单与 canonical 缺省 MUST 以 workflow bundle 规则文件 **`model-tiers.md`** 为单一真相源（经 resolver 全局解析；强档=verify/对抗裁决/final 终审；中档=领域镜/生成/实现；弱档=纯机械步）〔grill-amendment：推翻"config 段真相源 + SKILL 内联缺省×4"——多处 copy 漂移面〕。**档位映射 MUST 按机队分列**〔add-codex-host-support〕：Claude 机队缺省 opus/sonnet/haiku、Codex 机队缺省 gpt-5.6-sol/gpt-5.6-terra/gpt-5.6-luna（机队锚定，adr/0006(c)——档位是相对执行机队的相对词，不绑单一产品线）。**当前机队 MUST 由 `resolve-models.sh` 按宿主正信号判定**（见能力 `host-adaptive-execution`），编排 skill MUST 引用其导出的 `SDFLOW_TIER_*` 变量。消费仓 `config.yaml` 的 `model-tiers` 段 MUST 仅作可选 per-repo **覆盖**；编排 skill（sdflow-ship/done/spec-review/code-review）的模型选择 MUST 以一句引用指向规则文件与覆盖段，MUST NOT 内联具体模型名。

#### Scenario: 消费仓无覆盖段用 canonical 缺省
- **WHEN** 消费仓 config.yaml 无 model-tiers 段，跑任一编排 skill
- **THEN** skill 按规则根 `model-tiers.md` 中**当前宿主所属机队**的 canonical 缺省档位运行，MUST NOT 报错、MUST NOT 静默降级门禁步模型

#### Scenario: verify 档位来自映射（覆盖优先）
- **WHEN** 消费仓 config.yaml model-tiers 段把强档覆盖为某模型
- **THEN** sdflow-done 的 verify 子代理按覆盖映射选模型；无覆盖时用规则文件中本机队的强档缺省，MUST NOT 落到弱档

#### Scenario: 同一门禁步在两宿主下各取本机队档位〔add-codex-host-support〕
- **WHEN** verify 步分别在 Claude 宿主与 Codex 宿主运行且无 per-repo 覆盖
- **THEN** 前者取 Claude 机队强档、后者取 Codex 机队强档；两者 MUST NOT 因宿主切换而降档（门禁步禁降档是硬约束）

### Requirement: 跨模型 outside voice 默认开、失败回落且非阻塞

sdflow-spec-review 与 sdflow-code-review SHALL 默认启用跨模型 outside voice（**另一个机队**的「找漏」第二意见）：sdflow-code-review 每次自带 code outside voice；sdflow-spec-review 复用 autoplan 产物中的 outside-voice findings（见反静默守卫 Requirement）。

**runner MUST 由宿主决定，MUST NOT 硬编码**〔add-codex-host-support〕：runner 恒为**当前宿主之外的另一个机队的强档**（Claude 宿主 → Codex；Codex 宿主 → Claude）。`preflight` MUST 探测**目标 runner 的 CLI**，而非固定探测 codex——固定探测 codex 会在 Codex 宿主下返回 ready 并导致 **codex 自审 codex**，是必须杜绝的假绿。是否启用由环境决定——目标 runner CLI 未安装即天然关停（工作层不设软 off-switch，〔grill-amendment Q3〕）；目标 runner 不可用（未装/未认证/报错/超时）时 MUST fallback 到同 prompt 的 fresh **同宿主**只读子代理，且该轮 `runner == host`（如实标为非跨模型）；宿主判不出（`host="unknown"`）时 MUST NOT 跑 voice（无从确定"另一个机队"）。一切失败均为 informational，MUST NOT 阻塞评审流程。

报告 outside-voice 留痕 MUST 使用模板写死的 v1 机器锚行（严格 KV、按调用位点复数化、guard/runner 正交）：`<!-- sdflow:outside-voice v1 site="…" guard="…" host="claude|codex|unknown" runner="claude|codex" reason_code="…" findings="N" truncated="…" -->`〔add-codex-host-support：新增 `host=`；`runner` 枚举收缩为机队家族，**`claude-fallback` 废弃**——「跨模型性」自此为派生量 `runner ≠ host`，MUST NOT 再编码进枚举值〕（确定性机判，不押自然语言；人类原因文本在锚行外）〔grill-amendment Q5 + spec-review-amendment 文法 v1〕；评审收尾步 MUST 机械自检锚行存在，缺失即报错〔spec-review-amendment〕。

#### Scenario: Claude 宿主下跑跨模型 voice
- **WHEN** sdflow-code-review 运行于 `host=claude` 且 codex preflight 返回 ready
- **THEN** 经共享 helper（`render-prompt` 同源拼接，exec 硬编码 `-s read-only --ephemeral`，最终消息经 `--output-last-message` 提取）调 codex（5min 封顶），findings 进合并池，锚行记 `host="claude" runner="codex"`

#### Scenario: Codex 宿主下跑跨模型 voice〔add-codex-host-support〕
- **WHEN** sdflow-code-review 运行于 `host=codex` 且 `claude` CLI preflight 返回 ready
- **THEN** 经**同一个** helper（同一 `render_prompt`/`secret_scan`/截断）调 `claude -p --model <Claude 强档> --output-format text --disallowedTools Write Edit NotebookEdit`，findings 进合并池，锚行记 `host="codex" runner="claude"`

#### Scenario: 目标 runner 不可用回落同宿主子代理
- **WHEN** preflight 返回 not_installed（目标 runner 的 CLI 未装）
- **THEN** 以 `render-prompt` 输出的同一 prompt 派 fresh 同宿主只读子代理兜底，评审继续不中断，锚行记 `runner` 等于 `host` + `reason_code="not-installed"`（该轮非跨模型，如实可见）

#### Scenario: exec 超时与报错分别留痕〔spec-review-amendment：原合并场景拆分〕
- **WHEN** exec 超时（exit 124）或非零报错（exit 1，含 auth 失败，stderr 转发）
- **THEN** 分别以 `reason_code="timeout"` / `reason_code="exec-error"`（附 stderr 摘要于锚行外）回落同宿主子代理，两类可在报告中区分

#### Scenario: 无目标 runner 环境天然关停且留痕
- **WHEN** 运行环境未安装目标 runner 的 CLI
- **THEN** preflight 返回 not_installed，回落同宿主只读子代理并留痕，不存在需要另行关闭的软开关〔grill-amendment Q3〕

#### Scenario: 宿主判不出则不跑 voice〔add-codex-host-support〕
- **WHEN** `CLAUDECODE` 与 `CODEX_THREAD_ID` 两个正信号皆无（或同时存在，信号冲突）
- **THEN** 本轮 MUST NOT 跑 outside voice；锚行记 `host="unknown" reason_code="host-unknown"`；报告显著标注本轮无跨模型第二意见，MUST NOT 任选一个 runner 跑了充作跨模型

### Requirement: outside-voice tension 不静默采纳

outside voice 与主审分歧（tension）SHALL 中立并陈、标 TENSION：sdflow-spec-review 写入报告决策登记区（选项 + 推荐 + 两方视角 + **三面后果（系统 / 用户 / 开发循环）+ 主次判定**，设计 HARD-GATE 人一次性拍板）；sdflow-code-review 按 T10 三级协议自动裁决（有客观判据自动裁 / 无则派对抗镜复核 / 复核不过或无从复核则 defer 进 buglist/todolist + hand-off）并**按三镜 + 主次记理由**，MUST NOT 以自评置信（"有把握"）为自动裁决唯一依据〔impl-review-fix F1/CV2〕。outside voice 的建议 MUST NOT 被静默自动采纳（不直接改代码/设计而不留痕）。

**置信过滤豁免 SHALL 按「是否跨机队」判定，MUST NOT 按 runner 枚举值硬编码**〔add-codex-host-support〕：**`runner ≠ host`**（真跨模型）的 outside-voice findings MUST NOT 经自评置信阈值（<80）预过滤——跨模型自评不可比、异见易被同族标尺误杀——一律直通对抗裁决，被裁掉的连理由落报告「已裁掉」区〔grill-amendment Q4〕；**`runner == host`**（同族 fallback）的 findings 属同族产物，照过同族置信滤（豁免理由对其不成立）。

> 〔为何改判据〕旧规则写死 `runner=codex` 豁免——该值在 **Codex 宿主**下恰恰意味着**自审**，旧规则会给自审发放跨模型豁免。判据必须是关系式 `runner ≠ host`，不是枚举值。

#### Scenario: 设计侧分歧进决策登记区
- **WHEN** outside voice 与 spec-review 主审对同一设计点结论相反
- **THEN** 报告决策登记区新增 TENSION 条目（两方观点 + 推荐 + 三面后果 + 主次判定），不中途 AskUserQuestion

#### Scenario: 代码侧分歧自动裁决或 defer
- **WHEN** outside voice 与 code-review 主审分歧且裁决无客观判据
- **THEN** defer 进 issues 池并写入 hand-off，不静默采纳任一方

#### Scenario: 低自评置信的跨模型 finding 不被预筛
- **WHEN** 某条 `runner ≠ host` 的 finding 自评置信低于 Step3 阈值（<80）
- **THEN** 该条仍进入对抗裁决（不被置信滤拦截）；若裁决不成立，连理由落报告「已裁掉」区

#### Scenario: 同族 fallback finding 照过同族滤
- **WHEN** 某条 `runner == host` 的 finding 自评置信低于阈值
- **THEN** 按同族 findings 常规处理（过滤规则一致），不享受跨模型豁免

#### Scenario: Codex 宿主下的 codex findings 不再误享豁免〔add-codex-host-support〕
- **WHEN** `host="codex"` 且某条 finding 的 `runner="codex"`（同族 fallback 产物）
- **THEN** 照过同族置信滤，MUST NOT 因 `runner` 值恰为 `codex` 而豁免（旧规则的假绿点）
