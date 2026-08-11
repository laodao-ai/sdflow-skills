### Task 4: 首轮 dogfood + 收口

**Blocked-by:** 3
**R-ID:** R1, R2, R3, R4

跑首轮真实 `/sdflow-upstream-watch`（真网络四源采集）并收口散点：

1. 开发 checkout 跑 `bash setup.sh` 验证新链建立 + `--check` 门绿。
2. 真跑 collect（四源真实网络）→ 报告落 `openspec/upstream/reports/` → advance 建锚。
3. 验证 gstack 节含真 delta（`960c3a8..` 区间非空为预期基线）。
4. T264 → DONE（recorder set-status，evidence 指 schema drift 采集器实现 + 测试）。
5. 确认 T245/T246/T267 在首轮报告 seed 节在场后保持池内原状。
6. 全仓 `/usr/bin/python3 -m pytest` 绿。
7. 手工验收 upgrade 提醒两分支（超阈值提醒行 / 无锚静默）。

- [ ] setup.sh 新链建立成功 + sync_principles --check 绿
- [ ] 首轮 collect 四源均产出 facts（ok 或 degraded 各有据）
- [ ] 报告落盘且 gstack 节含真 delta
- [ ] advance 建锚成功（anchors.yaml 已创建、last_run 已写入）
- [ ] T264 已 set-status DONE（evidence 指采集器）
- [ ] T245/T246/T267 池内原状未变
- [ ] 全仓 pytest 绿
- [ ] [e2e] upgrade 提醒超阈值时输出一行含天数的提醒、无锚时静默跳过

