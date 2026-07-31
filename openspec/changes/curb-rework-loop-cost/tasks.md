# Tasks · curb-rework-loop-cost

> **Requirement ID 简称**（与 `specs/` 双向追溯）
> - **IO-1** = `impl-orchestration` / 出 ticket 模式产出 tracer-bullet ticket 并落盘即返回（MODIFIED，含 ①②⑤）
> - **IO-2** = `impl-orchestration` / 每 ticket 双轴审加修复环（MODIFIED，含 ④ 与 Tests are code）
> - **IO-3** = `impl-orchestration` / fix 轮的 review package 只含本轮修复 diff（ADDED，③）
> - **IO-4** = `impl-orchestration` / 往既有测试补断言同样适用 red-before-green（ADDED，⑨）
> - **SW-1** = `spec-workflow` / sdflow-code-review 自动修复后的复审边界与硬上限（ADDED，⑥）
>
> **前置事实（如实标注）**：⑩「Tests are code」的**实现已于本 change 立项前落盘**（`d1aa607`，
> 已在 `main`），故 IO-2 中该段落属**补写 spec 以对齐既有实现**，任务 2.3 仅做一致性核对，
> MUST NOT 重复实现。

## 1. 配置契约先行（P0 · ② 是 ① 的前置）

- [ ] 1.1 **IO-1** — `sdflow-init/assets/**/config.template.yaml` 的 `test-suites` 增加 quick/full 两档示例与注释；保持字符串形状为合法子集
- [ ] 1.2 **IO-1** — `sdflow-implement/SKILL.md:313-322`「聚合套件发现契约」写入分档消费语义：字符串 ⇒ 两档同命令；映射 ⇒ 读 `quick`/`full`，缺 `quick` 记该层无 quick 档（unit 层例外：缺 quick 取 full，MUST NOT 跳过），缺 `full` 视为未分档（quick=full）。具体命令由 `sdflow-devenv` 运行时调研写入，本处只定义消费规则
- [ ] 1.3 **IO-1** — `sdflow-devenv/SKILL.md` 增加 test-suites 发现与写入能力：运行时调研项目的测试基础设施，推荐 quick/full 分档命令，写入 `openspec/config.yaml` 的 `test-suites`；已有配置时保留不覆盖

## 2. 实现期循环边界（P0/P1）

- [ ] 2.1 **IO-1** — 改写 `sdflow-implement/SKILL.md:328-330` 单一盘面条款：中间轮 = unit 全层 + 上轮失败用例（⊂ unit 层，结果仅供诊断）；收口 = 全量且所有通过行锚同一最终 SHA。**保留**原「所有判通过的行锚同一最终 SHA」语句与拼接反例
- [ ] 2.2 **IO-1** — 同段落写入「范围 MUST NOT 由『哪层受影响』判断界定」，并明确「要求为该判断写明依据不构成缓解」；全仓 grep 清除「受影响层」提法
- [ ] 2.3 **IO-2** — 核对 `sdflow-implement/SKILL.md:616-621` 的「Tests are code」措辞与本 change specs 中 IO-2 的表述一致（实现已在 `d1aa607`，本任务只做一致性核对，不重复实现）
- [ ] 2.4 **IO-2** — `sdflow-implement/SKILL.md:651-657` 熔断规则增加判据 (b)：同一文件累计被 Critical/Important 命中 ≥3 轮即熔断（与指纹无关），仲裁命题为「这个门本身该不该存在」；写入「MUST NOT 靠改进指纹算法替代 (b)」；声明 (a)(b) 同时命中时 (b) subsume (a)；计数窗口 = 全 change 跨全部 ticket；熔断账本持久化到 `impl-reports/breaker-ledger.md`（格式 = `轮次|文件|指纹|严重度`）；(b) 仲裁 dispatch 的 review package 含该文件 ticket 起点以来累积 diff（不受 ③ 增量限定）
- [ ] 2.5 **IO-4** — `sdflow-implement/SKILL.md:509` red-before-green 扩展到「往既有测试补断言或修改既有断言的期望值/判定逻辑」场景；同时明确收尾票的既有豁免不受影响
- [ ] 2.6 **IO-3** — `sdflow-implement/SKILL.md:583` review package 构造改为 fix 轮只打包「上轮已审 SHA..HEAD」；首轮范围不变
- [ ] 2.7 **IO-1** — `sdflow-implement/SKILL.md:270` 附近增加出票语法面有界性闸门，判据覆盖伪装形态（「在某格式文件中定位/插入/修改某处」）；标注为指令层约束、非机械保证

## 3. 代码审复审边界（P0）

- [ ] 3.1 **SW-1** — `sdflow-code-review/SKILL.md` 新增复审边界规定：自动修复后复审一轮、只审修复 diff、硬上限 1、残差 defer 并在报告标注；无自动修复时不触发
- [ ] 3.2 **SW-1** — 消除文档分叉：改写 `sdflow-code-review/SKILL.md:181` 对比表右列措辞，与 `sdflow-implement/SKILL.md:349,353` 统一为「存在复审循环，硬上限 1 轮」
- [ ] 3.3 **SW-1** — 全仓 grep 核验不再存在「无 re-review 紧闭环」类相反表述（proposal 的 Success Metrics 第 4 条）

## 4. 手段出处（P2 · 无 R-ID，追溯至 proposal - What Changes ⑫）

- [ ] 4.1 `sdflow-devenv/references/verification-patterns.md` 增「格式解析手段对照表」一节：有标准库→用库；有权威第三方库且项目可依赖→用库；工具自身即权威→让工具跑一遍；都没有→收窄子集 + 界外 fail-loud
- [ ] 4.2 在 ⑤ 的闸门文案中回指该对照表，使被拦下的场景有手段出处

## 5. 验证与收口

- [ ] 5.1 跑全仓 `pytest`，确认 1.3 新增测试通过且无既有回归
- [ ] 5.2 按 proposal - Success Metrics 逐条自检：① 结构判据（收口证据行同 SHA、中间轮无集成/e2e 通过行）② 复审轮数上界 ③ 熔断可触发 ④ 文档分叉消除
- [ ] 5.3 `openspec validate curb-rework-loop-cost --strict --type change` 通过
- [ ] 5.4 **实现验证**（收尾）：按聚合套件发现契约运行本 change 的聚合测试套件并全部通过，证据落 `impl-reports/`，每层一行 `<层>|<命令原文>|<退出码>|<SHA>`

## 测试覆盖图（TG-18）

| code path / 契约面 | 测试类型 | 落点 | 任务 |
|---|---|---|---|
| **T1** `test-suites` 分档消费语义（字符串 / 映射 / 缺 quick / 缺 full） | **无自动化测试**——消费方是 SKILL.md prose 指令（模型运行时读 config 判断），无 runtime parser；由阶段二设计审 + 阶段三双轴审的语义核验承担 | — | 1.2 |
| **T2** 中间轮与收口轮范围分离（条款语义） | **无自动化测试**——纯 SKILL.md prose，由阶段二设计审 + 阶段三双轴审的语义核验承担 | — | 2.1 / 2.2 |
| **T3** 熔断判据 (b) | **无自动化测试**——熔断是编排器运行时行为，无确定性捕获路径（`ship_gate` 不介入）；由 IO-2 的 Scenario 作为语义验收 | — | 2.4 |
| **T4** 复审硬上限 | **无自动化测试**——同 T3，指令层约束由编排器自报 | — | 3.1 |
| **T5** 文档分叉消除 | 机械（grep 断言） | 手工 grep，见 3.3 | 3.3 |
| **T6** 全仓无回归 | 既有全量套件 | 仓根 `pytest` | 5.1 / 5.4 |

> 🔴 **诚实边界**：本 change 的多数交付物是 **SKILL.md 的 prose 契约**，无确定性信号可供机械捕获
> （adr/0018 的语义残余）。T2/T3/T4 标「无自动化测试」是**合法的残余划分**，MUST NOT 为凑覆盖率
> 编造恒真断言——那正是 IO-4（补断言须验红）要防的形态。可机械化的只有 T1（配置解析）、
> T5（grep 断言）与 T6（回归），已全部覆盖。
