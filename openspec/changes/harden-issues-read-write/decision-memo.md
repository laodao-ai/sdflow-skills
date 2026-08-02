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

- **D1 读取路径补词表校验，不 _die** — `_legacy_item_from_row` 读 legacy 表时 status/type/priority 超出词表 → `problems.append` 报告，不中止；**砍掉的候选**：_die 中止（= 现状，一条脏行炸全盘）
- **D2 reindex 总项数只增不减守卫** — `_reindex_core` 写盘前读旧 INDEX 总项数（open+closed），新 < 旧 → fail-closed 拒覆盖 exit 非零；**砍掉的候选**：百分比阈值（50%、80%）— 总项数只增不减是精确不变量，百分比有假阳/假漏窗口
- **D3 triage 解耦：batch add 不碰 status** — 删 `_bug_triage` / `_todo_triage` 的 `open_untriaged` 两行，`new_status = old_status`；**砍掉的候选**：保留推状态但改为可选参数 — 过度设计，batch add 语义是「归批次」不是「改状态」
- **D4 不做 §3 normalize** — 已被 `migrate_legacy.py`（de549f4）根治；**砍掉的候选**：本 change 补 normalize — 白做（T231 已明确砍掉）
- **D5 change 名用 `harden-issues-read-write`** — 旧分支 `feat/harden-issues-read-path` 保留（缺陷报告载体），本 change 不接续

## 承重约束

- **C1 改动面 = `sdflow_issues_core/__init__.py` + `issues.py` + 测试** — 验证：grep `_legacy_item_from_row` / `open_untriaged` / `_reindex_core` 消费方全在这两文件内；**证据锚**：`__init__.py:812,892,1797,1836` + `issues.py:604`
- **C2 写入路径（cmd_add / set-status）的 _die 不动** — 验证：cmd_add:1958-1963 的 _die 拒非法写入是正当防护；**证据锚**：`__init__.py:1958-1963`（只读路径才改）
- **C3 总项数只增不减是精确不变量** — 验证：正常操作（add/set-status/batch）只增项或改状态，不删项；reindex 从文件扫描重建，项数降 = 扫描残缺；**证据锚**：B12 实测 57→51 = 6 项消失
- **C4 `open_untriaged` 删除不影响 sweep** — 验证：`issues.py` 的 sweep 不经 triage，直接调 `set-status --to PROPOSED`；**证据锚**：grep `open_untriaged` 只命中 `_bug_triage` / `_todo_triage` 两处

## 接受的边角

- legacy 表里的**历史**脏值不会被自动修复（只显红报告） — 概率/影响/完美成本：脏值在目标态可达但历史数据修复需 migrate_legacy；**为何接受**：显红已足够，修复交 migrate_legacy 已有路径

## 三镜代价

本次无 TG-23 命中。
