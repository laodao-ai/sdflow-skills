## Purpose

issues 台账读取路径诚实化：legacy 表词表校验（显红不罢工）+ reindex 写盘总项数守卫 + batch triage 状态解耦。

## ADDED Requirements

### Requirement: 读取路径词表校验（显红不罢工）[spec-review-amendment]

读取 legacy 表时，status / specific_field（type 或 priority）的值 SHALL 在 core 层（`_build_effective_snapshot`）和 consumer 边界（`validate_scan_envelope`）两层同步经 `POOL_SPEC` 注入的词表校验。超出词表的值 SHALL 记入 `problems` 列表（显红），**MUST NOT** 中止扫描或 raise。脏值项 SHALL 仍收入 items 列表（不丢弃、不过滤），确保盘点总数准确。

理由：现状 `_legacy_item_from_row:819` 把 `cells[4]` 原样透传为 status，无校验 → 脏状态项静默计入 open，盘点数字造假。且 `validate_scan_envelope`（`issues.py:437-440`）对 status/specific_field 枚举漂移直接 raise ValueError → reindex 整体中止。

#### Scenario: 脏 status 被报告但不中止扫描（core 层）

- **WHEN** legacy 表某行 status 列的值不在 `POOL_SPEC.status_values` 中
- **THEN** `_build_effective_snapshot` 返回的 `problems` 列表包含一条标注该项 ID 和脏值的消息
- **AND** 该项仍出现在返回的 items 列表中（不被丢弃）
- **AND** `_build_effective_snapshot` 正常返回（不 raise）

#### Scenario: 脏 status 被报告但不中止扫描（consumer 边界）

- **WHEN** `scan --json` 输出中某项 status 不在 `POOL_SPEC.status_values` 中
- **THEN** `validate_scan_envelope` 把该项收入返回的 items 列表 + 记入 problems
- **AND** 不 raise ValueError

#### Scenario: 脏 specific_field 被报告但不中止扫描

- **WHEN** legacy 表某行 type/priority 列的值不在 `POOL_SPEC.specific_values` 中
- **THEN** `problems` 列表包含一条标注该项 ID 和脏值的消息
- **AND** 该项仍出现在返回的 items 列表中

### Requirement: reindex 总项数只增不减守卫 [spec-review-amendment]

`_reindex_core` 写盘前 SHALL 用两段式解析读取旧 INDEX.md 的总项数（open 表格行数 + "共 N 项已闭合"聚合行的 N），若新扫描总项数 < 旧总项数，SHALL fail-closed 拒绝覆盖（非零退出）。首次建 INDEX（旧总项数 = 0 或旧文件不存在）时跳过校验。旧 INDEX 存在但不可解析时视为 0（跳过校验 + 记 problem 警告）。

理由：正常操作（add / set-status / batch）只增项或改状态、不删项，总项数只增不减是精确不变量。B12 实测旧版 issues.py 扫不到 overlay 新池 → 57 项降到 51 项，6 项静默消失且 exit 0。INDEX.md 的 closed 项只有聚合摘要行（不逐行渲染），单纯数表格行只能得到 open 项数，量纲不一致会导致守卫结构性偏松。

#### Scenario: 版本偏斜下 reindex 拒绝覆盖

- **WHEN** `_reindex_core` 新扫描的总项数 < 旧 INDEX.md 的总项数（两段式解析：open 行数 + closed 聚合数）
- **THEN** raise `ReindexStageError` 且不覆盖 INDEX.md
- **AND** 退出码非零

#### Scenario: 首次建 INDEX 不触发守卫

- **WHEN** 旧 INDEX.md 不存在或总项数 = 0（含不可解析降级）
- **THEN** 正常写入，不触发骤降检测

### Requirement: sweep 路径 triage 状态解耦 [spec-review-amendment]

`_bug_triage` 和 `_todo_triage` SHALL 支持 `promote` 参数（默认 `True`）。`promote=False` 时 MUST NOT 修改 item 的 status（只赋批次）。`triage` CLI 子命令 SHALL 新增 `--batch-only` flag 映射到 `promote=False`。`cmd_sweep` SHALL 以 `triage --batch-only` 调用 triage（归批次不改状态）。直接调用 `triage`（无 `--batch-only`）保持原行为（赋批次+推进状态）。

理由：triage 的"赋批次+推进状态"是 SKILL.md 正式契约（:494-496），直接调 triage 的行为不应改变。`cmd_batch_add`（`issues.py:968-1007`）本来就不碰 status（纯注册表操作）。真正的"越权"只在 sweep 编排层：sweep 通过子进程调用 triage（`issues.py:1126-1132`），间接触发状态推进。

#### Scenario: sweep 路径 batch add 不改 status

- **WHEN** `cmd_sweep` 对一个 status=OPEN 的项执行 `triage --batch-only`
- **THEN** 该项 batch 被更新
- **AND** 该项 status 仍为 OPEN（未被改为 PROPOSED）

#### Scenario: 直接 triage 保持原行为

- **WHEN** 直接调用 `triage --id X --批次 Y`（无 `--batch-only`）对一个 status=OPEN 的项
- **THEN** 该项 batch 被更新
- **AND** 该项 status 被推进为 PROPOSED（原行为不变）
