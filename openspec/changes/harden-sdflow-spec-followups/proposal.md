## Why

`add-sdflow-spec` 已归档，但其 Codex 宿主边界、FF-0 在跨仓/不可解析命令下的行为、终审追溯口径和体量门仍有可复现缺口。当前入口每次加载 20,768 个字符，也把未启用或异常路径带入默认上下文。

## Success Metrics

- [spec-review-amendment] FF-0 只对完整匹配的单条直接 literal 创建调用使用 payload `cwd` 执行三分支判定；其余包含创建字样的复合、包装、跨目录或动态形态不对错仓 deny，并留下带稳定原因码且不越权的未判定上下文。
- `sdflow-spec` 的 Codex 文案只陈述已验证的宿主语义；T132 按 A/B 入口分别认定收敛信号。
- `SKILL.md` 保留全部每次必执行的契约且不超过 18,000 Unicode 字符；按需资料可被确定条件加载。
- T232、T238、T240、T241 的已归档修正与台账状态一致，T233–T237、T242 有可验证处置。

## Non-Goals

- 不执行 T239，不在任何下游消费项目运行 `sdflow-init update`。
- 不启用阶段二外派，也不改变其 A/B 回退结论。
- 不解析 shell 来推断 `cd`、变量展开或命令的实际作用目录。

## What Changes

- [spec-review-amendment] 以正向有限的直接调用 allowlist 硬化 FF-0；未命中 allowlist 时保留 fail-open，但通过无决策的 PreToolUse context 记录稳定原因码与说明。
- 将 `sdflow-spec` 的 Codex 手动触发、终审追溯与 A/B grill 收敛语义改为可证实口径。
- 将入口重构为薄 `SKILL.md` 加按需 references，并以机械测试守住入口体量和必驻契约。
- [spec-review-amendment] 更新相关主规格、测试和 issue 台账，按逐票证据关闭已完成及本 change 完成的项目；T132 与 T239 保持 OPEN/未处理。

## Requirement Priorities

- [spec-review-amendment] **P0**：FF-0 不对未证明作用仓的命令使用 payload `cwd` 执法；未判定输出不得携带 `permissionDecision: allow`。
- [spec-review-amendment] **P0**：原 protected branch、same-change、other-feature + one-shot ack 三分支语义不得回退。
- [spec-review-amendment] **P1**：Codex、终审追溯、A/B 收敛信号按可验证事实表述；T132 只订正未来 gate 的输入契约，不在本 change 实现或关闭。
- [spec-review-amendment] **P1**：`SKILL.md` ≤ 18,000 Unicode 字符，且 resident-contract 语义锚和按需 reference 加载条件均由测试守住。
- [spec-review-amendment] **P2**：逐票台账备注与归档事实复核；不影响 P0/P1 行为交付。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `spec-authoring`: 收紧 `sdflow-spec` 的宿主边界、终审追溯、阶段一信号与入口体量契约。
- `spec-workflow`: 明确 FF-0 对跨仓/不可解析命令的非越权审计行为，以及 T132 对 A/B 入口的收敛识别前提。

## Impact

- [spec-review-amendment] `sdflow-spec/SKILL.md` 与其 references、`sdflow-init/assets/hooks/ff0-branch-guard.py`、`sdflow-init/scripts/init.py` 既有 hook 安装路径、canonical workflow、对应测试和 `openspec/issues/todolist/`。
- 下游 bundle 不在本 change 中分发；canonical 改动保持可由后续 rollout 取得。

## Compliance

N/A：无外部服务、隐私数据或监管接口改动。
