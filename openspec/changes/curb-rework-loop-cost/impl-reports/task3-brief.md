### Task 3: 代码审复审边界与文档分叉消除（⑥）

**Blocked-by:** 2
**R-ID:** SW-1

在 sdflow-code-review SKILL.md 中新增复审边界规定，并消除与 sdflow-implement 的文档分叉。

复审边界：自动修复后 MUST 复审一轮（只审修复 diff、不重审全量）；仍有 Critical/Important → 不再自发第三轮，全部 defer 进 buglist 并在报告标注「复审上限已达」；无自动修复时不触发复审。硬上限 1 轮。

文档分叉消除：改写 sdflow-code-review SKILL.md 对比表右列措辞，与 sdflow-implement 统一为「存在复审循环，硬上限 1 轮」。全仓 grep 核验不再存在「无 re-review 紧闭环」类相反表述。

依赖 Task 2 的理由：消除文档分叉要求 sdflow-implement 侧的措辞已先落地（Task 2 落地熔断与 fix 循环相关条款），否则两侧对齐的目标措辞尚不确定。

- [ ] sdflow-code-review 新增复审边界规定（一轮、只审修复 diff、硬上限 1、残差 defer + 标注）
- [ ] 对比表右列措辞对齐（统一为「存在复审循环，硬上限 1 轮」）
- [ ] 全仓 grep 确认无「无 re-review 紧闭环」残存表述

