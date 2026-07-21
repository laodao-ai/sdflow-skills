# issues 台账合一：一个 skill、一份共享 `core`，撤独立分发换彻底去重

> 状态：**Accepted**（2026-07-21，grill `dedupe-issues-scripts-shared-layer` 收敛；同日 spec-review 补正守法机械形态与共享源命名）。

issues 台账由三个物理脚本承载——`buglist.py`（1814 行）/ `todolist.py`（1788 行）/ `issues.py`（2539 行）。bug 与 todo 是 ~85% 镜像的双胞胎（**75 个同名 `def`**、剥 docstring 后 AST 等价）；`atomic_write`/`repo_root`/`canonical_id`/整套 frontmatter document mechanics 更是**三份都内联**（`determinism-guards` 的 THREE_WAY roster）。三脚本又各带一份 `SKILL.md`，其正文有 **189 行（≈62%）**逐字相同。

**重复分三层**：① 执行逻辑（代码）② 台账约定（`SKILL.md` 正文）③ 跨脚本共享 helper。此前靠「物理多份 + AST 等价守」维持一致，每次改动多写、漂移风险常驻。

## 决策

**把三个 skill 合并为一个 `sdflow-issues`，owns 整个 issues 台账系统；共享逻辑收敛为唯一命名内部 package `sdflow-issues/scripts/sdflow_issues_core/`。**

1. **一个 skill 一个触发面**。幸存者 = `sdflow-issues`（「issues 台账」是领域正名，它本就 owns `INDEX.md` + `batches.md`）。`sdflow-buglist`/`sdflow-todolist` 目录删除，其触发并入 `sdflow-issues` 的 `SKILL.md`——bug↔todo 的分池分类（「坏了没」）由模型在 skill 内按 `SKILL.md` 判，不再靠选哪个触发在门口押 pool。**误判落错池不可机械恢复**（无 `move` 命令，pre-merge 亦无）→ SKILL.md 给骑墙判定规则 + 记为已知代价，move 命令 defer（design AD-6）。
2. **CLI 表面保三薄入口**。`sdflow-issues/scripts/` 下保留 `buglist.py`/`todolist.py`/`issues.py` 三个薄入口文件，**全部同目录 `from sdflow_issues_core import`**（**唯一命名 package·非裸 `import core`**——避 `sys.modules["core"]` 全局碰撞；薄入口顶部 `sys.path.insert` 令 file-based 测试加载可解，spec-review R4）。命令语法一字不动。**「行为逐命令等价」= 路径前缀替换 + `issues.py` sibling-spawn 常量改同目录 + import 改 package**（**非**「只有路径前缀」那么简单，spec-review R8）。
3. **差异经封闭 schema `POOL_SPEC` 注入，`core` 内无 pool 条件分支**。bug/todo 差异（文件粒度、目录、legacy glob、特定字段、状态词表、终态集、**ID 前缀**、**scan 输出键**）收敛为一张**封闭 schema** 参数表 `POOL_SPEC`；`core` 按它取值，MUST NOT 出现针对 pool 值的条件分支（含 subscript/别名/三元/match/dict-dispatch），**禁任意 callable 逃生口**（那会让「差异全可参数化」不可证伪，spec-review R3/Q2）；策略钩子须命名 + 限签。
4. **零分发机制**。共享 package 就住在这个 skill 目录内，随整目录 symlink 分发；三薄入口同目录 import，**无跨目录 import、无副本、无 sibling 安装、setup.sh 无需为分发 core 改动**（只靠既有 orphan 清理回收被删的两个旧 symlink；`OUR_LEGACY_NAMES` 保留旧名用于 Windows legacy marker 清理）。

## 这是对 `determinism-guards` 架构的正式反转（而非「旧代码写错了」）

`determinism-guards` 的目标态明文写着：三份 recorder「各自内联一份」共享 helper、`测试 MUST NOT 抽公共运行时模块或建立 recorder 间 import`（D4 隔离）。**那个决策在它的前提下是对的**——前提是「每个 skill 必须独立分发、可单装」。

本决策**撤销该前提**：这三个 skill 相互关联、恒一起安装，「单装一个」不是真实场景。前提一撤，「各自内联 + AST 守」失去理由，「抽一份共享 `core`」成为可行且更优解。∴：

- `determinism-guards` 的「镜像 helper AST 等价」requirement 及其 THREE_WAY/TWO_WAY roster **整体退役**（物理只剩一份 `core`，没有任何东西需要保持同步——一致性从「事后拦漂移」升级为「结构上无从漂移」）。
- 一致性守法改为守**新面**：`core` 内无 pool 条件分支（**AST 级、诚实标 best-effort 代理**——字面 `if pool==` 子串扫描漏 subscript/别名/三元/match/dict-dispatch，spec-review R2）+ `POOL_SPEC` **封闭 schema 完备 + 关系正确性**（`terminal_set⊆statuses`，spec-review R3）+ **薄入口 thinness 同一性守**（helper `__module__=='sdflow_issues_core'`，防 shadow，spec-review R9）。这不是「守法降级」，是被守对象从「多份是否一致」变成了「单份是否被参数化污染 / 被薄入口 shadow」。**诚实边界**：源码扫描是辅助代理、非机械充要，真正不变量由 POOL_SPEC 封闭 schema 正面保证（基准 5）。
- **`direct↔scan` golden 降级为接线守**（spec-review R6）：合一后两 code-path 跑同一 `core` parser ⇒「一方漏 rule」结构不可能、自比自己 = tautology ⇒ 不再宣称抓 rule 遗漏，降级为守「同源两 code-path 接线正确」；真 rule-完整性守须 core-parse vs 外部 golden fixture。
- 一致性**零回归门用覆盖判据**（node-id manifest allowlist + 全 subcommand 触达），**非 `≥603` 魔数**（魔数被删 7 个 mirror 测试证伪：603−7+2=598<603，spec-review R5）。
- `determinism-guards` 中与本合并无关的守（`config.yaml` 结构 lint、`batches.md` grammar lint、scan-envelope fail-closed 校验）**不受影响**。
- **下游连带**（spec-review R1）：合一牵动 `.github/workflows/windows-recorder-smoke.yml`（CI 必红）+ 两份主 spec（`recorder-root-resolution`/`spec-workflow` 带 MODIFIED delta）+ `test_setup_sdflow.py` + 三 prose SKILL 引用 + `issues.py` sibling 常量——全部 fail-closed 必改，由机械引用守卫（allowlist）兜底。反向：`sdflow-ship`/`sdflow-code-review` 的「defer 进 buglist/todolist **池**」指池目录（不合并）、`setup.sh` `OUR_LEGACY_NAMES` 旧名——**不改**。

> 判据锚**目标态**：问的是「合一后的 producer 会不会再产出漂移」（答：结构上不能），不是「现存三份现在漂没漂」。拿「AST 守现在拦得住」论证「不必合一」，是拿现状给目标松绑（`adr/0011` 目标态论证）。

## Considered Options

- **一个 skill + 单一源 package `sdflow_issues_core` + 三薄入口（选中）**：三层重复全消；零分发机制；回归面 = 路径替换 + spawn 常量改同目录 + import 改 package。代价：`SKILL.md` 合并后变大（三份去重 ≈ 450–550 行）；触发面从三塌一（用户可见），但这三个 skill 本就相互关联、无人单装。**共享源用唯一命名 package 而非裸 `core.py`**（spec-review R4：裸 `core` 有 `sys.modules["core"]` 全局碰撞 + file-based 测试加载脆性——同目录 import 并**不**天然免疫，起草期「同目录 import 根本不产生 import 脆性」的判断被 spec-review 证伪）。
- **保三 skill、只共享 `core.py`（安装期字节复制进各 skill）**〔起草期候选 (a')〕：未选。它为「每 skill 自含、可单装」而生，但**独立分发一撤，副本的唯一理由消失**——既然恒一起装，就该共享同一物理文件，不该每 skill 一份生成副本（还带来「仓内生成物的 git 归属」新问题）。且它只消一层重复（代码），留下 `SKILL.md` 正文重复不碰。
- **保三 skill、共享 `core` 走跨目录 import / sys.path 注入**〔起草期候选 (a)〕：未选。引入运行期跨目录 import 路径脆性（`__file__` 解析、装配依赖）——合一后同目录 package import 免掉**跨目录**部分（但仍需唯一命名 + sys.path 处理应对模块名碰撞与 file-based 加载，见选中项）。
- **一个 skill + 内部 cohesive package（recorder/document/locking/ledger/policies 子模块）+ 三 wrapper**〔spec-review 补议，Codex G7/R10〕：**方向认可但本 change 显式 defer**。它解决「单一源 ≠ 单一巨型文件」（避免数千行 god module）+ 消掉 issues 自调用子进程，但属**内部再分层 + 子进程→import 重构**，超出本 change「消三层重复」的内聚交付物边界（基准 4）。`sdflow_issues_core` 起步为单 `__init__.py`，拆子模块记 todo（design AD-7）。
- **维持现状（三份 + AST 守）**：未选 = 不做本 change。AST 守只事后拦漂移、不免除多写，且不碰 `SKILL.md` 正文重复。
- **CLI 塌成一个 `issues.py` 子命令树**（`issues.py bug add …`）：未选（至少不在本 change）。最终 CLI 更干净，但命令语法全改 → 每个 caller 与每条测试的调用串重写，把零回归从「换路径」放大到「换语法」。纯审美收益，值将来另开一个 CLI change，不塞进去重 change。
