# Tasks: issues-v2-single-file-model

## 1. 核心脚本 `issues.py`

- [ ] 1.1 实现 `read_issue()` / `write_issue()` / `parse_frontmatter()` 基础 IO [STOR-01]
- [ ] 1.2 实现 `cmd_add` —— `add --pool --json` 创建新 issue 到 open/ [STOR-05, STOR-04]
- [ ] 1.3 实现 `cmd_set_status` —— 状态校验 + 终态自动 git mv [STOR-02, STOR-06]
- [ ] 1.4 实现 `cmd_scan` —— 扫描 open/closed + 过滤 + JSON 输出 [STOR-07]
- [ ] 1.5 实现 `cmd_reindex` —— 再生 INDEX.md + CLOSED.md [STOR-03]
- [ ] 1.6 实现 `cmd_next_id` —— 跨 open+closed 扫文件名取 max+1 [STOR-04]

## 2. 迁移工具 `migrate`

- [ ] 2.1 实现 legacy 表格格式解析器 [MIG-01]
- [ ] 2.2 实现 frontmatter overlay 格式解析器 [MIG-01]
- [ ] 2.3 实现迁移主流程：解析 → 字段映射 → 写 v2 文件 → reindex [MIG-02, MIG-04]
- [ ] 2.4 实现幂等逻辑（已存在则跳过）+ 统计报告 [MIG-03]

## 3. 本仓数据迁移

- [ ] 3.1 对本仓执行 `issues.py migrate --root .`，验证 287 个 issue 全部迁移 [MIG-02]
- [ ] 3.2 清理旧文件（`buglist/`、`todolist/`、`batches.md`、`batch-triage-rules.md`、`consolidation-plan.md`）
- [ ] 3.3 清理旧脚本（`buglist.py`、`todolist.py`、`sdflow_issues_core/`、`migrate_legacy.py`）[REMOVED]

## 4. 消费方更新

- [ ] 4.1 更新 `sdflow-issues/SKILL.md`：命令示例、数据模型、路由逻辑 [STOR-01~07]
- [ ] 4.2 更新 `sdflow-done/SKILL.md`：sweep 调用路径改为 `issues.py scan` [STOR-07]
- [ ] 4.3 更新 `hack/tests/test_harden_sdflow_spec_followup_closure.py`：`TODO_SCRIPT` 路径 [STOR-07]
- [ ] 4.4 更新 `CLAUDE.md` / `README.md`：命令示例和路径引用

## 5. 测试

- [ ] 5.1 核心命令测试：add / set-status / scan / reindex / next-id [STOR-01~07]
- [ ] 5.2 迁移测试：两种旧格式解析 + 字段映射 + 幂等 [MIG-01~04]
- [ ] 5.3 清理旧测试文件（与旧格式深度耦合的测试全部删除）
- [ ] 5.4 全仓 pytest 绿

## 测试覆盖图 (TG-18)

| 代码路径 | 测试类型 | 覆盖 task |
|----------|---------|-----------|
| `read_issue` / `write_issue` | 单元测试 | 5.1 |
| `cmd_add` | 集成测试（tmp_path + subprocess） | 5.1 |
| `cmd_set_status` + git mv | 集成测试（git init + subprocess） | 5.1 |
| `cmd_scan` 过滤 | 单元测试 | 5.1 |
| `cmd_reindex` 再生 | 集成测试 | 5.1 |
| `cmd_next_id` 跨目录 | 单元测试 | 5.1 |
| legacy 表格解析 | 单元测试 | 5.2 |
| frontmatter overlay 解析 | 单元测试 | 5.2 |
| 迁移主流程 | 集成测试（fixture 仓） | 5.2 |
| 幂等跳过 | 集成测试 | 5.2 |
| sdflow-done sweep 集成 | 外部消费方冒烟 | 5.4 |
