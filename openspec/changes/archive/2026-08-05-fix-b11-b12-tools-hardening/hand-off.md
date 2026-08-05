# Hand-off: fix-b11-b12-tools-hardening

**日期**: 2026-08-05

## ✅ 完成了什么

issues-triage roadmap B11+B12 合批的 8 条 issue 全部关闭：

| ID | 结果 | 证据锚 |
|---|---|---|
| T176 | DONE（先前已修） | `outside-voice.sh:913-916` timeout=0 拒绝 |
| T230 | DONE（先前已修） | `outside-voice.sh:836-851` D2 出境截断 |
| T68 | DONE（先前已修） | `anchor_lint.py:105-114` fence_char+fence_len 匹配 |
| T174 | DONE | `test_outside_voice.py:42` sec 整数截断 |
| T139 | DONE | `outside_voice_guard.py:98-102` findall + 数量校验 |
| T140 | WONTDO | 旧报告不走重 lint 路径 |
| T56 | DONE | `trivial_shape.py:153` tests/plugins/ 排除 |
| T188 | DONE | `hack/tests/test_test_basename_uniqueness.py` basename 唯一性守卫 |

全仓 pytest 2446 passed, 10 skipped。

## ⏳ 未完成 / 延后

- 无本 change 新增的 bug/todo（issues scan 返回空）
- 1 条预存测试失败（`test_harden_sdflow_spec_followup_closure::test_spec_authoring_requirement_ids_and_resident_identity_are_consistent`）——SA-14 锚断言失效，不属于本 change，需单独修复

## ▶ 下一阶段建议

- roadmap B11+B12 已在实现过程中更新为 v10（85 条 open todo），总览表已标完成
- 下一批次 B13（sdflow-maintain 扫描器硬化，4 条）已就绪，可直接开 change
- 预存 SA-14 测试失败建议在 B15（文档+术语+spec 订正）或单独修复中处理
