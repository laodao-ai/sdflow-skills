## Context

见 proposal.md「Why」。设计所需的现状事实（均已实查）：

- Step1 现为 gstack `/review` 原生执行，锚 `<!-- sdflow:step1-broad-review v1 mode="native|simulated" -->`；
  `anchor_lint.py` 对该锚只核存在性（`MANDATORY` 元组），mode 枚举校验只在 spec-review 侧
  `outside_voice_guard`（作用对象 `gstack-review.md`，非本层报告）。
- lens-metric 折叠映射单一源 = `lens-metric-contract.md` 的 `lens-metric-fold` 机读块（现有
  `gstack-adv: broad` 行）；`lens_metric_emit.py` 对未知 raw 名 fail-closed。
- `fanout-capability` 锚 `mirrors=` 合法 token 集 `{domain,adversarial,grounding,history}` 在
  `anchor_lint.check_fanout_consistency` 与 `host-adaptive-execution` / `workflow-metrics` 两 spec
  钉死；dead-fanout-multi-mirror 计数集 = 同一集合。
- spec 级消费点：`spec-workflow/spec.md` §「Step1 恒跑 + trivial_shape 守卫」；提示词消费点
  `prompts/step8-code-review.md` + needle `hack/tests/test_workflow_split.py`。

### 消费点依赖图（改动面一览）

```
sdflow-code-review/SKILL.md (Step1 重写 · Step2/3 pre-emit gate)
  ├─ 锚 step1-broad-review ──▶ anchor_lint.py MANDATORY（存在性，锚名不变 ⇒ 零改）
  ├─ 锚 fanout-capability mirrors= ──▶ anchor_lint.py token 枚举 ＋broad（＋golden 测试）
  │        └─ spec 钉死: host-adaptive-execution · workflow-metrics（各出 delta）
  ├─ lens-metric roster raw="scope-audit" ──▶ lens-metric-contract.md fold 块（gstack-adv 行替换）
  ├─ Step1 恒跑守卫语义 ──▶ spec-workflow spec（delta）
  └─ dispatch 提示词 ──▶ prompts/step8-code-review.md ──▶ test_workflow_split.py needle
code-checklists/ (base CR-10/11 · backend CR-BE-02扩/CR-BE-03 · 新 llm.md)
  └─ trigger-catalog.md（TG-27 行 + HR-TG 成员行——hr_tg_intersect.py 动态 parse，零代码改动）
docs/（workflow.md · quality-layering.md · workflow-skills/* · external-dependencies.md）
```

## Goals / Non-Goals

**Goals（设计级边界）**：Step1 的替换对下游（Step3 合并池、lens-metric、ship_gate、retro 聚合）
**接口不变**——broad 镜行、`step1-broad-review` 锚、findings 结构均保持既有形状，只换生产方式。

**Non-Goals**：见 proposal；另加设计级两条——不改 `trivial_shape.py`（EXEMPT 判定逻辑不动，只消费
其结果）；不改 `hr_tg_intersect.py`（HR-TG 成员从 catalog 单一源动态 parse，加行即生效）。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。

## 设计细节

### 1. Step1 自持 scope 审计（替换 gstack native）

**执行协议**（D1）：

- **dispatch**〔spec-review-amendment：时序钉死〕：**能力探针挪至 Step0（与 tier-resolution 同位、
  每轮恰一次），Step1 与 Step2 共用同一次结果**（`fanout-capability` 锚每轮恰一条不变，MUST NOT 为
  Step1 另探落第二条锚）。Step0 后主 session 派一个 fresh 子代理（中档 `$SDFLOW_TIER_MID`）。
  **并行边界**：diff 命中白名单形状（EXEMPT 候选）时 Step2 免除判定 MUST 阻塞等 Step1 结果
  （守卫语义要求 scope-drift 能作废 EXEMPT——异步迟到的揭穿换不回已跳过的多镜）；diff 非白名单
  形状时 Step1 才与 Step2 fan-out 并行（结果同在 Step3 barrier 前收齐）。
- **输入**：`{change_dir}` 的 proposal.md（scope / Non-Goals）+ tasks.md + design.md +
  `DIFF_BASE..HEAD` diff（`--stat` + 全量）。prompt MUST 原文携带「四条通则」区块（传播纪律），
  MUST 声明「不要 AskUserQuestion，返回结构化 findings」。
- **审计两轴**：
  - **scope-drift**：diff 改动文件 ↔ proposal scope 比对——出圈改动（不在 What Changes /
    tasks 覆盖内）逐条列 SCOPE CREEP；Non-Goals 被实现也算 creep。
  - **完成度（五态）**：tasks.md 逐 task 判 `DONE / PARTIAL / NOT DONE / CHANGED / UNVERIFIABLE`，
    判定纪律吸收 gstack 原则：DONE 从严（需 diff 内具体证据，碰过文件≠做了）、CHANGED 从宽
    （换路径达成同目标算完成，注明差异）、UNVERIFIABLE 诚实（diff 证明不了的外部状态如实列出
    需人工核验项，宁可多列不静默判 DONE）；**PARTIAL = 部分子项有 diff 内证据其余没有、
    NOT DONE = diff 内无任何相关证据**〔spec-review-amendment：五态判据补齐，防轮间分叉〕。
- **输出**〔spec-review-amendment：落盘物补齐〕：① **逐 task 五态表**（每 task 一行：状态 +
  一句证据引用；DONE/CHANGED 也在列，非仅负向态——五态审计须整体可审计）；② 结构化 findings
  （每条：类型 `SCOPE-CREEP/NOT-DONE/PARTIAL/UNVERIFIABLE` + 证据 file:line 或 task 条目 +
  严重度；CHANGED 由表行承载注明差异、不单独出 finding）→ 进 Step3 合并池按普通 finding 走
  裁决/置信/自动修/defer（informational shift-left，不设门、不 AskUserQuestion——C8）。
  **与 verify 关系钉死**：本审计 MUST NOT 勾改 tasks.md 复选框、MUST NOT 替代 sdflow-done
  verify 终审（verify 为最终权威）；Step4 自动修后的「复审一轮」SHALL 把 scope-drift 维度纳入
  复审范围（修复 diff 自身的越界改动可见，报告锚定的 reviewed_sha 才名副其实）。
- **降级**：host=codex 且能力探针 `subagents="unavailable"` ⇒ 主 session 亲做同一审计协议，
  报告显著标注「⚠️ scope 审计降级（主 session 亲做，存在自查偏置）」。
- **恒跑守卫**：`trivial_shape` EXEMPT 时本步照跑；审计揭出隐藏逻辑 ⇒ EXEMPT 作废、Step2 照跑
  （spec-workflow 既有语义，delta 中保留原文强度）。

**锚**：`<!-- sdflow:step1-broad-review v1 mode="subagent|main-session" -->`——新枚举如实记执行位
（`subagent`=子代理独立完成，`main-session`=降级亲做）；旧值 `native|simulated` 退役（归档报告
不迁移）。anchor_lint 零改动（只核存在性，C1）。

### 2. mirrors token：`broad` 进合法集、不进计数集

- `anchor_lint.py`：mirrors 合法 token 集扩为 `{domain,adversarial,grounding,history,broad}`；
  **dead-fanout-multi-mirror 计数集维持 `{domain,adversarial,grounding,history}` 不变**。
  依据：计数集语义是「机制死却报多镜 = 自相矛盾」，而 broad 有主 session 降级**合法**路径
  （恒跑守卫）——`subagents="unavailable"` + `mirrors="broad,history"` 中 broad 不构成矛盾
  （降级亲做是设计内行为），入计数集会把合法降级误判 fail。
- `mirrors=` 落值规则：Step1 子代理成功 ⇒ 含 `broad`；降级主 session 亲做 ⇒ 仍含 `broad`
  （它确实独立于 Step2 完成，与「缩 roster 到主 session 实际独立完成的镜」既有语义一致）。
- golden 测试：新增「mirrors 含 broad 合法」「unavailable + broad + 1 镜不触发 dead-fanout」
  「unavailable + broad + 2 镜仍触发」三用例。

### 3. lens-metric：raw 名替换

- contract `lens-metric-fold` 块：`gstack-adv: broad` 行**替换**为 `scope-audit: broad`（D3④，
  不共存）；折叠表 prose（contract §折叠表 + workflow-metrics spec :14 prose）同步改述。
- roster 行仍为 canonical `{lens:"broad", runner:"<host>", site:—}`（契约 schema：`roster[].lens`
  MUST ∈ lens enum，raw 名只出现在 `findings[].hits[].raw`——`hits[].raw` 从 `gstack-adv` 改
  `scope-audit`，经 fold 折叠到 `broad`）；emitter 归约后锚行 `lens="broad"` 不变——下游
  （retro 聚合、MIN_LENS_ROWS）零感知〔spec-review-amendment：原文把 scope-audit 写进 roster.lens
  会被 emitter 判 enum 越域 fail-closed，与契约 `lens-metric-input-schema` 矛盾〕。
- **skew 探测信号扩展（新 SKILL × 旧 tools 方向，高发面）**〔spec-review-amendment〕：SKILL 既有
  「skew 探测」段（现探 emitter `--host` + contract `runner:none` 两旧信号）MUST 追加本 change 的
  两个新信号——① contract `lens-metric-fold` 块含 `scope-audit:` 行；② anchor_lint 支持 `broad`
  mirrors token（探 `_MIRRORS_LEGAL` 常量行或等价 `--help`/源码 grep 信号）。任一探不到 ⇒ 沿用同段
  既有「硬停 + 提示先跑 `sdflow-init update`」文案。依据：SKILL 走全局 symlink 瞬时生效、消费仓
  tools/contract 走拷贝惰性更新——不加新信号则每个未 update 消费仓的每轮评审在**末步** lint 才
  fail-closed（整轮 fan-out + voice 成本报废、报错无修法指引）；旧两信号探不到这个方向。同时
  emitter「未知 raw 镜名」与 anchor_lint「mirrors-unknown-token」两处报错文案 MUST 追加
  「若本仓 `openspec/workflow/` 为旧版，请先跑 `sdflow-init update`」一句（可操作指引）。

### 4. checklist 吸收（C7 定案，措辞全部改写为语言无关 + 括号多语言示例）

| 落点 | 新条目 | 要点 |
|---|---|---|
| `code-review-base.md` | **CR-10 命令/代码注入** | 变量插值进 shell 串（subprocess shell=True / os.system / 反引号拼接）→ 参数数组；eval/exec 执行模型或外部输入生成的代码须沙箱/白名单 |
| `code-review-base.md` | **CR-11 枚举/取值完备性** | 新增枚举值/状态串/类型常量 ⇒ 逐消费者 trace（**必须读 diff 外代码**，grep 兄弟值找全消费点后逐个读）；allowlist/过滤数组核对；case/if-else 链 fall-through 到错误默认 |
| `domains/backend.md` | **CR-BE-03 DB 层竞态** | find-or-create 无唯一索引防并发重复；check-then-set 用原子 `WHERE 旧值` UPDATE；状态迁移非原子导致跳变/双跳；绕过模型校验的直写 DB |
| `domains/backend.md` | **CR-BE-02 扩点** | 检查点追加：用户可控数据进不安全 HTML 渲染防 XSS——**仅服务端模板场景（html_safe / \|safe）**；客户端框架（dangerouslySetInnerHTML / v-html）待 frontend domain，见 proposal Non-Goals〔设计门拍板 Q3〕 |
| `domains/llm.md`（新） | **CR-LLM-01 输出信任边界** | LLM 生成值（email/URL/名称/结构化对象）持久化/外发前格式与 shape 校验；LLM 生成 URL 外呼前 allowlist 防 SSRF；LLM 输出入知识库/向量库前防存储型 prompt 注入 |
| `domains/llm.md`（新） | **CR-LLM-02 prompt 一致性** | prompt 列表用 1-indexed；prompt 声称的工具/能力与实际 wiring 一致；限额/约束多处声明防漂移 |
| SKILL Step3 滤除类目 | Suppressions 扩两条 | 阈值/常量不强制求注释（调参即腐）；无害冗余助可读性不标 |

- `README.md` 注册表加 `llm.md` 行（extends base，ID 前缀 `CR-LLM-`）。
- ID 纪律：全部新号，不复用不重排。

### 5. TG-27（LLM 集成面）

trigger-catalog 「领域清单」段加行：

> TG-27 | **LLM 集成面**（代码**消费 LLM/agent 产出**并持久化/执行/外呼：输出解析、锚行 parse、
> 工具 wiring、RAG/知识库写入）| — | `llm` | — | —

- 触发判据用具体行为描述（catalog 既有纪律）；纯 prose/SKILL.md 编辑不触发（D2 收窄措辞）。
  **排除句（MUST 写进 catalog 行）**〔spec-review-amendment〕：评审工作流自身对**自报控制面锚**
  （同会话内受信任 agent 自己写的 `<!-- sdflow:… -->` 控制锚）的读取/校验**不算 TG-27**——
  只有消费**外部/不可信** LLM 产出（用户对话内容、RAG 检索结果、第三方 agent 产出）才算；
  否则本仓每次改 anchor_lint/emitter 都字面命中「锚行 parse」，高频假阳污染 Q5 复评样本
  （原措辞例证「锚行 parse」删除）。
- **消费规则显式化**〔spec-review-amendment〕：`sdflow-code-review/SKILL.md` 领域镜选择段 MUST
  加一行 `TG-27 → domains/llm.md`（与 TG-01→backend 同构），否则 llm.md 成注册表孤儿——
  加行任务并入 tasks 1.4。
- HR-TG 成员行 `TG-26` 后追加 `TG-27`（`hr_tg_intersect.py` 动态 parse，零代码改动）；
  命中率/产出走 Q5 复评注记（跑满 10 次可摘出）。
- TG-27 domain 仅建 code-checklists 侧（spec-checklists 无 llm.md，与 frontend 反向先例同构）——
  catalog 行注一句「code-review-only」防未来读者误判缺失〔spec-review-amendment〕。

### 6. pre-emit verification gate（C9）

- **Step2 子代理 prompt 模板**追加产出纪律：「每条 finding MUST 引出触发它的具体代码行原文
  （file:line + 逐字引文）；**非局部 finding（缺失校验/跨文件数据流/时序竞态/absence 类）以
  「可复核证据包」替代单行引文**（多处 file:line 引文、或『应在而不在』的缺失对照——引出本应
  含该防护的位置原文），仍须可复核定位；两者皆无 ⇒ 该条自报置信 MUST ≤50」
  〔spec-review-amendment：单行引文一刀切会与 CR-11「必须读 diff 外代码」自相矛盾、系统性
  压制依赖链/时序/缺失性 bug〕。
- **Step3 置信过滤**追加规则：既无引文又无证据包的 finding 置信上限 50（必被 <80 滤除）→ 落
  「已裁掉」区一行带过（可审计，反静默压制既有条款覆盖）。
- **作用域**：本纪律仅约束 Step2 各镜的代码 finding，不作用于 Step1 scope 审计的任务级证据
  〔spec-review-amendment〕。
- 诚实边界：引文真实性无机械核验（子代理自报），本 gate 是产出纪律非机械门——SKILL 措辞
  照此声明，MUST NOT 声称机械保证。

## Risks / Trade-offs

- [自持 scope 审计质量弱于 gstack 多年调校] → 意图源从 plan-file 猜测升级为四件套确定源，
  结构性优势抵消；dogfood 首轮验证（Success Metrics），弱点走 issues 池迭代。
- [每轮多一次中档 dispatch 成本] → 换偏置消除（memo 三镜代价：系统镜为主）；lens-metric
  采纳率/独立率数据可事后复评该镜价值。
- [bundle skew 双向] → 反向（旧 SKILL raw=gstack-adv × 新 contract）：emitter fail-closed 非假绿，
  修法=重跑 `sdflow-init update`；接受（memo 边角②）。**正向（新 SKILL × 旧 tools/contract，
  高发面）：由 skew 探测新信号在起跑前拦截 + 报错文案带修法指引（见「3. lens-metric」段
  〔spec-review-amendment〕），不再接受为静默边角。**
- [mode 新枚举与归档旧锚并存] → 归档为冻结审计件不迁移；lint 不校验 mode 值，无机械冲突。
- [TG-27 在本仓命中过频] → 触发措辞已收窄到「代码消费 LLM 产出」；Q5 复评可摘出 HR。

## Migration Plan

1. 单 change 内一次完成：SKILL.md + assets（checklists/catalog/contract/anchor_lint/prompts）+
   specs 三 delta + 测试 + docs（P0→P1→P2 顺序见 proposal）。
2. 发布：merge 后运行 checkout `git pull` + `bash setup.sh`（SKILL symlink 即时 + tools 拷贝）；
   消费仓 `sdflow-init update` 刷 bundle。窗口期纪律 = 既有 pull→setup 规范。
3. 回滚：单 commit revert + 重跑 setup.sh/update——gstack skill 本身未卸载，回滚后 Step1
   原样恢复 native 执行；无数据迁移。

## Open Questions

无——可延后项均已显式 defer 进 issues 池（python.md domain、spec-review 姊妹依赖）。

## Compliance

- 遵守 DOC-1（正文即最终态，gstack 时代描述不留正文）；premise-verification（本设计引用的
  file:line 均实查）；机械化优先基准（fold 块/HR-TG 成员/needle 均走单一源，不复制清单）；
  基准 5（不新增任何解析器——五态判定是模型判断，tasks.md 消费走既有 checkbox 约定）。
- 托管区块（`sdflow:principles` / `sdflow:tier-resolution` / `sdflow:async-branch`）零触碰；
  `sdflow:async-branch` 等值门（`check_async_branch_parity.py`）不受影响（Step1 改动在 marker 外）。
- 无豁免项。
