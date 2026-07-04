## 1. 契约测试（TDD 先行）

- [ ] 1.1 在 `sdflow-ship/tests/` 新增 contract 测试：读 `workflow.md` 文件，正则抽出其中的 checkpoint 标签格式 token，用它构造真实 subject（`checkpoint(demo:task1-slug): msg`），`import TAG_RE from ship_gate` 并断言 `TAG_RE.match` 成功、捕获组 == `("demo","1")`。测试直接读文件 + import，不硬编码期望串。（对应 Scenario「文档格式串与解析器双向绑定」）
- [ ] 1.2 增裸格式向后兼容断言：`checkpoint(task1-slug)` 被 `TAG_RE` match 且命名空间组为 `None`；断言 `workflow.md` 仍含裸格式向后兼容声明文字。（对应 Scenario「裸格式向后兼容两端一致」）
- [ ] 1.3 增派发引用断言：`sdflow-ship/SKILL.md` RUN_PLAN 段 MUST NOT 再含完整格式字面复述（断言不含独立格式串），MUST 保留派发语义要点关键词（「implementer」「gate 只认当前 change」等）。（对应 Scenario「派发指令引用而非复述」）——先跑，应因 SKILL.md 现含字面而红。

## 2. 瘦身文档到单一源

- [ ] 2.1 `sdflow-ship/SKILL.md` RUN_PLAN 派发段：删除完整格式字面复述，改为引用 workflow.md「step6 tag 契约」；保留派发动作 + 「由 implementer 执行」「gate 只认当前 change、跨 stacking 不污染」「裸格式向后兼容」等语义要点。跑 1.3 转绿。
- [ ] 2.2 `sdflow-init/assets/workflow/workflow.md` step6：在格式字面处补一句自我声明「此格式字面为权威定义，消费方（SKILL.md 等）引用不复述」，防后人再复制粘贴。跑 1.1/1.2 保持绿。

## 3. 回归 + 部署

- [ ] 3.1 跑 `pytest sdflow-ship/tests/`（含既有 `test_workflow_authority.py`）全绿，确认瘦身未破既有断言；跑仓级 `pytest` 无回归。
- [ ] 3.2 改了 `assets/workflow/` 权威源与 skill → 在开发 checkout 跑 `bash setup.sh`，使 symlink/canonical 生效可测。
