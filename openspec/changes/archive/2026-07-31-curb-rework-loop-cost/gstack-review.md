# Autoplan 广审报告 · curb-rework-loop-cost

<!-- sdflow:step1-broad-review v1 mode="native" -->

> 佐证：autoplan 经 Skill 机制原生执行，CEO subagent + Eng subagent（Agent tool 前台）+ Codex voice（codex exec）三路真实调用。

## 综合 Findings（去重合并后 · 按严重度排序）

### Critical / High

**[G-1] 「收口全量」不覆盖最终代码盘面 — 收尾票在 code-review 之前执行**
- 来源：Codex #1 + Eng #1（部分重叠）
- 问题：`impl-orchestration` 明定收尾票在 `sdflow-code-review` 之前，code-review Step4 自动修复会改源码，修复后的最终 SHA 从未跑过 full 集成/e2e。设计把兜底交给不扩张职责的 `sdflow-done verify`，不构成测试执行保证。
- 置信：高
- 严重度：Critical
- 建议：spec 应显式说明此时效缺口是「已知且接受的残余风险」（design.md Risks 第 5 条已有，但 spec 的 Requirement 段未回指），或增加「code-review 自动修复后若改动覆盖聚合套件 scope，verify 阶段 SHOULD 复跑一次 full」的弱建议。

**[G-2] T1 没有可测的实现对象 — `test-suites` 解析规则无 runtime parser**
- 来源：Eng #2 + Codex #3（完全重叠）
- 问题：仓内 `test-suites` 的实际消费者是 `sdflow-implement/SKILL.md` 的模型指令，无 Python 函数。task 1.3 要求在 `sdflow-init/tests/` 写单元测试，但没有实现对象。
- 置信：高（grep 核验无 runtime parser）
- 严重度：High
- 建议：要么新增一个可调用的 `parse_test_suites()` 辅助函数（scope 入 task），要么把 T1 移入「无自动化测试」桶并修正覆盖图声明。

**[G-3] 「上轮失败的具体用例」对非 unit 层技术上不可行**
- 来源：Eng #1 + CEO F3-1（部分重叠）
- 问题：spec 写「中间轮 = unit 全层 + 上轮失败的具体用例」，同时 Scenario 写「集成与 e2e 不跑」。但 spec 未明确「上轮失败的具体用例」特指 unit 层内。且对 integration/e2e 这类不透明命令，精确重跑单个用例本身就触碰「无界语法面」问题。
- 置信：高
- 严重度：High
- 建议：spec 中显式限定「上轮失败的具体用例 ⊂ unit 层」。

**[G-4] `test-suites` 缺档语义对 unit 层存在矛盾**
- 来源：Codex #2
- 问题：规则说「中间轮跑 unit 全层（若配了 quick 取 quick）」但同时说「映射缺 quick 视为该层无 quick 档」。若 unit 配了 `{full: pytest}` 而无 quick，中间轮应跑 unit full 还是跳过？两条规则给出相反结果。
- 置信：高
- 严重度：High
- 建议：spec 应明确「unit 层在中间轮 MUST 始终跑——若无 quick 则取 full」，区分 unit（必跑）与 integration/e2e（可推迟到收口）。

**[G-5] ③ 与 ④ 存在未声明的交互 — 硬上限仲裁者只看最后一轮增量 diff**
- 来源：Eng #3
- 问题：③ 限定 fix 轮 review package 只含本轮增量。④(b) 触发时仲裁命题是「这个门本身该不该存在」，需要看跨轮模式。但仲裁者只收到最后一轮的增量 diff，无法看到前两轮的修复历史。
- 置信：高
- 严重度：High
- 建议：明确 ④(b) 升档仲裁的 review package 应含累积 diff 或至少是 ticket 起点以来该文件的全部修改历史，不受 ③ 的增量限定。同时声明 ④(b) 优先于 ③。

**[G-6] 指令层约束的自我证伪 — 本 change 证明了 MUST 会被打折，④⑥ 仍是纯指令层**
- 来源：CEO F1-1 + CEO F6-1 + Codex #6
- 问题：proposal 用「该条款实际未被执行」（37 轮 fix 漏掉 8 个红测）证明问题存在，但 ④⑥ 的解决方案仍是指令层 MUST，无机械门、无审计锚、无何时重新评估的时间锚。design Goals 声称「四个控制点均可机械求值、fail-safe」，但 ⑤⑥ 明确标注为非机械保证。
- 置信：高
- 严重度：High
- 建议：(a) 修正 Goals 措辞为「尽可能由确定信息界定」；(b) 给 ④⑥ 补可 grep 的结构化审计标记（不是机械门，但支持后验复核）；(c) 写一条 retro 时的检查锚点，避免「以后再说」变成「永远不说」。

### Medium

**[G-7] 阈值校准样本与 ⑤ 病理重叠 — ⑤ 生效后阈值可能需要复核**
- 来源：CEO F1-2
- 问题：④ 的阈值 3 由两个「手搓解析器」病例校准，而 ⑤ 正是拦截这类病理的出票闸门。⑤ 生效后，剩余触发 ④ 的病理（真实设计分歧等）的合理阈值从未被验证。
- 置信：中
- 严重度：Medium
- 建议：在假设 A1 中补一句「⑤ 生效后应基于非解析器类病理重新采样复核阈值」。

**[G-8] proposal Success Metric #2 指向不存在的产物**
- 来源：Eng #4 + Codex #5
- 问题：Success Metric 写「`impl-reports/` 下 `code-review-*-fix<N>.md`」，但 `sdflow-code-review` 只产出一个 `code-review-report.md`，不产出 per-round 文件。该 metric 永远 trivially pass。
- 置信：高
- 严重度：Medium（metric 无效但不影响实现正确性）
- 建议：改为 grep `code-review-report.md` 中的「复审上限已达」标注或 checkpoint commit 计数。

**[G-9] 同指纹/硬上限两条触发可同时命中，无优先级声明**
- 来源：Eng #5
- 问题：④ 的 (a) 同指纹 2 轮和 (b) 同文件 3 轮可在第 3 轮同时触发，(a) 的处置是 recover-or-defer，(b) 的处置是升 strong 审「门该不该存在」——两个不同范围的仲裁可能同时派出。
- 置信：中
- 严重度：Medium
- 建议：spec 声明 (b) subsume (a)，同时命中时只派 (b)。

**[G-10] ⑪ 被推迟但它是唯一能把极端病例「归零」的措施**
- 来源：CEO F2-1
- 问题：本 change 的唯一 fix8/37 轮极端案例的直接生成器是本仓手搓 YAML 解析器（⑪），但 ⑪ 被推迟。本 change 交付的是「给失控代价设上限」而非「消除失控根因」。
- 置信：中（战略层面，非技术缺陷）
- 严重度：Medium
- 建议：proposal Non-Goals 或 decision-memo 显式说明此优先级选择的理由（blast radius），并与 ⑫ 的对照表联动说明「⑤⑫ 先行 → ⑪ 补」的顺序依赖。

**[G-11] C1 的论证超出证据 — 中间轮全量对盘面零贡献 ≠ 对早期回归发现零价值**
- 来源：Codex #4
- 问题：C1 的证据锚证明中间轮结果不进最终报告（对盘面零贡献），但 decision-memo 自己承认中间轮有「早期发现回归」的未声明价值。C1 应降格表述。
- 置信：中
- 严重度：Medium
- 建议：C1 标题改为「中间轮全量对最终盘面无贡献」，明确保留「但有早期回归发现价值，该价值由收口全量兜底」。

**[G-12] ①③④⑥ 叠加后诊断能力系统性下降**
- 来源：Codex #9
- 问题：中间轮不跑集成/e2e、review package 只看增量、implement 第 3 轮熔断、code-review 只允许 1 轮复审——四项同时发生时，跨轮/跨层回归更晚暴露且可能被直接 defer。这是有意选择，但 design/proposal 未显式声明。
- 置信：中
- 严重度：Medium
- 建议：Risks 补一条「四项叠加后诊断窗口收窄，defer ≠ 验证通过，是以已知缺陷换取循环上界」。

### Low / Informational

**[G-13] task 2.2 清除「受影响层」grep 的目标在现有代码中不存在**
- 来源：Eng #6
- 问题：grep 目标是 decision-memo 自己过程中产生的候选措辞，不是 production 代码里的存量。grep 会 trivially pass。
- 置信：高
- 严重度：Low（无害，仅标注）
- 建议：task 2.2 改为「写入新条款时 guard against 引入该提法」。

**[G-14] empty-string quick/full 配置值未定义**
- 来源：Eng #7 + Codex #2 partial
- 置信：中
- 严重度：Low
- 建议：按通则④不为此纠结——空命令跑一遍就会 fail-loud，fail-safe。

**[G-15] ⑫ 的受众与本 change 其余七项不同，合并理由偏弱**
- 来源：CEO F6-2
- 置信：低
- 严重度：Low
- 建议：如实标注「主题相关」而非「内聚」。影响极小。

## 自动决策登记（autoplan，按 G2 不弹窗）

| ID | 决策 | 理由 |
|---|---|---|
| AD-1 | 接受 D0（8 项范围） | P3 pragmatic — ⑪ blast radius 确实不同量级 |
| AD-2 | 接受 D1（确定信息界定） | P1 completeness — fail-safe > fail-open |
| AD-3 | 接受 D2（复审 1 轮硬上限） | P5 explicit — 比「一轮即止」更完整（闭合修复无人审缺口） |
| AD-4 | 接受 A1-A3（三条假设） | P6 bias toward action — 启发式可落地后调 |

## Phase 1 (CEO) + Phase 3 (Eng) 双声共识表

```
DUAL VOICES — CONSENSUS TABLE:
═══════════════════════════════════════════════════════════════
  维度                          Claude   Codex   共识
  ─────────────────────────────  ──────   ─────   ────────
  1. 前提是否成立？              部分      部分    DISAGREE(C1/C6 论证超出证据)
  2. 解决的是正确的问题？        是        是      CONFIRMED
  3. 范围校准正确？              是        是      CONFIRMED(⑪推迟合理)
  4. 备选方案是否充分论证？      基本      基本    CONFIRMED(F4-2 论证不自洽 → taste)
  5. 技术方案内部一致？          否        否      DISAGREE(G-1/G-3/G-4/G-5)
  6. 测试覆盖充分？              否        否      DISAGREE(G-2/G-8)
═══════════════════════════════════════════════════════════════
CONFIRMED = 3/6, DISAGREE = 3/6
```

[gstack-amendment]
