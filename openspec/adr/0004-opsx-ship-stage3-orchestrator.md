# opsx-ship：阶段三过设计门后连续跑到 merge 的编排 orchestrator

> 落地名 sdflow-ship，见 adr/0007 命名规范。

设计把三阶段"连续化"做到了**设计层**（去 `/clear` G1、阶段三去人类门 P3e），却没做到**编排层**——人仍需照 `workflow.md` 逐步 copy prompt 手动调 5.5→9。新增 skill `opsx-ship`（暂定名，备选 opsx-deliver / opsx-run）补编排层：**一次调用**把阶段三 `embedded-test-sop`(条件) → `writing-plans`(→ subagent-dev) → `impl-review` → `opsx-done` → merge 串起来驱动。

**窄 scope——明确不越两个人类点：**

- **不跨 grill（step 3）**：多轮人类对抗对话，本性不可折叠。
- **不跨设计门（step 5）**：全流程唯一 HARD-GATE；orchestrator 只从**过门之后**起跑。人手动跑 ff / grill / spec-review / 过门，过门后调 `opsx-ship` 驱动到 merge。

**尊重子步门禁（非蒙头跑）**：`opsx-done` 的 verify FAIL（核心缺口）/ `impl-review` 的真 blocker → **停并上抛**，不继续；只有"能修自动修 / 拿不准 defer"才往下走。否则就成新的假✅ 温床（违背 CONTEXT.md 术语『verify 终门』/『假✅』的元原则：任何一层评审覆盖不得无声蒸发）。

**meta-orchestrator——chain 现有 skill、不取代**：`spec-review` 不在其内（属阶段二、在设计门前）；`impl-review` / `opsx-done` 被它调。`workflow.md` 的阶段三 step 表即其内部序列；workflow.md 仍是人读的 reference。与决策 P3a「阶段三串接连续自动跑」逐字吻合。

## Considered Options

- **窄 = 仅阶段三（5.5→9）（选中）**：安全（不碰 grill / 设计门两个人类点）、收益最大（编排层空白正在此段）、风险最小。正是"过设计门后自动跑到 merge"的可执行化。
- **宽 = 全管线可续跑（内置 grill / 设计门 2 个暂停点）**：更省手，但门口易出错（设计门是拼死保住的唯一人类门，自动跨门风险高）+ grill 暂停/续跑交互绕。弃——先窄后可扩。
- **不做 orchestrator（维持手动逐步）**：编排层无自动化，违背设计"连续"初衷，用户仍每步 copy prompt。

## Consequences

- 新 skill `opsx-ship`：阶段三步骤成其内部序列；须实现——过门前置校验（确认 `spec-review-report.md` 已批准、已过设计门才起跑）、子步门禁传播（verify FAIL / impl-review blocker → 停）、失败上抛。
- 与 `opsx-done` 的关系：`opsx-ship` ⊃ `opsx-done`（chain 它）；命名区分——ship = 阶段三驱动、done = 收尾闭环。
- `embedded-test-sop` 的条件触发判定（TG-02 ∧ 高风险/TG-18）由 opsx-ship 顺带判、命中才跑。
- 与"编排层连续 vs 设计层连续"这对新术语配套（见 CONTEXT.md）。
- **落地 change**：`opsx-ship-orchestrator`（若最终改名，同步 change 名 + 本 ADR 标题）。
