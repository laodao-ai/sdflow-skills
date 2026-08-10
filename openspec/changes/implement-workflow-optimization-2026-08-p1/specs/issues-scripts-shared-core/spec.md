# issues-scripts-shared-core Delta Specification

## ADDED Requirements

### Requirement: reopen 命令契约（终态唯一受控逆转换）

issues CLI SHALL 新增 `reopen <ID> --reason <理由> [--to OPEN|PROPOSED]` 子命令，作为终态的唯一受控逆转换；既有「终态不可再改」语义相应收窄为「不可经 set-status 再改」，set-status 对 closed/ 的硬拒守卫 MUST 原样保留。命令行为：

- **守卫**：ID 格式合法；目标 issue MUST 位于 `closed/`（位于 open/ 时以非零退出拒绝）；ID 前缀与 frontmatter pool 一致；`--reason` 必填。
- **状态**：默认置 OPEN；`--to` 仅接受该 pool 的非终态值，终态值以非零退出拒绝。
- **字段**：`closed_date` / `closed_reason` / `resolved_by` 清为 null；原 closed_reason MUST 保留进追加的历史行（含日期、旧状态→新状态、reopen 理由与原 closed_reason）。
- **原子序**：先在 closed/ 原位置原子写入更新后的 frontmatter+body，再迁移回 open/（git 仓库内用 `git mv`）；中断残留（closed/ 内非终态文件）SHALL 可被 reindex 检出。
- **reindex**：命令内自动执行，完成后 INDEX.md / CLOSED.md 与文件系统一致。

#### Scenario: 往返一致性

- **WHEN** 对同一 issue 依次执行 add → set-status 置终态 → reopen
- **THEN** 该 issue 文件位于 open/ 对应池目录、status 为 OPEN（或 --to 指定的非终态值）、三个终态字段为 null、正文含记录原 closed_reason 的历史行，且 INDEX.md 计入 open 项、CLOSED.md 不再计入该项

#### Scenario: open 项拒绝 reopen

- **WHEN** 对位于 open/ 的 issue 执行 reopen
- **THEN** 命令以非零退出并报「不在终态」，文件与索引无任何变更

#### Scenario: 缺 reason 拒绝

- **WHEN** 执行 reopen 未提供 `--reason`
- **THEN** 命令以非零退出，文件与索引无任何变更

#### Scenario: --to 传终态值拒绝

- **WHEN** 执行 reopen 且 `--to` 为该 pool 的终态值（如 todo 池的 DONE/WONTDO）
- **THEN** 命令以非零退出并报状态值非法，文件与索引无任何变更

#### Scenario: 既有守卫零回归

- **WHEN** reopen 命令落地后对 closed/ 中的 issue 执行 set-status
- **THEN** 仍以非零退出拒绝（「已处于终态」守卫原样），既有全部契约测试保持通过
