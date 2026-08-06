# Task 6 — 实现验证收尾（聚合套件 + Success Metrics + issues 池 + 全局窗口前置）

## 定位声明（本票的诚实边界）

本票跑在 `sdflow-code-review` 及其自动修复循环**之前**——它回答的是「Task 1–5 全部功能票实现完毕
这一刻，聚合套件是否通过」，**不声称**「最终代码通过聚合套件」。`sdflow-done` 的 verify 仍是最终门。

## 1. 聚合套件发现契约

**命令来源判定**：`openspec/config.yaml` 顶层无 `test-suites` 键（已实测：`grep -n "test-suites"
openspec/config.yaml` 退出码 1，无匹配）。依仓内既有约定判定：

- `CLAUDE.md` §「运行测试」明文：「测试各 skill **自包含**在 `<skill>/tests/`……用 pytest 直接跑：
  `pytest`（发现并运行全部 test_*.py）」——**本仓不做 unit/integration/e2e 分层组织**，只有一条
  聚合命令。
- `.github/workflows/mechanical-gates.yml` 的唯一测试步骤名为「Full test suite」，命令即
  `python -m pytest -q -rs`，同样不分层。
- 已实测确认仓内**不存在**按 `integration`/`e2e` 命名的独立测试目录或套件：
  `find . -type d \( -iname "*integration*" -o -iname "*e2e*" \)` 唯一命中是
  `openspec/changes/archive/2026-07-10-matt-workflow-integration`（一个 change 目录名，非测试层）。

**结论**：本仓的聚合套件 = 单层 `pytest` 全量发现；integration / e2e 记「未覆盖（本仓无此层）」，
判定依据同上。本机环境事实：裸 `pytest` 不存在，须用 `/usr/bin/python3 -m pytest`（CLAUDE.md 已载明）。

## 2. 三层证据 schema

| 层 | 命令原文 | 退出码 | 测试时 git rev-parse HEAD |
|---|---|---|---|
| unit（本仓唯一聚合套件） | `/usr/bin/python3 -m pytest -q -rs` | 0 | `458d44d338843f2b7a94b4501de96335990a7f63` |
| integration | — | 未覆盖 | 判定依据：仓内无按 integration 命名的独立套件/目录（§1），CLAUDE.md 与 CI 均只定义单一聚合 pytest 命令 |
| e2e | — | 未覆盖 | 判定依据：仓内无按 e2e 命名的独立套件/目录（§1），同上 |

**unit 层原始输出（尾部摘要）**：

```
2466 passed, 10 skipped in 298.87s (0:04:58)
```

10 条 skip 全部为已知环境隔离项（非本 change 引入、非回归），逐条：
- `test_outside_voice.py` ×2：真机模型探针，需 `SDFLOW_OV_REAL_MODEL_SMOKE=1` 且本机装 `claude`
- `test_outside_voice_child_lifecycle.py` ×1：15 次高频混合信号风暴复现率环境敏感，docstring 已声明
  「MUST NOT 因为常 skip 就删除」
- `test_outside_voice_utf8.py` ×1：M3 磁盘写满场景，环境未能建立前提
- `test_task2_windows_local_fs_smoke.py` ×6：要求真实 Windows 本地磁盘（本机 macOS，天然不适用）

**四类失败分诊**：本次退出码为 0，无失败，不适用分诊。

**所有判「通过」的行锚同一 SHA**：`458d44d338843f2b7a94b4501de96335990a7f63`（unit 层运行前后 `git
rev-parse HEAD` 一致；integration/e2e 未覆盖不产生锚）。

## 3. Success Metrics 静态核验

### 3.1 `grep -rn "gstack" sdflow-code-review/SKILL.md` 严格归零

```
$ grep -rn "gstack" sdflow-code-review/SKILL.md
(无输出)
$ echo $?
1
```

Exit 1（grep 无匹配的标准退出码）= 严格归零，DOC-1 口径（正文零残留，不留「历史注记」豁免）满足。

### 3.2 `openspec validate --strict` 绿

裸 `openspec validate --strict`（无子命令）返回「Nothing to validate」提示可选项，非本仓惯用调用形式；
改用等价的显式子命令，全部绿：

```
$ openspec validate absorb-gstack-review --strict
Change 'absorb-gstack-review' is valid

$ openspec validate --changes --strict
- Validating...
✓ change/absorb-gstack-review
Totals: 1 passed, 0 failed (1 items)

$ openspec validate --specs --strict
- Validating...
✓ spec/architecture-design
✓ spec/batch-triage
✓ spec/determinism-guards
✓ spec/devenv-provisioning
✓ spec/encoding-hygiene
✓ spec/host-adaptive-execution
✓ spec/hr-tg-intersection-check
✓ spec/impl-orchestration
✓ spec/issues-scripts-shared-core
✓ spec/lens-metric-emit
✓ spec/maintain-scan
✓ spec/openspec-170-followup
✓ spec/outside-voice-background-jobs
✓ spec/outside-voice-exec-integrity
✓ spec/outside-voice-reuse-guard
✓ spec/recorder-root-resolution
✓ spec/roadmap-planning
✓ spec/roadmap-review-reconcile
✓ spec/spec-authoring
✓ spec/spec-workflow
✓ spec/workflow-metrics
✓ spec/workflow-retro
✓ spec/yq-yaml-operations
Totals: 23 passed, 0 failed (23 items)
```

「gstack 不在场可跑通」Scenario 以 §3.1 grep 归零静态证成（SKILL 无任何 gstack 调用路径 = 无运行时
依赖），未另造缺席环境（spec-review-amendment 已明确此证明方式）。

## 4. issues 池记三条 todo

用开发 checkout 相对路径脚本 `python3 sdflow-issues/scripts/issues_v2.py`（非 `~/.claude/skills/`
symlink），显式传 `source_change: "absorb-gstack-review"`：

| ID | 池 | module | 摘要 |
|---|---|---|---|
| T267 | todo | `openspec/workflow/spec-checklists (domains)` | 建立 python.md checklist domain 承接 Async/Sync 混用等 Python 专属检查点（gstack Pass-2 剩余条目，本 change 因归属 domain 不存在而 defer） |
| T268 | todo | `sdflow-spec-review`（autoplan 依赖）+ `outside_voice_guard.py` | 处置 spec-review 侧 autoplan 姊妹依赖与 `outside_voice_guard.py`（本 change 只吸收 code-review 一侧，spec-review 侧仍留第三方 gstack/autoplan 运行时依赖，未定优先级） |
| T269 | todo | `openspec/workflow/lens-metric-contract.md`, `openspec/workflow/WORKFLOW-GUIDE.md`（仓根） | 清理仓根 `openspec/workflow/` 下孤儿副本（非 pin、功能死件，权威源已迁至 `sdflow-init/assets/workflow/`，是 grep gstack 时的假阳来源） |

三条命令均返回 `{"id": "T26x", ..., "source_change": "absorb-gstack-review"}`，已执行
`python3 sdflow-issues/scripts/issues_v2.py reindex`（退出码 0，`open 72 项 / closed 221 项`）。

## 5. 开发 checkout 全局窗口（开窗前置）

`bash setup.sh` 会把 `~/.sdflow/workflow`、`~/.claude/skills/*`、`~/.codex/skills/*` 全部翻向本开发
树，属机器级影响的时间盒操作。

**开窗前** `readlink ~/.sdflow/workflow`：
```
/Users/cheneyzhao/.skills/sdflow-skills/sdflow-init/assets/workflow
```
（指向运行 checkout）

**执行** `bash setup.sh`：退出码 0；关键输出片段：
```
sdflow-skills v1.0.0-133-g458d44d-dirty ready → /Users/cheneyzhao/.claude/skills /Users/cheneyzhao/.codex/skills
  ✓ workflow @ /Users/cheneyzhao/.sdflow — 接管：/Users/cheneyzhao/.skills/sdflow-skills/sdflow-init/assets/workflow → /Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-init/assets/workflow
  ...（39 个 skill symlink + 3 个 agent 定义 + 7 个 hack 文件全部接管）
[sync_principles] ✅ 20 个投放面全部与真相源一致
[gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致
[tier-resolution-parity] ✅ 4 处宿主/档位解析核心段逐字节一致
[encoding-hygiene] ✅ 所有入口脚本均满足编码前导契约
```
`sync_principles.py --check` 门禁绿（本 change 未改通则，符合预期）。

**开窗后** `readlink ~/.sdflow/workflow`：
```
/Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-init/assets/workflow
```
确认已指向本开发树。

**还原方式**（合并后执行，供收尾提示引用）：在运行 checkout `~/.skills/sdflow-skills` 重跑
`bash setup.sh`，把全局指针（`~/.sdflow/workflow`、`~/.claude/skills/*`、`~/.codex/skills/*`）
翻回运行 checkout。`~/.sdflow/hack/` 下文件是拷贝非软链，同样靠这次重跑刷新，仅改软链无法还原。

`setup.sh` 运行后 `git status --short` 核验：仅新增本票产物（三条 issue 文件 + INDEX.md 更新 +
本报告本身），未触碰仓内任何受版本控制的 skill 源文件——全局窗口的影响面严格限定在
`~/.sdflow/`、`~/.claude/skills/`、`~/.codex/skills/`、`~/.claude/agents/`。

## 6. dogfood 分工声明（诚实边界）

`tasks.md` 6.4 要求本 change 自身跑一次 `/sdflow-code-review` 并核验产出锚（`mode="subagent"` 锚 /
`scope-audit` 折叠出的 `lens="broad"` 行 / `anchor_lint` 通过）。

**该实跑观测不由本票执行**——本票是无法再派子代理的实现子代理，跑不了多镜 fan-out 评审。该观测由
本票之后 ship 链序的 code-review 步天然承担（本节 §5 开窗后，它跑的就是本 change 新版
`sdflow-code-review/SKILL.md` 的 Step1 自持 scope 审计）。

**本票只完成**：① 开窗前置（§5，`~/.sdflow/workflow` 已确认指向本开发树，`/sdflow-code-review`
下一次运行会解析到新 SKILL）；② 待核锚清单落盘（见下）。**本票 MUST NOT 声称已完成实跑观测**——
以下三项留待 ship 链序 code-review 步的报告核验：

- [ ] `mode="subagent"` 锚（Step1 scope 审计确实由 fresh 子代理执行，非主 session 自查降级）
- [ ] `scope-audit` 折叠出的 `lens="broad"` 行（lens-metric-fold 契约块新 raw 名正确折叠进 roster）
- [ ] `anchor_lint` 通过（mirrors 合法集含 `broad`、dead-fanout 计数集不受污染）

## 7. Concerns

无。全部 8 条验收标准均已落实且证据齐全；无回归、无环境故障、无需上抛编排层的事项。
