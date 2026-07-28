# Task 2：T10 拆成 `T10-choice` 与 `review-loop-breaker` 两条具名规则

状态：`DONE`

## 范围核对（tasks.md §2.1–2.11、§3.1–3.4、§6.3–6.4、§7.1）

唯一口径 = `design.md`「T10 scope-check」表。全仓 `grep -rn "T10"`（不带 `--include`）建立完整落点视图，
逐条与该表对齐后分三类处理。

### Group A（15 处规范性落点，改名 `T10-choice` + ②步统一升 strong）

| # | 落点 | 处理 |
|---|---|---|
| 1 | `sdflow-init/assets/workflow/workflow.md:110`（canonical 定义） | 改名 + ②补 `strong` + 括注"T10"历史别名说明 |
| 2 | `sdflow-ship/SKILL.md:164` | 改名 + ②补 `strong`；台账行 `T10复核:` → `T10-choice复核:` |
| 3–5 | `sdflow-code-review/SKILL.md:7,170,289`（frontmatter description / 概述 / ②步展开） | 改名 + ②补 `strong` |
| 6 | `sdflow-code-review/SKILL.md:532`（台账行格式） | `T10复核:` → `T10-choice复核:` |
| 7 | `openspec/specs/spec-workflow/spec.md:83` | 改名 + ②补 `strong` + **补回丢失的「按三镜+主次」**（M1 缺口） |
| 8 | `openspec/specs/spec-workflow/spec.md:638` | 改名 + ②补 `strong`（原已含「按三镜+主次」） |
| 9 | `openspec/specs/impl-orchestration/spec.md:27`（出票模式·粒度争议） | 改名 + 补 `strong` |
| 10 | `sdflow-implement/SKILL.md:249`（出票模式起手检查） | 改名 + 补 `strong` |
| 11 | `sdflow-implement/SKILL.md:317`（无 quiz-the-user 说明） | 改名 + 补 `strong` |
| 12 | `sdflow-implement/SKILL.md:328`（一致性自扫②步） | 改名 + 补 `strong` |
| 13 | `sdflow-implement/SKILL.md:608`（附录 B 出处说明） | 改名 + 补 `strong` |
| 14 | `sdflow-init/assets/workflow/ff-generation-constraints.md:68` | 改名 + 补 `strong` |
| 15 | `docs/workflow-overview.md:257`（人读并列定义 + mermaid 图） | 标题改名 + 图②节点补 `strong` |

【别名保留·不编辑】`openspec/specs/spec-workflow/spec.md:29`——确认未改动（属无关 Requirement 的
Scenario 指针，"T10" 仍可解析为历史别名，design 已裁决不划算）。

**一致性核对**：Group A 15 处中，原文已含「按三镜+主次」的 7 处保留原样；design 明确标出的唯一缺口
（:83）已补回；其余为无 ①②③ 全展开的简短引用（terse mention），design 未要求补该短语，仅要求
改名+补 strong——逐条核对与 design 表指令一致，不做超出范围的额外改写。

### Group B（`review-loop-breaker`，1 处，独立成文）

`sdflow-implement/SKILL.md` 熔断段（原 :541-544）整段重写，不再以裸 `T10` 引用：

- **触发**：同一发现连续 2 轮 re-review 仍未消解。
- **身份键**：从"同 file:line + 同问题"改为"同文件 + 规范化问题指纹"，明写"行号只作定位不作身份"。
- **三级处置改为互斥终态**：①有客观判据→自动选记理由后关闭（附"预期极少触发"原因说明，保留不删，
  对应 tasks.md 3.4）；②无客观判据→派 **strong 档**对抗镜复核，复核不成立→关闭，成立且可修→
  strong 档 fixer 修复并**仅复验一次**（通过关闭/不通过转③）；③复核不过/无从复核/成立但不可修→
  defer 进 buglist 并停。MUST NOT 停在"已确认成立"而无后续动作。
- 段内保留一处对照性提及 `T10-choice`（说明"本规则 MUST NOT 引用其它能力的 T10 标签"及两者触发
  条件不同）——与已定稿的 delta（`impl-orchestration/spec.md:65`）措辞同构，非误留。

### 【不动】与【本 change 自产】

- `sdflow-implement/SKILL.md:419`（NEEDS_CONTEXT 表尾）与 `openspec/specs/impl-orchestration/spec.md:60`
  ——"T10"字样原样保留，逐字核对未被误改。
- `openspec/CONTEXT.md:299`：术语条目改写为登记两条具名规则 + "T10"别名关系（`T10-choice`/
  `review-loop-breaker` 各自的触发条件、落点与 canonical 引用一并写入）。
- `openspec/adr/0031`：**正文一字未改**，仅在文末追加一行指向两条具名规则最终定名与 design 的
  scope-check 表。

## 全仓复核（§7.1）

```
$ grep -rn "T10" . | grep -v "openspec/changes/harden-implement-review-loop/" \
    | grep -v "openspec/changes/archive/" | grep -v "openspec/issues/" \
    | grep -v "openspec/ROADMAP.md" | grep -vE "T10:[0-9]|T10[0-9]"
```

核对结果：

- Group A 15 处：措辞一致，均含 `T10-choice` + `strong` 标注（详见上表）。
- Group B 落点：不再以裸 `T10` 引用规则本身（仅保留一处对照性提及 `T10-choice`，与已定稿 delta
  同构，非"T10"裸标签）。
- 【不动】2 处（`sdflow-implement/SKILL.md` NEEDS_CONTEXT 尾部 + `impl-orchestration/spec.md:60`）：
  "T10" 字样原样健在，未被误删。
- 【别名保留】1 处（`spec-workflow/spec.md:29`）：未改动。
- 【Task 1 提前正确使用】1 处（`sdflow-implement/SKILL.md:170`，"出票模式同样消费档位：全 ticket
  语义一致性自扫遇到粒度争议时的 `T10-choice` 仲裁步要派 **strong** 对抗镜"）——**〔fix1 补记〕**
  本次首轮 §7.1 分类漏纳此行：该行由 Task 1 commit `9f6bcf22`（"新增第零步宿主/档位解析"）写入，
  写入时点在本票 `T10-choice` 定名之前，但措辞已提前正确使用该名字（非本票改名对象——不在 design
  scope-check 表内、当时也未改名，故不落 Group A），审计时应显式归类为"已是目标态、无需改动"，
  原报告未提及即遗漏，非误改。
- 【本 change 自身审计/报告文本】**〔fix2 补记 · 常设分类规则〕**：本 change 的 plan、impl-report、
  `planning-decisions.md` 等自身产物在陈述规则时**必然**引用 `T10-choice` 字面（如
  `sdflow-implement/SKILL.md:251` 由 fix1 新增的行格式引述）。这类命中是**合规新增、非改名对象**，
  一律归本类，**不逐行枚举**。
  🔴 **为何改为常设规则而非补记具体行**〔`review-loop-breaker` 判定 · `T10-choice` ①档，客观判据〕：
  §7.1 首版给出「总命中 = 53 行、分类穷尽」这类**绝对计数**断言，而本审计文本自身含 `T10-choice`
  字面 ⇒ **任何一次对本报告的编辑都会使该计数 +1、令断言当场失效**（fix1 修完 finding 1 即把 53
  变成 54，两轴 re-review 同时判其不实）。这是自指循环，追数永不收敛。∴ 口径改为：
  **① 计数一律标注快照 commit；② 本类命中按规则归属、不进逐行清单。**
- **计数快照口径**：上述五类 + 本类的分类，针对 commit `aafbdb9` 的工作树状态；此后对本报告或
  `planning-decisions.md` 的任何编辑若新增 `T10-choice` 字面，按上一条常设规则自动归类，
  **不构成分类缺口，也不需要重算总数**。
- 其余命中（`docs/` 下除 `workflow-overview.md` 外的分析/历史类文档、`sdflow-done/scripts/
  roadmap_writeback_draft.py:88` 的历史决策注记、`sdflow-issues/tests/test_batch_lint.py`、
  `openspec/specs/determinism-guards/spec.md:88` 的无关示例 ID）——均不在 design scope-check 表内、
  且属分析类/历史记录类/无关示例，按表口径不属扫改范围，未改动。

## 落点数量与文件改动统计

```
$ git diff --stat
 docs/workflow-overview.md                                          |  4 +--
 openspec/CONTEXT.md                                                |  2 +-
 openspec/adr/0031-t10-label-split-by-decision-semantics.md         |  2 ++
 openspec/specs/impl-orchestration/spec.md                          |  2 +-
 openspec/specs/spec-workflow/spec.md                                |  4 +--
 sdflow-code-review/SKILL.md                                        |  8 +++---
 sdflow-implement/SKILL.md                                          | 30 +++++++++++-------
 sdflow-init/assets/workflow/ff-generation-constraints.md           |  2 +-
 sdflow-init/assets/workflow/workflow.md                            |  2 +-
 sdflow-ship/SKILL.md                                               |  2 +-
 10 files changed, 36 insertions(+), 22 deletions(-)
```

10 个改动文件，与本票范围（15 处 Group A 落点 + 1 处 Group B + 2 处 CONTEXT/adr 自产，散布在
10 个物理文件里）吻合；`openspec/changes/harden-implement-review-loop/{proposal,design,tasks,specs}`
四件套 **零改动**（未触发 ship_gate design 域失鲜）。

## 测试执行（本票 Blocked-by: 1，链上模块 = Task 1 触及的四个 skill + `hack/tests/`）

```
$ /usr/bin/python3 -m pytest hack/tests/test_tier_resolution_parity.py sdflow-implement/tests \
    sdflow-ship/tests sdflow-init/tests -q
1159 passed, 4 skipped in 214.80s

$ /usr/bin/python3 -m pytest hack/tests/test_harden_sdflow_spec_followup_closure.py -q
16 passed in 0.73s
```

（该文件是仓内唯一断言 `spec-workflow/spec.md` / `impl-orchestration/spec.md` 内容的测试，核对
其未因本票对这两份 spec 的措辞改动而破坏。）

**全仓回归**（超出本票强制范围，但本票改动含 `openspec/specs/**` 与文档，做一次全量确认无跨模块
误伤）：

```
$ /usr/bin/python3 -m pytest -q
2893 passed, 11 skipped, 3 xfailed in 278.74s
```

计数与 Task 1 报告记录的基线（同为 2893 passed / 11 skipped / 3 xfailed）完全一致，无新增失败、
无新增 skip，确认本票零回归。

## 完成信号

本次提交不带 `task2-` 完成标签、不勾 plan 复选框（后置双写时序，由双轴审通过后补打）。

## 未做/裁剪的部分

无。tasks.md §2 全 11 项、§3 全 4 项、§6.3–6.4、§7.1 均已完成并有对应证据。
