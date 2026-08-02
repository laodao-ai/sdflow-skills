---
ship-gate:
  code_review: pass
  reviewed_sha: 8e284fd02186539f45ca6456890f840672de1395
---

## code-review 报告 — tickets-parallel-frontier

<!-- sdflow:step1-broad-review v1 mode="native" -->

### 命中范围

栈: 无命中领域（纯 Markdown skill 集合）  清单: CR-01~09 通用基线  gstack/review: scope-drift 无偏离 / 完成度 2/2 任务 100%

改动面：`sdflow-implement/SKILL.md` 一个文件，46 行新增 / 7 行删除，全部为 Markdown prose 条款修改。

### 子代理能力锚

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

### HR-TG 判定

<!-- sdflow:hr-tg v1 hit="TG-04,TG-17" declared="TG-04,TG-17" evidence="TG-04: worktree 隔离并行派发 implementer 子代理; TG-17: frontier 编排从严格串行改为宿主条件化受限并行" -->

命中 TG-04（子代理调度安全：worktree 隔离并行派发）+ TG-17（管线编排：frontier 从串行改为受限并行）。

### Findings（置信 ≥80）

无存活 finding。

CR-01~09 逐条审查结果：
- CR-01~04（错误处理/nil 安全/资源清理）：不适用——纯 Markdown prose 修改，无代码级错误处理
- CR-05（并发与互斥）：高度相关——本 change 引入并行 dispatch，但通过 worktree 隔离（每个 implementer 独立 `.git/index`）结构性消除 index 竞态，merge conflict 由 `git merge --no-ff` 原生检测 fail-loud。无 finding。
- CR-06~08：不适用（无代码级类型转换/日志/常量）
- CR-09：不适用（无新增测试文件）

对抗推理（2 角度）：
1. 并发竞态：worktree 隔离给每个 implementer 独立 `.git/index`，index 竞态不存在。merge conflict 由 git 原生检测。✅
2. 错误路径：BLOCKED 票 worktree 直接丢弃不 merge、完成票正常审、merge conflict 走 halt envelope、Codex 退化串行。✅

历史核查：frontier 段从未被 revert，本次是首次从严格串行改为并行。前序 change（curb-rework-loop-cost）未触碰 frontier 红线。无历史冲突。

### 已裁掉（反静默压制，可审计）

| # | 来源 | 发现 | 置信 | 裁掉理由 |
|---|---|---|---|---|
| X1 | code-voice+hr-tg | brief 文件在主工作树未提交，worktree 隔离看不到 | 35 | 错误前提：Read tool 使用绝对路径访问文件系统（非 git），worktree 隔离只隔离 .git/index 不隔离文件系统读取 |
| X2 | code-voice+hr-tg | worktree 生命周期无清理步骤 | 45 | Agent tool 文档明确「有改动时 path and branch are returned in the result」供编排层处置；BLOCKED 票 worktree 由 harness 自动回收；prose 指令层不需要定义 git worktree remove 的具体命令 |
| X3 | code-voice+hr-tg | 跨票语义集成盲区未登记为接受的边角 | 50 | 已有结构性缓解（出票并行安全约束 + 收尾票聚合套件 + 本 skill 冷审），是所有并行执行策略的固有残余，decision-memo 已登记 merge conflict 兜底 |
| X4 | code-voice | 共享测试资源争用未讨论 | 25 | 过于泛化，任何并行执行都有此顾虑，非设计层面能解决的问题 |

### 修复 / defer 台账

无自动修复、无 defer。

### Outside-voice 锚

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="claude" reason_code="not-installed" findings="0" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="claude" reason_code="not-installed" findings="0" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->

两站点均走同族 fallback（preflight 因独立 shell 环境变量不持久报 exit 1）。4 条 findings 全部 <80 滤掉。

### 度量锚

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="claude" site="code-voice" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="claude" site="hr-tg" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->

### 结论

- [x] 建议进 /sdflow-done
- [x] 无 defer 残差
