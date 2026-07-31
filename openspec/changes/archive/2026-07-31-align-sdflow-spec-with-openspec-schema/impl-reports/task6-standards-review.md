---
task: 6
axis: standards
verdict: BLOCKED
---

# Task 6 Standards 轴复审

## 范围与结论

只读核验了 `task6-documentation-boundaries.md`、`task6-brief.md`、`tickets.md` 的 Task 6、`tasks.md` 的 6.1–6.4、`design.md`、当前 diff、README、roadmap、issues INDEX，以及 canonical/dogfood `generation-process.md`。

结论：**BLOCKED**。

用户已批准跳过全量 `pytest`；该批准不覆盖 Task 6.4 要求的安装/ bundle 刷新门。

## 已通过

- `README.md` 已记录 project-local schema 的职责、提示层委派边界、版本门 fallback、迁移顺序和 fork 漂移限制。
- `openspec/roadmaps/openspec-1.7.0-followup/roadmap.md` 已将 P1 标为已交付，并保留 P2/P3 未开。
- T264 已写入 todolist，`openspec/issues/INDEX.md` 已出现 `T264 | todo | PROPOSED | align-sdflow-spec-with-openspec-schema`。
- canonical `sdflow-init/assets/workflow/generation-process.md` 已加入作用边界段和检查项。
- `git diff --check` 通过。
- 未发现 `openspec/issues/batches.md` 的内容 diff；其工作树状态属于现有索引/批次文件的工作树变化，不作为本 Task 6 阻断项。

## 阻断项

### S1：dogfood workflow 出现重复文档块

文件：`openspec/workflow/generation-process.md`

当前文件中：

- `### project-local schema 的作用边界` 出现 2 次（canonical 仅 1 次）；
- `project-local schema 已通过版本门吗？...` 检查项出现 2 次（canonical 仅 1 次）。

这不是 canonical → dogfood 的合法生成差异，而是 dogfood 文档的重复内容，违反单一上下文布局与同步要求。应删除重复块/重复检查项，使 dogfood 与 canonical 的新增语义各出现一次。

### S2：Task 6.4 安装刷新门未完成

`tasks.md` 的 6.4 要求修改 `sdflow-init/assets/` 后重跑一次安装，因为 hook/bundle 是 copy 安装而非 symlink。`task6-documentation-boundaries.md` 明确记录 `setup.sh / bundle refresh` 未运行，且直接手工同步了 dogfood copy。

因此当前没有本次 canonical 变更经过正常安装刷新后的证据。全量 pytest 的批准不能替代该 P0 安装门；在 S1 修正后仍需运行安装刷新并核验 canonical/dogfood 结果。

## 复审边界

- 本轮未运行全量 `pytest`，按用户批准处理，未将其标绿。
- 本轮未修改实现文件；仅写入本报告。
- 在 S1、S2 关闭并重新核验前，不应将 Task 6 判为 PASS，也不应推进 Task 7 收尾。
