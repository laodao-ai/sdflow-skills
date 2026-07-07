## ADDED Requirements

### Requirement: recorder 字段内容安全——防 `|` 致表列腐蚀

issues 池 recorder（`buglist.py` / `todolist.py` / `issues.py`）以 markdown 表存状态总览，其行解析按 `|` 切列。recorder SHALL 保证**字段值内的 ASCII `|` 不破坏列的位置解析**：写路径 MUST 把字段值（`module` / `summary` / 批次名等）里的 `|` 转义为 `\|`；解析器 MUST 按**未转义** `|` 切列、读出后反转义还原原值；读路径遇既有**未转义**（历史腐蚀）`|` MUST fail-safe——尽力解析、不抛异常、不产生二次腐蚀。此为系统性数据完整性保证，非单点修补。

#### Scenario: 含 `|` 字段存取往返逐字节一致

- **WHEN** 记录一条 `summary` 或 `module` 字段含 ASCII `|` 的 item（如命令 `grep a | b`）
- **THEN** 写入表中为转义形式 `\|`，后续 `scan` / `set-status` 读回的字段值与原文逐字节一致，且该行及后续列不发生错位

#### Scenario: 旧裸 `|` 腐蚀行解析不 crash

- **WHEN** 解析一个字段含**未转义** `|` 的历史遗留行
- **THEN** 解析器不抛异常、尽力还原可读列、不对该行做二次腐蚀（fail-safe 降级而非崩溃）

### Requirement: reindex 一致性问题可观测且不阻断重建

`issues.py reindex` SHALL 把子进程 `scan` 报出的表↔块一致性 problems **回显到 stderr**（逐条带 pool / 文件定位），使独立跑 reindex 时的不一致对用户可见（兑现 D5 承诺）。problems 非空 MUST NOT 使 reindex 失败——INDEX SHALL 照常确定性重建、退出码为 0；此与**致命错误**（无法读取文件等）仍以非 0 退出相区分（一致性警示与致命失败分层）。

#### Scenario: problems 回显 stderr 但不阻断 INDEX 重建

- **WHEN** 池中某 dated 文件存在表↔块不一致，运行 `issues.py reindex`
- **THEN** 每条 problem 逐条出现在 stderr（含 pool / 文件定位），INDEX 仍被完整重建，退出码为 0

#### Scenario: 独立跑 reindex 时不一致不再静默

- **WHEN** 不经 `scan`、直接运行 `reindex`，且池中存在表↔块不一致项
- **THEN** 用户从 stderr 看到具体不一致项（而非静默重建、不一致被吞）
