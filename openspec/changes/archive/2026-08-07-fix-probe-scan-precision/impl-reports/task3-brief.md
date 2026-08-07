### Task 3: 告警语义改写（stale_shadow_warnings + maintain_scan）

**Blocked-by:** 2
**R-ID:** R4 (spec-workflow MODIFIED 残留副本须告警), R5 (maintain-scan MODIFIED)

`init.py` `stale_shadow_warnings()` 判据扩员（原 `RULE_MARKERS` 三项之外增查残留 `tools/` + `lens-metric-contract.md`）+ 文案改为带前置条件的死件表述 + 可复制删除命令。清理 checkpoint 孤儿告警的旧 pin 措辞。`sdflow-maintain` 兜底扫描同步改写。

- [ ] `stale_shadow_warnings()` 判据扩员 + 新文案（带前置条件 + 可复制删除命令）
- [ ] 清理 checkpoint 孤儿告警的 pin 措辞
- [ ] `sdflow-maintain` `test_maintain_scan.py` 按新语义断言反转（tools-only 残留 → 报死件告警）
- [ ] 文案测试正反双断言：不含 `显式 pin`/`遮蔽全局`，含新死件文案关键词与前置条件提示

