### Task 1: 核心脚本 issues.py——全部 CRUD 命令 + 测试

**Blocked-by:** none
**R-ID:** STOR-01, STOR-02, STOR-03, STOR-04, STOR-05, STOR-06, STOR-07

实现 `sdflow-issues/scripts/issues.py` 单入口 CLI，包含以下子命令：

**内部函数**：`parse_frontmatter()` / `read_issue()` / `write_issue()` / `find_issue()`。
- `parse_frontmatter` 解析 `---` 围栏内的 YAML 子集（`^key: "value"$` 或 `^key: null$`）
- `write_issue` 创建新文件用 `O_CREAT|O_EXCL`；更新已有文件用 `.tmp` + `os.rename`（原子替换）
- `find_issue(id)` 在 open/ 和 closed/ 中定位

**命令**：
- `add --pool {bug|todo} --json '{...}'`：创建新 issue 到 open/，含 detect_change + O_CREAT|O_EXCL + git add
- `set-status --id {ID} --to {STATUS} [--evidence ...] [--reason ...]`：状态校验 + body 历史行 + 终态 git mv（含 tracked 检查、非 git 降级）
- `scan [--pool] [--status] [--source-change] [--all] [--json]`：扫描过滤 + JSON 输出
- `reindex`：再生 INDEX.md + CLOSED.md
- `next-id --pool {bug|todo}`：跨 open+closed 扫文件名取 max+1

**测试**（tasks 5.1 对应，与实现同票 TDD）：
- `parse_frontmatter` / `read_issue` / `write_issue` 的 YAML 双引号序列化单元测试
- `write_issue` 并发 O_CREAT|O_EXCL 重试集成测试（multiprocessing）
- `cmd_add` 集成测试（tmp_path + detect_change + git add）
- `cmd_set_status` 集成测试（git init + body 历史行 + git mv + 未 tracked 先 git add + 非 git 降级 os.rename）
- `cmd_set_status` todo DONE 缺 evidence 拒绝单元测试
- `cmd_scan` 过滤单元测试（含 --source-change）
- `cmd_reindex` 再生集成测试
- `cmd_next_id` 跨目录单元测试

- [ ] `parse_frontmatter` 正确解析双引号值和 null
- [ ] `write_issue` 创建新文件使用 O_CREAT|O_EXCL，并发写同 ID 时后到者 FileExistsError
- [ ] `cmd_add` 创建 issue 到 open/，frontmatter 含所有必填字段，detect_change 自动填 source_change
- [ ] `cmd_set_status` 终态时填 closed_date/resolved_by + 追加 body 历史行 + git mv（含 tracked 检查）
- [ ] `cmd_set_status` 非 git 仓终态降级为 os.rename
- [ ] `cmd_set_status` todo DONE 缺 evidence 被拒（非零退出码）
- [ ] `cmd_scan` 默认只输出 open/，--all 含 closed/，--source-change 正确过滤
- [ ] `cmd_reindex` 再生的 INDEX.md/CLOSED.md 含全部 issue 且按 ID 排序
- [ ] `cmd_next_id` 跨 open+closed 正确取 max+1
- [ ] 全部单元+集成测试通过

