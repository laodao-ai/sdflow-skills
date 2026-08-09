# Task 2：spec-review SKILL 重写与同源注入机制 — 实现报告

## 范围

`openspec/changes/absorb-gstack-autoplan/impl-reports/task2-brief.md` 全 6 项 + 7 项验收，逐项完成。

## 1. `sdflow-spec-review/SKILL.md` 重写（tasks.md 2.1）

- **frontmatter description**：删 autoplan 提法，改述为「自持广审双镜（strategy/plan-eng）+ 领域镜/对抗镜/接地镜 + design-voice，单批并行 dispatch」。
- **正文重写**：
  - 旧「## 第一步：autoplan 子步（广审·原生执行）」+「## 第二步：规划镜头 + 并行 fan-out 子代理」合并为
    「## 第一步：能力探针 + 规划镜头 + 单批 dispatch（广审双镜 + 领域镜 + 对抗镜 + 接地镜 + design-voice）」。
  - 删除「两段 dispatch」时序图（dispatch①/dispatch②）与「串行纪律〔T20〕分治」条款——单批 dispatch 下
    全部镜互不依赖、均评审当前盘面，等待理由消失（DD1）。
  - 新增单批 dispatch 时序图：能力探针 → 单批（strategy/plan-eng/领域/对抗/接地/design-voice）→ Step3 合并裁决 → Step4 产出。
  - 镜表新增 strategy/plan-eng 两行（内容由 `### 广审镜` 小节的托管块承载，见第 2 节）；删除「与 autoplan 的分工」表
    与「防重叠（1.4）」条款，替换为「base 与 domains 二分」分工线（base 归广审镜、domains 归领域镜，两清单本就互斥）。
  - Step3（综合裁决）：合并去重描述从「autoplan findings（Step1）+ 各镜」改为「广审双镜 + 领域镜 + 对抗镜 + 接地镜」；
    checkpoint 从「P2c 第 2 次」改为「P2c 唯一一次」（旧广审子步的独立 checkpoint 已随单批 dispatch 合并退役）。
  - Step4（产出）：lens-metric roster 段新增显式折叠说明——strategy/plan-eng 为非-outside-voice 普通镜，均折叠到
    同一 canonical `lens="broad"` 行键（`runner==host`, `site="—"`），两镜各自 findings 以 `hits:[{"raw":"strategy"}]`
    / `hits:[{"raw":"plan-eng"}]` 计入，由 emitter 读 fold 表归属（DD1/DD4，tasks.md 2.4）。
  - 决策登记区示例 ASCII 图里的 `autoplan/裁决已定` 改为通用措辞 `某镜发现,裁决已定`（DOC-1，避免示例字面量残留已退役工具名）。
- **验收**：`grep -n "autoplan\|gstack" sdflow-spec-review/SKILL.md` 归零（含历史/rationale 措辞——全部改写为不含字面量的表述，如"外部工具"/"广审产物落盘复用判定"）。

## 2. `step1-broad-review` 锚枚举换值（tasks.md 2.2）

`mode="native|simulated"` → `mode="subagent|main-session"`：`subagents="available"` 时 `mode="subagent"`
（strategy/plan-eng 均以 fresh 子代理执行）；`subagents="unavailable"` 时 `mode="main-session"`（主 session
亲做两镜判断，`mirrors=` 仍计入 `broad` token）。诚实边界声明保留：mode 值为主 session 自报，`anchor_lint`
只验族存在性（前缀匹配），不校验枚举值，MUST NOT 声称机械保证——与 design DD3 一致；`anchor_lint.py` 本身零
代码改动（Task 1 已确认该锚族只做存在性校验，本票无需再动脚本）。

## 3. Step1 四环节删除 + design-voice 转正（tasks.md 2.3）

删除：① autoplan 原生执行步骤 ② 主 session 落盘 `gstack-review.md`（`[gstack-amendment]`）③
`outside_voice_guard.py` 调用（reason_code 三前置判定 + 复用/回落分支）④ `checkpoint-commit.sh
spec-review-autoplan` 调用。design-voice 现在单批 dispatch 内**恒自跑**（不再判定是否"复用 autoplan 的
codex 输出"）：按 outside-voice 调用协议 site="design-voice" 直接派出，结果在 Step3 barrier collect。

`guard=` 字段从 outside-voice 锚文法移除（SKILL.md 里的锚行示例：`<!-- sdflow:outside-voice v1
site="…" host="…" runner="…" reason_code="…" findings="N" truncated="…" -->`，无 `guard=`）。`anchor_lint.py`
零代码改动——该字段本就未被解析（`anchor_lint.py:555` 明写 `MUST NOT 解析 guard=`），此次是纯文档级同步。
`declared-sites` 完整性声明段的 reuse-guard 特例说明一并改写为通用的「期望值 vs 观测值两个独立集合」表述
（不再举 design-voice 复用态为例，因为该复用态已不存在）。

## 4. lens-metric 落锚指引同步（tasks.md 2.4）

见上 1 节 Step4 部分；同时确认 `lens-metric-contract.md`（Task 1 已完成的 fold 表：`strategy: broad` +
`plan-eng: broad`）与本次 SKILL 文案完全对齐——roster 恒一行 `lens="broad"`，findings 侧用 `raw=`
承载两镜真实身份供折叠。

## 5. 广审镜定义同源注入机制（tasks.md 2.5，design DD7「同源=模板注入」）

- **真相源**：新建 `sdflow-init/assets/snippets/broad-mirrors.md`——内含 DD2 完整规格：strategy/plan-eng
  两镜的 R 项范围表（strategy=BASE-01/08/09/10/12/13/14/18/22/26/27/30 + 默认规则兜底；plan-eng=
  BASE-05/06/16/17/19/25/28）、两镜共同 prompt 契约五要素、plan-eng 防重叠语义补句。文件自带
  `sdflow:broad-mirror-def:start/end` marker（与 principles 源文件同惯例——marker 是源内容的一部分，
  注入时整行替换，不是"包在外面"）。
- **注入脚本扩展**：`hack/sync_principles.py` 新增第二个独立 marker 家族（`BROAD_MIRROR_START/END` +
  `SOURCE_BROAD_MIRRORS` + `BROAD_MIRROR_TARGETS`），复用既有 `render()`/`_blocks()`（新增 `start`/`end`
  可选参数，默认值保持向后兼容，principles 家族调用点零改动）、新增 `broad_mirror_targets()`。`main()`
  改为遍历两个 `(targets, start, end)` 组，`--check`/`--apply` 单次调用覆盖两个家族。
- **投放面**：`sdflow-spec-review/SKILL.md`（`### 广审镜` 小节）与 `sdflow-roadmap/SKILL.md`（新增
  `## 广审镜（strategy / plan-eng）定义（同源，供下方 review 节引用）` 小节，插入点在原「## review：
  按商业化信号分档」之前）——两处均已手工放好空 marker 对，`sync_principles.py --apply` 原地回填；
  各自紧邻处补一句"评审对象路径 = ……"声明（spec-review：`{change_dir}` 四件套；roadmap：三件套整体 plan，
  C7 契约）。
- **`setup.sh --check` 门禁**：无需新增调用点——`setup.sh` 既有的 `sync_principles.py --check` 调用
  （四条通则门）在脚本内部已同时覆盖两个 marker 家族；仅把告警文案从「四条通则有漂移」改为「托管块有漂移
  （四条通则 / 广审镜定义）」，避免广审镜漂移时人读到文不对题的提示。
- **注意（重要教训，记录以防未来复发）**：`render()` 用「lines[start_idx:end_idx+1] 整段替换为 `block(src)`」
  的实现——`block(src)` 必须**自带**首尾 marker 行才能在替换后继续存在于目标文件里（源文件不是"marker 之间
  的内容"，而是"含 marker 的完整块"，与既有 `skill-principles.md` 的形态一致）。首次实现 broad-mirrors.md
  时忘记这点，导致 `--apply` 把手工放置的 marker 一起吞掉、退化到 `_insert_anchor()`（首个 H1 后）兜底路径，
  在两个 SKILL 里各产生一份错位重复内容；已定位（`test_broad_mirror_render_is_idempotent` 先行发现幂等性
  破裂）并手工清理 + 修正源文件后重新 `--apply`，现幂等（连续两次 `--apply` 后 `--check` 报 22 个投放面
  全部一致，无漂移）。

### 测试（TDD：先写红测试）

`hack/tests/test_sync_principles.py` 新增 6 个测试：源文件存在性、投放面固定为两个 SKILL、两 SKILL 托管块
逐字节一致、drift→red→apply→green 定点用例（tmp_path 隔离，不碰真实工作树）、render 幂等性、setup.sh 门禁
文案覆盖两个家族。全部先红（`AttributeError: no attribute 'BROAD_MIRROR_START'`）后经脚本实现转绿。
`hack/tests/test_sync_principles.py` 全量 19 passed。

## 6. bundle 规则文档同步（tasks.md 1.4，本票范围）

- **`sdflow-init/assets/workflow/spec-review.md`**：§四 L2 表「autoplan 双声」→「strategy/plan-eng 双镜（自持）」；
  §五「现有机制的分工」表 autoplan 行替换为「广审双镜（strategy/plan-eng，本 skill 自持 fresh 子代理，按 base
  R 项划分）」行，处置措辞改为"覆盖 base 计划级+工程级 R 项"。
- **`sdflow-init/assets/workflow/workflow.md`**：阶段二流程图/步骤表/关键决策段/生成评审对称图四处，
  「Step1 autoplan(广审)→Step2 并行多镜→Step3 一份 report」及「内部 2×checkpoint（autoplan 子步/
  sdflow-spec-review 子步）」改为「Step1 单批 dispatch(自持广审双镜+领域镜+对抗镜+接地镜+design-voice)→
  Step3 一份 report」+「内部 1×checkpoint」；「autoplan 已含 eng 镜→多镜不重复跑 eng」改为「base 与 domains
  两层清单本就互斥，无需去重协商」。
- **`WORKFLOW-GUIDE.md`**（生成物）：`python3 hack/gen_workflow_guide.py --write` 重新生成——workflow.md 是
  其单一源之一，改完源后必须重跑生成器，否则 `test_workflow_split.py::test_guide_is_in_sync_with_its_sources`
  会红（先红后修，已验证）。副作用：该文件此前含 autoplan/gstack 字样（`docs/workflow-skills/gstack-*.md`
  的引用等），重新生成后随源头清零，为 Task 5 文档 sweep 减少了一处遗留面。
- **`reference/quality-layering.md`**：**核验后判定无需改动**——`grep -n "autoplan\|gstack"` 归零（改动前后
  皆零命中），全文读过一遍确认它谈的是**代码侧**质量分层（subagent-driven-development 三层审 + 注入点
  A/B），§四对称表里 spec 侧只抽象引用「sdflow-spec-review(validation+对抗+接地)」，不曾提及 autoplan 或
  Step1/Step2 内部结构，故无需修改。task2-brief 第 6 条列了此文件但未见到实际需要改的内容，如实记录该
  判定的依据而非为凑"改了三个文件"强行改动。

## 关联修复（发现即改，非本票核心但同源导致，fold 判据：紧耦合+低增量）

发现并修复了两处因本票文本改动直接触发红灯的既有测试断言（都是硬编码字面量断言，断言的正是本票要删除
的旧行为文本本身）：

1. `sdflow-init/tests/test_codex_subagent_authorization.py::test_both_skills_probe_precedes_fanout_dispatch`——
   断言 spec-review SKILL.md 含字面量「两段 dispatch」，随旧结构删除必然触发；改为断言新字面量
   「单批 dispatch（一条消息内派出本轮全部镜」，语义不变（探针小节仍须早于 fan-out 派发表格）。
2. `sdflow-ship/tests/test_serial_discipline.py::test_step2_serial_must_sentence`——原用例正是在断言
   T20 串行纪律的三句原文存在，而 T20 本身是本票要删除的对象。重写为
   `test_t20_serial_discipline_retired_single_batch_dispatch`，反向断言三句旧文已清零 + 新增
   「单批全并行 dispatch」「互不依赖」两句新文存在。

判据：两处都是「改一个文件、明确触发的既有测试红」，修复量各 3-5 行、不涉及新设计判断，符合 CLAUDE.md
fold-vs-defer 的 AND 门（同 capability ∧ 高耦合 ∧ 低增量）。

## `sdflow-roadmap/SKILL.md` 改动边界（如实声明）

本票**只**在 roadmap SKILL 里建立同源注入机制的落点（新增 `## 广审镜（strategy / plan-eng）定义（同源，
供下方 review 节引用）` 小节 + 托管块 + 一句评审对象声明），**未**改动其后紧邻的「## review：按商业化
信号分档（判定点②）」及后续小节——那部分的重写（删判定点②、恒跑双镜、失败处置改述）是 tasks.md 5.1，
分派给另一票（Blocked-by 本票）。当前 `grep -n "autoplan" sdflow-roadmap/SKILL.md` 仍有 5 处命中
（review 分档相关小节），均在未改动的旧内容里，非本票遗漏。

## 验证

```
/usr/bin/python3 -m pytest hack/tests/test_sync_principles.py -q                              # 19 passed
/usr/bin/python3 -m pytest sdflow-init/tests/test_codex_subagent_authorization.py sdflow-ship/tests/test_serial_discipline.py -q   # 12 passed
/usr/bin/python3 hack/check_async_branch_parity.py                                            # ✅ 2 处逐字节一致
/usr/bin/python3 hack/check_tier_resolution_parity.py                                         # ✅ 4 处逐字节一致
/usr/bin/python3 hack/sync_principles.py --check                                              # ✅ 22 个投放面全部一致
grep -n "autoplan\|gstack" sdflow-spec-review/SKILL.md                                        # 归零
grep -n "autoplan\|gstack" sdflow-init/assets/workflow/spec-review.md sdflow-init/assets/workflow/workflow.md  # 归零
/usr/bin/python3 -m pytest -q                                                                  # 全仓（见下）
```

全仓 `pytest -q`：2487 passed, 10 skipped，1 个**已知无关**失败——
`sdflow-init/tests/test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`。
与 task1-bundle-sync.md 记录的失败**同一条、同一错误文本**（"对照组：裸 --bg --exec 的输出未出现在
`claude logs` 里"）——本沙盒环境对 `claude` CLI `logs` 子命令行为的前置假设不成立，与本票任何改动
（SKILL.md 文本 / sync_principles.py / broad-mirrors.md / bundle 规则文档）无耦合，未做处理。

## 改动文件清单

- `sdflow-spec-review/SKILL.md`（重写）
- `sdflow-roadmap/SKILL.md`（新增广审镜定义小节 + 托管块）
- `sdflow-init/assets/snippets/broad-mirrors.md`（新建，真相源）
- `hack/sync_principles.py`（扩展第二 marker 家族）
- `hack/tests/test_sync_principles.py`（新增 6 用例）
- `sdflow-init/assets/workflow/spec-review.md`（§四/§五表同步）
- `sdflow-init/assets/workflow/workflow.md`（阶段二四处同步）
- `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`（重新生成）
- `setup.sh`（门禁告警文案泛化）
- `sdflow-init/tests/test_codex_subagent_authorization.py`（needle 同步，关联修复）
- `sdflow-ship/tests/test_serial_discipline.py`（重写为反向断言，关联修复）
