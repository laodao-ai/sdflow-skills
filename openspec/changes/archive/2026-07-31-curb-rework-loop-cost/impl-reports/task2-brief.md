### Task 2: 熔断硬上限与出票闸门（④⑤⑨③）

**Blocked-by:** none
**R-ID:** IO-2, IO-3, IO-4

在 sdflow-implement SKILL.md 中落地四项循环边界改进：熔断硬上限（④）、出票语法面有界性闸门（⑤）、red-before-green 扩展（⑨）、review package 增量化（③）。

熔断侧：review-loop-breaker 增加判据 (b)——同一文件累计被 Critical/Important 命中 ≥3 轮即熔断（与指纹无关），仲裁命题为「这个门本身该不该存在」。写入 MUST NOT 靠改进指纹算法替代 (b)。声明 (a)(b) 同时命中时 (b) subsume (a)。计数窗口 = 全 change 跨全部 ticket。熔断账本持久化到 impl-reports/breaker-ledger.md（格式 = 轮次|文件|指纹|严重度）。(b) 仲裁 dispatch 的 review package 含该文件 ticket 起点以来累积 diff（不受 ③ 增量限定）。

闸门侧：出票模式增加验收标准的语法面有界性闸门——无界语法面 MUST NOT 写成机械门。判据覆盖伪装形态（「在某格式文件中定位/插入/修改某处」）。标注为指令层约束、非机械保证。

TDD 侧：red-before-green 扩展到「往既有测试补断言或修改既有断言的期望值/判定逻辑」场景。收尾票的既有豁免不受影响。

review package 侧：fix 轮 review package 构造改为只打包「上轮已审 SHA..HEAD」，首轮范围不变。

一致性核对：核对 Tests are code 措辞与 IO-2 spec 表述一致（实现已在 d1aa607，只做核对不重实现）。

- [ ] 熔断规则增加判据 (b) + subsume 声明 + 计数窗口 + 账本持久化 + 仲裁累积 diff
- [ ] 出票语法面有界性闸门（含伪装形态判据 + 非机械保证标注）
- [ ] red-before-green 扩展到补断言/改断言场景
- [ ] review package fix 轮增量化
- [ ] Tests are code 一致性核对

