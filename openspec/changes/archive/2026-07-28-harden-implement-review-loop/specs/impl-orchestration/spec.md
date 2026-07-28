## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: 执行模式串行工作 frontier 并以文件交接

执行模式 SHALL 按 Blocked-by 拓扑串行工作 frontier（首版 MUST NOT 并行派发 implementer）；每 ticket 派发 fresh implementer 子代理，契约为 TDD at pre-agreed seams、定期 typecheck、**单元测试 + 本 ticket 声明的 e2e 场景 + 本 ticket `Blocked-by` 链上模块的集成测试**（MUST NOT 跑**与本票无依赖关系**的集成/e2e 套件——聚合回归由「实现验证」收尾 ticket 承担，见「出 ticket 模式产出 tracer-bullet ticket 并落盘即返回」需求）、完成信号双写；「本 ticket 声明的 e2e 场景」SHALL 由 ticket 验收标准中标注为 e2e 的条目界定，未标注即该票无 e2e 场景〔spec-review-amendment M7〕；implementer 状态词表为 DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED——NEEDS_CONTEXT SHALL 由编排层从盘面（design.md/specs/ticket 文本）自答，答不出走 defer 或停，MUST NOT 编造；BLOCKED 无法消解 SHALL 停并上抛。子代理产物 SHALL 以文件交接：implementer 全量报告写 report file（按 ticket 名命名）只返回状态摘要；reviewer 输入 diff 经 review-package 式文件传递，MUST NOT 把大产物粘贴进 dispatch prompt。审出的 cannot-verify-from-diff 项（需求活在未改动代码或跨 ticket）SHALL 由编排层亲自消解，且 SHALL 设预算上界：需触碰超过 3 个文件、或从盘面（design/specs/ticket 文本）不可直接解答时，MUST 按「确认缺口退回 implementer」处理〔spec-review-amendment F7〕。frontier 的 next-ready 判定 SHALL 由确定性 helper 计算（解析 Blocked-by + gate done_tasks 拓扑排序，stdlib-only）〔F8〕。一切停机（BLOCKED/依赖缺失/gate 拒绝）SHALL 以统一 halt envelope 呈现：错误码、ticket 号与名、已核证据、已写盘副作用、精确恢复步骤〔F7〕；BLOCKED 的 blocker 记录 SHALL 落盘 report file（change 目录内、git-tracked，防 compaction 蒸发）〔F7〕。DONE_WITH_CONCERNS SHALL 与 DONE 同路径进双轴审，implementer 所述 concerns 逐字附给两轴〔F7〕。

#### Scenario: frontier 串行推进

- **WHEN** ticket 2、ticket 3 均 Blocked-by ticket 1 且 ticket 1 完成
- **THEN** 编排层按 ticket 号序先派 ticket 2，完成后再派 ticket 3，同一时刻至多一个 implementer 在工作

#### Scenario: NEEDS_CONTEXT 从盘面自答

- **WHEN** implementer 返回 NEEDS_CONTEXT 询问某接口约定
- **THEN** 编排层从 design.md/ticket 文本中定位答案回填再派发；盘面无答案时按 T10 处理（defer 或停），不编造

> 〔spec-review-amendment H6〕本 Scenario 的 "T10" 字样 SHALL 原样保留——它是仅引用尾部处置（defer 或停）、未提及仲裁步的轻量引用，design 的 scope-check 表把它列在【不动】。首版 delta 曾把它改写成「按 defer 或停处理」，属 MODIFIED 整段替换时的静默删除。

#### Scenario: 功能 ticket 只测本票范围

- **WHEN** 某功能 ticket 的 implementer 即将返回 DONE
- **THEN** 已运行单元测试 + 该 ticket 声明的 e2e 场景（若有）+ 本票 `Blocked-by` 链上模块的集成测试并全部通过，MUST NOT 运行与本票无依赖关系的集成/e2e 套件

### Requirement: 每 ticket 双轴审加修复环，领域清单注入 Standards 轴

每 ticket 实现完成后 SHALL 并行派发两个评审子代理：Standards 轴（仓内文档化标准 + Fowler smell 基线，且 SHALL 把 code-checklists/domains/<命中栈>（经 resolve-workflow.sh 解析）作为标准源注入 = 注入点 B）与 Spec 轴（对照 ticket 文本验收标准与 R-ID 溯源需求）；两轴均按 mid 档派发（见「sdflow-implement 档位解析与声明」需求）；两轴输出各 SHALL 封顶（<400 词量级）。Critical/Important 发现 SHALL 派 fix 子代理（mid 档）修复并 re-review 直至通过；Minor 发现 SHALL defer 进 todolist（显式带 change 字段）。code-checklists/domains 经 resolve-workflow.sh 解析失败、规则根不可达或命中栈无清单时，Standards 轴 MUST NOT 宣称通过——SHALL 显式停或在报告记「领域清单未覆盖」并留降级原因〔spec-review-amendment F13〕。

**熔断规则 `review-loop-breaker`（本需求独立定义，MUST NOT 引用其它能力的 "T10" 标签——本场景语义为「同一发现反复未消解」，与阶段三 `T10-choice`「≥2 方案自动选」触发条件不同）**：

- **触发**：同一发现连续 2 轮 re-review 仍未消解 SHALL 停止循环。
- **身份键 SHALL 跨轮稳定**：判定「是否同一发现」SHALL 用「同文件 + 规范化问题指纹」，**行号只作定位、MUST NOT 作为身份键的组成部分**〔spec-review-amendment H3〕——修复几乎必然移动行号，用行号当身份会让同一未解决问题被认成新发现、轮次计数清零，`MUST NOT 无限循环` 无从兑现。
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

#### Scenario: 复核判成立后必须走向终态

- **WHEN** strong 档复核判定该发现确实成立
- **THEN** 编排层 SHALL 二选一：可修则派 strong 档 fixer 修复并仅复验一次；不可修则 defer 进 buglist 并停上抛。MUST NOT 在「确认成立」后回到原 re-review 循环

### Requirement: 出 ticket 模式产出 tracer-bullet ticket 并落盘即返回

sdflow-implement 出 ticket 模式 SHALL 从 design.md 与 tasks.md 产出 3-6 张 tracer-bullet 垂直切片 ticket（计数仅约束垂直切片；expand–contract 例外序列的迁移批次、以及下述「实现验证」收尾 ticket 均不占该预算〔spec-review-amendment E5〕）：每 ticket 为打穿全层、可独立验证的行为级描述，MUST NOT 预写实现代码或具体文件路径；每 ticket SHALL 声明显式 Blocked-by 阻塞边与 R-ID 需求标注；宽重构（单一机械改动 blast radius 扫全仓）SHALL 走 expand–contract 序列例外而非强行垂直切片。ticket 文件头部 SHALL 逐字携带 design 领域约束为 Global Constraints 节。

**计划文件名 SHALL 按轨分列**〔spec-review-amendment · adr/0033〕：tickets 轨落盘 `tickets.md`，superpowers 轨保持 `superpowers-plan.md`。**在途 plan MUST NOT 被重命名**——完成判据窗口起点由 `git log --diff-filter=A -- <plan 路径>` 取得，该判据**不跟随重命名**，改名会把窗口起点推到改名 commit，使改名前的全部 checkpoint 标签落到窗口外、已完成 ticket 被判未完成并可能重派。∴ 在途 plan SHALL 保留原文件名直至该 change 归档。gate 与 route helper SHALL 经**同一份共享 resolver** 定位计划文件（MUST NOT 各自手抄文件名列表）：按序探测两个名字；**两者同时存在 SHALL fail-closed 判 UNKNOWN**（不猜哪个是真的）；均不存在则判 RUN_PLAN。**文件名 MUST NOT 参与轨道路由判定**——路由权威仍是 config 键 + plan frontmatter marker，文件名只用于定位，避免新增一个会与 marker 冲突的冗余信号。

出 ticket SHALL 落盘即返回编排层（ship），MUST NOT 在同一调用内直通执行——保 ship_gate 在出 ticket 后/执行前的校验插入点。原版 to-tickets 的 quiz-the-user 人类步 SHALL 删除（阶段三无人类门），粒度争议按 `T10-choice` 三级决策协议处理（①有客观判据自动选并**按三镜 + 主次**记理由；②无客观判据派 **strong 档**对抗镜复核推荐切分方案，通过方自动选；③复核不过或无从复核 defer）〔spec-review-amendment M3：首版此处漏了「按三镜 + 主次」限定词〕。**出票模式的仲裁记录 SHALL 有确定性审计落点**：写入 `impl-reports/planning-decisions.md`（change 目录内、git-tracked，由出票落盘的同一次 checkpoint 一并提交），行格式 = 「`T10-choice` 复核: <方案> | 对抗镜结论 <通过/证伪> | <理由(三镜+主次)>」——出票模式无 code-review 报告产物，此前该仲裁结果**无处可落**〔spec-review-amendment M15〕。

**出 ticket 模式 SHALL 在全部功能垂直切片之后追加一张强制的「实现验证」收尾 ticket**，`Blocked-by` 声明为全部功能 ticket 号，`R-ID` 为 `all`（语义 = 覆盖本 change 全部需求的聚合验证，Spec 轴据此核验而非逐条溯源）〔spec-review-amendment M6〕，其验收标准 SHALL 为「按下述发现契约运行本 change 的聚合测试套件（单元+集成+e2e）并全部通过」。

**聚合套件发现契约（MUST NOT 解析构建文件）**〔spec-review-amendment Q6〕：① 命令来源优先级 = `openspec/config.yaml` 的 `test-suites.{unit,integration,e2e}` 显式配置 → 缺失则由该票 implementer 依仓内既有约定判定并在票报告写明命令原文与判定依据；② 「某命令能不能跑」SHALL 由**真跑一遍看退出码**回答，MUST NOT 靠解析 Makefile/package.json 预判 target 是否存在；③ 仓内确无某层时 SHALL 记「未覆盖（本仓无此层）」并附依据，**MUST NOT fail-closed 罢工**——`sdflow-implement` 的承诺是「不管什么项目都能跑完实现管线」，罢工分支直接背叛该承诺；④ 证据 SHALL 落确定性 schema，每层一行 `<层> | <命令原文> | <退出码> | <测试时 git rev-parse HEAD>`，未覆盖层写 `<层> | — | 未覆盖 | <依据>`；⑤ 退出码非 0 SHALL 分四类处置：本 change 引入的回归 → 进 fix 循环；仓内既有红测（以 base SHA 复跑确认）→ 记录放行；flaky（同命令复跑一次即绿）→ 记录放行；环境故障 → halt envelope 停并上抛。

**该票 SHALL 走跟普通 ticket 相同的 implementer + 双轴审 + fix 循环**，但 SHALL 定制三处执行契约〔spec-review-amendment H9〕：① **豁免 red-before-green**（该票不写产品代码，验收物是证据不是 diff）；② **主证据锚 = 该票 impl-report 文件 + 其内的 SHA 三元组，MUST NOT 依赖该票产生 commit**（`checkpoint-commit.sh` 在干净树上直接成功退出、不建 commit，聚合套件一次绿时可能根本无 commit）；③ Standards 轴核验范围 SHALL 为「修复方式未靠**加 skip / 改测试配置 / 删除或弱化断言**蒙混过关」（原措辞只禁删除或弱化断言，挡不住加 skip）。

**`sdflow-done` 的 verify SHALL 引用该票 impl-report 作为「实现期聚合覆盖」需求的证据锚，不扩张 verify 自身职责**；**锚的语义 SHALL 限定为「实现期结束时聚合套件通过」，MUST NOT 表述为「最终代码通过全量回归」**——该票执行于 `sdflow-code-review` 及其自动修复循环之前，code-review 之后的修复由其自身保障机制覆盖，此证据时效缺口是已知且接受的残余风险〔spec-review-amendment Q2〕。**该锚 SHALL 按实现管线条件化**：仅当本 change 走 tickets 轨时要求；superpowers 轨（canonical 缺省）下该需求判「不适用」，**MUST NOT 判 gap**〔spec-review-amendment C2〕。

**收尾票的存在与位置 SHALL 有机械保证**〔spec-review-amendment H12〕：`ship_gate` 的 plan 校验 SHALL 增加一道——**当且仅当计划文件名为 `tickets.md`** 时，该 plan MUST 恰含一张「实现验证」收尾 ticket 且其 `Blocked-by` ⊇ 全部功能 ticket 号，不满足即判非 0；文件名为 `superpowers-plan.md` 时 SHALL 跳过此项并输出一行提示（该名同时覆盖两种情形：superpowers 轨的 plan——本就无收尾票要求；以及改名生效前落盘的在途 tickets 轨 plan——grandfather）。**此处以文件名为判据 SHALL 仅用于区分「新出 plan / 在途或他轨 plan」，MUST NOT 被解读为用文件名做轨道路由**——gate 无需知道当前轨道即可执行本校验，路由权威仍是 config 键 + frontmatter marker。

出票落盘前 SHALL 做一次全 ticket 语义一致性自扫（拓扑之外的语义矛盾，如某票假设的接口形状被另一票废弃）；发现矛盾按 `T10-choice` 三级决策协议处理（①有客观判据自动选并**按三镜 + 主次**记理由；②无客观判据派 **strong 档**对抗镜复核；③复核不过或无从复核则停并上抛），不批量问人，仲裁记录同样落 `impl-reports/planning-decisions.md`。

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
- **THEN** ship_gate 判非 0 并指出缺失项；旧名 `superpowers-plan.md` 的在途 plan 不触发此校验，只输出 grandfather 提示

#### Scenario: 两个计划文件名同时存在则 fail-closed

- **WHEN** change 目录下 `tickets.md` 与 `superpowers-plan.md` 同时存在
- **THEN** gate 判 UNKNOWN 并提示人工删除其一，MUST NOT 猜测哪个是当前有效计划

#### Scenario: 仓内无 e2e 层时记未覆盖而非罢工

- **WHEN** 收尾票 implementer 判定本仓确无 e2e 层
- **THEN** 证据行记 `e2e | — | 未覆盖 | <判定依据>`，该票仍可通过双轴审，MUST NOT 因缺层停机

#### Scenario: superpowers 轨不因缺聚合锚被判 gap

- **WHEN** 某 change 走 canonical 缺省的 superpowers 轨，无「实现验证」收尾票
- **THEN** `sdflow-done` verify 对「实现期聚合覆盖」需求判「不适用（非 tickets 轨）」，MUST NOT 判 gap

#### Scenario: 粒度争议派 strong 档复核并落审计

- **WHEN** design.md 无「切片建议」节，编排层需自主决定切分方案且存在 ≥2 个合理候选
- **THEN** 无客观判据可判时派一个 strong 档对抗镜复核推荐的切分方案，不问用户；仲裁结论按行格式落 `impl-reports/planning-decisions.md`

#### Scenario: 一致性自扫发现矛盾派 strong 档复核

- **WHEN** 全 ticket 语义一致性自扫发现某票假设的接口形状被另一票明确废弃，且无客观判据可自动选
- **THEN** 派一个 strong 档对抗镜复核该矛盾的处置方案，复核不过或无从复核则停并上抛，不批量问人，仲裁结论落 `impl-reports/planning-decisions.md`
