## ADDED Requirements

### Requirement: 总览表 row 字段 table-cell-safe（写时 reject 守盘面完整性）

issues 池 recorder（`buglist.py` / `todolist.py` / `issues.py`）以 markdown 表存状态总览（「盘面即状态」的盘面），其行按 `|` 切列。recorder SHALL 在**写路径**保证进入总览表 row 的字段（`module` / `summary` / `change` / batch key）**table-cell-safe**：字段含 ASCII `|` **或**换行（会致列错位 / 整行截断而腐蚀盘面）时 MUST 拒绝写入（`_die` 报清晰错误，复用既有 priority/status 非法即拒的写时校验惯例），MUST NOT 静默转义或替换。详细块的 prose 字段（现象/根因/修复等）不受此约束（非 `|` 分隔表）。此为写时 fail-closed 守卫，非事后解析补救。

#### Scenario: 字段含 `|` 或换行被写时拒绝

- **WHEN** 记录或回写一条 item，其 `summary` / `module` / `change` / batch key 含 ASCII `|` 或换行
- **THEN** recorder 以清晰错误拒绝写入（`_die`），不产生任何列错位 / 行截断的腐蚀盘面，并提示改写

#### Scenario: 详细块 prose 不受 table-cell-safe 约束

- **WHEN** 一条 item 的详细块字段（现象 / 根因 / 修复等 prose）含 `|` 或换行
- **THEN** 正常写入（详细块非 `|` 分隔表、无腐蚀风险），不被拒绝

### Requirement: reindex 一致性问题可观测且不阻断重建

`issues.py reindex` SHALL 把子进程 `scan` 报出的表↔块一致性 problems **回显到 stderr**（逐条带 pool / 文件定位），使独立跑 reindex 时的不一致对用户可见（兑现 D5 承诺）。problems 非空 MUST NOT 使 reindex 失败——INDEX SHALL 照常确定性重建、退出码为 0；此与**致命错误**（无法读取文件等）仍以非 0 退出相区分（一致性警示与致命失败分层）。

#### Scenario: problems 回显 stderr 但不阻断 INDEX 重建

- **WHEN** 池中某 dated 文件存在表↔块不一致，运行 `issues.py reindex`
- **THEN** 每条 problem 逐条出现在 stderr（含 pool / 文件定位），INDEX 仍被完整重建，退出码为 0

#### Scenario: 独立跑 reindex 时不一致不再静默

- **WHEN** 不经 `scan`、直接运行 `reindex`，且池中存在表↔块不一致项
- **THEN** 用户从 stderr 看到具体不一致项（而非静默重建、不一致被吞）
