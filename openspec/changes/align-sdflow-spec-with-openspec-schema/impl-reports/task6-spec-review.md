---
task: 6
axis: spec
status: BLOCKED
---

# Task 6 Spec 轴复审

## 结论

**BLOCKED**。Task 6 的边界意图大部分已写入 README、canonical workflow、dogfood workflow、roadmap 和 todolist，但当前交付仍有范围未满足及文档副本质量问题：阶段一入口要求的 `CLAUDE.md` 未同步，dogfood workflow 有重复段落/清单，且 Task 6 设计任务要求的安装刷新未完成。

全量 `pytest` 按用户批准跳过，不作为本次阻断理由；该跳过已在 implementer 报告中如实记录，未被标记为通过。

## Acceptance matrix

| Task 6 acceptance | 结论 | 证据 |
|---|---|---|
| 阶段一入口文档说明 project-local schema 与提示层边界 | **BLOCKED** | `sdflow-init/assets/workflow/generation-process.md` 与 `openspec/workflow/generation-process.md` 已新增边界说明，但 `tasks.md:6.1` 明确要求同步 `CLAUDE.md` 阶段一入口段；当前 `CLAUDE.md` 仍无 project-local schema、委派提示层及相关版本/迁移说明。 |
| roadmap P1 标记为已交付 | PASS | `openspec/roadmaps/openspec-1.7.0-followup/roadmap.md` 顶部 P1 表格及 P1 小节均标为“已交付（本 change）”，同时保留全量 pytest 未作为放行证据的说明。 |
| fork 漂移无机械门记录到 todolist，且本 change 不实现该能力 | PASS | `openspec/issues/todolist/2026-07-todolist.md` 已新增 T264，明确记录一次性 fork、无 drift 检测/自动 rebase；roadmap 亦保留该遗留边界，未扩展到 P2/P3。 |
| 文档中的 schema、委派、fallback、迁移顺序与 ticket 语义一致 | **BLOCKED** | 内容主旨基本一致，但 `openspec/workflow/generation-process.md` 第 67–89 行重复完整插入 schema 边界段，第 143–144 行重复 checklist；这会造成同一规则在 dogfood 副本内重复维护，且与 canonical 文件不一致。 |
| 设计任务 6.4：修改 assets 后重跑安装，验证消费侧不是旧版 | **BLOCKED** | `task6-documentation-boundaries.md` 明确记载 `setup.sh / bundle refresh` 未运行；Task 6 的 `tasks.md:62` 将该项列为 P0。用户批准的是跳过全量 pytest，不等于批准跳过安装刷新。 |

## Scope checks

- README 已说明 schema 的 artifact/dependency/`skip_specs`/delegation 作用、版本门 fallback、先补写后切换配置，以及 fork drift 不在本 change 范围内。
- canonical asset `sdflow-init/assets/workflow/generation-process.md` 与新增边界目标基本一致。
- roadmap 未把本 change 扩展到 P2/P3；T264 的记录与 scope 一致。
- `tickets.md` 未被本轮 implementer 修改，符合“只写实现报告、不开 checkpoint”的现状，但任务勾选仍未形成完成证据。
- `git diff --check` 通过。

## Required fixes before PASS

1. 按 Task 6.1 将 project-local schema、委派仅为提示层、fallback 与迁移顺序的入口说明同步到 `CLAUDE.md`，并核对其与 canonical bundle 不矛盾。
2. 删除 `openspec/workflow/generation-process.md` 中重复的 schema 边界段和重复 checklist，使 dogfood 副本与 canonical 结构一致。
3. 按 Task 6.4 在修改后的 assets 上重新运行安装/刷新流程，验证消费侧使用新 bundle；若环境确实无法完成，须留下命令、退出状态、阻断原因和未覆盖范围，不能把 P0 视为完成。`n