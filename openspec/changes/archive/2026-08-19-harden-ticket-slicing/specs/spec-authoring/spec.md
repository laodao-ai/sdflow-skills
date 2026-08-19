## ADDED Requirements

### Requirement: SA-17 相位 B scope 内聚检查与相位 C 切片建议生成〔harden-ticket-slicing〕

相位 B 收敛前检查（ADR/术语回扫的同一检查点）SHALL 增加 **scope 内聚检查**：按 change 拆分标准（单一源 `openspec/workflow/reference/change-decomposition-standard.md`，经 resolver 解析，指针引用 MUST NOT 复制标准文本）核目标态范围 = **一个完整内聚的阶段结果**——砍窄、加宽、混拼不相关功能均为偏离；发现偏离 SHALL 连同拆分/合并建议呈现给人拍板，MUST NOT 静默调整范围。

相位 C 生成 design.md SHALL 遵循生成约束的「切片建议」升档语义（SHOULD）：非平凡 change 的 design.md 决策区 SHOULD 含「切片建议」节（初步 ticket 划分 + 阻塞边草图）；缺席时 SHALL 在 design.md 写明一句为何不需要（如单票即可交付的小修）。缺席理由的成立性由阶段二 BASE-31 审项核验，本相位只负责「有节或有理由」二择一恒成立，MUST NOT 两者皆无。

#### Scenario: 非平凡 change 生成含切片建议节

- **WHEN** 相位 C 生成一个多任务、多文件面的 change 的 design.md
- **THEN** design.md 决策区含「切片建议」节（初步票划分 + 阻塞边草图），供阶段二评审与出票模式消费

#### Scenario: 平凡小修缺席切片建议须附理由

- **WHEN** 相位 C 生成一个单文件小修 change 的 design.md，判断无需切片草图
- **THEN** design.md 写明一句缺席理由（如「单票交付，无切分必要」），MUST NOT 静默缺节

#### Scenario: 相位 B 发现混拼时呈现拆分建议

- **WHEN** 相位 B 拷问发现目标态混入了一个与主线无耦合的独立功能
- **THEN** 主 session 按拆分标准判其不满足内聚判据，向人呈现「拆出另开 change」建议与依据，由人拍板；MUST NOT 静默砍掉或静默保留
