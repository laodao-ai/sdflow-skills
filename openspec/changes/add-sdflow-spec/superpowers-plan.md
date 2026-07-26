---
impl-pipeline: tickets
---

## Global Constraints

> 以下为 `design.md` 的硬约束与 Compliance 条款**逐字摘录**（非转述）。每个 implementer / reviewer
> 子代理共享这一份注意力透镜。

**总约束（design.md · Context）**：

> 约束：产物契约不变（标准四件套 + openspec CLI + FF-0）；下游阶段三不动；通则托管单一源机制不可绕过；**canonical 规则单一源不可分叉**。

**D1 诚实收窄**：

> 🔴 **诚实收窄**〔spec-review-amendment F-04〕：原文「跳过风险**结构性消灭**」与 `proposal.md` 自认的「非机械保证」矛盾，**改为**：「拷问是管线的**内建默认路径**，跳过须主动偏离指令；这是结构性改善，不是机械保证」。

**D2 生成子代理的判断边界**：

> writer 遇未决判断 MUST 返回结构化 blocker，MUST NOT 自行补全。

**D3 agent 定义与派发**：

> - 🔴 **派发参数 = `subagent_type`，不是 `agentType`**〔spec-review-amendment F-01〕。依据：`docs/subagent-definitions-plan.md:114-145` 把三条路径分清——①Agent 工具（参数 `subagent_type`）②agent 定义文件（载体）③Workflow `agent()`（参数 `agentType`），而同文 `:136-137` 明记 **③ 不采纳**（需用户每次显式授权）。
> - 🔴 **fallback 不是等价降级，改为亲查/亲写**〔spec-review-amendment F-01 · hr-tg V-3〕：原设计的「agent 定义不可用 → 通用子代理 + prompt 内联通则」**撤掉了唯一的工具权限边界 = 降级即提权**（`docs/subagent-definitions-plan.md:116-123`：直接 Agent 路径无法限制工具集），且 agent 正文承载的角色纪律（researcher 的「材料不回传」、writer 的「自调 instructions / 禁 AskUserQuestion」）在 fallback 下全部消失。**改为**：researcher 不可用 → 主 session **亲查**；writer 不可用 → 主 session **亲写**。MUST NOT 用权限更宽的通用子代理当安全 fallback。

**D4 档位解析与传递**：

> 🔴 **档位解析 MUST 照既有加固协议，不得自造简写**〔spec-review-amendment F-06(Eng)〕：`sdflow-spec-review/SKILL.md` 第零步第 3 项的 (a) unset 清脏 →(b) `[ -x ]` 预检 fail-loud →(c) 捕获退出码再 eval →(d) eval 后校验枚举与非空，**四步一步不少**（裸 `eval "$(…)"` 会被脚本缺失静默吞，且旧值留存 ⇒ 拿旧宿主假绿；`resolve-models.sh:61/74/209` 三种失败面都 exit 0 只在 stderr 告警）。
> 🔴 **传递方式**：harness 每次 Bash 调用是独立 shell，`export` **不跨调用存活**。⇒ 主 session 从该次工具输出里读到**具体模型 id**，再把**字面值**填进派发的 `model` 参数；SKILL.md 正文写变量名（不内联 id），二者不矛盾。

**D8 降级与诊断**：

> 🔴 **报告必须 actionable**〔spec-review-amendment F-18〕：降级/失败报告 SHALL 含 **problem + cause（exit code / 缺失文件 / 实际版本）+ 可执行的下一步**。
> 🔴 **外部检索的退避与错误分类**〔spec-review-amendment F-25〕：规定总时间预算；仅对 429/5xx 做一次带 jitter 的有界重试；认证/schema 错误立即 fail-closed；**降级前确认替代路径不复用同一故障依赖**。

**D9 纪要落盘与 B 起手前移**：

> 🔴 **原论证的盲点已修**〔spec-review-amendment F-12〕：**处置**：Phase B **增量落盘**（每条承重约束站稳即追加写 memo 草稿），把全损窗口收窄到「两次保存之间」。
> 🔴 **「删分支即净」补条件限定**〔spec-review-amendment F-05〕：**当且仅当 B 收敛时工作树是干净的**。否则 FF-0 的 `checkout -b` 会把用户的脏改动带上新分支，`checkpoint-commit.sh:51` 的无条件 `git add -A` 再把它们全部提交 ⇒ 删分支会连用户被裹挟进来的活一起删。

**D11 安装协议**：

> 🔴 **Windows 分支明写取舍**：散装 `.md` 无 marker 落点 ⇒ **Windows 下不铺 agents，走主 session 亲查/亲写路径**，并在 `skipped[]` 报一行。MUST NOT 写「copy + 所有权守卫」这种做不出来的东西。
> 🔴 **`--check` 的真实性质**〔spec-review-amendment F-29〕：`setup.sh:261-266` 的 `if !` 结构使 `set -e` 不触发、**退出码恒 0** ⇒ 它是**提示不是门**。真正会红的是 `hack/tests/`。spec 措辞按此如实写。

**安全与数据保护（design.md · BASE-28 · TG-17 命中）—— 五项处置逐字**：

> | # | 面 | 处置 |
> |---|---|---|
> | S1 | **`Bash` 不是只读** —— 原 D3 断言「六者皆只读、不破无写权边界」是事实错误（可 `>` 重定向、`rm`、`git commit`、`curl -X POST`；工具 allowlist 不能限制 Bash 子命令） | **首选**：用作用域参数收窄（`docs/subagent-definitions-plan.md:223-224` 实测 `tools` 支持作用域参数）→ `Bash(git log:*), Bash(rg:*), Bash(grep:*)` 之类白名单集。**备选**（作用域语法未实测通过时）：如实改称「工具集为**检索取向**；`Bash` 非只读，只读性由 agent 正文角色纪律约束，**属指令层非机械门**」 |
> | S2 | **出境通道无 secret scan** | **拆两个 agent**：`local-researcher`（无网络）/ `web-researcher`（无仓库读取、无 `Bash`，只接收主 session 生成的**最小净化查询**）。任何外发参数 MUST 先过 secret scan（**复用** `openspec/specs/host-adaptive-execution/spec.md:82-96` 既有的 secret scan + 读围栏 + 拒发语义，MUST NOT 新造），命中即拒发且**禁 fallback** |
> | S3 | **间接 prompt injection** | Web 内容一律定义为**不可执行数据**（指令性文字视为数据）；网络 agent 禁 `Bash`/仓库读取；主 session 只消费带来源的事实摘要；影响设计决策的结论须第二来源或官方来源复核 |
> | S4 | **`resolvedOutputPath` confused deputy** | 由确定性 wrapper 解析并验证 JSON；对目标做 canonicalization，要求严格位于 `openspec/changes/<name>/`、匹配预期 artifact allowlist、拒绝 symlink 逃逸，再把净化后的路径交给写入方 |
> | S5 | **全局 agent 名册暴露** | 两个 agent 的 `description` 写成**排他式**（「仅由 `/sdflow-spec` 编排派发，其它场景 MUST NOT 选用」），把误选风险压到最低 |

**Compliance〔D-6〕（design.md 全节逐字）**：

> - **adr/0005 dev/runtime checkout 纪律**：遵守——setup.sh 改动在开发 checkout 验证，测完在运行 checkout 重跑还原（Migration Plan 已点名该窗口）。
> - **通则托管单一源**：遵守——agent 定义正文的通则块由 `sync_principles.py` 以 **skill 味源**渲染（受众为下发子代理），MUST NOT 手改块内部；投放面用 **glob 发现**（非硬编码清单，否则 SA-07 的「新增未纳入即变红」场景做不出来），并新增 `AGENT_TARGETS` 显式配 `SOURCE`（`PROJECT_TARGETS` 固定用 `SOURCE_PROJECT`，直接加进去会注入错误味源）。
> - **host-adaptive-execution「档位按机队分列、skill 引用变量不内联模型名」**：遵守——agents `model: inherit`；SKILL.md 正文写变量名，派发时填该次解析出的具体 id（D4）。档位解析走既有四步加固协议。
> - **workflow.md G1「全流程不用 `/clear`」**：**带具名例外地遵守**——本 change 为「阶段一→阶段二」这一段增加一处例外，依据是 G1 未覆盖的两条（cache 按模型隔离 + 产/审错档），并**同 change 修订 G1 文本**使单一源不分叉（D6/D10）。MUST NOT 只改本仓非托管区而留 canonical 说反话。
> - **DOC-1（正文即最终态）**：遵守——本文无考古层；`[spec-review-amendment]` 标记附于被修正处，说明「改成什么 + 为什么」，非演进史叙述。
> - **跨模块共享数据模型边界**：决策纪要为本 skill 私有中间产物（**不并入 design.md**，见 BASE-24）；唯一跨界产物是标准四件套，契约未变。
> - **TG-17 信任边界**：**命中**，处置见 BASE-28 五项（S1 Bash 权限 / S2 出境 secret scan / S3 injection / S4 路径 containment / S5 全局名册）。
> - **基准 5（无界语法禁手搓）**：遵守——不解析任何 Markdown/YAML 语法面。⚠️ **但原文对本基准的引用是误用**〔spec-review-amendment F-03〕：**改为**：存在态问 `status`，**合格态问 `validate --strict`**，MUST NOT 手搓 Markdown 解析器——三者分开写。

**本仓工程约束（跨票通用）**：

- 本机 pytest 只在系统 python：一律用 `/usr/bin/python3 -m pytest`。
- 通则托管块**一律经 `hack/sync_principles.py --apply` 生成**，MUST NOT 手改块内部。
- 改共享字符串/常量前先全量 `grep`（**不加 `--include` 限定**），消费者会跨 `.md` / `.py` / `.sh` / `.yml`。
- **实现期提交 MUST NOT 带 `task<N>-` 完成标签**；完成标签与验收复选框由编排层在双轴审通过后补打。

---

### Task 1: `sdflow-spec` skill 本体上线且机械门会红

**Blocked-by:** none
**R-ID:** SA-01, SA-03, SA-04, SA-05, SA-06, SA-08, SA-09, SA-10, SA-13

交付一个人可触发的 `sdflow-spec` skill，其指令完整承载三相位管线（澄清 A → 拷问 B → 生成 C）：
相位 A 的提前收束禁止清单、相位 B 的起手三步（工作树前置检查 / FF-0 三分支判定 / 建 change）与
增量落盘、相位 C 的强制阅读清单与「存在态 vs 合格态」分离核验、终审的中间态判据、降级阶梯与
三要素诊断契约、出口序列的原样呈现、相位 checkpoint、重入探测与纪要身份核验、ADR/术语惰性提议钩子。

skill 声明 `disable-model-invocation: true`，四条通则块纳入 `sync_principles.py` 投放面。表格型
少判断内容（降级阶梯表、ADR/术语最小模板、决策纪要字段 schema）外置，主体保持在体量上限内。

同时消解本票直接造成的过期断言：新增一个 SKILL.md 会使「投放面 = N 个 SKILL.md」这类硬编码计数
失真——按「删掉数字、让脚本自报」处理，并全量扫同族残留（不限定文件类型）。

配套两道**会红**的机械门：决策纪要缺失或必填小节为空即判红；一份被截断的产物喂进
`openspec validate --strict` 必须判红（证明「存在态 ≠ 合格态」这条判据真的挡得住）。

- [x] `/sdflow-spec` 在两个 runtime 均可见，且模型无法自行唤起（只能人触发）
- [x] 三相位管线的全部判据在指令中可查：A 的收束禁止清单三项、B 起手三步、B 的停止信号最小充分条件、C 的强制阅读清单（specs 步显式读 design）、写后 `status` + `validate --strict` 双判、终审的 design↔specs 互验与中间态判据、出口序列三步原样贴且**只引两条理由**
- [x] 决策纪要的字段集（含 `schema_version`/`change`/`branch`/时间戳/决策 hash 身份字段）与增量落盘时机在指令中明确；纪要 MUST NOT 并入 design.md，design 的 Decisions 只留指针
- [x] 通则托管块由 `sync_principles.py --apply` 落入，`--check` 无漂移
- [x] SKILL.md 主体行数 ≤ 设计给定上限，超出部分已外置到 `references/`
- [x] 新增 pytest 用例：`decision-memo.md` 缺失 / 必填小节为空 → 红；定点删掉该门必须红（非恒真锚）
- [ ] 新增 pytest 用例：截断的 design.md 经 `openspec validate --strict` → 红
- [x] 硬编码的 SKILL.md 计数已删除并改由脚本自报；`grep -rn` 全量扫（不加 `--include`）无同族残留
- [x] 仓根 `/usr/bin/python3 -m pytest` 全绿；`setup.sh` 幂等重跑无异常

---

### Task 2: canonical 规则单一源不再分叉，四入口选择规则双落点生效

**Blocked-by:** 1
**R-ID:** SA-11, SA-14, SA-05, SA-09

消除本 change 与既有权威规则源之间的矛盾：按 SA-11 枚举的**七处** canonical 源逐一同步——推荐
流水线加分支（已装本 skill 的仓走单入口，未装沿用旧三步）、G1 的「阶段一→阶段二」具名例外及其
两条依据（cache 按模型隔离 / 产审错档，**MUST NOT 写「主审需冷视角」**）、G1 第二处载体的独立
同步、生成物随源重生成、既有阶段一衔接 Requirement 声明新旧入口共存与路由、托管块中「ff 之后是
grill」条款的显式处置、FF-0 弱判据改为三分支判定（含其 hook 实现）。

同时把 SA-14 的四入口选择规则落到**两个受众面**：人读侧（本仓项目指令文件的非托管区，含使用路径
与出口序列）与 AI 读侧（canonical 的阶段一流程分支）。并落定旧入口的 sunset 条件（采用率 / 质量 /
成本三档阈值 + 未达标即删除本 skill 的处置）——该条款**与阶段二成败无关，本票即落定**。

- [x] SA-11 的七处逐处已同步，无一遗漏；托管区块经刷新机制生成（未手改块内）
- [x] G1 例外在其**两处载体**上各自成立（二者字面措辞不同，须分别核验，MUST NOT 指望一条 grep 同时命中）
- [x] 机械核验的 grep 锚**打得中真实结构**：跨行 ASCII 图不得用单行正则当判据（该模式实测零命中 = 永不变红的空判据）；无可靠单行锚点者如实标为人核
- [x] 生成物已随源重生成，其阶段一段落反映新分支
- [x] FF-0 三分支判定在规则文本与其 hook 实现上一致（hook 原先只挡保护分支）
- [x] 四入口选择规则在人读侧与 AI 读侧各有一份，内容不矛盾
- [x] 旧入口 sunset 条件已写死阈值与未达标处置
- [x] README 的 skills 列表含 `sdflow-spec` 且有可复制 Quick Start；重跑 `setup.sh` 后双 runtime 可见

---

### Task 3: 阶段一端到端可跑通并抗故障（阶段一验收门）

**Blocked-by:** 1, 2
**R-ID:** SA-01, SA-04, SA-05, SA-06, SA-09, SA-13

对一个**真实且有一定复杂度的需求**（非玩具）跑通 A→B→C 全程，证明薄编排形态本身就是合法交付
形态：相位 B 不可跳过、B 起手三步生效、纪要字段完整且含身份字段、增量落盘真的在约束站稳时发生、
四件套 `status` + `validate --strict` 全过、终审有记录、出口序列原样呈现、相位 checkpoint 锚落盘。

再做故障注入，六种情形各验一次处置正确：工作树脏、在其它 feature 分支、目标分支已存在、纪要陈旧
（身份字段不匹配）、CLI 缺失、CLI 载荷 schema 断言不过。

并做 `/clear` 无损抽检：清上下文后冷读产物，确认决策 why（**含砍掉的候选与砍的理由**）全部可得；
报告须如实标注该结论是 N=1 自评、非统计显著。

收尾把与阶段二/三成败无关的遗留项一并落定：相位 checkpoint 锚对 retro 归因率的改善实测；
`disable-model-invocation` 在另一宿主的语义未核项登记；与本 change 不互斥、覆盖「人直接敲
`opsx:ff`」那条本 skill 够不着路径的独立工作项登记。

- [x] dogfood 演练在一个非玩具需求上跑完 A→B→C，八项核验逐条有证据（不是「看着过」）
- [x] 六种故障各注入一次，处置与失败模式表一致：脏树/错分支 halt 问人、分支已存在走 fallback、陈旧纪要拒绝进 C 并呈摘要、CLI 缺失与 schema 不符 fail-closed 且报实际版本 + 修复命令
- [x] `/clear` 后冷读产物，砍掉的候选与理由可追溯；报告标注「N=1 自评，非统计显著」
- [x] retro 的阶段一归因率相对基线有改善，或如实记录未改善及原因
- [x] 两项未核/后续工作已登记进 todolist，**显式带 `change` 字段**（省略会误挂当前活跃 change）
- [x] 阶段一验收门结论明确落纸：本票 + Task 1 + Task 2 全过 ⇒ 方可启动阶段二

---

### Task 4: 阶段二外派能力上线（实测门先行 + 三个 agent 定义 + 铺设机械层）

**Blocked-by:** 3
**R-ID:** SA-07, SA-02, SA-12, SA-08

**先过 GO/NO-GO 实测门**：在写任何依赖 agent 定义的 producer 之前，真派一次仓内检索 agent，核验
它**确实走了 agent 定义路径**而非 fallback；核验派发的 `model` 参数收到的是具体模型 id（非字面
变量名）且档位解析走四步加固协议；实测 `tools` 的作用域参数形态是否被解析（该结果决定 S1 走
收窄还是诚实声明）。**NO-GO 即判红并停在阶段一形态**——MUST NOT 用「失败则改验 fallback」把这
道门变成不可能红的恒绿门。

门过后交付三个 agent 定义（仓内检索 / 联网调研 / 单产物生成），工具面按 S1/S2 处置，正文承载角色
纪律与排他式 description，通则块经托管机制注入；落地 S2 的最小净化查询生成与外发 secret scan
（**复用**既有实现，MUST NOT 新造）；把托管投放面改为 **glob 发现**并配独立的 skill 味源；新写独立
的 agents 安装协议（所有权守卫比既有 idiom 更严：只接管软链**且**指向本仓；Windows 分支明写不铺
并报一行）；SKILL.md 的 dispatch 段接上 `subagent_type`，任一定义不可用即降级为主 session 亲做。

- [x] GO/NO-GO 实测门有真实派发证据；结论为 NO-GO 时本票即停并如实记录（不得改验 fallback 后宣告通过）
- [x] 三个 agent 定义齐备，工具面与 S1/S2 一致；联网 agent 无仓库读取、无 `Bash`；description 为排他式
- [x] 托管投放面用 glob 发现；**新增定点用例**「往 agents 目录放一个新 `.md` → `--check` 必红」（验证是 glob 而非硬编码）
- [x] 全仓首个 setup.sh 测试就位：假 HOME 实跑，断言 ①三个定义各铺出软链且指向本仓 ②预置非本仓同名文件不被覆盖且进 `skipped[]` ③删源重跑清悬空链 ④重跑幂等
- [x] dispatch 使用 `subagent_type`（MUST NOT `agentType`）；定义不可用 → 主 session 亲查/亲写，**MUST NOT 退通用子代理**
- [x] S3/S4/S5 行为验证：网页内容中的指令性文本不被执行；越界/symlink 的写入目标被拒；三个 description 的排他性生效
- [x] 仓根 `/usr/bin/python3 -m pytest` 全绿（含本票新增用例）

---

### Task 5: 阶段二成本与质量判定（A/B 三路 + 论证密度比对）

**Blocked-by:** 4
**R-ID:** SA-02

在同一个**真实复杂 change**（非玩具需求）上跑三路对照——legacy（旧三入口）/ thin（阶段一薄编排）/
subagent（阶段二外派），量总 token、总美元、墙钟、人工返工量、阶段二评审 findings 数与采纳率，
按约定单价折算。

再做论证密度人工比对：「纪要驱动的 design.md」vs「有完整拷问上下文的 design.md」——比的是砍掉候选
的具体反例是否留存、承重约束的推导链是否完整，**而非只查字段填没填**。

据此给出阶段二验收门结论：安全面（S3/S4/S5）全过是**前提**，即便成本达标、安全不达标也不得推进；
成本与质量任一不达标 ⇒ 回退到阶段一薄编排形态（这是设计已声明的合法交付形态），agent 定义作为
未启用资产保留或删除，结论如实记入 hand-off。

- [x] 三路各跑一次同一真实复杂 change，五项指标齐全且可复核（不是估算）
- [x] 论证密度比对有具体举例（哪条砍掉的候选在纪要驱动路径上丢了/留了），不是形容词级结论
- [x] 阶段二验收门结论落纸：安全前提是否满足、成本质量是否不劣于 thin 路、判 GO 还是回退
- [x] 判回退时：回退动作已执行到位，agent 定义的去留有明确处置，hand-off 如实记录
- [x] 成本结论标注样本量与统计显著性边界（N=1 不得表述为已证实）

---

### Task 6: 阶段三产品化（分发定案 + 下游推广 + 回滚演练 + sunset 判定）

**Blocked-by:** 5
**R-ID:** SA-07, SA-11, SA-14

**仅当 Task 5 判 GO 时执行**；判回退则本票不执行，如实记入 hand-off 并说明原因。

核验 agent 定义的全局分发实际行为与文档一致；把本 change 的 canonical 改动经 bundle 更新机制推至
消费项目，并核验下游确实拿到；按设计给出的**正确顺序**实跑一次回滚演练（先在仍运行新版 installer
时移除 agents → 再 revert → 重跑 setup），核验全局 agents 目录无悬空软链残留；最后按 Task 2 已落定
的阈值判定旧入口是否进入 sunset，达标则更新人读侧与 canonical 的推荐措辞。

- [ ] 全局分发的实际铺设行为与文档描述一致（含 Windows 不铺 agents 的明写取舍）
- [ ] 至少一个下游消费项目跑完 bundle 更新，其规则副本已含本 change 的七处改动，阶段一流程在该项目可用
- [ ] 回滚演练按「先 uninstall → 再 revert → 重跑 setup」顺序实跑，全局 agents 目录零悬空软链
- [ ] 按已落定阈值判定 sunset：达标则人读侧与 canonical 的推荐措辞同步更新；未达标则按 Task 2 写死的处置执行
- [ ] 阶段三验收门结论落纸：本票四项全过 ⇒ 本 change 可进 `/sdflow-done`
