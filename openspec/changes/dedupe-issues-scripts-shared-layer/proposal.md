# dedupe-issues-scripts-shared-layer

> **触发判定（TG，起手一次性）**：**TG-06 ⚠️HR**（跨模块共享数据模型边界：重评并变更 D-6「独立分发」边界，三 skill 合一 + 共享 `core`）·
> TG-10（跨 3+ 组件：三脚本 + setup.sh + 下游编排器）· TG-13（大改架构：三 skill 合一）· TG-14（新组件 `core.py` + 重构）·
> TG-18（测试计划：603 零回归 + 新守法）· TG-19（多条需求）· TG-23（≥2 方案 → `adr/0027`）。
>
> **HR-TG 命中非空 {TG-06}** ⇒ spec-review 规划镜头 MUST 单开领域 cross-model。

## Why

**issues 台账三脚本（`buglist.py`/`todolist.py`/`issues.py`，共 6141 行）的重复分三层，且没有一层被真正消除、只被『事后守』：**

1. **执行逻辑**：bug↔todo 有 77 个同名 `def`、90% 剥 docstring 后 AST 等价。
2. **共享 helper**：`atomic_write`/`repo_root`/`canonical_id`/整套 frontmatter mechanics **三份都内联**（含 `issues.py`）。
3. **台账约定**：`sdflow-buglist`/`sdflow-todolist` 两份 `SKILL.md` 正文 133 行（≈58%）逐字相同——**这一层根本无守**。

现状靠「物理多份 + `determinism-guards` 的 AST 等价守」维持一致：每次改动多写、漂移风险常驻。**AST 守只事后拦漂移、不免除多写**，且只覆盖第 1、2 层，不碰第 3 层。

**为什么现在做**：这三脚本的边界是增量生长的疤（buglist 先造 → todolist 克隆 → issues 后挂编排器），不是设计 seam。domain model（`CONTEXT.md`「三维度分家」）早已把台账当**一个概念**（一 item、三正交字段、status 词表按 pool 各异 = 一个东西 + 一个 pool 参数）。三 skill 相互关联、恒一起装，「单装一个」从不真实发生——**独立分发这个约束一撤，就该合一，让重复从『多份保持一致』变成『物理上无从漂移』。**

## What Changes

- **三 skill 合并为一个 `sdflow-issues`**（owns 整个 issues 台账：两池记录 + 跨池 reindex/batch/sweep）。`sdflow-buglist`/`sdflow-todolist` 目录删除，触发短语并入 `sdflow-issues` 单份 `SKILL.md`；一个触发面 `/sdflow-issues`，bug↔todo 分池分类由模型在 skill 内按「坏了没」判。
- **共享逻辑收敛为唯一物理源** `sdflow-issues/scripts/core.py`（THREE_WAY + TWO_WAY 全收）；bug/todo 差异经一张 `POOL_SPEC` 参数表注入，`core` 内 MUST NOT 有 `if pool` 条件分支。
- **CLI 保三薄入口**：`buglist.py`/`todolist.py`/`issues.py` 三个薄入口留在 `sdflow-issues/scripts/`，同目录 `import core`；**命令语法一字不改，只改路径前缀**（`sdflow-buglist/scripts/` → `sdflow-issues/scripts/`）。**零跨目录 import、零副本、零 sibling 安装、setup.sh 无需为分发 core 改动**（只靠既有 orphan 清理回收被删的两个旧 symlink）。603 测试零回归。
- **BREAKING（脚本路径）**：调用方引用的脚本路径前缀变更（`sdflow-buglist`/`sdflow-todolist` → `sdflow-issues`）。凡引用旧目录名/路径的托管点（`README`/`CLAUDE.md`/`AGENTS.md`/`sdflow-init` 铺设面/`sdflow-done`·`sdflow-ship`(+`ship_gate.py`)·`sdflow-code-review`/`test_sync_principles.py` 计数）MUST 同步——漏改即合并后调用断裂（fail-closed）。
- **`determinism-guards` 守法演进**：镜像 AST 守（三向/两向 roster）退役（`test_mirror_consistency.py` 删除——物理只剩一份，无对象），换为「`core` 无 pool 分支 + `POOL_SPEC` 完备」；scan-envelope 校验 / golden 等价 / `config.yaml` lint / `batches.md` lint 不受影响。

## Capabilities

### New Capabilities
- `issues-scripts-shared-core`: 三 skill 合一为 `sdflow-issues` · 共享逻辑单一物理源 `core` + `POOL_SPEC` 注入 · CLI 三薄入口逐命令等价零回归 · 下游托管引用同步。

### Modified Capabilities
- `determinism-guards`: 镜像 helper AST 等价守（THREE_WAY/TWO_WAY roster）退役 → 换为单一源 + 无 pool 分支 + `POOL_SPEC` 完备守；D4 隔离条款随合一改写（同目录 `import core` 是目标架构、非违规）。config/batch/scan-envelope 三守不动。

## 可证伪假设

- **A1（差异全可参数化）**：bug↔todo 的全部差异可经 `POOL_SPEC` 注入、无需 `core` 内 pool 分支。**证伪信号**：某深层逻辑无法参数化 → 该处保留 `POOL_SPEC` 策略钩子并记为例外，**不默认整体退回多写**。
- **A2（行为逐命令等价可达）**：合一为纯结构变换、外部行为不变。**证伪信号**：某命令输出（JSON/落盘字节/退出码）合一前后不等 → 阻断，非交付。
- **A3（下游引用面已枚举全）**：AD-5 清单覆盖所有活跃托管引用点。**证伪信号**：合一后全仓检索仍有活跃点引用旧目录 / pytest 因漏改而红。
