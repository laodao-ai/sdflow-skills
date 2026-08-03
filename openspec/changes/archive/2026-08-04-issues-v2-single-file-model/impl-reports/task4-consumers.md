# Task 4 实现报告：消费方全部更新 + 全仓 pytest 绿

## 结果

`/usr/bin/python3 -m pytest --ignore=.claude -q` → **2471 passed, 10 skipped (Windows-only) in 285.55s**
（exit code 0）。修复前基线（Task 3 报告记录）为 `2458 passed, 13 failed, 10 skipped`；13 个失败全部
来自 `hack/tests/test_harden_sdflow_spec_followup_closure.py`，本票修复后新增 13 个 passed（2471-2458=13），
skip 数不变，与预期完全吻合。

## 逐项完成情况

1. **`hack/tests/test_harden_sdflow_spec_followup_closure.py`**（红测根因，最优先修）——
   `TODO_SCRIPT` 改指向 `issues_v2.py`；`_todos()` 加 `--pool todo --all --json`（v2 默认只扫
   `open/`，T132/T239/T232 等历史项已 DONE/WONTDO 落在 `closed/`，必须 `--all` 才能查到）；
   `_block()` 重写为直接读 v2 文件（`open/` 或 `closed/` 下的 `{ID}.md`）frontmatter 之后的 body，
   不再依赖已删除的 `<!-- sdflow-issue-block:start/end -->` marker 与 `todolist/2026-07-todolist.md`
   总览表。16 个用例全部通过（原 13 红 + 3 绿）。

2. **`sdflow-issues/SKILL.md`**——数据模型（12 字段 frontmatter schema、`open/`/`closed/` 目录、
   两状态词表 bug={OPEN,PROPOSED,FIXED,WONTFIX}/todo={OPEN,PROPOSED,DONE,WONTDO}）+ 命令文档
   （`issues_v2.py` 单入口 CLI：add/set-status/scan/reindex/next-id/migrate）+ 路由/触发逻辑
   （单脚本 `--pool` 参数区分两池，非三脚本路由）全面重写。四条通则区块用
   `python3 hack/sync_principles.py --check` 核验未破坏（22 个投放面一致）。

3. **`sdflow-done/SKILL.md` §2.1**——sweep（scan 两池 → 逐项 triage → batch add → reindex 写操作）
   改写为只读查询 `issues_v2.py scan --json --source-change {change} --status OPEN --status PROPOSED`；
   hand-off 由"引批次号"改为"直接列 ID"；同步更新第二步 hand-off 模板措辞与"设计原则"section 的对应
   bullet。§2.1 之外一处引用（"issues sweep 同位不同性"对比句）同步改"issues scan"。

4. **`CLAUDE.md`/`README.md`**——pytest 命令示例（`test_buglist.py` → `test_issues_v2.py`）；
   `README.md`「Recorder 存储契约」段落改写为单文件模型描述（`O_CREAT|O_EXCL` 并发保护、无仓级锁，
   注明 ADR-0025 的 overlay/snapshot-lock 架构本身已被替代，零依赖 YAML 原则仍沿用）。

5. **`AGENTS.md`/`sdflow-init/assets/snippets/claude-section.md`**——`openspec/issues/buglist|todolist/`
   路径引用改 `openspec/issues/open|closed/`（三处相同措辞，含 CLAUDE.md 一处，共四处同步）。

6. **`openspec/CONTEXT.md`**——「批次 (Batch)」「三维度分家」标注退役、重写为「两维度分家(源/status)」；
   「终态集」「reindex」术语更新到 v2 目录/命令；新增退役说明段落覆盖 ADR-0025/0027 相关的 11 条
   detailed 术语条目（共享 frontmatter envelope / recorder durability boundary / canonical Unicode
   string / canonical recorder ID / canonical recorder render / 锁 owner-participant / display title /
   marker-framed prose block / mode-structure invariant / provenance-backed idempotent recovery /
   单一源共享 core）——标注「留档备史」而非删除（两份 ADR 仍是已 Accepted 的历史决策记录）；
   Flagged ambiguities 新增两条（core.py/POOL_SPEC 进一步退役、分诊/sweep 退役）。

7. **三个主 spec 的 delta**（新建在本 change 的 `specs/` 下，遵 OpenSpec MODIFIED/REMOVED delta 惯例，
   `openspec validate issues-v2-single-file-model --strict` 通过）：
   - `spec-workflow`：MODIFIED 4 个 Requirement（阶段三 defer 路径措辞、债务池目录+两维度、
     skill 命名一致性的 sibling 脚本 Scenario、outside-voice tension 的 defer 措辞）+
     REMOVED 1 个 Requirement（批次注册表与 reindex 被动同步状态，含 Reason/Migration）。
   - `determinism-guards`：REMOVED 3 个 Requirement（recorder 镜像 helper AST 守/`batches.md`
     grammar lint/确定性守卫不越权），均因 `core.py`/`POOL_SPEC`/`batches.md` 已不存在而失去校验
     对象；本 capability 内与 issues 无关的 `config.yaml` 结构 lint Requirement 未动。
   - `recorder-root-resolution`：MODIFIED 4 个 Requirement（三薄入口→单入口 issues_v2.py，
     并移除随仓级锁一并消解的跨进程根分裂已知缺口 B15 及其 `xfail` Scenario——已核实
     `test_repo_root_identity_issues.py` 确无该 xfail 用例，Task 3 已删除）；1 个通用 pytest
     基础设施 Requirement 未动。

8. **`.github/workflows/windows-recorder-smoke.yml`**——第 86 行引用的
   `test_task5_delivery_contract.py::test_sweep_cli_executes_all_four_utf8_subprocess_sites`
   已被 Task 3 删除，替换为直接调用 `issues_v2.py`（add → set-status → reindex）在 GBK 编码下的
   smoke（本机 macOS 实跑验证三条命令成功、覆盖 `issues_v2.py` 全部 7 个 `subprocess.run` 调用点中的
   6 个：`repo_root` 的 `git rev-parse --show-toplevel`、`detect_change` 的 `git rev-parse
   --abbrev-ref HEAD` 回退分支、`_is_git_repo`、`git add`、`git ls-files`、`git mv`）。

## 已知残余 / 未在本票范围内的事项（如实登记，非本票缺陷）

- **`design.md` 消费方清单提到「reindex 骤降守卫移植到 v2」，但核实后 v2 `issues_v2.py::cmd_reindex`
  未实现等价的「总项数只增不减」守卫**（v1 该守卫在 `issues-scripts-shared-core` 能力的
  「reindex 总项数只增不减守卫」Requirement 中）。已核对本 change 自己的 `issues-v2-storage`
  能力 delta（STOR-03）对此保持沉默——不在 Task 4 的 R-ID 范围（STOR-01/05/06/07）内，且新增脚本
  行为超出「消费方更新」票的授权范围（会违反④「不加宽」）。determinism-guards delta 如实标注
  「无等价机制需要移植」而非虚构一个不存在的守卫。**留给人工判断**：是否需要另开票在
  `issues_v2.py` 补一个轻量骤降守卫（v2 单文件模型的失败模式已收窄为"单个文件损坏时静默 WARN 跳过"，
  风险面比 v1 小但未消除）。
- `openspec/INDEX.md`、三份主 spec（`openspec/specs/{spec-workflow,determinism-guards,
  recorder-root-resolution}/spec.md`）本身、以及 `docs/` 目录下的历史分析文档未改——按惯例这些由
  `sdflow-done` 归档步（`openspec archive` CLI）在本 change 归档时同步，不是 Task 4（consumer-update
  阶段）的职责；`docs/` 系列文档也不在 task4-brief 的 12 个消费方名单内。
- `openspec/adr/0010`、`openspec/adr/0027` 与 `openspec/issues/{open,closed}/*.md` 中提及
  buglist.py/todolist.py 的内容均属历史记录（ADR 不可改写、issue body 是对历史事件的如实记载），
  未动，符合预期。

## 验证记录

- `pytest hack/tests/test_harden_sdflow_spec_followup_closure.py -q` → 16 passed
- `python3 hack/sync_principles.py --check` → ✅ 22 个投放面全部与真相源一致
- `openspec validate issues-v2-single-file-model --strict` → valid
- 本机手跑 smoke 命令（add → set-status FIXED → reindex，`issues_v2.py`）验证 workflow yml 里新增的
  三条命令语法与语义正确
- `pytest --ignore=.claude -q`（全仓）→ 2471 passed, 10 skipped, 0 failed
