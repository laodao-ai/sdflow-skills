## ADDED Requirements

### Requirement: 三 skill 合并为一个 `sdflow-issues` `[grill-amendment]`

issues 台账的 `buglist`/`todolist`/`issues` 三个 skill SHALL 合并为**一个 skill `sdflow-issues`**，owns 整个 issues 台账（两池记录 + 跨池 reindex/batch/sweep）。`sdflow-buglist`/`sdflow-todolist` 目录 MUST 删除，其触发短语并入 `sdflow-issues` 的单份 `SKILL.md`。合并后 MUST 只有**一个触发面 `/sdflow-issues`**；bug↔todo 的分池分类由模型在 skill 内按 `SKILL.md` 判定，不再由「选哪个 skill 触发」在门口决定 pool。

理由：三脚本边界是增量生长的疤、非设计 seam；domain model（`CONTEXT.md`「三维度分家」）早已把台账当一个概念（一 item、三正交字段、status 词表按 pool 各异）。合一同时消掉执行逻辑、共享 helper、`SKILL.md` 正文三层重复。见 `adr/0027`。

#### Scenario: 只有一个 skill 目录与触发面

- **WHEN** 合并完成后检查 `~/.claude/skills/` 与 `~/.codex/skills/`
- **THEN** 存在 `sdflow-issues`，**不存在** `sdflow-buglist`/`sdflow-todolist`（被删源的孤儿 symlink 由 setup.sh orphan 清理回收）
- **AND** 台账相关触发只解析到 `sdflow-issues` 一个 skill

### Requirement: 共享逻辑收敛为唯一物理源 `core`，差异经 `POOL_SPEC` 注入 `[grill-amendment]`

三条 CLI 共享的执行逻辑（THREE_WAY 的 `atomic_write`/`repo_root`/frontmatter mechanics 等 + TWO_WAY 的 bug↔todo 镜像）SHALL 收敛为**唯一物理源** `sdflow-issues/scripts/core.py`。bug/todo 的差异（文件粒度月/日、目录、特定字段 `type`/`priority`、状态词表、终态集）MUST 经一份**参数表 `POOL_SPEC`** 注入；`core` 源码 MUST NOT 含 `if pool == "bug"/"todo"` 式的 pool 条件分支——差异一律来自 `POOL_SPEC` 取值。

#### Scenario: 共享逻辑只有一处物理源

- **WHEN** 需要修改一条 bug/todo/issues 共有的命令逻辑
- **THEN** 存在**唯一**物理编辑源 `core.py`，无需在多处镜像修改
- **AND** 台账脚本顶层不再存在承载该逻辑的同名镜像函数对（度量：同名 `def` 交集大幅归零）

#### Scenario: pool 差异经 POOL_SPEC 注入、非条件分支

- **WHEN** `core` 需要 pool 特定值（文件粒度 / 目录 / 词表 / 终态集 / 特定字段）
- **THEN** 该值取自注入的 `POOL_SPEC`，`core` 源码中不出现 pool 名的条件分支

### Requirement: CLI 保三薄入口、命令语法不动、逐命令等价零回归 `[grill-amendment]`

`sdflow-issues/scripts/` SHALL 保留 `buglist.py`/`todolist.py`/`issues.py` **三个薄入口文件**，各自解析 args、注入 pool 的 `POOL_SPEC`、**同目录 `import core`**；MUST NOT 存在跨目录 import、副本、或 sibling 安装。各 CLI 命令的输入输出 MUST 与合并前**逐命令等价**，命令语法（子命令、参数）MUST 不变——**只有脚本路径前缀** `sdflow-buglist/scripts/` → `sdflow-issues/scripts/` 改变。现有 **603 passed 基线 MUST 零回归**。

#### Scenario: 运行期无跨目录 import、无副本

- **WHEN** 检查三个薄入口的 import
- **THEN** 共享逻辑经**同目录** `import core` 获得；不存在指向另一目录的 import，也不存在 `core` 的物理副本

#### Scenario: CLI 行为等价（仅路径前缀变）

- **WHEN** 对合并前后版本运行同一组命令（含 `add`/`scan --json`/`set-status`/`triage`/`reindex`/`batch`）于同一输入
- **THEN** 输出（stdout JSON、落盘文件字节、退出码）逐命令等价；调用差异仅为脚本路径前缀

#### Scenario: 测试基线零回归

- **WHEN** 合并完成后运行全仓 `pytest`
- **THEN** 通过数 ≥ 603（原基线），无 FAILED、无因重构导致的 skip

### Requirement: 下游托管引用同步（合并的必然连带） `[grill-amendment]`

合并 3→1 后，凡引用 `sdflow-buglist`/`sdflow-todolist` 目录名或其脚本路径的托管点 MUST 同步更新至 `sdflow-issues`（fail-closed，非可选——漏改即合并后调用断裂）：`README.md`、`CLAUDE.md`/`AGENTS.md`、`sdflow-init/assets/{snippets/claude-section.md, workflow/workflow.md}`、`sdflow-done`/`sdflow-ship`(+`ship_gate.py`)/`sdflow-code-review`、`hack/tests/test_sync_principles.py` 的投放面计数（17→15）。

#### Scenario: 无残留旧路径引用

- **WHEN** 合并完成后全仓检索 `sdflow-buglist`/`sdflow-todolist` 目录名或脚本路径
- **THEN** 除历史归档（`openspec/changes/archive/`）外，无活跃托管点仍引用旧目录；`test_sync_principles.py` 投放面计数与实际 `SKILL.md` 数一致
