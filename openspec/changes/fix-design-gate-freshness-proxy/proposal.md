## Why

`ship_gate.py` 的设计门新鲜度判据用**路径**作为「设计内容变了」的代理信号：只要有非 `checkpoint(impl-review)` subject 的提交触及 `proposal.md` / `design.md` / `tasks.md` / `specs/`，即判拍板失鲜 → `REFUSE_START`。

该代理是**过近似**。实现管线在每完成一个任务时更新 `tasks.md` 的完成度复选框——superpowers（`subagent-driven-development`）与 matt（`sdflow-implement` tickets）**两条管线皆然**。于是：

```
task1 done → 更新 tasks.md → gate → REFUSE_START → 停，等人批
task2 done → 更新 tasks.md → gate → REFUSE_START → 停，等人批
...
```

**阶段三「过设计门后一口气跑到 merge、无人类门」的承诺（adr/0004 红线）被反转成每任务一道人类门。** 该缺陷由消费项目在使用 workflow 时报出，非本仓自测发现——消费仓每次阶段三运行都撞。

而 `tasks.md` 的复选框状态对 gate 是**零信息量**：完成判据只读 `superpowers-plan.md` 的复选框与 checkpoint 标签（`ship_gate.py` `_parse_plan` / 完成判据窗口），`tasks.md` 仅作为设计内容的代理出现在 `DESIGN_WATCHED_NAMES` 中。

## What Changes

- **`tasks.md` 在 `superpowers-plan.md` 存在后退出 design 域监视集**（P0）。判据 = plan 文件存在性，纯存在性检查，零内容读取、零解析。plan 落盘即意味着完成信号权威已转移，`tasks.md` 此后不再承载任何被消费的权威。`proposal.md` / `design.md` / `specs/` 监视口径**逐字不变**。
- **`REFUSE_START` 失鲜 reason 补可操作指引**（P1）：报出触发失鲜的 commit 与文件，并给出两条分支处置（完成度更新 vs 真实设计变更）。诊断改善，**不改判据**。
- **`sdflow-implement` dispatch 契约补「信号权威表」**（P2）：正面陈述完成信号与设计工件的归属。仅对本仓自有 skill 有效——第三方实现 skill（superpowers / matt）不受此约束，故此项**不能作为主修法**。

**非 BREAKING**：判据只会从「失鲜」转向「新鲜」，不会让原本新鲜的判成失鲜；已归档 change 不重放 gate。

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

- `spec-workflow`: 设计门新鲜度判据新增角色分流——`superpowers-plan.md` 存在时 `tasks.md` 退出 design 域监视集；失鲜 `REFUSE_START` 的 reason 须携带触发点与处置指引。
- `impl-orchestration`: `sdflow-implement` 的 implementer dispatch 契约须携带完成信号与设计工件的权威归属声明。

## Impact

- `sdflow-ship/scripts/ship_gate.py` — `is_stale()` design 分支 + `REFUSE_START` emit 点
- `sdflow-ship/tests/` — 失鲜判据用例（新增角色分流正反例；既有 `checkpoint(impl-review)` 豁免用例须保持绿）
- `sdflow-implement/SKILL.md` — dispatch 契约段
- 分发：经 `setup.sh` 软链到 `~/.claude/skills` / `~/.codex/skills`，消费仓跑 `/sdflow-upgrade` 后生效

## 开放问题〔BASE-15〕

- **注释 / 措辞类改动是否也应豁免失鲜**——报出方期望「补充注释不应阻断」。本提案**列为 Non-Goal**：`design.md` / `specs/` 上「澄清性注释」与「设计变更」之间**无确定性信号**（注释本身即设计沟通，implementer 读到即照做），做内容感知等于在无界语义面上开补丁循环（基准 5 警号：每轮 review 补一个新分支 = 该函数不该存在）。该面的既有正解 = `checkpoint(impl-review)` subject 声明式豁免（显式表态、git 留痕可审计）。**此判定待 grill 阶段复核，非定论。**

## 假设列表〔BASE-14〕

| # | 假设 | 依据 | 若不成立 |
|---|---|---|---|
| A1 | superpowers 与 matt 两条实现管线均在每任务完成时更新 `tasks.md` 复选框 | 消费项目实地报告 | 若仅其一，P0 仍成立（判据不依赖谁在改），但发生频度评估需下调 |
| A2 | `tasks.md` 的复选框状态不被 gate 的完成判据消费 | 已核 `ship_gate.py`：完成判据只读 `superpowers-plan.md` + checkpoint 标签 | 已验证，非待验假设 |
| A3 | `superpowers-plan.md` 存在 ⇒ 完成信号权威已转移 | `ship_gate.py` 完成判据窗口以 plan 首次提交 sha 为起点 | 已验证，非待验假设 |
