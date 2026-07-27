# Task 3 fix1 · 真实产物证据与 SA-16 身份收口

## 结果

已修复两组 Important：主规格保留 `SA-14 四入口选择规则`，将常驻契约的重复
`SA-14` 身份改为 `SA-16`；逐票 closure test 不再只读台账备注或自证，而是直接读真实
仓内 artifact 并核验语义锚。

## 证据收口

- T233：`sdflow-spec/SKILL.md` 的 Codex 诚实边界 + resident-contract 对应用例。
- T234：主规格 `SA-15` + `todolist.py scan --json` 对 T132 的 OPEN/A-B 投影；当前 closure test
  不再是唯一证据。
- T235/T237：canonical FF-0 hook 的 `command-unverifiable`/context-only 语义 + PreToolUse
  公共进程 seam 测试。
- T236：`sdflow-spec/SKILL.md` 的整个 change 目录追溯边界 + resident-contract 对应用例。
- T242：实际读取 `sdflow-spec/SKILL.md` 执行 `len(entry) <= 18_000` + resident-contract
  里同一 Python Unicode 字符门。

额外机械锁定主规格所有 `SA-*` Requirement ID 唯一，并要求常驻契约在主规格与
delta 都精确为 `SA-16`，`tasks.md` 对应实现项以及 `superpowers-plan.md` Task 2/3/4
的 R-ID 与之一致。`test_canonical_entry_sync.py` 中正确指向四入口 `SA-14` 的引用未修改。

## TDD

### RED

```text
uv run --with pytest pytest hack/tests/test_harden_sdflow_spec_followup_closure.py -q
1 failed, 14 passed

AssertionError: 主规格 SA Requirement ID 必须唯一
```

### GREEN

```text
uv run --with pytest pytest hack/tests/test_harden_sdflow_spec_followup_closure.py -q
15 passed in 0.70s
```

## 回归与一致性

```text
uv run --with pytest pytest \
  hack/tests/test_harden_sdflow_spec_followup_closure.py \
  hack/tests/test_sdflow_spec_resident_contract.py \
  sdflow-init/tests/test_ff0_branch_guard.py \
  hack/tests/test_canonical_entry_sync.py \
  sdflow-issues/tests/test_task3_frontmatter_writer.py \
  sdflow-issues/tests/test_task5_delivery_contract.py -q
138 passed in 7.42s

openspec validate --all --strict
21 passed, 0 failed

python3 sdflow-issues/scripts/issues.py --root . reindex --strict
open 193 项，已闭合 72 项
INDEX 重建前后 SHA-256 一致：
79a99633cb2ff08a20dc35157230bbde1cfba241b081f94689ee4f0312a6cca3

git diff --check
PASS
```

reindex 只用于证明索引可重生且字节一致，不作为逐票语义已实现的证明。

## 范围

本 fix 只修改权威主规格、Task 3 证据报告的身份摘要、逐票 closure test 与本报告。
未修改当前 change 的 `proposal.md` / `design.md` / delta specs / `tasks.md` /
`superpowers-plan.md`，未勾 Task 3，未创建 task3 checkpoint，未执行 Task 4 `setup.sh`，四个未跟踪
review-package.diff 保持不动。
