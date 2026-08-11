# spec-workflow delta — implement-workflow-optimization-2026-08-p2

## ADDED Requirements

### Requirement: 评审裁决协议为机械前置 + 二元裁决 + 置信降排序

两评审 skill（sdflow-spec-review / sdflow-code-review）的裁决入口 SHALL 为三层各司其职（`adr/0041`）：

1. **机械引用核（前置门，确定性脚本）**：输入 SHALL 为结构化 JSON（每条 finding 带 `{file, line, quote}` 或 `evidence_pack` 机读字段，由 Step2 各镜输出契约保证；脚本 MUST NOT 解析 markdown 散文）〔spec-review-amendment〕。逐条核 finding 的引用真实性——引用路径存在、`file:line` 落在文件行数内、单行引文**命中所报行（或显式行范围）**〔spec-review-amendment：整文件子串核可被任意行号 + 他处文本绕过〕（spec-review 侧核对象含 change 四件套文档与代码）。输出三态〔spec-review-amendment〕：pass；fail（结构化字段在、任一查不过，或既无单行引文又无可复核证据包 ⇒ **机械落报告「已裁掉」区**，来源标 `[ref-check]` 与裁决裁掉项可区分）；**uncheckable**（引用为证据包 / 设计层引用等非干净 `path:N` 形态 ⇒ 不裁，原样直进二元裁决并标注未经机械核）。脚本本体不可恢复错误 SHALL 显式降级（整批标 `[ref-check-unavailable]` 直进二元裁决 + 报告显著标注机械门未生效，MUST NOT 呈现「全部 pass」假象、MUST NOT 阻断报告产出）〔spec-review-amendment〕。引文与断言的**语义对应**不在本层职责（归二元裁决）。脚本输出 SHALL 遵循消费型信号校验器输出诚实原则（不得 emit 与「已完整验证」不可区分的裸通过码）。
2. **二元裁决（强档）**：每条通过前置门的 finding SHALL 裁 `采纳 / 裁掉 / defer` 三态之一并附一句 critique 理由；裁「裁掉」的连理由落「已裁掉」区（反静默压制既有条款不变）。
3. **自报置信降级为排序信号**：置信仅 MAY 用于裁决处理顺序与报告排序，**MUST NOT 作为滤除门**——协议中 MUST NOT 存在任何数值置信阈值滤除（含封顶式间接滤除）。severity SHALL 保留为输出字段，**MUST NOT 作门**（与置信同为自报信号）。

同构边界：以上三层为两 skill 共同的「裁决动作层」；sdflow-spec-review 的「拿不准 → 决策登记区」人门路由 SHALL 保留（与置信数字脱钩，服务设计 HARD-GATE），sdflow-code-review 无人门、按既有 `T10-choice` / defer 路径处置，两侧 Step3 条款不要求全文同构。

#### Scenario: 引用失实的 finding 被机械裁掉且留痕
- **WHEN** 某条 finding 引用的 `file:line` 超出目标文件行数，或其单行引文不命中所报行〔spec-review-amendment〕
- **THEN** 该条不进入二元裁决，落「已裁掉」区并标 `[ref-check]` 与失败原因；MUST NOT 静默丢弃

#### Scenario: 非干净引用形态的 finding 不被机械错杀〔spec-review-amendment〕
- **WHEN** 某条 finding 的证据为证据包 / 设计层引用（如指向 proposal 决策点），无干净 `path:N` 三元组
- **THEN** 机械核判 uncheckable、不裁，该条原样进入二元裁决并标注未经机械核；MUST NOT 因形态非 `path:N` 落「已裁掉」区

#### Scenario: 机械核脚本崩溃时显式降级不假绿〔spec-review-amendment〕
- **WHEN** `findings_ref_check.py` 本体 crash 或输入 JSON 畸形
- **THEN** 整批 findings 标 `[ref-check-unavailable]` 直进二元裁决，报告显著标注机械门未生效；MUST NOT 静默呈现「全部 pass」，MUST NOT 阻断报告产出

#### Scenario: 低自报置信的 finding 不被滤除
- **WHEN** 某条 finding 自报置信极低（如 30）但引用核通过
- **THEN** 该条 MUST 进入二元裁决（置信只影响处理顺序）；裁决按 critique 理由定采纳/裁掉/defer，MUST NOT 因置信数字直接滤除

#### Scenario: 引文真实但断言不成立的 finding 由裁决层裁掉
- **WHEN** 某条 finding 的引文确实命中所报行（引用核通过），但其断言与代码语义不符〔spec-review-amendment〕
- **THEN** 二元裁决裁「裁掉」并附 critique 理由落「已裁掉」区——语义判断归裁决层，机械层 MUST NOT 越权判语义

### Requirement: 镜 roster 条件化派发（降采样）

评审 skill 的 roster 段 MAY 为单个镜声明**派发条件**（降采样处置的实现形态）。约束：

- 条件 MUST 为 dispatch 时**机械可判**的信号（TG 命中 / diff 规模 / 栈 / change 类型），**MUST NOT 引入运行时模型自判难度路由**。
- 条件判「本轮不派」的镜 MUST 照落 lens-metric 锚行（`runner="none"`、`findings=0`）〔设计门 Q1：合法组合矩阵扩展，condition-not-met 不进锚字段，跳过成因由 `mirror-dispositions.yaml` condition 字段 + 报告散文承载〕——跳过 MUST 可审计，MUST NOT 以不落锚的方式静默消失。
- 复评处置决定（保留 / 降采样 / 淘汰 / 不适用）SHALL 记录于 `openspec/retro/mirror-dispositions.yaml`（匹配键与 lens-metric 聚合分组键同构），roster 段改动与处置记录 SHALL 同轮一致。
- roster 处置改动与裁决协议改动 SHALL 落独立 commit，可分别 revert。

#### Scenario: 条件不满足的镜跳过但留锚
- **WHEN** 某镜声明派发条件「diff 含 rename 或触碰既有文件 ≥ N」且本轮 diff 不满足
- **THEN** 该镜不派发，本轮报告仍落其锚行 `runner="none" findings="0"`（合法组合矩阵扩展〔设计门 Q1〕），报告可见一行跳过说明；跳过成因在 `mirror-dispositions.yaml` condition 字段机读可查

#### Scenario: 条件满足照常派发
- **WHEN** 该镜的派发条件被本轮 diff 满足
- **THEN** 照常 fan-out，锚行按实际执行落，与无条件镜无差别

## MODIFIED Requirements

### Requirement: outside-voice tension 不静默采纳

outside voice 与主审分歧（tension）SHALL 中立并陈、标 TENSION：sdflow-spec-review 写入报告决策登记区（选项 + 推荐 + 两方视角 + **三面后果（系统 / 用户 / 开发循环）+ 主次判定**，设计 HARD-GATE 人一次性拍板）；sdflow-code-review 按 `T10-choice` 三级协议自动裁决（有客观判据自动裁 / 无则派 **strong 档**对抗镜复核 / 复核不过或无从复核则 defer 进 buglist/todolist + hand-off）并**按三镜 + 主次记理由**，MUST NOT 以自评置信（"有把握"）为自动裁决唯一依据〔impl-review-fix F1/CV2〕。outside voice 的建议 MUST NOT 被静默自动采纳（不直接改代码/设计而不留痕）。

**裁决入口对一切 findings 一视同仁**〔adr/0041〕：outside-voice findings（无论 `runner` 取值）与同族镜 findings 走同一「机械引用核 → 二元裁决」入口（见「评审裁决协议为机械前置 + 二元裁决 + 置信降排序」），不存在自评置信预过滤，也不再存在按合法组合矩阵的豁免通道——豁免机制随数值滤废除而失去对象。合法组合矩阵仍由 anchor_lint 用于 lens-metric 跨模型性度量，**MUST NOT 在裁决路径被重新引用为过滤或豁免判据**。被裁掉的连理由落报告「已裁掉」区不变。

#### Scenario: 设计侧分歧进决策登记区
- **WHEN** outside voice 与 spec-review 主审对同一设计点结论相反
- **THEN** 报告决策登记区新增 TENSION 条目（两方观点 + 推荐 + 三面后果 + 主次判定），不中途 AskUserQuestion

#### Scenario: 代码侧分歧派 strong 档自动裁决或 defer
- **WHEN** outside voice 与 code-review 主审分歧且裁决无客观判据
- **THEN** 派 strong 档对抗镜复核，复核不过或无从复核则 defer 进 issues 池并写入 hand-off，不静默采纳任一方，MUST NOT 用 mid 档同档互判代替

#### Scenario: 跨模型与同族 finding 同一裁决入口
- **WHEN** 同一轮 Step3 合并池同时含跨模型 outside-voice finding 与同族镜 finding
- **THEN** 两者走同一「机械引用核 → 二元裁决」路径，均不经任何数值置信滤，也无豁免分支；裁掉的各自连理由落「已裁掉」区

#### Scenario: 无执行轮无裁决对象
- **WHEN** 某 outside-voice 锚 `runner="none"`（该轮无执行）
- **THEN** 其 findings 恒 0、无任何条目进入裁决入口；MUST NOT 出现「对无执行轮豁免/过滤」的判定分支

#### Scenario: 低自评置信的跨模型 finding 不被预筛
- **WHEN** 某条跨模型 outside-voice finding 自报置信极低
- **THEN** 该条仍进入「机械引用核 → 二元裁决」（新协议下**任何** finding 都不被置信预筛，本保证从跨模型专属扩展为全量默认）；裁决不成立则连理由落「已裁掉」区

#### Scenario: 同族 fallback finding 照过同族滤
- **WHEN** 某条 `runner == host` 的同族 fallback finding 进入 Step3
- **THEN** 〔adr/0041 语义更新：「同族置信滤」已废除〕该条与其他 findings 走同一「机械引用核 → 二元裁决」入口，无任何按 runner 分流的特殊处理分支

#### Scenario: Codex 宿主下的 codex findings 不再误享豁免〔add-codex-host-support〕
- **WHEN** `host="codex"` 且某条 finding 的 `runner="codex"`（同族 fallback 产物）
- **THEN** 该条走统一裁决入口——豁免通道已整体废除，不存在任何可被 `runner` 取值误触的豁免分支

### Requirement: sdflow-code-review 为每次全跑的独立强制主审

阶段三的 `sdflow-code-review` MUST **每次必跑**、以独立冷视角作为强制代码评审主审（依据实测能抓真问题），MUST **恒产 code-review-report.md**，SHALL NOT 跳过代码评审、SHALL NOT 降级为「高风险才跑的残差抽查」（**默认开、仅机判无逻辑面才关**，非风险判断 gate-on）。深度按**两层**规则：

- **Step1（scope 审计：scope-drift + 计划完成度，自持）MUST 每次必跑**，MUST NOT 因任何判定降级或跳过——既是便宜的评审地板，又是**验白名单形状诚实性的守卫**（自称无逻辑面的 diff 若偷藏逻辑改动，scope-drift 抓）。执行位 SHALL 为 fresh 子代理（消除「主 session 携带生成历史、自查自己顺手多改」的结构性偏置）；**意图源 SHALL 锚 OpenSpec 四件套**（proposal 的 scope/Non-Goals + tasks.md + design.md，确定性来源，MUST NOT 依赖 plan-file 路径猜测或 commit-message 推断作为首选意图源）；子代理不可用时 SHALL 降级主 session 亲做并在报告显著标注「scope 审计降级（存在自查偏置）」，恒跑语义不变。报告锚 `step1-broad-review` 的 `mode` SHALL 如实记执行位（`subagent`=子代理独立完成 | `main-session`=降级亲做）。能力探针 SHALL 于第零步（宿主/档位解析同位）一次性执行，Step1 与 Step2 共用**同一次**探针结果（`fanout-capability` 锚每轮恰一条的既有约束不变，MUST NOT 为 Step1 另探一次落第二条锚）〔spec-review-amendment〕。
- **Step2（多镜 fan-out：领域镜+对抗镜+历史镜+机械引用核+二元裁决〔adr/0041〕）MUST 对任何含行为/逻辑面的 change 每次全跑**；**仅当** change 的 diff **机判命中「无逻辑面白名单形状」**时可免 Step2（多镜结构上零产出）。免除 MUST 由 Step1 scope-drift 守卫：scope-drift 揭出隐藏逻辑 → 白名单判定作废 → Step2 照跑。**守卫时序 SHALL 钉死**〔spec-review-amendment〕：diff 命中白名单形状（EXEMPT 候选）时，Step2 的免除判定 MUST **阻塞等待 Step1 结果收齐后**才可定案（否则 Step1 迟到的揭穿换不回已跳过的多镜，守卫空转）；diff 非白名单形状（Step2 反正要跑）时，Step1 MAY 与 Step2 fan-out 并行、结果在 Step3 barrier 收齐。

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
