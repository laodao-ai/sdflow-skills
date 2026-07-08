# Tasks — done-roadmap-writeback

> Requirement 追溯：**R1**=roadmap 回填降摩擦助手（定位到 phase 机械、勾哪几行判断留人）；**R2**=关联解析（前缀为主·marker 兜底·fence-aware·漏则退现状）。
> 〔spec-review-amendment · adr/0015 + 第三轮精化 P-1..P-5〕切分线重画：定位到 phase（change 名前缀确定性信号）=机械、勾哪几行=判断留人。**弃** scaffold/enum 聚合/编号统一/迁移。

## 1. 关联解析（R2）

- [ ] 1.1 主通道：change 名前缀 `implement-{roadmap}-pN-*` 确定性解析 roadmap+phase（消 C-14 chicken-egg，无需人手标）〔R2·P-2〕
- [ ] 1.2 兜底通道：change 内独占一行 marker `<!-- roadmap: {name}#{phase} -->`；检测 **fence-aware**（跳 code fence/行内 code）+ 行锚定 + 排除 change 自身讨论区（消 C-5 自指假阳）〔R2·P-5〕
- [ ] 1.3 覆写 + 优先级：done `--roadmap {name}#{phase}` > marker > 名前缀；多通道不一致 → warn（反静默）〔R2·C-6〕
- [ ] 1.4 未声明且前缀不符 → 退现状不阻塞；疑似 roadmap 驱动（分支名/change 名近 roadmap 目录）**SHOULD** 提示（C-12）〔R2·C-12〕

## 2. 回填草稿生成（R1）

- [ ] 2.1 读**步2 已实现盘面**：verify=PASS frontmatter + tasks 完成态 + change 名 + 分支（复用 ship_gate/done 已有读取，不新造真相源）；archive 路径(步3)/merge(步5) **留占位「待归档后人补」不预填**（P-1 消 C-1）〔R1〕
- [ ] 2.2 pytest 数机械锚：有测试从 verify-report 取、无则标 N/A（纯 Markdown change 无测试，不当交付事实预填；不重跑引入非确定）〔R1·C-8〕
- [ ] 2.3 形态探测（P-3 消 C-3）：复选框式（`- [ ] {id}`）→ 定位该 phase **候选复选框行集**（不判勾哪几行）；表格/散文式（`| ✅`）→ **不产复选框草稿、fail-loud 告知留人工**〔R1〕
- [ ] 2.4 task-log 完成总结骨架（两形态都产）：预填机械锚（change 名/verify 结论/pytest 数/archive 占位）+ 交付标注模板；价值叙述/阶段状态/deferred 留空位给人补〔R1〕
- [ ] 2.5 （可选）轻脚本辅助（前缀解析/形态探测/grep phase 行/读 frontmatter/拼骨架）+ `tests`；若纯 done 指令步则坏输入契约写成与载体无关的可判定行为规范〔R1〕

## 3. sdflow-done 收尾步（R1）

- [ ] 3.1 `sdflow-done/SKILL.md` hand-off 步：检测关联 → 生成草稿写进 `hand-off.md` + 提示「检测到关联 roadmap {name}#{phase}，草稿见下，请过目后回填」；**阶段三无门**——不弹窗、不阻塞归档/merge〔R1〕
- [ ] 3.2 `sdflow-done/SKILL.md` **第六步摘要抬一行**「⚠ roadmap {name} 回填草稿待人确认（见 hand-off）」使 merge 时点可见（P-4 消 C-4）；design 显式登记「产草稿即止、不保证 apply」残差〔R1〕
- [ ] 3.3 设计原则区登记：与 `§2.1 issues sweep` **同位不同性**（同为 done 收尾盘面消费，但 sweep 机械终写机器独占文件 / roadmap 回填**助人确认**，写入语义相反，C-7）——不诱导复用 sweep 自动落盘〔R1〕
- [ ] 3.4 助手 MUST NOT 写 change 产物文件（tasks/proposal，避 C1）；MUST NOT 产 per-行「建议勾」（只产阶段级候选行集，勾哪几行留人）；MUST NOT 机械聚合 enum/推 deferred〔R1·P-2〕

## 4. 关联约定入规则（R2）

- [ ] 4.1 （若关联约定入 workflow 规则）改 `sdflow-init/assets/workflow/` 权威源 + `sdflow-init update` 回灌（bundle 纪律）；命名约定 `implement-{roadmap}-pN` 若需强制则在 roadmap/触发规则登记〔R2〕

## 5. 验证（TG-18）

- [ ] 5.1 前缀解析：`implement-{roadmap}-pN` 命名 → 确定性解析 roadmap+phase 触发草稿〔R2·P-2〕
- [ ] 5.2 **fence-aware 防自指**（关键）：marker 串仅在 code fence/散文内（如本 change 自身）→ 判无关联、不误检测〔R2·P-5·C-5〕
- [ ] 5.3 时序：草稿只含步2 已实现锚（verify/tasks/change 名）；archive/merge 为占位不预填〔R1·P-1·C-1〕
- [ ] 5.4 形态分治：复选框式 → 定位候选行集；表格/散文式（wco fixture）→ fail-loud 留人工不静默〔R1·P-3·C-3〕
- [ ] 5.5 判断留人：助手不产 per-行建议勾、不改 roadmap、不聚合 enum；勾哪几行/价值叙述由人〔R1·P-2〕
- [ ] 5.6 边界：双通道不一致 warn；未声明退现状不阻塞 + 疑似驱动 SHOULD 提示；坏输入三分（absent/malformed/verify≠PASS）〔R2·C-6/C-9/C-12〕
- [ ] 5.7 dogfood：本 change 名非 `implement-*` 前缀 + marker 仅在 fence/散文内 → 应跳过（验 P-5）；另构造 `implement-{roadmap}-pN` fixture + 两形态 roadmap 验草稿生成〔R1/R2〕
- [ ] 5.8 若加脚本：`pytest` 覆盖坏输入三分 + fence 内不误检测 + 同盘面输入同骨架输出（确定性，无墙钟/随机）；`-W error` 0 warning〔R1·C-9〕

### 测试覆盖图（TG-18）

```
code path                                测试类型
───────────────────────────────────────  ────────────────────────────────
前缀解析 implement-{roadmap}-pN            pytest 或场景核对（5.1）
marker fence-aware 防自指(fence内不检测)    pytest（5.2/5.7）★关键
时序·archive/merge 占位不预填              场景核对（5.3）
形态探测·复选框式定位/表格式 fail-loud       pytest + 场景（5.4）
判断留人·不产per行建议勾/不改roadmap/不聚合   场景核对（5.5）
双通道优先级/不一致 warn                    pytest 或场景（5.6）
坏输入三分 absent/malformed/verify≠PASS     pytest（5.6/5.8）
不碰 change 产物文件（避 C1）               静态核对 + 场景（3.4）
带前缀 fixture + 两形态→草稿生成            dogfood（5.7）
同盘面输入→同骨架输出（确定性）             pytest（5.8）
```

> 最小核：机械部分（前缀解析/fence 检测/形态探测/盘面读/骨架）若脚本化则 pytest 覆盖坏输入三分 + 确定性 + fence 自指；判断部分（勾哪几行/算不算完成/价值叙述/阶段状态/deferred）走人确认、场景核对。**无** scaffold/enum/编号统一/迁移的重机制，无对应测试面。
