# Proposal: streamline-workflow-automation

> 详细设计见同目录 [design.md](./design.md)（决策速查表 G/P/I/C 系列为真相源）。本文只给动机、范围、影响、合规。
>
> **〔交付范围·Phase A〕本 change 只交付 Phase A（连续化三阶段 + 提交自动化 + bundle 骨架）**。OQ1 定案拆 3 相串行，
> Phase B（issues 池）/ Phase C（跨模型 voice）的任务与 spec Requirement 已移出、见 [ROADMAP.md](./ROADMAP.md)，
> A merge 后各开新 change。proposal 与 design 是三相**共享 umbrella**（描述全貌），tasks.md 与 spec delta 则**只含 Phase A**。

## Why

`openspec/workflow/workflow.md` 现状是 **15 步手动 runbook**：每步手动粘命令、含 2 个 `/clear` 会话断点 + 2 个 HARD-GATE。真正需要人类接力的只有 4 类卡点（grill 对话 / 批准门 / `/clear` / merge），其余 11 步是机械串接，却全靠人工粘贴驱动。痛点：

- **断点多**：`/clear` 销毁会话，逼人手动重新起命令；每个 review/收尾步都要单独粘。
- **评审产物散、决策要中途打断**：spec-review/impl-review 各出报告，人工再手动合并；中途 `AskUserQuestion` 打断自动流。
- **债务池会无声堆积**：修不了的问题进 buglist/todolist，但从"记录"到"清理"有时间差，易遗忘（现已靠手动"债务分诊"临时补救）。
- **评审独立性单一**：只有 Claude 一个模型家族审，盲区同处。

## What Changes

四大块（均**只改 laodao-skills 权威源〔bundle assets + 自制 skill〕，绝不改 superpowers/openspec/gstack 插件**；消费仓走 `update` 采纳）。**按相交付：块 1+2 + 块 7 骨架 = 本 change（Phase A，已交付）；块 3 = Phase B、块 4 = Phase C（已移出 → ROADMAP）**：

1. **连续化三阶段**（G1/G2 + P1–P3g）：`/clear` 由 fresh 子代理独立性替代；中途 `AskUserQuestion` 改报告决策登记；阶段二合并成 `spec-review` 编排器（autoplan→spec-review→一份报告），阶段三 `writing-plans→subagent-dev→impl-review→opsx-done` 连续跑到 merge；去旧 step 14 人类门 + 弃用官方 `/code-review` step；新增 `hand-off.md` 替代 `code-review-verify.md`。
2. **提交自动化**（G4/G5）：不用 hook 驱动提交；显式收尾动作 + 共享 `checkpoint-commit.sh` 兜底；可选 SessionEnd 警告 hook。
3. **issues 池与批次管理**（I1–I12）：`buglists/todolists/` 合并为 `issues/{buglist,todolist}/` + 生成的 `INDEX.md` + `batches.md` 批次注册表；每 change 完成 sweep 分诊、INDEX 被动摊清 open×批次并标 DONE（reindex 同步批次状态，不做逾期催办）、批次走 cleanup change 清。
4. **跨模型 outside voice**（C1–C6）：参考 gstack 机制**自包含重写**（不引用 gstack）；spec-review 复用 autoplan 的 outside voice、impl-review 自带；命中 HR-TG 子集时单开领域专属 cross-model；fallback 到 Claude 子代理。

## Success Metrics

- 单个变更全流程的**人类介入点从"15 次粘贴 + 2 clear + 2 门"降到 3 处**（grill 对话 / 设计门 / hand-off 异步再入口）。
- 阶段二/三**各产出一份合并报告**（spec-review-report.md / code-review-report.md），无需人工手动合并。
- 债务池**零无声堆积**：每 change 完成后本 change 新增 OPEN 项 100% 被分诊入批次；INDEX 被动摊清 open 项 × 批次并标出 DONE（reindex 同步批次状态，不做逾期催办）〔grill-amendment〕。
- outside voice **默认开且永不阻塞**：codex 不可用时自动回落 Claude 子代理，审查不中断。

## Non-Goals

- **不改 superpowers / openspec / gstack 插件文件**（升级安全；定制只在 laodao-skills 权威源 + 消费仓 `config.yaml`）。
- **不引用 gstack 工具**（codex 机制自包含重写，只依赖 codex CLI 本身）。
- **不改 gstack 自身的 outside voice 机制**（autoplan / gstack review 保 gstack 原生；自制机制只驱动自制 skill；C7）。
- **不 squash 碎 commit**（保持与现状逐任务提交一致的细粒度历史）。
- **不改 grill 的多轮对话本性**（它是唯一不可折叠的人类对抗环节）。
- **不在本 change 内清空既有 buglist/todolist 债务**（迁移结构即可；债务清理走各自 cleanup change）。
- **不含消费仓的采纳工作**：各消费仓（含 zhws_ops_api）`update` 采纳 + 迁移本地债务数据是**下游 routine**，不属本 toolkit change。

## Impact

> **本 change 归属 `laodao-skills` 仓**（权威源；design 原则 6 / G6）。

- **workflow bundle 源** `opsx-project-init/assets/`：`workflow/workflow.md`（改写）、`workflow/reference/quality-layering.md` §五（改写）、`workflow/trigger-catalog.md`（新增 TG-26）、新增 checkpoint 脚本；review UI `review-tool/` → `workflow/`（tools 归位，B1）。
- **自制 skill**：`spec-review`、`impl-review`、`opsx-done` 改写；`buglist-recorder`、`todolist-recorder` 脚本增强（批次列 / scan 维度 / triage / reindex / batch / 路径默认改 issues/）+ 约定段写入 issues 标准（I13）；新增 codex outside-voice 共享 helper。
- **opsx-project-init**：deploy 逻辑（`tools/` → `workflow/tools/`）、update 覆盖面、INDEX 注入。
- **下游消费仓（含 zhws_ops_api）——不在本 change 内，routine 采纳**：`opsx-project-init update` 重拉新 bundle + 迁移各自 buglist/todolist → issues/ + `config.yaml`/`CLAUDE.md` 路径。每个消费仓各自做。

## Stakeholders & External Dependencies（TG-20）

- **laodao-skills 是共享 toolkit**：本 change 的 recorder / review skill 改动会传导到其它使用它的项目（如嵌入式项目）。issues 目录结构定为 toolkit 新标准（I9）——需确认其它项目可接受迁移。
- **外部依赖**：codex CLI（可选，fallback 兜底）、gstack（工作流已依赖 autoplan/review；但 outside voice 自包含重写后不再依赖 gstack）。

## Assumptions（TG-22）

- **A1**：子代理 fresh-context 提供的独立性足以替代 `/clear`（依据 quality-layering.md L20-22 自认 `/clear` 边际收益）。失效影响：评审独立性下降 → 回退保留 `/clear`。
- **A2**：codex（不同模型家族）能提供非重叠的评审捕获。失效影响：outside voice 退化为等价于 fresh Claude 子代理，无净损。
- **A3**：本机 1M 上下文使"去 `/clear` 后主 session 携带全生成历史进评审"的 token/注意力成本可接受。

## Open Questions（TG-21）

- ~~**OQ1**：本 change 跨 4 大块、~30 任务，是否**拆成多个 phased change** 更稳？~~ **〔grill-amendment〕已定案：拆成 3 相串行**（Phase A 流水线骨架 → B issues 池 / C 跨模型 voice；B/C 依赖 A 落地后各开新 change dir）。拆法、相划分、依赖序、必守的 3 条约束见 [ROADMAP.md](./ROADMAP.md)。`design.md` 为三相共享真相源。
- **OQ2**：autoplan"每次都跑"（P2b）为 provisional——上线后观察普通变更空跑四镜的成本，决定是否回退条件触发。
- **OQ3**：issues 结构定为 toolkit 新标准 vs 仅 zhws 本地（I9 暂定新标准）——需确认其它项目迁移窗口。

## Compliance

- 遵守 `rules/destructive-commands.md`：迁移 buglist/todolist、任何 `mv`/删除前走 5 条硬性规则。
- 遵守"绝不改插件"（升级安全）：定制只在 laodao-skills 权威源 + 消费仓 `config.yaml`。
- 新增 `openspec/workflow/` 触发（TG-26）后**同步 `openspec/INDEX.md`**（CLAUDE.md workflow 硬性要求）。
- 无 DB schema / API 合约 / Auth 边界改动（纯 process/tooling 变更）。
- **Spec delta**：本 change 把工作流规范性行为固化为新能力 `specs/spec-workflow/spec.md`（ADDED）——**Phase A 交付 9 条 Requirement**（连续化 + 提交自动化 + bundle 权威源），归档时并入 `openspec/specs/`；Phase B（issues 结构 / 批次注册表）与 Phase C（跨模型 voice / HR-TG）各 2 条 Requirement **已移出至 [ROADMAP.md](./ROADMAP.md)**，并入各自 change 的 spec delta。`workflow.md` / 各 skill 为其详细实现，design.md 为详细设计。`openspec validate --strict` 通过。
