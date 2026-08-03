## Overview

将 issues 管理从多条目大文件模型改造为一个 issue 一个文件的单文件模型，同时将三脚本合一。

## Decisions

决策纪要见 [decision-memo.md](./decision-memo.md)。

## Data Model & Lifecycle (TG-05)

### 目录结构

```
openspec/issues/
├── open/           ← 每个活跃 issue 一个 .md
│   ├── B25.md
│   ├── T257.md
│   └── ...
├── closed/         ← 每个已关闭 issue 一个 .md
│   ├── B1.md
│   ├── T2.md
│   └── ...
├── INDEX.md        ← reindex 从 open/ 再生
└── CLOSED.md       ← reindex 从 closed/ 再生
```

### 单文件 schema（frontmatter）

```yaml
---
id: T257
pool: todo                    # todo | bug
status: OPEN                  # OPEN | PROPOSED | FIXED | WONTFIX | DONE | WONTDO
priority: null                # bug only: P1 | P2 | P3
type: null                    # todo only: 基础设施 | 性能优化 | ...（自由文本）
date: "2026-08-03"            # 创建日期
source_change: some-change    # 发现该 issue 的 change（可 null）
module: sdflow-ship           # 涉及模块
summary: "一行摘要"
resolved_by: null             # 修复该 issue 的 change（关闭时填）
closed_date: null             # 关闭日期
closed_reason: null           # WONTFIX/WONTDO 必填
---

自由格式 Markdown body（现象、根因、修复方案等）
```

### 状态生命周期

```
  ┌──────┐     ┌──────────┐     ┌───────────────┐
  │ OPEN │────▶│ PROPOSED │────▶│ FIXED / DONE  │
  └──────┘     └──────────┘     └───────────────┘
      │             │
      │             │           ┌─────────────────┐
      └─────────────┴──────────▶│ WONTFIX / WONTDO│
                                └─────────────────┘

终态触发：文件从 open/ 移到 closed/
非终态回退（如 PROPOSED → OPEN）：文件留在 open/
```

**状态与池的约束**：
- bug: 终态 = FIXED | WONTFIX
- todo: 终态 = DONE | WONTDO
- 脚本按 ID 前缀（B/T）推断 pool，校验终态词表

### ID 分配

- B 系列和 T 系列各自独立编号
- `next-id` 扫 `open/` + `closed/` 全部文件名，取对应前缀的 max+1
- 文件名即 ID：`{ID}.md`

## Component Design (TG-14)

### 脚本架构

```
issues.py（单入口 CLI）
├── cmd_add()           ← 创建新 issue 文件到 open/
├── cmd_set_status()    ← 修改 frontmatter status，终态时 git mv → closed/
├── cmd_scan()          ← 扫描 open/ 和/或 closed/，输出列表
├── cmd_reindex()       ← 再生 INDEX.md + CLOSED.md
├── cmd_next_id()       ← 输出下一个可用 ID
├── cmd_migrate()       ← 一次性从 v1 格式迁移到 v2
└── 内部函数
    ├── read_issue()    ← 读单文件 frontmatter + body
    ├── write_issue()   ← 原子写单文件（.tmp + rename）
    ├── find_issue()    ← 按 ID 在 open/ 和 closed/ 中定位
    └── parse_frontmatter() ← YAML frontmatter 解析
```

**与 v1 的架构差异**：
- 无 `sdflow_issues_core` 包——单文件操作足够简单，无需共享核心
- 无 `POOL_SPEC` 注入模式——pool 差异（终态词表、特有字段）内联为常量
- 无 `buglist.py` / `todolist.py` 薄入口——统一为 `issues.py`
- 无 `triage` / `sweep` 命令——batch 机制已砍

### CLI 接口

```bash
# 添加
python3 issues.py add --pool bug --json '{"module":"sdflow-ship","summary":"...","priority":"P1"}'
python3 issues.py add --pool todo --json '{"module":"sdflow-ship","summary":"...","type":"基础设施"}'

# 改状态（自动从 ID 前缀推断 pool）
python3 issues.py set-status --id B7 --to FIXED --evidence "commit abc123"
python3 issues.py set-status --id T5 --to WONTDO --reason "ROI 太低"

# 查询
python3 issues.py scan                        # 全部 open
python3 issues.py scan --pool bug             # 只看 bug
python3 issues.py scan --status OPEN          # 按状态筛
python3 issues.py scan --all                  # open + closed
python3 issues.py scan --json                 # 机器可读

# 索引再生
python3 issues.py reindex

# 下一个 ID
python3 issues.py next-id --pool bug          # 输出 B24
python3 issues.py next-id --pool todo         # 输出 T265

# 迁移（独立工具）
python3 issues.py migrate --root .
```

### add 命令流程

1. 从 `--json` 读入字段，校验必填（`module`, `summary`, `--pool`）
2. `next-id` 取下一个 ID
3. 组装 frontmatter（填 `id`, `pool`, `status: OPEN`, `date: today`）
4. 原子写 `open/{ID}.md`
5. 输出创建的文件路径和 ID

### set-status 命令流程

1. `find_issue(id)` 在 `open/` 和 `closed/` 定位文件
2. 校验状态转换合法性（终态不可再改）
3. 更新 frontmatter 中的 `status`
4. 若新状态为终态：
   - bug FIXED: 必须有 `--evidence`
   - WONTFIX/WONTDO: 必须有 `--reason`
   - 填 `closed_date`, `resolved_by`（如有）
   - `git mv open/{ID}.md closed/{ID}.md`
5. 原子写回

### reindex 命令

扫描 `open/` 所有 `.md` 文件的 frontmatter，按 ID 排序，生成 INDEX.md 表格：

```markdown
# Issues Index (Open)

| ID | Pool | Status | Date | Module | Summary |
|----|------|--------|------|--------|---------|
| B25 | bug | OPEN | 2026-08-01 | sdflow-ship | ... |
| T258 | todo | PROPOSED | 2026-08-03 | sdflow-issues | ... |
```

CLOSED.md 同理，额外含 `closed_date`, `resolved_by`, `closed_reason` 列。

### migrate 命令

```
v1 文件（buglist/*.md + todolist/*.md）
  │
  ├─ 解析 frontmatter overlay 格式（有 sdflow-issues: items: 的 YAML）
  │   └─ 逐条提取 item → read marker block → 组装 v2 单文件
  │
  ├─ 解析 legacy 表格格式（无 frontmatter，只有 Markdown 表格 + detail block）
  │   └─ 从表格行提取字段 → read detail section → 组装 v2 单文件
  │
  └─ 输出
      ├─ open/{ID}.md    （活跃 issue）
      ├─ closed/{ID}.md  （已关闭 issue）
      └─ 统计报告（迁移数、成功数、跳过数）
```

**迁移策略**：
- 读旧文件，逐条解析，写新文件
- 旧文件迁移完成后**不删除**（由用户确认后手动清理，或在 sdflow-done archive 时清理）
- 幂等：已存在的目标文件跳过（按 ID 判重）

### 字段映射（v1 → v2）

| v1 字段 | v2 字段 | 转换规则 |
|---------|---------|---------|
| `status` | `status` | 直接映射 |
| `priority` | `priority` | bug only，todo 置 null |
| `type` | `type` | todo only，bug 置 null |
| `time` | — | 丢弃 |
| `change` | `source_change` | 重命名 |
| `batch` | — | 丢弃 |
| `module` | `module` | 直接映射 |
| `summary` | `summary` | 直接映射 |
| — | `date` | 从文件名提取（buglist: `YYYY-MM-DD`，todolist: `YYYY-MM`→取01） |
| — | `resolved_by` | 已关闭 issue 取 `change` 字段（如有） |
| — | `closed_date` | 已关闭 issue 取 status 变更日志的最后日期（如有），否则取文件日期 |
| — | `closed_reason` | WONTFIX/WONTDO 从 marker block 提取 reason 行（如有） |
| marker block 内容 | body | 原样搬入（去掉 marker 标签） |

### sdflow-done 集成

`sdflow-done` 的 sweep 阶段当前调用 `buglist.py scan --json` + `todolist.py scan --json`。
v2 改为单调用：

```bash
python3 issues.py scan --json --status OPEN --status PROPOSED
```

输出格式保持 JSON 列表，每项含 `id`, `pool`, `status`, `summary`, `source_change` 等字段。

### 消费方更新清单

| 消费方 | 改动 |
|--------|------|
| `sdflow-issues/SKILL.md` | 命令示例、数据模型、路由逻辑全面更新 |
| `sdflow-done/SKILL.md` | sweep 调用路径改为 `issues.py scan` |
| `CLAUDE.md` | pytest 命令示例更新 |
| `README.md` | 同上 |
| `hack/tests/test_harden_sdflow_spec_followup_closure.py` | `TODO_SCRIPT` 路径改为 `issues.py` |

## Compliance

- TG-05（数据对象）：上方 Data Model & Lifecycle 章节覆盖
- TG-14（重构组件）：上方 Component Design 章节覆盖
- TG-23（方案选择）：决策记录在 decision-memo.md
- 其余 TG 不命中
