# Hand-off — curb-rework-loop-cost

## ✅ 完成了什么

本 change 的全部 8 项功能均已落地（verify PASS，20 条需求全 ✅，逐条有锚点）：

1. **① 单一盘面→中间轮/收口轮分离**：`sdflow-implement/SKILL.md` 第 7 条（中间轮只跑 unit + 上轮失败用例 ⊂ unit 层；收口跑全量锚同一 SHA；取消「受影响层」提法）
2. **② test-suites 成本分档**：聚合套件发现契约第 2 条（字符串/映射双形状 + unit 层例外）+ config.template.yaml 示例 + sdflow-devenv test-suites 发现与写入能力
3. **③ review package 增量化**：fix 轮只打包上轮已审 SHA..HEAD
4. **④ 熔断硬上限**：判据 (b) 同文件 ≥3 轮 + subsume 声明 + 全 change 计数窗口 + breaker-ledger 持久化 + 仲裁累积 diff
5. **⑤ 出票语法面有界性闸门**：含伪装形态判据 + 指令层约束标注 + 回指对照表
6. **⑥ code-review 复审边界**：硬上限 1 轮 + 文档分叉消除
7. **⑨ red-before-green 扩展**：覆盖补断言 + 修改既有断言
8. **⑫ 格式解析手段对照表**：verification-patterns.md §8

## ⏳ 未完成 / 延后

- **代码审 defer X-1**：复审轮 findings 未接入 lens-metric 度量管线（通则④简化，design Non-Goals 已覆盖）
- **⑪ YAML 界外 fail-loud**：proposal Non-Goals 已明确排除，单开 change（blast radius 不同量级）

## ▶ 下一阶段建议

1. **⑪ 单开 change**（优先级次于本 change，但与 ⑤⑫ 联动：⑤ 拦出票、⑫ 给替代手段、⑪ 补解析层根因）
2. **格式解析手段体检工具**：以 ⑫ 对照表为单一源，扫全仓现有 task 验收标准，找命中无界面的存量。须在 ⑫ 落地后开
3. **阈值复核**：⑤ 生效后一个自然观察窗（如 10 个 change），基于非解析器类病理重新采样校准 ④ 的阈值 3

（roadmap 回填：无关联，exit 3）
