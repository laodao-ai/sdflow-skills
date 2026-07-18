# Task 5 Spec Compliance Re-review — fix 1

结论：**FAIL**（Critical 0 / Important 1 / Minor 0）。固定范围
`2836244..c4bb398`；固定审包 `task5-review-fix1-package.diff` 与
`git diff --binary 2836244..c4bb398` byte-identical。

首轮四个 Important 中，I1（Windows smoke 的 active delegation setup）、I3（独立 legacy
baseline）与 I4（`sdflow-issues/SKILL.md` 退役合同）均已闭合；I2 要求的 actual Windows
local-disk 结果仍不存在。Task 5 / `tasks.md` 7.4 明定该 smoke 必须执行，故本轮仍不得 PASS。

## Critical

无。

## Important

### I1 — actual Windows local-disk smoke 尚未执行

- **要求**：`tasks.md` 7.4 与 `spec-workflow` 的平台保证矩阵要求在 Windows local-disk runner
  执行 acquire/conflict/participant/replace/cleanup + setup copy smoke；非 Windows skip 不能替代。
- **当前证据**：本机定向执行结果为 `8 passed, 2 skipped`，两个 skip 正是整个
  `test_task2_windows_local_fs_smoke.py`。当前 feature branch 不存在于 `origin`，
  `gh run list --branch feat/mlh-p6-recorder-frontmatter` 返回 `[]`；实现报告也明确记录 actual
  Windows 未执行。因此没有固定 commit、Windows runner、命令与 `2 passed` 结果可供验收。
- **已落地的可执行解锁面**：`.github/workflows/windows-recorder-smoke.yml` 对 `push`、
  `pull_request`、`workflow_dispatch` 生效，没有 branch 过滤，使用 `windows-latest`，并精确执行
  `py -m pytest -q sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error`。相关 paths
  包含 workflow 自身及 recorder/setup 改动，故当前 feature branch push 会自动触发。
- **唯一最小授权动作**：push 当前 feature branch，让上述 workflow 在固定 commit 上运行；只在
  保存 run URL、commit、`windows-latest` 与无 skip 的 `2 passed` 后，才可关闭本 finding。
  本轮不以静态 workflow、Darwin skip 或模拟平台替代真实 Windows 结果。

## 首轮 findings 闭合核对

### I1（原）— active delegation contract：PASS

Windows smoke 现在在 owner 锁域内建立并于 `finally` 恢复 `_ACTIVE_RECORDER_TOKEN` / 
`_ACTIVE_RECORDER_CHAIN`，再生成 `reindex → scan` participant env；断言 chain 精确为
`("reindex", "scan")`。同一通用 delegation setup 已另有非 Windows 测试先行执行，定向套件
绿色，故不会再等到 Windows runner 才暴露 `<missing> -> scan`。

### I3（原）— 独立 baseline：PASS

`test_task5_delivery_contract.py::_reference_legacy_rows` 是 test-side Markdown table projection，
没有调用 production `parse_table_rows`、`_legacy_item_from_row` 或 dual-reader legacy helper。
它动态枚举仓内全部 7 个 bug rows 与 152 个 todo rows，按 ID/file 对当前 dual-reader 逐项比较
module、summary、pool-specific field、status、time、change、batch；没有固化 corpus 总数。
T2/T66/T67/T85/T146 五个 shadowed rows 也全部进入比较：仅四个已批准 status delta
`PROPOSED → DONE` 被允许，T2 无 delta，其余字段必须与冻结 legacy row 相等。原先“同 helper
自证并跳过 overlay”的缺口已关闭。

### I4（原）— 公开 SKILL/人读术语：PASS

`sdflow-issues/SKILL.md` 已统一为显式 `--if-exists skip`、rename 任一阶段 non-zero + provenance
支撑的原命令重跑，以及 sweep 顶层 exclusive owner + allowlist participant；原 warn-only、调用方
解析报错文案与“并发安全未焊接”措辞已删除。bug/todo scan 成功输出改为
`frontmatter/marker/legacy 关系一致`，并有退役措辞反向回归。

## Task 5 acceptance 对账

| 条款 | 结论 | 证据 |
|---|---|---|
| Acceptance 1 / 5.1–5.3 | **PASS（沿用首轮）** | legacy writer cleanup 与 mirror/read-only 边界未被 fix1 破坏。 |
| Acceptance 2 / 5.4–5.5、6.2 | **PASS** | I4 的公开合同漂移已修复；consumer/docs/ADR 主合同沿用首轮通过项。 |
| Acceptance 3 / 6.1 | **PASS** | 独立 test-side baseline 覆盖全部 159 个 legacy rows，含 5 个 overlay delta，动态枚举不固化总数。 |
| Acceptance 4 / 6.3–6.4 | **PASS（沿用首轮）** | dogfood、旧表 bytes、strict reindex 与交付记录未被 fix1 破坏。 |
| Acceptance 5 / 7.1–7.4 | **FAIL** | 本地与静态 workflow contract 均已闭合；actual Windows runner 仍无 `2 passed` 结果。 |

## Verification

- `cmp task5-review-fix1-package.diff <(git diff --binary 2836244..c4bb398)` 等价检查 → PASS。
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task5_delivery_contract.py sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error` → `8 passed, 2 skipped`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `445 passed, 2 skipped`。
- `git diff --check 2836244..c4bb398` → PASS。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid。
- `gh run list --branch feat/mlh-p6-recorder-frontmatter` → `[]`；远端无该 branch。

结论不扩张：仓内可修的三个 Important 已闭合，当前只剩 tasks 7.4 的 actual Windows
local-disk 执行证据。该外部门关闭前，本 Spec 轴维持 FAIL。
