<!-- sdflow:step1-broad-review v1 mode="native" -->

# autoplan 广审（Step1）

## CEO 双声共识表

| 维度 | Claude | Codex | 共识 |
|---|---|---|---|
| 前提有效？ | T164/T148 有效 | T148 前提叙述需修正（非 bypass 修，是词汇语义修正） | DISAGREE（叙述精度） |
| 正确的问题？ | 是 | 是 | CONFIRMED |
| 范围校准？ | 合适但 T164 清单不完整 | 建议拆分 | DISAGREE |
| 备选方案覆盖？ | Non-Goals 合理 | 无遗漏 | CONFIRMED |
| 威胁模型精度？ | 措辞比实际防护更宽 | 不是安全修而是可靠性加固 | CONFIRMED |
| 验证覆盖？ | parity 不验引号是否在 | 验证计划证明同步不证明修复 | CONFIRMED |

## Findings

### F1 [gstack-amendment] · T164 清单遗漏 marker 内路径占位符

**严重度**：中 · **置信度**：高 · **来源**：Claude CEO

design.md 的修改清单和 tasks.md 1.1/1.2 只枚举了 `<f>`、`{run-dir}`、`<repo-root>` 三种占位符，
但 async-branch marker 段内还有 `<d>`、`<确切目录>` 两种形式出现在人工恢复场景的命令提示中
（code-review L448/465/466，spec-review 对应行），同样代表目录路径，同样未加引号，
不在 design.md 的「不需要（clamped integer / controlled enum）」排除列表中。

**建议**：补进 task 1.1/1.2 清单和 design.md 修改表。

### F2 [gstack-amendment] · T164 缺机械校验手段

**严重度**：中 · **置信度**：高 · **来源**：Claude CEO + Codex

parity 守卫只保证两份 SKILL 字节相同，不校验引号是否存在。T148 有反漂移锁测试，T164 没有。
建议加一个轻量 grep 断言（task 3 验证步骤新增一条）。

### F3 [gstack-amendment] · T164 威胁模型措辞修正

**严重度**：低 · **置信度**：高 · **来源**：Claude CEO + Codex

proposal/design 里"执行非预期命令"的措辞比实际防护范围更宽——双引号防参数拆分和 glob 展开，
不防命令替换。建议明确只声称"防止空格导致的参数拆分"并注明残留边界。

### F4 · T148 前提叙述精度

**严重度**：低 · **置信度**：中 · **来源**：Codex

Codex 指出：当前 `_parse_mirrors()` 已先以 `unknown-token` 拒绝 `history`，
到不了 `check_fanout_consistency()` 的 count 逻辑。所以 proposal 说的"漏算"
在技术上不精确——更准确说法是"被拒于门外（拿不到真名的合法入场券）"。
建议修正叙述。

## 自动决策登记

- D-auto-1：Codex 建议拆分两项为独立 change → **按项目 fold-vs-defer 准则，改动文件高度重叠，
  维持合一（P3 pragmatic + 项目基准④）**
- D-auto-2：Codex concern 关于 fallback 行 marker 内外不一致 → design.md 已分两表、tasks.md
  已单独列 task 1.4，实际不矛盾，**驳回**
