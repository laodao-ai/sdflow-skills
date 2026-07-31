# impl-orchestration Specification

## Purpose
TBD - created by archiving change matt-workflow-integration. Update Purpose after archive.
## Requirements
### Requirement: 管线路由为手动确定值，零模型自动判断

实现管线选择 SHALL 仅由手改/落盘的确定值决定，路由三跳为：① `openspec/config.yaml` 可选键 `impl-pipeline`（人手编辑，仅在新出 ticket 时刻读一次）；② plan 文件头 frontmatter 管线 marker（出 ticket 落盘后只读，锁定在途 change 归属）；③ 键缺失或值不识别 → 一律 superpowers 管线。MUST NOT 引入任何模型自由裁量的管线判断；改 config MUST NOT 影响任何已出 ticket 在途 change 的续跑。ship_gate MUST NOT 读取 config（保零依赖不变量）。键与 marker 的读取 SHALL 落确定性脚本（stdlib-only enum reader / route helper，不触 gate）〔spec-review-amendment F4〕；ship 派发 sdflow-implement 时 SHALL 以显式字面 args 传递模式与 done_tasks（SKILL.md 与 ship 链序两处共享同一契约串）〔F4〕。marker **存在但非法/重复/损坏** SHALL 停（UNKNOWN 语义）并留痕，MUST NOT 静默回退旧管线（防两管线混跑）——静默回退仅适用「键/marker 缺席」的缺省态〔F4〕。路由结果 SHALL 产出一行 PIPELINE_RECEIPT（读到的键值/选定管线/marker/plan sha）进当轮输出与判赢材料〔F3a〕。

#### Scenario: 缺省与非法值 fail 向旧管线

- **WHEN** config 无 `impl-pipeline` 键、键值拼错、或键值为 `superpowers`
- **THEN** RUN_PLAN 路由到 superpowers:writing-plans，行为与本变更前完全一致；键**存在而值不识别**时另回显一行提示（区别于缺省缺席）〔spec-review-amendment F12〕

#### Scenario: 在途 change 不受 config 切换影响

- **WHEN** 某 change 已以 tickets 管线出 ticket（marker 在盘面），随后 config 键被改回 superpowers
- **THEN** 该 change 的 CONTINUE_IMPL 续跑仍路由 sdflow-implement 执行模式（只认 marker），新出 ticket 的 change 才走新 config 值

#### Scenario: 对在途强制换管线属显式越权

- **WHEN** 操作者人工修改在途 change 的 plan 文件 marker
- **THEN** 视为显式越权通道（git 留痕、产物一致性自担）；skill MUST NOT 主动建议此操作

### Requirement: 出 ticket 模式产出 tracer-bullet ticket 并落盘即返回

sdflow-implement 出 ticket 模式 SHALL 从 design.md 与 tasks.md 产出 3-6 张 tracer-bullet 垂直切片 ticket（计数仅约束垂直切片；expand–contract 例外序列的迁移批次、以及下述「实现验证」收尾 ticket 均不占该预算〔spec-review-amendment E5〕）：每 ticket 为打穿全层、可独立验证的行为级描述，MUST NOT 预写实现代码或具体文件路径；每 ticket SHALL 声明显式 Blocked-by 阻塞边与 R-ID 需求标注；宽重构（单一机械改动 blast radius 扫全仓）SHALL 走 expand–contract 序列例外而非强行垂直切片。ticket 文件头部 SHALL 逐字携带 design 领域约束为 Global Constraints 节。

**验收标准的语法面有界性闸门 SHALL 在出票时施加**〔curb-rework-loop-cost〕：某条验收标准若要求对某种语法面**做机械判定**，出票方 SHALL 先判该语法面能否穷举——**有界**（如 CommonMark fence 变体、自有格式的机器锚行）⇒ 可写为机械门；**无界**（通用编程语言源码、YAML、make、shell）⇒ **MUST NOT 写成机械门**，SHALL 改为「让该工具自己回答」（真跑一遍看行为 / 调用该格式的权威解析器），或降级为 best-effort 展示且**不作判定依据**。该判据 SHALL 覆盖伪装形态——不仅匹配「扫描 / 识别 / 拒绝某形态 / 指纹」这类显式措辞，**还 SHALL 匹配「在某格式文件中定位 / 插入 / 修改某处」**（「只动一个键值」听起来不像解析，但「找到那个键」本身就要解析）。**本闸门是指令层约束，MUST NOT 被表述为机械保证。**

**计划文件名 SHALL 按轨分列**〔spec-review-amendment · adr/0033〕：tickets 轨落盘 `tickets.md`，superpowers 轨保持 `superpowers-plan.md`。**在途 plan MUST NOT 被重命名**——完成判据窗口起点由 `git log --diff-filter=A -- <plan 路径>` 取得，该判据**不跟随重命名**，改名会把窗口起点推到改名 commit，使改名前的全部 checkpoint 标签落到窗口外、已完成 ticket 被判未完成并可能重派。∴ 在途 plan SHALL 保留原文件名直至该 change 归档。gate 与 route helper SHALL 经**同一份共享 resolver** 定位计划文件（MUST NOT 各自手抄文件名列表）：按序探测两个名字；**两者同时存在 SHALL fail-closed 判 UNKNOWN**（不猜哪个是真的）；均不存在则判 RUN_PLAN。**文件名 MUST NOT 参与轨道路由判定**——路由权威仍是 config 键 + plan frontmatter marker，文件名只用于定位，避免新增一个会与 marker 冲突的冗余信号。

出 ticket SHALL 落盘即返回编排层（ship），MUST NOT 在同一调用内直通执行——保 ship_gate 在出 ticket 后/执行前的校验插入点。原版 to-tickets 的 quiz-the-user 人类步 SHALL 删除（阶段三无人类门），粒度争议按 `T10-choice` 三级决策协议处理（①有客观判据自动选并**按三镜 + 主次**记理由；②无客观判据派 **strong 档**对抗镜复核推荐切分方案，通过方自动选；③复核不过或无从复核 defer）〔spec-review-amendment M3：首版此处漏了「按三镜 + 主次」限定词〕。**出票模式的仲裁记录 SHALL 有确定性审计落点**：写入 `impl-reports/planning-decisions.md`（change 目录内、git-tracked，由出票落盘的同一次 checkpoint 一并提交），行格式 = 「`T10-choice` 复核: <方案> | 对抗镜结论 <通过/证伪> | <理由(三镜+主次)>」——出票模式无 code-review 报告产物，此前该仲裁结果**无处可落**〔spec-review-amendment M15〕。

**出 ticket 模式 SHALL 在全部功能垂直切片之后追加一张强制的「实现验证」收尾 ticket**，`Blocked-by` 声明为全部功能 ticket 号，`R-ID` 为 `all`（语义 = 覆盖本 change 全部需求的聚合验证，Spec 轴据此核验而非逐条溯源）〔spec-review-amendment M6〕，其验收标准 SHALL 为「按下述发现契约运行本 change 的聚合测试套件（单元+集成+e2e）并全部通过」。

**聚合套件发现契约（MUST NOT 解析构建文件）**〔spec-review-amendment Q6〕：① 命令来源优先级 = `openspec/config.yaml` 的 `test-suites.{unit,integration,e2e}` 显式配置 → 缺失则由该票 implementer 依仓内既有约定判定并在票报告写明命令原文与判定依据；② 「某命令能不能跑」SHALL 由**真跑一遍看退出码**回答，MUST NOT 靠解析 Makefile/package.json 预判 target 是否存在；③ 仓内确无某层时 SHALL 记「未覆盖（本仓无此层）」并附依据，**MUST NOT fail-closed 罢工**——`sdflow-implement` 的承诺是「不管什么项目都能跑完实现管线」，罢工分支直接背叛该承诺；④ 证据 SHALL 落确定性 schema，每层一行 `<层> | <命令原文> | <退出码> | <测试时 git rev-parse HEAD>`，未覆盖层写 `<层> | — | 未覆盖 | <依据>`；⑤ 退出码非 0 SHALL 分四类处置：本 change 引入的回归 → 进 fix 循环；仓内既有红测（以 base SHA 复跑确认）→ 记录放行；flaky（同命令复跑一次即绿）→ 记录放行；环境故障 → halt envelope 停并上抛。

**`test-suites` SHALL 支持成本分档**〔curb-rework-loop-cost〕：每层的值为**字符串**时 quick 与 full 两档同命令（今日形状，继续有效）；为**映射**时读 `quick` / `full` 两键——缺 `quick` 视为该层无 quick 档，缺 `full` 视为未分档（quick=full 同命令）。旧形状是新形状的合法子集，**未配置的消费仓行为 SHALL 等同于扩展前**，MUST NOT 要求下游同步改配置。`test-suites` 的具体命令因项目而异，**SHALL 由 `sdflow-devenv` 运行时调研项目测试基础设施后推荐写入**（已有配置时保留不覆盖），本 change 只定义 schema 与消费语义。

**中间 fix 轮与收口轮的测试范围 SHALL 分离，且范围 SHALL 由确定信息界定**〔curb-rework-loop-cost · adr/0035〕：

- **中间 fix 轮** SHALL 只跑 **unit 全层**（整层跑、不做用例筛选；若该层配了 `quick` 则取 `quick`，**无 `quick` 则取 `full`——unit 层 MUST NOT 因缺 quick 档被跳过**）**加上轮失败的具体用例（⊂ unit 层）**；集成与 e2e SHALL 整体推迟到收口。中间轮的结果**仅供诊断，SHALL NOT 作为最终报告的通过证据**。
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

### Requirement: ticket 文件兼容 ship_gate 既有完成判据契约

ticket 文件 SHALL 写入 change 目录的 `superpowers-plan.md`（试验期外衣文件名），每 ticket 以 `### Task N: <ticket 名>` 为标题、ticket 内含验收标准复选框；出 ticket 收尾 SHALL 显式 checkpoint（plan 单独提交建立完成窗口锚）〔grill-amendment〕。完成信号 SHALL **后置双写**〔spec-review-amendment F1；设计门 2026-07-10 拍板定稿（方案甲）〕：implementer 实现期提交 MUST NOT 带 `task<N>-` 完成标签；该 ticket 双轴审 + 修复环通过后，由执行模式补打 `checkpoint(<change>:task<N>-<slug>)` 完成标签并勾全验收复选框——**审过才算 done**；resume 发现「实现提交在、完成标签缺」SHALL 进入续审而非重实现。plan 首次提交后结构 SHALL 不可变：MUST NOT 重号/重排/删除/复用 Task 号，重规划只可追加新号〔F1〕。plan 文件 frontmatter SHALL 含且仅含 `impl-pipeline` 单键（无注释/示例/第二块——marker 块内杂行会被 gate 计为幻影任务）〔F5〕。ship_gate.py SHALL 零改动。

#### Scenario: gate 以既有双通道判定 ticket 完成

- **WHEN** 某 ticket 双轴审通过、执行模式按契约补打完成标签并勾框
- **THEN** 既有 ship_gate（未改动）经 checkpoint 标签 ∪ 复选框双通道判定该 Task 号 done，CONTINUE_IMPL 的 done_tasks 集合正确携带；审前中断 resume 时该 ticket 不在 done_tasks 中、进入续审〔spec-review-amendment F1〕

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

### Requirement: 试点回退与熔断哨兵

新管线 SHALL 以试点方式启用（逐仓/逐 change 翻 config 键），缺省路径（不翻键）SHALL 与本变更前行为一致。试点期 SHALL 以冷层 code-review Critical/严重 findings 相对同类型基线为熔断哨兵：恶化即停试点（config 回缺省），在途 tickets change 按 marker 跑完或人工越权处置。每个试点 change SHIPPED 后、选定下一试点前 SHALL 再生 retro 报告核对哨兵〔spec-review-amendment F3a〕；试点样本计入判赢集前 SHALL 核对 PIPELINE_RECEIPT/marker 与 config 意图一致（误路由 change 剔除样本）〔F3a〕；选样拒绝条件：跨模块宽重构、接口高度不确定、纯文档/琐碎类 MUST NOT 入样〔F3a〕。

#### Scenario: 哨兵触发回退

- **WHEN** 某试点 change 的冷层报告出现应被每 ticket 双轴审拦住的严重缺陷且相对基线明显上升
- **THEN** 停止新试点（config 键回缺省），恶化实证记入判赢材料，ticket 粒度/审深度回炉再议

### Requirement: implementer dispatch 携带信号权威归属声明

`sdflow-implement` 派发 implementer / fix 子代理时，dispatch prompt SHALL 携带一份**信号权威表**，正面声明「完成信号写哪里」与「设计工件不可碰」——子代理跑在 fresh context，看不见 SKILL.md 与 CLAUDE.md，未声明即等同未约束。

声明 SHALL 为正面陈述（列出权威归属），MUST NOT 仅写成禁令清单——禁令只挡列举到的那一种越界，权威表挡的是整个范畴。

本要求的适用面 SHALL 限于本仓自有的 `sdflow-implement`；第三方实现 skill（superpowers `subagent-driven-development`、matt `implement`）不受本要求约束，故本要求 MUST NOT 被当作设计门失鲜问题的唯一防线（机械防线在 `spec-workflow` 的设计门新鲜度内容判据）。

#### Scenario: dispatch prompt 含信号权威表

- **WHEN** `sdflow-implement` 执行模式派发 implementer 或 fix 子代理
- **THEN** prompt MUST 含信号权威表，至少覆盖两行归属：完成信号 = `superpowers-plan.md` 验收复选框 + `checkpoint(<change>:task<N>-<slug>)` 标签；设计工件 = `proposal.md` / `design.md` / `tasks.md` / `specs/`，实现期不修改
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

双轴审的 reviewer 输入经 review-package 式文件传递（见「执行模式串行工作 frontier 并以文件交接」需求）。**fix 轮次的 review package SHALL 只含该轮的修复 diff**（`上轮已审 SHA..HEAD`），MUST NOT 重新打包自 ticket 起点以来的累积全量 diff。

理由：fix 轮的评审命题是「这次修复对不对」，不是「重新全审这张票」；累积打包会让同一段 diff 被反复读入 reviewer context（实测单包最大达 1,356KB）。首轮 review package 的范围不变。

#### Scenario: 第二轮 fix 的 review package 不含首轮已审内容

- **WHEN** 某 ticket 首轮双轴审报出 Critical，fix 子代理修复后进入第 2 轮 re-review
- **THEN** 该轮 review package 的 diff 范围 SHALL 为「首轮已审 SHA..HEAD」，MUST NOT 包含首轮已经审过且未再改动的 hunk

### Requirement: 往既有测试补断言或修改既有断言同样适用 red-before-green

implementer 的 TDD 契约为 red-before-green（见「执行模式串行工作 frontier 并以文件交接」需求）。该纪律 SHALL 同样适用于**往既有测试文件补一条断言或修改既有断言的期望值/判定逻辑**的场景，而不限于新写测试：**补一条断言或修改既有断言时 SHALL 先确认它会红**——当场破坏被测点、确认该断言失败，再恢复。

理由：恒真断言（needle 被别的门满足，或压根没有用例走到该行）在写入时无成本可验，在事后 review 时才被发现，届时已需一整轮返工。修改期望值同理——改后仍恒真的断言同样是假绿。该自检成本为一次聚焦运行。

#### Scenario: 补断言或改断言未验红被 Standards 轴判为缺口

- **WHEN** implementer 往既有测试补了一条断言或修改了既有断言的期望值，报告中未给出「该断言曾验红」的证据
- **THEN** Standards 轴 SHALL 判该项为缺口并要求补验；MUST NOT 因「测试整体是绿的」而放过

#### Scenario: 收尾票豁免不受本需求扩展影响

- **WHEN** 「实现验证」收尾票按既有契约豁免 red-before-green
- **THEN** 该豁免继续有效——收尾票不写产品代码、验收物是证据不是 diff，本需求的扩展 MUST NOT 被解读为取消该豁免

