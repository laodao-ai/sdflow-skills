# hand-off — issues-pool-batch-mgmt（Phase B）

> 异步人类再入口 + 下个 change 种子。verify（PASS，证据锚点）之后、archive 之前产出，随归档留档。

## ✅ 完成了什么（已复核锚点存在性，非直搬 verify）

Phase B「issues 债务池与批次管理」全交付，160 测试绿（buglist+todolist+issues 三套），verify PASS 且每条 Requirement 附机验锚点：

- **债务池统一 issues 结构**：`buglist/todolist` 默认路径 → `openspec/issues/{buglist,todolist}/`；三维度分家（源=关联Change 列 / 批次=表**末列** / status 回归干净）；`issues/INDEX.md` 只由 `reindex` 生成 + GENERATED banner + 禁读旧（`issues.py` generate_index_md）。〔spec Req1，锚点见 verify-report〕
- **批次注册表 + reindex 被动同步**：`issues/batches.md` 字段级 grammar（生成行 vs 人写行）；`batch add/set-status/rename`；reindex 终态集判据（bug FIXED/WONTFIX·todo DONE/WONTDO）+ **0 成员保持 PLANNED 防假 DONE（D1）** + orphan 报警不静默 + 不越权只加 ⚠️（Q3）+ 不逾期催办（I12）。〔spec Req2〕
- **加固/机制**：dual-read 新旧路径 + 跨池 ID 冲突检测（Q1/D9）· 原子写保权限（D6）· reindex 幂等（D7，PYTHONHASHSEED 压测）· sweep 显式 --change（D4）· reindex 接入 sweep（D3）。
- **接入**：`opsx-done` sweep 步（去 Phase A 占位）· `workflow.md` sweep 引用（不碰 A / 不预写 C）· 两 recorder 约定段写 issues 标准（I13/D9）· **新建 `issues-recorder/SKILL.md`** 使 setup.sh 全局装（否则下游 sweep 找不到 issues.py，终审 Critical 已修）。

实现期 6 个修复循环全闭环（2 Critical：batches.md 缺尾换行致 ⚠️ 粘连破幂等的数据腐蚀 · issues-recorder 未全局装；4 Important）。

## ⏳ 未完成 / 延后

- **本 change 派生 5 个 defer（已 sweep 入批次 `issues-pool-batch-mgmt`，PLANNED，见 `openspec/issues/batches.md`）**：
  - T1 reindex 回显子进程 scan 的 problems（D5 独立跑 reindex 可见性）〔可观测性〕
  - T2 字段含 `｜` 破 markdown 表统一转义/拒绝（系统性、pre-existing，防位置解析读错列腐蚀）〔代码质量〕
  - T3 终态集跨脚本一致性守卫测试（防 issues.py TERMINAL_STATUSES 与 recorder STATUS_CODES 漂移）〔代码质量〕
  - T4 `batch add --if-exists skip` 幂等 + rename 后自动 reindex〔功能增强〕
  - T5 补 WONTDO/0成员IN_PROGRESS 分支测试 + 抽 `_find_row_file` 消除定位重复〔代码质量〕
- **Q1–Q3 provisional 裁决**（设计门超时按推荐临时裁、后经用户确认 A）：Q1 加固版（dual-read + 撞号检测，已交付）· Q2 保守（单批次 + rename + orphan 报警，已交付）· Q3 精确 patch（已交付）。均已落地，非遗留。

## ▶ 下一阶段建议

1. **开 cleanup change 清批次 `issues-pool-batch-mgmt`**（清 T1-T5）：优先 **T2**（`｜` 转义——虽 pre-existing 但真数据腐蚀风险）+ **T1**（reindex problems 可见性，补 D5 承诺）；T3-T5 次之。
2. **两个已登记的派生 change**（见 `openspec/ROADMAP.md`）：`minimize-repo-footprint`（ADR 0003）· `opsx-ship-orchestrator`（ADR 0004）——均只依赖已 merge 的 Phase A，可随时开。
3. **下游消费仓采纳**：`opsx-project-init update` 重拉 + 迁移各自 buglist/todolist → issues/；dual-read 已兜住"未迁移即撞号/隐形"的硬切风险（proposal Q1 记录）。
