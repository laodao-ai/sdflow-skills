# Task 3 · 主规格与问题台账逐票闭合

## 结果

已把本 change 的 FF-0、常驻入口、终审追溯和 T132 A/B 输入契约同步到权威主规格，并按 closure matrix 对
T132、T232–T242 逐 ID 写入可回查状态与证据。T239 未执行下游 rollout，保持非终态。

## 逐票终态与证据

| ID | 终态 | 证据 |
|---|---|---|
| T232 | DONE | `archive/2026-07-26-add-sdflow-spec/specs/spec-authoring/spec.md` 已把 `validate --strict` 的覆盖面订正为 delta spec |
| T238 | DONE | 同一归档 spec 已按 harness 实测写明 `model` 枚举别名契约 |
| T240 | DONE | `archive/2026-07-26-add-sdflow-spec/design.md` 已写明无 uninstall 分支的真实回滚顺序 |
| T241 | DONE | `archive/2026-07-26-add-sdflow-spec/tasks.md` 已补阶段三回退分支 |
| T233 | DONE | `793f583` 与 `hack/tests/test_sdflow_spec_resident_contract.py`：Codex 只陈述用户显式触发被接受，不把接口缺席写成拒绝 |
| T234 | DONE | 主规格 SA-15、T132 台账描述与 `test_harden_sdflow_spec_followup_closure.py`：A/B 输入分治且不用漂移行号 |
| T235 | DONE | `b573c37` 与 `sdflow-init/tests/test_ff0_branch_guard.py`：非直接 grammar 不对 payload cwd 的仓执法 |
| T236 | DONE | `793f583` 与 resident-contract 测试：终审追溯边界为整个 change 目录，memo 可作为唯一载体 |
| T237 | DONE | `b573c37` 与 FF-0 测试：未判定路径输出 `additionalContext`，不设置权限决定 |
| T242 | DONE | `793f583` 与 resident-contract 测试：入口以 Python `len()` 守 18,000 Unicode 字符门 |
| T132 | OPEN | 只订正未来 gate 输入：A = 有效 memo + `checkpoint(sdflow-spec-grill)`；B = `checkpoint(grill)` 或明确认可的锚；未实现 gate |
| T239 | PROPOSED | 未运行任何下游 `sdflow-init update`，保留独立 rollout 待办 |

状态通过 `sdflow-issues/scripts/todolist.py set-status` 写入，随后由
`sdflow-issues/scripts/issues.py reindex` 重建 `openspec/issues/INDEX.md`。T132 原为 legacy row，先经 CLI
same-file promotion，再仅订正其 summary/marker prose；保留 `OPEN`，未产生完成历史。

## 主规格同步

- `openspec/specs/spec-authoring/spec.md`
  - SA-01：Codex 宿主执行面诚实边界；
  - SA-06：整个 change 目录的终审追溯边界；
  - SA-16：18,000 Unicode 字符常驻契约与按需 reference；
  - SA-15：T132 分支 A/B 的未来输入契约且保持 OPEN。
- `openspec/specs/spec-workflow/spec.md`
  - 仅完整匹配单条直接 literal grammar 才使用 payload `cwd`；
  - 其余单调用统一 `command-unverifiable`；
  - 不设置 `permissionDecision`；保留 stacking deny 与直接调用三分支/ack。

## TDD 与验证

### RED

```text
uv run --with pytest pytest hack/tests/test_harden_sdflow_spec_followup_closure.py -q
13 failed, 1 passed
```

失败逐项指向：T232–T238/T240–T242 仍为 PROPOSED、T132 仍是漂移行号旧描述、主规格尚未同步。

### GREEN

```text
uv run --with pytest pytest hack/tests/test_harden_sdflow_spec_followup_closure.py -q
14 passed in 0.65s
```

### 受影响回归与规格校验

```text
openspec validate --all --strict
21 passed, 0 failed

uv run --with pytest pytest \
  hack/tests/test_harden_sdflow_spec_followup_closure.py \
  hack/tests/test_sdflow_spec_resident_contract.py \
  sdflow-init/tests/test_ff0_branch_guard.py \
  hack/tests/test_canonical_entry_sync.py \
  sdflow-issues/tests/test_task3_frontmatter_writer.py \
  sdflow-issues/tests/test_task5_delivery_contract.py -q
137 passed in 7.82s

git diff --check
PASS
```

未运行全量 pytest、`bash setup.sh` 或下游 rollout；这些属于 Task 4 / T239，不在本票范围。

## 范围核对

本票只修改主规格、issue ledger/INDEX、逐票 focused test、legacy overlay 投影测试与本报告。未修改当前
change 的 `proposal.md`、`design.md`、delta specs、`tasks.md`、`superpowers-plan.md`；未触碰三个未跟踪
review package；未勾 Task 3，未创建 task3 checkpoint。
