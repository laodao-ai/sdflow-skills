### Task 1: 删除两个评审 SKILL 的 skew 探测段

**Blocked-by:** none
**R-ID:** R1 (host-adaptive-execution REMOVED)

删除 `sdflow-code-review/SKILL.md` 与 `sdflow-spec-review/SKILL.md` 第零步的 skew 探测整段（code-review 四条信号、spec-review 两条信号），及其产生的悬空指代（档位解析步引用已删段的「三处均为…」措辞）。保持 `exit 2` 既有降级分支不变。

两个 SKILL 的 `sdflow:async-branch` marker 区间受 `hack/check_async_branch_parity.py` 逐字节等值门约束——MUST 两文件同改。区间内「两条分发链」措辞订正为单链表述（`manifest skew` 的修法保留）。`hack/tests/test_async_branch_parity.py` 的断言同批改写为新文案关键词。

- [ ] 删除 `sdflow-code-review/SKILL.md` skew 探测整段，步序号顺延
- [ ] 删除 `sdflow-spec-review/SKILL.md` skew 探测整段，步序号顺延
- [ ] 清理档位解析步悬空指代（改写为不引用已删段）
- [ ] 逐字比对确认两个 SKILL 的 `exit 2` 降级分支未被误改
- [ ] `sdflow:async-branch` 区间内「两条分发链」→ 单链表述，两文件同改
- [ ] `hack/tests/test_async_branch_parity.py` 断言同批改写
- [ ] 验收 grep：`grep -n "skew 探测\|lens-metric-enums\|scope-audit:\|_MIRRORS_LEGAL" sdflow-code-review/SKILL.md sdflow-spec-review/SKILL.md` 命中数恰为各文件 1 处（anchor_lint 自检段合法引用）

