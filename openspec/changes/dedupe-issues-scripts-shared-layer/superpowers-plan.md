---
impl-pipeline: tickets
---

## Global Constraints

> 以下条款逐字摘自本 change `design.md` 的 MUST / MUST NOT / SHALL 硬约束与 Compliance 节，
> 作为每个 implementer / reviewer 子代理的共享注意力透镜。**Spec 轴以 ticket 声明的目标态判定，
> 不以"现有代码本来就这样"松绑。**

### 架构反转（D-6，已由 grill + 设计 HARD-GATE 拍板）

- 本 change 显式**重评并变更**「独立分发」边界——三 skill 合一、撤销独立分发前提，已由 grill + 设计
  HARD-GATE 拍板（见 `adr/0027`），非悄悄改。
- 遵守 `adr/0027`（本 change 的架构决策源）与 `CONTEXT.md`「三维度分家 / 单一源共享 core」——重构不改
  item 数据语义。
- 遵守 `CLAUDE.md` 基准 4（一个 change 一个完整内聚交付物）——本 change =「issues 台账统一为一个 skill」
  一件事；读取路径修复（`harden-issues-read-path`）显式后置、不 fold；god-module 拆子模块 + move 命令
  （AD-6/AD-7）显式 defer；AD-5 下游引用同步（含 CI/主 spec delta）是合并的**必然连带**（漏改即断裂），
  属同一交付物、非另一件事。

### 唯一命名 package + 测试加载策略（AD-1 / R4）

- 用**唯一命名内部 package** `sdflow_issues_core/`（起步单 `__init__.py`），三薄入口
  `from sdflow_issues_core import ...`。裸模块名 `core` 共享全局 `sys.modules["core"]`——别处先加载同名
  模块时薄入口拿错 `core`；唯一命名消该碰撞。
- **测试加载策略 MUST 声明**：多数测试用 `importlib.util.spec_from_file_location()` 按文件加载、不设
  `sys.path`——∴ 薄入口顶部 MUST 显式 `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`
  后再 import package（或测试改 package-aware 加载）；二者择一，spec 钉死（SC-R3 Scenario）。

### CLI 零回归的真实构成（AD-2 / R8）

- 「零回归」**不是**「机械的路径替换」——`issues.py:66-69` 的运行期 sibling-spawn 常量
  `SKILLS_ROOT`/`BUGLIST_SCRIPT`/`TODOLIST_SCRIPT` **MUST 重写为同目录**
  `os.path.join(SCRIPT_DIR, "buglist.py")`，其承重注释（`issues.py:59-65` 明写「siblings」前提）
  **MUST 重写**去掉已作废的 sibling 前提（DOC-1）。∴「零回归」= 路径前缀替换 **+ 内部 spawn 常量改
  同目录 + import 机制改 package**，命令**输入输出**逻辑与断言不动。

### POOL_SPEC 封闭 schema + 禁任意 callable（AD-3 / Q2 / R3）

- `POOL_SPEC` 定义为**封闭 dataclass/TypedDict**，required 维 = 类型字段全集——**新增维必须改 schema**。
- 对可枚举维加**值正确性**断言：`terminal_set ⊆ 状态词表`、`POOL_SPEC` 值与 `RECORDER_POOL_CONFIG`
  现值一致（非只 non-None）。`POOL_SPEC.keys()` **fail-closed 断言 `== {"bug","todo"}`**（额外 key 即红）。
- `core` 源码 **MUST NOT** 出现针对 pool 值（`"bug"`/`"todo"`）的条件分支——差异一律来自 `POOL_SPEC`
  取值。若某深层逻辑证伪「差异全可参数化」，**MUST NOT** 塞进任意 callable 逃生口（那会让守卫永不失败、
  把重复从 core 挪进策略函数、不可证伪）；须保留为**命名 + 限定签名的策略钩子**，逐个记为例外 + 说明为何
  不能数据化 + 对 bug/todo 各跑同一 contract suite，**不默认整体退回多写**。

### 守法诚实边界（AD-4 / R2 / R6）

- 无 pool 分支守 **MUST NOT** 用字面 `if pool == "bug"` 子串扫描（真实分岔有 subscript、别名、三元、
  `match`、dict-dispatch 五形态，字面扫必漏）。改 **AST 级**：拦 `If`/`IfExp`/`Match`/`Compare` 右操作数
  ∈ `{"bug","todo"}` 且左操作数解析到 pool 值（含别名）+ mutation test 证守卫对 `expected_pool=="bug"`、
  `document["pool"]=="bug"` 反红。**且 spec MUST 诚实声明此扫描是 best-effort 代理、非 fail-closed 充要
  保证**（真正的不变量由 POOL_SPEC 封闭 schema 正面保证）。
- golden 合一后是同源两 code-path ⇒「一方漏某 rule」结构上不可能。spec 的 Scenario **MUST 删**「任一方漏
  rule → 失败」的宣称——降级为「同源两 code-path 的接线正确性」守，不 overclaim「机械充要」，也不降级实质
  守护力。

### 下游同步 fail-closed（AD-5 / R1）

- 合并 3→1 后，凡引用 `sdflow-buglist`/`sdflow-todolist` **目录名 / 脚本路径 / slash 触发名**的活跃托管点
  **MUST 同步更新**，否则合并后调用断裂/CI 打红/主 spec 留死路径（fail-closed，非可选）。
- 机械引用守卫 allowlist 中，`setup.sh` 的 `OUR_LEGACY_NAMES` **MUST 保留旧名**用于 Windows
  `.laodao-skills` legacy marker orphan 回收——**别当陈旧引用删**。
- `sdflow-ship`/`sdflow-code-review` 的「defer 进 buglist/todolist **池**」指池目录（**不合并**），
  **无脚本路径引用、无需改**。

### 行为等价门（Risks / SC-R3 / R5）

- 重构前后 CLI 逐命令行为等价**留存 param 化测试**（非丢弃的一次性快照）+ **覆盖判据零回归门**
  （node-id manifest allowlist + 全 subcommand 触达，**非 `≥603` 魔数**——魔数被删 7 个 mirror 测试证伪）
  为硬门。

### 完成态权威（信号归属）

- 本票完成信号 = ① 该 `### Task N:` 段的验收复选框全勾 ② 提交 subject 的
  `checkpoint(dedupe-issues-scripts-shared-layer:task<N>-<slug>)` 标签——**双轴审通过后由执行模式补打**，
  implementer 实现期 **MUST NOT** 自行勾框或打完成标签。
- 设计意图（`proposal.md` / `design.md` / `specs/` / `tasks.md`）**设计阶段已定稿，实现期不是它们的作者**
  ——发现设计有问题走 `NEEDS_CONTEXT` / `BLOCKED` 上抛编排层，**不自行改盘**。

### Task 1: 建零回归基线 + core package 骨架 + 封闭 POOL_SPEC schema 与守卫

**Blocked-by:** none
**R-ID:** SC-R2, SC-R3, DG-M1

冻结重构前的行为基线，并立起共享逻辑的物理容器与其守卫底座。本票不迁移任何 CLI 逻辑——只保证
「零回归门的度量基准存在」+「唯一命名 package 可 import」+「POOL_SPEC 是封闭 schema 且值关系被守住」。
POOL_SPEC 是后续所有差异注入的唯一入口，它的封闭性与关系正确性必须先于任何逻辑上移被守住，否则差异会
从后门（argparse default / 硬编码常量 / 任意 callable）漏进 core。

- [x] 冻结 pre-refactor pytest node-id manifest 作为零回归门的 allowlist 基线；标注意图删除项 =
      `test_mirror_consistency.py` 的 7 个测试 node
- [x] 唯一命名内部 package `sdflow_issues_core`（**非**裸 `core.py`）建立且可被 `from sdflow_issues_core
      import ...` 解析
- [x] `POOL_SPEC` 为封闭 dataclass/TypedDict，required 维含：文件粒度 / 目录 / legacy dir glob / 特定字段
      / 状态词表 / 终态集 / `DEFAULT_PREFIX`(B/T) / scan 输出键(bugs/items)；新增维不改 schema 即报错
- [x] schema 守卫红于：缺任一 required 维、`terminal_set ⊄ 状态词表`、`POOL_SPEC` 值与
      `RECORDER_POOL_CONFIG` 不一致、`POOL_SPEC.keys() != {"bug","todo"}`

### Task 2: 三层共享逻辑单一物理源 + 三薄入口迁入 sdflow-issues/scripts/（CLI 逐命令行为等价）

**Blocked-by:** 1
**R-ID:** SC-R2, SC-R3, DG-M1

本票是 expand 主体：把 THREE_WAY 共享 helper 与 TWO_WAY 镜像逻辑全部上移 `sdflow_issues_core` 作唯一物理
源，差异点改读 `POOL_SPEC`，消除 core 内一切 pool 值分支；三个入口壳化为薄入口并迁入 `sdflow-issues/scripts/`
最终家（含 `sys.path.insert` 令 file-based 测试可解 package import、sibling-spawn 常量改同目录、承重注释
重写）；对应 tests 迁入 `sdflow-issues/tests/`。收尾 CLI 逐命令外部行为与基线等价、既有测试全绿。

- [x] THREE_WAY 共享 helper（`atomic_write`/`repo_root`/`canonical_id`/`recorder_lock`/frontmatter
      mechanics 等）与 TWO_WAY 镜像逻辑全部上移 core，作唯一物理源；差异点改读 `POOL_SPEC`
- [x] 现存 pool 分支（三元 / `expected_pool==` 别名 / subscript 等）在迁进 core 前全部重写为 POOL_SPEC 取值；
      `core` 源码无任何针对 pool 值的条件分支
- [x] `buglist.py`/`todolist.py`/`issues.py` 壳化为薄入口（解析 args → 注入各自 `POOL_SPEC` →
      `from sdflow_issues_core import`；顶部 `sys.path.insert`）并迁入 `sdflow-issues/scripts/`；对应 tests
      迁入 `sdflow-issues/tests/` 且全绿
- [x] `issues.py` 跨池 reindex/batch/sweep 的 sibling-spawn 常量改同目录解析、承重注释去掉已作废的 sibling
      前提；`reindex`/`sweep` 仍能正确 spawn 子进程
- [x] CLI 逐命令（add / scan --json / set-status / triage / reindex / batch / next-id / sweep）外部行为与
      冻结基线等价，无回归

### Task 3: skill 合并 — SKILL.md 合一 + 骑墙规则 + 删旧目录

**Blocked-by:** 2
**R-ID:** SC-R1, R7

把两份 `SKILL.md` 正文（189 行 ≈62% 逐字重复）合并进 `sdflow-issues/SKILL.md`（一份覆盖两池 + 跨池、一个
触发面），补齐 bug↔todo 骑墙输入的判定规则并显式登记「误判落错池不可机械恢复」为已知代价，随后删除
`sdflow-buglist/`、`sdflow-todolist/` 目录（scripts 与 tests 已在 T2 迁走）。这是 contract 的第一步：旧
触发面塌缩为一个。

- [x] `sdflow-issues/SKILL.md` 覆盖两池 + 跨池，触发短语聚合到一个触发面，无逐字重复正文
- [x] SKILL.md 给出骑墙输入判定规则（「坏了没」判据 + 举例）+ 显式登记「误判落错池不可机械恢复」为已知代价
- [x] `sdflow-buglist/`、`sdflow-todolist/` 目录删除
- [x] `sdflow-issues/SKILL.md` 保留且仅保留一份 `sdflow:principles` 托管块

### Task 4: determinism-guards 守法切换（镜像守退役 → 单一源新守法）

**Blocked-by:** 2
**R-ID:** DG-M1, DG-M2

物理只剩一份 core ⇒ 三向/两向 AST 等价守失去对象，整体退役；守法改守新面：AST 级无 pool 分支守（诚实标
best-effort）、薄入口 thinness 同一性守、golden 诚实降级为接线守，并确认既有 fail-closed 校验不受迁移影响、
import 走同目录 package 无 sys.path 污染。守法的诚实边界（best-effort 声明、删 tautology 宣称）是本票硬约束。

- [x] `test_mirror_consistency.py`（三向/两向 roster）删除，无孤立 roster 残留
- [x] 无 pool 分支守为 AST 级（拦 `If`/`IfExp`/`Match`/`Compare` 右操作数 ∈{bug,todo} 且左操作数解析到
      pool 值/别名/subscript），mutation test 证其对 `expected_pool=="bug"`/`document["pool"]=="bug"` 反红；
      spec/test 诚实标 best-effort 代理、非充要
- [x] 薄入口 thinness 同一性守：THREE_WAY/TWO_WAY 名单每 helper 从薄入口 `getattr` 解析对象
      `__module__ == 'sdflow_issues_core'`（未被 shadow）
- [x] golden 降级为「同源两 code-path 接线正确」守，删「任一方漏 rule → 失败」宣称
- [x] `validate_scan_envelope` fail-closed / `config.yaml` lint / `batches.md` lint 随迁移继续绿；三薄入口经
      同目录 package import、无跨目录 import / sys.path 污染（除入口自身 dir）

### Task 5: 下游托管引用同步（AD-5 fail-closed + 机械引用守卫）

**Blocked-by:** 3
**R-ID:** SC-R4

合并的必然连带：凡引用旧 skill 目录名 / 脚本路径 / slash 触发名的活跃托管点全部同步更新（fail-closed），
并新增机械引用守卫把兜底从「手 grep 自觉」升级为门。依赖旧目录已删（T3）故守卫可断言其缺席。分范畴处理：
路径/名称引用、语义块重写、prose 分范畴、CI、安装测试、投放面计数——池目录引用与 `OUR_LEGACY_NAMES` 旧名
保留**不改**。

- [x] 路径/名称引用更新：README / CLAUDE.md / AGENTS.md skill 列表与数据类 skill 名单（3→1）、sdflow-init
      assets（claude-section.md / workflow.md）+ `sdflow-init/SKILL.md` 引用、`ship_gate.py` 路径引用、
      `sdflow-done/SKILL.md:207-211` 语义块重写
- [x] prose 分范畴：`sdflow-retro` 的 `/sdflow-buglist`·`/sdflow-todolist` slash prose 更新、
      `sdflow-implement/SKILL.md:378` skill-名 doc-pointer 改指 sdflow-issues；「defer 进 buglist/todolist
      **池**」概念不改
- [x] CI：`.github/workflows/windows-recorder-smoke.yml` 的 path-trigger + 测试调用改指 `sdflow-issues/tests/`；
      安装测试 `sdflow-init/tests/test_setup_sdflow.py` 断言由 `sdflow-buglist` 建链改为 `sdflow-issues` 建链
      + 旧目录 orphan 清理；`hack/tests/test_sync_principles.py` 投放面常量 17→15
- [x] 机械引用守卫 test：allowlist（archive / 历史 adr / issue ledger / `setup.sh` OUR_LEGACY_NAMES / 在途
      活跃 change 目录整体 / 池目录名）外出现旧 skill 目录/脚本路径/slash 名即 FAIL；现状下通过
- [x] 确认 `setup.sh` `OUR_LEGACY_NAMES` **保留** 旧名（Windows legacy marker orphan 回收依赖）；全仓检索确认
      除 allowlist 外无活跃托管点仍引用旧 skill

### Task 6: 行为等价留存测试 + 覆盖判据零回归门 + setup.sh 验证 + 显式 defer

**Blocked-by:** 4, 5
**R-ID:** SC-R3, R5, AD-6, AD-7

收口票：把逐命令行为等价固化为**留存**的 param 化测试（非一次性快照），立起覆盖判据零回归门（node-id
manifest allowlist + 全 subcommand 触达，非 `≥603` 魔数），跑 setup.sh 确认链接与 orphan 清理，并落两条显式
defer 占位 todo。全部前序完成后本票是最终验证面。

- [ ] CLI 逐命令 param 化测试**留存**（遍历全 subcommand：add / scan --json / set-status / triage / reindex
      / batch add|set-status|rename / next-id / sweep：stdout JSON + 落盘字节 + 退出码）
- [ ] 覆盖判据零回归：冻结 node-id manifest 除 allowlist（`test_mirror_consistency.py` 7 个）外每 node 仍
      pass；全 argparse subcommand migration 后逐一有测试触达；无 FAILED、无因重构导致的 skip（非 `≥603` 魔数）
- [ ] 跑 `setup.sh`：确认建 `sdflow-issues` 链接、orphan 清理回收 `sdflow-buglist`/`sdflow-todolist` 旧链接
- [ ] 记 todo 占位：`sdflow_issues_core` god-module 拆 cohesive 子模块 + issues 内部消自调用子进程（AD-7）；
      `move --to-pool` 跨池搬运命令（AD-6）
