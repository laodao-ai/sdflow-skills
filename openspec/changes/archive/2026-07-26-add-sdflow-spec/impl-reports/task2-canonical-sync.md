# Task 2 实现报告 —— canonical 规则单一源不再分叉，四入口选择规则双落点生效

**R-ID**：SA-11 · SA-14 · SA-05 · SA-09
**基线 HEAD**：`9af8adc`（Task 1 收票后）
**结论**：`DONE_WITH_CONCERNS`（工作全部完成；Concerns 见文末，均为「已做但需下游知情」的连带影响，非未完成项）

---

## 一、SA-11 七处 canonical 源 —— 逐处改了什么

| # | 源 | 改了什么 | 证据锚 |
|---|---|---|---|
| 1 | `sdflow-init/assets/workflow/generation-process.md` | §四 推荐流水线**拆成两分支**（A = 已装 `sdflow-spec` 走单入口，B = 未装沿用 `explore→ff→grill`），并新增「四入口选择规则」四条（默认走 `/sdflow-spec` · 仅三种情形用旧三步 · 模型侧禁自选 `opsx:ff` · 旧三步仍是合法路径）；§五 skill 选择表加 `/sdflow-spec` 行并把 `opsx:explore` 标为「走分支 B 时用」；§八 检查清单加分支判定一行 | `:51-91`（§四）、`:96`（§五）、`:117`（§八） |
| 2 | `sdflow-init/assets/workflow/workflow.md` | §三决策 2（G1）加**具名例外**三条子项：例外本身 + **只许两条理由**（cache 按模型隔离 / 产 · 审错档）+ **MUST NOT 用「主审裁决需冷视角」** + 例外边界（仅这一处交界；阶段二内部与阶段三仍禁）。另：§一流程图加分支 A/B 框、§二步骤表新增 `| 一 | 0 | /sdflow-spec |` 行并给步 1/1b/2/3 打「〔分支 B〕」、§三决策 1 与 §六检查清单同步 FF-0 三分支判定 | `:102-104`（G1 例外）、`:85`（步骤表新行）、`:100`（决策 1）、`:135-139`（清单） |
| 3 | `sdflow-init/assets/workflow/reference/quality-layering.md` | G1 的**第二处载体**（措辞「无 `/clear`（G1）」）同步同一例外 + 同两条理由 + 同一条 MUST NOT；§六检查清单那条也补上例外 | `:107-113`（正文）、`:125`（清单） |
| 4 | `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md` | **改源后重生成**（`python3 hack/gen_workflow_guide.py --write`），阶段一段落现以「阶段一 · 步骤 0 — `/sdflow-spec`」开头；`openspec/workflow/WORKFLOW-GUIDE.md`（本仓副本）随 `init.py update` 刷新 | `:17-23`；`gen_workflow_guide --check` 绿（`setup.sh` 尾部输出） |
| 5 | `openspec/specs/spec-workflow/spec.md` | 两条既有阶段一衔接 Requirement 各自声明共存与路由：①「雾量三段分流」Requirement 前置**「新旧入口共存与路由」**六条（分支 A 默认 / 分支 B 三种例外 / 模型侧 / FF-0 三分支 / 单一源不得分叉），正文改为「分支 B 内，阶段一入口 SHALL 按雾量三分」，并加两条 Scenario；②「grill 对上游已决分支瘦跑」Requirement 开头限定**只约束分支 B** | `:970-976`（路由）、`:983`（分支 B 限定）、`:990-999`（新 Scenario）、`:1002`（瘦跑限定） |
| 6 | `sdflow-init/assets/snippets/claude-section.md`（托管块源） | ①**归属修正**：`grill-with-docs` 从「来自 superpowers 插件」改为「Matt Pocock 的 skills 集合（`~/.agents/skills`，仓外、非 git 管理）」——**实机核验**：`~/.agents/skills/grill-with-docs` 存在，机器上无 superpowers 插件缓存目录；②「ff 之后是 grill」条款**显式加分支**（「本条只管分支 B」+ 说明分支 A 的拷问在管线内且在成文之前 + 诚实边界「结构性改善非机械保证」），**未删除该条款**；③新增「阶段一入口二选一」与「开分支 = FF-0 三分支判定」两条；④配套 skill 表加 `/sdflow-spec` 行 | `:82-84`、`:95`、`:118-125` |
| 7 | `sdflow-init/assets/workflow/ff-generation-constraints.md` | FF-0 从「已在 feature 分支 → 跳过（幂等）」弱判据改为**三分支判定表**（保护分支建 / 本 change 分支跳过 / **其它 feature 分支 halt 问人**）+ MUST NOT 沿用弱判据的理由（stacking → ship_gate 污染）+ `checkout -b` 失败 fallback；hook 段同步描述三分支与 `SDFLOW_FF0_ACK=1` 逃生口；调用方注入语与 `prompts/step2-ff.md` 一并改写 | `:14-30`；`prompts/step2-ff.md:1` |

**托管块刷新机制**：`python3 sdflow-init/scripts/init.py update --root .`（该命令由 `AGENTS.md:107` 记载为托管块同步入口，非猜测）→ 再跑 `python3 hack/sync_principles.py --apply`。**未手改任何 `opsx-init:*` / `sdflow:principles:*` 区块内部**；`sync_principles.py --check` 现报「19 个投放面全部与真相源一致」。

---

## 二、逐条验收标准 → 证据

### ✅ 1. SA-11 七处逐处已同步，无一遗漏；托管区块经刷新机制生成

见上表。刷新机制的证据：`init.py update` 输出「CLAUDE.md：更新托管区块 / AGENTS.md：更新托管区块」；`sync_principles.py --check` 退出 0。

### ✅ 2. G1 例外在其**两处载体**上各自成立（分别核验）

两处**字面不同**，一条 grep 命不中两处，故分开断言：

- `workflow.md:101` 载体措辞 = 「**全流程不用 `/clear`**」→ 例外在 `:102`。
  守卫：`hack/tests/test_canonical_entry_sync.py::test_workflow_md_g1_still_states_the_rule` / `::test_workflow_md_g1_names_the_exception` / `::test_workflow_md_g1_exception_cites_exactly_the_two_allowed_reasons` / `::test_workflow_md_g1_exception_forbids_the_cold_view_reason`
- `quality-layering.md:107` 载体措辞 = 「**无 `/clear`（G1）**」→ 例外在 `:108-113`，检查清单在 `:125`。
  守卫：`::test_quality_layering_still_states_the_rule` / `::test_quality_layering_names_the_same_exception` / `::test_quality_layering_forbids_the_cold_view_reason` / `::test_quality_layering_checklist_carries_the_exception`

两处均**只写两条理由**，且均带一条「MUST NOT 拿主审裁决需冷视角当理由」的禁令（D6 要求删除的第三条依据）。

### ✅ 3. 机械核验的 grep 锚打得中真实结构，且非恒真

新增 `hack/tests/test_canonical_entry_sync.py`（19 个用例，全绿）。纪律与做法：

- **锚一律 `has_line()` 单行命中**——`generation-process.md` §四 与 `workflow.md` §一都是**跨行 ASCII 图**，`explore.*ff.*grill` 这类单行正则对它零命中（tasks 1.8 点名的空判据）。故本文件**只锚图周边的单行散文/表格行，不锚图**。
- **每条锚做过定点变异回验**：跑了一轮 23 处变异（把被锚那句话改掉 → 对应用例必须红），**23/23 全红、零存活**。变异清单与结果见下表（脚本一次性执行，文件已原样还原，`git diff` 无残留）：

| 变异点 | 期望变红的用例 | 结果 |
|---|---|---|
| generation-process「默认走 \`/sdflow-spec\`」→「默认走 \`/opsx:ff\`」 | `test_generation_process_states_entry_selection_rule` | ✅ 红 |
| generation-process「仅下列三种情形用旧三步」→ 弱化措辞 | 同上 | ✅ 红 |
| generation-process「分支 A」→「路线 A」（全量） | `test_generation_process_has_two_branches` | ✅ 红 |
| generation-process「grill-with-docs」→「grill-xx」 | `test_generation_process_keeps_legacy_path_alive` | ✅ 红 |
| workflow「全流程不用 \`/clear\`」→「全流程禁用 \`/clear\`」 | `test_workflow_md_g1_still_states_the_rule` | ✅ 红 |
| workflow「「阶段一 → 阶段二」交界」→「这一段交界」 | `test_workflow_md_g1_names_the_exception` | ✅ 红 |
| workflow「cache 按模型隔离」→「缓存隔离」 | `..._cites_exactly_the_two_allowed_reasons` | ✅ 红 |
| workflow「产 / 审错档」→「产审错档」 | 同上 | ✅ 红 |
| workflow 把冷视角禁令改成「另一条理由是…」 | `..._forbids_the_cold_view_reason` | ✅ 红 |
| quality-layering「无 \`/clear\`（G1）」→ 改写 | `test_quality_layering_still_states_the_rule` | ✅ 红 |
| quality-layering「具名例外」→「备注」（全量） | `test_quality_layering_names_the_same_exception` | ✅ 红 |
| quality-layering 把冷视角禁令改成「另一条理由是…」 | `test_quality_layering_forbids_the_cold_view_reason` | ✅ 红 |
| quality-layering 检查清单那行去掉例外 | `test_quality_layering_checklist_carries_the_exception` | ✅ 红 |
| ff-constraints「三分支判定」→「两分支判定」（全量） | `test_ff0_rule_is_three_way` | ✅ 红 |
| ff-constraints「**halt 问人**」→「跳过」 | 同上 | ✅ 红 |
| ff-constraints「SDFLOW_FF0_ACK=1」→ 改名 | `test_ff0_rule_and_hook_agree_on_the_escape_hatch` | ✅ 红 |
| **hook**「SDFLOW_FF0_ACK=1」→ 改名（只改一侧） | 同上 | ✅ 红 |
| claude-section「本条只管分支 B」→「本条一律适用」 | `..._scopes_the_grill_clause_to_branch_b` | ✅ 红 |
| claude-section「Matt Pocock 的 skills 集合」→「superpowers 插件」 | `test_claude_section_attribution_is_fixed` | ✅ 红 |
| claude-section「阶段一入口二选一」→「阶段一入口」 | `..._carries_the_entry_selection_rule` | ✅ 红 |
| spec-workflow「新旧入口共存与路由」→「入口说明」 | `test_spec_workflow_declares_coexistence_and_routing` | ✅ 红 |
| spec-workflow「MUST NOT 沿用…弱判据」→ 改写 | 同上 | ✅ 红 |
| WORKFLOW-GUIDE「步骤 0 — \`/sdflow-spec\`」→ 改名 | `test_generated_guide_reflects_the_new_entry` | ✅ 红 |

- **一次修正**：初版把「冷视角」写成「全文所有含冷视角的行都必须带 MUST NOT」——**假红**：`workflow.md:59` 那句「sdflow-code-review 每次全跑·独立冷视角·强制主审」是在说 code-review，不是在给例外找理由。已改为「存在一条 `MUST NOT` + `冷视角` 的禁令行」这一精确判据（并在用例 docstring 里写清为什么不能用前者）。
- **人核残余如实登记**（`test_canonical_entry_sync.py` 末尾 `MANUAL_ONLY` 常量，MUST NOT 硬造恒真锚）：① `generation-process.md` §四 两张 ASCII 流水线图本体；② `workflow.md` §一 阶段一流程图分支框；③「三种例外情形语义是否互斥且穷尽」（无确定性信号）。

> ⚠️ **与 tasks.md 测试覆盖图的偏差（如实登记，未改 tasks.md）**：覆盖图把 generation-process / WORKFLOW-GUIDE / spec-workflow / claude-section / ff-generation-constraints 五处标为「人核 ❌」。实际写下来，这五处的**新增条款都落在单行散文/表格行上**，存在可靠单行锚点，故按基准 1（机械化优先）与基准 3（面治）一并机械化并做了变异回验。留人核的只有上面三条真无信号的。**这是覆盖增强，不是范围变更**。

### ✅ 4. 生成物已随源重生成，其阶段一段落反映新分支

`python3 hack/gen_workflow_guide.py --write` → 9877 字节；`WORKFLOW-GUIDE.md:17` 起为「## 阶段一 · 步骤 0 — `/sdflow-spec`」，步骤 2 的 prompt 全文已带 FF-0 三分支判定。一致性由既有 `hack/tests/test_workflow_split.py::test_guide_is_in_sync_with_its_sources` 守（全量 pytest 绿）。**未手改生成物。**

### ✅ 5. FF-0 三分支判定在规则文本与其 hook 实现上一致

- 规则文本：`ff-generation-constraints.md:14-30`（三分支表 + hook 段）。
- hook 实现：`sdflow-init/assets/hooks/ff0-branch-guard.py` —— 新增 `CHANGE_NAME_RE`（从命令取 change 名）、`CHANGE_NAME_OK_RE`（名字须是 `[A-Za-z0-9._-]+`）、`ACK_RE`；`main()` 现为三分支：保护分支 deny / `feat/{该 change}` 放行 / 其它 feature 分支 deny（人 ack 后放行）。
- **基准 5 遵守**：shell 命令行语法面无界 ⇒ 只认 `openspec new change <bare|'q'|"q">` 这一种**有界**形态，认不出就 **fail-open 放行**（沿用文件既有 fail-open 纪律），**没有新增任何「语法不支持」的罢工分支**。`"$NAME"` 这类待展开 token 被 `CHANGE_NAME_OK_RE` 挡回 fail-open（有专门用例）。
- 新增行为测试 `sdflow-init/tests/test_ff0_branch_guard.py`（**11 用例全绿**，真跑 hook 进程 + 真 git 仓）：保护分支 deny / 同 change 分支放行（含三种引号变体）/ **其它 feature 分支 deny** / 人 ack 后放行 / 取不到名 fail-open / 非 openspec 命令放行 / 非 Bash 工具放行 / 非 git 目录 fail-open。
- **变异回验**：把 hook 改回旧行为（分支②③合并为放行）→ `test_other_feature_branch_denies` 变红（`1 failed, 10 passed`），证明这条用例非恒真。

### ✅ 6. 四入口选择规则在人读侧与 AI 读侧各有一份，内容不矛盾

- **人读侧**（非托管区，手写）：`CLAUDE.md` / `AGENTS.md` 新增章节「阶段一入口：`/sdflow-spec` 使用路径 · 四入口选择规则 · 旧入口 sunset 条件」（CLAUDE.md `:186-233`，AGENTS.md `:105-152`，后者插在「## 修改与安全约定」前）。含使用路径四步（含出口序列与只许两条理由）+ 四入口选择规则 + sunset。
- **AI 读侧**：`generation-process.md:83-88`（canonical 阶段一流程分支）+ `openspec/specs/spec-workflow/spec.md:970-976`（正式 Requirement）+ 托管块 `claude-section.md:82`。
- **不矛盾**：三处的默认路径、三种例外情形（wayfinder 铺图 / 用户要求分步 / 环境不可用）、模型侧禁令**逐字同义**；人读侧顶部显式写明「AI 读侧在哪几个文件，改一处就改另一处」。

### ✅ 7. 旧入口 sunset 条件已写死阈值与未达标处置

落在 `CLAUDE.md` / `AGENTS.md` 新章节的「旧入口 sunset 条件」小节。**无 TBD / 无占位符**：

- **观察窗** = 上线后连续 **6 个新开 change** 或 **8 周**，先到者为准。
- **采用率** ≥ **5/6（83%）**；命中三种合法例外且在报告说明的那次不计入分母。依据：容一次漏网，再多即说明默认路径没立住。
- **质量** = 这些 change 的阶段二 spec-review「上下文缺失 / 需回问阶段一」类 finding 累计 **= 0**（proposal Success Metrics 口径），且 findings **采纳率 ≥ 0.79**。依据：`openspec/retro/report.md` 22 个带真锚 change 的采纳率**中位 0.855、P25 ≈ 0.795**（实算，取 P25 为下限）。
- **成本** = 阶段一墙钟中位 **≤ 75 min/change**。依据：retro 现基线 `ff` 1691.5 min + `grill` 345.4 min 摊到 40 个 change ≈ **51 min/change**（粗口径，`unknown` 桶占 56% 使真实值偏高），取 1.5×。
- **处置二选一**：三档全达标 ⇒ 旧三步进 sunset（CLAUDE.md 与 canonical 改措辞为「仅作三种例外的 fallback」，三个 skill 本体不删）；**任一档不达标 ⇒ 删除 `sdflow-spec`**（删目录 + README 条目 + 重跑 `setup.sh` 清孤儿 + 回滚 canonical 七处的分支 A 段落）。**MUST NOT 无限期延窗**——延窗须人拍板并把新窗口写回该节。
- 该条款**与阶段二成败无关**（窄复核订正要求的前移），文中显式写明。

### ✅ 8. README 含 `sdflow-spec` 且有可复制 Quick Start；双 runtime 可见

- `README.md:10-27` 新增 **Quick Start**（clone+setup 一段 bash + 项目内逐条敲的命令块，含出口序列与「模型唤不起」提示 + 未装时走旧三步的一行说明）。
- `README.md:38` Skills 列表新增分类「生成（阶段一）」的 `sdflow-spec` 行。
- `bash setup.sh` 重跑：`✓ sdflow-spec @ ~/.claude/skills`、`✓ sdflow-spec @ ~/.codex/skills`；`ls -la` 实证两侧软链均指向本仓 `sdflow-spec`。再跑一次幂等（同样 40 个 ✓）。

---

## 三、全量验证

| 命令 | 结果 |
|---|---|
| `/usr/bin/python3 -m pytest`（仓根全量） | **2683 passed, 10 skipped, 3 xfailed**（267s）。已知抖动用例 `test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret` 本轮**通过** |
| `bash setup.sh` | 绿、幂等；`sync_principles ✅ 19 个投放面一致` / `gen_workflow_guide ✅ 与单一源一致` / `async-branch-parity ✅` |
| `/usr/bin/python3 hack/sync_principles.py --check` | ✅ 19 个投放面全部与真相源一致 |
| `/usr/bin/python3 -m pytest hack/tests/test_canonical_entry_sync.py` | 19 passed |
| `/usr/bin/python3 -m pytest sdflow-init/tests/test_ff0_branch_guard.py` | 11 passed |
| `git diff` 亲验 | 17 改 + 2 新增文件，见下 |

**改动文件**：`sdflow-init/assets/workflow/{generation-process,workflow,ff-generation-constraints,WORKFLOW-GUIDE}.md`、`.../reference/quality-layering.md`、`.../prompts/step2-ff.md`、`sdflow-init/assets/snippets/claude-section.md`、`sdflow-init/assets/hooks/ff0-branch-guard.py`、`openspec/specs/spec-workflow/spec.md`、`openspec/workflow/WORKFLOW-GUIDE.md`、`openspec/CONTEXT.md`、`openspec/adr/0008-*.md`、`CLAUDE.md`、`AGENTS.md`、`README.md`、`docs/workflow-overview.md`、`docs/workflow-map.html`
**新增**：`hack/tests/test_canonical_entry_sync.py`、`sdflow-init/tests/test_ff0_branch_guard.py`

---

## Concerns

### C1（**最需要人知情**）FF-0 三分支判定与 `adr/0008` 的既有决议正面相邻，我按「决议不变、实证更新」处置

`adr/0008` 的 Considered Options 里**明确否决过**「在 FF-0 里拦 stacking」，两条理由：① FF-0 是通用跨项目守卫，stacking 有时是合法工作流，不该一刀切禁；② 把正确性寄托于「入口守卫无漏」违反防御纵深。而 SA-05/SA-11 要求的三分支判定**部分做了那件事**。

我的处置（未改 ADR 的决定，只加一段现状更新）：

- 理由①由 **ack 逃生口**满足 —— 新判据挡的是「静默默认发生」，不是「禁止 stacking」；人拍板后 `SDFLOW_FF0_ACK=1` 即可继续。
- 理由②**完全不受影响** —— 守卫仍可绕过（人 ack / fail-open 分支 / 手工 `git` / 非 Bash 入口），故 `ship_gate` 的 change-命名空间隔离 **MUST NOT** 因「现在 FF-0 会拦了」而被撤掉。
- 连带改了三处引用该实证的文本（否则它们变成事实错误）：`openspec/CONTEXT.md` 的 **Stacking 术语条**、`adr/0008` 末尾新增「〔现状更新〕」小节、`openspec/specs/spec-workflow/spec.md:522` 的 Scenario 括注。

**若人认为 ADR 的否决应当压过 SA-05，则 hook 那一支应回退为「只在文档层要求 halt、hook 不 deny」** —— 这是一次拍板，不是我能替人做的判断。当前实现按 spec（SA-05 明写 MUST NOT 沿用弱判据、SA-11 第 7 项明写「同步 hook」）执行。

### C2 全局副作用：`init.py update` 已把新 hook 装到 `~/.claude/hooks/`

`sdflow-init/scripts/init.py update --root .` 是托管块的刷新入口，但它**顺带幂等确保全局 FF-0 hook**，输出「ff0-branch-guard.py：脚本已更新 `/Users/cheneyzhao/.claude/hooks/ff0-branch-guard.py`」。⇒ **本机所有项目**从现在起都按三分支判定拦 `openspec new change`。这是该 hook「全局装一次、跨项目生效」的既有设计（`sdflow-init/SKILL.md:226`），非本票新引入的机制，但生效面确实扩大了，记此备知。回退 = `git checkout` 该 asset 后重跑 `init.py update`。

### C3 本票只改源，未推下游

canonical 改动按 tasks 8.2 属**阶段三**（`sdflow-init update` 推消费项目）。本仓自身的 `openspec/workflow/WORKFLOW-GUIDE.md` 副本已随 `init.py update` 刷新；其余消费项目仍是旧规则，直到它们各自跑 update。

### C4 覆盖增强超出 tasks 覆盖图的声明

见验收标准 3 的 ⚠️ 段：覆盖图声明「五处人核」，实际把其中可靠单行锚点的部分机械化了（并变异回验）。**未修改 `tasks.md`**（设计门产物，实现期不得改）——若要让覆盖图与实现一致，应在 `sdflow-done` 的 archive 阶段一并订正。
