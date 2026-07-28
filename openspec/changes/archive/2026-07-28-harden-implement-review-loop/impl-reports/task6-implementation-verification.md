# Task 6：实现验证（收尾票）—— 实现期聚合回归证据

**R-ID:** all（覆盖本 change 全部需求的聚合验证；Spec 轴据此核验而非逐条溯源）
**定位重申**：本票是**实现期**聚合回归门，不声称"最终代码通过聚合套件"；不是 verify、不替代 verify、不前移 verify。

---

## 1. 聚合套件命令判定（第 ① 条：config 缺失 → 依仓内既有约定判定）

**已核实**：`openspec/config.yaml` 无 `test-suites` 段（读过全文，仅有 `schema`/`context`/`rules` 三段）。

**判定依据**（读过的文件，未解析 Makefile/package.json）：

- 仓根无 `Makefile`/`package.json`/`Rakefile`（`ls` 确认不存在）——本仓不是靠构建文件 target 驱动测试的项目。
- `CLAUDE.md`「运行测试」节明文：测试各 skill 自包含在 `<skill>/tests/`，仓根另有两个根级 pytest 文件（`conftest.py` + `pytest.ini`，只承载 cwd 副作用断言），命令为 `pytest`（全量）或指定路径的子集。
- `.github/workflows/mechanical-gates.yml` 定义唯一测试步骤 **"Full test suite"** = `python -m pytest -q -rs`，覆盖全仓（`sdflow-*/tests/`、`hack/tests/`）。该文件还跑另外两道机械门（`check_async_branch_parity.py`、`sync_principles.py --check`），但那两道是本仓一致性门、不是"测试层"，本票不重复计入证据 schema。
- `.github/workflows/windows-recorder-smoke.yml` 是**按路径触发**的窄场景冒烟（仅 `sdflow-issues/tests/test_task2_windows_local_fs_smoke.py`，验 Windows 本地磁盘写入行为），只在 `windows-latest` runner 有效，本机（macOS）无法运行、也不构成独立的"集成层"或"e2e 层"入口。
- 全仓 `find` 未发现任何 `*e2e*`/`*integration*` 命名的独立可调用测试入口或脚本（命中的路径均为 `.git/objects` 哈希巧合或历史归档文档，非测试命令）。
- 本仓从未对**自身**跑过 `sdflow-devenv`（无 `.devenv.json` / `testing-strategy.md`）——三层测试策略框架是该 skill 交付给*其他*项目的产物，本仓自己没有沿用它来定义分层。

**判定结论**：本仓测试基础设施为**扁平单层**——CI 与项目约定都只暴露一条命令 `python -m pytest -q -rs`（对应 unit 层）。本仓无独立可调用的"集成层"/"e2e 层"命令，按发现契约第③条「仓内确无某层时记未覆盖 + 依据，MUST NOT fail-closed 罢工」处置：

- **unit**：有对应命令，真跑（见下）。
- **integration**：未覆盖——本仓无 `test-suites.integration` 配置、无 Makefile/package.json target、CI 只有一条覆盖全仓的 pytest 步骤，未拆分出独立的"集成层"命令。（旁注：pytest 套件内部混有少量真实子进程/OS 级行为用例，例如 `sdflow-init/tests/test_outside_voice_child_lifecycle.py` 用真实 `timeout`/`gtimeout` 验证进程组回收、`hack/tests/test_setup*.py` 类用例真实执行 `mkdir`/`ln`/`rm`——这些用例随 unit 行的同一次调用一并跑过，但本仓的既有约定从未把它们组织成第二条独立命令，故不另开一行、不重复计入。）
- **e2e**：未覆盖——本仓是 skill 指令集合（Markdown + Python/Bash 脚本），无部署中的应用/服务/UI 可供端到端驱动。CI 中唯一贴近"e2e"语义的 `windows-recorder-smoke.yml` 范围极窄（单一场景、按路径触发、仅 Windows），非通用 e2e 层，本机也无法运行。

## 2. 证据 schema（真跑一遍，退出码 + HEAD）

| 层 | 命令原文 | 退出码 | 测试时 `git rev-parse HEAD` |
|---|---|---|---|
| unit | `/usr/bin/python3 -m pytest -q -rs` | 0 | `f22bc100cc846fdffff138b66fa55bb739c096ff` |
| integration | — | 未覆盖 | 本仓无独立可调用的集成层命令（见上「判定依据」） |
| e2e | — | 未覆盖 | 本仓无 e2e 层（无部署应用/UI 可驱动，见上「判定依据」） |

**unit 层完整输出摘要**：

```
$ /usr/bin/python3 -m pytest -q -rs
2922 passed, 11 skipped, 3 xfailed in 289.52s (0:04:49)
```

11 条 skip 全部带机读理由（非静默降级）：2 条真机模型探针需 `SDFLOW_OV_REAL_MODEL_SMOKE=1`、1 条高频信号风暴复现率环境敏感（`test_outside_voice_child_lifecycle.py`，文档明确「MUST NOT 因常 skip 就删除」）、1 条磁盘写满场景本环境撞见 shell 原生诊断先于目标代码路径、7 条 Windows 本地磁盘冒烟需真实 Windows 环境（本机 macOS 恒 skip，属预期，`test_task2_windows_local_fs_smoke.py` docstring 明文「Non-Windows hosts skip this module and MUST NOT cite the skip as Windows evidence」）。3 条 xfail 均为已知预期失败（未逐条列出，非本票范围）。

## 3. 失败分诊

**无需分诊**——unit 层退出码为 0，未产生任何回归/既有红测/flaky/环境故障需处置。integration/e2e 两行均为「未覆盖」而非「运行失败」，不落入四类失败处置流程（发现契约③明文「缺层不罢工」）。

**Standards 轴核验范围**（本票自身双轴审的核验面，若走标准 implementer+双轴审+fix 循环）：本次未触发任何修复，因此「修复方式未靠加 skip / 改测试配置 / 删除或弱化断言蒙混过关」这条核验**无适用对象**——没有 fix 轮，没有东西可以被蒙混。

## 4. `openspec validate` 输出

```
$ openspec validate harden-implement-review-loop --strict --type change
Change 'harden-implement-review-loop' is valid
```

## 5. 两份 delta 与实际改动逐条对码

逐条核对 `specs/impl-orchestration/spec.md` 与 `specs/spec-workflow/spec.md` 的每条 ADDED/MODIFIED Requirement 与实现侧文件。

### 5.1 `impl-orchestration` delta

| Requirement | 实现侧核验 | 结论 |
|---|---|---|
| ADDED「sdflow-implement 档位解析与声明」 | `sdflow-implement/SKILL.md:169` 起「第零步」四步（清脏 unset 六变量→`[ -x resolve-models.sh]` 预检→捕获退出码 eval→eval 后校验），失败表 1–8 行逐类覆盖（resolver 不存在/不可执行/非零退出/输出无法 eval/host 非法/host 空值/tier 缺失/host=unknown），Codex 宿主能力探针段（:180-192）与硬停不缩 roster（:194 起），implementer/双轴审/fix 派发均引用 `$SDFLOW_TIER_MID`（:462, :586, :639），parity 守卫 `hack/tests/test_tier_resolution_parity.py` 存在且含四站点逐字节比对 + 16 条变异/结构测试 | ✅ 逐条对得上 |
| MODIFIED「执行模式串行工作 frontier 并以文件交接」（测试范围分层） | `sdflow-implement/SKILL.md:490-493`：单元测试 + 本票声明的 e2e 场景 + `Blocked-by` 链上集成测试，MUST NOT 跑与本票无依赖关系的集成/e2e；`:409` 附近"本票声明的 e2e 场景"由验收标准 e2e 标注条目界定 | ✅ 对得上 |
| MODIFIED「每 ticket 双轴审加修复环」（`review-loop-breaker`） | `sdflow-implement/SKILL.md:643-644` 起：独立定义、MUST NOT 引用 `T10-choice`、身份键"同文件+规范化问题指纹"（行号只定位）、三级处置收敛互斥终态（自动选/strong 复核/defer 且复核成立后二选一不可回到原循环） | ✅ 对得上 |
| MODIFIED「出 ticket 模式产出 tracer-bullet ticket」（收尾票 + 聚合契约 + 文件名 + gate 第四道） | `sdflow-implement/SKILL.md:285` 起「强制实现验证收尾 ticket」小节、模板 `:400`（`R-ID: all`、`Blocked-by` 全部功能票）；聚合发现契约（命令优先级/真跑判断/缺层不罢工/证据 schema/四类分诊）与 delta 逐句对应；计划文件名分轨 + 共享 resolver + 双存在 fail-closed + 在途改名 grandfather 见 `sdflow-ship/scripts/ship_gate.py:1229-1310`（`PLAN_FILENAMES`/`resolve_plan_path`/`PlanNameConflict`）与 `sdflow-implement/scripts/impl_route.py:48-61`（同源 import `resolve_plan_path`/`PLAN_FILENAMES`，非手抄）；gate 第四道校验见 `ship_gate.py:1403-1467`（当且仅当文件名为 `tickets.md` 时校验收尾票存在且 `Blocked-by` 覆盖全部功能票，`superpowers-plan.md` 跳过输出 grandfather 提示）；仲裁审计落点 `impl-reports/planning-decisions.md`（`sdflow-implement/SKILL.md:252`, `:427`） | ✅ 对得上 |

### 5.2 `spec-workflow` delta

| Requirement | 实现侧核验 | 结论 |
|---|---|---|
| MODIFIED「阶段三过设计门后连续自动跑到 merge」（`T10-choice` 命名 + 计划文件名分轨） | `sdflow-ship/SKILL.md:164` 起 `T10-choice` 三级协议定义（"T10"保留历史别名）；`sdflow-ship/SKILL.md:170` 路由链序含 `sdflow-implement` 字面派发串；计划文件名分轨/共享 resolver 描述与 `ship_gate.py` 实现一致 | ✅ 对得上 |
| MODIFIED「outside-voice tension 不静默采纳」 | 该 Requirement 本身不属本 change 直接改动范围（`T10-choice` 换名前已用统一"T10"标签，本 change 只做换名同步）——`openspec/specs/spec-workflow/spec.md:638` 已在 Task 2 提交（`98cc407`）中原地同步为 `T10-choice`，与本 change 主张的"仅换名不改语义"一致 | ✅ 对得上（换名同步，语义未变） |
| MODIFIED「模型档位映射（model-tiers）」 | `sdflow-init/assets/workflow/model-tiers.md` 不逐 skill 枚举名字（泛化"编排 skill 一律以一句引用"），故不存在"漏列 sdflow-implement"的字面缺口；`sdflow-ship/SKILL.md:165` 的 canonical 说明处已显式补 `implement`（"经各被链序调度的子 skill（spec-review/code-review/done/implement）"）；`sdflow-init/tests/test_codex_subagent_authorization.py:56` 断言含 `sdflow-implement` | ✅ 对得上 |

### 5.3 已知的有意例外（核对时按此判定、不计缺口）

- **本 change 自己的在途 plan 叫 `superpowers-plan.md`（旧名）**——按 design Migration Plan grandfather 保留；`ls openspec/changes/harden-implement-review-loop/` 确认该文件仍在，未被重命名，`git log --diff-filter=A -- .../superpowers-plan.md` 判据窗口起点未受扰动。`ship_gate` 对它跳过第四道收尾票校验、输出 grandfather 提示——已在 `ship_gate.py:1464-1467` 实测到（Task 5 双轴审已核验，本票不重跑）。
- **`openspec/specs/**` 与 delta 的差异属 delta-at-archive 纪律**——Task 2 提交（`98cc407`）主动同步了 `openspec/specs/spec-workflow/spec.md`（`:83` T10-choice 段、`:638` tension 段共两处）**与** `openspec/specs/impl-orchestration/spec.md`（`:27` 出票模式段）——共 **3 处**，比 task6-brief 转述的"两处"多 1 处（`impl-orchestration/spec.md:27`）；已用 `git log -p --follow` 核实该行确由同一提交改写，非笔误也非缺口，属"design scope-check 表 15 处 Group A 落点"里本就登记的第 9 项（`openspec/specs/impl-orchestration/spec.md:27`）。三处均已同步，无遗漏。
- **design scope-check 表未列的文档**（`docs/workflow-map.html`、`docs/workflow-console.html`、`docs/workflow-skills/{superpowers-writing-plans,superpowers-subagent-dev}.md`、`openspec/INDEX.md`）——proposal Impact 段的早期文件清单被 design「T10 scope-check（统一计数口径）」表明文取代（"此前 proposal『4 处』/design『6 个』/……五种口径互不一致，以本表为唯一口径"）。已逐个 grep 核实这几个文件均**不含**字面"T10"或需要因本 change 而改的内容（`docs/workflow-console.html`/`docs/workflow-map.html` 里仅存的"T10"字样是分析类图表标注，CONTEXT.md 已登记"T10 保留为历史别名，分析类文档无需扫改"）；`openspec/INDEX.md` 的 `impl-orchestration` 条目摘要已含 `tickets.md`/`adr-0033` 措辞（间接确认同步，无需逐字含"T10"）。判定：**非缺口，是 design 对 proposal 早期过量声明的收敛**，本票不据此判 gap。

## 6. Success Metrics 证据落点汇总

| Metric | 状态 | 证据 |
|---|---|---|
| 1（跨机队正确性） | **已验证** | `impl-reports/task1-tier-resolution.md`「Success Metric 1 证据」节：真实 Codex 宿主进程内 `eval "$(resolve-models.sh)"`，`HOST=codex STRONG=gpt-5.6-sol MID=gpt-5.6-terra LIGHT=gpt-5.6-luna`，零命中 Claude 机队专名；未跑完整 `tickets-plan`（brief 二选一，避免触发本 change 自身窗口锚风险），该缺口已在原报告如实记录，非本票需补 |
| 2（parity 守卫非恒真锚） | **已验证** | `impl-reports/task1-tier-resolution.md`「变异实测」节：4 文件 × 4 子步 = 16 次删除全部必红，两种恒真成因（门被别的断言满足 / 无用例走到那行）均排除；本票额外核实 `hack/tests/test_tier_resolution_parity.py` 随本次全量 pytest 一并跑过（含在 2922 passed 内） |
| 3（收尾票产生真实执行证据 + gate 对缺收尾票的 plan 必判非 0） | **前半：本票（见上第 2 节 unit 行）；后半：** `sdflow-ship/tests/test_gate_closing_ticket.py`（Task 5 新增，10 用例；`test_missing_closing_ticket_is_unknown` / `test_closing_ticket_missing_functional_dependency_is_unknown` 精确对应本 Metric 的两种坏形态判 `UNKNOWN`），随本次全量 pytest 一并跑过 | 已验证 |<br>〔双轴审 Spec 轴订正〕首版此处误引 `test_gate_impl_progress.py`——该文件只是同步了共享 fixture（补一张合法收尾票，避免其它用例被第四道校验拦下），**不是**本 Metric 的证据来源；底层论断（gate 对缺收尾票的 plan 必判非 0）经独立复跑成立，仅证据锚指错文件。
| 4（改名无残留） | **已验证** | `impl-reports/task4-filename-sync.md`「§7.3 全仓 grep 归因表」：非 archive/非 issues 路径下 `superpowers-plan` 剩余命中逐条归因为① superpowers 轨合法引用或②历史记录引用，tickets 轨零命中；本票复核该归因表口径与本次实测（`superpowers-plan.md` 未被本票触碰）一致 |

**四条 Metric 全部有证据落点，无「未验证」项。**

## 7. 与在途 todo 的关系（不处理，仅核对不误报）

- **T257**（`plan_was_renamed`/`plan_first_sha` 重复一次 git 调用）：性能优化类，Task 3 双轴审已 defer，非本 change 引入的回归，未影响本票的证据链，未处理（属既定 defer）。
- **T258**（review-package 逐字快照体积/污染）：编排层 defer，产物契约层面决策，未影响本票测试通过性，未处理（属既定 defer）。

## 8. 结论

- 本仓聚合套件的"单元层"证据 = 全量 `pytest`，2922 passed / 0 failed，SHA `f22bc100cc846fdffff138b66fa55bb739c096ff`。
- 集成/e2e 两层如实记「未覆盖」+ 判定依据，未 fail-closed 罢工。
- `openspec validate --strict` 通过。
- 两份 delta 与实现逐条核对完毕，无发现漂移；三处已知的有意例外（在途 plan 旧名、delta-at-archive 边界、design 对 proposal 早期声明的收敛）均按设计口径判定，未计为缺口。
- 四条 Success Metric 均有证据落点，无未验证项。

**本票不产生 commit（工作树干净、无产品代码改动）**——按 Global Constraints「证据落 report file，不依赖 commit」处置，`checkpoint-commit.sh` 在干净树上直接成功退出属预期行为，本票不主动调用它（无新增/改动文件需要提交）。
