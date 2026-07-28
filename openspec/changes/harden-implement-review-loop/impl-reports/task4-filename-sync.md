# Task 4 impl-report — 文件名措辞全量同步（宽重构迁移批次）

R-ID: R-tickets（出 ticket 模式产出 tracer-bullet ticket）

## 交付内容

tickets 轨在指令、bundle 规则、文档、既有测试断言四类面上一致地称呼新计划文件名
`tickets.md`；superpowers 轨的引用（`superpowers-plan.md`）原样保留，逐条可归因；历史记录面
（归档 change、issues 池、指向归档文件的 docstring 实路径）一律未动。本票不改
`ship_gate.py`/`impl_route.py` 的脚本逻辑（Task 3 已落地共享 resolver），只做措辞同步。

### 改动文件

**skill 指令面（§5.4/§5.5）**

- `sdflow-implement/SKILL.md`：外衣落盘路径 `{change_dir}/superpowers-plan.md` → `tickets.md`；
  `frontier`/`task-text` 调用示例、信号权威表「本票完成信号」行、`ship_gate.py 零改动`说明段，
  同步改为 `tickets.md`，并各处补一句指向 D5/adr-0033（明确 superpowers 轨仍用旧名、两名经
  共享 resolver 定位）。`:227` 指向 `matt-workflow-integration` 归档 plan 的历史引用未改
  （该引用本身路径缺归档日期前缀，是本票之外的既有问题，不在本票范围）。
- `sdflow-done/SKILL.md:189`："实现常经 `superpowers-plan` / subagent-driven-development 完成"
  改为同时列出 `tickets.md`（sdflow-implement 出票管线）与 `superpowers-plan.md` /
  subagent-driven-development，并注明 D5 分列关系——该句原描述"任何实现管线都可能不勾
  `tasks.md`"，D5 后需要覆盖两条轨都不漏。

**bundle 面（§5.6）**

- `sdflow-init/assets/workflow/workflow.md:94`（步骤表第 6 行）：规则·条件列补一句
  "tickets 轨产出改名为 `tickets.md`〔D5/adr-0033〕，两轨计划文件名分列，gate/route 经共享
  resolver 定位"；prompt 指针列补"本步骤只管 superpowers 轨，产出文件名不变"（放在
  `rule` 列而非 `prompt_cell` 列——`hack/gen_workflow_guide.py` 的 `render()` 只把
  `prompt_cell` 里 `**→` 之前的片段带进生成物，放错列会被生成器静默丢弃，已实测验证）。
  `产出物` 列 `superpowers-plan.md + 代码` 未改——描述的是 superpowers 轨真实产出，D5 不影响。
- `prompts/step6-writing-plans.md`：**未改**。该文件全文只有一行，是给人复制粘贴去调用
  `/writing-plans`（外部 superpowers skill）的原始 prompt 文本，仓内所有引用处都标注"原样
  复制，勿转述"。D5 只影响 tickets 轨的落盘文件名，`/writing-plans` 本身仍应生成
  `superpowers-plan.md`（superpowers 轨名不变），故该行提示文字本身无需改字；"明确其只管
  superpowers 轨"这一澄清放在 `workflow.md` 的规则列（上面一条），而非塞进这份会被原样粘贴
  执行的 prompt 正文里污染实际调用文本。
- `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`：运行 `python3 hack/gen_workflow_guide.py
  --write` 从更新后的 `workflow.md` + `prompts/*.md` 重新生成（禁手改，`--check` 复核已过）。
- `openspec/workflow/WORKFLOW-GUIDE.md`（仓内托管副本）：`cp` 自上一步生成物，与源一致。

**文档面（§5.8）**

- `docs/criteria-mechanization-tracker.md` 5b.1 行：写锚点从单一 `superpowers-plan.md` 改为
  "`tickets.md`（tickets 轨）/ `superpowers-plan.md`（superpowers 轨，D5/adr-0033）"，用锚点
  补充"共享 resolver 按序探测两名，双存在 fail-closed"——该文档明确"接地自源码"，须反映
  resolver 落地后的真实行为。
- `docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md` Q3 行：追加一句"Phase B 已在
  `harden-implement-review-loop` 拍板落地（`adr/0033`）"，与该文件自己此前明文"终局文件名
  迁移...留 Phase B 拍板"的记录闭环；`:62/:74/:94` 三处描述 2026-07-10 探索会当时观察到的
  ship_gate 状态，属历史record，未改。
- `openspec/INDEX.md` `impl-orchestration` 行：`出 ticket 契约` 括号内"外衣
  `superpowers-plan.md`"改为"外衣 `tickets.md`〔superpowers 轨保留 `superpowers-plan.md`，
  两名经共享 resolver 定位，双存在 fail-closed，D5/adr-0033〕"——该行是当前态描述（非历史
  record），须反映 D5 后的真实契约。
- **审计后确认无需改动**（既有内容已准确描述 superpowers 轨、未提及 tickets 轨文件名，
  D5 不影响其正确性）：`docs/workflow-overview.md`、`docs/workflow-map.md`、
  `docs/workflow-map.html`、`docs/workflow-console.html`、
  `docs/workflow-skills/superpowers-writing-plans.md`、
  `docs/workflow-skills/superpowers-subagent-dev.md`——这几份文档目前**完全未提及**
  `sdflow-implement`/tickets 轨的计划文件名（只讲 superpowers `writing-plans` 这一个黑盒
  技能自己的契约），逐条读过确认其中的 `superpowers-plan.md` 引用全部准确描述 superpowers
  轨、D5 未触及。补一整段"tickets 轨也存在"的新增内容会是加宽（通则③ MUST NOT 顺手扩大
  改动面），不在本票"文件名措辞同步"范围内。

**测试断言面（§5.7）**

- `sdflow-implement/tests/test_impl_route.py`：7 处生成通用 fixture 的字面量（`:173` 缺失文件
  判断、`:262/:275/:288/:299/:326` marker/route 各类通用用例、`:733` `task-text` CLI 示例）
  从 `superpowers-plan.md` 改为 `tickets.md`——这些用例测的是 marker 解析/路由逻辑，与"用哪个
  文件名"无关，改字面量纯粹是措辞对齐。`:370/:376`（Task 3 新增的
  `test_cli_route_both_plan_names_present_fails_closed`，**故意**同时写两个文件名以触发双存在
  冲突）保留不动。
- `sdflow-ship/tests/test_gate_impl_progress.py`：`:120`（`test_plan_task1_same_commit_counts`）
  与 `:139`（`test_uncommitted_plan_no_checkbox_unknown`）两处**独立**写盘（不经共享
  fixture）改为 `tickets.md`。`:30`（`approved_change` 共享 fixture 内部）**保留
  `superpowers-plan.md` 不变**——见下方「过程中发现并修复的问题」。
- `sdflow-ship/tests/test_gate_freshness.py`：`:480` 起的 5.1 用例
  `test_impl_source_edits_and_plan_checkbox_flip_keep_design_fresh` **保留
  `superpowers-plan.md`**（原因同上，该用例经 `_approved_with_tasks` → `approved_change`
  共享 fixture 写盘）；加了一句注释解释为何不能改。
- `hack/tests/test_checkpoint_slug_coverage.py:25`：docstring 里"非 producer"分类描述的
  `superpowers-plan.md` 改为"计划文件 `tickets.md` / `superpowers-plan.md`〔D5：两轨计划
  文件名分列〕"——该行只是散文描述，不是断言，纯措辞对齐。
- `hack/tests/test_harden_sdflow_spec_followup_closure.py:39`：**未改**。`PLAN = CHANGE /
  "superpowers-plan.md"` 指向的是已归档 change `archive/2026-07-27-harden-sdflow-spec-followups`
  的**真实磁盘文件**（该 change 走的是 superpowers 轨，其 plan 文件名从未是 tickets 轨范畴，
  D5 不适用），测试读取该文件真实内容核验 R-ID 标注。改字面量会让测试指向一个不存在的路径、
  当场报错——已通过 `test_gate_impl_progress.py`/`test_gate_freshness.py` 那次真实回归验证过
  "改一个被多处消费的字面量前必须 grep 全部消费方"这条教训，此处提前核实后判定不改。

**不动面（§5.9，已核实原样保留）**

- `openspec/changes/archive/**`、`openspec/issues/**` 的历史记录：未碰。
- `openspec/adr/0017`：只在末尾追加一行〔追记，`harden-implement-review-loop`〕指向
  `adr/0033`，正文 0-37 行逐字未改。
- `sdflow-implement/scripts/impl_route.py`（`:5,:21` 两处指向 archive 归档文件的 docstring
  实路径）：未碰，本票也未改动该脚本任何逻辑或字面量。

**新增（§6.2）**

- `openspec/adr/0033-tickets-plan-filename-split-by-track.md`：记录本次拍板——分轨命名 +
  共享 resolver 双存在 fail-closed（选中）；砍掉候选①全局统一改中性新名（如
  `impl-plan.md`）②只改文档不改脚本；含回滚代价（在途 change 若已用新名需人工改回、且要
  注意改名本身触发窗口锚推后的风险）。

## 过程中发现并修复的问题（共享 fixture 耦合，未列入原始改动面但必须处理）

`sdflow-ship/tests/test_gate_impl_progress.py` 的 `approved_change(...)` 是**跨 6 个测试文件
共享的 fixture**（`test_gate_namespace.py` / `test_gate_git_layer.py` / `test_plan_resolver.py` /
`test_gate_reviewed_sha.py` / `test_gate_tail.py` / `test_gate_freshness.py` 均
`from test_gate_impl_progress import approved_change, PLAN2`）。首轮编辑把 `approved_change`
内部写盘的文件名也改成了 `tickets.md`——这破坏了 `test_plan_resolver.py` 里依赖"该 fixture
写旧名"的用例语义（`test_both_plan_names_present_gate_fails_closed_unknown` 靠它先落盘旧名、
再手动追加新名制造双存在冲突；`test_inflight_plan_rename_rejected_as_unknown` 靠它先落盘旧名
再 `git mv` 到新名模拟违规改名），全量 pytest 首次运行时在这两个用例上真实红了（`git mv`
报 `fatal: bad source`，因为源文件根本不叫这个名字）；`test_gate_freshness.py` 的
`test_impl_source_edits_and_plan_checkbox_flip_keep_design_fresh` 也因为"共享 fixture 写旧名 +
本用例另写新名"两个文件同时落盘触发 resolver 的双存在 UNKNOWN 判定而变红。

已修复：`approved_change` 内部写盘字面量**改回** `superpowers-plan.md`（并加注释说明为何
不能改），`test_gate_freshness.py` 的对应用例同步改回、加注释；`test_gate_impl_progress.py`
里**不经过**共享 fixture 的两处独立写盘（`:120`/`:139`）维持改为 `tickets.md`。这是本仓
memory 记录过的教训（"改共享字符串前先全量 grep 消费方，别只看字面量匹配"）在函数级共享
状态上的复现——字面量搜索找不到"谁 import 了这个函数"，只有跑全量测试才能暴露。

## 附带清理：T135 todo 闭环

`openspec/issues/todolist/2026-07-todolist.md` 的 **T135**（"tickets 管线 plan 文件名不应
硬编码为 superpowers-plan.md"）动机与本票交付完全重合；Task 3 的 impl-report 明确写"T135 的
完整关闭需 Task 4 的文件名全量改名落地后才闭环，本票不越权代 Task 4 关闭"。本票用
`sdflow-issues/scripts/todolist.py set-status --id T135 --to DONE --evidence
"harden-implement-review-loop:task3(resolver)+task4(rename)"` 走正规 overlay 机制关闭
（frontmatter 侧 `status: DONE`，legacy 表冻结行仍显示 `OPEN`——与 T66/T67/T85/T146 等既有
先例同构，非"改写历史记录正文"）。该操作会触发 `sdflow-issues` 的
`test_repository_legacy_corpus_matches_independent_projection_item_by_item` 契约测（legacy
行与 frontmatter overlay 对拍需要登记 delta，否则 `KeyError`）——已在
`sdflow-issues/tests/test_task5_delivery_contract.py` 的 `DOGFOOD_OVERLAY_DELTAS` 新增
`"T135": {"status": ("OPEN", "DONE")}` 一行，与既有条目同构。

## §7.3 全仓 grep 归因表（非 archive、非 issues、非本 change 自身路径）

不带 `--include` 全量 `grep -rln "superpowers-plan"`，剔除 `openspec/changes/archive/**`、
`openspec/issues/**`、`openspec/changes/harden-implement-review-loop/**` 后逐条归因表如下
（计数以表为准，不在正文重复硬编码——本表自身即含被同一 grep 扫到的字符串，任何后续编辑都会
让绝对计数过期，Task 2 §7.1 已被同一模式咬过一次）；表格所反映的快照 = commit `4b1145a`
（本 impl-report 首次落盘所在提交）：

| 文件 | 归因 |
|---|---|
| `docs/criteria-mechanization-tracker.md` | 本票已同步（双名 + resolver 行为） |
| `docs/workflow-console.html` | ①superpowers 轨"writing-plans"卡片，未提及 tickets 轨，无需改 |
| `docs/workflow-map.html` | ①同上（3b 行 HTML 镜像） |
| `docs/workflow-map.md` | ①同上（3b 行 markdown 源） |
| `docs/workflow-overview.md` | ①同上（§4.1 表 + §5 黑盒表两处），全文未提 tickets 轨文件名 |
| `docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md` | ①②混合：Q3 行本票已补 Phase B 闭环note；`:62/:74/:94` 是 2026-07-10 探索会历史记录，未改 |
| `docs/workflow-skills/superpowers-subagent-dev.md` | ①superpowers 轨黑盒详解页，未提 tickets 轨 |
| `docs/workflow-skills/superpowers-writing-plans.md` | ①同上 |
| `hack/tests/test_checkpoint_slug_coverage.py` | 本票已同步（docstring 措辞） |
| `hack/tests/test_harden_sdflow_spec_followup_closure.py` | ②指向真实归档文件（superpowers 轨的 `2026-07-27-harden-sdflow-spec-followups/superpowers-plan.md`），未改 |
| `openspec/adr/0017-tickets-pipeline-gate-contract-veneer.md` | ②Accepted ADR 正文未改；本票仅追加一行指针到 adr/0033 |
| `openspec/adr/0033-tickets-plan-filename-split-by-track.md` | ①本票新增，描述分轨方案本身 |
| `openspec/INDEX.md` | 本票已同步 |
| `openspec/specs/impl-orchestration/spec.md` | ④主 specs——本 change 未归档，仍反映 pre-D5 状态；delta（`openspec/changes/harden-implement-review-loop/specs/impl-orchestration/spec.md`）已是 D5 后措辞，`sdflow-done` 归档时才会同步进主 specs，非本票范围 |
| `openspec/specs/spec-workflow/spec.md` | ④同上 |
| `openspec/workflow/WORKFLOW-GUIDE.md` | 本票已同步（托管副本，随 assets 源重新生成） |
| `sdflow-done/SKILL.md` | 本票已同步 |
| `sdflow-implement/scripts/impl_route.py` | ①resolver 契约本体（`PLAN_FILENAMES` 常量等）+ ②两处 archive 归档路径 docstring；Task 3 落地，本票未碰任何脚本逻辑 |
| `sdflow-implement/SKILL.md` | 本票已同步；剩余 `:227`（历史归档路径引用，②）与"superpowers 轨保留旧名"的说明性提及（①）合法 |
| `sdflow-implement/tests/test_impl_route.py` | 本票已同步 7 处；剩余 2 处是 Task 3 新增的双名冲突测试（①），故意保留 |
| `sdflow-init/assets/workflow/prompts/step6-writing-plans.md` | ①单行 prompt 文本，字面描述 superpowers 轨真实产出，未改（见上方"bundle 面"说明） |
| `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md` | 本票已同步（生成物） |
| `sdflow-init/assets/workflow/workflow.md` | 本票已同步 |
| `sdflow-ship/scripts/ship_gate.py` | ①resolver 契约本体，Task 3 落地，本票未碰 |
| `sdflow-ship/tests/test_gate_freshness.py` | ①共享 fixture 依赖旧名（见上方"过程中发现并修复的问题"），保留 |
| `sdflow-ship/tests/test_gate_impl_progress.py` | ①同上，`approved_change` 共享 fixture 保留旧名；2 处独立写盘已改新名 |
| `sdflow-ship/tests/test_plan_resolver.py` | ①Task 3 专门测试双名/改名场景的文件，本票未碰 |

## 自验（本票最高危红线）

```
python3 sdflow-ship/scripts/ship_gate.py --change harden-implement-review-loop --root "$(git rev-parse --show-toplevel)"
```

输出：`CONTINUE_IMPL → next=subagent-dev — 实现进度 3/6（窗口 [87e2dde, HEAD] 闭区间，集合归属）`，
`done_tasks: ["1", "2", "3"]`——Task 1/2/3 完成信号未受影响，本 change 自己的
`superpowers-plan.md` 全程未被本票触碰（既未改名、也未新建 `tickets.md`）。

## 测试执行范围

全量 `/usr/bin/python3 -m pytest`（本票是全仓字符串同步 + 共享 fixture 修复，回归面即全仓）：

| 层 | 命令原文 | 退出码 | 测试时 HEAD（工作树，本票提交前） |
|---|---|---|---|
| sdflow-issues（T135 overlay 验证） | `/usr/bin/python3 -m pytest sdflow-issues/ -q` | 0（669 passed, 7 skipped, 3 xfailed） | 87e2dde（工作树） |
| sdflow-ship + sdflow-implement（共享 fixture 回归） | `/usr/bin/python3 -m pytest sdflow-ship/tests/ sdflow-implement/tests/ -q` | 0（421 passed） | 同上 |
| 全仓回归 | `/usr/bin/python3 -m pytest -q` | 0（**2908 passed, 11 skipped, 3 xfailed**） | 同上 |

与本票起手基线（`2908 passed, 11 skipped, 3 xfailed`）逐位对齐，无一条因本票改动变红或消失。

## 完成信号（后置，本票不自行勾选/打标签）

按信号权威表，本票完成信号（复选框全勾 + `checkpoint(harden-implement-review-loop:task4-…)`
标签）由双轴审通过后补打，实现期未创建该标签、未勾 `superpowers-plan.md` 复选框、
未改动 `proposal.md`/`design.md`/`tasks.md`/`specs/`。本票**已真实 commit**（见下）。
