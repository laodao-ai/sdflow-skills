---
impl-pipeline: tickets
---

## Global Constraints

以下条款逐字摘自本 change 的 `design.md`（Goals / Non-Goals / 设计细节 / Compliance），
对每一张 ticket 的 implementer 与 reviewer 同等生效：

**Goals（设计级边界）**：Step1 的替换对下游（Step3 合并池、lens-metric、ship_gate、retro 聚合）
**接口不变**——broad 镜行、`step1-broad-review` 锚、findings 结构均保持既有形状，只换生产方式。

**Non-Goals**：见 proposal；另加设计级两条——不改 `trivial_shape.py`（EXEMPT 判定逻辑不动，只消费
其结果）；不改 `hr_tg_intersect.py`（HR-TG 成员从 catalog 单一源动态 parse，加行即生效）。

**dispatch**〔spec-review-amendment：时序钉死〕：**能力探针挪至 Step0（与 tier-resolution 同位、
每轮恰一次），Step1 与 Step2 共用同一次结果**（`fanout-capability` 锚每轮恰一条不变，MUST NOT 为
Step1 另探落第二条锚）。Step0 后主 session 派一个 fresh 子代理（中档 `$SDFLOW_TIER_MID`）。
**并行边界**：diff 命中白名单形状（EXEMPT 候选）时 Step2 免除判定 MUST 阻塞等 Step1 结果
（守卫语义要求 scope-drift 能作废 EXEMPT——异步迟到的揭穿换不回已跳过的多镜）；diff 非白名单
形状时 Step1 才与 Step2 fan-out 并行（结果同在 Step3 barrier 前收齐）。

**输入**：`{change_dir}` 的 proposal.md（scope / Non-Goals）+ tasks.md + design.md +
`DIFF_BASE..HEAD` diff（`--stat` + 全量）。prompt MUST 原文携带「四条通则」区块（传播纪律），
MUST 声明「不要 AskUserQuestion，返回结构化 findings」。

**与 verify 关系钉死**：本审计 MUST NOT 勾改 tasks.md 复选框、MUST NOT 替代 sdflow-done
verify 终审（verify 为最终权威）；Step4 自动修后的「复审一轮」SHALL 把 scope-drift 维度纳入
复审范围（修复 diff 自身的越界改动可见，报告锚定的 reviewed_sha 才名副其实）。

**mirrors 计数集**：`anchor_lint.py`：mirrors 合法 token 集扩为 `{domain,adversarial,grounding,history,broad}`；
**dead-fanout-multi-mirror 计数集维持 `{domain,adversarial,grounding,history}` 不变**。

**roster 行**仍为 canonical `{lens:"broad", runner:"<host>", site:—}`（契约 schema：`roster[].lens`
MUST ∈ lens enum，raw 名只出现在 `findings[].hits[].raw`）。

**TG-27 排除句（MUST 写进 catalog 行）**：评审工作流自身对**自报控制面锚**
（同会话内受信任 agent 自己写的 `<!-- sdflow:… -->` 控制锚）的读取/校验**不算 TG-27**——
只有消费**外部/不可信** LLM 产出（用户对话内容、RAG 检索结果、第三方 agent 产出）才算。

**消费规则显式化**：`sdflow-code-review/SKILL.md` 领域镜选择段 MUST
加一行 `TG-27 → domains/llm.md`（与 TG-01→backend 同构），否则 llm.md 成注册表孤儿。

**pre-emit 引文纪律**：「每条 finding MUST 引出触发它的具体代码行原文
（file:line + 逐字引文）；**非局部 finding（缺失校验/跨文件数据流/时序竞态/absence 类）以
「可复核证据包」替代单行引文**（多处 file:line 引文、或『应在而不在』的缺失对照——引出本应
含该防护的位置原文），仍须可复核定位；两者皆无 ⇒ 该条自报置信 MUST ≤50」。
**作用域**：本纪律仅约束 Step2 各镜的代码 finding，不作用于 Step1 scope 审计的任务级证据。
诚实边界：引文真实性无机械核验（子代理自报），本 gate 是产出纪律非机械门——SKILL 措辞
照此声明，MUST NOT 声称机械保证。

**Compliance**：

- 遵守 DOC-1（正文即最终态，gstack 时代描述不留正文）；premise-verification（本设计引用的
  file:line 均实查）；机械化优先基准（fold 块/HR-TG 成员/needle 均走单一源，不复制清单）；
  基准 5（不新增任何解析器——五态判定是模型判断，tasks.md 消费走既有 checkbox 约定）。
- 托管区块（`sdflow:principles` / `sdflow:tier-resolution` / `sdflow:async-branch`）零触碰；
  `sdflow:async-branch` 等值门（`check_async_branch_parity.py`）不受影响（Step1 改动在 marker 外）。
- 无豁免项。

**R-ID 对照**（本 change delta spec 的 Requirement 缩写）：
`SW-1` = spec-workflow·sdflow-code-review 为每次全跑的独立强制主审 ·
`SW-2` = spec-workflow·广审层原生执行，模拟必须显式标注降级 ·
`SW-3` = spec-workflow·代码审 finding 须引出触发行原文（ADDED） ·
`HAE-1` = host-adaptive-execution·子代理不可用时镜数如实降级 ·
`WM-1` = workflow-metrics·度量锚契约 sdflow:lens-metric v1。

### Task 1: anchor_lint 接纳 broad 镜而不误判降级为自相矛盾

**Blocked-by:** none
**R-ID:** HAE-1, WM-1

评审报告的 `fanout-capability` 锚在 `mirrors=` 里写出 `broad` 时被 lint 判为合法；同时，
「子代理机制报 unavailable 却声称跑了多个 fan-out 镜」这一自相矛盾的判定**不因 broad 的加入
而变松**——`broad` 有「主 session 亲做仍算独立完成」的合法降级路径，故它进合法 token 集、
不进 dead-fanout 计数集。当前实现把合法集与计数集混用同一个常量，本票须把二者拆开，
使「扩合法集」不会顺带污染计数判据。

另外，当消费仓的 workflow bundle 是旧版（不认识 `broad`）时，lint 报出的 unknown-token 错误
须自带可操作的修法指引，而不是让使用者对着一个陌生 token 名发呆。

- [ ] `mirrors=` 含 `broad` 时 lint 判合法通过
- [ ] `subagents="unavailable"` + `mirrors="broad,history"` 不触发 dead-fanout-multi-mirror
- [ ] `subagents="unavailable"` + `mirrors="broad,domain,history"` 仍触发 dead-fanout-multi-mirror
- [ ] `step1-broad-review` 锚取新枚举值 `mode="subagent"` 时 lint 通过（锁定「lint 不校验 mode 值」不变量）
- [ ] mirrors-unknown-token 报错文案含「若本仓 `openspec/workflow/` 为旧版，请先跑 `sdflow-init update`」
- [ ] 合法 token 集与 dead-fanout 计数集为两个独立常量，改前者不影响后者（有测试佐证）；**合法集常量名钉死为 `_MIRRORS_LEGAL`**（`design.md:106` 已按此名声明 SKILL 侧 skew 探测信号，Task 3 据此写探测段——改名即断链）
- [ ] `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` 既有用例全绿

### Task 2: lens-metric 折叠源改认 scope-audit 并给出旧版修法指引

**Blocked-by:** none
**R-ID:** WM-1

度量锚的折叠映射单一源不再认识 `gstack-adv` 这个原始镜名，改认 `scope-audit`——两者**不共存**，
是替换而非新增。折叠目标仍是 canonical lens `broad`，因此下游（retro 聚合、MIN_LENS_ROWS、
锚行 `lens="broad"`）对本次替换零感知。契约文档里描述折叠关系的散文同步改述，与机读块不得分叉。

同样地，emitter 遇到不认识的原始镜名而 fail-closed 时，报错须带上「bundle 可能是旧版」的
可操作指引——这条路径正是 SKILL 已更新而消费仓 bundle 未更新时的第一现场。

- [ ] 折叠机读块含 `scope-audit: broad` 行，且不再含 `gstack-adv` 行
- [ ] 契约文档中描述折叠关系的散文与机读块一致（无 `gstack-adv` 残留）
- [ ] 原始镜名 `scope-audit` 经折叠后产出 `lens="broad"` 的锚行
- [ ] emitter 遇未知原始镜名时报错文案含「若本仓 `openspec/workflow/` 为旧版，请先跑 `sdflow-init update`」（有测试断言）
- [ ] `sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py` 既有 fold 用例全绿

### Task 3: 代码审 Step1 改为自持 scope 审计，全 SKILL 去 gstack 依赖

**Blocked-by:** none
**R-ID:** SW-1, SW-2, SW-3, HAE-1

代码审编排器的第一步不再借道第三方 skill 的原生执行，而是自己派一个 fresh 中档子代理，
以本 change 目录的四件套为确定性意图源，做 scope-drift 与完成度两轴审计——意图不再靠
commit message 猜。审计产出逐 task 五态表（DONE / PARTIAL / NOT DONE / CHANGED /
UNVERIFIABLE，DONE/CHANGED 也在表内）与负向态 findings，findings 汇入既有合并池按普通
finding 走裁决，不设门、不向用户提问。

能力探针的位置随之上移到第零步、每轮恰一次，Step1 与 Step2 共用同一次结果；探针判不可用时
Step1 由主 session 亲做，并在报告显著标注存在自查偏置。`trivial_shape` 判 EXEMPT 时本步照跑，
且审计一旦揭出隐藏逻辑即作废 EXEMPT——因此 EXEMPT 候选形状下的免除判定必须等 Step1 结果，
不能与之并行。

Step1 的执行位如实写进 `step1-broad-review` 锚的 mode 值（新枚举 `subagent|main-session`），
度量侧的原始镜名改用 `scope-audit`（只出现在 findings 的 hits 里，roster 行仍是 canonical
`broad`）。SKILL 的 skew 探测段要能在起跑前发现「本 SKILL 已是新版、但本仓 bundle 还是旧版」
这个高发方向，而不是让整轮 fan-out 跑完在末步 lint 才炸。

同一票内还落两条产出纪律：Step2 各镜的 finding 必须引出触发行原文或等价的可复核证据包，
引不出则自报置信封顶 50；Step3 置信过滤据此把它们滤出主结论并在「已裁掉」区留一行痕迹，
另扩两条明确滤除类目。

本票收尾时，本 SKILL 正文里不得再有任何 gstack 提法——包括分工表、报告格式区、命中范围行。

- [ ] `grep -n "gstack" sdflow-code-review/SKILL.md` 无输出（严格归零，不留「历史注记」豁免）
- [ ] Step1 描述为恒跑 fresh 中档子代理的 scope 审计，输入明列 proposal/tasks/design + `DIFF_BASE..HEAD` diff，且要求 prompt 原文携带四条通则区块与「不 AskUserQuestion」声明
- [ ] Step1 审计两轴写明：scope-drift（出圈改动逐条列 SCOPE CREEP，Non-Goals 被实现算 creep）+ 完成度五态，且五态判定纪律逐条钉死（DONE 从严 / CHANGED 从宽 / UNVERIFIABLE 诚实 / PARTIAL=部分子项有 diff 内证据 / NOT DONE=diff 内无任何相关证据）
- [ ] Step1 产出含逐 task 五态表（DONE/CHANGED 也在列）+ 负向态 findings，并明写不勾 tasks.md、不替代 verify 终审、Step4 自动修后复审一轮纳入 scope-drift 维度
- [ ] 能力探针段落位于第零步（与档位解析同位），文中声明 Step1/Step2 共用同一次探针结果、`fanout-capability` 锚每轮恰一条
- [ ] 并行边界写明：EXEMPT 候选形状下 Step2 免除判定阻塞等 Step1 结果，非白名单形状才并行
- [ ] 降级分支写明主 session 亲做 + 报告显著标注「⚠️ scope 审计降级（存在自查偏置）」；恒跑守卫（EXEMPT 时照跑、揭出隐藏逻辑则 EXEMPT 作废）语义保留
- [ ] 锚 mode 枚举为 `subagent|main-session`
- [ ] 报告格式区：mirrors 说明含 `broad` token；lens-metric 的 `findings[].hits[].raw` 用 `scope-audit`，roster 行仍写 canonical `lens="broad"`
- [ ] 领域镜选择段含一行 `TG-27 → domains/llm.md`
- [ ] skew 探测段追加两个新信号（contract 折叠块含 `scope-audit:` 行；anchor_lint 支持 `broad` token），任一探不到沿用既有「硬停 + 提示先跑 `sdflow-init update`」文案
- [ ] Step2 子代理 prompt 模板含引文纪律全文（含非局部 finding 的可复核证据包替代路径），并声明「产出纪律非机械门」
- [ ] Step3 置信过滤含「既无引文又无证据包 ⇒ 置信上限 50 ⇒ 落已裁掉区一行留痕」，明确滤除类目扩两条 Suppressions（阈值/常量不强制求注释；无害冗余助可读性不标）
- [ ] `sdflow:principles` / `sdflow:tier-resolution` / `sdflow:async-branch` 托管区块字节级未变

### Task 4: code-checklists 吸收五类缺口并新建 LLM 领域清单

**Blocked-by:** none
**R-ID:** SW-1

把与第三方 skill 逐条比对后确认的五类真空缺口落进本仓清单体系：base 层补命令/代码注入与
枚举取值完备性两条；backend 领域补 DB 层竞态一条、并给既有条目补上服务端模板渲染的 XSS
检查点；另建 LLM 领域清单收纳「代码消费 LLM 产出」这一面的输出信任边界与 prompt 一致性。
措辞一律语言无关、示例放括号里，避免把清单钉死在某个技术栈上。

新领域要真正被选中，须同时在触发目录里有对应触发条目、在清单注册表里有登记、在选用规则
示例里有映射行——三处缺一它就是孤儿。触发措辞收窄到「代码消费 LLM/agent 产出并持久化/
执行/外呼」，并带排除句，防止本仓每次改自己的锚行工具都字面命中。

ID 一律新号，不复用不重排。

- [ ] base 清单含新条目：命令/代码注入（shell 串插值 → 参数数组；eval/exec 执行模型或外部输入生成的代码须沙箱/白名单）
- [ ] base 清单含新条目：枚举/取值完备性（新值逐消费者 trace 且明写「必须读 diff 外代码」；allowlist 数组核对；case 链 fall-through 到错误默认）
- [ ] backend 领域含新条目：DB 层竞态（find-or-create 无唯一索引 / check-then-set 原子 WHERE / 状态迁移非原子 / 绕过模型校验直写）
- [ ] backend 既有 XSS 相关条目扩点覆盖服务端模板渲染场景，并注明客户端框架面待 frontend domain（不声称覆盖）
- [ ] 新建 LLM 领域清单，含输出信任边界（持久化/外发前格式与 shape 校验、URL allowlist 防 SSRF、入库防存储型 prompt 注入）与 prompt 一致性（1-indexed、工具声明与 wiring 一致、限额单一声明）两条
- [ ] 清单注册表登记 LLM 领域行（extends base，ID 前缀 `CR-LLM-`）
- [ ] 选用规则示例块含 `TG-27 → llm.md` 映射行
- [ ] 触发目录领域清单段含 TG-27 行，措辞为「代码消费 LLM/agent 产出并持久化/执行/外呼」，含排除句，且行内注明 code-review-only domain
- [ ] 触发目录 HR-TG 成员行追加 TG-27，且 `hr_tg_intersect.py` 实跑能正确 parse 出该成员（零代码改动）
- [ ] 全部新条目为新 ID，未复用或重排既有 ID

### Task 5: 提示词与全量文档同步到自持 scope 审计的新提法

**Blocked-by:** 3
**R-ID:** SW-1

工作流文档、质量分层参考、编排器提示词、以及 docs 下的技能说明与总览（含 HTML 控制台页），
凡把第一步描述为「借道第三方 skill 原生执行」的地方，一律改述为自持 scope 审计——措辞与
Task 3 在 SKILL 里定下的提法一致，不各写各的。提示词改动对应的 needle 断言同步更新。

第三方 skill 的说明文档本身**保留**，但定位改述为「非运行时依赖的第三方 skill 参考」，
而不是删除。扫残留时不能只扫 `.md`：`.py` / `.sh` / `.html` 里同样有硬编码提法。

需要区分「必须改」与「合法保留」：本 change 只移除**代码审侧**的运行时依赖，设计审侧的
autoplan 依赖、归档件、ADR 等历史文件里的提法一律不动。

- [ ] 工作流主文档三处（编排器描述 / 代码侧质量层 / checklist 勾选项）改述为自持 scope 审计
- [ ] 质量分层参考里的相关行同步改述
- [ ] 编排器提示词删去第三方 skill 提法，且 `hack/tests/test_workflow_split.py` 的 needle 断言同步更新并通过
- [ ] docs 下代码审技能说明、外部依赖说明、工作流总览、以及 HTML 控制台页中描述第一步的段落全部更新
- [ ] 第三方 review skill 的说明文档保留，定位改述为「非运行时依赖的第三方 skill 参考」
- [ ] 用不带 `--include` 限定的全量 grep 复扫一遍，逐条判定残留是「必须改」还是「合法保留」（设计审侧依赖 / 归档 / ADR / 历史文档），并在报告里列出判定依据
- [ ] 本票新提法与 Task 3 在 SKILL 中使用的提法一致（报告里给出对照）

### Task 6: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4,5
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落
`impl-reports/task6-<slug>.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

本仓的测试命令是 `/usr/bin/python3 -m pytest`（本机裸 `pytest` 不存在、默认 `python3` 未装
pytest——这是本机环境事实）。仓 `openspec/config.yaml` 若无 `test-suites` 配置，则依仓内既有
约定判定并在报告里写明命令原文与判定依据；确无某层则记「未覆盖（本仓无此层）」+ 判定依据，
**不得 fail-closed 罢工**。

除聚合回归外，本票还承接本 change 的三项收尾：Success Metrics 静态核验、issues 池记录、
以及为紧随其后的 dogfood 打开全局窗口。

**dogfood 分工声明（诚实边界）**：`tasks.md` 6.4 要求本 change 自身跑一次 `/sdflow-code-review`
并核验产出锚。该实跑观测**由本票之后 ship 链序的 code-review 步天然承担**（开窗后它跑的就是
本 change 的新 SKILL），本票只负责**开窗前置**与**待核锚清单的落盘**，不重复跑一次多镜评审。
本票 MUST 在报告里显式写明这一分工与待核锚清单，MUST NOT 声称已完成实跑观测。

**开窗是机器级影响的时间盒操作**：`bash setup.sh` 会把 `~/.sdflow/workflow`、`~/.claude/skills/*`、
`~/.codex/skills/*` 全部翻向本开发树。本票 MUST 在报告里写明还原方式（合并后在运行 checkout
`~/.skills/sdflow-skills` 重跑 `bash setup.sh`），供收尾提示引用。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] `grep -rn "gstack" sdflow-code-review/SKILL.md` 严格归零（贴命令与输出）
- [ ] `openspec validate --strict` 绿（贴输出）
- [ ] issues 池记三条 todo（用开发 checkout 的 `sdflow-issues/scripts`、显式传 `change` 字段）：① python.md domain（Async/Sync 混用条目落点）② spec-review 侧 autoplan 姊妹依赖处置 ③ 仓根 `openspec/workflow/` 孤儿副本清理（`lens-metric-contract.md` / `WORKFLOW-GUIDE.md`）
- [ ] 开发 checkout 跑 `bash setup.sh` 成功，且 `readlink ~/.sdflow/workflow` 确认指向本开发树（贴输出）
- [ ] 报告写明 dogfood 分工声明 + 待核锚清单（`mode="subagent"` 锚 / `scope-audit` 折叠出的 `lens="broad"` 行 / anchor_lint 通过）+ 全局窗口还原方式
