### Task 4: 完成本仓 dogfood 切换的零回归验证

**Blocked-by:** 2, 3
**R-ID:** SW-SCHEMA, SA-05, SA-17

本仓切换到 project-local schema 后，在途 change 的 artifact 状态保持不变；一次性新 change 能证明 CLI 返回的新依赖图被相位 C 正确消费，验证用 change 不进入最终工作树。

- [ ] 切换前为全部在途 change 保存 `openspec status --json` 快照
- [ ] 运行初始化/更新流程后，schema bundle 与 config 已切换到目标状态
- [ ] 切换后逐 artifact 对比 status 快照，状态完全一致
- [ ] 一次性 change 验证 `specs` 含 design、`tasks` 含 proposal 的 dependencies，验证完删除
- [ ] 验证结果记录了 CLI 实际输出，不以静态解析配置文件替代

