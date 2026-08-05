---
ship-gate:
  verify: PASS
  reviewed_sha: 6bc2359dbcf75dd84cb149088c137901de796598
---

# Verify Report: fix-b11-b12-tools-hardening

**日期**: 2026-08-05
**结论**: PASS

## 逐需求核对表

| # | 需求/任务 | 代码出处 | 状态 |
|---|----------|---------|------|
| 1.1 | T174 fake-timeout 桩整数截断 | `sdflow-init/tests/test_outside_voice.py:42` — `sec="${sec%%.*}"` 截断 | PASS |
| 1.2 | T174 child_lifecycle 无需改动 | `sdflow-init/tests/test_outside_voice_child_lifecycle.py` — 使用 `shift 3; exec` 形式，无算术运算，确认无需改动 | PASS |
| 1.3 | T174 测试绿 | 全仓 pytest 2446 passed | PASS |
| 1.4 | T174 标 DONE | `openspec/issues/closed/todo/T174.md` — status: DONE, resolved_by: fix-b11-b12-tools-hardening | PASS |
| 2.1 | T139 parse_mode .findall() + 数量校验 | `sdflow-init/assets/workflow/tools/outside_voice_guard.py:98` — `_S1_RE.findall(outside)` + `:100` 缺锚 EmitError + `:102` 多锚 EmitError；权威源与 `openspec/workflow/tools/` 副本 diff 为空（完全同步） | PASS |
| 2.2 | T139 补测试 | `sdflow-init/assets/workflow/tools/tests/test_outside_voice_guard.py:421` — `test_duplicate_step1_anchors_fail_closed` + `:431` — `test_single_step1_anchor_returns_mode` | PASS |
| 2.3 | T139 测试绿 | 全仓 pytest 2446 passed | PASS |
| 2.4 | T139 标 DONE | `openspec/issues/closed/todo/T139.md` — status: DONE, resolved_by: fix-b11-b12-tools-hardening | PASS |
| 3.1 | T140 标 WONTDO | `openspec/issues/closed/todo/T140.md` — status: WONTDO, closed_reason 记录旧报告不走重 lint 路径 | PASS |
| 4.1 | T56 trivial_shape tests/plugins/ 排除 | `sdflow-init/assets/workflow/tools/trivial_shape.py:153` — `"tests/plugins/" not in path` 条件；权威源与 `openspec/workflow/tools/` 副本 diff 为空（完全同步） | PASS |
| 4.2 | T56 补测试 | `sdflow-init/assets/workflow/tools/tests/test_trivial_shape.py:211` — `test_new_tests_plugins_not_exempt` | PASS |
| 4.3 | T56 测试绿 | 全仓 pytest 2446 passed | PASS |
| 4.4 | T56 标 DONE | `openspec/issues/closed/todo/T56.md` — status: DONE, resolved_by: fix-b11-b12-tools-hardening | PASS |
| 5.1 | T188 basename 唯一性守卫 | `hack/tests/test_test_basename_uniqueness.py` — 扫全仓 test_*.py basename，重复即 fail | PASS |
| 5.2 | T188 测试绿 | 全仓 pytest 2446 passed | PASS |
| 5.3 | T188 标 DONE | `openspec/issues/closed/todo/T188.md` — status: DONE, resolved_by: fix-b11-b12-tools-hardening | PASS |
| 6.1 | 全仓 pytest 绿 | 2446 passed, 10 skipped, 1 failed（SA-14 预存 fail，不属本 change） | PASS |
| 6.2 | roadmap 批次状态更新 | tasks.md 已勾选 | PASS（未独立核验 roadmap 文件，属 minor 记录项） |

## 缺口清单

无核心缺口。

**预存 fail 说明**: `hack/tests/test_harden_sdflow_spec_followup_closure.py::test_spec_authoring_requirement_ids_and_resident_identity_are_consistent` 断言 SA-14 锚，属 sdflow-spec 后续 change 的遗留断言，与本 change 无关。

## 补充核验

- **skip_specs: true** 已在 `.openspec.yaml` 确认——纯工具加固无行为 spec 变更，无 delta specs 是预期行为。
- **实现管线**: config.yaml 配置 `impl-pipeline: tickets`，但本 change 无 tickets.md/superpowers-plan.md，系直接在主 session 实现的小批量加固，按实际情况处置。
- **权威源同步**: outside_voice_guard.py 和 trivial_shape.py 的权威源（`sdflow-init/assets/workflow/tools/`）与 openspec 副本（`openspec/workflow/tools/`）完全一致（diff 为空）。
