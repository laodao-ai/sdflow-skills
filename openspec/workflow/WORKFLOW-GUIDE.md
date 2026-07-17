<!-- 本文件由 hack/gen_workflow_guide.py 从 workflow.md + prompts/ 机械生成。DO NOT EDIT。 -->
<!-- 改 prompt → 改 prompts/step*.md（单一源）；改流程 → 改 workflow.md；然后跑 --write。 -->

# Spec 工作流 —— 完整参考手册（给人看）

> **这份是给人读的**：从头到尾，每步 prompt 全文都在，不用跳文件。
>
> **模型 MUST NOT 读本文** —— 要取某一步的 prompt，直接读 `workflow/prompts/step*.md`
> （一步一文件，几百字节）。读本文 = 为你不需要的 90% 付 token。
>
> **MUST NOT 手改本文**：prompt 的单一源是 `prompts/step*.md`，流程的单一源是 `workflow.md`；
> 手改这里，下次生成即被覆盖，而且会与单一源漂移。

---

## 阶段一 · 步骤 1 — `/opsx:explore`

**prompt**（原样复制，勿转述 · 单一源 `prompts/step1-explore.md`）：

```
/opsx:explore {topic}
```

**产出物**：—

**规则 · 条件**：generation-process ③发散；**单 session 可收敛的模糊才跑**（问题清晰直接 ff；事中判定超单 session 转 wayfinder，见 1b）

## 阶段一 · 步骤 1b — `wayfinder chart`

事中判定超单 session（讨论已跨 session/跨天，或经历 /clear/压缩仍未收敛）才切入；铺图逐 ticket 决议；TG 判命中前置写入 map Notes（**增强非转移**：ff 起手判触发纪律不变，Notes 有则核对、无则照常全判，缺失不硬卡）；缺装（`~/.claude/skills/wayfinder` 不存在）→ 显式降级 opsx:explore

**产出物**：map.md + issues/*.md

**规则 · 条件**：T126/D6；三档判据事中可观察

## 阶段一 · 步骤 2 — `/opsx:ff`

**prompt**（原样复制，勿转述 · 单一源 `prompts/step2-ff.md`）：

```
/opsx:ff {change}。若不在 feature 分支则先 git checkout -b feat/{change}。若 change 源于 wayfinder map：调用语显式携带 map 路径（如 @openspec/roadmaps/{name}/map.md）并按 ff-generation-constraints.md「wayfinder→ff 衔接契约」逐区读取。完成后 checkpoint-commit ff。
```

**产出物**：proposal/design/specs/tasks

**规则 · 条件**：ff-generation-constraints(FF-0)+config；**必跑**

## 阶段一 · 步骤 3 — `/grill-with-docs`

**prompt**（原样复制，勿转述 · 单一源 `prompts/step3-grill.md`）：

```
/grill-with-docs 死磕 {change dir} 的 design.md（连 proposal/specs/tasks）。守三条通则——尤其：拷问的基准是【目标态】，MUST NOT 用「现在代码不是这么写的 / 存量里没出现过」否决设计（现状只用来核事实，不用来定对错）；事实自己查（grep 得到的别问）；≥2 方案先调研再给推荐，别把选项丢回来。落档：ADR→openspec/adr/、术语→openspec/CONTEXT.md；文档改动标 [grill-amendment]。收敛后 checkpoint-commit grill（多轮中途不提交）。
```

**产出物**：design/ADR/CONTEXT 更新

**规则 · 条件**：generation-process ③对抗；非平凡变更必跑。**grill 是独立审视，一律全深度**——MUST NOT 因上游（explore / wayfinder 已决 ticket）已经想过就瘦跑或跳过某条分支；拿上游产出给自己松绑，二次审视就退化成盖章（见 ff-generation-constraints.md 的回链锚条款）。

## 阶段二 · 步骤 4 — `/sdflow-spec-review`

**prompt**（原样复制，勿转述 · 单一源 `prompts/step4-spec-review.md`）：

```
/sdflow-spec-review 独立审查 {change dir}
```

**产出物**：spec-review-report.md

**规则 · 条件**：编排器：内部 autoplan→并行多镜→**一份**报告；中途不 AskUserQuestion（决策登记进报告）；fresh 子代理替代 /clear；内部 2×checkpoint；改动标 [spec-review-amendment]。**非平凡必跑（主审）**

## 阶段二 · 步骤 5 — `HARD-GATE`

人工过 **一份** `spec-review-report.md`（决策登记区已摊开选项+推荐+三面后果(系统/用户/开发循环)+主次判定）→ 批准设计

**产出物**：（人工：批准后才进实现）

**规则 · 条件**：generation-process 门；**★全流程唯一人类门**

## 阶段二 · 步骤 5.5 — `/embedded-test-sop`

**prompt**（原样复制，勿转述 · 单一源 `prompts/step5_5-embedded-sop.md`）：

```
/embedded-test-sop 基于 {change dir} 的 specs/ + 评审结论生成 {change}-sop.md 手工测试文档 + log-checks.yaml，存到 {change dir}。
```

**产出物**：{change}-sop.md + log-checks.yaml

**规则 · 条件**：嵌入式专属条件触发：TG-02(嵌入式固件) **∧**（启动/复位·状态机·协议 等高风险 **∨** TG-18 有测试计划）；非嵌入式天然不触发

## 阶段三 · 步骤 6 — `/writing-plans`

**prompt**（原样复制，勿转述 · 单一源 `prompts/step6-writing-plans.md`）：

```
/writing-plans 按 {change dir} 的 design.md 与评审结论生成任务清单 superpowers-plan.md，参考 tasks.md 分组，有测试计划则附测试覆盖图。把 design 的领域约束逐字写进 plan 的 Global Constraints，**并在每个 Task 段内复述与该任务相关的那几条 + 三条通则**——`scripts/task-brief` 只抽 `### Task N` 那一段喂给 implementer，**Global Constraints 不进 brief，写在那里 implementer 一个字都看不到**。plan 每任务的 commit 步 MUST 显式写 `bash ~/.sdflow/hack/checkpoint-commit.sh <change>:task<N>-<slug> "<描述>"`（<change> = 本 change 的 openspec kebab slug），由 implementer 自己执行——该标签是 /sdflow-ship gate 的完成判据主锚，格式不合会导致 gate 数不到。生成后自动以 subagent-driven-development 执行，自动完成全部任务，每任务完成跑测试套件确认无 warning；逐任务 checkpoint；final whole-branch 终审 dispatch 时把 code-checklists/domains/<命中栈>（规则根经 ~/.sdflow/hack/resolve-workflow.sh 解析）作额外 review lens 附给 reviewer；无法自动解决的记入 buglists 或 todolists。
```

**产出物**：superpowers-plan.md + 代码

**规则 · 条件**：superpowers + quality-layering 注入点 A；**必跑（计划→实现自动化）**；实现管线可经 config.yaml `impl-pipeline: tickets` 键路由至 sdflow-implement（缺省不变，细则见 sdflow-ship/SKILL.md 链序）

## 阶段三 · 步骤 7 — `/subagent-driven-development`

（由步骤 6 自动触发）

**prompt**（原样复制，勿转述 · 单一源 `prompts/step7-subagent-dev.md`）：

```
/subagent-driven-development 自动完成全部任务，每任务完成跑测试套件确认无 warning；逐任务 checkpoint；final whole-branch 终审 dispatch 时把 code-checklists/domains/<命中栈>（规则根经 ~/.sdflow/hack/resolve-workflow.sh 解析） 作额外 review lens 附给 reviewer；无法自动解决的记入 buglists 或 todolists。
```

**产出物**：代码

**规则 · 条件**：quality-layering 注入点 B（领域审前移进生成循环，即时 fix+re-review 闭环）。**🔴 派 implementer / task-reviewer / fix / 终审子代理时，dispatch prompt MUST 原文携带三条通则**——子代理是 fresh context，**看不见 CLAUDE.md**；且 `scripts/task-brief` 只抽 `### Task N` 段，plan 的 Global Constraints 与 Context 都不进 brief。漏带 ⇒ implementer 眼前只有现状代码，**必然**把「现有代码不是这么写的」当成「那就按现状来」（通则③）。实现管线可经 config.yaml `impl-pipeline: tickets` 键路由至 sdflow-implement（缺省不变，细则见 sdflow-ship/SKILL.md 链序）

## 阶段三 · 步骤 8 — `/sdflow-code-review`

**prompt**（原样复制，勿转述 · 单一源 `prompts/step8-code-review.md`）：

```
/sdflow-code-review 每次全跑独立审查 {change dir} 的代码变更（并入 gstack/review 的 scope-drift+完成度审计；能修的自动修标 [impl-review-fix]、修不了/拿不准的记 buglists/todolists；汇总一份 code-review-report.md）。完成后 checkpoint-commit sdflow-code-review。
```

**产出物**：code-review-report.md

**规则 · 条件**：编排器：**每次全跑·独立冷·强制主审**〔P3c〕；清单逐条+对抗+历史镜+置信过滤；阶段三无人类门（自动修/裁/defer，不 AskUserQuestion）+ 跨模型 outside voice（always code voice + HR-TG 领域 cross-model）

## 阶段三 · 步骤 9 — `/sdflow-done`

**prompt**（原样复制，勿转述 · 单一源 `prompts/step9-done.md`）：

```
/sdflow-done
```

**产出物**：verify-report + hand-off + 归档 + 提交 + 合并

**规则 · 条件**：sdflow-done skill；verify(防假✅证据锚点)→**issues sweep 子步(§2.1,已就位：分诊本change OPEN项入批次→reindex)**→hand-off.md→archive(+delta 同步)→commit→merge；**必跑（闭环）**

---

*流程骨架与设计决策 → [workflow.md](./workflow.md) · 演进史 → [workflow-history.md](./workflow-history.md)*
