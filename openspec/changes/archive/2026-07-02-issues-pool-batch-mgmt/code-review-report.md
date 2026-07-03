# code-review-report — issues-pool-batch-mgmt（Phase B）

> 阶段三代码评审留档。方法：subagent-driven-development（16 任务 TDD，逐任务 fresh 子代理实现 + 逐任务 spec+质量双审 + 修复循环）+ **final whole-branch review（opus，附 backend code-checklist 镜）**。

## 结论：ready to merge ✅

- **测试**：160 passed（buglist 35 + todolist 38 + issues 63 … 三包合计），含 reindex 幂等（PYTHONHASHSEED 压测）、端到端三处一致（t16，变异测试验证断言鉴别力）。
- **载重约束逐条实测真守住**（终审核）：三维度分家 · 终态集(bug FIXED/WONTFIX、todo DONE/WONTDO) · D1(0成员防假DONE) · Q2(单批次key=本change+rename+orphan报警) · Q3(只patch生成行/不越权只加⚠️) · dual-read(Q1) · 跨池ID冲突(D9) · 原子写(D6) · 幂等(D7) · 显式--change(D4) · reindex接入sweep(D3)。
- **无硬性 Critical/Important 阻断**。

## 实现期修复循环（逐任务审已闭环）

| 任务 | 修的问题 | 严重度 |
|---|---|---|
| Task 3 | atomic_write 用 mkstemp(0600)+replace 静默收紧文件权限 0644→0600 | Important |
| Task 4 | list_files 整体 sorted(全路径) 使旧目录排新目录前（违"新在前"） | Important |
| Task 5 | todolist 顺序测试 docstring 假保护表述（生产码正确） | Important |
| Task 11 | batches.md 末尾缺换行→⚠️ 粘连人写行+破幂等的数据腐蚀 | **Critical** |
| Task 12 | 约定段"0成员永远PLANNED/DONE不由人标"超前于代码 | Important |
| Task 13 | issues-recorder 无 SKILL.md→setup.sh 不装/下游 sweep 找不到 issues.py；issues.py 不探 git 根 | **Critical** |

全部已修 + 复审确认解决（多数带 stash 回归验证/子目录实测/pre-post 对照）。

## Defer（final-review 非阻断项 → issues/todolist，opsx-done sweep 待 triage）

| ID | 项 | 类型 |
|---|---|---|
| T1 | reindex 回显子进程 scan 的 problems（补齐独立跑 reindex 的表↔块不一致可见性，D5，final-review F1） | 可观测性 |
| T2 | 字段含 `｜` 破 markdown 表：统一转义/拒绝（系统性，pre-existing，未引入新 Critical） | 代码质量 |
| T3 | 终态集跨脚本一致性守卫测试（issues.py TERMINAL_STATUSES ⊆ recorder STATUS_CODES 防漂移） | 代码质量 |
| T4 | batch add --if-exists skip + rename 后自动 reindex | 功能增强 |
| T5 | 补 WONTDO/0成员IN_PROGRESS 分支测试 + 抽 _find_row_file 消除定位重复 | 代码质量 |

## 已裁掉区
空——终审未推翻任何 per-task 结论；累积 Minor 全部逐条裁为"可接受 merge / 记 todo"（见上），无静默丢弃。

## backend code-checklist 镜
CR-BE-01(DB)/CR-BE-02(HTTP) 不适用（纯文件型 Python CLI）；base 层数据工具维度（一致性/幂等/错误处理/原子写/向后兼容/边界）逐条覆盖良好，唯一缺口 = T1（reindex 吞 problems，已记 defer）。
