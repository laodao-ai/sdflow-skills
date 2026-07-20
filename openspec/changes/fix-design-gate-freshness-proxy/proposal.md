## Why

`ship_gate.py` 的设计门新鲜度判据用**路径**作为「设计内容变了」的代理信号：只要有非 `checkpoint(impl-review)` subject 的提交触及 `proposal.md` / `design.md` / `tasks.md` / `specs/`，即判拍板失鲜 → `REFUSE_START`。

该代理是**过近似**：阶段三期间对 `tasks.md` 完成度复选框的更新**零设计内容**，却与真实设计改动共用同一条路径判据，一律判失鲜 → `REFUSE_START` → 停，等人批。

**已证实的事故形态**〔spec-review-amendment，原叙事经核实修正〕：
- **本仓已发生**：`openspec/issues/buglist/2026-07-04-buglist.md` 的 B2——`tasks.md` 勾选回填触发假失鲜（已用 `checkpoint(impl-review)` subject 豁免修复，即本条代理过近似的**第一次**点补）。
- **消费项目报出**：阶段三运行中反复撞 `REFUSE_START`。
- **写入方不是 SKILL 契约**：经核实 `sdflow-implement` 与 superpowers `subagent-driven-development` **均不写** `tasks.md`（详见假设 A1′）。实际写入来自 **agent 的自由行为**与 `sdflow-done` §0.3 的批量对账。

**这恰恰提高了紧迫性而非降低**：写入方既然不受任何 SKILL 契约约束，prose 禁令结构上防不住，**机械判据是唯一防线**。撞门频度取决于 agent 行为而非固定管线，故本 change **不宣称**「每任务一撞 / 每消费仓必撞」的确定频率——但每一次撞击都在反转阶段三「过设计门后一口气跑到 merge、无人类门」的承诺（adr/0004 红线）。

而 `tasks.md` 的复选框状态对 gate 是**零信息量**：完成判据只读 `superpowers-plan.md` 的复选框与 checkpoint 标签（`ship_gate.py` `_parse_plan` / 完成判据窗口），`tasks.md` 仅作为设计内容的代理出现在 `DESIGN_WATCHED_NAMES` 中。

## What Changes

- **只豁免「纯勾选框状态翻转」这一个已证零信息量的改动形态**（P0）〔spec-review-amendment，原方案「按角色分流」经双 CEO 镜证伪，见 design ADR-1〕。提交只触及 `tasks.md`、且前后两版差异行在勾选框标记归一化后逐行等值 ⇒ 不失鲜；其余一切照判。**监视集保持固定四件套不变**，豁免面精确等于已证零信息量的集合。
- **`REFUSE_START` 失鲜 reason 补可操作指引**（P1）：报出触发失鲜的 commit 与文件，并给出两条分支处置（完成度更新 vs 真实设计变更）。诊断改善，**不改判据**。
- **`sdflow-implement` dispatch 契约补「信号权威表」**（P2）：正面陈述完成信号与设计工件的归属。仅对本仓自有 skill 有效——第三方实现 skill（superpowers / matt）不受此约束，故此项**不能作为主修法**。

**这是一次门禁放松（guardrail relaxation），不是兼容性补丁**〔spec-review-amendment，CEO 镜纠正〕。原文以「只会从失鲜转向新鲜」论证「非 BREAKING」——**方向搞反了**：对一道门而言，**扩大准入面本身就是安全语义变更**。故 P0 的豁免面 MUST 精确等于已证零信息量的集合，且每一寸扩张都须独立举证。

### 需求优先级〔BASE-23〕

| P | 需求 | 不做的后果 |
|---|---|---|
| **P0** | `tasks.md` 角色修正 | 阶段三无人类门承诺持续失效，每消费仓每次运行必撞 |
| **P1** | 失鲜 reason 指引 | 撞门者无从判断该重跑设计门还是该改行为，只能猜 |
| **P2** | dispatch 契约信号权威表 | 本仓自有管线仍可能重蹈（但 P0 已兜住后果） |

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `spec-workflow`: 设计门新鲜度判据由**纯路径代理**改为**内容判据**——提交若只触及 design 域监视集内的 `tasks.md` 且内容差异仅为勾选框状态，则不失鲜；失鲜 `REFUSE_START` 的 reason 须携带触发点与处置指引。
- `impl-orchestration`: `sdflow-implement` 的 implementer dispatch 契约须携带完成信号与设计工件的权威归属声明。

## Impact

- `sdflow-ship/scripts/ship_gate.py` — `is_stale()` design 分支 + `REFUSE_START` emit 点
- `sdflow-ship/tests/` — 失鲜判据用例（新增内容判据正反例；既有 `checkpoint(impl-review)` 豁免用例须保持绿）
- `sdflow-implement/SKILL.md` — dispatch 契约段
- 分发：经 `setup.sh` 软链到 `~/.claude/skills` / `~/.codex/skills`，消费仓跑 `/sdflow-upgrade` 后生效

## 开放问题〔BASE-15〕

- **注释 / 措辞类改动是否也应豁免失鲜**——报出方期望「补充注释不应阻断」。本提案**列为 Non-Goal**：`design.md` / `specs/` 上「澄清性注释」与「设计变更」之间**无确定性信号**（注释本身即设计沟通，implementer 读到即照做），做内容感知等于在无界语义面上开补丁循环（基准 5 警号：每轮 review 补一个新分支 = 该函数不该存在）。该面的既有正解 = `checkpoint(impl-review)` subject 声明式豁免（显式表态、git 留痕可审计）。**此判定待 grill 阶段复核，非定论。**

## 假设列表〔BASE-14〕

| # | 假设 | 依据 | 若不成立 |
|---|---|---|---|
| A1 | ~~两条实现管线均在每任务完成时更新 `tasks.md` 复选框~~ **已证伪，修订如下**〔spec-review-amendment〕 | — | — |
| A1′ | `tasks.md` 的勾选框会在阶段三被写入，写入方**不是** SKILL 契约而是 **agent 的自由行为** | 已核实：`sdflow-implement/SKILL.md:142` **只读** `tasks.md`（全文无写操作，完成信号写 `superpowers-plan.md`）；superpowers `subagent-driven-development` 通篇无 `tasks.md`；本仓唯一文档化的写入方是 `sdflow-done` §0.3 的**一次性批量对账**。外部消费项目报告的「每任务一撞」叙事**未能在本仓管线代码中找到对应**。**但同类事故本仓已发生过**：`openspec/issues/buglist/2026-07-04-buglist.md:48-56`（B2，`tasks.md` 勾选回填触发假失鲜，已 FIXED） | P0 仍成立且**更该做**——正因写入方是不受契约约束的自由行为，prose 禁令（P2）结构上防不住，机械判据是唯一防线 |
| A2 | `tasks.md` 的复选框状态不被 gate 的完成判据消费 | 已核 `ship_gate.py`：完成判据只读 `superpowers-plan.md` + checkpoint 标签 | 已验证，非待验假设 |
| A3 | `superpowers-plan.md` 存在 ⇒ 完成信号权威已转移 | `ship_gate.py` 完成判据窗口以 plan 首次提交 sha 为起点 | 已验证，非待验假设 |
