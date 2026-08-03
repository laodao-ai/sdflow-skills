## Overview

将 issues 管理从多条目大文件模型改造为一个 issue 一个文件的单文件模型，同时将三脚本合一。

## Decisions

决策纪要见 [decision-memo.md](./decision-memo.md)。

## 并发安全 [spec-review-amendment]

v2 采用文件名级 `O_CREAT|O_EXCL` 写保护（C8），不需要仓级 `.recorder.lock`：
- `write_issue` 创建新文件时用 `os.open(path, O_WRONLY|O_CREAT|O_EXCL)`，后到者拿到 `FileExistsError` → `next-id` 重试
- v2 单文件模型下，文件名 `{ID}.md` 即互斥粒度；v1 的 participant 嵌套模式（sweep 子步共享锁域）在 v2 不需要（sweep 已砍）
- `set-status` / `reindex` 操作单文件，无跨文件竞争

## YAML 序列化策略 [spec-review-amendment]

沿用 ADR-0025 零依赖原则（C9），不引入 PyYAML：
- frontmatter 写出时值一律双引号包裹：`key: "value"`（内部 `"` → `\"`，`null` 写成字面 `null` 不加引号）
- 读回匹配 `^key: "(.*)"$` 或 `^key: null$`
- schema 只有 12 个扁平 string/null 字段，这是有界语法面，手写完全可控
- 真实语料有 5 个 summary 含 `# ` 或 `: ` 等 YAML 敏感字符（如 T73），双引号包裹封死截断风险

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
3. 自动探测 `source_change`（复用 `detect_change` 逻辑：优先 openspec/changes/ 下唯一目录 → git branch 去前缀 → null）；`--json` 里的 `source_change` 显式传值可覆盖 [spec-review-amendment]
4. 组装 frontmatter（填 `id`, `pool`, `status: OPEN`, `date: today`, `source_change`）
5. 用 `O_CREAT|O_EXCL` 写 `open/{ID}.md`（并发写同 ID 时后到者 FileExistsError → 重试 next-id）[spec-review-amendment]
6. `git add open/{ID}.md`（幂等，非 git 仓时跳过）[spec-review-amendment]
7. 输出创建的文件路径和 ID

### set-status 命令流程

1. `find_issue(id)` 在 `open/` 和 `closed/` 定位文件
2. 校验状态转换合法性（终态不可再改）
3. 校验门禁 [spec-review-amendment]：
   - bug FIXED: 必须有 `--evidence`
   - **todo DONE: 必须有 `--evidence`**（沿用 v1 行为）
   - WONTFIX/WONTDO: 必须有 `--reason`
4. 更新 frontmatter 中的 `status`
5. 追加状态变更历史行到 body：`> {date} 状态：{old} → {new}（{evidence 或 reason}）` [spec-review-amendment]
6. 若新状态为终态：
   - 填 `closed_date`, `resolved_by`（如有）
   - 确保文件已 tracked（`git ls-files --error-unmatch`，未 tracked 则先 `git add`）[spec-review-amendment]
   - `git mv open/{ID}.md closed/{ID}.md`；非 git 仓降级为 `os.rename` [spec-review-amendment]
7. 原子写回（先写 frontmatter+body → 再移文件，部分失败时文件在 open/ 但 status 已更新，reindex 可检测不一致）[spec-review-amendment]

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

**迁移策略** [spec-review-amendment]：
- 读旧文件，**逐 item 去重**（非逐文件二选一）：对每个文件，先收集 legacy 表格行 → 再用 frontmatter overlay items 覆盖（frontmatter 优先），按最终 effective 集合输出。复用 `_build_effective_snapshot` 的 shadow 逻辑
  - 真实语料：`todolist/2026-07-todolist.md` 同时含 152 行 legacy 表格 + 146 个 overlay 项，34 个 ID 两边都有
- 旧文件迁移完成后**不删除**（由用户确认后手动清理，或在 sdflow-done archive 时清理）
- 幂等：已存在的目标文件跳过（按 ID 判重）
- PLANNED 批次信息迁移：34 个 PLANNED 批次的成员/优先级/计划文本搬入对应 issue 的 body（`> [迁移自批次 {batch_key}] 原计划: {plan_text}`）

### 字段映射（v1 → v2）[spec-review-amendment]

| v1 字段 | v2 字段 | 转换规则 |
|---------|---------|---------|
| `status` | `status` | 直接映射 |
| `priority` | `priority` | bug only，todo 置 null |
| `type` | `type` | todo only，bug 置 null |
| `time` | — | 丢弃 |
| `change` | `source_change` | 重命名（语义 = 记录该 issue 时所在的 change，非修复者） |
| `batch` | — | 丢弃（PLANNED 批次的计划文本迁移进成员 issue body） |
| `module` | `module` | 直接映射 |
| `summary` | `summary` | 直接映射 |
| — | `date` | 从文件名提取（buglist: `YYYY-MM-DD`，todolist: `YYYY-MM`→取01） |
| — | `resolved_by` | **不从 `change` 字段取**（那是 source，不是 resolver）；从 body 的状态变更历史行提取（如 `→ FIXED（fix-xxx）` 模式）；提取不到则 null |
| — | `closed_date` | best-effort 从 body 的状态变更历史行（`> {date} 状态：X → Y`）提取终态日期；格式不匹配或不存在则取文件日期（已知不精确的近似值，非结构化保证） |
| — | `closed_reason` | WONTFIX/WONTDO 从 marker block 提取 reason 行（如有） |
| marker block 内容 | body | 原样搬入（去掉 marker 标签） |

**迁移数据约束豁免**：迁移产出的文件不经过 `set-status` 命令，不受 STOR-06 的 evidence/reason 门禁约束——历史数据缺 evidence 或 reason 是已知事实，不阻塞迁移。

### sdflow-done 集成 [spec-review-amendment]

`sdflow-done` 的 sweep 阶段当前调用复合命令 `issues.py --root . sweep --change {change_name}`（内部固化 scan→triage→batch add→reindex，持仓级 `recorder_lock`）。v2 砍掉 batch/triage/sweep 后，改为只读查询：

```bash
python3 issues.py scan --json --source-change {change_name} --status OPEN --status PROPOSED
```

**与 v1 sweep 的差异**：
- v1 sweep 是写操作（triage 打标签 + batch add + reindex）；v2 scan 是只读查询，天然幂等
- v1 hand-off 引批次号（`batches.md` 条目）；v2 hand-off 直接列 ID 列表（每个 ID 即文件名 `open/{ID}.md`，比批次号更直观）
- v1 依赖 `recorder_lock` 并发保护写窗口；v2 scan 只读，不需要锁
- 过滤能力：v2 `scan --source-change` 等价 v1 `scan --change --open-ungrouped`（按来源 change 圈定范围）

输出格式保持 JSON 列表，每项含 `id`, `pool`, `status`, `summary`, `source_change` 等字段。
sdflow-done §2.1 需要重写（不是简单改调用路径），但新版更简单。

### 消费方更新清单 [spec-review-amendment]

| 消费方 | 改动 |
|--------|------|
| `sdflow-issues/SKILL.md` | 命令示例、数据模型、路由逻辑全面更新（拆为两个子任务：数据模型/命令文档 + 路由/触发逻辑） |
| `sdflow-done/SKILL.md` | §2.1 重写——sweep 改为只读 scan + hand-off 改为列 ID |
| `CLAUDE.md` | pytest 命令示例更新 |
| `README.md` | 同上 |
| `hack/tests/test_harden_sdflow_spec_followup_closure.py` | `TODO_SCRIPT` 路径改为 `issues.py` |
| `AGENTS.md` | `openspec/issues/buglist\|todolist/` 路径引用改为 `open/\|closed/` |
| `sdflow-init/assets/snippets/claude-section.md` | 同上（此为推给消费仓的模版） |
| `openspec/CONTEXT.md` | 领域术语更新（三脚本→单脚本、目录结构、终态词表） |
| `openspec/specs/spec-workflow/spec.md` | 补 MODIFIED delta（L210 目录断言、L222 batch/sweep MUST、L333-334 buglist.py Scenario、L95/L660 defer 路径） |
| `openspec/specs/determinism-guards/spec.md` | 补 MODIFIED/REMOVED delta（POOL_SPEC 完备性守卫消解；batch lint 消解；reindex 骤降守卫移植到 v2） |
| `openspec/specs/recorder-root-resolution/spec.md` | 补 MODIFIED delta（三薄入口→单入口；repo_root 逻辑原样移植） |
| `.github/workflows/windows-recorder-smoke.yml` | 更新/退役硬编码测试路径 |

## Compliance

- TG-05（数据对象）：上方 Data Model & Lifecycle 章节覆盖
- TG-14（重构组件）：上方 Component Design 章节覆盖
- TG-23（方案选择）：决策记录在 decision-memo.md
- 其余 TG 不命中
