# dedupe-issues-scripts-shared-layer

> **触发判定（TG，起手一次性）**：**TG-06 ⚠️HR**（跨模块共享数据模型边界：重评并变更 D-6「独立分发」边界，三 skill 合一 + 共享 `core`）·
> TG-10（跨 3+ 组件：三脚本 + setup.sh + 下游编排器）· TG-13（大改架构：三 skill 合一）· TG-14（新组件 `sdflow_issues_core` package + 重构）·
> TG-18（测试计划：603 零回归 + 新守法）· TG-19（多条需求）· TG-23（≥2 方案 → `adr/0027`）。
>
> **HR-TG 命中非空 {TG-06}** ⇒ spec-review 规划镜头 MUST 单开领域 cross-model。

## Why

**issues 台账三脚本（`buglist.py`/`todolist.py`/`issues.py`，共 6141 行）的重复分三层，且没有一层被真正消除、只被『事后守』：**

1. **执行逻辑**：bug↔todo 有 **75 个同名 `def`、~85% 剥 docstring 后 AST 等价**〔spec-review-amendment：接地镜实测 75/85.3%，原「77/90%」偏乐观〕。
2. **共享 helper**：`atomic_write`/`repo_root`/`canonical_id`/整套 frontmatter mechanics **三份都内联**（含 `issues.py`）。
3. **台账约定**：`sdflow-buglist`/`sdflow-todolist` 两份 `SKILL.md` 正文 **189 行（≈62%）**逐字相同——**这一层根本无守**〔spec-review-amendment：接地镜实测 189/61.6%，原「133/58%」低报实际重复〕。

现状靠「物理多份 + `determinism-guards` 的 AST 等价守」维持一致：每次改动多写、漂移风险常驻。**AST 守只事后拦漂移、不免除多写**，且只覆盖第 1、2 层，不碰第 3 层。

**为什么现在做**：这三脚本的边界是增量生长的疤（buglist 先造 → todolist 克隆 → issues 后挂编排器），不是设计 seam。domain model（`CONTEXT.md`「三维度分家」）早已把台账当**一个概念**（一 item、三正交字段、status 词表按 pool 各异 = 一个东西 + 一个 pool 参数）。三 skill 相互关联、恒一起装，「单装一个」从不真实发生——**独立分发这个约束一撤，就该合一，让重复从『多份保持一致』变成『物理上无从漂移』。**

## What Changes

- **三 skill 合并为一个 `sdflow-issues`**（owns 整个 issues 台账：两池记录 + 跨池 reindex/batch/sweep）。`sdflow-buglist`/`sdflow-todolist` 目录删除，触发短语并入 `sdflow-issues` 单份 `SKILL.md`；一个触发面 `/sdflow-issues`，bug↔todo 分池分类由模型在 skill 内按「坏了没」判。
- **共享逻辑收敛为唯一物理源** `sdflow-issues/scripts/sdflow_issues_core/`（**唯一命名内部 package**，THREE_WAY + TWO_WAY 全收）；bug/todo 差异经一张**封闭 schema** `POOL_SPEC` 参数表注入，`core` 内 MUST NOT 有针对 pool 值的条件分支〔spec-review-amendment Q1：从裸 `core.py` 改唯一命名 package，避免 `sys.modules["core"]` 全局碰撞 + 令测试的 file-based 加载显式，见 design AD-1/AD-2〕。
- **CLI 保三薄入口**：`buglist.py`/`todolist.py`/`issues.py` 三个薄入口留在 `sdflow-issues/scripts/`，`from sdflow_issues_core import ...`（同目录 package，非裸模块名）；**命令语法一字不改**——但**路径前缀变更 + `issues.py` 内部 sibling-spawn 常量须重写为同目录**（非「只有前缀」，见 AD-2）。**零跨目录 import、零副本、零 sibling 安装、setup.sh 无需为分发 core 改动**（只靠既有 orphan 清理回收被删的两个旧 symlink）。零回归门以**覆盖判据**（node-id manifest + 全 subcommand 触达）守、非 `≥603` 魔数〔spec-review-amendment：见 A2/AD-4〕。
- **BREAKING（脚本路径 + slash 触发面）**：调用方引用的脚本路径前缀变更（`sdflow-buglist`/`sdflow-todolist` → `sdflow-issues`）**且用户可见 slash `/sdflow-buglist`·`/sdflow-todolist` 删除**。凡引用旧目录名/脚本路径/slash 名的**活跃托管点** MUST 同步（fail-closed，漏改即断裂）——完整清单 + 由**机械引用守卫（allowlist）**兜底，见 AD-5。⚠️ **含本地 pytest 照不到的 `.github/workflows/windows-recorder-smoke.yml` CI + 两份主 spec（须带 MODIFIED delta）+ `test_setup_sdflow.py` + 三 prose SKILL 引用**；反向，`sdflow-ship`/`sdflow-code-review` 的「defer 进 buglist/todolist **池**」指池目录（不合并）**无需改**。
- **`determinism-guards` 守法演进**：镜像 AST 守（三向/两向 roster）退役（`test_mirror_consistency.py` 删除——物理只剩一份，无对象），换为「`core` 无 pool 分支（**AST 级、诚实标 best-effort 代理**）+ `POOL_SPEC` **封闭 schema 完备 + 关系正确性**（`terminal_set⊆statuses` 等）+ **薄入口 thinness 同一性守**」；`config.yaml` lint / `batches.md` lint 不受影响。⚠️ **direct↔scan golden 合一后降级**为「同源两 code-path 接线守」——**不再是 rule-omission 守**（同 core parser 自比自己 = tautology，见 AD-4/R6）。

## Capabilities

### New Capabilities
- `issues-scripts-shared-core`: 三 skill 合一为 `sdflow-issues` · 共享逻辑单一物理源 `core` + `POOL_SPEC` 注入 · CLI 三薄入口逐命令等价零回归 · 下游托管引用同步。

### Modified Capabilities
- `determinism-guards`: 镜像 helper AST 等价守（THREE_WAY/TWO_WAY roster）退役 → 换为单一源 + 无 pool 分支（AST 级·best-effort）+ `POOL_SPEC` 封闭 schema 完备 + 关系正确性守 + 薄入口 thinness 同一性守；golden 降级为接线守（非 rule-omission）；D4 隔离条款随合一改写（同目录 package import 是目标架构、非违规）。config/batch 守不动。
- `recorder-root-resolution`〔spec-review-amendment R1〕: 三 recorder 路径引用由 `sdflow-buglist`/`sdflow-todolist` sibling 路径更新为 `sdflow-issues/scripts/` 同目录（root-resolution 语义不变，仅路径字面随合一同步）。
- `spec-workflow`〔spec-review-amendment R1〕: RENAME-MAP 的 skill 名枚举 requirement + 其 trigger/路径解析 Scenario 随 `sdflow-buglist`/`sdflow-todolist` 删除而**修订**（skill 已不存在——枚举与场景更新，非静默 grep 替换）。

## 可证伪假设

- **A1（差异全可参数化）**：bug↔todo 的全部差异可经 `POOL_SPEC`（**封闭 schema**）注入、无需 `core` 内 pool 分支。**证伪信号**：某差异既不在 schema 声明维、又无法纯数据化 → 记为**命名 + 限定签名的策略钩子例外**（禁任意 callable），**不默认整体退回多写**。⚠️ **完备守只查 presence 不够**（spec-review R3）：schema 须**封闭**（新增维必须改 schema）+ 对可枚举维加**值正确性**断言（`terminal_set⊆statuses`、与 `RECORDER_POOL_CONFIG` 现值一致）+ 补漏项维（`DEFAULT_PREFIX` 前缀 / scan 输出键 / legacy dir glob）；`POOL_SPEC.keys()` fail-closed 断言 `=={"bug","todo"}` 或令 consumer roster 从同一 registry 派生。
- **A2（行为逐命令等价可达）**：合一为纯结构变换、外部行为不变。**证伪信号**：某命令输出（JSON/落盘字节/退出码）合一前后不等 → 阻断，非交付。⚠️ **零回归门形态**（spec-review R5）：`≥603` 魔数被本 change 删 7 个 mirror 测试证伪（603−7+2=598<603，必卡红或逼灌水）⇒ 改**覆盖判据**——冻结 node-id manifest（allowlist 只许删 `test_mirror_consistency.py` 7 个）+ 断言 argparse 全 subcommand（**含 `next-id`/`sweep` 跨池命令**）migration 后逐一有测试触达 + 等价快照改**留存 param 化测试**。
- **A3（下游引用面已枚举全）**：AD-5 清单 + **机械引用守卫（allowlist）**覆盖所有活跃托管引用点。**证伪信号**：合一后全仓检索仍有活跃点引用旧 skill 目录/脚本路径/slash 名 / pytest 或 CI 因漏改而红。⚠️ **原清单不全**（spec-review R1，已补）：漏 CI workflow、两主 spec delta、`test_setup_sdflow.py`、三 prose SKILL、`issues.py` sibling 常量；反向 overclaim `sdflow-ship`/`sdflow-code-review`（池名概念、非路径引用）。
