# Tasks — plan-workflow-cost-optimization

## 范围说明

本变更交付物 = 产出 `openspec/roadmaps/workflow-cost-optimization/` roadmap 文档包。实际实施由未来独立变更按阶段分解驱动（P1=✅ 已交付 `adaptive-workflow-routing`；P0/P2a/P2b/P3/P4 待开）。

## 1. 归档 / 整理
- [x] 1.1 无废弃文档需处置（roadmap 目录新建）

## 2. 产出 roadmap 文档包
- [x] 2.1 `openspec/roadmaps/workflow-cost-optimization/requirements.md`
- [x] 2.2 `openspec/roadmaps/workflow-cost-optimization/design.md`
- [x] 2.3 `openspec/roadmaps/workflow-cost-optimization/roadmap.md`
- [x] 2.4 `openspec/roadmaps/workflow-cost-optimization/task-log.md`
- [x] 2.5 `openspec/roadmaps/workflow-cost-optimization/memo.md`（强制：讨论 >30 轮）

## 3. 交叉 review（✅ 完成）
- [x] 3.1 把 4 件套作为整体 plan 说明给 review skill（roadmap.md 主入口，引 requirements/design；task-log 不审）
- [x] 3.2 跑 `/plan-eng-review`（取其实质：codex 冷模型 outside voice + 四维工程审）
- [x] 3.3 review 所有 issue 列入 `task-log.md` 「## Review 处置」，每条标 ✅采纳/⚪裁掉(带理由)/⏭延后（30 条去重 15 组：9 采纳 / 3 延后 / 3 裁掉）
- [x] 3.4 确认「## Review 处置」无「未处置」条目（已核）

## 4. 交叉引用
- [x] 4.1 CLAUDE.md「OpenSpec 双重角色」段补 `openspec/roadmaps/{name}/` 目录角色行（原只提 sdflow-roadmap skill、无目录角色）

## 5. 归档本变更
- [x] 5.1 `/opsx:archive plan-workflow-cost-optimization`（回填 2026-08-20：本 change 现位于 `openspec/changes/archive/`，归档动作已完成）
