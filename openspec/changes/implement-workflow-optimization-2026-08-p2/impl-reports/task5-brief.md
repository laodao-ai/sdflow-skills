### Task 5: Done 终态快照接线

**Blocked-by:** none
**R-ID:** R-快照

在 sdflow-done 收尾流程接入终态 token 快照采集点。

**行为**：
- sdflow-done 第三步（Archive）起手前、change 目录尚在原位时，调 `token_snapshot.py --step done-final`（anchor=true）
- 追加进 change 目录 token-log.jsonl，随 archive 搬走
- 失败显式降级不挡收尾（同既有口径）
- 残余盲区（archive/commit/merge 自身用量）在契约文档如实声明
- host 判定补丁：codex/unknown 宿主不走 Claude transcript mtime fallback，直接落显式降级行
- `done-final` step 值入契约文档
- retro join 对该行可读（冒烟）
- 已知边界声明：done 收尾跨 session 重试时 token 统计可能重复计入（view-only 精度边界）

- [ ] sdflow-done SKILL 第三步起手含 token_snapshot 调用接线
- [ ] 失败显式降级不挡收尾流程
- [ ] codex/unknown 宿主不走 Claude mtime fallback，直接显式降级
- [ ] done-final step 值记入契约文档
- [ ] retro join 对 done-final 行可读

