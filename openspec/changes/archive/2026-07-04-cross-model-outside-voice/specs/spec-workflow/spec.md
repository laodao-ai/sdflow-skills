# spec-workflow Delta — cross-model-outside-voice

## ADDED Requirements

### Requirement: 跨模型 outside voice 默认开、失败回落且非阻塞
sdflow-spec-review 与 sdflow-code-review SHALL 默认启用跨模型 outside voice（codex/GPT 家族「找漏」第二意见）：sdflow-code-review 每次自带 code outside voice；sdflow-spec-review 复用 autoplan 产物中的 outside-voice findings（见反静默守卫 Requirement）。是否启用由环境决定——codex CLI 未安装即天然关停（工作流层不设软 off-switch，〔grill-amendment Q3〕）；codex 不可用（未装/未认证/报错/超时）时 MUST fallback 到同 prompt 的 fresh Claude 子代理；一切失败均为 informational，MUST NOT 阻塞评审流程。报告 outside-voice 留痕 MUST 使用模板写死的 v1 机器锚行（严格 KV、按调用位点复数化、guard/runner 正交）：`<!-- sdflow:outside-voice v1 site="…" guard="…" runner="codex|claude-fallback" reason_code="…" findings="N" truncated="…" -->`（确定性机判，不押自然语言；人类原因文本在锚行外）〔grill-amendment Q5 + spec-review-amendment 文法 v1〕；评审收尾步 MUST 机械自检锚行存在，缺失即报错〔spec-review-amendment〕。

#### Scenario: codex 就绪时跑跨模型 voice
- **WHEN** sdflow-code-review 运行且 codex preflight 返回 ready
- **THEN** 经共享 helper（`render-prompt` 同源拼接，exec 硬编码 `-s read-only --ephemeral`，最终消息经 `--output-last-message` 提取）调 codex（5min 封顶），findings 进合并池，锚行记 `runner="codex"`〔spec-review-amendment〕

#### Scenario: codex 不可用回落 Claude 子代理
- **WHEN** preflight 返回 not_installed
- **THEN** 以 `render-prompt` 输出的同一 prompt 派 fresh Claude 子代理兜底，评审继续不中断，锚行记 `runner="claude-fallback" reason_code="not-installed"`

#### Scenario: exec 超时与报错分别留痕〔spec-review-amendment：原合并场景拆分〕
- **WHEN** exec 超时（exit 124）或非零报错（exit 1，含 auth 失败，stderr 转发）
- **THEN** 分别以 `reason_code="timeout"` / `reason_code="exec-error"`（附 stderr 摘要于锚行外）回落子代理，两类可在报告中区分

#### Scenario: 无 codex 环境天然关停且留痕
- **WHEN** 运行环境未安装 codex CLI
- **THEN** preflight 返回 not_installed，回落 Claude 子代理并留痕，不存在需要另行关闭的软开关〔grill-amendment Q3〕

### Requirement: outside-voice 复用挂反静默守卫
sdflow-spec-review 复用 autoplan 产出的 `gstack-review.md` outside-voice findings 时，SHALL 校验产物有效性，按序判定：①**来源**——`step1-broad-review` 锚行为 `simulated` 则产物一律视同无效（模拟广审可臆造格式合规的 codex 段，结构性检查挡不住）〔spec-review-amendment〕；②**新鲜度**——产物早于 change 最新改动视同缺失（guard=stale）〔spec-review-amendment〕；③**结构**——文件缺失 / 解析不出 codex 段（解析锚定 adr/0002 的 `codex#N` 标签约定）/ findings 为 0 条。任一不过 MUST 打印带原因码（file-missing / section-not-found / zero-findings / stale / simulated-source）的显式降级日志并回落自跑 codex 设计 outside voice，MUST NOT 静默当「本次无 voice」跑过；诱因为文件整体缺失时措辞 MUST 声明「仅补偿 outside-voice 切片，广审其余镜仍缺」〔spec-review-amendment〕。C2 复用的前提是 autoplan 每次都跑（P2b）；若 autoplan 未跑，spec-review MUST 自跑设计 outside voice。

#### Scenario: autoplan 产物有效则复用不重开
- **WHEN** `gstack-review.md` 来源为 native、晚于 change 最新改动、且解析出 ≥1 条 codex outside-voice finding
- **THEN** 直接纳入合并池，不重复调 codex（避免双 codex），报告记「复用 autoplan outside voice N 条」

#### Scenario: 产物缺失或 0 条触发守卫回落
- **WHEN** `gstack-review.md` 缺失 / 解析不出 codex 段 / codex findings 为 0 条
- **THEN** 打印带原因码的降级日志并自跑 codex 设计 voice，锚行记 guard 原因

#### Scenario: 模拟来源或过期产物不得复用〔spec-review-amendment〕
- **WHEN** `gstack-review.md` 的 step1 锚行为 `simulated`，或其内容早于 change 最新改动
- **THEN** 视同产物无效（guard=simulated-source / stale），回落自跑，MUST NOT 因其格式完整而复用

### Requirement: 高风险领域 cross-model 由 HR-TG 子集判定并留痕
两评审 skill 的规划镜头步 SHALL 顺带判定：本变更命中的 TG 集合 ∩ HR-TG 子集 {TG-04, TG-06, TG-07, TG-08, TG-09, TG-16, TG-17, TG-26} 是否非空；非空则单开领域专属 cross-model（聚焦命中的高风险域，「找领域镜漏的」）。判定结果无论正反 MUST 写入报告（可审计）且 MUST 含 v1 机器锚行 `<!-- sdflow:hr-tg v1 hit="…|none" evidence="…" -->`，命中时 evidence 字段 MUST 给出判据触发点（哪处变更对应哪个 TG，30 秒可人工复核——判定本身是 prose 产物，无核验层则误判无人接住）〔grill-amendment Q5 + spec-review-amendment〕；HR-TG 子集清单以 trigger-catalog 为单一源，SKILL 只引用 ID。

#### Scenario: 命中 HR-TG 单开领域 cross-model
- **WHEN** 规划镜头判定命中 TG-08（外部依赖）
- **THEN** 单开一次领域 cross-model（codex，失败照常回落），报告记「命中 TG-08 → 已跑领域 cross-model」

#### Scenario: 未命中则不开且留痕
- **WHEN** 命中集 ∩ HR-TG = ∅
- **THEN** 不开领域 cross-model，报告记「HR-TG 判定：未命中」

### Requirement: outside-voice tension 不静默采纳
outside voice 与主审分歧（tension）SHALL 中立并陈、标 TENSION：sdflow-spec-review 写入报告决策登记区（选项 + 推荐 + 两方视角，设计 HARD-GATE 人一次性拍板）；sdflow-code-review 有把握则自动裁决并记理由、拿不准则 defer 进 buglist/todolist + hand-off。outside voice 的建议 MUST NOT 被静默自动采纳（不直接改代码/设计而不留痕）。**`runner=codex`** 的 outside-voice findings MUST NOT 经自评置信阈值（<80）预过滤——跨模型自评不可比、异见易被同族标尺误杀——一律直通对抗裁决，被裁掉的连理由落报告「已裁掉」区〔grill-amendment Q4〕；`runner=claude-fallback` 的 findings 属同族产物，照过同族置信滤（豁免理由对其不成立）〔spec-review-amendment〕。

#### Scenario: 设计侧分歧进决策登记区
- **WHEN** codex voice 与 spec-review 主审对同一设计点结论相反
- **THEN** 报告决策登记区新增 TENSION 条目（两方观点 + 推荐 + 后果），不中途 AskUserQuestion

#### Scenario: 代码侧分歧自动裁决或 defer
- **WHEN** codex voice 与 code-review 主审分歧且裁决无客观判据
- **THEN** defer 进 issues 池并写入 hand-off，不静默采纳任一方

#### Scenario: 低自评置信的 codex finding 不被预筛
- **WHEN** 某条 `runner=codex` 的 finding 自评置信低于 Step3 阈值（<80）
- **THEN** 该条仍进入对抗裁决（不被置信滤拦截）；若裁决不成立，连理由落报告「已裁掉」区

#### Scenario: fallback finding 照过同族滤〔spec-review-amendment〕
- **WHEN** 某条 `runner=claude-fallback` 的 finding 自评置信低于阈值
- **THEN** 按同族 findings 常规处理（过滤规则一致），不享受跨模型豁免

### Requirement: 广审层原生执行，模拟必须显式标注降级
两评审 skill 的 Step1 广审（sdflow-spec-review 的 autoplan、sdflow-code-review 的 gstack /review）SHALL 由主 session 经 Skill 机制原生执行（其指令直接进主 session，非子代理读 SKILL.md 转述模拟）。原生执行完成后由主 session 汇总结论落盘 `gstack-review.md`（广审工具自身无「写任意路径」机制，落盘责任在编排方）〔spec-review-amendment〕。原生执行不可用时 MUST 降级为模拟广审，且报告与运行日志 MUST 显式标注「模拟广审（降级模式）」，MUST NOT 把模拟呈现为原生运行；报告 Step1 段 MUST 含 v1 机器锚行 `<!-- sdflow:step1-broad-review v1 mode="native|simulated" -->`，native 声明建议附侧信道佐证（如广审工具自身的运行痕迹）〔grill-amendment Q5 + spec-review-amendment〕。

#### Scenario: 正常路径原生执行 autoplan
- **WHEN** sdflow-spec-review Step1 启动且 autoplan skill 可用
- **THEN** 主 session 原生执行 autoplan（含其 preamble/telemetry/自动决策全流程），产出 `gstack-review.md`

#### Scenario: 原生不可用显式降级
- **WHEN** autoplan / gstack review skill 不可用（未安装等）
- **THEN** 以子代理模拟广审，报告显式标注「模拟广审（降级模式）」及原因

### Requirement: gstack 边界守恒——读产出物合法、依赖内部禁止
自制 outside-voice 机制（共享 helper、spec-review 回落自跑、code-review code voice）SHALL 只依赖 codex CLI 本身，MUST NOT 调用、复制或修改 gstack/superpowers 内部 bin、探针、config；gstack 自家 skill（autoplan / gstack review）的原生 outside voice 原样不动。读取 gstack 的产出物（如 `gstack-review.md`）合法，不属内部依赖。

#### Scenario: 实现不触碰 gstack 内部
- **WHEN** 本 change 实现完成
- **THEN** 变更 diff 不含任何 gstack 安装目录/内部文件；helper 源码 grep 不到 gstack 内部路径引用

#### Scenario: 无 codex 无 gstack 环境审查不中断
- **WHEN** 在既无 codex CLI 也无 gstack 的环境运行两评审 skill
- **THEN** outside voice 退化为 fresh-context Claude 子代理（独立性保留、丢跨模型），评审完整跑完
