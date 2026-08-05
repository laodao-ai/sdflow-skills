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

**规则 · 条件**：条件：问题 / 方向模糊、方案未定时先跑；问题清晰直接进步 2。人示意收敛（如"开搞"/"做吧"/"开 change"）→ 模型自动 invoke `/sdflow-spec`（generation-process §四 自动触发规则）

## 阶段一 · 步骤 2 — `/sdflow-spec`

一次跑完 澄清(A)→拷问(B)→生成(C)。人可直接触发；模型 SHALL 在人示意收敛或用户描述需求且需要开 change 时自动 invoke，MUST NOT 自主判断"该开 change 了"

**产出物**：proposal/design/specs/tasks + decision-memo.md

**规则 · 条件**：generation-process §四；出口序列 = `/clear` → 换档 → `/sdflow-spec-review`（对 G1 的具名例外，见 §三.2）

## 阶段二 · 步骤 3 — `/sdflow-spec-review`

**prompt**（原样复制，勿转述 · 单一源 `prompts/step4-spec-review.md`）：

```
/sdflow-spec-review 独立审查 {change dir}
```

**产出物**：spec-review-report.md

**规则 · 条件**：编排器：内部 autoplan→并行多镜→**一份**报告；中途不 AskUserQuestion（决策登记进报告）；fresh 子代理替代 /clear；内部 2×checkpoint；改动标 [spec-review-amendment]。**非平凡必跑（主审）**

## 阶段二 · 步骤 4 — `HARD-GATE`

人工过 **一份** `spec-review-report.md`（决策登记区已摊开选项+推荐+三面后果(系统/用户/开发循环)+主次判定）→ 批准设计

**产出物**：（人工：批准后才进实现）

**规则 · 条件**：generation-process 门；**★全流程唯一人类门**

## 阶段三 · 步骤 5 — `/writing-plans`

**prompt**（原样复制，勿转述 · 单一源 `prompts/step6-writing-plans.md`）：

```
/writing-plans 按 {change dir} 的 design.md 与评审结论生成任务清单 superpowers-plan.md（superpowers 轨固定用此名；tickets 轨改用 `tickets.md`、由 `sdflow-implement` 出票，不走本 prompt），参考 tasks.md 分组，有测试计划则附测试覆盖图。把 design 的领域约束逐字写进 plan 的 Global Constraints，**并在每个 Task 段内复述与该任务相关的那几条 + 四条通则**——`scripts/task-brief` 只抽 `### Task N` 那一段喂给 implementer，**Global Constraints 不进 brief，写在那里 implementer 一个字都看不到**。plan 每任务的 commit 步 MUST 显式写 `bash ~/.sdflow/hack/checkpoint-commit.sh <change>:task<N>-<slug> "<描述>"`（<change> = 本 change 的 openspec kebab slug），由 implementer 自己执行——该标签是 /sdflow-ship gate 的完成判据主锚，格式不合会导致 gate 数不到。生成后自动以 subagent-driven-development 执行，自动完成全部任务，每任务完成跑测试套件确认无 warning；逐任务 checkpoint；final whole-branch 终审 dispatch 时把 code-checklists/domains/<命中栈>（规则根经 ~/.sdflow/hack/resolve-workflow.sh 解析）作额外 review lens 附给 reviewer；无法自动解决的记入 buglists 或 todolists。
```

**产出物**：superpowers-plan.md + 代码

**规则 · 条件**：**仅当仓显式设 `impl-pipeline: superpowers` 时走本行**（superpowers 轨：writing-plans → subagent-driven-development，产出文件名不变；superpowers + quality-layering 注入点 A）；**缺省（无该键）走 tickets 轨**，不产出本步骤文件，路由至 sdflow-implement 出票执行（细则见 sdflow-ship/SKILL.md 链序；tickets 轨产出为 `tickets.md`〔D5/adr-0033〕，两轨计划文件名分列，gate/route 经共享 resolver 定位）

## 阶段三 · 步骤 6 — `/subagent-driven-development`

（由步骤 5 自动触发，**仅 superpowers 轨**）

**prompt**（原样复制，勿转述 · 单一源 `prompts/step7-subagent-dev.md`）：

```
/subagent-driven-development 自动完成全部任务，每任务完成跑测试套件确认无 warning；逐任务 checkpoint；final whole-branch 终审 dispatch 时把 code-checklists/domains/<命中栈>（规则根经 ~/.sdflow/hack/resolve-workflow.sh 解析） 作额外 review lens 附给 reviewer；无法自动解决的记入 buglists 或 todolists。
```

**产出物**：代码

**规则 · 条件**：quality-layering 注入点 B（领域审前移进生成循环，即时 fix+re-review 闭环）。**🔴 派 implementer / task-reviewer / fix / 终审子代理时，dispatch prompt MUST 原文携带四条通则**——子代理是 fresh context，**看不见 CLAUDE.md**；且 `scripts/task-brief` 只抽 `### Task N` 段，plan 的 Global Constraints 与 Context 都不进 brief。漏带 ⇒ implementer 眼前只有现状代码，**必然**把「现有代码不是这么写的」当成「那就按现状来」（通则③）。tickets 轨的等价执行见 sdflow-implement 编排器（缺省即 tickets）

## 阶段三 · 步骤 7 — `/sdflow-code-review`

**prompt**（原样复制，勿转述 · 单一源 `prompts/step8-code-review.md`）：

```
/sdflow-code-review 每次全跑独立审查 {change dir} 的代码变更（并入 gstack/review 的 scope-drift+完成度审计；能修的自动修标 [impl-review-fix]、修不了/拿不准的记 buglists/todolists；汇总一份 code-review-report.md）。完成后 checkpoint-commit sdflow-code-review。
```

**产出物**：code-review-report.md

**规则 · 条件**：编排器：**每次全跑·独立冷·强制主审**〔P3c〕；清单逐条+对抗+历史镜+置信过滤；阶段三无人类门（自动修/裁/defer，不 AskUserQuestion）+ 跨模型 outside voice（always code voice + HR-TG 领域 cross-model）

## 阶段三 · 步骤 8 — `/sdflow-done`

**prompt**（原样复制，勿转述 · 单一源 `prompts/step9-done.md`）：

```
/sdflow-done
```

**产出物**：verify-report + hand-off + 归档 + 提交 + 合并

**规则 · 条件**：sdflow-done skill；verify(防假✅证据锚点)→**issues sweep 子步(§2.1,已就位：分诊本change OPEN项入批次→reindex)**→hand-off.md→archive(+delta 同步)→commit→merge；**必跑（闭环）**

---

*流程骨架与设计决策 → [workflow.md](./workflow.md) · 演进史 → [workflow-history.md](./workflow-history.md)*
