# Hand-off — fix-voice-quoting-and-mirror-vocab

## ✅ 完成了什么

- **T164 路径引号修正**：两份 review SKILL.md 的 async-branch marker 内外所有路径模板加双引号（`<f>`/`{run-dir}`/`<repo-root>`/`{change_dir}`/`<d>`/`<确切目录>`），parity 守卫通过（锚：`hack/check_async_branch_parity.py` 实跑 ✅，commit `c4a263c`）
- **T148 `_FANOUT_MIRRORS` 扩展**：加入 `"history"` token，docstring 同步，消费拷贝刷新（锚：`anchor_lint.py:672`，commit `61ec9dd`）
- **code-review SKILL 真名替换**：`mirrors=` 模板从 `grounding` 改为 `history`，删除借用叙事（锚：`sdflow-code-review/SKILL.md:242`，commit `560ec77`）
- **三份 spec SHALL 条款扩展**：`{domain,adversarial,grounding}` → `{domain,adversarial,grounding,history}`（锚：`host-adaptive-execution/spec.md:157/159/161/174`、`workflow-metrics/spec.md:37`、`spec-workflow/spec.md:890`）
- **反漂移锁测试拆分+更新**：按文件区分预期（spec-review→grounding、code-review→history），借用文档测试改为验证真名（锚：`test_codex_subagent_authorization.py:150-179`，11 passed）
- **功能测试新增**：`test_anchor_lint.py` 补 history token 接受 + dead-fanout-multi-mirror 触发（锚：`test_anchor_lint.py`，29 passed）
- **todolist T164/T148 标 DONE**（代码审自动修）

## ⏳ 未完成 / 延后

本 change 无新增 buglist/todolist 批次（sweep 0 项）。代码审 defer 2 项：

- **F2**：`openspec/adr/0023-fanout-capability-probe-mechanical-floor.md:26` 仍写 3-token 词表，与扩展后的 4-token `_FANOUT_MIRRORS` 不一致（ADR 非脚本消费，无运行时影响）
- **F3**：引号改动 7 处仅 2 处有 golden 反漂移测试覆盖（dispatch + cleanup），其余 5 处（mkdir/exec+sidecar/collect/await/reconcile）无 golden 锁

## ▶ 下一阶段建议

- F2（ADR 词表漂移）和 F3（golden 测试覆盖面）可合一个小 change 清理，优先级低（无运行时影响）
- 本 change 来源 roadmap `high-value-issues-cleanup` P2（安全与锚一致性），P2 行可标完成
