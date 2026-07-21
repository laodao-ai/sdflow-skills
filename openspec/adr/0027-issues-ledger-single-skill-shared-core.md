# issues 台账合一：一个 skill、一份共享 `core`，撤独立分发换彻底去重

> 状态：**Accepted**（2026-07-21，grill `dedupe-issues-scripts-shared-layer` 收敛）。

issues 台账由三个物理脚本承载——`buglist.py`（1814 行）/ `todolist.py`（1788 行）/ `issues.py`（2539 行）。bug 与 todo 是 90% 镜像的双胞胎（77 个同名 `def`、剥 docstring 后 AST 等价）；`atomic_write`/`repo_root`/`canonical_id`/整套 frontmatter document mechanics 更是**三份都内联**（`determinism-guards` 的 THREE_WAY roster）。三脚本又各带一份 `SKILL.md`，其正文有 133 行（≈58%）逐字相同。

**重复分三层**：① 执行逻辑（代码）② 台账约定（`SKILL.md` 正文）③ 跨脚本共享 helper。此前靠「物理多份 + AST 等价守」维持一致，每次改动多写、漂移风险常驻。

## 决策

**把三个 skill 合并为一个 `sdflow-issues`，owns 整个 issues 台账系统；共享逻辑收敛为唯一物理源 `sdflow-issues/scripts/core.py`。**

1. **一个 skill 一个触发面**。幸存者 = `sdflow-issues`（「issues 台账」是领域正名，它本就 owns `INDEX.md` + `batches.md`）。`sdflow-buglist`/`sdflow-todolist` 目录删除，其触发并入 `sdflow-issues` 的 `SKILL.md`——bug↔todo 的分池分类（「坏了没」）由模型在 skill 内按 `SKILL.md` 判，不再靠选哪个触发在门口押 pool。
2. **CLI 表面保三薄入口**。`sdflow-issues/scripts/` 下保留 `buglist.py`/`todolist.py`/`issues.py` 三个薄入口文件，**全部同目录 `import core`**。命令语法一字不动（`buglist.py add …` 仍是 `buglist.py add …`），只有路径前缀从 `sdflow-buglist/` 变为 `sdflow-issues/`。∴「行为逐命令等价」缩为机械的路径替换，回归面最小。
3. **差异经 `POOL_SPEC` 注入，`core` 内无 pool 条件分支**。bug/todo 的差异（文件粒度月/日、目录、特定字段 `type`/`priority`、状态词表、终态集）收敛为一张参数表 `POOL_SPEC`；`core` 按它取值，MUST NOT 出现 `if pool == "todo"/"bug"`——那只是把镜像换成条件分叉，未真正消重。
4. **零分发机制**。共享 `core.py` 就住在这个 skill 目录内，随整目录 symlink 分发；三薄入口同目录 import，**无跨目录 import、无副本、无 sibling 安装、setup.sh 无需为分发 core 改动**（只靠既有 orphan 清理回收被删的两个旧 symlink）。

## 这是对 `determinism-guards` 架构的正式反转（而非「旧代码写错了」）

`determinism-guards` 的目标态明文写着：三份 recorder「各自内联一份」共享 helper、`测试 MUST NOT 抽公共运行时模块或建立 recorder 间 import`（D4 隔离）。**那个决策在它的前提下是对的**——前提是「每个 skill 必须独立分发、可单装」。

本决策**撤销该前提**：这三个 skill 相互关联、恒一起安装，「单装一个」不是真实场景。前提一撤，「各自内联 + AST 守」失去理由，「抽一份共享 `core`」成为可行且更优解。∴：

- `determinism-guards` 的「镜像 helper AST 等价」requirement 及其 THREE_WAY/TWO_WAY roster **整体退役**（物理只剩一份 `core`，没有任何东西需要保持同步——一致性从「事后拦漂移」升级为「结构上无从漂移」）。
- 一致性守法改为守**新面**：`core` 内无 pool 条件分支 + `POOL_SPEC` 各 pool 取值完备（缺项即红）。这不是「守法降级」，是被守对象从「多份是否一致」变成了「单份是否被参数化污染」。
- `determinism-guards` 中与本合并无关的守（`config.yaml` 结构 lint、`batches.md` grammar lint、scan-envelope fail-closed 校验）**不受影响**。

> 判据锚**目标态**：问的是「合一后的 producer 会不会再产出漂移」（答：结构上不能），不是「现存三份现在漂没漂」。拿「AST 守现在拦得住」论证「不必合一」，是拿现状给目标松绑（`adr/0011` 目标态论证）。

## Considered Options

- **一个 skill + 单一源 `core` + 三薄入口（选中）**：三层重复全消；零分发机制；回归面 = 路径替换。代价：`SKILL.md` 合并后变大（三份去重 ≈ 450–550 行）；触发面从三塌一（用户可见），但这三个 skill 本就相互关联、无人单装。
- **保三 skill、只共享 `core.py`（安装期字节复制进各 skill）**〔起草期候选 (a')〕：未选。它为「每 skill 自含、可单装」而生，但**独立分发一撤，副本的唯一理由消失**——既然恒一起装，就该共享同一物理文件，不该每 skill 一份生成副本（还带来「仓内生成物的 git 归属」新问题）。且它只消一层重复（代码），留下 133 行 `SKILL.md` 正文重复不碰。
- **保三 skill、共享 `core` 走跨目录 import / sys.path 注入**〔起草期候选 (a)〕：未选。引入运行期 import 路径脆性（`__file__` 解析、装配依赖）——这是 `determinism-guards` D4 当初要躲的失败模式，合一后同目录 import 根本不产生它。
- **维持现状（三份 + AST 守）**：未选 = 不做本 change。AST 守只事后拦漂移、不免除多写，且不碰 `SKILL.md` 正文重复。
- **CLI 塌成一个 `issues.py` 子命令树**（`issues.py bug add …`）：未选（至少不在本 change）。最终 CLI 更干净，但命令语法全改 → 每个 caller 与每条测试的调用串重写，把零回归从「换路径」放大到「换语法」。纯审美收益，值将来另开一个 CLI change，不塞进去重 change。
