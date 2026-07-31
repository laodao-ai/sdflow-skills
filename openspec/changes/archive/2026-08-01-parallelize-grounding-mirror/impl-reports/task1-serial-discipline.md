# Task 1 实现报告：串行纪律条款改写——分治接地镜与领域/对抗镜

## 改动

`sdflow-spec-review/SKILL.md:197`（第二步开篇的串行纪律〔T20〕引用块），单处替换：

**改前**：

> **串行纪律〔T20〕**：**MUST 待 Step1 checkpoint 完成后才 fan-out，禁止与 Step1 并行**（多镜评审对象须含 autoplan amendment）；若历史运行已并行，Step3 裁决须 diff autoplan amendment 增量核对并在报告注明。

**改后**：

> **串行纪律〔T20〕分治**：**领域镜 / 对抗镜 MUST 待 Step1 checkpoint 完成后才 fan-out**（多镜评审对象须含 autoplan amendment——它们依赖 autoplan 对 design/specs 的修订）；**接地镜 MAY 与 Step1 并行起跑**（读当前盘面的 design/specs + 真实代码核验代码事实，不依赖 autoplan 的设计判断产出）。autoplan amendment 后 SHALL NOT 自动补跑接地镜（amendment 新增的代码事实引用由 `sdflow-code-review` 的 grounding/history 镜兜底覆盖）。

## 验收标准核对

- [x] 串行纪律条款明确区分接地镜（MAY 并行）与领域/对抗镜（MUST 等 checkpoint）——改后条款用粗体分句写清两类镜的时序规则。
- [x] 兜底条款已删除——「若历史运行已并行，Step3 裁决须 diff autoplan amendment 增量核对并在报告注明」整句已移除，未保留任何变体。
- [x] 条款措辞与 spec delta 的 Scenario 一致——逐条对照 `openspec/changes/parallelize-grounding-mirror/specs/spec-workflow/spec.md`：
  - Scenario「领域/对抗镜等待 autoplan 先行」（MUST 等待 checkpoint 完成后再 fan-out，评审对象须含 amendment）⇔ 改后条款前半句原样对应。
  - Scenario「接地镜与 autoplan 并行」（MAY 在同一时刻 dispatch，读当前盘面 design/specs + 真实代码核验代码事实）⇔ 改后条款接地镜半句原样对应（措辞「读当前盘面的 design/specs + 真实代码核验代码事实」直接取自该 Scenario）。
  - Scenario「amendment 后不补跑接地镜」（SHALL NOT 被要求补跑，覆盖缺口由 code-review 的 grounding 镜兜底）⇔ 改后条款末句原样对应。

## 改动面确认

`git diff` 只命中 `sdflow-spec-review/SKILL.md` 一处 hunk（第 197 行该条款所在段落），未涉及脚本/测试/其它 SKILL 文件，符合 Global Constraints「改动面仅 `sdflow-spec-review/SKILL.md` 一个文件，三处条款改写」中的第一处。

未改动 Step2 fan-out 编排段（:232 上方的 dispatch 时序描述）与能力探针段（:207-230）——这两处分别是 Task 2、Task 2 的验收范围（tickets.md 里 Task 2 blocked-by Task 1），不在本 Task 1 scope 内。

## 状态

DONE — 一行摘要：T20 条款已按 spec delta 分治改写（接地镜 MAY 并行、领域/对抗镜 MUST 等 checkpoint），兜底条款已删除，措辞与 3 个相关 Scenario 逐句对齐，改动面仅此一处 hunk。
