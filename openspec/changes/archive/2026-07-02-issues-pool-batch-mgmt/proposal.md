# Proposal: issues-pool-batch-mgmt（Phase B）

> **本 change = `streamline-workflow-automation` 拆分的 Phase B**（OQ1 定案拆 3 相串行）。
> 拆法/相划分/依赖序见归档 [ROADMAP.md](../archive/2026-07-02-streamline-workflow-automation/ROADMAP.md)「Phase B 待迁」。
> **决策真相源 = 归档 umbrella [design.md](../archive/2026-07-02-streamline-workflow-automation/design.md) §八 + 决策速查表 I1–I13**——本 change 的 proposal/design/tasks **反向引用、不重复推导**。
> 本 change 只交付 **块 3（issues 池与批次管理）**；连续化（块1/2=Phase A 已交付）、跨模型 voice（块4=Phase C）不在本 change。

## Why

阶段三把"修不了的问题进 buglist/todolist → hand-off 引导另开 change 清理"作为债务出口，但债务从"记录"到"清理"有时间差，**会无声堆积、易遗忘**——现状已靠用户**手动**"债务分诊"临时补救（见 zhws `2026-07-todolist.md` 头部把 OPEN 项手动归组待起 change）。这套手动仪式暴露的 smell（umbrella design §8.1）：

- **状态列被塞进批次组**（"归属5A(vpd)"）→ 污染干净的生命周期状态。
- **`关联Change` 一格塞两件事**（源 phase-4 · target phase-5）→ **源**(哪发现) 与 **target**(哪修) 混一格。
- **根因**：缺一个独立的"批次"维度。

Phase B 把这套手动分诊**系统化**并修掉它暴露的 smell。

## What Changes

块 3 = umbrella 决策 **I1–I13**（只改 laodao-skills 权威源〔recorder skill + workflow bundle〕，消费仓走 `opsx-project-init update` 采纳）：

1. **统一 issues 结构**（I1/I3/I7/I8）：`openspec/buglists/`+`todolists/` 合并为 `openspec/issues/{buglist,todolist}/`（bug 按日 / todo 按月），item 分**源change(provenance,不可变) / 批次(triage,可变) / status(生命周期,回归干净)** 三维度；per-file 状态总览表保留。
2. **INDEX 只生成·禁手改**（I2）：新增 `reindex` 命令从 dated 文件重建 `issues/INDEX.md`（摊清 open item × 批次、标 DONE），杜绝第三漂移源。
3. **批次注册表**（I11/I4）：`issues/batches.md` 单文件给批次第一类身份（`PLANNED→IN_PROGRESS→DONE`，条目薄；批次 key = 清理 change 名）；新增 `batch` 命令（add/set-status，跨 bug+todo）。
4. **债务闭环 = 被动 + reindex 同步状态**（I12〔grill-amendment / Q5〕）：**不做逾期主动催办**；INDEX 被动摊清 open×批次并标 DONE，reindex 拿 item 池当 ground truth **同步批次状态**（成员全 DONE→批次 DONE、不一致标出纠正）。
5. **sweep 接入 opsx-done**（I5/I6）：每 change 完成在 opsx-done 生成 hand-off 那步**只分诊本 change 新增 OPEN 项**入批次 → `batches.md`(PLANNED) → hand-off 引用；`workflow.md` 追加 sweep 步引用。
6. **脚本/工具连带**（I9/I10）：两 recorder 路径默认改 `issues/`、scan 加维度 `--源/--批次/--open-ungrouped`、加 `triage` 命令；review UI（`workflow/tools/engine.js`、`review.html`）读 issues 新路径。生效范围 = laodao-skills **toolkit 新标准**（I9）。
7. **标准归属**（I13）：以上标准的**唯一真相源 = 两 recorder skill 的"约定速查"段**（写进去），不另起 rules 文件。

## Success Metrics

- 债务池**零无声堆积**：每 change 完成后本 change 新增 OPEN 项 100% 被分诊入批次；`issues/INDEX.md` 被动摊清 open×批次并标 DONE。
- **无第三漂移源**：`INDEX.md` 只由 `reindex` 生成、禁手改；批次状态由 reindex 拿 item 池校验同步（手改状态与成员不一致时被标出纠正）。
- **三维度干净**：status 列不再混入批次；源/批次/target 分家。

## Non-Goals

- **不含连续化**（块1/2 = Phase A 已交付）与**跨模型 outside voice**（块4 = Phase C）。
- **不清空既有 buglist/todolist 债务**（迁移结构即可；债务清理走各自 cleanup change）。
- **不做逾期主动催办**（I12〔grill-amendment〕：判据难定、投机；改被动摊清）。
- **不含消费仓采纳**：各消费仓 `update` 采纳 + 迁移本地债务数据是**下游 routine**，不属本 toolkit change。
- **不另起 rules 文件**（I13：标准归 recorder 约定段，避免第二真相源）。

## Impact

> **本 change 归属 `laodao-skills` 仓**（权威源；umbrella design 原则6 / G6）。

- **自制 skill**：`buglist-recorder`、`todolist-recorder` 脚本增强（路径默认 issues/ + 批次列 + scan 维度 + triage + reindex + batch）+ 各自"约定速查"段写入 issues 标准（I13）+ 测试更新。
- **opsx-done**：落地 issues sweep 步（去掉 A 留的〔Phase B 补〕占位）。
- **workflow bundle 源**：`workflow/workflow.md` 追加 sweep 步引用（ROADMAP 约束1：B 增量改一次）；review UI `workflow/tools/engine.js` + `review.html` 读 issues 新路径。
- **下游消费仓——不在本 change 内，routine 采纳**：`update` 重拉新 bundle + 迁移各自 buglist/todolist → issues/ + 路径引用。各消费仓各自做。
  - ⚠️ **硬切风险 + 加固〔spec-review Q1，provisional〕**：默认路径 `buglists/`→`issues/` 是**破坏性变更**；若下游只 `update`（拉新脚本）而未迁移旧数据，新脚本按新路径 `next_id` 会从 B1 重数、**与旧文件 ID 撞号**，旧 OPEN 债对新 scan **隐形**（违本 change「零无声堆积」）。故 Phase B **必交付过渡期 dual-read**（新旧路径都扫再取 max）+ **ID 撞号检测**，把风险从"寄望下游完整迁移"降到"未迁移也不撞号/不隐形"。完整数据搬迁仍属下游 routine。

## Stakeholders & External Dependencies（TG-20）

- **laodao-skills 是共享 toolkit**：recorder / review skill 改动传导到其它使用它的项目（如嵌入式项目）。issues 目录结构定为 toolkit 新标准（I9）——**需确认其它项目可接受迁移**（承接 umbrella OQ3）。

## Open Questions（TG-21）

- **OQ3（承接 umbrella）**：issues 结构定为 toolkit 新标准 vs 仅本地——需确认其它项目迁移窗口。默认新标准，旧文件无 `批次` 列时兼容留空（I8），降低迁移摩擦。

## Compliance

- 遵守 `rules/destructive-commands.md`：迁移 buglist/todolist、任何 `mv`/删除前走 5 条硬性规则（本仓当前无 issues 数据，主要影响下游消费仓）。
- 遵守"绝不改插件"（升级安全）：定制只在 laodao-skills 权威源 + 消费仓 `config.yaml`。
- workflow bundle 源变更（sweep 步引用）后**同步消费仓走 `update`**；本仓 `openspec/INDEX.md` 若有规则计数变更同步。
- 无 DB schema / API 合约 / Auth 边界改动（纯 process/tooling 变更）。
- **Spec delta**：本 change 向既有能力 `spec-workflow` 追加 **2 条 Requirement**（债务池统一 issues 结构且 INDEX 只生成〔I1/I2/I3〕；批次注册表 + reindex 被动同步状态〔I11/I12/I5/I6〕），归档时并入 `openspec/specs/spec-workflow/`。详细设计见 umbrella design §8，落地见本 change design.md + tasks.md。
