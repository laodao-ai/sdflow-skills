### Task 3: 三处消费点以指针方式引用拆分标准

**Blocked-by:** 1
**R-ID:** SA-17 · 阶段拆分锚定 change 拆分标准（ADDED）

让拆分标准在三个真正做分解判断的位置生效：产 spec 的收敛前检查、roadmap 的阶段拆分、代码审的
defer 流。三处**一律指针引用**单一源，不复制标准文本（grep 可验无复制）。

- [ ] 产 spec 的相位 B 收敛前检查新增 **scope 内聚检查**：按拆分标准核目标态范围 = 一个完整内聚的阶段结果（砍窄 / 加宽 / 混拼不相关功能均为偏离）；发现偏离连同拆分或合并建议**呈现给人拍板**，MUST NOT 静默调整范围
- [ ] roadmap 的阶段拆分处加指针引用：每阶段 = 一个完整阶段结果（未来恰好一次 change 可交付）；MUST NOT 按来源批次 / 顺手凑票拆分，MUST NOT 把一个内聚交付物拆散跨多阶段，MUST NOT 把不相干功能混入同一阶段
- [ ] 代码审的 defer 流加 fold/defer 判定指针：related 发现先过 BASE-18 AND 门再定去向，对齐既有 fold-vs-defer 条款
- [ ] 三处均为指针引用，**未复制**标准文本（自验方式：grep 标准文的特征句，命中只应有单一源一处）
- [ ] 代码审 SKILL 的编辑**未落入** async 调度 marker 段内（`hack/tests/test_async_branch_parity.py` 守两站点逐字节一致，落进去即红）
- [ ] `sdflow:principles` 托管块零改动（只动业务段）

