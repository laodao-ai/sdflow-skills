---
ship-gate:
  verify: PASS
---

# verify-report — async-outside-voice

- **change**: `async-outside-voice`
- **日期**: 2026-07-18
- **结论**: **PASS**（核心功能全部落地并有可机验锚点；仅余 3 项文档陈旧措辞的 Minor 缺口 + 已登记 deferred）

核对方式：以 tasks.md + delta spec 为准，逐条回到**产物本身**（SKILL.md 行号 / 脚本函数 / 测试 / commit）取锚，不采信复选框与既有报告措辞。全量机械门实跑：`/usr/bin/python3 -m pytest hack/tests/ sdflow-init/assets/workflow/tools/tests/ -q` → **381 passed**；`python3 hack/check_async_branch_parity.py` → exit 0（`[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致`）。

## 逐需求核对表

| 需求 / 任务 | 出处（文件:行 / 测试名 / commit） | 状态 |
|---|---|---|
| 1.1 spec-review 加 `$SDFLOW_HOST` 分支 + 内层 900/300 + 通知驱动 collect barrier | `sdflow-spec-review/SKILL.md:286-346`（marker 段），矩阵表 `:301-305`，barrier `:319-331` | ✅ |
| 1.2 dispatch 记「站点↔task_id」+ collect 逐站点取 | `sdflow-spec-review/SKILL.md:339-345`（⑧ 记账表 + 「MUST 按本表逐站点取」） | ✅ |
| 1.3 `run_in_background` 能力自探 + 降级标注 | `sdflow-spec-review/SKILL.md:292-296`（②，`background="available|unavailable"`，MUST NOT 假装 async 成功） | ✅ |
| 2.1 code-review 同款分支（逐字对齐） | `sdflow-code-review/SKILL.md:284-344`（同 marker 段）；commit `17e8b44` + `84aefa8` | ✅ |
| 2.2 机械等值门（marker + 脚本 + setup.sh + tests + 首跑绿） | `hack/check_async_branch_parity.py`；`setup.sh:235-241`；`hack/tests/test_async_branch_parity.py`；实跑 exit 0 | ✅ |
| — 站点相关内容留 marker 外（G1） | declared-sites 段在 marker 外：spec-review `:354`、code-review `:352`；context 构造在 marker 外 `:271-282` | ✅ |
| 3.1 collect 语义：通知驱动 barrier、结构化退出码、RUNNING 让出轮次、timeout 只由实测 124 产生 | `sdflow-spec-review/SKILL.md:319-331`（⑥），退出码表 `:333-340`（⑦：124→timeout / 1·2·未知→exec-error / 3→secret-hit） | ✅ |
| — 退出码通道 = runner 写不了的 sidecar（spec Scenario「不可被 runner 伪造」） | `sdflow-spec-review/SKILL.md:308-311`（④ sidecar `{run-dir}/<site>.rc` + 威胁模型）、`:315-319`（⑤ `^[0-9]+$` / 缺席→exec-error）；commit `aec3380` | ✅ |
| 3.2 `outside-voice.sh` / 合法组合矩阵 / 出境安全三件套零改动 | `git diff main...HEAD -- sdflow-init/assets/hack/outside-voice.sh` → **0 行**；anchor_lint diff 无删除行（纯 additive）；`test_matrix_cross_tool_golden_full_cartesian`（`test_outside_voice_guard.py:394`）绿 | ✅ |
| 3.3 天花板可配 + 校验（async 900 / sync 300，config 直读、非法回落默认） | `sdflow-spec-review/SKILL.md:288-291`（①：`outside-voice.async-timeout-seconds`、正整数 1..3600、越界→回落 900、MUST NOT `--timeout 0`）；`openspec/config.yaml:70-74` 注释段 | ✅ |
| 3.4 per-run 不可变 context 路径 + 父目录仍在 `.outside-voice/` + manifest | `sdflow-spec-review/SKILL.md:273-282` / `sdflow-code-review/SKILL.md:271-280`（`mktemp -d`、run-id 字面值、`**/.outside-voice/` 条款、`dispatch-manifest.tsv` printf） | ✅ |
| 3.5 per-site 完整性机械核（declared == 期望集 ∧ == 实落集，复用 `fence_outside_lines`） | `anchor_lint.py:554-620` `check_declared_sites`（`fence_outside_lines` 复用见 `:561`、公式重算 `:604-610`、反规避注释 `:611-615`）；测试 98 处 declared 断言，`sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` 全绿；commit `41bce45`+`8c2c998` | ✅ |
| — declared 按「应有锚」而非「应 dispatch」（复用态不假红） | spec-review `:354-356`（`{design-voice}∪{hr-tg|…}`）、code-review `:352-356`（`{code-voice}∪…` + 「MUST NOT 混用」） | ✅ |
| 4.1 smoke（①②④⑤ 实证 / ③ 部分） | `impl-reports/task5-verification-smoke.md`、`-fix1.md:132`（三时刻单调 dispatch 10:38:10 ≤ terminal 10:42:32 ≤ collect 10:43:35）、`-fix2.md:69-82`（900s 真 exit 124） | ⚠️ 见下（诚实说明属实） |
| 4.2 全笛卡尔 golden 回归与 change 前一致 | `test_matrix_cross_tool_golden_full_cartesian`；`task5-verification-smoke.md:131-132`（cart_pre / cart_post sha256 相同 `cb1548f4…526e7`） | ✅ |
| 4.3 降级路径 smoke + 外层 ≥330000ms 断言 | `task5-verification-smoke.md:252-275`（外层实参 330000ms、实测 181s > 默认 120s） | ✅ |
| 4.4 自探降级分支可跑（Open Q2 已由读码解） | 同 4.3 §6；ADR-6 记于 design.md | ✅ |
| 4.5 安全错误路径（只取 exit0 stdout、不采信原始 stderr） | `task5-verification-smoke.md:284-300`（exit 1/2/3 实跑，rc=2 ⇒ findings 池取空）；写出面收窄 commit `de0ffba` | ✅ |
| 5.1 Codex efficacy=0 todo | `openspec/issues/todolist/2026-07-todolist.md:21`（T162） | ✅ |
| 5.2 DRY 全抽取 todo | 同上 `:22`（T163） | ✅ |
| CI 泳道 | `.github/workflows/mechanical-gates.yml:25-26,28-29,31-32`（parity / principles / 全量 pytest 三步独立） | ✅ |

## 4.1 的「部分达成」说明是否属实

**属实。** tasks.md:33 称 ①②④⑤ 已实证、③ 的「真实负载」半未达成（时长由 PATH shim 控制 runner 返回时刻）。核对 `-fix2.md:5-26` 确认：shim 只替换裸命令 `codex`/`claude` 控制返回时刻，编排路径（host 分支 → run_in_background dispatch → 真 `timeout -k 10 900`）全真；`-fix2.md:69-82` 有真 exit 124 端到端。「后台跨 600000ms 上限存活」另由 702s 主 session 探针实证（SKILL.md:297）。措辞未夸大，且 `[~]` 而非 `[x]`——诚实标记正确。

## 缺口清单

### 核心缺口
无。

### Minor 缺口（均可接受，不阻塞）

1. **两个 SKILL 的 ④/⑦ 残留哨兵时代措辞**（`sdflow-spec-review/SKILL.md:307`「两分支共用同一哨兵 envelope」、`:314`「为什么是 `printf '\n…'` 而不是 `echo`」整段、`:340`「envelope 0 行或 ≥2 行」；code-review 同位置逐字相同）。sidecar 修法下命令形态已是 `printf '%s' "$?" > {run-dir}/<site>.rc`，无 `\n` 前置、无行计数语义 ⇒ 该段是**死文本**。行为无害（真正的判定规则 `:315-319` 写的是 sidecar），但违反 DOC-1「正文即最终态」。两侧字节相同 ⇒ 等值门不受影响。**建议后续清理**。
2. **tasks.md:16（3.1）仍描述「哨兵 envelope 三条」**，与 delta spec（sidecar）不一致。计划文档陈旧，非产物缺陷。
3. **`-fix2.md:69-82` 的真 exit 124 证据取自哨兵通道**（`<<<SDFLOW_EXEC_EXIT>>>124`），即替换前的设计。sidecar 通道本身的三态实测记于 `code-review-report.md:65`（正常落 rc / 被杀缺席 / 非数字），已覆盖，但**真 124 未在 sidecar 通道下重跑**。属证据代际差，风险低（`printf '%s' "$?"` 对 rc 值无分支）。

### 已登记 deferred（非本次缺口）
B9(P1, 200KB 截断切断 UTF-8)、B10(P2, 孤儿 runner 进程) — `openspec/issues/buglist/2026-07-18-buglist.md:8-9`（均 VERIFIED，`change=async-outside-voice`）；T157/T158/T160–T167（含 T165 真实模型 >300s 未证、T166 end marker 硬化待查）、T162/T163 — `openspec/issues/todolist/2026-07-todolist.md`。

---

**PASS**
