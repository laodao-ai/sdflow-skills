---
impl-pipeline: tickets
---

## Global Constraints

以下约束逐字摘自本 change design.md / decision-memo.md / specs 的 MUST/MUST NOT/SHALL 条款：

- frontmatter 写出时值一律双引号包裹：`key: "value"`（内部 `"` → `\"`，`null` 写成字面 `null` 不加引号）；读回匹配 `^key: "(.*)"$` 或 `^key: null$`。不引入 PyYAML 依赖（ADR-0025）。
- `write_issue` 创建新文件用 `O_CREAT|O_EXCL`（后到者 `FileExistsError` → `next-id` 重试）。
- frontmatter 必填字段：`id`, `pool`, `status`, `date`, `module`, `summary`。可选字段：`priority`(bug only), `type`(todo only), `source_change`, `resolved_by`, `closed_date`, `closed_reason`。字段顺序固定。
- 脚本 SHALL 只读写 frontmatter，MUST NOT 解析 body 内容。
- 终态：bug = FIXED | WONTFIX；todo = DONE | WONTDO。终态触发 git mv open/ → closed/（非 git 仓降级 os.rename）。
- set-status 校验：bug FIXED 必须 `--evidence`；todo DONE 必须 `--evidence`；WONTFIX/WONTDO 必须 `--reason`。终态 issue 不可再改 status。
- set-status 成功后追加 body 变更历史行：`> {date} 状态：{old} → {new}（{evidence 或 reason}）`。
- set-status 到终态时 git mv 前确保文件已 tracked（`git ls-files --error-unmatch`，未 tracked 则先 `git add`）。
- INDEX.md / CLOSED.md 为派生产物，MUST NOT 手工编辑，reindex 再生。
- add 含 detect_change 自动填 source_change + `git add`（幂等，非 git 仓时跳过）。
- scan 默认只扫 open/，`--all` 含 closed/；支持 `--pool`/`--status`/`--source-change`/`--json` 过滤。
- 迁移逐 item 去重（frontmatter 优先于 legacy 表格行），复用 `_build_effective_snapshot` 的 shadow 逻辑。迁移数据不受 STOR-06 的 evidence/reason 门禁约束。
- resolved_by 从 body 状态变更历史行提取，不从旧 `change` 字段取。closed_date best-effort 从 body 提取，失败取文件日期。
- PLANNED 批次信息迁移进成员 issue body（`> [迁移自批次 {batch_key}] 原计划: {plan_text}`）。
- sdflow-done sweep 替代为 `issues.py scan --json --source-change {change_name} --status OPEN --status PROPOSED`。
- 新增 Python 入口脚本须带 4 行 `reconfigure` 前导（`sys.stdout`/`sys.stderr` encoding="utf-8"）。

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

- [x] `parse_frontmatter` 正确解析双引号值和 null
- [x] `write_issue` 创建新文件使用 O_CREAT|O_EXCL，并发写同 ID 时后到者 FileExistsError
- [x] `cmd_add` 创建 issue 到 open/，frontmatter 含所有必填字段，detect_change 自动填 source_change
- [x] `cmd_set_status` 终态时填 closed_date/resolved_by + 追加 body 历史行 + git mv（含 tracked 检查）
- [x] `cmd_set_status` 非 git 仓终态降级为 os.rename
- [x] `cmd_set_status` todo DONE 缺 evidence 被拒（非零退出码）
- [x] `cmd_scan` 默认只输出 open/，--all 含 closed/，--source-change 正确过滤
- [x] `cmd_reindex` 再生的 INDEX.md/CLOSED.md 含全部 issue 且按 ID 排序
- [x] `cmd_next_id` 跨 open+closed 正确取 max+1
- [x] 全部单元+集成测试通过

### Task 2: 迁移工具 migrate + 测试

**Blocked-by:** 1
**R-ID:** MIG-01, MIG-02, MIG-03, MIG-04, MIG-05

在 `issues.py` 中实现 `cmd_migrate` 子命令，提供一次性从 v1 格式到 v2 格式的迁移。

**核心流程**：
1. 扫描 `openspec/issues/buglist/*.md` + `openspec/issues/todolist/*.md`
2. 每个文件：解析 legacy 表格行 → 再用 frontmatter overlay items 覆盖同 ID（frontmatter 优先）→ 得到 effective 集合
3. 每个 item：字段映射（resolved_by 从 body 提取、closed_date best-effort、date 从文件名提取）
4. 写 v2 文件：活跃 → open/{ID}.md，已关闭 → closed/{ID}.md
5. PLANNED 批次信息迁移：读 batches.md，把 PLANNED 批次的计划文本追加到成员 issue body
6. 幂等：已存在目标文件跳过（按 ID 判重）
7. 完成后自动调 reindex
8. 输出统计报告（迁移数、跳过数、shadowed ID 数、resolved_by 来源分桶）

**迁移数据约束豁免**：迁移产出的文件不经过 set-status，不受 STOR-06 门禁约束。

**测试**（tasks 5.2 对应，与实现同票 TDD）：
- 双格式共存去重（frontmatter 优先于 legacy 表格行）单元测试
- 迁移主流程集成测试（fixture 仓：含 resolved_by body 提取、closed_date best-effort）
- 幂等跳过集成测试
- PLANNED 批次信息迁移集成测试

- [x] 解析纯 legacy 表格格式，从表格行+detail section 提取全部字段
- [x] 解析纯 frontmatter overlay 格式，从 frontmatter+marker block 提取
- [x] 同文件双格式共存时 frontmatter 优先于 legacy 表格行（ID 冲突去重）
- [x] 字段映射正确：resolved_by 从 body 提取、closed_date best-effort、date 从文件名
- [x] 活跃 issue 到 open/，已关闭到 closed/
- [x] PLANNED 批次的计划文本迁移进成员 issue body
- [x] 幂等：已存在的目标文件跳过，统计报告含 skipped 数
- [x] 迁移后自动 reindex，INDEX.md/CLOSED.md 完整
- [x] 统计报告含 shadowed ID 数和 resolved_by 来源分桶

### Task 3: 本仓数据迁移 + 旧文件清理 + 测试调整

**Blocked-by:** 2
**R-ID:** MIG-02, STOR-01

在本仓执行实际迁移，清理旧代码，调整测试。

**迁移执行**：
- 对本仓执行 `python3 sdflow-issues/scripts/issues.py migrate --root .`
- 验证 287 个 issue 全部迁移到 v2 格式（open/ + closed/ 文件数之和 = 287）
- reindex 后 INDEX.md/CLOSED.md 内容完整

**旧文件清理**：
- 删除旧文件：`buglist/`、`todolist/`、`batches.md`、`batch-triage-rules.md`、`consolidation-plan.md`
- 删除旧脚本：`buglist.py`、`todolist.py`、`sdflow_issues_core/`（2175 行包）、`migrate_legacy.py`

**测试调整**：
- 清理格式耦合的旧测试（表格解析、marker block 双写一致性等）
- 改造保留格式无关的不变量测试：`test_repo_root_identity_*`（仓根解析）、`test_task2_windows_local_fs_smoke`（Windows 编码）、`test_task6_coverage_gate`（覆盖率门禁）——改指向 v2 的 issues.py

- [x] 迁移完成，open/ + closed/ 文件数之和 = 287
- [x] INDEX.md 列出 open/ 中全部 issue，CLOSED.md 列出 closed/ 中全部
- [x] 旧文件（buglist/、todolist/、batches.md 等）和旧脚本（buglist.py、todolist.py、sdflow_issues_core/、migrate_legacy.py）已删除
- [x] 格式耦合的旧测试已清理
- [x] 格式无关的不变量测试改造后通过（仓根解析、Windows 编码、覆盖率门禁）

### Task 4: 消费方全部更新 + 全仓 pytest 绿

**Blocked-by:** 3
**R-ID:** STOR-01, STOR-05, STOR-06, STOR-07

更新全部 11 个消费方引用，确保全仓一致：

1. `sdflow-issues/SKILL.md`：数据模型文档（单文件 schema、open/closed 目录）+ 命令文档（issues.py CLI）
2. `sdflow-issues/SKILL.md`：路由逻辑、触发判据（从三脚本路由改为单脚本）
3. `sdflow-done/SKILL.md` §2.1：sweep 改为只读 `scan --source-change` + hand-off 改列 ID
4. `hack/tests/test_harden_sdflow_spec_followup_closure.py`：`TODO_SCRIPT` 路径改为 `issues.py`
5. `CLAUDE.md` / `README.md`：命令示例和路径引用
6. `AGENTS.md`：issues 路径引用（buglist|todolist → open/|closed/）
7. `sdflow-init/assets/snippets/claude-section.md`：同上（推给消费仓的模版）
8. `openspec/CONTEXT.md`：领域术语更新（三脚本→单脚本、目录结构、终态词表）
9. `openspec/specs/spec-workflow/spec.md`：补 MODIFIED delta（batch/sweep/buglist.py 断言）
10. `openspec/specs/determinism-guards/spec.md`：补 MODIFIED/REMOVED delta
11. `openspec/specs/recorder-root-resolution/spec.md`：补 MODIFIED delta（三薄入口→单入口）
12. `.github/workflows/windows-recorder-smoke.yml`：更新硬编码测试路径

- [x] sdflow-issues/SKILL.md 更新完成（数据模型 + 命令文档 + 路由/触发逻辑）
- [x] sdflow-done/SKILL.md §2.1 重写完成（sweep → scan --source-change + hand-off 列 ID）
- [x] hack/tests/ 中 TODO_SCRIPT 路径更新
- [x] CLAUDE.md / README.md 命令示例更新
- [x] AGENTS.md / claude-section.md / CONTEXT.md 路径引用更新
- [x] spec-workflow/determinism-guards/recorder-root-resolution 三个 spec 的 delta 补完
- [x] windows-recorder-smoke.yml 测试路径更新
- [x] 全仓 `pytest` 绿（无红测）

### Task 5: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落
`impl-reports/task5-verify.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
