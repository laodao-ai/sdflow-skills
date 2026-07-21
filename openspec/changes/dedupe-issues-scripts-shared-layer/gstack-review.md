<!-- sdflow:step1-broad-review v1 mode="native" -->

# gstack-review — dedupe-issues-scripts-shared-layer `[gstack-amendment]`

> **Step1 广审（autoplan native）**。mode="native"：autoplan 指令原生进主 session 执行，按其方法论跑
> CEO/Eng/DX 三角 + 双声（Claude 独立广审子代理 + Codex 广审 voice），fan-out 到 fresh context。
> **侧信道佐证（真实运行痕迹）**：Claude 广审子代理 agentId `ae8861ba4b0c4e343`（墙钟 378s、21 tool_uses、
> 101K tokens、真读三脚本 + AST + 全仓 grep）；Codex 广审 session `019f83f3-c683-7fd2-afe2-e71b3f79ba99`
> （model=gpt-5.6-sol、reasoning=high、read-only sandbox、exit 0）。二者独立 fresh context，均以**目标态**为基准
> （prompt 内焊死「不拿现状反驳目标」）。

## 裁决摘要（两声一致）

**两个独立广审 voice 均判：设计 HARD-GATE 当前不应通过**——1 个合并后必然失败的 Critical（AD-5 引用面不全、
CI 必红）+ 多个 High 级契约缺口（守法可绕过、A1 逃生口不可证伪、import core 非纯路径替换、603 弱门、
install 残留）。方向（3→1 合一、撤「独立分发」）**站得住**（setup.sh 实测无单装路径），问题全在**目标态契约的
机械守卫与引用完备性**——不是「该不该合」，是「合的守法与连带面没做全」。

---

## 广审 findings（合并两声 + 主 session 接地）

### G1 [Critical] AD-5 下游引用清单不全，合并后 CI 必红 + 主 spec 留死路径

**两声 + 主 session 三方独立收敛。** AD-5 声称枚举「所有活跃托管引用点」，可证伪假设 A3 的证伪信号
=「合一后全仓检索仍有活跃点引用旧目录」——该信号在**多个未列点**触发：

- 🔴 **`.github/workflows/windows-recorder-smoke.yml`**（Codex 独家抓）：`:35` 跑
  `py -m pytest sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py`（合并后该路径已删），
  且 `:18` trigger 含 `sdflow-issues/**` ⇒ **改幸存 skill 即触发这个必然失败的 workflow**。`:8-9,16-17`
  的 `paths:` 旧 glob 亦 stale。**这是最硬的 fail-closed 实例——一个保证打红的 CI job。**
- 🟡 **`openspec/specs/recorder-root-resolution/spec.md:5-6,77-78`**（主 spec）：把三 recorder 路径
  `sdflow-buglist/scripts/buglist.py` 写死为契约。本 change **不带该 capability 的 MODIFIED delta**
  ⇒ 归档不会修正，合一后主 spec 留死路径。
- 🟡 **`openspec/specs/spec-workflow/spec.md:285,293,297`**（主 spec）：`:285` 是**活跃 MUST**（RENAME-MAP
  枚举 `sdflow-buglist`/`sdflow-todolist` 为必备 skill 名），`:293/297` 是断言其触发/路径解析的 Scenario。
  删两 skill 使该 accepted spec 的 requirement + scenario 失真，**无 delta 携带修正**。task 5.5 的 grep-replace
  会**静默重写一条 spec requirement**——过程错误（spec 改动应走 delta，非 sweep）。
- 🟡 **`sdflow-init/tests/test_setup_sdflow.py:106,151`**：端到端安装测试断言 setup 后 `sdflow-buglist`
  链接建立——目录删后此断言 FAIL（task 6.2 pytest 会撞红，但 AD-5 未列它为编辑目标，实现者会撞红而无任务指引预期改法）。
- 🟢 **`issues.py:68-69`** 运行期常量 `BUGLIST_SCRIPT`/`TODOLIST_SCRIPT` =
  `os.path.join(SKILLS_ROOT, "sdflow-buglist", "scripts", "buglist.py")`（`_scan_pool` 按此 spawn）
  ⇒ 合并后指向不存在路径。task 2.3 只说「子进程契约保持」，**未点名这两个常量必须重写为同目录**。
- 🟢 **prose 引用已删触发面**：`sdflow-retro/SKILL.md:107-108`、`sdflow-implement/SKILL.md:378`、
  `sdflow-init/SKILL.md:138` 引用 `/sdflow-buglist`·`/sdflow-todolist`；`sdflow-done/SKILL.md:207-211`
  是**语义块**（描述整个 sibling-独立分发架构，正是被反转的东西），需语义重写非路径替换。
- 🟢 **docs**：`docs/workflow-map.md:171-172`、`docs/sdflow-fable5/02-module-reference.md`、
  `docs/drafts/sdflow-issues-toolchain-defects.md` stale。

**修法**：① 新增 `recorder-root-resolution` + `spec-workflow` 两份 MODIFIED delta（或显式 reconcile RENAME-MAP
——skill 已不存在，枚举 + scenario 必须修订，非 grep 替换）；② Windows workflow、`test_setup_sdflow.py`、
既有 `sdflow-issues/tests/`、上述 SKILL/docs 引用全进 tasks；③ **增机械引用守卫**（allowlist 放行 archive/
历史 ADR/issue ledger/`setup.sh` 为清孤儿保留的旧名，其余出现旧名即 FAIL）——把 A3 从「实现者手 grep 的自觉」
升级为门。证据：`design.md:103`（AD-5 有限集）、`windows-recorder-smoke.yml:8/18/35`、
`recorder-root-resolution/spec.md:5/77`、`spec-workflow/spec.md:285/293/297`、`test_setup_sdflow.py:106`、
`issues.py:68-69`。〔视角：Eng/DX〕〔置信：高〕

### G2 [High] 「core 无 pool 分支」守法 spec 定义过窄 + 可平凡绕过 → 守法即剧场

**主 session 已独立接地确认。** MODIFIED spec + AD-3/AD-4 把禁止形写死为 `if pool == "bug"/"todo"`，但**真实待上移
core 的 pool 分支有四种形态**，字面 token 扫描漏掉多数：

- `document["pool"] == "bug"`（issues.py:900/991/1001/1056，**subscript 形——扫变量名 `pool ==` 必漏 4 处**）
- `expected_pool == "bug"`（issues.py:677/689、buglist.py:1218/1230）
- `"bugs" if pool == "bug" else "items"`（issues.py:1365 三元）
- `pool == "bug"`（buglist.py:1508）

Codex 另举可绕法：`match pool` / `kind = pool` 后比较 kind / `handlers[pool](...)` 映射 dispatch
（issues.py:1522/1528 已存在）/ comprehension 内比较（issues.py:1476）/ callable 内部重新比较。
`POOL_SPEC` 完备测试只证键存在、**不证策略没重新分叉**。∴「无 pool 分支通过」只证「无某一文本片段」，
不证「结构上无从漂移」（AD-4/ADR-0027 的原话）——这正是本仓 CLAUDE.md 基准 5 与「gate 子串检测自指坑」的复发。

**修法**：守卫改为 **AST 级**——限制字面量 `"bug"`/`"todo"` 只出现在 POOL_SPEC 声明区，`core` 算法体内对
pool discriminator 的任何比较（`Compare`/`Subscript`/`IfExp`/`match`/dict-dispatch/alias）一律拉红；
配 mutation tests 覆盖各绕法（`test_logic_drift_is_caught` analogue，证守卫对 `expected_pool == "bug"`、
`document["pool"] == "bug"` 反红，非只对 `pool == "bug"`）。core API 接受不可变 `PoolSpec` 对象、不接受 pool string。
证据：`determinism-guards/spec.md:7,9,17`、`issues.py:900/991/1001/1056/677/689/1365/1522/1528/1476`、
`buglist.py:1218/1230/1508`。〔视角：Eng〕〔置信：高〕

### G3 [High] A1「差异全可参数化」的 POOL_SPEC 维度不全，callable 逃生口使 A1 事实上不可证伪

**两声收敛。** AD-3 只枚举五类差异（粒度/目录/字段/词表/终态集），但真实差异含**行为策略、非取值差异**：

- bug 必须有详细 marker block；todo 可完全无 block（buglist.py:1218-1231 vs todolist.py:1399/1474）。
- bug `FIXED` 除 evidence 必须存在根因；todo `DONE` 只需 evidence（buglist.py:1554 vs todolist.py:1515）。
- todo 状态变化时动态创建 minimal block；bug 假定 block 必然存在（todolist.py:1608）。
- 另有不同必填 JSON 字段、时间格式、header/body renderer、scan JSON key、排序、CLI 参数。

这些是**存在/不存在行为**（marker 子系统 bug-only），非词表值差。迁移后它们变成 `if spec["has_markers"]:`
——**通过任何 pool-name 守卫，同时原样保留分支**。AD-3「值可为可调用」的逃生口（design.md:93）= 任何整段
业务逻辑都能塞进 callable ⇒ A1 永不失败、重复只是从 core 挪进策略函数。

**修法**：实现前写**完整封闭的 PoolSpec schema**（ID prefix/日期时间格式/路径/必填字段/renderer policy/
marker required policy/legacy promotion/completion validation/scan envelope key/filter/sort）；**禁任意 callable**
——若确需策略钩子，逐个命名 + 限定签名 + 说明为何不能数据化，并对 bug/todo 各跑同一 contract suite。
design 诚实声明 core **将**含 config-value 条件（`if spec["has_markers"]`），守卫只禁 pool-name 形，
真正不变量是「pool 知识集中在 POOL_SPEC」，源码扫描不完全证明它（承本仓「有信号≠有可机械捕获路径」）。
证据：`design.md:81,93`、`buglist.py:1218/1230/1456/1515/1554`、`todolist.py:1399/1474/1515/1608`。
〔视角：Eng〕〔置信：高〕

### G4 [High·TENSION] 同目录 `import core` 是否「只换路径前缀」——两声分歧

- **Codex（High）**：非纯路径替换。`python buglist.py` 时 script 目录进 sys.path，但测试多用
  `importlib.util.spec_from_file_location()` 按文件加载（test_task2_semantic_lock.py:15、
  test_frontmatter_dual_reader.py:17、test_task3_frontmatter_writer.py:16 均不改 sys.path）——wrapper 加
  `import core` 后这些测试 `ModuleNotFoundError`，除非重写或污染 sys.path；且裸模块名 `core` 共享全局
  `sys.modules["core"]`，别处先加载同名模块 → wrapper 拿错 core（无 `core.__file__` 校验）。test_issues.py:17
  已用全局 `sys.path.insert`，扩大 collision 面。
- **Claude 子代理（无阻）**：同目录 import 经 `sys.path[0]`=脚本目录解析（整目录 symlink 下 abspath≠realpath 仍可解），
  `core` 非 stdlib 名、碰撞风险可忽略。

**主 session 裁决建议**：Codex 说的**文件式加载路径**风险真实（既有测试确按 `spec_from_file_location` 加载、不改
sys.path，wrapper 内 `import core` 在该加载方式下会断），Claude 的「CLI 直跑能解」只覆盖 subprocess 路径、
不覆盖测试的 file-based loading。二者不矛盾——是**两条加载路径**，spec 未声明保证哪条。∴ 采信 Codex：
**修法** = 用唯一命名内部 package（如 `scripts/sdflow_issues_core/`）或按 `__file__` 精确加载 + 校验 origin；
spec 明确「保证 CLI subprocess / 也保证 file-based module loading / wrapper 是否 re-export 旧 helper API」，
三 wrapper 的 installed-path·直接执行·动态加载分别如何测。证据：`design.md:77`、
`test_task2_semantic_lock.py:15`、`test_frontmatter_dual_reader.py:17`、`test_issues.py:17`。〔视角：Eng〕〔置信：高〕

### G5 [High] 「≥603 passed」是可游戏化计数，不能证明零回归

**两声收敛。** 同一 change 删 mirror tests、迁移测试目录、改 import/断言；只要求最终 `≥603` ⇒ 可删原行为
测试再补同数量新结构测试而过门。行为快照矩阵（tasks.md:43）缺 `next-id`/`sweep`/全部 batch 子命令/`--help`/
非法输入/stderr/锁冲突/重复运行/Windows 安装路径，不足以支撑「逐命令等价」。

**修法**：重构前冻结 pytest node-id manifest，只允许显式列出的 mirror-test node 被删；门改为 `== expected`
（pre-refactor pass count 减去意图删除的 mirror tests，非 `≥603`）；先生成本 change 内不可 rebaseline 的黑盒
golden；覆盖全子命令/flags/成功失败路径/stdout·stderr bytes/退出码/落盘 bytes/重复执行/并发锁/Unix symlink+
Windows copy 两种安装；wrapper tests 与 core tests 分开（防「直接测 core 全绿、wrapper 已坏」）。
证据：`tasks.md:22,28,43,44`、`specs/issues-scripts-shared-core/spec.md:45-47`。〔视角：Eng〕〔置信：高/中〕

### G6 [Medium] 「恒一起装、从不单装」只对默认 happy path 成立；升级后可能残留旧触发面

**Codex.** setup.sh 确实遍历安装全部 skill，但**逐 skill 决策**——遇非本工具拥有的同名目录会 skip（setup.sh:46/60），
orphan cleanup 只接管自属 symlink/marker（:86/102）。曾手工复制/他工具装/marker 丢失的旧 `sdflow-buglist`/
`sdflow-todolist` 会继续存在，与新 `sdflow-issues` 同时触发。而 spec.md:9 绝对要求旧 skill 不存在。且这不只是
脚本路径 BREAKING——用户可见的 `/sdflow-buglist`·`/sdflow-todolist` 也删（migration 只突出脚本路径，低估 DX）。

**修法**：把 slash-command 删除声明为正式 breaking + 版本/迁移策略；`setup.sh` 完成后检查两旧目录（自属则清理、
非自属则 fail/warn + 输出精确人工迁移命令，不宣称满足「一个触发面」）；加 partial install/marker 丢失/foreign
collision/手工 copy 四类升级测试；`setup.sh:26` 旧名保留用于清理、不被全仓替换误删。证据：`setup.sh:38/46/60/86/102`、
`README.md:59/74`、`spec.md:9`。〔视角：CEO/DX〕〔置信：高〕

### G7 [Medium] 「一个 skill」被误等同于「一个巨型 core.py」+ 保留已失理由的进程边界

**Codex + Claude（Claude F4 同源）.** 去重只要求「一项逻辑一个实现」，不要求全塞一个文件；目标 core.py 很可能仍是
数千行 god module（六月后修改/定位/monkeypatch 恶化）。设计保留 `issues.py → buglist.py/todolist.py scan --json`
子进程（design.md:66、issues.py:1499）——两 scan 各读全 snapshot 再过滤 pool，一次 reindex 重复扫全台账 +
维护两种内部 envelope；合一后该进程边界已无独立分发价值。ADR Considered Options 未评估「一个 skill + 内部
cohesive package + legacy wrapper」（adr/0027:30）。

**修法（建议，非阻断）**：一个 skill + 一个内部 package（recorder/document/locking/ledger/policies）+ 三兼容
wrapper；issues 内部对一个 snapshot 调两次 pool view，不自调用子进程。或将「subprocess→import + 内部拆包」
显式记为 defer（如 CLI-subcommand-tree defer 的先例），别把已死前提的注释化石化（DOC-1）。
证据：`design.md:66,77`、`issues.py:1499`、`buglist.py:1671`、`todolist.py:1648`、`adr/0027:30`。〔视角：Eng/DX〕〔置信：中〕

### G8 [Low] 数字/措辞小瑕

- AD-5「17→15，自动少一个」措辞错：删两 skill 是 **−2**，非「少一个」（design.md:105；实测 `grep -rl sdflow:principles`
  = 17，含 buglist/todolist/issues，合并后 15）。`sync_principles.py` 动态枚举自动 −2，只 `test_sync_principles.py:4,18`
  硬编码 `17` 需手改 `15`。〔Claude F6〕
- Why/Context「77 同名 def、90% AST 等价」不精确：Codex 复现剥 docstring 后 **66/77=85.7%**，roster 实为
  THREE_WAY ~40 + TWO_WAY ~24（test_mirror_consistency.py），非「77 个 TWO_WAY」。非承重、不影响决策。〔Codex〕
- per-pool 启用/禁用粒度丢失（config-skills 四态）：今可单独禁 `sdflow-todolist` 记录，合并后只能整体 toggle
  `sdflow-issues`。bug/todo 本是一台账，可接受——但应进 trade-offs 明写，成决策非意外。〔Claude F7〕

---

## 视角检查·无实质问题（接地确认）

- **CEO — 「独立分发」前提 & 过早否掉的方案**：setup.sh globs `REPO_DIR/*/` 无条件装每个顶层 skill 目录、
  **无单装路径** ⇒「恒一起装」对本仓事实成立，撤 D4 有据（非现状-反驳）。ADR-0027 Considered Options
  （单skill+core、装期复制 a'、跨目录 import a、维持现状、CLI 子命令树）对 Markdown-skills 仓合理穷尽
  （打包成真 Python 模块过度，隐含被 a 覆盖）。回滚干净（revert + setup.sh，无数据迁移）。除 G7 外无 6 月后悔陷阱。
- **Eng — orphan 清理 & 同目录 import 基本机制**：setup.sh cleanup_orphans（74-111）用 `-e` 解析回收 dangling
  symlink——删两目录会正确 orphan-clean 旧链（G6 是 foreign/partial 边角，非主路径）。
- **DX — bug↔todo 分类移交模型**：CLI 仍保显式 pool 入口（`buglist.py add`/`todolist.py add`），「坏了没」模型
  路由只在 SKILL.md NL 层，误分类低代价可恢复（re-add/set-status）。SKILL.md ≈450-550 行大但一次 load 替原三份。

---

## 决策登记候选（转 spec-review-report 决策区）

- **[需拍板 Q]** G4 import 加载策略：裸 `import core` vs 唯一命名内部 package vs `__file__` 精确加载——推荐内部 package。
- **[需拍板 Q]** G3 callable 逃生口去留：推荐禁任意 callable、策略钩子须逐个命名限签。
- **[需拍板 Q]** G7 god module vs 内部拆包：推荐内部 cohesive package；至少显式 defer 留档。
- **[自动决策 D]** G1 AD-5 补全 + 机械引用守卫：fail-closed 必改，无异议默认采纳。
- **[自动决策 D]** G2 守卫升 AST 级：必改，否则守法即剧场。

---

## Codex 广审 voice（原始第二意见·跨模型·供 outside-voice 复用守卫）

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="7" truncated="false" -->

**runner=codex · session `019f83f3-c683-7fd2-afe2-e71b3f79ba99` · model gpt-5.6-sol · read-only · exit 0**
**裁决：设计 HARD-GATE 不应通过（1 Critical + 5 High + 1 Medium）**。findings 已并入上方 G1-G8：

1. **Critical** — AD-5 引用清单不完整，目标态直接打红 CI（windows-recorder-smoke.yml）+ 留互相矛盾的主规格（→ G1）。
2. **High** — A1 的 POOL_SPEC 维度远不完整，callable 逃生口使 A1 事实上不可证伪（→ G3）。
3. **High** — 「源码扫描无 pool branch」非有效守卫、可平凡绕过（match/dispatch/alias/callable）（→ G2）。
4. **High** — 同目录 `import core` 非「只换路径前缀」，破坏 file-based 加载 + 全局模块碰撞（→ G4）。
5. **High** — 「603 passed」可游戏化计数，不证零回归（→ G5）。
6. **High** — 「恒一起装从不单装」只对 happy path 成立，升级后可能残留三触发面（→ G6）。
7. **Medium** — 「一个 skill」≠「一个巨型 core.py」，保留已失理由的子进程边界（→ G7）。
