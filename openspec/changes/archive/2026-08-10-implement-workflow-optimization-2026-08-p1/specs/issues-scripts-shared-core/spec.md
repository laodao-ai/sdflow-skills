# issues-scripts-shared-core Delta Specification

## ADDED Requirements

### Requirement: reopen 命令契约（终态唯一受控逆转换）

issues CLI SHALL 新增 `reopen <ID> --reason <理由> [--to OPEN|PROPOSED]` 子命令，作为终态的唯一受控逆转换；既有「终态不可再改」语义相应收窄为「不可经 set-status 再改」，set-status 对 closed/ 的硬拒守卫 MUST 原样保留。命令行为：

- **守卫**：ID 格式合法；目标 issue MUST 位于 `closed/`（位于 open/ 时以非零退出拒绝）；ID 前缀与 frontmatter pool 一致；`--reason` 必填。[spec-review-amendment] 文件位于 closed/ 但 `status` 已非终态 ⇒ 判为中断残留，走幂等恢复（见原子序），MUST NOT 按正常路径重复执行字段清理与历史行追加。
- **状态**：默认置 OPEN；`--to` 仅接受该 pool 的非终态值，终态值以非零退出拒绝。
- **字段**：`closed_date` / `closed_reason` / `resolved_by` 清为 null；原 closed_reason MUST 保留进追加的历史行（含日期、旧状态→新状态、reopen 理由与原 closed_reason；[spec-review-amendment] 原 closed_reason 为空——FIXED/DONE 路径本不写该字段——时历史行写「（无 closed_reason）」，MUST NOT 渲染出 `null`/空串）。
- **原子序**：先在 closed/ 原位置原子写入更新后的 frontmatter+body，再迁移回 open/（git 仓库内用 `git mv`）；[spec-review-amendment] 中断残留（closed/ 内非终态文件）的恢复 = 对同 ID 重跑 reopen 幂等续跑迁移（只补 `git mv` + reindex，不重复写历史行），且 reindex SHALL 对 closed/ 内非终态文件输出可见告警（「可被检出」以此落地——现渲染路径对 status 照单全收，无告警即检不出）。
- **reindex**：命令内自动执行，完成后 INDEX.md / CLOSED.md 与文件系统一致。[spec-review-amendment] 迁移成功后 reindex 自身失败时，错误信息 MUST 明示「重开已生效，重跑 reindex 即自愈」（reindex 为无状态重算，可安全重跑），MUST NOT 让调用方把非零退出误读为「未发生任何变更」。

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

#### Scenario: 中断残留幂等恢复 [spec-review-amendment]

- **WHEN** reopen 在原位原子写成功、`git mv` 执行前中断（closed/ 内残留 status 已非终态、字段已清、历史行已追加的文件），随后对同 ID 重跑 reopen
- **THEN** 命令幂等续跑迁移与 reindex 成功收敛（文件回 open/、索引一致），且不重复追加历史行、不产生「原 closed_reason：null」类误导记录

#### Scenario: 既有守卫零回归

- **WHEN** reopen 命令落地后对 closed/ 中的 issue 执行 set-status
- **THEN** 仍以非零退出拒绝（「已处于终态」守卫原样），既有全部契约测试保持通过
