## MODIFIED Requirements

### Requirement: 出 ticket 模式产出 tracer-bullet ticket 并落盘即返回

sdflow-implement 出 ticket 模式 SHALL 从 design.md 与 tasks.md 产出 3-6 张 tracer-bullet 垂直切片 ticket（计数仅约束垂直切片；expand–contract 例外序列的迁移批次、以及下述「实现验证」收尾 ticket 均不占该预算〔spec-review-amendment E5〕）：每 ticket 为打穿全层、可独立验证的行为级描述，MUST NOT 预写实现代码或具体文件路径；每 ticket SHALL 声明显式 Blocked-by 阻塞边与 R-ID 需求标注；宽重构（单一机械改动 blast radius 扫全仓）SHALL 走 expand–contract 序列例外而非强行垂直切片。ticket 文件头部 SHALL 逐字携带 design 领域约束为 Global Constraints 节。

**验收标准的语法面有界性闸门 SHALL 在出票时施加**〔curb-rework-loop-cost〕：某条验收标准若要求对某种语法面**做机械判定**，出票方 SHALL 先判该语法面能否穷举——**有界**（如 CommonMark fence 变体、自有格式的机器锚行）⇒ 可写为机械门；**无界**（通用编程语言源码、YAML、make、shell）⇒ **MUST NOT 写成机械门**，SHALL 改为「让该工具自己回答」（真跑一遍看行为 / 调用该格式的权威解析器），或降级为 best-effort 展示且**不作判定依据**。该判据 SHALL 覆盖伪装形态——不仅匹配「扫描 / 识别 / 拒绝某形态 / 指纹」这类显式措辞，**还 SHALL 匹配「在某格式文件中定位 / 插入 / 修改某处」**（「只动一个键值」听起来不像解析，但「找到那个键」本身就要解析）。**本闸门是指令层约束，MUST NOT 被表述为机械保证。**

**计划文件名 SHALL 按轨分列**〔spec-review-amendment · adr/0033〕：tickets 轨落盘 `tickets.md`，superpowers 轨保持 `superpowers-plan.md`。**在途 plan MUST NOT 被重命名**——完成判据窗口起点由 `git log --diff-filter=A -- <plan 路径>` 取得，该判据**不跟随重命名**，改名会把窗口起点推到改名 commit，使改名前的全部 checkpoint 标签落到窗口外、已完成 ticket 被判未完成并可能重派。∴ 在途 plan SHALL 保留原文件名直至该 change 归档。gate 与 route helper SHALL 经**同一份共享 resolver** 定位计划文件（MUST NOT 各自手抄文件名列表）：按序探测两个名字；**两者同时存在 SHALL fail-closed 判 UNKNOWN**（不猜哪个是真的）；均不存在则判 RUN_PLAN。**文件名 MUST NOT 参与轨道路由判定**——路由权威仍是 config 键 + plan frontmatter marker，文件名只用于定位，避免新增一个会与 marker 冲突的冗余信号。

出 ticket SHALL 落盘即返回编排层（ship），MUST NOT 在同一调用内直通执行——保 ship_gate 在出 ticket 后/执行前的校验插入点。原版 to-tickets 的 quiz-the-user 人类步 SHALL 删除（阶段三无人类门），粒度争议按 `T10-choice` 三级决策协议处理（①有客观判据自动选并**按三镜 + 主次**记理由；②无客观判据派 **strong 档**对抗镜复核推荐切分方案，通过方自动选；③复核不过或无从复核 defer）〔spec-review-amendment M3：首版此处漏了「按三镜 + 主次」限定词〕。**出票模式的仲裁记录 SHALL 有确定性审计落点**：写入 `impl-reports/planning-decisions.md`（change 目录内、git-tracked，由出票落盘的同一次 checkpoint 一并提交），行格式 = 「`T10-choice` 复核: <方案> | 对抗镜结论 <通过/证伪> | <理由(三镜+主次)>」——出票模式无 code-review 报告产物，此前该仲裁结果**无处可落**〔spec-review-amendment M15〕。

**出 ticket 模式 SHALL 在全部功能垂直切片之后追加一张强制的「实现验证」收尾 ticket**，`Blocked-by` 声明为全部功能 ticket 号，`R-ID` 为 `all`（语义 = 覆盖本 change 全部需求的聚合验证，Spec 轴据此核验而非逐条溯源）〔spec-review-amendment M6〕，其验收标准 SHALL 为「按下述发现契约运行本 change 的聚合测试套件（单元+集成+e2e）并全部通过」。

**聚合套件发现契约（MUST NOT 解析构建文件）**〔spec-review-amendment Q6〕：① 命令来源优先级 = `openspec/config.yaml` 的 `test-suites.{unit,integration,e2e}` 显式配置 → 缺失则由该票 implementer 依仓内既有约定判定并在票报告写明命令原文与判定依据；② 「某命令能不能跑」SHALL 由**真跑一遍看退出码**回答，MUST NOT 靠解析 Makefile/package.json 预判 target 是否存在；③ 仓内确无某层时 SHALL 记「未覆盖（本仓无此层）」并附依据，**MUST NOT fail-closed 罢工**——`sdflow-implement` 的承诺是「不管什么项目都能跑完实现管线」，罢工分支直接背叛该承诺；④ 证据 SHALL 落确定性 schema，每层一行 `<层> | <命令原文> | <退出码> | <测试时 git rev-parse HEAD>`，未覆盖层写 `<层> | — | 未覆盖 | <依据>`；⑤ 退出码非 0 SHALL 分四类处置：本 change 引入的回归 → 进 fix 循环；仓内既有红测（以 base SHA 复跑确认）→ 记录放行；flaky（同命令复跑一次即绿）→ 记录放行；环境故障 → halt envelope 停并上抛。

**`test-suites` SHALL 支持成本分档**〔curb-rework-loop-cost〕：每层的值为**字符串**时 quick 与 full 两档同命令（今日形状，继续有效）；为**映射**时读 `quick` / `full` 两键——缺 `quick` 视为该层无 quick 档，缺 `full` 回落到 `quick`。旧形状是新形状的合法子集，**未配置的消费仓行为 SHALL 等同于扩展前**，MUST NOT 要求下游同步改配置。

**中间 fix 轮与收口轮的测试范围 SHALL 分离，且范围 SHALL 由确定信息界定**〔curb-rework-loop-cost · adr/0035〕：

- **中间 fix 轮** SHALL 只跑 **unit 全层**（整层跑、不做用例筛选；若该层配了 `quick` 则取 `quick`）**加上轮失败的具体用例**；集成与 e2e SHALL 整体推迟到收口。中间轮的结果**仅供诊断，SHALL NOT 作为最终报告的通过证据**。
- **收口时**（双轴审判通过、打完成标签之前）SHALL 跑一次全量（各层取 `full`），报告中所有判「通过」的行 SHALL 锚**同一个最终 SHA**（= 最后一次修复之后的 `git rev-parse HEAD`）。**单一盘面语义不变**〔原 impl-review-fix FIX-4〕：`unit@A → integration@B` 拼接式的「全部通过」依旧非法。
- 🔴 **范围 MUST NOT 由「哪层受影响」的判断界定**——e2e 按定义端到端、集成测试跨模块，任何改动都可能影响它们，「本次不影响某层」是不可靠判断，把它放进关键路径等于把 fail-open 写进条款。**要求实施者为该判断写明依据不构成缓解**：要求解释一个不可靠判断，只会得到一个有说服力的错误判断。

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

#### Scenario: 中间 fix 轮不跑集成与 e2e

- **WHEN** 收尾票的聚合套件在某轮失败，implementer 修复后进入下一轮
- **THEN** 该轮只跑 unit 全层加上轮失败的具体用例，集成与 e2e 不跑；该轮报告中集成/e2e 层 SHALL NOT 出现「通过」证据行

#### Scenario: 收口轮跑全量且所有通过行锚同一 SHA

- **WHEN** 双轴审判定该票通过、准备打完成标签
- **THEN** 各层取 `full` 命令跑一次全量，报告中所有判「通过」的行锚同一个最终 SHA；若某层的通过行锚在更早的 SHA 上，该报告 SHALL 判不合格

#### Scenario: 未配 quick 档的消费仓行为不变

- **WHEN** 某消费仓的 `test-suites.unit` 仍是字符串形状（未分档）
- **THEN** quick 与 full 两档均取该字符串命令，行为等同于扩展前，MUST NOT 因缺 quick 档报错或罢工

#### Scenario: 验收标准要求解析无界语法面时被出票闸门拦下

- **WHEN** 某待出 ticket 的验收标准写作「静态门须能识别私有 Tab/focus trap 指纹」或「窄范围 patch 逻辑只动 YAML 的某单键值」
- **THEN** 出票方 SHALL 判该语法面无界并改写该验收标准——改为让该工具自己回答（真跑一遍 / 调权威解析器），或降级为不作判定依据的展示；MUST NOT 原样出票

### Requirement: 每 ticket 双轴审加修复环，领域清单注入 Standards 轴

每 ticket 实现完成后 SHALL 并行派发两个评审子代理：Standards 轴（仓内文档化标准 + Fowler smell 基线，且 SHALL 把 code-checklists/domains/<命中栈>（经 resolve-workflow.sh 解析）作为标准源注入 = 注入点 B）与 Spec 轴（对照 ticket 文本验收标准与 R-ID 溯源需求）；两轴均按 mid 档派发（见「sdflow-implement 档位解析与声明」需求）；两轴输出各 SHALL 封顶（<400 词量级）。Critical/Important 发现 SHALL 派 fix 子代理（mid 档）修复并 re-review 直至通过；Minor 发现 SHALL defer 进 todolist（显式带 change 字段）。code-checklists/domains 经 resolve-workflow.sh 解析失败、规则根不可达或命中栈无清单时，Standards 轴 MUST NOT 宣称通过——SHALL 显式停或在报告记「领域清单未覆盖」并留降级原因〔spec-review-amendment F13〕。

**Standards 轴的治理规则 SHALL 含「Tests are code」**〔curb-rework-loop-cost〕：Fowler smell 基线同样适用于**测试文件**，尤其 Duplicated Code（重复的测试形状应合并）与 Speculative Generality（为想象中的需求预写的测试应删除）——测试只增不减会让全量套件的单次成本单调上升，而该轴是流程中唯一的遏制点。**reviewer MUST NOT 直接删测试**，只报 finding 交裁决。

**熔断规则 `review-loop-breaker`（本需求独立定义，MUST NOT 引用其它能力的 "T10" 标签——本场景语义为「同一发现反复未消解」，与阶段三 `T10-choice`「≥2 方案自动选」触发条件不同）**：

- **触发（两条判据并列，命中任一即停）**：
  - **(a) 同指纹判据**：同一发现连续 2 轮 re-review 仍未消解 SHALL 停止循环。
  - **(b) 与指纹无关的硬上限**〔curb-rework-loop-cost · adr/0035〕：**同一文件累计被 Critical/Important 发现命中 ≥3 轮**时，无论各轮的问题指纹是否相同，SHALL 停止循环。此时仲裁的命题 SHALL 是「**这个门 / 这段实现本身该不该存在**」，而非「这一条 finding 是否成立」。
  - 判据 (b) 存在的理由：(a) 的身份键可被「同一根因每轮换一个语法分支」绕过——每轮指纹不同则计数清零，`MUST NOT 无限循环` 无从兑现。**MUST NOT 试图靠「让指纹算法更能识别同一根因」来替代 (b)**：那要求指纹算法判断「什么是同一个根因」，本身即模型判断，且落在无界语法面上。
- **身份键 SHALL 跨轮稳定**：判定「是否同一发现」SHALL 用「同文件 + 规范化问题指纹」，**行号只作定位、MUST NOT 作为身份键的组成部分**〔spec-review-amendment H3〕——修复几乎必然移动行号，用行号当身份会让同一未解决问题被认成新发现、轮次计数清零。
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

## ADDED Requirements

### Requirement: fix 轮的 review package 只含本轮修复 diff

双轴审的 reviewer 输入经 review-package 式文件传递（见「执行模式串行工作 frontier 并以文件交接」需求）。**fix 轮次的 review package SHALL 只含该轮的修复 diff**（`上轮已审 SHA..HEAD`），MUST NOT 重新打包自 ticket 起点以来的累积全量 diff。

理由：fix 轮的评审命题是「这次修复对不对」，不是「重新全审这张票」；累积打包会让同一段 diff 被反复读入 reviewer context（实测单包最大达 1,356KB）。首轮 review package 的范围不变。

#### Scenario: 第二轮 fix 的 review package 不含首轮已审内容

- **WHEN** 某 ticket 首轮双轴审报出 Critical，fix 子代理修复后进入第 2 轮 re-review
- **THEN** 该轮 review package 的 diff 范围 SHALL 为「首轮已审 SHA..HEAD」，MUST NOT 包含首轮已经审过且未再改动的 hunk

### Requirement: 往既有测试补断言同样适用 red-before-green

implementer 的 TDD 契约为 red-before-green（见「执行模式串行工作 frontier 并以文件交接」需求）。该纪律 SHALL 同样适用于**往既有测试文件补一条断言**的场景，而不限于新写测试：**补一条断言时 SHALL 先确认它会红**——当场破坏被测点、确认该断言失败，再恢复。

理由：恒真断言（needle 被别的门满足，或压根没有用例走到该行）在写入时无成本可验，在事后 review 时才被发现，届时已需一整轮返工。该自检成本为一次聚焦运行。

#### Scenario: 补断言未验红被 Standards 轴判为缺口

- **WHEN** implementer 往既有测试补了一条断言，报告中未给出「该断言曾验红」的证据
- **THEN** Standards 轴 SHALL 判该项为缺口并要求补验；MUST NOT 因「测试整体是绿的」而放过

#### Scenario: 收尾票豁免不受本需求扩展影响

- **WHEN** 「实现验证」收尾票按既有契约豁免 red-before-green
- **THEN** 该豁免继续有效——收尾票不写产品代码、验收物是证据不是 diff，本需求的扩展 MUST NOT 被解读为取消该豁免
