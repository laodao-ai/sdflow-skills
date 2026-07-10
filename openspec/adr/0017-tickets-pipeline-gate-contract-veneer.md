# 0017 · tickets 管线以文件名外衣复用 ship_gate 契约，gate 文件名配置化永久否决

> 状态：Accepted（2026-07-10，grill `matt-workflow-integration` design 收敛）
> 关联：adr/0004（ship 阶段三编排器）· adr/0006（gate 驱动/机械层）· adr/0007（命名整合，否决 ship2）·
> CONTEXT「ticket（实现分解单位）」「盘面即状态」· 决策底稿 docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md §5/§10

## Context

`matt-workflow-integration` 引入 tickets 实现管线（tracer-bullet 垂直切片，替代 writing-plans 的带码 plan）作为 superpowers 管线的可选双轨。ship_gate.py（阶段三完成判据台账，约 842 行、多轮 hardening 沉淀）的完成判据契约为：**文件名 `superpowers-plan.md`（:722）+ `### Task <n>:` 标题集（fence-aware）+ checkpoint 标签 ∪ 复选框双通道（:740-752）**——任务体内容完全不设限。新管线的 ticket 文件如何与 gate 对接，三个候选真实分歧过（三镜 + 对抗镜评审）：A. 沿用旧文件名（外衣）；B. gate 文件名配置化；C. gate 小改新文件名。

未来读者打开 `superpowers-plan.md` 看到行为级 ticket 而非带码 plan 时，第一反应必是「为什么不改名/不做成可配置」——本 ADR 记录答案。

## Decision

### 1. 试验期：ticket 文件穿 `superpowers-plan.md` 外衣，gate 零改动

- ticket 文件写入 change 目录旧文件名，每 ticket 以 `### Task N: <ticket 名>` 为标题、ticket 内验收复选框 + frontmatter 管线 marker；完成信号双写（checkpoint `<change>:task<N>-<slug>` 标签 + 勾框）。
- gate 的三道落盘校验（fence/零标题/重号 :727-739）、B1 窗口锚（plan 首次提交 sha）、CONTINUE_IMPL done_tasks resume 语义**原样可用**——票体内容 gate 不关心，兼容是逐行亲验的事实而非假设。
- 出 ticket 收尾 MUST 显式 checkpoint（plan 单独提交建立窗口锚，不依赖「首 ticket add -A 捎带提交」的巧合自愈）。

### 2. gate 文件名配置化**永久否决**（不是延后，是否决）

- `plan_first_sha` 窗口锚按**路径** keyed（:740）——双文件名使窗口锚、fence 校验、双文件并存裁决全部裂成分支，制造新 UNKNOWN 态；
- gate 刻意**零依赖**（:286「不 import yaml」不变量）——读 config 破坏该不变量；
- 「世界上可能存在两个 plan 文件名」是常态化的双源歧义，与单一源纪律正面冲突。
- 三案独立评审均否决此选项，无幸存论证。

### 3. 「文件名说谎」的语义债分两拍还，emit 提示串同拍

- 试验期承受外衣（gate 是全仓被加固最重的脚本，未定案的方案不配动它）；**判赢毕业后（Phase B）**再拍终局：改中性文件名（须带旧名 fallback + 双文件同存判 UNKNOWN，防多仓异步升级期的假初始态/静默重出 ticket）vs 永不改名——以试点期「外衣误导排障」实证为判据。
- gate emit 的 next 提示串（:724 `writing-plans` / :750 `subagent-dev`）同拍改管线中性词；试验期以 ship SKILL.md 链序显式声明「此二态映射以链序为权威、next 仅信息性」消歧——gate 的**状态判定**权威不变，失真的只是 skill 名提示。

## Consequences

- **正**：换管线 = 换 ship 链序两处映射指向；gate 及其测试零波及；两管线可同时在飞（marker 隔离在途）；回退 = config 键回缺省。
- **负（显式承受）**：试验期文件名与内容不符，排障首眼可能被误导（记入试点观察项）；弱档模型照 next 提示串误路由的窗口期风险（链序权威声明压制，实发即 Phase B 提前）。
- **边界**：本 ADR 只锚 gate 契约对接方式；管线路由策略（手动 config 键 + 盘面 marker、零模型判断）与 ship 不 fork 属可逆策略决策，记录在 change design.md（D2/D5），不占 ADR。
