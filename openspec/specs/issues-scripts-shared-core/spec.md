# issues-scripts-shared-core Specification

## Purpose

`sdflow-buglist`/`sdflow-todolist`/`sdflow-issues` 三个 skill 合并为单一 `sdflow-issues`（`adr/0027`）后，
三条 CLI 薄入口（`buglist.py`/`todolist.py`/`issues.py`）共享的执行逻辑收敛为**唯一命名 package**
`sdflow-issues/scripts/sdflow_issues_core/`。本能力管辖：该 package 的存在与命名约束（禁裸模块名
`core`）、bug/todo 差异经封闭 schema `POOL_SPEC` 注入（禁 `core` 内条件分支）、三薄入口经同目录
import 获得同一实现且命令语法/行为逐命令等价、以及合并后对全仓活跃托管点引用的机械守卫兜底。
## Requirements
### Requirement: 三 skill 合并为一个 `sdflow-issues` `[grill-amendment]`

issues 台账的 `buglist`/`todolist`/`issues` 三个 skill SHALL 合并为**一个 skill `sdflow-issues`**，owns 整个 issues 台账（两池记录 + 跨池 reindex/batch/sweep）。`sdflow-buglist`/`sdflow-todolist` 目录 MUST 删除，其触发短语并入 `sdflow-issues` 的单份 `SKILL.md`。合并后 MUST 只有**一个触发面 `/sdflow-issues`**；bug↔todo 的分池分类由模型在 skill 内按 `SKILL.md` 判定，不再由「选哪个 skill 触发」在门口决定 pool。

理由：三脚本边界是增量生长的疤、非设计 seam；domain model（`CONTEXT.md`「三维度分家」）早已把台账当一个概念（一 item、三正交字段、status 词表按 pool 各异）。合一同时消掉执行逻辑、共享 helper、`SKILL.md` 正文三层重复。见 `adr/0027`。

#### Scenario: 只有一个 skill 目录与触发面

- **WHEN** 合并完成后检查 `~/.claude/skills/` 与 `~/.codex/skills/`
- **THEN** 存在 `sdflow-issues`，**不存在** `sdflow-buglist`/`sdflow-todolist`（被删源的孤儿 symlink 由 setup.sh orphan 清理回收）
- **AND** 台账相关触发只解析到 `sdflow-issues` 一个 skill

### Requirement: 共享逻辑收敛为唯一命名 package `sdflow_issues_core`，差异经封闭 schema `POOL_SPEC` 注入 `[grill-amendment]` `[spec-review-amendment]`

三条 CLI 共享的执行逻辑（THREE_WAY 的 `atomic_write`/`repo_root`/frontmatter mechanics 等 + TWO_WAY 的 bug↔todo 镜像）SHALL 收敛为**唯一命名内部 package** `sdflow-issues/scripts/sdflow_issues_core/`（**MUST NOT** 用裸模块名 `core`——避免全局 `sys.modules["core"]` 碰撞）。bug/todo 的差异 MUST 经一份**封闭 schema 参数表 `POOL_SPEC`** 注入；`POOL_SPEC` SHALL 为封闭 dataclass/TypedDict，required 维 = 类型字段全集，至少含：文件粒度（月/日）、目录、**legacy dir glob**、特定字段（`type`/`priority`）、状态词表、终态集、**ID 前缀 `DEFAULT_PREFIX`（B/T）**、**scan 输出键（`bugs`/`items`）**——新增维 MUST 改 schema（不得硬编码进 core / argparse default / callable 逃生）。`core` 源码 MUST NOT 含针对 pool 值（`"bug"`/`"todo"`）的条件分支——差异一律来自 `POOL_SPEC` 取值。

#### Scenario: 共享逻辑只有一处物理源

- **WHEN** 需要修改一条 bug/todo/issues 共有的命令逻辑
- **THEN** 存在**唯一**物理编辑源 package `sdflow_issues_core`，无需在多处镜像修改
- **AND** 台账薄入口顶层不再存在承载该逻辑的同名镜像函数对；且 THREE_WAY/TWO_WAY 名单每个 helper 从薄入口 `getattr` 解析的对象 `__module__ == 'sdflow_issues_core'`（thinness 同一性守，未被 shadow）

#### Scenario: pool 差异经 POOL_SPEC 注入、非条件分支

- **WHEN** `core` 需要 pool 特定值（文件粒度 / 目录 / legacy glob / 词表 / 终态集 / 特定字段 / 前缀 / scan 键）
- **THEN** 该值取自注入的 `POOL_SPEC`，`core` 源码中不出现针对 pool 值的条件分支（含 subscript/别名/三元/match/dict-dispatch 形态）

#### Scenario: POOL_SPEC 封闭 schema + 关系正确性

- **WHEN** 校验 `POOL_SPEC`
- **THEN** 缺任一 required 维即红；`terminal_set ⊆ 状态词表`，值与 `RECORDER_POOL_CONFIG` 现值一致（非只 non-None）
- **AND** `POOL_SPEC.keys()` fail-closed 断言 `== {"bug","todo"}`（额外 key 即红），或跨池 consumer roster 从同一 registry 派生

### Requirement: CLI 保三薄入口、命令语法不动、逐命令等价、覆盖判据零回归 `[grill-amendment]` `[spec-review-amendment]`

`sdflow-issues/scripts/` SHALL 保留 `buglist.py`/`todolist.py`/`issues.py` **三个薄入口文件**，各自解析 args、注入 pool 的 `POOL_SPEC`、**同目录 `from sdflow_issues_core import ...`**（MUST NOT 跨目录 import、副本、sibling 安装）。为令 file-based 测试加载（`importlib.spec_from_file_location`，不设 sys.path）下 package import 可解，薄入口顶部 MUST 显式 `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`（或测试改 package-aware 加载）——二者择一，测试策略 MUST 明确。各 CLI 命令的输入输出 MUST 与合并前**逐命令等价**，命令语法 MUST 不变；除脚本路径前缀外，`issues.py` 的运行期 sibling-spawn 常量（`SKILLS_ROOT`/`BUGLIST_SCRIPT`/`TODOLIST_SCRIPT`）MUST 重写为同目录定位。零回归 MUST 由**覆盖判据**守护，**MUST NOT** 用 `通过数 ≥ N` 魔数（该魔数被本 change 删除 mirror 测试证伪）。

#### Scenario: 运行期无跨目录 import、无副本、无 sys.modules 碰撞

- **WHEN** 检查三个薄入口的 import
- **THEN** 共享逻辑经**同目录**唯一命名 package `from sdflow_issues_core import` 获得；不存在跨目录 import、`core` 物理副本、或裸模块名 `core`（避 `sys.modules["core"]` 碰撞）

#### Scenario: CLI 行为等价（含 sibling-spawn 常量重写）

- **WHEN** 对合并前后版本运行同一组命令（含 `add`/`scan --json`/`set-status`/`triage`/`reindex`/`batch` **及 `next-id`/`sweep`/`batch add|set-status|rename` 全 argparse subcommand**）于同一输入
- **THEN** 输出（stdout JSON、落盘文件字节、退出码）逐命令等价；`reindex`/`sweep` 的子进程 spawn 走**同目录**常量、不指向已删 sibling 目录

#### Scenario: 覆盖判据零回归（非计数魔数）

- **WHEN** 合并完成后
- **THEN** 冻结的 pre-refactor pytest node-id manifest 中，除 **allowlist**（`test_mirror_consistency.py` 的 7 个测试）外每个 node 仍存在且 pass；argparse 注册的**全部** subcommand（含 `next-id`/`sweep`）migration 后逐一有测试触达；行为等价快照为**留存 param 化测试**（非丢弃的一次性快照）；无 FAILED、无因重构导致的 skip

### Requirement: 下游托管引用同步（合并的必然连带·机械守卫兜底） `[grill-amendment]` `[spec-review-amendment]`

合并 3→1 后，凡引用 `sdflow-buglist`/`sdflow-todolist` 目录名 / 脚本路径 / slash 触发名的**活跃托管点** MUST 同步更新（fail-closed——漏改即调用断裂/CI 打红/主 spec 死路径）：`README.md`、`CLAUDE.md`/`AGENTS.md`、`sdflow-init/assets/{snippets/claude-section.md, workflow/workflow.md}`、`sdflow-init/SKILL.md`、`sdflow-done/SKILL.md`（语义块重写）、`ship_gate.py`、`sdflow-retro`/`sdflow-implement`/`sdflow-init` SKILL.md 的 slash prose、`issues.py` 的 sibling-spawn 常量、`.github/workflows/windows-recorder-smoke.yml`（path-trigger + 测试调用）、`sdflow-init/tests/test_setup_sdflow.py` 的安装断言、`hack/tests/test_sync_principles.py` 投放面计数（**17→15，少两个**）；两份主 spec（`recorder-root-resolution`、`spec-workflow`）MUST 携带 **MODIFIED delta**（见本 change specs/）。**MUST NOT** 改动：`sdflow-ship`/`sdflow-code-review` SKILL.md 的「defer 进 buglist/todolist **池**」（指池目录、不合并）、`setup.sh` 的 `OUR_LEGACY_NAMES` 旧名（Windows legacy marker 清理依赖）。全仓引用完整性 MUST 由**机械守卫 test（allowlist）**守护，非只靠人工 sweep。

#### Scenario: 机械引用守卫（allowlist 兜底）

- **WHEN** 合并完成后跑全仓引用守卫
- **THEN** 除 allowlist（`openspec/changes/archive/`、历史 `adr/`、issue ledger `openspec/issues/*`、`setup.sh` `OUR_LEGACY_NAMES`、**整个在途活跃 change 目录 `openspec/changes/{active}/**`**——含四件套 + specs delta + 评审产物 `spec-review-report.md`/`gstack-review.md`/`.outside-voice/`、池目录名 `openspec/issues/buglist|todolist/`）外，无活跃托管点仍引用旧 skill 目录/脚本路径/slash 名，否则 FAIL
- **AND** `test_sync_principles.py` 投放面计数与实际 `SKILL.md` 数一致（15）

#### Scenario: CI 与安装测试同步

- **WHEN** 合并完成
- **THEN** `windows-recorder-smoke.yml` 的 path-trigger 与测试调用指向 `sdflow-issues`（不再 hard-fail）；`test_setup_sdflow.py` 断言 setup 后建 `sdflow-issues` 链、旧目录已 orphan 清理

