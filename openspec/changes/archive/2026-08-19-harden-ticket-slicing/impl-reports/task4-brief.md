### Task 4: T141 收口（issues 池状态与证据链闭合）

**Blocked-by:** 1,2,3
**R-ID:** —（issues 池纪律；对应 proposal「Impact - issues 池：T141 关闭」）

T141（把 change 拆分标准融入 workflow 三处触发）开了七周未收口，本 change 的 Task 1–3 已交付其全部
实质内容，此票负责让 issues 池的状态与事实一致：把 T141 置为 DONE，`resolved_by` 指向本 change，
证据指向 Task 1 产出的单一源文件与 Task 3 的三处引用。

- [ ] T141 状态由 OPEN 变为 DONE，`resolved_by` = 本 change 名
- [ ] evidence 指向拆分标准单一源文件 + 三处指针引用的落点（可被后续读者按图索骥）
- [ ] **用开发 checkout 的 issues 脚本操作**（本仓 `sdflow-issues/scripts/`），MUST NOT 用 `~/.claude/skills` 下的 symlink（那指向运行 checkout 的旧版 writer）
- [ ] 操作后 T141 已不在 open 池、在 closed 池中，且全仓 issues 相关测试仍绿

