# Task 4：T141 收口（issues 池状态与证据链闭合）

## 做了什么

1. 用本仓（开发 checkout）的 `sdflow-issues/scripts/issues_v2.py`（MUST NOT 用 `~/.claude/skills` 下指向运行 checkout 的旧版 symlink，已按纪律避开）执行：
   ```
   python3 sdflow-issues/scripts/issues_v2.py set-status --id T141 --to DONE --evidence "拆分标准单一源：sdflow-init/assets/workflow/reference/change-decomposition-standard.md（4规则+why，Task 1 新建）；三处引用：sdflow-init/assets/workflow/ff-generation-constraints.md:44 + spec-checklists/spec-quality-base.md BASE-18/BASE-31、sdflow-roadmap/SKILL.md:215、sdflow-spec/references/scope-cohesion-check.md、sdflow-implement/SKILL.md:647、sdflow-code-review/SKILL.md:405（Task 2/3 落地）"
   ```
   输出：`{"id": "T141", "pool": "todo", "old": "OPEN", "new": "DONE", "file": "openspec/issues/closed/todo/T141.md"}`，退出码 0。
   `resolved_by` 由脚本 `detect_change()` 自动探测——`openspec/changes/` 下当时有两个未归档目录
   （`add-frontend-checklists` + `harden-ticket-slicing`，非唯一）⇒ 落到分支名去前缀这条路径：
   `feat/harden-ticket-slicing` → `harden-ticket-slicing`，与本 change 名一致，无需手工干预。

2. **编排层补充发现并要求修复**：脚本只维护 frontmatter，issue 正文里的**遗留静态属性表**
   （`| 状态 | ... |` 行，第 21 行）不在 `sdflow-issues/scripts/` 任何代码的维护范围内
   （已 grep 确认零命中）。写入时该行仍留着旧值 `OPEN`，与 frontmatter 的 `status: "DONE"`
   矛盾，且直接违反本票验收标准第 1 条「T141 状态由 OPEN 变为 DONE」（读者可见的状态字段
   也要一致）。对照已关闭 issue（如 `closed/todo/T1.md:21`）确认惯例是该行同步写 `DONE`。
   已手工把该行改为 `| 状态 | DONE |`（只改一个词，未动表格其余内容、未动正文其它段落、
   未碰任何其它 issue 文件）。

## T141 改后 frontmatter 全文

```yaml
---
id: "T141"
pool: "todo"
status: "DONE"
priority: null
type: "基础设施"
date: "2026-07-01"
source_change: null
module: "`workflow bundle (roadmap/ff/spec-review/implement/code-review)`"
summary: "把「拆分标准=一个change一个完整阶段结果」融入 workflow 三处触发"
resolved_by: "harden-ticket-slicing"
closed_date: "2026-08-19"
closed_reason: null
---
```

## 正文 evidence 注记原文 + 表格状态行（改后）

```
| 属性 | 值 |
|------|------|
| 模块 | `workflow bundle (roadmap/ff/spec-review/implement/code-review)` |
| 类型 | 基础设施 |
| 状态 | DONE |

...

> 2026-08-19 状态：OPEN → DONE（拆分标准单一源：sdflow-init/assets/workflow/reference/change-decomposition-standard.md（4规则+why，Task 1 新建）；三处引用：sdflow-init/assets/workflow/ff-generation-constraints.md:44 + spec-checklists/spec-quality-base.md BASE-18/BASE-31、sdflow-roadmap/SKILL.md:215、sdflow-spec/references/scope-cohesion-check.md、sdflow-implement/SKILL.md:647、sdflow-code-review/SKILL.md:405（Task 2/3 落地））
```

## 核验

1. `ls openspec/issues/open/todo/ | grep T141` → exit 1（不在 open 池）；`ls openspec/issues/closed/todo/ | grep T141` → 命中（在 closed 池）。
2. `/usr/bin/python3 -m pytest sdflow-issues/tests/ -q`：
   ```
   ........................................................................ [ 57%]
   ...............................................ssssss.                   [100%]
   120 passed, 6 skipped in 10.61s
   ```
   退出码 0。
3. `/usr/bin/python3 -m pytest -q`（全仓，前台跑完拿退出码，未丢后台等通知）：
   ```
   2601 passed, 10 skipped in 375.81s (0:06:15)
   ```
   退出码 0。

## Concerns

- **发现记录**：issue 正文的静态属性表「状态」字段是**遗留手写字段**，`sdflow-issues/scripts/`
  没有任何代码同步它（grep 全仓 `sdflow-issues/scripts/*.py` 零命中该表格结构）。本次是手工
  按已关闭 issue 的惯例同步的。这不属于 Task 4 的 scope（Non-Goals 明确「不引入切片建议的机械
  格式校验」，且本票 Global Constraints 要求 `ship_gate.py` 及一切机械层脚本零改动），故未去
  给脚本补一个「同步该表格」的写路径——如后续想让这个字段不再依赖手工同步，建议另开 todo。
