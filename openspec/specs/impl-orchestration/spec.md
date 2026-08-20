# impl-orchestration Specification

## Purpose
TBD - created by archiving change matt-workflow-integration. Update Purpose after archive.

## Requirements

### Requirement: ticket 文件兼容 ship_gate 既有完成判据契约

ticket 文件 SHALL 写入 change 目录的 `tickets.md`，每 ticket 以 `### Task N: <ticket 名>` 为标题、ticket 内含验收标准复选框；出 ticket 收尾 SHALL 显式 checkpoint（plan 单独提交建立完成窗口锚）〔grill-amendment〕。完成信号 SHALL **后置双写**〔spec-review-amendment F1；设计门 2026-07-10 拍板定稿（方案甲）〕：implementer 实现期提交 MUST NOT 带 `task<N>-` 完成标签；该 ticket 双轴审 + 修复环通过后，由执行模式补打 `checkpoint(<change>:task<N>-<slug>)` 完成标签并勾全验收复选框——**审过才算 done**；resume 发现「实现提交在、完成标签缺」SHALL 进入续审而非重实现。plan 首次提交后结构 SHALL 不可变：MUST NOT 重号/重排/删除/复用 Task 号，重规划只可追加新号〔F1〕。plan 文件 frontmatter SHALL 含且仅含 `impl-pipeline` 单键（无注释/示例/第二块——marker 块内杂行会被 gate 计为幻影任务）〔F5〕；该键为文件格式契约，SHALL 无路由读取方〔adr/0042〕。

#### Scenario: gate 以既有双通道判定 ticket 完成

- **WHEN** 某 ticket 双轴审通过、执行模式按契约补打完成标签并勾框
- **THEN** 既有 ship_gate 经 checkpoint 标签 ∪ 复选框双通道判定该 Task 号 done，CONTINUE_IMPL 的 done_tasks 集合正确携带；审前中断 resume 时该 ticket 不在 done_tasks 中、进入续审〔spec-review-amendment F1〕

### Requirement: 执行模式宿主条件化受限并行工作 frontier 并以文件交接

执行模式 SHALL 按 Blocked-by 拓扑计算工作 frontier（`next_ready` 返回所有前置已完成的 ticket 号集合）；行为按宿主分支（`$SDFLOW_HOST` 第零步已 resolve）〔spec-review-amendment〕：

- **`host=claude`**：`next_ready` 返回多个候选时 SHALL 并行派发 implementer 子代理，**每个 implementer SHALL 使用 `isolation: "worktree"`**（Agent tool 原生参数，harness 自动创建独立 git worktree）。所有 implementer 返回后，编排层 SHALL **逐票按号序串行** merge worktree 分支回主分支（`git merge --no-ff`）→ 双轴审 → fix 循环（如有）→ checkpoint commit。
- **`host=codex` / `host=unknown`**：`next_ready` 返回多个候选时 SHALL **按号序逐个派发**（退化为串行），行为与改动前完全一致——Codex 无原生 worktree 隔离且进程回收模型不兼容并行。
- `next_ready` 返回单个候选时行为与串行模式一致（两宿主一致）。

**并行 dispatch 约束（Claude 宿主）**：每个 implementer 在独立 worktree 中工作，有独立 `.git/index` 和工作树，不存在 index 竞态；dispatch prompt MAY 建议按文件名 `git add <具体文件>`（最佳实践，非 MUST——worktree 隔离下通配暂存不会带入别人的改动）；双轴审 SHALL 串行执行（不同票之间亦不并行，反向变异共享工作树会交叉感染）；收尾 ticket（`Blocked-by` = 全部功能票号）`next_ready` 只返回它一个，始终单独串行执行。

**review-package 生成（并行批次，Claude 宿主）**：merge 回主分支后，每个 merge commit 天然隔离各票改动——审第 N 票时 `before-sha` = merge commit 的第一父（merge 前主分支 HEAD）、`after-sha` = merge commit 自身，`git diff <merge_parent1>..<merge_commit>` 天然只含该票改动；串行票的 review-package 沿用既有 `<before-sha>..<after-sha>` 规则不变；fix 轮的 `<before-sha>` 沿用既有规则不变（fix commit 在串行审阶段单线程产生，无并发写入）。

**异常处理（Claude 宿主）**：并行 implementer 中某个返回 BLOCKED / NEEDS_CONTEXT 时，harness 无中途取消能力，编排层 SHALL 等全部返回后逐个处理状态；BLOCKED 票的 worktree 直接丢弃（不 merge 回主分支），无脏改动污染；完成态票据正常走完 merge+审+checkpoint，不因兄弟票 BLOCKED 而搁置，白跑成本为可接受边角。`git merge --no-ff` 冲突时编排层 SHALL 上报人介入（halt envelope 五要素）——worktree 隔离下 merge conflict 是**真正的 fail-loud**。

其余契约不变：每 ticket 派发 fresh implementer 子代理，契约为 TDD at pre-agreed seams、定期 typecheck、**单元测试 + 本 ticket 声明的 e2e 场景 + 本 ticket `Blocked-by` 链上模块的集成测试**（MUST NOT 跑**与本票无依赖关系**的集成/e2e 套件——聚合回归由「实现验证」收尾 ticket 承担，见「出 ticket 模式产出 tracer-bullet ticket 并落盘即返回（tickets.md 单名）」需求）、完成信号双写；「本 ticket 声明的 e2e 场景」SHALL 由 ticket 验收标准中标注为 e2e 的条目界定，未标注即该票无 e2e 场景〔spec-review-amendment M7〕；implementer 状态词表为 DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED——NEEDS_CONTEXT SHALL 由编排层从盘面（design.md/specs/ticket 文本）自答，答不出走 defer 或停，MUST NOT 编造；BLOCKED 无法消解 SHALL 停并上抛。子代理产物 SHALL 以文件交接：implementer 全量报告写 report file（按 ticket 名命名）只返回状态摘要；reviewer 输入 diff 经 review-package 式文件传递，MUST NOT 把大产物粘贴进 dispatch prompt。审出的 cannot-verify-from-diff 项（需求活在未改动代码或跨 ticket）SHALL 由编排层亲自消解，且 SHALL 设预算上界：需触碰超过 3 个文件、或从盘面（design/specs/ticket 文本）不可直接解答时，MUST 按「确认缺口退回 implementer」处理〔spec-review-amendment F7〕。frontier 的 next-ready 判定 SHALL 由确定性 helper 计算（解析 Blocked-by + gate done_tasks 拓扑排序，stdlib-only）〔F8〕。一切停机（BLOCKED/依赖缺失/gate 拒绝）SHALL 以统一 halt envelope 呈现：错误码、ticket 号与名、已核证据、已写盘副作用、精确恢复步骤〔F7〕；BLOCKED 的 blocker 记录 SHALL 落盘 report file（change 目录内、git-tracked，防 compaction 蒸发）〔F7〕。DONE_WITH_CONCERNS SHALL 与 DONE 同路径进双轴审，implementer 所述 concerns 逐字附给两轴〔F7〕。

#### Scenario: Claude 宿主 frontier 受限并行推进（worktree 隔离）

- **WHEN** `$SDFLOW_HOST=claude`，ticket 2、ticket 3 均 Blocked-by ticket 1 且 ticket 1 完成
- **THEN** 编排层并行派发 ticket 2 和 ticket 3 的 implementer（各自 `isolation: "worktree"`）；两者全部返回后，merge worktree-2 回主分支 → 审 ticket 2 → checkpoint，merge worktree-3 回主分支 → 审 ticket 3 → checkpoint

#### Scenario: Codex 宿主退化为串行

- **WHEN** `$SDFLOW_HOST=codex`，ticket 2、ticket 3 均 Blocked-by ticket 1 且 ticket 1 完成
- **THEN** 编排层按号序先派 ticket 2（无 worktree 隔离）→ 审 → checkpoint，再派 ticket 3 → 审 → checkpoint

#### Scenario: 依赖图为线性链时退化为串行

- **WHEN** 每 ticket 的 Blocked-by 严格指向前一 ticket（1→2→3→4→5）
- **THEN** `next_ready` 每次只返回一个候选，行为与改动前完全一致（两宿主一致）

#### Scenario: 并行 implementer 的 review-package 隔离（Claude 宿主）

- **WHEN** ticket 2 和 ticket 3 并行执行完毕（各在独立 worktree），编排层进入串行 merge+审
- **THEN** merge ticket 2 的 worktree 分支后，审 ticket 2 的 review-package diff = `merge_parent1..merge_commit`，天然只含 ticket 2 的改动

#### Scenario: 并行 implementer 某个 BLOCKED（Claude 宿主）

- **WHEN** ticket 2、ticket 3、ticket 4 并行派发（各自 worktree），ticket 3 返回 BLOCKED
- **THEN** 编排层等全部返回后，逐个处理：merge ticket 2 和 ticket 4 的 worktree 分支回主分支并正常进审+checkpoint；ticket 3 的 worktree 直接丢弃（不 merge），按 BLOCKED halt envelope 处理

#### Scenario: 并行 implementer 碰同一文件时 merge conflict fail-loud

- **WHEN** ticket 2 和 ticket 3 并行执行后各自改了同一文件的不同段
- **THEN** merge ticket 2 后无冲突；merge ticket 3 时 `git merge --no-ff` 报冲突，编排层 SHALL 上报人介入

#### Scenario: NEEDS_CONTEXT 从盘面自答

- **WHEN** implementer 返回 NEEDS_CONTEXT 询问某接口约定
- **THEN** 编排层从 design.md/ticket 文本中定位答案回填再派发；盘面无答案时按 T10 处理（defer 或停），不编造

> 〔spec-review-amendment H6〕本 Scenario 的 "T10" 字样 SHALL 原样保留——它是仅引用尾部处置（defer 或停）、未提及仲裁步的轻量引用，design 的 scope-check 表把它列在【不动】。首版 delta 曾把它改写成「按 defer 或停处理」，属 MODIFIED 整段替换时的静默删除。

#### Scenario: 功能 ticket 只测本票范围

- **WHEN** 某功能 ticket 的 implementer 即将返回 DONE
- **THEN** 已运行单元测试 + 该 ticket 声明的 e2e 场景（若有）+ 本票 `Blocked-by` 链上模块的集成测试并全部通过，MUST NOT 运行与本票无依赖关系的集成/e2e 套件

### Requirement: 每 ticket 双轴审加修复环，领域清单注入 Standards 轴

每 ticket 实现完成后 SHALL 并行派发两个评审子代理：Standards 轴（仓内文档化标准 + Fowler smell 基线，且 SHALL 把 code-checklists/domains/<命中栈>（经 resolve-workflow.sh 解析）作为标准源注入 = 注入点 B）与 Spec 轴（对照 ticket 文本验收标准与 R-ID 溯源需求）；两轴均按 mid 档派发（见「sdflow-implement 档位解析与声明」需求）；两轴输出各 SHALL 封顶（<400 词量级）。Critical/Important 发现 SHALL 派 fix 子代理（mid 档）修复并 re-review 直至通过；Minor 发现 SHALL defer 进 todolist（显式带 change 字段）。code-checklists/domains 经 resolve-workflow.sh 解析失败、规则根不可达或命中栈无清单时，Standards 轴 MUST NOT 宣称通过——SHALL 显式停或在报告记「领域清单未覆盖」并留降级原因〔spec-review-amendment F13〕。

**Standards 轴的治理规则 SHALL 含「Tests are code」**〔curb-rework-loop-cost〕：Fowler smell 基线同样适用于**测试文件**，尤其 Duplicated Code（重复的测试形状应合并）与 Speculative Generality（为想象中的需求预写的测试应删除）——测试只增不减会让全量套件的单次成本单调上升，而该轴是流程中唯一的遏制点。**reviewer MUST NOT 直接删测试**，只报 finding 交裁决。

**熔断规则 `review-loop-breaker`（本需求独立定义，MUST NOT 引用其它能力的 "T10" 标签——本场景语义为「同一发现反复未消解」，与阶段三 `T10-choice`「≥2 方案自动选」触发条件不同）**：

- **触发（两条判据并列，命中任一即停）**：
  - **(a) 同指纹判据**：同一发现连续 2 轮 re-review 仍未消解 SHALL 停止循环。
  - **(b) 与指纹无关的硬上限**〔curb-rework-loop-cost · adr/0035〕：**同一文件累计被 Critical/Important 发现命中 ≥3 轮**时，无论各轮的问题指纹是否相同，SHALL 停止循环。此时仲裁的命题 SHALL 是「**这个门 / 这段实现本身该不该存在**」，而非「这一条 finding 是否成立」。
  - 判据 (b) 存在的理由：(a) 的身份键可被「同一根因每轮换一个语法分支」绕过——每轮指纹不同则计数清零，`MUST NOT 无限循环` 无从兑现。**MUST NOT 试图靠「让指纹算法更能识别同一根因」来替代 (b)**：那要求指纹算法判断「什么是同一个根因」，本身即模型判断，且落在无界语法面上。
  - **(a)(b) 同时命中时 (b) subsume (a)**〔curb-rework-loop-cost · R-9〕：第 3 轮同时满足两条判据时，只派 (b) 的仲裁（「门本身该不该存在」），MUST NOT 同时派两个不同 scope 的仲裁。
- **计数窗口 SHALL 为全 change 生命周期**〔curb-rework-loop-cost · R-10〕：「同一文件累计命中轮数」跨该 change 的全部 ticket 累计，MUST NOT 按单 ticket 独立清零。
- **熔断账本 SHALL 持久化**〔curb-rework-loop-cost · R-5〕：编排层在每轮 fix-review 后 SHALL 追加一行到 `impl-reports/breaker-ledger.md`，格式 = `轮次 | 文件 | 指纹 | 严重度`。该账本 git-tracked，支持跨 context 压缩后恢复计数与事后审计，但不构成机械门。
- **身份键 SHALL 跨轮稳定**：判定「是否同一发现」SHALL 用「同文件 + 规范化问题指纹」，**行号只作定位、MUST NOT 作为身份键的组成部分**〔spec-review-amendment H3〕——修复几乎必然移动行号，用行号当身份会让同一未解决问题被认成新发现、轮次计数清零。
- **(b) 仲裁 dispatch 的 review package SHALL 含该文件 ticket 起点以来的累积 diff**〔curb-rework-loop-cost · R-4〕，不受「fix 轮 review package 只含本轮修复 diff」（③）的增量限定——仲裁命题是「门本身该不该存在」，需要看跨轮修复模式。**(b) 优先于 ③。**
- **三级处置 SHALL 归于互斥终态，MUST NOT 停在「已确认成立」而无后续动作**〔spec-review-amendment H4〕：①有客观判据（测试/断言/基准可判）→ 自动选并记理由后关闭（**预期极少触发**：触发前提已是连续 2 轮不消解，能客观判定的话第 1 轮就该修好；保留该档是为两组处置形状对称，成本近零）；②无客观判据 → 派对抗镜复核该发现是否成立，复核 SHALL 用 **strong 档**（本场景是低频、需要独立判断力打破同档循环的仲裁点）——复核判**不成立** → 关闭该发现并记理由；判**成立且可修** → 派 strong 档 fix 子代理修复并**仅复验一次**，复验通过则关闭、不通过转 ③；③复核不过、无从复核、或判成立但不可修 → defer 进 buglist 并停上抛。**MUST NOT 无限循环。**

执行模式 MUST NOT 追加 warm final whole-branch review（冷层 sdflow-code-review 紧随其后承担全分支审）。

#### Scenario: 双轴审通过才推进下一 ticket

- **WHEN** 某 ticket Spec 轴报缺失验收项
- **THEN** 派 fix 子代理修复 → re-review → 通过后才标记该 ticket 完成并推进 frontier；MUST NOT 带着未修 Critical/Important 推进

#### Scenario: 实现完成直接交冷层

- **WHEN** 全部 ticket 完成、gate 判定进入 RUN_CODE_REVIEW
- **THEN** 直接触发 sdflow-code-review 冷层主审，中间无 warm 全分支终审步

#### Scenario: 熔断后派 strong 档对抗镜复核

- **WHEN** 同一发现连续 2 轮 re-review 仍未消解，且无客观判据可自动选
- **THEN** 编排层派一个 strong 档对抗镜复核该发现是否成立，不得沿用 mid 档同档互判

#### Scenario: 修复移动行号不重置熔断计数

- **WHEN** 某发现在第 1 轮修复后行号变化，但同文件内同一问题指纹仍存在
- **THEN** 第 2 轮 re-review SHALL 判定为同一发现并触发熔断，MUST NOT 因 `file:line` 不同而当作新发现重新计数

#### Scenario: 同根因换语法分支被硬上限熔断

- **WHEN** 某文件连续 3 轮各报出一条 Critical/Important 发现，但三轮的问题指纹各不相同（如同一解析器每轮被指出漏掉一个新的语法构造）
- **THEN** SHALL 触发 (b) 硬上限熔断，仲裁命题为「这个门本身该不该存在」；MUST NOT 因指纹不同而继续第 4 轮

#### Scenario: 复核判成立后必须走向终态

- **WHEN** strong 档复核判定该发现确实成立
- **THEN** 编排层 SHALL 二选一：可修则派 strong 档 fixer 修复并仅复验一次；不可修则 defer 进 buglist 并停上抛。MUST NOT 在「确认成立」后回到原 re-review 循环

### Requirement: 不引入 ledger 与 task-brief 层

执行模式 MUST NOT 维护 progress ledger 类跨会话状态文件（完成态唯一真相源 = gate 的 checkpoint∪复选框双通道，resume 经 CONTINUE_IMPL done_tasks）；MUST NOT 引入 task-brief 抽取层（行为级 ticket 文本即 brief，dispatch 直携 ticket 文本）。

#### Scenario: 中断后 resume 不重派

- **WHEN** 执行中途会话中断，重调 /sdflow-ship
- **THEN** gate 从盘面输出 done_tasks 已完成 ticket 号集，编排层跳过已完成 ticket 从 frontier 续跑，全程无 ledger 参与

### Requirement: implementer dispatch 携带信号权威归属声明

`sdflow-implement` 派发 implementer / fix 子代理时，dispatch prompt SHALL 携带一份**信号权威表**，正面声明「完成信号写哪里」与「设计工件不可碰」——子代理跑在 fresh context，看不见 SKILL.md 与 CLAUDE.md，未声明即等同未约束。

声明 SHALL 为正面陈述（列出权威归属），MUST NOT 仅写成禁令清单——禁令只挡列举到的那一种越界，权威表挡的是整个范畴。

本要求的适用面 SHALL 限于本仓自有的 `sdflow-implement`；本要求 MUST NOT 被当作设计门失鲜问题的唯一防线（机械防线在 `spec-workflow` 的设计门新鲜度内容判据）。

#### Scenario: dispatch prompt 含信号权威表

- **WHEN** `sdflow-implement` 执行模式派发 implementer 或 fix 子代理
- **THEN** prompt MUST 含信号权威表，至少覆盖两行归属：完成信号 = `tickets.md` 验收复选框 + `checkpoint(<change>:task<N>-<slug>)` 标签；设计工件 = `proposal.md` / `design.md` / `tasks.md` / `specs/`，实现期不修改
- **AND** 该表 MUST 与 `ship_gate.py` 实际消费的完成判据一致（plan 复选框 + checkpoint 标签），MUST NOT 声明 gate 并不读取的信号源

#### Scenario: 权威表缺席不得静默降级

- **WHEN** 因 SKILL 裁剪或模板漂移导致 dispatch prompt 未携带信号权威表
- **THEN** 该缺席 MUST NOT 被当作「已由 gate 兜住所以无所谓」——gate 的监视集分流只消解失鲜误判，不阻止 implementer 写脏设计工件；本要求与 gate 侧要求 SHALL 各自独立成立

### Requirement: sdflow-implement 档位解析与声明

`sdflow-implement` SHALL 在起手执行"宿主/档位解析"四步,**语义**与 `sdflow-code-review`/`sdflow-spec-review` 一致(清脏 unset `SDFLOW_HOST`/`SDFLOW_TIER_STRONG`/`SDFLOW_TIER_MID`/`SDFLOW_TIER_LIGHT` → 预检 `resolve-models.sh` 可执行 → 捕获退出码后 eval → eval 后校验)。**对齐目标为四步语义,MUST NOT 要求与任一姊妹 skill 逐字相同**〔spec-review-amendment Q5〕:各 skill 内部的"本步第 N 项"类交叉引用是依该文件本地结构派生的量、不可搬运,跨文件引用 SHALL 使用具名锚点(如「见预检步」)。四份拷贝的一致性 SHALL 由机械 parity 守卫对归一化核心段做逐字节比对保证,MUST NOT 只靠人工核对。

该四步 SHALL 在"一文件两入口"(`tickets-plan` / `tickets-exec`)结构中**置于文件最前、两入口共用、无条件执行**——出票模式同样消费档位(粒度争议与一致性自扫的仲裁步派 strong 对抗镜),不是空转步。

**失败与降级处置(fail-closed)**:下列任一情形 SHALL fail-loud 硬停,MUST NOT 用空档位或默认值继续派发——① `resolve-models.sh` 不存在或不可执行;② 非零退出或输出无法 eval;③ eval 后 `$SDFLOW_HOST` 为空(= resolver 没跑成)或不属 `{claude,codex,unknown}`;④ `$SDFLOW_HOST` ∈ `{claude,codex}` 但三档任一为空;⑤ **`$SDFLOW_HOST` = `unknown`**;⑥ Codex 宿主下能力探针判子代理不可用。**③ 与 ⑤ SHALL 分别报错,MUST NOT 把空值吸进 unknown 路径**。**⑤/⑥ 之所以硬停而非降级**:`sdflow-implement` 不派子代理就跑不了任何 ticket,与 `sdflow-code-review`"缩 roster 到主 session 独立完成的镜"的降级路径**不同构**,不存在等价的单 session 退路〔spec-review-amendment H10〕。停机 SHALL 以既有五要素 halt envelope 呈现,其 ticket 号字段填「—(起手失败,无票上下文)」,并逐类给出 problem+cause+fix。

implementer、Standards 轴、Spec 轴、fix 子代理派发 SHALL 引用本次解析得到的 `$SDFLOW_TIER_MID`,MUST NOT 内联具体模型名。Codex 宿主下这四类派发 SHALL 视为已授权(项目指令文件的「Codex 子代理授权」段 MUST 同步列入 `sdflow-implement`)〔spec-review-amendment H11〕。

#### Scenario: 档位解析成功后派发子代理

- **WHEN** `sdflow-implement` 起手完成宿主/档位解析,`$SDFLOW_HOST` ∈ `{claude,codex}` 且三档均非空
- **THEN** 后续 implementer/Standards轴/Spec轴/fix 子代理 dispatch 均引用 `$SDFLOW_TIER_MID`,不内联模型名

#### Scenario: 档位解析失败即硬停

- **WHEN** `resolve-models.sh` 不可执行,或 eval 后 `$SDFLOW_HOST` ∈ `{claude,codex}` 但三档任一为空
- **THEN** `sdflow-implement` fail-loud 硬停,报告 problem+cause+fix,MUST NOT 用空档位或默认值继续派发

#### Scenario: host 为空与 host=unknown 分别报错

- **WHEN** eval 后 `$SDFLOW_HOST` 取到空值(resolver 没跑成),或取到 `unknown`(跑成但判不出宿主)
- **THEN** 两者 SHALL 报**不同**的 cause 与 fix,且均硬停;`unknown` MUST NOT 被当作"三档可为空"的合法态继续执行,空值 MUST NOT 回落当 `unknown` 处置

#### Scenario: Codex 宿主子代理不可用则硬停而非缩 roster

- **WHEN** `$SDFLOW_HOST="codex"` 且能力探针判定子代理机制不可用
- **THEN** `sdflow-implement` 硬停并提示在受支持宿主下运行,MUST NOT 由主 session 顶替 implementer/双轴审继续跑 ticket

#### Scenario: 四个 skill 的第零步由机械守卫锁住

- **WHEN** 任一 skill(`sdflow-implement`/`sdflow-done`/`sdflow-code-review`/`sdflow-spec-review`)的第零步核心段被单方面修改
- **THEN** parity 守卫测试判红;守卫 SHALL 对每一步都有效(逐步删除任一步必红),MUST NOT 是恒真锚

### Requirement: fix 轮的 review package 只含本轮修复 diff

双轴审的 reviewer 输入经 review-package 式文件传递（见「执行模式宿主条件化受限并行工作 frontier 并以文件交接」需求）。**fix 轮次的 review package SHALL 只含该轮的修复 diff**（`上轮已审 SHA..HEAD`），MUST NOT 重新打包自 ticket 起点以来的累积全量 diff。

理由：fix 轮的评审命题是「这次修复对不对」，不是「重新全审这张票」；累积打包会让同一段 diff 被反复读入 reviewer context（实测单包最大达 1,356KB）。首轮 review package 的范围不变。

#### Scenario: 第二轮 fix 的 review package 不含首轮已审内容

- **WHEN** 某 ticket 首轮双轴审报出 Critical，fix 子代理修复后进入第 2 轮 re-review
- **THEN** 该轮 review package 的 diff 范围 SHALL 为「首轮已审 SHA..HEAD」，MUST NOT 包含首轮已经审过且未再改动的 hunk

### Requirement: 往既有测试补断言或修改既有断言同样适用 red-before-green

implementer 的 TDD 契约为 red-before-green（见「执行模式宿主条件化受限并行工作 frontier 并以文件交接」需求）。该纪律 SHALL 同样适用于**往既有测试文件补一条断言或修改既有断言的期望值/判定逻辑**的场景，而不限于新写测试：**补一条断言或修改既有断言时 SHALL 先确认它会红**——当场破坏被测点、确认该断言失败，再恢复。

理由：恒真断言（needle 被别的门满足，或压根没有用例走到该行）在写入时无成本可验，在事后 review 时才被发现，届时已需一整轮返工。修改期望值同理——改后仍恒真的断言同样是假绿。该自检成本为一次聚焦运行。

#### Scenario: 补断言或改断言未验红被 Standards 轴判为缺口

- **WHEN** implementer 往既有测试补了一条断言或修改了既有断言的期望值，报告中未给出「该断言曾验红」的证据
- **THEN** Standards 轴 SHALL 判该项为缺口并要求补验；MUST NOT 因「测试整体是绿的」而放过

#### Scenario: 收尾票豁免不受本需求扩展影响

- **WHEN** 「实现验证」收尾票按既有契约豁免 red-before-green
- **THEN** 该豁免继续有效——收尾票不写产品代码、验收物是证据不是 diff，本需求的扩展 MUST NOT 被解读为取消该豁免

### Requirement: 阶段三派发直连 sdflow-implement（唯一管线）

tickets SHALL 为唯一实现管线〔adr/0042，取代「管线路由为手动确定值，零模型自动判断」需求〕。ship 编排 SHALL 无路由直连派发：gate 判 RUN_PLAN ⇒ 派发 `sdflow-implement mode=tickets-plan change={change}`；判 CONTINUE_IMPL ⇒ 派发 `sdflow-implement mode=tickets-exec change={change} done_tasks={gate JSON done_tasks 原样透传}`。派发 SHALL 以显式字面 args 传递模式与 done_tasks（SKILL.md 与 ship 链序两处共享同一契约串）〔承 F4〕。`openspec/config.yaml` 的 `impl-pipeline` 键 SHALL 无读取方（键退役）：存量键 MUST NOT 影响任何行为。ship_gate MUST NOT 读取 config（零依赖不变量，逐字保留）。计划文件 `tickets.md` 的 frontmatter SHALL 含且仅含 `impl-pipeline: tickets` 单键——该键为文件格式契约（无注释/示例/第二块，marker 块内杂行会被 gate 计为幻影任务〔承 F5〕），SHALL 无路由读取方。

#### Scenario: RUN_PLAN 直连出票模式

- **WHEN** gate 判定 RUN_PLAN
- **THEN** ship 直接派发 `sdflow-implement mode=tickets-plan`，全程无路由 helper 调用、无 PIPELINE_RECEIPT 产出

#### Scenario: CONTINUE_IMPL 直连执行模式

- **WHEN** gate 判定 CONTINUE_IMPL 且 JSON `done_tasks` 为已完成号集
- **THEN** ship 直接派发 `sdflow-implement mode=tickets-exec done_tasks={原样透传}`，MUST NOT 重算或猜测 done_tasks

#### Scenario: 存量 impl-pipeline 键不影响行为

- **WHEN** 某仓 `config.yaml` 仍残留 `impl-pipeline` 键（任意取值，含 `superpowers`）
- **THEN** 阶段三行为与无键完全一致（键无读取方），MUST NOT 报错、MUST NOT 路由到任何旧管线

### Requirement: 出 ticket 模式产出 tracer-bullet ticket 并落盘即返回（tickets.md 单名）

sdflow-implement 出 ticket 模式 SHALL 从 design.md 与 tasks.md 产出 3-6 张 tracer-bullet 垂直切片 ticket（计数仅约束垂直切片；expand–contract 例外序列的迁移批次、以及下述「实现验证」收尾 ticket 均不占该预算〔spec-review-amendment E5〕；design.md 写明成立的「单票交付」缺席理由且出票确为 1 张功能票时，是与 expand–contract 并列的合法例外，同样不受该预算约束〔impl-review-fix〕）：每 ticket 为打穿全层、可独立验证的行为级描述，MUST NOT 预写实现代码或具体文件路径；每 ticket SHALL 声明显式 Blocked-by 阻塞边与 R-ID 需求标注；宽重构（单一机械改动 blast radius 扫全仓）SHALL 走 expand–contract 序列例外而非强行垂直切片。ticket 文件头部 SHALL 逐字携带 design 领域约束为 Global Constraints 节。

**切片建议消费语义 SHALL 为「默认采纳 + 偏离审计」**〔harden-ticket-slicing〕：出票起手 SHALL 读 design.md 的「切片建议」节；节存在时其初步 ticket 划分与阻塞边草图 SHALL 作为**默认切分方案**采纳（该草图已经阶段二评审与设计 HARD-GATE，是流程中唯一被强档模型审过、人门可见的切分判断），出票方对草图的每处**实质偏离**（增/删/合并票、改阻塞边、改切片边界）SHALL 逐条记入 `impl-reports/planning-decisions.md` 并附理由，行格式 = 「切片偏离: <偏离点> | <理由(三镜+主次)>」，MUST NOT 静默偏离；节缺席或偏离时按下述必触发条款复核。

**T10-choice 对抗镜复核 SHALL 必触发于三种情形之一**〔harden-ticket-slicing〕：① design.md **既无**「切片建议」节、**也无**成立的缺席理由（= SA-18 违规态；有成立缺席理由的合规缺席不触发本条——但缺席理由蕴含单票交付而实际出票 >1 张功能票 ⇒ 视同条件③矛盾触发〔spec-review-amendment Q1-A〕）；② 出票实质偏离草图（偏离后的方案须复核）；③ 草图与 design.md 正文矛盾（评审 amendments 只改其他节时，切片节可残留旧切分——文件级失鲜监视不覆盖节级一致性，此处是该缺口的唯一显形点）。任一命中即派 **strong 档**对抗镜复核切分方案，复核记录按既有行格式落 `impl-reports/planning-decisions.md`；既有「粒度争议」触发路径保留不变。复核结论 SHALL 按既有 `T10-choice` 三级协议出口处理：通过 ⇒ 按复核确认的方案出票；**复核不过或无从复核 ⇒ 停并上抛**（与下方一致性自扫段同口径），MUST NOT 以被证伪的切分方案继续出票〔spec-review-amendment〕。**必触发为指令层约束（「偏离/矛盾」的判定由出票方自报，无确定性信号），MUST NOT 被表述为机械保证。**

**验收标准的语法面有界性闸门 SHALL 在出票时施加**〔curb-rework-loop-cost〕：某条验收标准若要求对某种语法面**做机械判定**，出票方 SHALL 先判该语法面能否穷举——**有界**（如 CommonMark fence 变体、自有格式的机器锚行）⇒ 可写为机械门；**无界**（通用编程语言源码、YAML、make、shell）⇒ **MUST NOT 写成机械门**，SHALL 改为「让该工具自己回答」（真跑一遍看行为 / 调用该格式的权威解析器），或降级为 best-effort 展示且**不作判定依据**。该判据 SHALL 覆盖伪装形态——不仅匹配「扫描 / 识别 / 拒绝某形态 / 指纹」这类显式措辞，**还 SHALL 匹配「在某格式文件中定位 / 插入 / 修改某处」**（「只动一个键值」听起来不像解析，但「找到那个键」本身就要解析）。**本闸门是指令层约束，MUST NOT 被表述为机械保证。**

**计划文件名 SHALL 为 `tickets.md` 单名**〔adr/0042；adr/0033 的按轨分列语境成为历史〕。**在途 plan MUST NOT 被重命名**——完成判据窗口起点由 `git log --diff-filter=A -- <plan 路径>` 取得，该判据**不跟随重命名**，改名会把窗口起点推到改名 commit，使改名前的全部 checkpoint 标签落到窗口外、已完成 ticket 被判未完成并可能重派。∴ 在途 plan SHALL 保留原文件名直至该 change 归档。gate SHALL 经共享 resolver 定位计划文件：`tickets.md` 存在即用之；不存在则判 RUN_PLAN。

出 ticket SHALL 落盘即返回编排层（ship），MUST NOT 在同一调用内直通执行——保 ship_gate 在出 ticket 后/执行前的校验插入点。原版 to-tickets 的 quiz-the-user 人类步 SHALL 删除（阶段三无人类门），粒度争议按 `T10-choice` 三级决策协议处理（①有客观判据自动选并**按三镜 + 主次**记理由；②无客观判据派 **strong 档**对抗镜复核推荐切分方案，通过方自动选；③复核不过或无从复核 defer）〔spec-review-amendment M3：首版此处漏了「按三镜 + 主次」限定词〕。**出票模式的仲裁记录 SHALL 有确定性审计落点**：写入 `impl-reports/planning-decisions.md`（change 目录内、git-tracked，由出票落盘的同一次 checkpoint 一并提交），行格式 = 「`T10-choice` 复核: <方案> | 对抗镜结论 <通过/证伪> | <理由(三镜+主次)>」——出票模式无 code-review 报告产物，此前该仲裁结果**无处可落**〔spec-review-amendment M15〕。

**出 ticket 模式 SHALL 在全部功能垂直切片之后追加一张强制的「实现验证」收尾 ticket**，`Blocked-by` 声明为全部功能 ticket 号，`R-ID` 为 `all`（语义 = 覆盖本 change 全部需求的聚合验证，Spec 轴据此核验而非逐条溯源）〔spec-review-amendment M6〕，其验收标准 SHALL 为「按下述发现契约运行本 change 的聚合测试套件（单元+集成+e2e）并全部通过」。

**聚合套件发现契约（MUST NOT 解析构建文件）**〔spec-review-amendment Q6〕：① 命令来源优先级 = `openspec/config.yaml` 的 `test-suites.{unit,integration,e2e}` 显式配置 → 缺失则由该票 implementer 依仓内既有约定判定并在票报告写明命令原文与判定依据；② 「某命令能不能跑」SHALL 由**真跑一遍看退出码**回答，MUST NOT 靠解析 Makefile/package.json 预判 target 是否存在；③ 仓内确无某层时 SHALL 记「未覆盖（本仓无此层）」并附依据，**MUST NOT fail-closed 罢工**——`sdflow-implement` 的承诺是「不管什么项目都能跑完实现管线」，罢工分支直接背叛该承诺；④ 证据 SHALL 落确定性 schema，每层一行 `<层> | <命令原文> | <退出码> | <测试时 git rev-parse HEAD>`，未覆盖层写 `<层> | — | 未覆盖 | <依据>`；⑤ 退出码非 0 SHALL 分四类处置：本 change 引入的回归 → 进 fix 循环；仓内既有红测（以 base SHA 复跑确认）→ 记录放行；flaky（同命令复跑一次即绿）→ 记录放行；环境故障 → halt envelope 停并上抛。

**`test-suites` SHALL 支持成本分档**〔curb-rework-loop-cost〕：每层的值为**字符串**时 quick 与 full 两档同命令（今日形状，继续有效）；为**映射**时读 `quick` / `full` 两键——缺 `quick` 视为该层无 quick 档，缺 `full` 视为未分档（quick=full 同命令）。旧形状是新形状的合法子集，**未配置的消费仓行为 SHALL 等同于扩展前**，MUST NOT 要求下游同步改配置。`test-suites` 的具体命令因项目而异，**SHALL 由 `sdflow-devenv` 运行时调研项目测试基础设施后推荐写入**（已有配置时保留不覆盖），本 change 只定义 schema 与消费语义。

**中间 fix 轮与收口轮的测试范围 SHALL 分离，且范围 SHALL 由确定信息界定**〔curb-rework-loop-cost · adr/0035〕：

- **中间 fix 轮** SHALL 只跑 **unit 全层**（整层跑、不做用例筛选；若该层配了 `quick` 则取 `quick`，**无 `quick` 则取 `full`——unit 层 MUST NOT 因缺 quick 档被跳过**）**加上轮失败的具体用例（⊂ unit 层）**；集成与 e2e SHALL 整体推迟到收口。中间轮的结果**仅供诊断，SHALL NOT 作为最终报告的通过证据**。
- **收口时**（双轴审判通过、打完成标签之前）SHALL 跑一次全量（各层取 `full`），报告中所有判「通过」的行 SHALL 锚**同一个最终 SHA**（= 最后一次修复之后的 `git rev-parse HEAD`）。**单一盘面语义不变**〔原 impl-review-fix FIX-4〕：`unit@A → integration@B` 拼接式的「全部通过」依旧非法。
- 🔴 **范围 MUST NOT 由「哪层受影响」的判断界定**——e2e 按定义端到端、集成测试跨模块，任何改动都可能影响它们，「本次不影响某层」是不可靠判断，把它放进关键路径等于把 fail-open 写进条款。**要求实施者为该判断写明依据不构成缓解**：要求解释一个不可靠判断，只会得到一个有说服力的错误判断。

**该票 SHALL 走跟普通 ticket 相同的 implementer + 双轴审 + fix 循环**，但 SHALL 定制三处执行契约〔spec-review-amendment H9〕：① **豁免 red-before-green**（该票不写产品代码，验收物是证据不是 diff）；② **主证据锚 = 该票 impl-report 文件 + 其内的 SHA 三元组，MUST NOT 依赖该票产生 commit**（`checkpoint-commit.sh` 在干净树上直接成功退出、不建 commit，聚合套件一次绿时可能根本无 commit）；③ Standards 轴核验范围 SHALL 为「修复方式未靠**加 skip / 改测试配置 / 删除或弱化断言**蒙混过关」（原措辞只禁删除或弱化断言，挡不住加 skip）。

**`sdflow-done` 的 verify SHALL 引用该票 impl-report 作为「实现期聚合覆盖」需求的证据锚，不扩张 verify 自身职责**；**锚的语义 SHALL 限定为「实现期结束时聚合套件通过」，MUST NOT 表述为「最终代码通过全量回归」**——该票执行于 `sdflow-code-review` 及其自动修复循环之前，code-review 之后的修复由其自身保障机制覆盖，此证据时效缺口是已知且接受的残余风险〔spec-review-amendment Q2〕。**该锚为无条件要求**（tickets 为唯一实现管线〔adr/0042〕）。

**收尾票的存在与位置 SHALL 有机械保证**〔spec-review-amendment H12〕：`ship_gate` 的 plan 校验 SHALL 含一道——该 plan MUST 恰含一张「实现验证」收尾 ticket 且其 `Blocked-by` ⊇ 全部功能 ticket 号，不满足即判非 0〔adr/0042：旧名 grandfather 条款随双名退役删除〕。

出票落盘前 SHALL 做一次全 ticket 语义一致性自扫（拓扑之外的语义矛盾，如某票假设的接口形状被另一票废弃）；发现矛盾按 `T10-choice` 三级决策协议处理（①有客观判据自动选并**按三镜 + 主次**记理由；②无客观判据派 **strong 档**对抗镜复核；③复核不过或无从复核则停并上抛），不批量问人，仲裁记录同样落 `impl-reports/planning-decisions.md`。

**出票时 SHALL 评估并行安全性**〔spec-review-amendment〕：对 `Blocked-by` 声明使得 `next_ready` 可能同时返回的一组 ticket（即它们的 `Blocked-by` 集合是 `done` 集的子集，会同时出现在 ready 列表中），出票方 SHALL 确认——① 它们的行为边界不重叠（不改同一模块的同一接口）；② 一个的产出不是另一个的输入；③ 有疑问时 SHALL 保守声明依赖（宁可串行不可误并行）；④ 若产出多张 `Blocked-by` 覆盖全部其余票号的 ticket，SHALL 让后者追加声明对前者的 `Blocked-by`，确保收尾节点唯一（`next_ready` 只返回一个收尾候选）。该约束为指令层语义约束（出票方的模型判断）；兜底为 worktree 隔离下 `git merge --no-ff` 的原生冲突检测（真正的 fail-loud）——即使出票判断失误（两票改同一文件），各自 commit 到独立 worktree 分支，merge 回主分支时 git 正常冲突检测会 fail-loud（见「执行模式宿主条件化受限并行工作 frontier 并以文件交接」需求）。

#### Scenario: 并行安全的 ticket 不声明互相 Blocked-by

- **WHEN** 某 change 有 3 张功能 ticket，T2 改脚本 A，T3 改脚本 B，T4 改 SKILL.md 的不同段，三者均只 Blocked-by T1
- **THEN** 出票方判定三者行为边界不重叠、产出不互为输入，保留 `Blocked-by: 1` 不加互相依赖

#### Scenario: 有数据流依赖时保守声明串行

- **WHEN** T2 新增一个函数，T3 的验收标准调用该函数
- **THEN** 出票方 SHALL 让 T3 声明 `Blocked-by: 1,2`，确保 T3 在 T2 完成后才执行

#### Scenario: 出 ticket 后 gate 先行校验再执行

- **WHEN** 出 ticket 模式完成落盘并返回
- **THEN** ship 重跑 ship_gate，plan 文件经 fence/标题/重号**及收尾票**四道校验后才发出 CONTINUE_IMPL，执行模式才被派发

#### Scenario: 宽重构走 expand–contract

- **WHEN** 某 tasks.md 条目是重命名共享符号类宽重构
- **THEN** 出 ticket 为 expand ticket → 迁移批次 ticket（各自 Blocked-by expand）→ contract ticket（Blocked-by 全部迁移批次），不产出「一 ticket 打穿全仓」的伪垂直切片

#### Scenario: 出票模式恒含实现验证收尾票

- **WHEN** 出 ticket 模式产出 N 张功能垂直切片（3≤N≤6）
- **THEN** `tickets.md` 额外含一张「实现验证」收尾 ticket，`Blocked-by` 全部 N 张功能票号，`R-ID: all`，不计入 3–6 预算计数

#### Scenario: 缺少收尾票的 plan 被 gate 拒绝

- **WHEN** `tickets.md` 不含收尾票，或其 `Blocked-by` 漏了某张功能票号
- **THEN** ship_gate 判非 0 并指出缺失项

#### Scenario: 仓内无 e2e 层时记未覆盖而非罢工

- **WHEN** 收尾票 implementer 判定本仓确无 e2e 层
- **THEN** 证据行记 `e2e | — | 未覆盖 | <判定依据>`，该票仍可通过双轴审，MUST NOT 因缺层停机

#### Scenario: 无切片建议且无缺席理由时复核必触发〔spec-review-amendment Q1-A〕

- **WHEN** design.md 既无「切片建议」节、也无成立的缺席理由，出票方自主决定切分方案（无论是否存在多个候选）
- **THEN** 出票方 SHALL 派一个 strong 档对抗镜复核该切分方案，不问用户；仲裁结论按行格式落 `impl-reports/planning-decisions.md`

#### Scenario: 合规缺席（有理由）的小修不触发必复核〔spec-review-amendment Q1-A〕

- **WHEN** design.md 无「切片建议」节但写明了成立的缺席理由（如「单票交付，无切分必要」），出票产出与理由一致（1 张功能票）
- **THEN** 不触发条件① 复核；若实际出票 >1 张功能票（与缺席理由矛盾），出票方 SHALL 视同条件③ 派 strong 档对抗镜复核，仲裁结论落 `planning-decisions.md`

#### Scenario: 粒度争议派 strong 档复核并落审计

- **WHEN** 出票过程中出现粒度争议（≥2 个合理切分候选）且无客观判据可判
- **THEN** 派一个 strong 档对抗镜复核推荐的切分方案，不问用户；仲裁结论按行格式落 `impl-reports/planning-decisions.md`（既有触发路径，与必触发三条件并存）

#### Scenario: 有切片建议且未偏离时默认采纳、不派复核

- **WHEN** design.md 含「切片建议」节，出票产出的票划分与阻塞边与草图一致（无实质偏离），且无粒度争议
- **THEN** 出票方按草图物化 tickets.md，`planning-decisions.md` 无偏离行，无须派 T10-choice 复核（草图已经阶段二评审与人门）

#### Scenario: 偏离草图须记录并触发复核

- **WHEN** design.md 切片建议为 4 张票，出票方判断其中两张应合并为一张
- **THEN** 出票方 SHALL 在 `planning-decisions.md` 记一行「切片偏离: 合并票 X/Y | <理由(三镜+主次)>」，并派 strong 档对抗镜复核偏离后的方案；MUST NOT 静默按己意出票

#### Scenario: 草图与 design 正文矛盾时触发复核

- **WHEN** 评审 amendments 废弃了 design 正文中的某机制，而切片建议节仍含一张以该机制为交付物的票
- **THEN** 出票方 SHALL 判「草图与 design 正文矛盾」，派 strong 档对抗镜复核修正后的切分方案，仲裁结论落 `planning-decisions.md`；MUST NOT 照旧草图出票

#### Scenario: 必触发复核证伪时停并上抛〔spec-review-amendment〕

- **WHEN** 任一必触发情形派出的 strong 档对抗镜将切分方案判「证伪」，且无可自动修正的替代方案
- **THEN** 出票流程停并上抛，MUST NOT 以被证伪的切分方案继续出票；仲裁结论仍按行格式落 `impl-reports/planning-decisions.md`

#### Scenario: 一致性自扫发现矛盾派 strong 档复核

- **WHEN** 全 ticket 语义一致性自扫发现某票假设的接口形状被另一票明确废弃，且无客观判据可自动选
- **THEN** 派一个 strong 档对抗镜复核该矛盾的处置方案，复核不过或无从复核则停并上抛，不批量问人，仲裁结论落 `impl-reports/planning-decisions.md`

#### Scenario: 中间 fix 轮不跑集成与 e2e

- **WHEN** 收尾票的聚合套件在某轮失败，implementer 修复后进入下一轮
- **THEN** 该轮只跑 unit 全层加上轮失败的具体用例（⊂ unit 层），集成与 e2e 不跑；该轮报告中集成/e2e 层 SHALL NOT 出现「通过」证据行

#### Scenario: 收口轮跑全量且所有通过行锚同一 SHA

- **WHEN** 双轴审判定该票通过、准备打完成标签
- **THEN** 各层取 `full` 命令跑一次全量，报告中所有判「通过」的行锚同一个最终 SHA；若某层的通过行锚在更早的 SHA 上，该报告 SHALL 判不合格

#### Scenario: 未配 quick 档的消费仓行为不变

- **WHEN** 某消费仓的 `test-suites.unit` 仍是字符串形状（未分档）
- **THEN** quick 与 full 两档均取该字符串命令，行为等同于扩展前，MUST NOT 因缺 quick 档报错或罢工

#### Scenario: 验收标准要求解析无界语法面时被出票闸门拦下

- **WHEN** 某待出 ticket 的验收标准写作「静态门须能识别私有 Tab/focus trap 指纹」或「窄范围 patch 逻辑只动 YAML 的某单键值」
- **THEN** 出票方 SHALL 判该语法面无界并改写该验收标准——改为让该工具自己回答（真跑一遍 / 调权威解析器），或降级为不作判定依据的展示；MUST NOT 原样出票

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
且池文件 frontmatter 的 `source_change` 字段（`issues_v2.py` 实际字段名）MUST 等于当前
change 名（防误抄/复用他 change 既有 id 假绿 `[spec-review-amendment]`）；不满足 ⇒ 同
「该步进行中，重跑」处置。defer 台账只承载**本轮新入池项**——finding 已被既有票（前序
change 入池、`source_change` 为旧 change）覆盖时，引用写在裁决说明、MUST NOT 进 defer
台账（否则 gate 必拒、而重复 add 造重复票 `[spec-review-amendment]`）。
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

- **WHEN** 报告 defer 台账行携带的 id 对应池文件存在，但其 frontmatter `source_change`
  字段为另一 change 名（误抄/复用既有票号）
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

### Requirement: 执行期票外发现上报编排层按拆分标准判 fold/defer〔harden-ticket-slicing〕

执行模式中 implementer 撞到**与本 change 相关但在本票验收范围之外**的 bug/改进点时，SHALL 上报编排层处置，**MUST NOT 自行扩 scope 顺手修**（绕过双轴审的 scope 契约，票的验收边界失效）。**上报通道 SHALL 比照 `DONE_WITH_CONCERNS` 的既有形状**〔impl-review-fix〕：implementer SHALL 将发现全量写入该票 report file 的固定小节 `## 票外发现`，并在 dispatch 返回值的一行摘要中追加标注 `[has-off-ticket-finding]`；编排层看到该标注时 MUST Read 该小节全文以获取 AND 门判据，MUST NOT 仅凭一行摘要判定。编排层 SHALL 按 change 拆分标准（单一源 `openspec/workflow/reference/change-decomposition-standard.md`，经 resolver 解析；判定入口 = BASE-18 防吸积 AND 门：同 capability ∧ 高耦合 ∧ 低增量）判定——三者皆满足 ⇒ **fold**（该票尚未进入双轴审 ⇒ 可并入当前票验收标准；已在双轴审途中或已完成 ⇒ 追加进后续 ready 票、或新增一张 Blocked-by 当前票的票——MUST NOT 中途改动已在双轴审途中的票的验收标准〔spec-review-amendment〕；均走正常 implementer + 双轴审，且**执行期新增的票 SHALL 补齐出票模式对 ticket 的强制字段与闸门**〔impl-review-fix〕——`Blocked-by` / `R-ID` / 验收复选框 / 验收标准的语法面有界性闸门，或在该票文本中显式列出豁免哪些、为何）；任一不满足 ⇒ **defer**（recorder 落 issues 池，显式带 `change` 字段）。判定与去向 SHALL 记一行入该票 impl-report。

#### Scenario: implementer 撞到相关票外 bug 上报而非顺手修

- **WHEN** implementer 实现某票时发现相邻函数一个与本 change 一致性相关的 bug，修复约 5 行
- **THEN** implementer 将发现写入该票 report file 的 `## 票外发现` 小节，并在返回摘要标 `[has-off-ticket-finding]`，MUST NOT 直接改动票外代码；编排层读该小节全文按 AND 门判定（同 capability、高耦合、低增量皆满足）后 fold 进当前 change 的后续票

#### Scenario: 不满足 AND 门的发现 defer 进 issues 池

- **WHEN** implementer 发现一个真独立、需自身设计审查的改进点
- **THEN** 编排层判 defer，经 recorder 落 todolist（显式带 change 字段），该票不因此扩 scope
