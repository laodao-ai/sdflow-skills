## Why

返工循环（实现期 fix 循环、代码审复审循环）的成本由 **fix 轮次 × 每轮固定开销**决定，而当前机制把最贵的一项——全量测试运行——**直接绑定在 fix 轮次上**（`sdflow-implement/SKILL.md:328-330`「任何产品代码修复之后，MUST 重跑全部已覆盖层」）。全量 e2e/集成套件的单次成本随项目复杂度单调上升，运行次数又随轮次上升，**两个因子同时增长**。

三仓 7 天 16 change 实测（`openspec/roadmaps/workflow-cost-optimization/impl-rework-cost-report.md`）：测试/实现行数比 0.75–2.02x 属正常，**异常的是 impl-report 达实现代码的 2.10–5.45x**；fix 轮 = 0 的 change 只留 9–16 次跑测试痕迹，fix 轮 ≥13 的达 73–136 次，**差 8–15 倍**。

两个实证暴露了机制而非执行的问题：

- **该条款实际未被执行**——`align-sdflow-spec-with-openspec-schema` 跑了 37 个 fix 轮、深至 fix8，却漏掉 `test_runtime_gitignore.py` 的 8 个红测（stub 签名未跟上新增关键字参数）。若任何一轮真跑过全仓 pytest，它必然当场暴露。要求 N 次而实际打折，不如明确要求 1 次并真的验证它。
- **熔断对「同根因换马甲」结构性失效**——同一 R-ID `CR-02/CR-09` 跨 fix5/6/7 三轮换三个 YAML 语法角落，每轮指纹不同 ⇒ `review-loop-breaker`「连续 2 轮同指纹」永不触发。

此外 `sdflow-code-review` **完全没有 fix 循环熔断**，且与 `sdflow-implement` 存在文档分叉（前者 `:181` 称「无 re-review 紧闭环」，后者 `:349,353` 称其有「自动修复循环 / fix 循环」）。

## What Changes

按 TG-19 标注优先级。决策依据与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)，设计原则见 `openspec/adr/0035`。

**P0**

- **① 单一盘面：每轮全量 → 收口一次全量**。中间 fix 轮跑 **unit 全层 + 上轮失败的具体用例**；集成/e2e 整体推到收口。收口跑一次全量，所有判「通过」的行锚同一最终 SHA（**单一盘面语义不变**，被改掉的只是「每轮都重跑」这条对该目的零贡献的强化）。**取消「受影响层」提法**——中间轮范围 MUST 由确定信息界定，MUST NOT 由「哪层受影响」的判断界定。
- **② `test-suites` 成本分档 + 显式配置**。每层可选配 `quick` / `full` 两条命令（只配一条时两档同命令，向后兼容）。具体命令因项目而异，**由 `sdflow-devenv` 运行时调研项目测试基础设施后推荐写入** `config.yaml`。**与 ① 同批落地是硬要求**：① 的收益完全依赖收口那次全量有确定性的命令来源，否则退化回「implementer 每次临时判定范围」。
- **⑥ `sdflow-code-review` 补 fix 循环边界**。自动修复后 MUST 复审**一轮**（只审修复 diff、不重审全量）；仍有 Critical/Important ⇒ 不再自发第三轮，全部 defer 进 buglist 并在报告标注。同时消除与 `sdflow-implement:349,353` 的文档分叉。

**P1**

- **④ `review-loop-breaker` 补与指纹无关的硬上限**。同一文件累计被 Critical/Important 命中 ≥3 轮即熔断，升 strong 档仲裁「**这个门本身该不该存在**」，而非继续仲裁单条 finding 是否成立。
- **⑤ 出票闸门：禁手搓解析器型验收标准**。验收标准若要求对某语法面做机械判定，出票时即判该面能否穷举；无界（通用编程语言 / YAML / make / shell）⇒ MUST NOT 写成机械门，改为「让工具自己回答」或降级为不作判定依据的展示。判据 MUST 覆盖伪装形态——不只匹配「扫描 / 识别 / 拒绝某形态」，还须匹配「**在某格式文件中定位 / 插入 / 修改某处**」。
- **⑨ red-before-green 扩展到「往既有测试补断言」**。现表述只覆盖新写测试；扩展为补一条断言时同样 MUST 先确认它会红（当场破坏被测点验证）。

**P2**

- **③ `review-package.diff` 增量化**。fix 轮只打包 `上轮SHA..HEAD`（实测最大 1,356KB 全量包）。
- **⑫ `sdflow-devenv` 增「格式解析手段对照表」**。落 `references/verification-patterns.md`（现有负面知识库），为 ⑤ 拦下的场景提供手段出处：有标准库 → 用库；有权威第三方库且项目可依赖 → 用库；工具自身即权威 → 让工具跑一遍；都没有 → 收窄子集 + 界外 fail-loud。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `impl-orchestration`: 「每 ticket 双轴审加修复环」的熔断判据增加与指纹无关的硬上限（④）；「出 ticket 模式产出 tracer-bullet ticket」的验收标准约束增加语法面有界性闸门（⑤）；收尾票的聚合套件发现契约增加 quick/full 成本分档与中间轮范围界定（①②）；TDD 契约的 red-before-green 适用面扩展到补断言场景（⑨）；双轴审 review package 改增量（③）。
- `spec-workflow`: 新增一条 Requirement 规定 `sdflow-code-review` 自动修复后的复审边界与硬上限（⑥），并消除与 `impl-orchestration` 侧关于该循环是否存在的表述分叉。

⑫ 为 `sdflow-devenv` 知识库内容扩充，**不改变 `devenv-provisioning` 的任何 Requirement**，故不列入 Modified Capabilities。

## Impact

- **`sdflow-implement/SKILL.md`**：`:270`（出票验收标准约束）、`:313-322`（聚合套件发现契约）、`:328-330`（单一盘面）、`:583`（review package 构造）、`:509`（red-before-green）、`:651-657`（loop-breaker）。
- **`sdflow-code-review/SKILL.md`**：新增复审边界规定；`:181` 对比表措辞对齐。
- **`sdflow-devenv/SKILL.md`**：增加 test-suites 发现与写入能力（运行时调研后推荐 quick/full 分档命令）。
- **`sdflow-devenv/references/verification-patterns.md`**：新增对照表一节。
- **`openspec/config.yaml` 模板与 `sdflow-init`**：`test-suites` 增加 quick/full 两档（向后兼容，缺档位时退化为单命令）。
- **下游消费仓**：SKILL 经 symlink 即时生效；`config.template.yaml` 的 `test-suites` 扩展经 `sdflow-init update` 下发。**不强制下游立即配置**——未配 quick 档时行为等同今天。
- 不命中 TG-01/02/03：本仓技术栈为 Markdown + Python 脚本，不涉及 backend·go / embedded / frontend 领域清单。

## Success Metrics

- **全量运行次数与 fix 轮次解耦**（结构判据，非定量阈值）：收口票的证据 schema 中，判「通过」的行全部锚同一最终 SHA，且中间 fix 轮的报告不含集成/e2e 层的「通过」证据行——只含 unit 与上轮失败用例。
- **`sdflow-code-review` 的复审轮数有上界**：任一 change 的 `impl-reports/` 下 `code-review-*-fix<N>.md` 的 `N` 最大值 ≤ 1；超出即说明硬上限未生效。
- **熔断可触发**：构造「同文件连续 3 轮 Critical/Important 但指纹各异」的场景时，`review-loop-breaker` 触发升档仲裁而非继续循环。
- **文档分叉消除**：`grep` 不再能在 `sdflow-implement` 与 `sdflow-code-review` 中找到关于「code-review 有无 fix 循环」的相反表述。

> **不设定量耗时阈值**（如「native 矩阵总耗时降 X%」）：待优化量本身随项目复杂度单调上升，此刻测出的秒数必然过期，拿它当阈值只会催生一轮很快失效的调参。验收取结构判据。

## Non-Goals

- **不做 ⑪（YAML 界外 fail-loud）**——交付物不同（解析健壮性 vs 循环行为），且改 5 个脚本的全流程承重解析面，blast radius 与本 change 的 prose 契约改动不是一个量级。单开 change。
- **不做「格式解析手段体检工具」**——它 MUST 以 ⑫ 的对照表为单一源，⑫ 未落地前做它必然硬编码一份判据并随后漂移。顺序上必须在 ⑫ 之后。
- **不做 test impact analysis**（按用例级依赖图精选测试）——需覆盖率数据或静态依赖图，三个消费栈（pytest / go test / vitest+playwright）无统一现成工具，成本远超本 change。它解决「精确性」，本 change 解决「可靠性」，是不同问题。
- **不放宽零依赖不变量**——该不变量支撑「symlink 进任意消费仓」的承诺，与本 change 无关，MUST NOT 顺手改动。
- **不重新设计 verify 的执行模型**——`sdflow-done` 的 verify 位置与职责不变。
- **不修改单一盘面的语义**——只改「每轮都重跑」这条实现手段。

## 利益相关方与外部依赖（TG-20）

- **下游消费仓**：本仓是 `sdflow-init` 的 bundle 权威源，②的 `config.template.yaml` 扩展与各 SKILL 改动会经 `sdflow-init update` / symlink 下发。**兼容策略 = 缺档位即退化为今天的单命令行为**，不要求下游同步改配置。
- **`ship_gate.py`**：④⑥ 不新增机械门，但若未来要机械保证复审轮数上界，落点在此。本 change 不做。
- **无外部计费服务依赖**（TG-24 不命中）。

## 假设（TG-22）

- **A1 硬上限阈值（熔断 3 轮 / 复审 1 轮）足够区分正常修复与失控循环**。依据：两个病例均在第 3 轮已可判定；本仓 7 天 16 change 中 fix 轮 ≤2 者占多数。**失效影响**：误伤真·不同问题 ⇒ 提前升 strong 档复核（处置是复核不是放过，代价有界）；或放过第 3 轮才暴露的真问题 ⇒ 退化为今天的状态。
- **A2 「验收标准是否要求对某语法面做机械判定」在出票时判得出**。依据：正例 `archive/2026-07-31-align-sdflow-spec-with-openspec-schema/tasks.md:30` 出票时即写下「MUST NOT 解析 Markdown 结构」，该面未出问题。**样本量为 1**。**失效影响**：⑤ 漏判 ⇒ 退化为今天的状态（不比现状更差），且 ⑫ 的对照表可降低漏判率。⑤ 是指令层约束，MUST NOT 声称机械保证。
- **A3 中间轮跑 unit 全层的成本可接受**。依据：unit 是三层中最便宜的一层。**失效影响**：若某消费仓的 unit 层本身极慢，中间轮反馈变慢——由 ② 的 quick 档兜底（该仓可为 unit 也配 quick）。

## Compliance

N/A —— 本 change 不涉及个人数据、许可证、监管或安全合规要求；改动范围限于本仓工作流编排指令与配置模板。
