wrote openspec/changes/sweep-pool-debt-2026-08/impl-reports/task4-brief.md: 10 lines
memo D7，无 spec delta）

按 DT-5 判据把 `sdflow-spec/SKILL.md` 可下沉小节移入 `references/`，把 SKILL 本体压回预算，既有 resident-contract 契约测试保持全绿。

- [ ] 按 DT-5 判据（可下沉 = 执行到该步才需展开的判据表/参考细节；不可下沉 = 流程骨架/铁律/fail-closed 分支）挑选 `sdflow-spec/SKILL.md` 可下沉小节 → `references/`（含路由句），本体 ≤16,000 字符（余量 ≥2,000）
- [ ] `pytest hack/tests/test_sdflow_spec_resident_contract.py` 全绿 + 全量 pytest 复核

