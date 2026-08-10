### Task 1: recorder reopen 命令

**Blocked-by:** none
**R-ID:** R-IS1

在 `sdflow-issues/scripts/issues_v2.py` 新增 `reopen` 子命令，实现 closed→open 的唯一受控逆转换。

行为描述：
- `issues_v2.py reopen <ID> --reason <理由> [--to OPEN|PROPOSED]`
- 守卫：ID 必须位于 closed/（在 open/ ⇒ `_die`「ID {id} 不在终态（位于 open/），无需 reopen」）、pool/前缀一致、`--reason` 必填（argparse required）、`--to` 只接受非终态值（OPEN|PROPOSED，终态值 ⇒ `_die`「--to 只接受非终态状态（OPEN|PROPOSED），收到 {v}」）
- closed/ 内文件状态已非终态 ⇒ 判中断残留，幂等续跑迁移（不重复清字段、不重复追加历史行）
- 状态默认回 OPEN，`--to PROPOSED` 可选
- 字段清理：closed_date/closed_reason/resolved_by → null；原 closed_reason 进历史行（空值写「（无 closed_reason）」）
- 历史行格式：`> 日期 状态：WONTDO → OPEN（reopen：<理由>；原 closed_reason：<原值>）`
- M-2 原子序：closed/ 原位原子写 → git mv 回 open/
- 命令内自动 reindex（含 closed/ 非终态文件 WARNING 输出；git mv 后 reindex 失败文案「重开已生效，重跑 reindex 即自愈」）
- 复用 `issues_v2.py` 内联 mechanics（`_die`/`atomic_write_text`/`cmd_set_status` M-2 序/`cmd_reindex`），MUST NOT import `sdflow_issues_core`
- MUST NOT 改 set-status 既有守卫
- 契约测试（`sdflow-issues/tests/`）：往返（add→终态→reopen→字段/目录/INDEX/CLOSED 全一致）、拒绝面三例（open 项 / 缺 reason / --to 终态值，均验「文件与索引零变更」）、中断残留幂等恢复用例（原位写后 mv 前中断 → 重跑收敛且不重复历史行）、既有守卫零回归（set-status 对 closed/ 仍拒 + 全量既有测试绿）
- SKILL.md 文档同步：`sdflow-issues/SKILL.md` 补 `reopen` 用法块并修正措辞

- [ ] reopen 子命令实现（守卫 + 字段清理 + M-2 原子序 + 自动 reindex + 中断残留恢复）
- [ ] 契约测试：往返 + 拒绝面三例 + 中断残留幂等 + 既有守卫零回归
- [ ] SKILL.md 文档同步

