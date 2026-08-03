# Tasks: issues-v2-single-file-model

## 1. 核心脚本 `issues.py`

- [x] 1.1 实现 `read_issue()` / `write_issue()` / `parse_frontmatter()` 基础 IO [STOR-01]——write_issue 创建新文件用 O_CREAT|O_EXCL（C8）；frontmatter 值一律双引号包裹（C9）[spec-review-amendment]
- [x] 1.2 实现 `cmd_add` —— `add --pool --json` 创建新 issue 到 open/，含 detect_change 自动填 source_change + git add [STOR-05, STOR-04, C10] [spec-review-amendment]
- [x] 1.3 实现 `cmd_set_status` —— 状态校验（含 todo DONE evidence 门禁）+ evidence/reason 追加到 body 变更历史行 + 终态 git mv（先确保 tracked；非 git 降级 os.rename）[STOR-02, STOR-06] [spec-review-amendment]
- [x] 1.4 实现 `cmd_scan` —— 扫描 open/closed + `--pool`/`--status`/`--source-change`/`--json` 过滤 + JSON 输出 [STOR-07] [spec-review-amendment]
- [x] 1.5 实现 `cmd_reindex` —— 再生 INDEX.md + CLOSED.md [STOR-03]
- [x] 1.6 实现 `cmd_next_id` —— 跨 open+closed 扫文件名取 max+1 [STOR-04]

## 2. 迁移工具 `migrate`

- [x] 2.1 实现双格式解析 + 逐 item 去重（frontmatter 优先于 legacy 表格行，复用 shadow 逻辑）[MIG-01] [spec-review-amendment]
- [x] 2.2 实现迁移主流程：解析 → 字段映射（resolved_by 从 body 提取、closed_date best-effort）→ 写 v2 文件 → reindex [MIG-02, MIG-04] [spec-review-amendment]
- [x] 2.3 实现幂等逻辑（已存在则跳过）+ 统计报告（含 shadowed ID 数、resolved_by 来源分桶）[MIG-03] [spec-review-amendment]
- [x] 2.4 实现 PLANNED 批次信息迁移（成员 issue body 追加批次计划文本）[MIG-05] [spec-review-amendment]

## 3. 本仓数据迁移

- [x] 3.1 对本仓执行 `issues.py migrate --root .`，验证 287 个 issue 全部迁移 [MIG-02]
- [x] 3.2 清理旧文件（`buglist/`、`todolist/`、`batches.md`、`batch-triage-rules.md`、`consolidation-plan.md`）
- [x] 3.3 清理旧脚本（`buglist.py`、`todolist.py`、`sdflow_issues_core/`、`migrate_legacy.py`）[REMOVED]

## 4. 消费方更新 [spec-review-amendment]

- [x] 4.1a 更新 `sdflow-issues/SKILL.md`：数据模型、命令文档 [STOR-01~07]
- [x] 4.1b 更新 `sdflow-issues/SKILL.md`：路由逻辑、触发判据 [STOR-01~07]
- [x] 4.2 重写 `sdflow-done/SKILL.md` §2.1：sweep→scan --source-change + hand-off 改列 ID [C10]
- [x] 4.3 更新 `hack/tests/test_harden_sdflow_spec_followup_closure.py`：`TODO_SCRIPT` 路径
- [x] 4.4 更新 `CLAUDE.md` / `README.md`：命令示例和路径引用
- [x] 4.5 更新 `AGENTS.md`：issues 路径引用
- [x] 4.6 更新 `sdflow-init/assets/snippets/claude-section.md`：issues 路径引用（推给消费仓的模版）
- [x] 4.7 更新 `openspec/CONTEXT.md`：领域术语（三脚本→单脚本、目录结构、终态词表）
- [x] 4.8 补 `openspec/specs/spec-workflow/spec.md` MODIFIED delta（L210/L222/L333-334/L95/L660）
- [x] 4.9 补 `openspec/specs/determinism-guards/spec.md` MODIFIED/REMOVED delta（POOL_SPEC 守卫消解 + reindex 骤降守卫移植）
- [x] 4.10 补 `openspec/specs/recorder-root-resolution/spec.md` MODIFIED delta（三薄入口→单入口）
- [x] 4.11 更新/退役 `.github/workflows/windows-recorder-smoke.yml` 硬编码测试路径

## 5. 测试 [spec-review-amendment]

- [x] 5.1 核心命令测试：add（含并发 O_CREAT|O_EXCL 重试）/ set-status（含 todo DONE evidence、非 git 降级、未 tracked git add）/ scan（含 --source-change）/ reindex / next-id [STOR-01~07]
- [x] 5.2 迁移测试：双格式共存去重 + 字段映射（resolved_by body 提取）+ 幂等 + 批次信息迁移 [MIG-01~05]
- [x] 5.3a 清理格式耦合的旧测试（表格解析、marker block 双写一致性等）
- [x] 5.3b 改造保留格式无关的不变量测试（仓根解析 `test_repo_root_identity_*`、Windows 编码 `test_task2_windows_local_fs_smoke`、覆盖率门禁 `test_task6_coverage_gate`）
- [x] 5.4 全仓 pytest 绿

## 测试覆盖图 (TG-18) [spec-review-amendment]

| 代码路径 | 测试类型 | 覆盖 task |
|----------|---------|-----------|
| `read_issue` / `write_issue`（含 YAML 双引号序列化） | 单元测试 | 5.1 |
| `write_issue` 并发 O_CREAT\|O_EXCL 重试 | 集成测试（multiprocessing） | 5.1 |
| `cmd_add`（含 detect_change + git add） | 集成测试（tmp_path + subprocess） | 5.1 |
| `cmd_set_status` + body 变更历史行 + git mv（含未 tracked 先 git add、非 git 降级） | 集成测试（git init + subprocess） | 5.1 |
| `cmd_set_status` todo DONE 缺 evidence 拒绝 | 单元测试 | 5.1 |
| `cmd_scan` 过滤（含 --source-change） | 单元测试 | 5.1 |
| `cmd_reindex` 再生 | 集成测试 | 5.1 |
| `cmd_next_id` 跨目录 | 单元测试 | 5.1 |
| 双格式共存去重（frontmatter 优先于 legacy 表格行） | 单元测试 | 5.2 |
| 迁移主流程（含 resolved_by body 提取、closed_date best-effort） | 集成测试（fixture 仓） | 5.2 |
| 幂等跳过 | 集成测试 | 5.2 |
| PLANNED 批次信息迁移 | 集成测试 | 5.2 |
| 仓根解析（改造自 v1 test_repo_root_identity_*） | 集成测试 | 5.3b |
| Windows 编码（改造自 v1 test_task2_windows_local_fs_smoke） | CI 冒烟 | 5.3b |
| sdflow-done scan --source-change 集成 | 外部消费方冒烟 | 5.4 |
