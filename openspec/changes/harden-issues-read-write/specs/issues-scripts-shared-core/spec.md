## Purpose

issues 台账读取路径诚实化：legacy 表词表校验（显红不罢工）+ reindex 写盘总项数守卫 + batch triage 状态解耦。

## ADDED Requirements

### Requirement: 读取路径词表校验（显红不罢工）

`_scan_pool` 读取 legacy 表时，status / specific_field（type 或 priority）的值 SHALL 经 `POOL_SPEC` 注入的词表校验。超出词表的值 SHALL 记入 `problems` 列表（显红），**MUST NOT** `_die` 中止扫描。脏值项 SHALL 仍收入 items 列表（不丢弃、不过滤），确保盘点总数准确。

理由：现状 `_legacy_item_from_row:819` 把 `cells[4]` 原样透传为 status，无校验 → 脏状态项静默计入 open，盘点数字造假。且 reindex 路径遇非法值直接 `_die`（`__init__.py:1963`），一条脏行炸掉整个 INDEX。

#### Scenario: 脏 status 被报告但不中止扫描

- **WHEN** legacy 表某行 status 列的值不在 `POOL_SPEC.status_values` 中
- **THEN** `_scan_pool` 返回的 `problems` 列表包含一条标注该项 ID 和脏值的消息
- **AND** 该项仍出现在返回的 items 列表中（不被丢弃）
- **AND** `_scan_pool` 正常返回（不 `_die`、不 raise）

#### Scenario: 脏 specific_field 被报告但不中止扫描

- **WHEN** legacy 表某行 type/priority 列的值不在 `POOL_SPEC.specific_values` 中
- **THEN** `_scan_pool` 返回的 `problems` 列表包含一条标注该项 ID 和脏值的消息
- **AND** 该项仍出现在返回的 items 列表中

### Requirement: reindex 总项数只增不减守卫

`_reindex_core` 写盘前 SHALL 读取旧 INDEX.md 的总项数（open + closed），若新扫描总项数 < 旧总项数，SHALL fail-closed 拒绝覆盖（非零退出）。首次建 INDEX（旧总项数 = 0）时跳过校验。

理由：正常操作（add / set-status / batch）只增项或改状态、不删项，总项数只增不减是精确不变量。B12 实测旧版 issues.py 扫不到 overlay 新池 → 57 项降到 51 项，6 项静默消失且 exit 0。

#### Scenario: 版本偏斜下 reindex 拒绝覆盖

- **WHEN** `_reindex_core` 新扫描的总项数 < 旧 INDEX.md 的总项数
- **THEN** raise `ReindexStageError` 且不覆盖 INDEX.md
- **AND** 退出码非零

#### Scenario: 首次建 INDEX 不触发守卫

- **WHEN** 旧 INDEX.md 不存在或总项数 = 0
- **THEN** 正常写入，不触发骤降检测

### Requirement: batch triage 状态解耦

`_bug_triage` 和 `_todo_triage` 在 batch add 时 MUST NOT 修改 item 的 status。batch add 的语义 = 归批次，不改状态。要改状态 SHALL 走 `set-status` 命令。

理由：现状 `open_untriaged` 集合在 batch add 时把 OPEN/VERIFIED 强推为 PROPOSED → 对「有归属无认领」项撒谎。

#### Scenario: batch add 不改 status

- **WHEN** 对一个 status=OPEN 的项执行 batch add
- **THEN** 该项 batch 被更新
- **AND** 该项 status 仍为 OPEN（未被改为 PROPOSED）
