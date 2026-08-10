### Task 2: 实修率历史回算

**Blocked-by:** none
**R-ID:** R-WR1

在 `sdflow-retro/scripts/retro_report.py` 新增实修率回算（聚合④段），从归档报告 finding 行机械提取 fix-status 与 lens 归属。

行为描述：
- 真语料试算前置：先用一次性脚本对归档报告跑窄文法（fix-status 三态 + 有界记号 lens 匹配），产出 per-(layer,lens) 可判定数预估，密度结论写进 impl 记录后再进正式实现
- fix-status 三态判定：精确 needle `已修[impl-review-fix]` → 实修；含 defer 类标注 → defer；含 `impl-review-fix` 裸串或处置动词但不命中精确 needle → 未知桶（MUST NOT 判未修）；无任何处置信号 → 未修
- 封闭 lens 关键词表（LENS_ENUM 同源六值映射 + `域` 别名）：只在有界来源记号内匹配（表格行「来源」列或 `〔…〕`/`【…】` 标签），MUST NOT 全行子串匹配；0 或多命中 → 未知桶
- 复用 `lens_metric_aggregate.py` 的 `_fence_aware_lines` 滤围栏示范锚，不改该模块任何既有函数签名
- 聚合④段渲染：per-(layer,lens) 实修数/可判定/未知/覆盖率/实修率 + 阈值 5 单一源常量（<5 标「参考」）+ change 边界修复 commit 佐证 flag（不参与判定）
- 测试（`sdflow-retro/scripts/tests/`）：合成语料用例（可判定/lens 歧义/零命中/围栏内示范锚不入计/fix-status 变体/自由文本关键词不构成归属）+ 真仓再生冒烟（聚合④在场、13 面待复评镜实修率或「参考」可读）

- [ ] 真语料试算前置：一次性脚本跑窄文法密度预估，结论写进 impl 记录
- [ ] 窄文法提取函数（fix-status 三态 + lens 有界匹配）
- [ ] 聚合④段渲染（实修率表 + 阈值 + 佐证 flag）
- [ ] 测试：合成语料单元 + 真仓再生冒烟

