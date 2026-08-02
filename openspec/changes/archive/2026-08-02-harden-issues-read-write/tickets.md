---
impl-pipeline: tickets
---

## Global Constraints

- 改动面 = `sdflow_issues_core/__init__.py` + `issues.py` + `SKILL.md` + 测试。MUST NOT 改写入路径（cmd_add / set-status 的 `_die` 是正当防护）。
- 遵守 `POOL_SPEC` 封闭 schema 注入（不加 pool 条件分支）。
- 脏值项 MUST 仍收入 items 列表（不丢弃、不过滤），确保盘点总数准确。problem 报告应包含 item ID 和脏值。
- `validate_scan_envelope` 降级后 MUST NOT raise，收进 problems + 继续。
- 总项数只增不减是精确不变量；旧 INDEX 不可解析时视为 0（跳过校验 + 记 problem 警告），不卡死 reindex。
- `triage` CLI 的原行为（赋批次+推进状态）MUST 保持不变；`--batch-only` 只在显式传入时生效。
- `cmd_sweep` 的子进程调用 MUST 改用 `triage --batch-only`。

### Task 1: 读取路径两层词表校验

**Blocked-by:** none
**R-ID:** R1

在 core 层 `_build_effective_snapshot`（`__init__.py:826-901`）的自检段追加 status 和 specific_field 词表校验：超出词表的值记入 `problems`，不 raise、不 `_die`、不丢弃项。

在 consumer 边界 `validate_scan_envelope`（`issues.py:437-440`）将 status 和 specific_field 枚举漂移的硬 `raise ValueError` 降级为收进 problems + 继续。

- [x] `_build_effective_snapshot` 自检段追加 `item["status"] not in spec.status_values` → `problems.append`
- [x] `_build_effective_snapshot` 自检段追加 `item[spec.specific_field] not in spec.specific_values` → `problems.append`
- [x] `validate_scan_envelope` status/specific_field 枚举漂移的硬 raise 改为收进 problems + 继续
- [x] 测试：构造脏 status 的 legacy 行 → 断言 problems 非空 + 项仍在 items 中 + scan 正常返回
- [x] 测试：构造脏 specific_field 的 legacy 行 → 断言 problems 非空 + 项仍在 items 中
- [x] 测试：构造脏 status 项 → 跑 `issues.py reindex` 端到端 → 断言不崩 + problems 非空

### Task 2: reindex 总项数只增不减守卫

**Blocked-by:** none
**R-ID:** R2

在 `issues.py` 新增 `_count_index_items(path)` 辅助函数：两段式解析旧 INDEX.md（open = 数 `| [A-Z]\d+ |` 表格行，closed = 解析"共 N 项已闭合"聚合行的 N），返回两者之和。不存在/不可解析 → 返回 0。

`_reindex_core` 写盘前调用该函数，新扫描总项数 < 旧总项数 → `raise ReindexStageError` 拒绝覆盖。

- [x] 新增 `_count_index_items(index_path)` 函数：两段式解析 open 行数 + closed 聚合数
- [x] `_reindex_core` 写盘前调用，`new_count < old_count` 且 `old_count > 0` → raise ReindexStageError
- [x] 测试：旧 INDEX 有 N 项（含 closed 聚合行）、新扫描 < N → 断言 raise + INDEX 未被覆盖
- [x] 测试：旧 INDEX 只有 closed 项（open=0、closed>0）、新扫描丢了 closed 项 → 断言 raise
- [x] 测试：首次建（旧不存在）→ 正常写入不触发守卫
- [x] 测试：旧 INDEX 格式损坏 → 返回 0 跳过校验，不卡死 reindex

### Task 3: sweep 路径 triage 状态解耦 + 文档同步

**Blocked-by:** none
**R-ID:** R3

给 `_bug_triage` / `_todo_triage` 加 `promote` 参数（默认 `True`）。`promote=False` 时跳过 `open_untriaged` 推进逻辑（`new_status = old_status`）。`triage` CLI 子命令新增 `--batch-only` flag 映射到 `promote=False`。`cmd_sweep` 的子进程调用改为 `triage --batch-only`。SKILL.md 同步更新 triage/sweep 文档。

- [x] `_bug_triage` 加 `promote` 参数（默认 True），`promote=False` 时 `new_status = old_status`
- [x] `_todo_triage` 加 `promote` 参数（默认 True），`promote=False` 时 `new_status = old_status`
- [x] `triage` CLI 新增 `--batch-only` flag → args 传递到 `_cmd_triage` → `promote=False`
- [x] `cmd_sweep` 子进程调用改为 `triage --batch-only --id X --批次 Y`
- [x] 测试：直接 triage OPEN 项（无 --batch-only）→ 断言 status 变为 PROPOSED（原行为不变）
- [x] 测试：triage --batch-only OPEN 项 → 断言 status 仍为 OPEN + batch 已更新
- [x] 测试：cmd_sweep 端到端 → 断言被 sweep 项 status 保持原样
- [x] SKILL.md:495-496 triage 命令表：补充 `--batch-only` 说明
- [x] SKILL.md:505 sweep 协议描述：注明 sweep 使用 `--batch-only`

### Task 4: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落
`impl-reports/task4-verification.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [x] 单元测试证据齐全并通过
- [x] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [x] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
