# 阶段三去人类门，verify 靠证据锚点堵假绿

阶段三（实现 → 代码评审 → 收尾）**去掉旧 step 14 的阻塞人类门**，过完阶段二设计门后一口气自动跑到 merge。代价是 **verify（在 opsx-done 内）成为唯一终门**。为让这个唯一门可信，给 verify 焊死三条防"假✅"约束：(a) 每条 Requirement 的 ✅ 必附一个可机验锚点（测试名 / commit hash / 文件行号），无锚点的 ✅ 一律降级为 gap；(b) verify 子代理用强模型 + "Do Not Trust the Report" 冷启，禁用弱模型；(c) hand-off.md 不继承 verify 的 ✅，引用项须独立复核。

## Considered Options

- **去人类门 + verify 证据锚点硬约束（选中）**：全流程只在阶段二设计门停一次人类，阶段三全自动。用机验锚点 + 强模型 verify 替代人肉盯梢来防假✅。换来连续自动流，且门的可信度不再依赖人是否认真看。
- **阶段三保留一个轻量人类门**：过设计门后仍让人 10 秒扫一眼 hand-off + verify-report 再放行。多一道人肉兜底，但破坏"一口气跑到 merge"，且人肉扫一眼恰恰是 T45/T46 假✅溜过去的那种失效模式。
- **纯 verify 当唯一门、不加约束（design 原状）**：最省事，但 verify 有假✅前科（T45/T46），不完整的活会静默 merge 且被 hand-off 固化，不可接受。

## Consequences

- opsx-done 的 verify 步须改造：产出的 verify-report.md 每条 Requirement 的判定都要挂锚点；verify 子代理指定强模型（不走弱模型省钱路径，呼应 CLAUDE.md 铁律）。
- hand-off.md 产出步须显式声明"未落实/延后项不得继承 verify ✅"，其"已完成"清单引用 verify 结论时至少复核锚点存在性。
- 无锚点的需求（如纯性能基线、估时类"软"需求）会被 verify 判成 gap 而非 ✅，逼实现方要么补可机验的证据（benchmark/测试），要么显式 defer 进 buglist/todolist——即 T45/T46 那类"标了✅其实没做"从源头堵死。
- 反向风险：证据锚点约束提高了 verify 的严格度，可能把"确实做了但没留可机验痕迹"的需求误判成 gap；接受此偏保守，因假✅（漏）比假红（误报）后果重——假红当场补锚点即可，假✅会静默 merge。
