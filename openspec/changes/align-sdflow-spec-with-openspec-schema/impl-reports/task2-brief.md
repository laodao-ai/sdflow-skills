### Task 2: 让初始化与更新安全下发并迁移 schema

**Blocked-by:** 1
**R-ID:** SW-SCHEMA

消费仓在 CLI 版本满足门槛时能获得并启用 project-local schema；版本不足、命令缺失或输出异常时保持内置 schema 并明确报告原因。更新时，在途 change 先获得正确的 schema 绑定，再切换配置；下发采用整删重拷，且已有配置只改 schema 单键。

- [ ] CLI 版本按 semver 数值元组判断，`<1.7.0`、命令缺失和非数字输出均 fail-closed 并输出一行结论
- [ ] 仅扫描含 `proposal.md` 的在途 change；缺绑定者被补写，已有绑定者 no-op，归档和 stray 目录不受影响
- [ ] 任一补写失败会中止本次运行，配置不会切换；顺序有测试证据
- [ ] schema bundle 采用 rmtree-first 整删重拷，权威源删除的文件不会残留在消费仓
- [ ] 配置模板与消费仓配置在版本门通过时指向 fork schema，update 模式只改 schema 行且其余内容保持 byte-identical
- [ ] 版本门与迁移补写结论进入既有动作汇总

