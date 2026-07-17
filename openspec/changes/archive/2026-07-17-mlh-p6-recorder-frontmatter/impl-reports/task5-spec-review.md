# Task 5 Spec Compliance Review — cleanup、migration evidence 与 delivery reconciliation

结论：**FAIL**（Critical 0 / Important 4 / Minor 0）。固定范围
`933066d1e95bcce38231b151fc9fd3d1d99c394d..a8b1bb27c32effd46110c943acadde67005886ab`；固定审包
`task5-review-package.diff` 与 `git diff --binary 933066d..a8b1bb2` byte-identical，SHA-256 均为
`8e5b975e3afc8c9958d13b1cf3411a86f4f7c60433c9bbe2f7f5e7b47da9995c`。

Task 5 的 legacy writer cleanup、mirror/consumer 主合同、ADR/CONTEXT 主干、dogfood 当前盘面、POSIX
定向套件和 installed-path consumer smoke 已落地；但 Windows 验收合同本身尚不可运行、实际 Windows
结果缺失、全 corpus baseline 不是独立 baseline，且一个公开 SKILL 仍保留与目标态相反的恢复/锁语义，
所以不能勾 Task 5 或把 whole-change 视为已 ship。

## Critical

无。

## Important

### I1 — Windows smoke 的 owner→participant 前半段在任何平台都会先失败

- **位置**：`sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py:36-43`；
  `sdflow-buglist/scripts/buglist.py:293-307`。
- **问题**：测试直接 `recorder_lock(root, "reindex")` 后调用
  `recorder_child_env("scan", owner.token)`，却没有按生产复合入口建立
  `_ACTIVE_RECORDER_CHAIN`。该 helper 要求当前 chain 存在且允许 `reindex -> scan`；因此 Windows runner
  也会稳定得到 `RecorderLockError ... delegation denied: <missing> -> scan`，到不了 participant、
  conflict、replace、cleanup 断言。当前 POSIX 上对同一函数序列的独立 probe 已复现该精确错误，证明这
  不是“只能等 Windows 才知道”的平台分支。
- **违反条款**：Task 5 acceptance 5、`tasks.md` 7.4、`spec-workflow` 的 participant 受控委派与 Windows
  local-FS smoke 场景。当前实现报告写“期望 2 passed”没有可执行依据。
- **修复**：优先用真实 `issues reindex -> recorder scan` 复合入口验证 owner/participant；若保留函数级
  smoke，则按生产入口设置并在 `finally` 恢复 active token/chain。把 delegation 通用前半段另放到
  非 Windows 测试使其先在 POSIX 变绿，Windows-only 部分只承担 local-drive/sharing/copy 差异。

### I2 — 明定必跑的 actual Windows local-disk smoke 没有结果

- **位置**：`tasks.md:57`、`specs/spec-workflow/spec.md:177,264-265`、
  `impl-reports/task5-delivery-reconciliation.md:60-76`。
- **问题**：当前为 Darwin；定向结果 `442 passed, 2 skipped` 的两项正是 actual-Windows-only tests。
  报告正确地没有把 skip 伪报 PASS，但“Windows 本地盘必须执行 smoke”是批准的兼容目标，不是可延期
  的说明项。修好 I1 后仍须得到真实 runner 的无 skip 结果。
- **最小解锁条件**：推荐授权在当前 feature branch 增加一个 `windows-latest` GitHub Actions workflow
  并 push；本仓 Actions 已启用、`gh` 已认证且有 workflow scope。workflow 在固定 commit 执行
  `py -m pytest -q sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error`，必须 `2 passed`，
  保存 repo/commit/runner/命令/结果。代价是 private-repo Windows minutes 和一次当前 ship 契约之外的
  push 授权。备选是提供可访问的 Windows local-disk checkout 执行同一命令；UNC/network path 不能替代。

### I3 — “升级前 baseline vs 新 dual-reader”被实现成当前 helper 与自身比较

- **位置**：`sdflow-buglist/tests/test_task5_delivery_contract.py:62-88`；实现报告 `:23-29`。
- **问题**：`document["effective_items"]` 与 expected 都来自当前同一个 module，expected 又直接调用当前
  `_legacy_item_from_row()`；dual-reader 的 legacy projection 本身正是同一 helper 的结果。parser/helper
  若同步回归，两侧会一起变化而测试仍绿。测试还对 `canonical in owned` 直接 `continue`，把本次 overlay
  dogfood 的 T85/T66/T67/T146/T2 全部排除。
- **量化证据**：当前 corpus 有 159 个 legacy rows（bug 7 + todo 152），其中 5 个 legacy rows 被
  overlay shadow；测试只比较其余 154 项，并且 154 项仍是同实现自证。它没有保存或调用独立的
  pre-upgrade legacy-only baseline。
- **违反条款**：Task 5 acceptance 3、`tasks.md` 6.1、design NFR“legacy-only parser baseline 对新
  dual-reader 的 corpus snapshot comparison”。“不硬编码动态总数”不等于可以省略独立参考面。
- **修复**：从 change 的 pre-reader 锚生成独立、可审计的 legacy-only baseline，或用独立 reference
  parser 对同一冻结 pre-dogfood corpus 取值；再由当前 dual-reader 对逐 item 全关键字段比较。ID/file
  动态枚举、总数不长期硬编码；对五个 dogfood item 分开断言预期可变字段与必须保持的 immutable
  module/summary/type/time/change/batch，不能整项跳过。

### I4 — 用户契约仍写着已被目标态废止的 warn-only 与“无并发锁”语义

- **位置**：`sdflow-issues/SKILL.md:160-162,190-197`；成功输出术语见
  `sdflow-buglist/scripts/buglist.py:1513-1520` 与 todolist 对应 `_render_scan()`。
- **问题**：同一 SKILL 一处要求调用方自行把 batch 已存在错误解释为幂等，另一处又正确说明 sweep 固定
  `--if-exists skip`；随后又称 rename reindex failure 是 warn-only，并称 sweep“并发安全未焊接、调用方
  MUST 串行”。这些与本 change 已批准的 `batch rename` 任一阶段 non-zero + 原命令重跑、顶层 exclusive
  owner + participant lock 域直接冲突。bug/todo 成功输出还对 canonical frontmatter-only 文档显示
  `表↔块一致`，继续把冻结 legacy 表描述成现行写侧真相。
- **违反条款**：Task 5 acceptance 2、`tasks.md` 5.4，以及 SW-RI-2/SW-RI-3 的 lock/retry 外部合同。
  关键词存在测试不能证明文档没有反向旧合同。
- **修复**：删除旧 add/warn-only/D6 段，统一为当前 `--if-exists skip`、owner/participant lock、rename
  fail-closed + provenance-backed same-command retry；把 scan 成功术语改为 frontmatter/marker/legacy
  relation 的准确描述。增加禁止旧措辞的文档回归，而不只是断言新关键词出现。

## Minor

无。

## Task 5 acceptance / tasks 5.x–7.x 对账

| 条款 | 结论 | 证据 |
|---|---|---|
| Acceptance 1 / 5.1–5.3：删 legacy writer、保留 read/promotion、更新 mirror | **PASS** | 三脚本无 `_reject_cell_unsafe`；`issues.py` 独立 `_reject_batch_line_unsafe` 只守 batches；dated writer call-graph 不走 text/table mutation；mirror `7 passed`。 |
| Acceptance 2 / 5.4–5.5、6.2：consumer/docs/ADR | **PARTIAL** | strict consumer、主 README/ADR/CONTEXT 与多数 SKILL 术语已更新；`sdflow-issues/SKILL.md` 仍公开相反的 warn-only/无锁合同（I4）。 |
| Acceptance 3 / 6.1：全 corpus baseline | **FAIL** | 当前测试是同 helper 自证并跳过五个 overlay legacy item，没有独立 pre-upgrade baseline（I3）。 |
| Acceptance 4 / 6.3–6.4：真实 dogfood 与记录 | **PASS** | T85/T66/T67/T146/T2 effective status 均 DONE、scan problems=0；legacy table region 与 `933066d` bytes 相等；`reindex --strict` 收敛为 open 105 / closed 55，roadmap/task-log/batches 有关联记录。 |
| Acceptance 5 / 7.1–7.4：验证与跨平台 smoke | **FAIL** | recorder `-W error`、mirror、普通 full pytest、OpenSpec、diff、consumer smoke 均有证据；Windows contract 自身先失败且 actual runner 未执行（I1/I2）。 |

`full pytest -W error` 本轮独立复跑为 `38 failed, 1578 passed, 2 skipped`，与报告一致，失败来自既知
`sdflow-maintain`/`sdflow-architecture` ResourceWarning 基线。`tasks.md` 7.3 的字面要求是“运行并保存
结果”，而 7.1 才明确要求 recorder 定向套件全绿无 warning；因此本 Spec 轴不把这 38 项另立 Task 5
finding，但最终 verify 不得把该命令描述成绿色 warnings-as-errors gate。

## Verification

- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error`
  → `442 passed, 2 skipped`。
- Task 5 + mirror + Windows contract（当前非 Windows）→ `12 passed, 2 skipped`。
- `uv run --with pytest pytest -q -W error` → `38 failed, 1578 passed, 2 skipped`。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid。
- `git diff --check 933066d..a8b1bb2`、`python3 hack/sync_principles.py --check` → PASS。
- 独立 delegation probe → `RecorderLockError ... delegation denied: <missing> -> scan`。
- `scan --json` dogfood probe → T85/T66/T67/T146/T2 均 DONE、0 problems；strict reindex exit 0。

存在四个 Important，Task 5 需修复后重审；Windows 实机授权只是 I2 的最小外部门，不能替代 I1、I3、I4
的仓内修复。
