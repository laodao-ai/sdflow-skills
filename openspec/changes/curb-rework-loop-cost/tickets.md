---
impl-pipeline: tickets
---

## Global Constraints

- 零依赖不变量与 GC-2 边界锁不在本 change 范围内，MUST NOT 顺手改动。
- `sdflow-implement/SKILL.md:330-332` 的「所有判通过的行锚同一最终 SHA」是既有正确性契约，本设计不触碰。
- MUST NOT 在任何产物中声称 ⑤⑥ 是机械保证——它们是指令层约束。
- 遵守 CLAUDE.md 基准 5（无界语法禁手搓）：本 change 自身不引入任何解析器。
- 遵守 adr/0018 的机械/语义划分。
- 下游消费仓经 symlink（SKILL）与 `sdflow-init update`（bundle/模板）两条独立分发链，二者不同步。扩展设计为向后兼容。
- 本 change 全部交付物是 SKILL.md prose 契约与配置模板，无 Python 脚本、无数据迁移。

### Task 1: 配置分档与单一盘面条款（①②）

**Blocked-by:** none
**R-ID:** IO-1

在 sdflow-implement 和 sdflow-init/sdflow-devenv 中落地 test-suites 成本分档（②）与中间轮/收口轮范围分离（①）。

配置模板侧：sdflow-init 的 config.template.yaml 增加 test-suites 的 quick/full 两档示例与注释，保持字符串形状为合法子集。

消费语义侧：sdflow-implement SKILL.md 的「聚合套件发现契约」写入分档消费规则——字符串 ⇒ 两档同命令；映射 ⇒ 读 quick/full，缺 quick 记该层无 quick 档（unit 层例外：缺 quick 取 full，MUST NOT 跳过），缺 full 视为未分档（quick=full）。具体命令由 sdflow-devenv 运行时调研写入，本处只定义消费规则。

单一盘面条款侧：改写 sdflow-implement SKILL.md 的中间轮/收口轮范围——中间 fix 轮 = unit 全层 + 上轮失败用例（⊂ unit 层，结果仅供诊断）；收口 = 全量且所有通过行锚同一最终 SHA。写入「范围 MUST NOT 由『哪层受影响』判断界定」且「要求为该判断写明依据不构成缓解」。全仓 grep 清除「受影响层」提法。

devenv 侧：sdflow-devenv SKILL.md 增加 test-suites 发现与写入能力段落——运行时调研项目的测试基础设施，推荐 quick/full 分档命令写入 config.yaml 的 test-suites；已有配置时保留不覆盖。

- [x] config.template.yaml 增 test-suites quick/full 两档示例
- [x] sdflow-implement 聚合套件发现契约写入分档消费语义（含 unit 层例外）
- [x] sdflow-implement 单一盘面条款改写（中间轮/收口轮分离 + 取消受影响层）
- [x] sdflow-devenv SKILL.md 增 test-suites 发现与写入能力段落
- [x] 全仓 grep 确认无残存「受影响层」提法

### Task 2: 熔断硬上限与出票闸门（④⑤⑨③）

**Blocked-by:** none
**R-ID:** IO-2, IO-3, IO-4

在 sdflow-implement SKILL.md 中落地四项循环边界改进：熔断硬上限（④）、出票语法面有界性闸门（⑤）、red-before-green 扩展（⑨）、review package 增量化（③）。

熔断侧：review-loop-breaker 增加判据 (b)——同一文件累计被 Critical/Important 命中 ≥3 轮即熔断（与指纹无关），仲裁命题为「这个门本身该不该存在」。写入 MUST NOT 靠改进指纹算法替代 (b)。声明 (a)(b) 同时命中时 (b) subsume (a)。计数窗口 = 全 change 跨全部 ticket。熔断账本持久化到 impl-reports/breaker-ledger.md（格式 = 轮次|文件|指纹|严重度）。(b) 仲裁 dispatch 的 review package 含该文件 ticket 起点以来累积 diff（不受 ③ 增量限定）。

闸门侧：出票模式增加验收标准的语法面有界性闸门——无界语法面 MUST NOT 写成机械门。判据覆盖伪装形态（「在某格式文件中定位/插入/修改某处」）。标注为指令层约束、非机械保证。

TDD 侧：red-before-green 扩展到「往既有测试补断言或修改既有断言的期望值/判定逻辑」场景。收尾票的既有豁免不受影响。

review package 侧：fix 轮 review package 构造改为只打包「上轮已审 SHA..HEAD」，首轮范围不变。

一致性核对：核对 Tests are code 措辞与 IO-2 spec 表述一致（实现已在 d1aa607，只做核对不重实现）。

- [ ] 熔断规则增加判据 (b) + subsume 声明 + 计数窗口 + 账本持久化 + 仲裁累积 diff
- [ ] 出票语法面有界性闸门（含伪装形态判据 + 非机械保证标注）
- [ ] red-before-green 扩展到补断言/改断言场景
- [ ] review package fix 轮增量化
- [ ] Tests are code 一致性核对

### Task 3: 代码审复审边界与文档分叉消除（⑥）

**Blocked-by:** 2
**R-ID:** SW-1

在 sdflow-code-review SKILL.md 中新增复审边界规定，并消除与 sdflow-implement 的文档分叉。

复审边界：自动修复后 MUST 复审一轮（只审修复 diff、不重审全量）；仍有 Critical/Important → 不再自发第三轮，全部 defer 进 buglist 并在报告标注「复审上限已达」；无自动修复时不触发复审。硬上限 1 轮。

文档分叉消除：改写 sdflow-code-review SKILL.md 对比表右列措辞，与 sdflow-implement 统一为「存在复审循环，硬上限 1 轮」。全仓 grep 核验不再存在「无 re-review 紧闭环」类相反表述。

依赖 Task 2 的理由：消除文档分叉要求 sdflow-implement 侧的措辞已先落地（Task 2 落地熔断与 fix 循环相关条款），否则两侧对齐的目标措辞尚不确定。

- [ ] sdflow-code-review 新增复审边界规定（一轮、只审修复 diff、硬上限 1、残差 defer + 标注）
- [ ] 对比表右列措辞对齐（统一为「存在复审循环，硬上限 1 轮」）
- [ ] 全仓 grep 确认无「无 re-review 紧闭环」残存表述

### Task 4: 格式解析手段对照表（⑫）

**Blocked-by:** 2
**R-ID:** —

在 sdflow-devenv 的 references/verification-patterns.md 增加「格式解析手段对照表」一节，为 ⑤ 拦下的场景提供手段出处。

对照表内容：有标准库 → 用库；有权威第三方库且项目可依赖 → 用库；工具自身即权威 → 让工具跑一遍；都没有 → 收窄子集 + 界外 fail-loud。

在 ⑤ 闸门文案中回指该对照表，使被拦下的场景有「那应该怎么做」的指引。

依赖 Task 2 的理由：闸门回指要求 ⑤ 的闸门文案已先落地（Task 2 产出）。

- [ ] verification-patterns.md 增「格式解析手段对照表」一节
- [ ] ⑤ 闸门文案回指该对照表

### Task 5: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落 impl-reports/（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

同时按 proposal Success Metrics 逐条自检：① 结构判据（收口证据行同 SHA、中间轮无集成/e2e 通过行）② 复审轮数上界 ③ 熔断可触发 ④ 文档分叉消除。

运行 `openspec validate curb-rework-loop-cost --strict --type change` 确认四件套格式合规。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] Success Metrics 逐条自检通过
- [ ] openspec validate 通过
