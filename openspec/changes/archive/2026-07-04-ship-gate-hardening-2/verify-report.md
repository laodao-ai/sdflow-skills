# verify-report — ship-gate-hardening-2

日期：2026-07-04
Change：ship-gate-hardening-2

## 结论：PASS

<!-- ship-gate: verify=PASS -->

Do-Not-Trust 冷启核验：逐条比对 spec/tasks 要求与 `sdflow-ship/scripts/ship_gate.py` 真实代码，每条 ✅ 附机验锚点（文件:行 / 测试名）。仓级 `python3 -m pytest -q` = **342 passed**（tasks.md 基线 328 + 本批新增 R1/R2 锚测，零回归）。

## 逐需求核对表

| 需求 / Scenario | 代码出处（文件:行 / 测试） | 状态 |
|---|---|---|
| **R1/T32** TAG_RE 可选命名空间捕获组 `checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-` | `ship_gate.py:231` | ✅ |
| **R1/T32** `done_task_ids(root, sha, change)` 命名组非空 → 仅 `ns==change`（精确==）计入；裸标签走窗口计入 | `ship_gate.py:262,286-289` | ✅ |
| **R1/T32** 字面前缀过滤放宽 `startswith("checkpoint(")`（非旧 `checkpoint(task`，否则命名标签被整条跳过） | `ship_gate.py:281` | ✅ |
| **R1/T32** 判别性负例（B 号=A 缺号）区分"只计当前"vs"两个都计"，真实 git commit fixture | `test_gate_namespace.py:9 test_namespace_isolation_discriminating`（+ 5 姊妹测） | ✅ |
| **R1/T32** 旧无命名空间裸标签向后兼容（窗口计入，升级前行为） | `test_gate_namespace.py:29 test_namespace_backward_compat_bare` | ✅ |
| **R1/T32** 非法 ns（大写/下划线）降级假阴安全，不误归属 | `test_gate_namespace.py:48 test_namespace_noncanonical_ns_degrades_safe` | ✅ |
| **R2/T34** `_parse_plan` fence-aware 单遍（标题与复选框共享同一 fence 状态） | `ship_gate.py:302-329` | ✅ |
| **R2/T34** `checkbox_done_ids` 按 `### Task <n>:` 分段、每段独立全勾判定（替换全局 checkboxes_all） | `ship_gate.py:332-336` | ✅ |
| **R2/T34** 复选框行锚定 `^\s*-\s+\[[ xX]\]`（非全文子串）+ 忽略 fenced code block 内伪框 | `ship_gate.py:299,313-328`；`test_gate_impl_progress.py:159 test_t34_fenced_checkbox_not_counted` | ✅ |
| **R2/T34** 全局单勾不放行未勾其它 task（分段绑定） | `test_gate_impl_progress.py:145 test_t34_no_checkbox_task_not_globally_passed` | ✅ |
| **R2/T34** 两通道并集 `checkpoint_done ∪ checkbox_done` 后判 `plan_ids ⊆ done` | `ship_gate.py:450-454`；`test_t34_checkbox_union_with_checkpoint:152` | ✅ |
| **R2/T34** 重号 `### Task <n>:` 段 → UNKNOWN（set 折叠掩盖假✅） | `ship_gate.py:345-350,444-447`；`test_t34_duplicate_task_number_unknown:168` | ✅ |
| **R2/T34** 未闭合围栏（悬空 ```）→ UNKNOWN（fail-safe） | `ship_gate.py:353-356,435-437`；`test_t34_unclosed_fence_unknown:177` | ✅ |
| **R2/T34** fenced 内 `### Task N:` 示例标题不算 task/不误判重号 | `test_t34_task_header_in_fence_not_counted:187` | ✅ |
| **producer①** 权威源 `sdflow-init/assets/workflow/workflow.md` 步6 checkpoint 步名改命名空间 `<change>:task<N>-<slug>` + 裸格式兼容注 | workflow.md 步6行 | ✅ |
| **producer②** `sdflow-ship/SKILL.md` RUN_PLAN 派发 args 同步命名空间格式 | SKILL.md:29 链序 RUN_PLAN | ✅ |
| **producer③** `test_workflow_authority.py` 断言 token 更新为命名空间 + 新增 SKILL 断言 | `test_workflow_authority.py:16-31 test_step6_tag_contract / test_skill_producer_arg_namespaced` | ✅ |
| **contract** `checkpoint-commit.sh` 零改（逐字插值 step 即产命名空间标签） | `git diff 9b5501b..HEAD -- sdflow-init/assets/hack/checkpoint-commit.sh` 空 | ✅ |
| **T33.1** 头注释「已知不覆盖」含裸污染残留（stacking+撞号）+ MUST NOT 用独立分支纪律缓解 | `ship_gate.py:60-63` | ✅ |
| **T33.1** 头注释含 T33 工作树 dirty 停置理由 | `ship_gate.py:64-66` | ✅ |
| **B1/B4 回归** 既有完成判据测试逐字不变、全绿 | `test_gate_impl_progress.py` 全通 | ✅ |
| **全量 pytest** 仓级 342 passed（基线 328 不回归） | `python3 -m pytest -q` = 342 passed | ✅ |

## 缺口清单

无核心缺口。所有 spec Scenario（T32 命名空间隔离 / 向后兼容；T34 全局单勾不放行 / 两通道并集 / 代码块伪框 / 重号 UNKNOWN）均有对应实现行与真实 git fixture 锚测。producer 三契约点同批改齐，checkpoint-commit.sh 零改经 git diff 证实。

## 结论

**PASS** — 代码真实实现 spec/tasks 每条要求，证据锚点齐备，无假✅，无回归。
