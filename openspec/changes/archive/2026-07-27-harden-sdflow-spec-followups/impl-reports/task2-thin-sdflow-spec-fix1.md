# Task 2 fix1 实现报告：补齐传播纪律与 reference 负向契约

## 状态

DONE

## 修复结果

- `sdflow-spec/references/delegation-protocol.md` 不再依赖 agent 定义承载四条通则；协议明确要求每一次派发的
  prompt 都把 `sdflow:principles` 从 `start` 到 `end` 的完整托管区块原文内联，并禁止转述、摘要、只给
  指针或依赖 agent 定义副本。
- `hack/tests/test_sdflow_spec_resident_contract.py` 将 reference 路由收紧为同一列表项内的「明确加载条件 +
  非空精确标签相对链接」，不再以彼此分离的任意子串为通过条件。
- 新增两个负向样本，分别证明空标签 `[](references/...)` 与条件、链接之间插入其它文字都会被拒绝；新增
  外派 prompt 原文传播的逐字在场锚。

## TDD 记录

公共 seam：安装后宿主读取的 `sdflow-spec/SKILL.md` 按需 reference 路由，以及启用外派时读取的
`references/delegation-protocol.md`。

- RED：`uv run --with pytest pytest hack/tests/test_sdflow_spec_resident_contract.py -q`
  - 结果：`1 failed, 9 passed`。
  - 失败点：旧外派协议缺少“每一次派发的 prompt 原文携带完整托管区块”的传播锚。
- GREEN：同命令在最小文档修复后为 `10 passed`。
- 负向链接用例在 RED 阶段已通过，证明新判据能拒绝空标签和条件/链接分离的退化形态；实际三个入口链接
  保持合格。

## 验证

- `uv run --with pytest pytest hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_sdflow_spec_agents.py hack/tests/test_sdflow_spec_failure_modes.py hack/tests/test_decision_memo_gate.py hack/tests/test_sync_principles.py hack/tests/test_checkpoint_slug_coverage.py hack/tests/test_canonical_entry_sync.py -q`
  - `132 passed in 10.34s`
- `python3 hack/sync_principles.py --check`
  - `22 个投放面全部与真相源一致`
- `openspec validate harden-sdflow-spec-followups --strict`
  - `Change 'harden-sdflow-spec-followups' is valid`
- `git diff --check`
  - 通过

## 范围边界

- 未修改 `proposal.md`、`design.md`、`specs/`、`tasks.md` 或 `superpowers-plan.md`。
- 未勾选 Task 2，未创建 Task 2 完成 checkpoint。
- 三个既有未跟踪 review package 原样保留，未纳入本修复。
