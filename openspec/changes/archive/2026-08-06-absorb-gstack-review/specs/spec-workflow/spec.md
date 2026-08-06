## MODIFIED Requirements

### Requirement: sdflow-code-review 为每次全跑的独立强制主审

阶段三的 `sdflow-code-review` MUST **每次必跑**、以独立冷视角作为强制代码评审主审（依据实测能抓真问题），MUST **恒产 code-review-report.md**，SHALL NOT 跳过代码评审、SHALL NOT 降级为「高风险才跑的残差抽查」（**默认开、仅机判无逻辑面才关**，非风险判断 gate-on）。深度按**两层**规则：

- **Step1（scope 审计：scope-drift + 计划完成度，自持）MUST 每次必跑**，MUST NOT 因任何判定降级或跳过——既是便宜的评审地板，又是**验白名单形状诚实性的守卫**（自称无逻辑面的 diff 若偷藏逻辑改动，scope-drift 抓）。执行位 SHALL 为 fresh 子代理（消除「主 session 携带生成历史、自查自己顺手多改」的结构性偏置）；**意图源 SHALL 锚 OpenSpec 四件套**（proposal 的 scope/Non-Goals + tasks.md + design.md，确定性来源，MUST NOT 依赖 plan-file 路径猜测或 commit-message 推断作为首选意图源）；子代理不可用时 SHALL 降级主 session 亲做并在报告显著标注「scope 审计降级（存在自查偏置）」，恒跑语义不变。报告锚 `step1-broad-review` 的 `mode` SHALL 如实记执行位（`subagent`=子代理独立完成 | `main-session`=降级亲做）。能力探针 SHALL 于第零步（宿主/档位解析同位）一次性执行，Step1 与 Step2 共用**同一次**探针结果（`fanout-capability` 锚每轮恰一条的既有约束不变，MUST NOT 为 Step1 另探一次落第二条锚）〔spec-review-amendment〕。
- **Step2（多镜 fan-out：领域镜+对抗镜+历史镜+置信过滤+对抗裁决）MUST 对任何含行为/逻辑面的 change 每次全跑**；**仅当** change 的 diff **机判命中「无逻辑面白名单形状」**时可免 Step2（多镜结构上零产出）。免除 MUST 由 Step1 scope-drift 守卫：scope-drift 揭出隐藏逻辑 → 白名单判定作废 → Step2 照跑。**守卫时序 SHALL 钉死**〔spec-review-amendment〕：diff 命中白名单形状（EXEMPT 候选）时，Step2 的免除判定 MUST **阻塞等待 Step1 结果收齐后**才可定案（否则 Step1 迟到的揭穿换不回已跳过的多镜，守卫空转）；diff 非白名单形状（Step2 反正要跑）时，Step1 MAY 与 Step2 fan-out 并行、结果在 Step3 barrier 收齐。

**无逻辑面白名单形状**（机判、post-diff、由确定性脚本判，MUST NOT 依作者自评）SHALL 仅含：①`diff 仅动代码内注释行（语言感知）或约定文档文件`——约定文档**扩展名锚定**：`VERSION` / `README·CHANGELOG·LICENSE·NOTICE`（无扩展或 `.md/.rst/.txt`）/ `.rst` / `docs/` 下 `.md·.rst·.txt`；**裸 `*.txt` 不算文档**（`requirements.txt`/`runtime.txt` 等依赖 pin 是 load-bearing，落 NOT）、**`docs/` 下 `.py` 等源码不算文档**（按代码判定）、**任意其他 `.md`（消费仓散落 markdown 可能承载行为）默认 NOT**；②`diff 仅新增 tests/ 下文件`（排除 import 副作用 `conftest.py`/`__init__.py`）；③版本常量收窄为 `VERSION`/`CHANGELOG`（代码里的 `API_VERSION`/`SCHEMA_VERSION` 无法机判是否切 code-path → NOT）。判器 MUST **语言感知**（按语言解析注释/块注释/多行字符串边界，MUST NOT 裸正则前缀）；MUST 应用**行为面路径豁免清单**——凡 diff 触及 workflow bundle 自身（`sdflow-init/assets/workflow/**`、编排/评审 `SKILL.md`、`ship_gate.py`、`route`/判器脚本、`workflow.md`）即 NOT 无逻辑面（**这些 markdown/脚本承载行为，非文档**），即便 diff 形状看似「仅动 markdown」；`tests/` 豁免 MUST 排除被生产码 import 的 test helper（如 `conftest.py`）；版本常量 MUST 整行匹配 `^\s*<IDENT>\s*=\s*<version-literal>\s*$` 且拒绝任何附加 token（防夹带 `API_VERSION`/`SCHEMA_VERSION` 等切 code-path 的 load-bearing 常量）。

#### Scenario: 有逻辑面的普通变更 Step2 多镜照跑
- **WHEN** 一个含逻辑改动的变更完成实现（不匹配任何白名单形状）
- **THEN** sdflow-code-review 的 Step1 与 Step2 多镜 fan-out 均 MUST 全跑，MUST NOT 因「routine/低风险」而免多镜

#### Scenario: 纯注释/文档 diff 免 Step2 但 Step1 恒跑
- **WHEN** 一个 diff 仅动注释/纯文档行（语言感知判定、且不触行为面路径清单）的变更
- **THEN** Step1（scope-drift+完成度）MUST 跑；确认无隐藏逻辑后 Step2 多镜可免（结构零产出），仍产 code-review-report.md

#### Scenario: scope-drift 揭穿伪装的白名单形状
- **WHEN** 某 change 自称「仅改注释」但 Step1 scope-drift 揭出顺手改了逻辑
- **THEN** 白名单判定 MUST 作废、Step2 多镜 MUST 照跑

#### Scenario: 改 bundle/SKILL/gate 自身即便是 markdown 也不免多镜
- **WHEN** 一个 diff 只改 `sdflow-code-review/SKILL.md` 或 `workflow.md` 一行指令（形状=仅动 markdown）
- **THEN** 判器 MUST 因行为面路径豁免清单判其 NOT 无逻辑面 → Step2 多镜照跑，MUST NOT 因「仅动 markdown」误免（bundle markdown 承载行为）

#### Scenario: load-bearing 版本常量不免多镜
- **WHEN** 一个 diff 改 `API_VERSION = 2` 或 `SCHEMA_VERSION`（切 code-path/契约）
- **THEN** 判器 MUST NOT 判其为白名单版本常量（其有 code-path 依赖）→ Step2 照跑

#### Scenario: Step1 scope 审计由 fresh 子代理执行并如实落锚
- **WHEN** 一轮 sdflow-code-review 启动且子代理机制可用
- **THEN** scope 审计 SHALL 由 fresh 子代理执行（输入含 proposal/tasks/design + diff），其结构化 findings SHALL 进 Step3 合并池按普通 finding 裁决（informational shift-left，不设人类门）；报告锚 SHALL 落 `mode="subagent"`

#### Scenario: 子代理不可用时 Step1 降级亲做但不跳过
- **WHEN** 能力探针判 `subagents="unavailable"`
- **THEN** scope 审计 SHALL 由主 session 亲做同一审计协议（恒跑守卫不变），报告 SHALL 显著标注降级与自查偏置，锚 SHALL 落 `mode="main-session"`；MUST NOT 以子代理不可用为由跳过 Step1

#### Scenario: 完成度审计按五态分类且判定纪律钉死
- **WHEN** scope 审计对 tasks.md 逐 task 判完成度
- **THEN** SHALL 用五态 `DONE / PARTIAL / NOT DONE / CHANGED / UNVERIFIABLE` 分类，且 SHALL 遵守：DONE 从严（须 diff 内具体证据，碰过文件不等于做了）、CHANGED 从宽（换路径达成同目标算完成并注明差异）、UNVERIFIABLE 诚实（diff 证明不了的外部状态 MUST 如实列为待人工核验项，MUST NOT 静默判 DONE）、**PARTIAL = 部分子项有 diff 内证据而其余没有、NOT DONE = diff 内无任何相关证据**〔spec-review-amendment〕；审计产出 SHALL 含**逐 task 五态表**（每 task：状态 + 一句证据引用，DONE/CHANGED 也在列，非仅负向态），负向态（NOT DONE/PARTIAL/UNVERIFIABLE）与 SCOPE-CREEP 各生成一条 finding 进 Step3 合并池、CHANGED 以注明差异的表行承载不单独出 finding；**本审计为 informational shift-left，MUST NOT 勾改 tasks.md 复选框、MUST NOT 替代 sdflow-done verify 终审（verify 为最终权威）**〔spec-review-amendment〕

#### Scenario: gstack 不在场时评审全流程可跑通
- **WHEN** 运行机器未安装 gstack skill
- **THEN** sdflow-code-review 全流程 SHALL 正常完成（Step1 无降级日志、无模拟分支）——scope 审计为自持能力，MUST NOT 依赖任何 gstack 资产在场

### Requirement: 广审层原生执行，模拟必须显式标注降级

〔spec-review-amendment：本 Requirement 原文点名「sdflow-code-review 的 gstack /review」并把锚 mode 钉死为 `native|simulated`——code-review Step1 自持化后该措辞与上方 Requirement 自相矛盾，本 delta 将其收窄为仅 spec-review 侧；code-review 层 Step1 的执行位与 mode 枚举（`subagent|main-session`）由「sdflow-code-review 为每次全跑的独立强制主审」Requirement 独立承载。〕

**sdflow-spec-review 的 Step1 广审（autoplan）**SHALL 由主 session 经 Skill 机制原生执行（其指令直接进主 session，非子代理读 SKILL.md 转述模拟）。原生执行完成后由主 session 汇总结论落盘 `gstack-review.md`（广审工具自身无「写任意路径」机制，落盘责任在编排方）〔spec-review-amendment〕。原生执行不可用时 MUST 降级为模拟广审，且报告与运行日志 MUST 显式标注「模拟广审（降级模式）」，MUST NOT 把模拟呈现为原生运行；报告 Step1 段 MUST 含 v1 机器锚行 `<!-- sdflow:step1-broad-review v1 mode="native|simulated" -->`（此枚举仅约束 spec-review 层的 `gstack-review.md` 产物），native 声明建议附侧信道佐证（如广审工具自身的运行痕迹）〔grill-amendment Q5 + spec-review-amendment〕。

#### Scenario: 正常路径原生执行 autoplan
- **WHEN** sdflow-spec-review Step1 启动且 autoplan skill 可用
- **THEN** 主 session 原生执行 autoplan（含其 preamble/telemetry/自动决策全流程），产出 `gstack-review.md`

#### Scenario: 原生不可用显式降级
- **WHEN** autoplan skill 不可用（未安装等）
- **THEN** 以子代理模拟广审，报告显式标注「模拟广审（降级模式）」及原因

## ADDED Requirements

### Requirement: 代码审 finding 须引出触发行原文（pre-emit 引文纪律）

Step2 各镜子代理产出的每条 finding MUST 附「触发该 finding 的具体代码行」（file:line + 逐字引文）；引文指向框架元构造生成的符号时（ORM 声明/装饰器/迁移文件），SHALL 引创建该符号的元构造原文而非期待字面名出现在类体。**非局部 finding（缺失校验 / 跨文件数据流 / 时序竞态 / absence 类——无单一触发行者）SHALL 以「可复核证据包」替代单行引文**：多处 file:line 逐字引文、或「应在而不在」的缺失对照（引出本应包含该防护的位置原文），仍 MUST 可复核定位；MUST NOT 因「引不出单一触发行」把此类 finding 一律压到 ≤50（否则与 CR-11「必须读 diff 外代码」自相矛盾、系统性压制依赖链/时序/缺失性 bug）〔spec-review-amendment〕。既无单行引文、又无可复核证据包的 finding，其自报置信 MUST ≤50；Step3 置信过滤 SHALL 将其滤出主结论，并按反静默压制条款在「已裁掉」区一行留痕（可审计）。

本纪律为**产出纪律非机械门**——引文真实性由子代理自报，无机械核验路径；SKILL 与报告 MUST NOT 声称其为机械保证。**本纪律仅约束 Step2 各镜的代码 finding，不作用于 Step1 scope 审计的任务级证据**（后者的证据形态为 diff 内证据/task 条目引用，由五态判定纪律独立约束）〔spec-review-amendment〕。

#### Scenario: 引不出触发行的 finding 被滤出主结论
- **WHEN** 某镜报出「字段 X 不存在于模型 Y」类 finding 但未引出模型 Y 定义处的逐字代码行
- **THEN** 该 finding 自报置信 MUST ≤50 → Step3 SHALL 滤出主结论并在「已裁掉」区一行留痕，MUST NOT 以置信 ≥80 直接进 Findings 主区

#### Scenario: 引文纪律不豁免反静默压制
- **WHEN** 无引文 finding 被滤除
- **THEN** 该滤除 SHALL 可审计（已裁掉区一行带过），MUST NOT 静默丢弃
