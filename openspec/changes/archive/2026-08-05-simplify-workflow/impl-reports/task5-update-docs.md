# Task 5 impl-report：更新 snippets、CLAUDE.md、AGENTS.md、本地 pin 与 companion 文档

## 完成的工作（按 brief A-G 分组）

### A. `sdflow-init/assets/snippets/claude-section.md`（下推模板，单一源）
- 删「阶段一入口二选一」「ff 之后是 grill」「grill-with-docs 归属」三段（分支 B/wayfinder/
  grill-with-docs/手动限制内容）。
- 加自动触发规则：人示意收敛（"开搞"/"做吧"/"开 change"）→ 模型自动 invoke `/sdflow-spec`；
  模型 MUST NOT 自主判断"该开 change 了"。
- 加 impl-pipeline 缺省描述（缺省 = tickets，显式 `impl-pipeline: superpowers` 才走旧管线）。
- skill 角色表里 `/sdflow-spec` 一行去掉"分支 A""只能人触发"措辞，改为"人可直接触发，模型按
  自动触发规则在人示意收敛时自动 invoke"。
- （embedded-test-sop 本就不在这份 snippet 的编排类列表里，无需删——见下方"发现但未改动"）。

### B. `CLAUDE.md`（本仓）
- 删「两类 skill」编排类列表里的 `embedded-test-sop`。
- 整段替换「阶段一入口：`/sdflow-spec` 使用路径 · 四入口选择规则 · 旧入口 sunset 条件」
  （原 215-275 行，含「四入口选择规则」「旧入口 sunset 条件」两个子节 ≈60 行）为简化版
  「阶段一入口：`/sdflow-spec` 使用路径（唯一线性路径）」——单轨五步：explore 条件 →
  人示意收敛/模型自动 invoke → `/sdflow-spec` 三相位 → checkpoint 两处 → 出口序列
  `/clear`→spec-review→HARD-GATE→`/clear`→`/sdflow-ship`。
- `opsx-init:start/end` 托管块内容（OpenSpec 工作流 + Codex 子代理授权两节，含 grill-with-docs
  blockquote）手动同步为 claude-section.md 的新内容（详见「本地 pin/托管块同步」节，说明为何
  手动而非跑 `sdflow-init update`）。

### C. `AGENTS.md`（本仓）
- 对非托管区「阶段一入口」小节做与 CLAUDE.md 完全相同的替换（原 111-171 行）。
- 托管块内容同步为 claude-section.md 新内容（同 B）。
- 验证：`entry_section(CLAUDE.md) == entry_section(AGENTS.md)`（逐字相等，机验见下方新增测试）。

### D. `openspec/workflow/` 本地 pin 处置
**发现**：CLAUDE.md 自己的架构描述（`### OpenSpec 的双重角色` 一节）声明"仓库只保留
`openspec/workflow/tools/`，规则不留仓内副本"，但实际状态是 48 个文件的完整规则副本
（`git log` 显示曾在 `b013172` 删过，又被后续 `align-sdflow-spec-with-openspec-schema`
的 `update --dev` 全量刷新命令重新铺回——这条命令的 docstring 明确写着"仅供 toolkit 源仓
`update --dev` dogfood 刷新用"，正是这条命令重新制造了 pin）。这个 pin 会让
`resolve-workflow.sh` 命中本地副本、屏蔽掉 Task 4 已经改好的全局 canonical——即 spec-review /
code-review / done 三个 skill 在本仓跑起来读到的仍是**旧的双轨规则**，跟 Task 1-4 的所有改动
完全脱节。

**处置**：按 brief 给的两个选项之一——"删除规则文件恢复全局解析"——`git rm` 掉 40 个规则文件
（`workflow.md` / `generation-process.md` / `ff-generation-constraints.md` / `spec-review.md` /
`trigger-catalog.md` / `design-diagrams.md` / `model-tiers.md` / `config.template.yaml` /
`workflow-history.md` / `prompts/*`（9 个）/ `reference/*`（7 个）/ `spec-checklists/*`（8 个）/
`code-checklists/*`（7 个）），只保留 `tools/`（6 个脚本，review 工具机械，非规则）+
`lens-metric-contract.md`（`anchor_lint.py` 的读时依赖）+ `WORKFLOW-GUIDE.md`（生成物，给人看
的手册）——这三类是 `sdflow-init/scripts/init.py` 的 `copy_bundle(full=False)` 路径本就会保留
的最小集，与 CLAUDE.md 自己的架构声明重新对齐。

已验证 `resolve-workflow.sh --explain` 现在正确命中 `source=global-canonical`（之前会命中
`source=local-pin`）。

`WORKFLOW-GUIDE.md` 本地副本已过期（比 canonical 早一天，缺 Task 4 重生成后的单轨内容）——
已用 `cp` 从 canonical 同步（`copy_bundle` 非 full 模式本就会做这个拷贝，这里手动复现同一
动作，见下方「未跑 sdflow-init update 的原因」）。`lens-metric-contract.md` 已核对与 canonical
一致，无需动。

### E. Companion 文档（4 份，按关键词逐处清理）
- **`docs/workflow-map.md`**：流程图删 RUN_SOP 行、explore/propose 行去分支标注、人类门①从
  "grill"改"拷问"；阶段表删 3a（SOP）行、3b-3e 重排为 3a-3d；verdict 表删 RUN_SOP 行；速览行
  "12 ship_gate 裁决"改"11"（verdict 表实际剩 11 个，matches ship_gate.py 当前 verdict 集）；
  `log_check.py` 行的"拟 embedded-test-sop"改为如实登记该宿主已删、消费方待定。
- **`docs/workflow-overview.md`**：§0 全局流程图、§1 三阶段画像表、§2 阶段一详解（含内嵌
  mermaid + 分支 A/B 两个子表）、§3 设计审 mermaid（删 SOP 分支）、§4.2 ship_gate mermaid +
  判定态表（删 RUN_SOP，"12 个判定态"改"11 个"）、§5 外部黑盒表、§7 自检清单——全部改为单轨
  描述。
- **`docs/criteria-mechanization-tracker.md`**：删整个「5a. ship·SOP（条件）」小节（2 行判据，
  对应已删的 `tg02_hit`/`RUN_SOP`）；「5.1 下一步是谁（12 verdict 推导）」改"11 verdict"；
  「2. 人类门① grill」小节标题改"人类门① 拷问（`/sdflow-spec` 相位 B）"，删已随
  `ff-generation-constraints.md` wayfinder→ff 衔接契约一起退役的"2.3 grill 瘦跑"判据行；覆盖
  小结的粗计数字同步（🟢 ~22→~20，🔵 ~18→~17，🟡 不变）。
- **`docs/sdflow-fable5/02-module-reference.md`**：删「§5.4 embedded-test-sop：数据类的反例」
  整节（该 skill 已删除）、skill 总表删该行、"编排类"列表删该名、"数据类六件套"改"五件套"
  （§5 现只剩 recorder 三件套 + retro + maintain = 5 个，原第 6 个是被删的 embedded-test-sop
  反例条目）、§3.1 ship_gate 状态机 mermaid 删 RUN_SOP 节点、§7 端到端拓扑 mermaid 删分支
  A/B 子图与 RUN_SOP 边。

### F. `README.md`
- Skills 列表本就没有 `embedded-test-sop` 这一行（该行此前已不存在，броウ无需删）——检查后
  确认此条验收标准天然满足。
- **发现并顺带修的相邻问题**：Quick Start 的操作说明仍写着"`/sdflow-spec` 与
  `/grill-with-docs` 只能人手动敲，模型唤不起"+"没装 `sdflow-spec` 的项目沿用旧三步"这两句，
  与本 change 的目标态直接矛盾（且落在 Task 6 最终验证脚本会扫的 `disable-model-invocation`/
  `分支 B` 关键词射程外——它写的是"人手动敲""旧三步"这类同义表述，不会被字面关键词扫到，
  但语义上就是要清理的那类残留）。已改为单轨描述（explore 条件 → `/sdflow-spec`，人可直接
  触发/模型自动 invoke）。

## 未跑 `sdflow-init update` 的原因（诚实边界）

原计划：手动改完 `claude-section.md` 后跑 `python3 sdflow-init/scripts/init.py update --root .`
（非 `--dev`，避免触发 D 节提到的那个会重新铺回本地 pin 的全量刷新）来机械同步 CLAUDE.md /
AGENTS.md 的 `opsx-init` 托管块与 `INDEX.md`。

实跑时 `migrate_changes()` 对本 change 自己的 `.openspec.yaml` marker 报错退出：
```
ERROR: 文件系统操作失败：schema marker 不可解析：./openspec/changes/simplify-workflow/.openspec.yaml
```
排查：`_marker_schema()` 要求 marker 文件**恰好**只有 `schema` 一个键，但这个 change 的
`.openspec.yaml`（`openspec new change` CLI 官方写的，`git log` 显示该两键格式是从更早的
`curb-rework-loop-cost` 一路拷贝下来的存量形态）实际有 `schema` + `created` 两个键——这是
`sdflow-init/scripts/init.py` 里一个与本 change 无关的**预先存在的校验过严 bug**：只要仓里有
任何一个**在途（非归档）** change 用官方 CLI 的标准双键格式创建，`update` 就会在这一步硬退出。
本 change 自己就撞上了这个 bug（自举失败）。

处置：改为**手动**把更新后的 `claude-section.md` 内容原样拼进 CLAUDE.md / AGENTS.md 的
`opsx-init:start/end` 标记之间（严格复现 `inject()` 函数的格式规则：起始标记后一个空行 +
内容 + 结束标记），并用 `diff` 核对两处托管块与 snippet **字节级完全一致**。`INDEX.md` 的
`opsx-init:rules` 托管块已核对本就与 `index-section.md` 一致，无需改动。

`init.py` 的这个 marker 校验 bug **未修**——不在本票范围（`sdflow-init/scripts/init.py` 不是
brief 列出的文件），如实登记供后续处理。

## 顺带修复的关联问题（fold 而非 defer，理由见下）

以下三处不在 brief 的 A-G 文件清单内，但都是**由本 change 早前的 Task 1/3 直接导致**、且
会让 Task 6 的"pytest 全仓全绿"验收门当场变红的真实测试回归——按通则④"执行中撞到与本次功能
相关的 bug → 立即 fold 做掉，不 defer、不另开"处理，而非留给 Task 6 去发现。

1. **`sdflow-ship/SKILL.md`**：frontmatter description、链序段落、design 失鲜求值窗口描述里
   残留 4 处 `RUN_SOP`/`embedded-test-sop`/"5.5→9"（Task 1 清理 `ship_gate.py` 时未同步更新
   这份消费该 gate 契约的 SKILL.md——ship_gate.py 已经不会再 emit `RUN_SOP`，这份文档继续讲
   `RUN_SOP→跑 embedded-test-sop` 会让编排 LLM 在运行时对着一个不存在的分支等待）。已改为
   "5→8"（权威编号见下方"第二轮"节——首版误写成"6→9"，被全仓 pytest 揪出后已纠正）、删
   RUN_SOP 分支描述、design 失鲜窗口改"`RUN_PLAN` / `CONTINUE_IMPL`"（与
   ship_gate.py 当前"两入口"注释对齐）、"不跨 grill"改"不跨拷问"。

2. **`hack/tests/test_sdflow_spec_resident_contract.py`**（2 个用例红）：断言
   `sdflow-spec/SKILL.md` frontmatter 必须含 `disable-model-invocation: true`——Task 3 已经
   删掉这行 frontmatter，这条门断言的是被删掉的东西。改为断言**不存在**（正向验证 Task 3 的
   目标态），并加一行说明性 message。

3. **`sdflow-init/tests/test_setup_sdflow.py::TestBrandAndMarkerNarrowing::
   test_legacy_marker_recognized_only_for_our_names`**（1 个用例红）：这个测试的 `_GONE_NAMES`
   是从仓内实际目录动态派生的（`(REPO/name/"SKILL.md").is_file()`），Task 1 删掉
   `embedded-test-sop/` 后它自动落入 `_GONE_NAMES` 桶，测试断言"旧名的 `.laodao-skills` 标记
   拷贝应被 setup.sh 清理掉"——但实测清不掉。往下查到 `setup.sh` 里一个**更早的、独立的**
   bug：`cf557a7`（"迁出 OpenSpec 升级与嵌入式 SOP skill"，本仓今天早些时候的另一次提交，
   已在本分支历史里，不是本 change 引入的）把 `embedded-test-sop`/`openspec-upgrade` 从
   `OUR_LEGACY_NAMES`（决定 `.laodao-skills` 标记认不认自属的名单）移到了新增的
   `MIGRATED_SKILL_NAMES`（"已迁出，只回收不接管"名单），但**忘了同步改 `is_our_marker_copy()`
   的判据**——它只查 `OUR_LEGACY_NAMES`，导致 `cleanup_migrated_skills()` 里"如果是
   marker-copy 就清理"那条分支永远判"不是我们的"、永远不清理，这两个已迁出 skill 的旧
   Windows/`.laodao-skills` 拷贝装成永久卡在用户机器上、`setup.sh` 再也碰不到它们。
   已修：`is_our_marker_copy()` 的 `.laodao-skills` 判据从只查 `OUR_LEGACY_NAMES` 改为查
   `OUR_LEGACY_NAMES ∪ MIGRATED_SKILL_NAMES`（`install_into()` 的正常安装路径不受影响——它的
   遍历源是 `$REPO_DIR/*/`，两个已迁出 skill 的源目录本就不存在，永远不会进这个循环；受影响
   的只有 `cleanup_migrated_skills()` 的回收判定）。

## 重写而非删除的一份测试文件（超出 brief 范围的判断，附理由）

`hack/tests/test_canonical_entry_sync.py`（11 个用例红）整份文件的存在理由是"双轨入口
（分支 A/B + 四入口选择规则 + sunset 条件）不得在 7 处载体间分叉"——这正是本 change 要**消除**
的设计本身，SA-14/D10 是它锚的旧 spec Requirement ID。11 个红用例逐一断言"canonical 里必须
出现『分支 A』『分支 B』『旧三步』……"这类字面串，本 change 的 Task 4/本票的 A-C 项已经把这些
字面串从 canonical 和人读侧删干净——这些用例现在**测的是它本该测没有的东西**。

处置依据是本 change 自己在 Task 3 里对同类情形定的先例：`sdflow-init/tests/
test_grill_handoff.py`"grill 不再是流程中的独立步骤，该回归门随之退役"——**整体删除**。
`test_canonical_entry_sync.py` 是同一类情形（被测设计本身退役），但比 `test_grill_handoff.py`
多一层：文件末尾 3 个用例（`test_codex_auth_section_parity` /
`test_entry_section_exists_in_both_human_carriers` /
`test_two_human_carriers_are_verbatim_identical`）测的是"CLAUDE.md / AGENTS.md /
claude-section.md 三处手抄副本互相不许分叉"，这条纪律跟双轨/单轨无关、正交，且**恰恰是我这次
手动同步三处托管块时最容易踩空的坑**（原文件 docstring 自己点破："两份是手抄的同一段话，唯一
兜底是一句 prose『改一处就改另一处』——而会想起去查那句 prose 的人本来就不会漏改"）。整份删掉
会把这条价值也一起倒掉，且我自己刚在 D/B/C 三节里手写了三份需要保持同步的内容，缺这道机械门
等于自己给自己挖了一个下次编辑会踩的坑。

故未走"整体删除"，走"改写"：保留这 3 条 parity 用例（原样复用），把其余 11 条"presence 断言
双轨字面串"换成两类新断言——① presence：新的自动触发规则措辞在 canonical 与人读侧同步出现；
② absence：`分支 A`/`分支 B`/`disable-model-invocation: true` 等已退役措辞不许再出现在
canonical 或人读侧（防未来编辑手滑改回双轨语言）。新文件 8 个用例，全绿，见下方验证记录。

这一步超出 brief 的 A-G 文件清单，但与"companion 文档 RUN_SOP/embedded-test-sop/wayfinder/
分支 B 引用已清理"这条 Task 5 总验收标准直接相关——一份专门断言"分支 B 必须存在"的测试文件不
处理，Task 6 的"pytest 全仓全绿"门永远过不了。

## 发现但未改动的残留（超出本票范围，登记供 Task 6 / 后续处理）

- **`sdflow-init/assets/workflow/tools/anchor_lint.py` 与本地 `openspec/workflow/tools/
  anchor_lint.py` 内容不一致**：本地副本（Aug 4）比 canonical 源（Aug 3）新，多了一段
  "lens-metric-enums 块未闭合时 fail-closed 报错"的健壮性修复（canonical 缺这段）。与本票
  的 RUN_SOP/embedded-test-sop/wayfinder/分支 B 清理无关，是一个独立的、canonical 落后本地
  的代码级 drift，不在本票范围内评估/修复——未覆盖本地这份"更新"的版本（未 `cp` canonical
  覆盖过去，避免回退掉这段健壮性修复）。
- **`docs/workflow-map.html`、`docs/workflow-console.html`**：仍含"分支 A（默认）"/"分支 B"
  措辞（各 1-3 处）。brief 的 companion 文档清单只列了 4 份 `.md`，这两份 `.html` 可视化视图
  不在列；Task 6 的残留扫描命令本身也只扫 `*.md`/`*.py`/`*.yaml`（不含 `*.html`），不会拦到
  这两处。未改动，登记供后续处理。
- **`sdflow-init/scripts/init.py` 的 `_marker_schema()` 校验过严 bug**：见上方"未跑
  `sdflow-init update` 的原因"一节，独立 bug，未修。

## 第二轮：全仓 pytest 揪出的第 4 处回归（sdflow-ship/tests/）

第一次全仓 `pytest -q`（后台任务，290s）在 2442 用例全绿之外，多挂了 1 个：
`sdflow-ship/tests/test_workflow_authority.py::test_orchestrator_entry_row` 断言
`workflow.md` 里同时含 `/sdflow-ship` 和字面串 `"5.5"`——Task 4 重写 `workflow.md` 步骤表后
阶段三步骤已连续编号为 5-8（写计划→SDD→代码审→done），不再有 5.5 半号步骤，这条断言测的
也是被删掉的东西，同属上面"顺带修复"的同一类回归（Task 1/4 完成时未跑到 `sdflow-ship/tests/`
这个具体用例，或跑的时候 workflow.md 还没被 Task 4 重写）。

顺带发现并纠正了我自己在"顺带修复 1"（`sdflow-ship/SKILL.md`）里犯的一个错：当时凭印象把
驱动区间写成"6→9"，而 `workflow.md` §二 步骤表的权威编号其实是**5→8**（三 | 5 |
/writing-plans；三 | 6 | SDD；三 | 7 | code-review；三 | 8 | done）——已改正
`sdflow-ship/SKILL.md` 的 description 与正文两处「6→9」「从步 6」为「5→8」「从步 5」，
并把 `test_orchestrator_entry_row` 的断言从检查"5.5 存在"改为检查"5→8 存在 且 5.5 不存在"
（双向锚：既验证新事实、也防旧措辞复活）。

## 验证

```
$ bash -n setup.sh                                             # 语法检查
syntax OK
$ /usr/bin/python3 -m pytest hack/tests/test_canonical_entry_sync.py -v
8 passed
$ /usr/bin/python3 -m pytest hack/tests/test_sdflow_spec_resident_contract.py -q
10 passed
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_setup_sdflow.py -q
20 passed
$ /usr/bin/python3 -m pytest sdflow-ship/tests/ -q
345 passed
$ /usr/bin/python3 -m pytest -q                                 # 全仓，第二轮（第一轮 2442 passed + 1 failed）
2443 passed, 10 skipped in 290.21s (0:04:50)
```

全仓 `pytest` 现全绿：**2443 passed, 10 skipped, 0 failed**。

## MUST NOT 遗漏声明

- 未勾 `tickets.md` Task 5 复选框（已核对仍为 `[ ]`）。
- 未带 checkpoint 标签。
- 未改 `openspec/changes/simplify-workflow/` 下除本报告外的其它文件。
