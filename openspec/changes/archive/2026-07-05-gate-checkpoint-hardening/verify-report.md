# Verify Report — gate-checkpoint-hardening

- 日期：2026-07-05
- Change：gate-checkpoint-hardening
- 验证方式：Do-Not-Trust 冷核 —— 逐条对码/对文案锚点，不信复选框与既有措辞

## 结论：PASS
<!-- ship-gate: verify=PASS -->

3 条 ADDED + 1 条 MODIFIED 需求全部有可机验证据锚点落地；全套件零回归（`pytest` 375 passed，`sdflow-ship/tests/` 109 passed），`openspec validate gate-checkpoint-hardening` 通过。核心功能无缺口，仅 2 处属预期 defer/post-archive（非缺陷）。

## 逐需求核对表

| 需求 / 任务 | 代码出处（可机验锚点） | 状态 |
|---|---|---|
| **T36 格式源单一化**：TAG_RE 带 canonical-shape 头注释 + 权威声明 | `ship_gate.py:300-308`（头注释 + `TAG_RE`）；`workflow.md` 保留一处格式串标"权威见 TAG_RE" | ✅ |
| **CR-3 slug 非契约**：`<slug>` 为建议性、TAG_RE 不校验 | `ship_gate.py:302` 注释「`<slug>` 是建议性约定…TAG_RE 不校验其存在或形状」；`TAG_RE` 正则实到 `task(\d+)-` 前缀止 | ✅ |
| **SR-4 防漂移机械钩子**：TAG_RE 旁 checklist 注释 | `ship_gate.py:307`「SR-4 checklist：改此正则前先 grep workflow.md 里的格式串样例是否需要同步更新」 | ✅ |
| **SR-5 断言改写**：SKILL 不含完整格式串、workflow.md 含源 | `test_workflow_authority.py:23-35`（`test_skill_producer_arg_namespaced`：断言 `<change>:task<N>-<slug> not in` SKILL、`in` workflow.md，两侧均含 `TAG_RE`）—— PASS | ✅ |
| **T36 SKILL 派发句引用式**：无完整格式串复述 | `sdflow-ship/SKILL.md:29`「按 workflow.md §二/步骤6 的格式规则（权威见 `ship_gate.py` `TAG_RE`〔T36〕）」，无 `<change>:task<N>-<slug>` 串 | ✅ |
| **T43/SR-6 锚模板独占裸行**：spec-review 锚去反引号 | `sdflow-spec-review/SKILL.md:102` `<!-- ship-gate: design-approved -->` 独占裸行、无反引号无尾注 | ✅ |
| **SR-10 code-review pass/blocked 各配各注（未合并）** | `sdflow-code-review/SKILL.md:149-152`：149「（pass：建议进 /sdflow-done）」→150 pass 锚；151「（blocked：存在未解 blocker）」→152 blocked 锚，语义分列未合并 | ✅ |
| **SR-6 测试逐行 strip==anchor** | `test_anchor_contract.py:20-30`（`line.strip()==a` + 断言无反引号包裹）—— PASS | ✅ |
| **T35/SR-2 新鲜度 committed-only 注释（无逻辑改）** | `ship_gate.py:64-70` 定夺注释 committed-only；`is_stale`/`report_last_sha` 逻辑逐字未动（仍走 `git log`，不读工作树） | ✅ |
| **CR-4 merge untracked 机械 halt**：任何 `??`→halt | `sdflow-done/SKILL.md:251`「任何 `??` untracked 存在即 halt+报告…分诊交人工，脚本/skill 侧不做分类」 | ✅ |
| **CR-6 `-c core.quotePath=false`** | `sdflow-done/SKILL.md:248,250`（与 ship_gate `_GIT_HARDEN` 一致） | ✅ |
| **CR-5 gitignore 边界声明** | `sdflow-done/SKILL.md:251`「本检查不覆盖 gitignore 排除的路径…」 | ✅ |
| **SR-2 MUST NOT AskUserQuestion / 非交互 halt** | `sdflow-done/SKILL.md:252`「非交互 halt+报告…MUST NOT 用 AskUserQuestion 中途问、MUST NOT 静默继续 ff-merge」 | ✅ |
| **codex-2 tracked 路径 defer** | `openspec/issues/todolist/2026-07-todolist.md:59`（T51 OPEN，关联本 change） | ✅ |
| **T26/SR-1 无状态 helper**：`anchor_set`/`breaker_no_progress` 纯函数 | `ship_gate.py:250-266`（不接收 HEAD/mtime、不落地文件） | ✅ |
| **CR-2 对称 fail-safe**：before OR after is None → True | `ship_gate.py:264`「if before is None or after is None: return True」 | ✅ |
| **CR-1 熔断按 verdict 分治** | `sdflow-ship/SKILL.md:29`：①`STEP_IN_PROGRESS`→锚集判据；②`RERUN_STALE`→以「重跑后仍返回同一 RERUN_STALE」为准，MUST NOT 用锚集不变误判 | ✅ |
| **SR-1 HEAD/mtime MUST NOT 免疫 + fail-safe** | `sdflow-ship/SKILL.md:29`「HEAD 移动、文件修改时间戳变化 MUST NOT 作免疫信号…快照缺失保守判无进展」 | ✅ |
| **T26 CI 测试**：锚集不变判无进展 / 新锚判有进展 / fail-safe after=None | `test_gate_breaker.py:23-46`（4 用例含 `test_failsafe_missing_after_snapshot`）—— PASS | ✅ |
| **既有 TAG_RE / 判定逻辑逐字未动** | `TAG_RE`（`ship_gate.py:308`）、`decide`/`is_stale`/`done_task_ids` 逻辑未改；`test_producer_parser_contract.py` 等既有测试全绿 | ✅ |
| **SR-3 MODIFIED 块含 `<change-slug>`** | `specs/spec-workflow/spec.md:41` `## MODIFIED Requirements`；:47/:51 用 `<change-slug>` 占位符，delta 无残留 `<当前change>` 占位符 | ✅ |
| **T35/SR-2 软提示（非门禁）** | `sdflow-ship/SKILL.md:36,45`（`git status --porcelain` 排除 openspec/，仅信息性不改退出码） | ✅ |
| **5.1 归档后主 spec:517 同步为 `<change-slug>`** | 属 post-archive 校验；delta 已正确走 MODIFIED（archive 时替换旧文本），当前尚未归档故不可即验 | ⚠️（预期，非缺口） |

## 缺口清单

无核心功能缺口。以下 2 项为设计内 defer / 时序性事项，非缺陷：

1. ⚠️ **tracked 非-openspec 改动被 `git add -u` 先提交、绕过 merge 前 untracked 硬检查** —— 本 change SR-2 缩简版明确只覆盖 untracked，tracked 一路已 defer todolist（T51，OPEN，关联 gate-checkpoint-hardening）。符合 tasks 3.5 / spec 范围边界声明。
2. ⚠️ **主 spec:517 `<当前change>`→`<change-slug>` 同步** —— 依赖 `openspec archive` 执行 MODIFIED 替换，属 post-archive 校验点。delta 已正确以 MODIFIED（非仅 ADDED）承载，归档机制会驱动替换，验证机制到位。

## 验证命令实录

- `python3 -m pytest sdflow-ship/tests/ -q` → 109 passed
- `python3 -m pytest -q`（全仓）→ 375 passed（零回归）
- `openspec validate gate-checkpoint-hardening` → Change 'gate-checkpoint-hardening' is valid
- 6 个 checkpoint 命名空间标签均在位：`checkpoint(gate-checkpoint-hardening:task1..task6-*)`

---

PASS —— 3 ADDED + 1 MODIFIED 需求全部有可机验锚点落地，全仓 pytest 零回归，validate 通过；2 处 ⚠️ 均为设计内 defer / post-archive 时序事项，非核心功能缺失。
