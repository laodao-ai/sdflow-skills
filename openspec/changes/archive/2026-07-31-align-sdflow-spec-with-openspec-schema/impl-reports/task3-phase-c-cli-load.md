# Task 3 implementation report — phase C CLI load

状态：`DONE_WITH_CONCERNS`

## Scope

仅实现 Task 3（SA-05、SA-17），未勾选 `tickets.md`，未创建 task checkpoint。

## Implemented

- 更新 `sdflow-spec/SKILL.md` C.2：优先消费 `dependencies` 对象列表，并在 schema 依赖图不足时回退到写死的 proposal/design/specs 阅读超集。
- 更新 C.3：
  - 在应用 instruction 前剥离成对的 `sdflow:delegation` 区块；缺失、乱序或不成对时 fail-closed，并报告 problem/cause/fix。
  - 将 glob 型 `resolvedOutputPath` 视为模式，按 capability 推导具体 specs 路径；既有输出只使用 `existingOutputPaths`。
  - 对 `skipped` artifact 跳过写入，并从依赖阅读清单移除。
- 更新 C.4 与终审说明，保留 status/validate 分离判定及 design↔specs 双向核验。
- 新增 `hack/tests/test_task3_phase_c_contract.py`，覆盖上述文档契约。

## TDD / verification

- Red：新增契约测试初次运行 `3 failed, 1 passed`，确认旧文档缺少 Task 3 语义。
- Green slice：实现后 Task 3 契约测试曾达到 `4 passed`。
- 已执行 `git diff --check`，未发现空白错误。
- 按用户要求，后续未运行全量测试，也未继续进行长时间验证。

## Concerns

- 既有 `sdflow-spec` 宽契约测试在 Windows 环境出现 Bash/CLI 预检相关失败；这些失败未归因于 Task 3，未继续追查。
- 文档入口有 18,000 Unicode 字符预算；本次压缩过程中曾触发该预算，最终状态未再运行测试确认，需后续短验证确认预算与既有契约均为绿。

## Changed files

- `sdflow-spec/SKILL.md`
- `hack/tests/test_task3_phase_c_contract.py`
- 本报告
