# design — dedupe-issues-scripts-shared-layer `[grill-amendment]`

## Context

issues 台账由三个物理脚本承载：`buglist.py`（1814 行）/ `todolist.py`（1788 行）/ `issues.py`（2539 行），共 6141 行。三者的重复分**三层**：

1. **执行逻辑**：bug↔todo 有 77 个同名 `def`、90% 剥 docstring 后 AST 等价（`determinism-guards` 的 TWO_WAY roster）。
2. **共享 helper**：`atomic_write`/`repo_root`/`canonical_id`/`recorder_lock`/整套 frontmatter document mechanics **三份都内联**（THREE_WAY roster）——含 `issues.py`。
3. **台账约定（`SKILL.md` 正文）**：`sdflow-buglist`/`sdflow-todolist` 两份 `SKILL.md` 正文有 133 行（≈58%）逐字相同。

此前靠「物理多份 + AST 等价守」维持一致——每次改动多写、漂移风险常驻，且第 3 层（`SKILL.md` 正文）根本无守。

这三脚本的边界是增量生长的疤（buglist 先造 → todolist 克隆 → issues 后挂做编排器），不是设计出来的 seam。domain model（`CONTEXT.md`「三维度分家」）早已把台账当**一个概念**：一条债务 item、三正交字段、status 词表按 pool 各异——即「一个东西 + 一个 pool 参数」。

## Goals / Non-Goals

**Goals:**
- 三脚本的**三层重复全消**：执行逻辑 + 共享 helper 收敛为唯一物理源 `core.py`；`SKILL.md` 正文合一。
- CLI 逐命令外部行为等价，现有 **603 测试零回归**。
- 三 skill 合并为一个 `sdflow-issues`，owns 整个 issues 台账。

**Non-Goals:**
- 不改数据模型（三态 / versioned frontmatter）、不改台账文件格式、不改 CLI 命令语法与既有触发短语（只改脚本路径前缀）。
- **不改读取路径行为**（= 后置的 `harden-issues-read-path`）。
- **不做 CLI 子命令树重整**（`issues.py bug add …`）——纯审美收益，将来另开 CLI change。

## 设计图（TG-13 C4 Context+Container · 组件/依赖图）

### C4 — Context（系统 ↔ 外部）

```
   ┌───────────┐   记 bug / 记 todo / 跨池      ┌──────────────────────┐
   │  用户 /    │──── /sdflow-issues ──────────▶│  sdflow-issues       │
   │  编排 skill │   (done sweep 调 reindex)     │  (一个 skill·整台账)  │
   └───────────┘                                └──────────┬───────────┘
                                                           │ 读写
                                                   ┌───────▼────────┐
                                                   │ openspec/issues │
                                                   │ dated md + INDEX│
                                                   │ + batches.md    │
                                                   └────────────────┘
```

### C4 — Container（目标态：一个 skill·单一源）

```
  dev repo / 运行 checkout（整目录随 setup.sh symlink）:
   sdflow-issues/
    ├─ SKILL.md              ← 一份，覆盖两池 + 跨池，一个触发面
    └─ scripts/
        ├─ core.py           ← 唯一物理源（THREE_WAY + TWO_WAY 共享逻辑）
        ├─ buglist.py        ← 薄入口：解析 args → 注入 bug POOL_SPEC → 调 core
        ├─ todolist.py       ← 薄入口：todo POOL_SPEC → 调 core
        └─ issues.py         ← 薄入口：跨池 reindex/batch/sweep → 调 core
   [三薄入口同目录 import core·零跨目录 import·零副本·零 sibling 安装]
```

### 组件/依赖图（目标态）

```
              core.py  ── 参数注入 ──▶ POOL_SPEC{ bug | todo }
              ▲  ▲  ▲                  (月/日·目录·字段·词表·终态集)
    同目录 import │  │  │ 同目录 import
   ┌────────────┘  │  └────────────┐
 buglist.py      todolist.py      issues.py
 (bug POOL_SPEC) (todo POOL_SPEC) (跨池；子进程调 buglist/todolist scan --json)
```

## Decisions

### AD-1：三 skill 合一为 `sdflow-issues`，共享逻辑单一物理源

见 `adr/0027`。要点：一个 skill 一个触发面（幸存者 `sdflow-issues`，`sdflow-buglist`/`sdflow-todolist` 目录删除，触发并入）；共享逻辑收敛为唯一 `sdflow-issues/scripts/core.py`；`core` 随整目录 symlink 分发，三薄入口同目录 import——**零跨目录 import、零副本、零 sibling 安装、setup.sh 无需为分发 core 改动**。

撤销独立分发前提的依据、以及对 `determinism-guards` 架构的正式反转，均见 `adr/0027`。

### AD-2：CLI 保三薄入口，命令语法不动

`sdflow-issues/scripts/` 下保 `buglist.py`/`todolist.py`/`issues.py` 三个薄入口（各自解析 args、注入 pool 的 `POOL_SPEC`、调 `core`），命令语法一字不改，**只有路径前缀** `sdflow-buglist/scripts/` → `sdflow-issues/scripts/`。∴「603 零回归」= 机械的路径替换，命令逻辑与断言不动。三薄入口 + 一份 `core` + 一份 `SKILL.md` 与「一个 skill」完全自洽（三入口是实现细节，一个触发面）。

### AD-3：差异经 `POOL_SPEC` 注入，`core` 无 pool 条件分支

bug↔todo 差异收敛为一张参数表 `POOL_SPEC`，`core` 按它取值：

| 差异维 | bug | todo |
|---|---|---|
| 文件粒度 | 日（`file_for_date`/`today_str`） | 月（`file_for_month`/`this_month`） |
| 目录 | `buglists_dir` | `todolists_dir` |
| 特定字段 | `priority` ∈ `PRIORITIES` | `type` ∈ `TYPE_TAGS` |
| 状态词表 | `OPEN/VERIFIED/PROPOSED/IN_PROGRESS/FIXED/WONTFIX/BLOCKED` | `OPEN/PROPOSED/DONE/WONTDO` |
| 终态集 | `{FIXED, WONTFIX}` | `{DONE, WONTDO}` |

`core` 源码 MUST NOT 出现 `if pool == "bug"/"todo"`——差异一律来自 `POOL_SPEC` 取值。若某深层逻辑证伪「差异全可参数化」，则该处保留 `POOL_SPEC` 里的策略钩子（值可为可调用），并在本节记为例外，**不默认整体退回多写**。

### AD-4：`determinism-guards` 守法演进（镜像 AST 守退役）

物理只剩一份 `core.py` ⇒ `determinism-guards` 的「三份剥 docstring AST 等价 + THREE_WAY/TWO_WAY roster」requirement **整体退役**（`test_mirror_consistency.py` 删除）。守法改为守新面：
- `core` 内**无 pool 条件分支**（源码扫描断言）；
- `POOL_SPEC` 对每个 pool 的每个差异维**取值完备**（缺项即红）。

本 change 携带 `determinism-guards` 的 **MODIFIED delta**（见 specs/）。其 `config.yaml` 结构 lint / `batches.md` grammar lint / scan-envelope 校验三条 requirement 与本合并无关，**不动**。

### AD-5：下游托管引用同步（合并的必然连带，fail-closed）

合并 3→1 后，凡引用 `sdflow-buglist`/`sdflow-todolist` 目录名或其脚本路径的托管点，**MUST 同步更新**，否则合并后调用断裂（fail-closed，非可选）：`README.md` skills 列表、`CLAUDE.md`/`AGENTS.md` 配套 skill 表、`sdflow-init/assets/{snippets/claude-section.md, workflow/workflow.md}`（下游铺设面，改后 `sdflow-init update` 推）、`sdflow-done`/`sdflow-ship`(+`ship_gate.py`)/`sdflow-code-review` 里的路径引用、`hack/tests/test_sync_principles.py`（投放面计数 17→15，`sync_principles.py` 已动态枚举、自动少一个）。全部进 tasks.md。

## Risks / Trade-offs

- **[大重构引入行为回归]** → 重构前后 CLI 逐命令行为等价快照 + 603 基线零回归为硬门；分命令渐进迁移，每步跑对应 tests。命令语法不变使回归面收窄为路径替换。
- **[漏改某个下游引用 → 合并后调用断裂]** → AD-5 的引用清单是 fail-closed 必改项；`test_sync_principles.py` 计数门 + 全仓 pytest 兜底暴露漏网。
- **[`SKILL.md` 合并后变大]** → 靠 pool 参数表 + 清晰分节压到 ≈450–550 行；一份大文件 loaded once，替代原三份分别 load。
- **[`POOL_SPEC` 参数化不完全]** → 保留策略钩子的例外口，非整体退回多写；design 记例外。

## Migration Plan

- 纯结构重构 + skill 目录合并，**无数据迁移**（不碰台账文件）。
- 渐进：建 `sdflow-issues/scripts/core.py` 骨架 → 逐命令把 bug/todo 逻辑上移 core + `POOL_SPEC` 注入 → buglist/todolist 壳化并迁入 `sdflow-issues/scripts/` → issues.py 迁入并改用 `import core` → 合并 `SKILL.md` → 删 `sdflow-buglist`/`sdflow-todolist` 目录 → AD-5 下游引用同步 → 镜像 AST 守退役 + 新守法落地 → 全量行为等价 + 603 回归。
- 部署 = 合并后随 setup.sh 生效（orphan 清理回收被删的两个旧 symlink；数据类 skill 改 scripts → 必跑对应 tests）。
- 回滚 = revert change commit + 重跑 setup.sh（恢复三 skill symlink），无残留数据副作用。

## Compliance

- **D-6 架构边界（核心）**：本 change 显式**重评并变更**「独立分发」边界——三 skill 合一、撤销独立分发前提，已由 grill + 设计 HARD-GATE 拍板（见 `adr/0027`），非悄悄改。
- 遵守 `adr/0027`（本 change 的架构决策源）与 `CONTEXT.md`「三维度分家 / 单一源共享 core」——重构不改 item 数据语义。
- **`determinism-guards` 契约演进**：镜像 AST 守退役换为单一源 + `POOL_SPEC` 完备守（AD-4），一致性从「事后拦漂移」升级为「结构上无从漂移」，不降级。
- 遵守 `CLAUDE.md` 基准 4（一个 change 一个完整内聚交付物）——本 change = 「issues 台账统一为一个 skill」一件事；读取路径修复（`harden-issues-read-path`）显式后置、不 fold；AD-5 下游引用同步是合并的**必然连带**（漏改即断裂），属同一交付物、非另一件事。
