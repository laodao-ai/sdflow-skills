---
schema_version: 1
change: harden-issues-read-write
branch: feat/harden-issues-read-write
generated_at: 2026-08-02T12:36:14+00:00
decision_hash: ec484c3a2be1
---

# 决策纪要 · harden-issues-read-write

## 目标态

issues 读取路径词表校验（显红不罢工）+ reindex 写盘前骤降 fail-closed + triage 解耦不强推状态。

## 拍板决策

- **D1 读取路径两层同步词表校验，不中止** [spec-review-amendment] — core 层 `_build_effective_snapshot` + consumer 边界 `validate_scan_envelope` 两处同步降级：超出词表 → `problems.append` 报告，不 raise/不 _die；**砍掉的候选**：只改 core 不改 consumer（= `validate_scan_envelope` 仍硬 raise，reindex CLI 路径未修）
- **D2 reindex 总项数只增不减守卫（两段式解析）** [spec-review-amendment] — `_reindex_core` 写盘前用两段式解析读旧 INDEX 总项数（open 表格行数 + "共 N 项已闭合"聚合行的 N），新 < 旧 → fail-closed 拒覆盖 exit 非零；**砍掉的候选**：① 只数 `| T/B` 行 — INDEX.md 的 closed 项只有聚合摘要行不逐行渲染，只数表格行 = 只数 open，量纲对不上"总项数"，guard 结构性偏松（设计审 R2）② 百分比阈值 — 总项数只增不减是精确不变量，百分比有假阳/假漏窗口 ③ 旁路状态文件 — 无现成信号源需新建，成本高于两段式反解析且引入新状态文件生命周期管理
- **D3 sweep 路径 triage 状态解耦：--batch-only flag** [spec-review-amendment] — `_bug_triage`/`_todo_triage` 加 `promote` 参数（默认 True），`triage` CLI 新增 `--batch-only` flag（`promote=False`），`cmd_sweep` 改用 `triage --batch-only`；**砍掉的候选**：① 直接删 `open_untriaged` — triage 的"赋批次+推进状态"是 SKILL.md 正式契约（:494-496），直接删会改变 triage 命令本身的语义 + 静默改变 sweep 行为 + SKILL.md 三处过期 + todo marker block 补建副作用（设计审 R3/R5/R9）② "只改 cmd_batch_add" — cmd_batch_add 本来就不碰 status（纯注册表操作），此方案基于错误前提
- **D4 不做 §3 normalize** — 已被 `migrate_legacy.py`（de549f4）根治；**砍掉的候选**：本 change 补 normalize — 白做（T231 已明确砍掉）
- **D5 change 名用 `harden-issues-read-write`** — 旧分支 `feat/harden-issues-read-path` 保留（缺陷报告载体），本 change 不接续

## 承重约束

- **C1 改动面 = `sdflow_issues_core/__init__.py` + `issues.py` + `SKILL.md` + 测试** [spec-review-amendment] — 验证：grep `_legacy_item_from_row` / `open_untriaged` / `_reindex_core` / `validate_scan_envelope` 消费方全在这两文件内；`SKILL.md` 需同步更新 triage 文档。**证据锚**：`__init__.py:812,826-901,1797,1836` + `issues.py:437-440,604,1126-1132`
- **C2 写入路径（cmd_add / set-status）的 _die 不动** — 验证：cmd_add:1958-1963 的 _die 拒非法写入是正当防护；**证据锚**：`__init__.py:1958-1963`（只读路径才改）
- **C3 总项数只增不减是精确不变量** — 验证：正常操作（add/set-status/batch）只增项或改状态，不删项；reindex 从文件扫描重建，项数降 = 扫描残缺；**证据锚**：B12 实测 57→51 = 6 项消失
- **C4 sweep 经 triage 子命令间接复用 `_bug_triage`/`_todo_triage`** [spec-review-amendment] — 验证：`cmd_sweep`（`issues.py:1126-1132`）对每个待分诊项通过子进程调用 `triage --id --批次`，路由到 `_bug_triage`/`_todo_triage`。`--batch-only` flag 使 sweep 路径的 `promote=False`（不推进状态），直接 triage 保持 `promote=True`（原行为不变）。**证据锚**：`issues.py:1126-1132`（sweep 调 triage 子命令）+ grep `open_untriaged` 只命中 `_bug_triage` / `_todo_triage` 两处

## 接受的边角

- legacy 表里的**历史**脏值不会被自动修复（只显红报告） — 概率/影响/完美成本：脏值在目标态可达但历史数据修复需 migrate_legacy；**为何接受**：显红已足够，修复交 migrate_legacy 已有路径

## 三镜代价

本次无 TG-23 命中。
