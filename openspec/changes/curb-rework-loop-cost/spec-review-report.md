---
ship-gate:
  design_approved: true
  reviewed_sha: efd6660e71ba0b76cb52dde1346e68417dea22c6
---

# Spec Review Report · curb-rework-loop-cost

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-05,TG-18,TG-19,TG-22,TG-23" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->

> **评审对象**：`openspec/changes/curb-rework-loop-cost/`（四件套 + decision-memo + adr/0035）
> **命中 TG**：TG-05, TG-18, TG-19, TG-22, TG-23（均非 HR-TG）
> **领域镜**：无（TG-01/02/03 不命中）
> **对抗镜**：2 个（sonnet，fresh context）
> **接地镜**：1 个（haiku，fresh context）
> **outside-voice**：design-voice（exec exit=1 → 同族 fallback，reason_code=exec-error）

---

## 综合 Findings（去重合并后 · 主 session 对抗裁决 · 按严重度排序）

### 需修改（采纳）

**[R-1] 「上轮失败的具体用例」scope 歧义 — 对非 unit 层技术不可行**
- 命中镜：autoplan(Eng) + 对抗镜2 + Codex
- 问题：spec 写「中间轮 = unit 全层 + 上轮失败的具体用例」，同时 Scenario 写「集成与 e2e 不跑」。「上轮失败用例」若含 integration/e2e，与 Scenario 矛盾；且对不透明命令（`make integration`）精确重跑单个用例触碰「无界语法面」。
- 裁决：**采纳**（三路独立命中，文本直读即得矛盾）
- 严重度：High
- 建议：spec 显式限定「上轮失败的具体用例 ⊂ unit 层」，五份文档（proposal/design/adr/decision-memo/spec）统一措辞。
- ✅ **已修正** `[spec-review-amendment]`：proposal/decision-memo/spec/tasks/Scenario 五处统一加「⊂ unit 层」限定。

**[R-2] unit 层缺 quick 时 design.md 通用规则与 spec.md 必跑约束矛盾**
- 命中镜：autoplan(Codex) + 对抗镜2
- 问题：design.md:79 通用规则「缺 quick → 中间轮跳过该层」套到 unit 层 = 中间轮零覆盖。spec.md:19-21 要求 unit 必跑。
- 裁决：**采纳**（两路独立命中，逐字对照即得矛盾）
- 严重度：High
- 建议：spec 声明 unit 层必跑约束优先于通用规则——unit 缺 quick 时中间轮取 full。design.md 通用规则限定为仅适用于集成/e2e。
- ✅ **已修正** `[spec-review-amendment]`：design.md 解析规则加 unit 层例外；spec.md 中间轮条款加「无 quick 则取 full——unit 层 MUST NOT 因缺 quick 档被跳过」。

**[R-3] T1 无可测实现对象 — `test-suites` 解析规则无 runtime parser**
- 命中镜：autoplan(Eng) + Codex
- 问题：task 1.3 要求写单元测试，但仓内无 Python 解析函数。接地镜确认 `config.template.yaml` 中 `test-suites` 键不存在。
- 裁决：**采纳**
- 严重度：High
- 建议：二选一——(a) scope 内新增 `parse_test_suites()` helper 函数并配 pytest 测试；(b) 把 T1 移入「无自动化测试」桶，修正覆盖图声明。推荐 (a)（通则①：消费方是 prose 指令，但在 `sdflow-init/scripts/` 补一个验证函数可让 `config_lint` 机械校验配置形状，收益 > 成本）。
- ✅ **已修正（人拍板 Q-3 → 选 b）** `[spec-review-amendment]`：test-suites 消费方是模型运行时读 config 判断，无 runtime parser。T1 移入「无自动化测试」桶；原 task 1.3（写 parser 测试）改为 sdflow-devenv test-suites 发现能力（prose 任务）。

**[R-4] ③ 与 ④ 未声明的交互 — (b) 仲裁者只看最后一轮增量 diff**
- 命中镜：autoplan(Eng) + 对抗镜1 + 对抗镜2
- 问题：③ 限定 fix 轮 review package 只含本轮增量。④(b) 升档仲裁需看跨轮模式。仲裁者看不到前两轮修复历史。
- 裁决：**采纳**（三路命中，结构性矛盾明确）
- 严重度：High
- 建议：spec 声明 ④(b) 仲裁 dispatch 的 review package 含该文件 ticket 起点以来的累积 diff，不受 ③ 增量限定。(b) 优先于 ③。
- ✅ **已修正** `[spec-review-amendment]`：spec 熔断规则加「(b) 仲裁 dispatch 的 review package 含累积 diff，不受 ③ 增量限定，(b) 优先于 ③」。

**[R-5] 熔断计数无持久化账本要求 — 机制靠「编排器会自己记得」**
- 命中镜：对抗镜1
- 问题：IO-2 的熔断判据要求跨轮「累计」计数，但无处要求把文件命中次数写进 git-tracked 持久化文件。fix 子代理是 fresh context，主 session 压缩后可能丢失计数。
- 裁决：**采纳**（对照 planning-decisions.md、code-review-report.md 都有显式落盘要求，唯独熔断计数没有）
- 严重度：High
- 建议：要求编排层在每轮 fix-review 后追加一行到轻量账本（如 `impl-reports/breaker-ledger.md`），格式 = `轮次|文件|指纹|严重度`。不需要机械门，但支持事后审计。
- ✅ **已修正** `[spec-review-amendment]`：spec 熔断规则加持久化账本条款（`impl-reports/breaker-ledger.md`，git-tracked）。

**[R-6] Success Metric #2 指向不存在的产物**
- 命中镜：autoplan(Eng) + Codex
- 问题：proposal 写「`impl-reports/` 下 `code-review-*-fix<N>.md` 的 N ≤ 1」，但 `sdflow-code-review` 只产出一个 `code-review-report.md`，无 per-round 文件。该 metric 永远 trivially pass。
- 裁决：**采纳**
- 严重度：Medium
- 建议：改为 grep `code-review-report.md` 中的「复审上限已达」标注 + 检查该 change 的 checkpoint commit 中 `impl-review` 标签计数。
- ✅ **已修正** `[spec-review-amendment]`：proposal Success Metric #2 改为 code-review-report.md 标注 + checkpoint 计数。

**[R-7] Goals 措辞「四个控制点均可机械求值、fail-safe」与规格自相矛盾**
- 命中镜：autoplan(Codex) + 对抗镜1
- 问题：design Goals 声称全部可机械求值，但 ⑤⑥ 明确标注为指令层约束、非机械保证。
- 裁决：**采纳**
- 严重度：Medium
- 建议：Goals 改为「四个边界控制点的判据一律**尽可能**由确定信息界定，失效方向为 fail-safe」——删掉「均可机械求值」。
- ✅ **已修正** `[spec-review-amendment]`：design.md Goals 已改。

**[R-8] ⑨ red-before-green 只覆盖「补断言」未覆盖「改断言」**
- 命中镜：design-voice(fallback)
- 问题：⑨ 措辞限定「补一条断言」（新增），但修改既有断言的期望值（如 `assertEqual(x,5)` → `assertTrue(x is not None)`）同样能制造假绿，字面上落在扩展范围外。
- 裁决：**采纳**（成本极低——只需扩宽一个短语）
- 严重度：Medium
- 建议：⑨ 措辞从「补断言」扩到「补断言或修改既有断言的期望值/判定逻辑」。IO-4 spec 同步。
- ✅ **已修正** `[spec-review-amendment]`：proposal ⑨ + spec IO-4 Requirement/Scenario 均扩宽。

**[R-9] (a)(b) 同时触发无优先级声明**
- 命中镜：autoplan(Eng)
- 问题：④ 的 (a) 同指纹 2 轮和 (b) 同文件 3 轮可在第 3 轮同时触发，两个不同范围的仲裁可能同时派出。
- 裁决：**采纳**
- 严重度：Medium
- 建议：spec 声明 (b) subsume (a)，同时命中时只派 (b)。
- ✅ **已修正** `[spec-review-amendment]`：spec 熔断规则加「(a)(b) 同时命中时 (b) subsume (a)」。

**[R-10] 熔断计数窗口（单 ticket / 全 change）未定义**
- 命中镜：对抗镜2
- 问题：「累计」二字未限定统计窗口。同一文件在 ticket A 被命中 2 轮、ticket B 又被命中 2 轮，是否合并？
- 裁决：**采纳**
- 严重度：Medium
- 建议：显式声明计数窗口 = 全 change 生命周期内跨全部 ticket 累计。
- ✅ **已修正** `[spec-review-amendment]`：spec 熔断规则加「计数窗口 = 全 change 生命周期跨全部 ticket」。

**[R-11] `full` 缺配回落 `quick` 使收口轮可能悄悄变窄**
- 命中镜：对抗镜2
- 问题：某层只配 `quick` 无 `full`，收口取 `full` 时静默 fallback 到 `quick`。SHA 锚检通过但实际跑的是缩窄命令。
- 裁决：**采纳**
- 严重度：Medium
- 建议：`full` 缺配时视为未分档（quick=full 同命令），或收口报告显式标注「本层无 full 档，取 quick 替代」。
- ✅ **已修正** `[spec-review-amendment]`：design.md 与 spec.md 统一改为「缺 full 视为未分档（quick=full 同命令）」，消除静默变窄。

### 需拍板（设计门决策）

**[Q-1] 跨文件同根因可绕过 (a)(b) 且无全局硬顶**
- 命中镜：对抗镜1 + CEO + design-voice
- 问题：(a) 靠指纹、(b) 靠文件，但同一根因跨文件轮换可绕过两者并集。且 IO-2 无与文件/指纹都无关的全局轮数硬顶。
- 选项 A：补「该 ticket 累计 fix-review 轮数 ≥ N（如 5）」全局硬顶 → 兜底覆盖全面，但增加一条新判据。
- 选项 B：在 Risks / 接受的边角补一条「跨文件同根因逃逸」并五问定级 → 承认残余风险但不加码。
- 推荐：**B**（通则④简化；跨文件逃逸概率低，且 ①②⑤⑥ 已收窄整体循环成本。三面后果：系统镜 = 残余通道存在但概率极低、用 retro 后验发现更省；用户镜 = 无感知；开发循环镜 = 加全局硬顶增加一个新判据维护面）。

**[Q-2] 聚合套件 fix 循环是否受 review-loop-breaker 管辖**
- 命中镜：对抗镜2
- 问题：收尾票的「测试失败→修→重跑」循环由退出码驱动，review-loop-breaker 由 reviewer findings 驱动，两者是否同一计数轨道 spec 未交代。若脱钩，proposal 引用的 fix 轮 ≥13 的极端案例恰恰不在本 change 治理范围内。
- 选项 A：显式声明收尾票的 fix 循环复用 review-loop-breaker 计数 → 闭合缺口。
- 选项 B：补一条收尾票专属的轮数硬顶（如收尾票 fix 轮 ≤ 5）→ 独立且简单。
- 选项 C：在 Risks 补声明「收尾票的 fix 循环在目标态下应更短（①② 已缩窄每轮范围），暂不加硬顶，观察」→ 最简。
- 推荐：**C**（通则④；收尾票的 fix 循环在 ①② 下每轮只跑 unit，成本已大幅下降。且收尾票经双轴审，Standards 轴的 findings 会触发 review-loop-breaker。三面后果：系统镜 = 理论缺口但①②已收窄影响；用户镜 = 无感知；开发循环镜 = 加硬顶增复杂度、需定义新计数口径）。

**[Q-3] T1 的实现路径选择（新增 parser helper vs 移入无自动化测试桶）**
- 见 R-3 的两个选项。推荐 (a) 新增 helper——但需决策是否扩大 scope。

### 已裁掉（裁决不成立或已被覆盖，保留可审计）

**[X-1] 「收口全量不覆盖 code-review 后盘面」— 降级为已知接受**
- 来源：autoplan(Codex) + Eng
- 裁掉理由：design.md Risks 第 5 条已显式承认此风险（「该锚语义限定为实现期结束时…code-review 之后的修复由其自身保障机制覆盖，此证据时效缺口是已知且接受的残余风险」），且 spec IO-1 最后一段有回指。不是遗漏，是有意选择。

**[X-2] 「⑪ 被推迟但它是唯一能把极端病例归零的措施」— 已有充分理由**
- 来源：CEO
- 裁掉理由：decision-memo D0 已显式记录砍掉理由（blast radius 量级不同），proposal Non-Goals 明确列出，不是遗漏。优先级选择已由人拍板确认。

**[X-3] 「C1 论证超出证据」— 降级为措辞建议**
- 来源：Codex
- 裁掉理由：C1 标题已写「中间 fix 轮的测试结果在设计上就不进最终报告」，这句本身成立。decision-memo 在同条的 ⚠️ 注记已承认早期发现回归价值。论证未超出，只是标题可更精确。不构成设计缺陷。

**[X-4] 阈值校准样本与 ⑤ 病理重叠**
- 来源：CEO
- 裁掉理由：假设 A1 已标注为「启发式」且写了失效影响。⑤ 生效后复核阈值是自然的 retro 检查点，不需要在本 change 提前决策。

**[X-5] quick 命令语义无约束可复活 C6**
- 来源：对抗镜2
- 裁掉理由：quick 的配置由下游消费仓控制，本 change 无法约束下游命令的内容。「quick 应覆盖同一测试总体」是配置指南建议，不是 SKILL 契约能保证的。config.template.yaml 的注释可以加一句提醒，但不构成 spec 级 finding。降级为**实现时在模板注释中加一句提醒**。

**[X-6] 指令层自我证伪（④⑥ 仍是指令层）**
- 来源：CEO + Codex
- 裁掉理由：design.md 已明确写「不为复审轮数新增机械门，机械化留待有确定性捕获路径时再议」，且「诚实边界」明确标注。R-5 已采纳「补审计账本」建议，这比机械门更实际。R-7 已采纳修正 Goals 措辞。两条合起来已覆盖此 concern 的可行部分。

**[X-7] 回滚声明未讨论反向兼容窗口**
- 来源：design-voice
- 裁掉理由：概率极低（需要先 `sdflow-init update` 推了新 config 再 revert 本仓），且 prose 消费方不会硬崩溃。通则④。

**[X-8] 「全部功能票号」定义不精确**
- 来源：对抗镜1
- 裁掉理由：这是 `ship_gate.py` 的实现级细节，本 change 只写 Requirement 语义。实现时需要精确定义，但不影响设计审。降级为 task 2.7 的实现注记。

**[X-9] flaky 判定门槛过低**
- 来源：对抗镜1
- 裁掉理由：flaky 判定是聚合套件发现契约的既有条款（非本 change 新增），本 change 未修改该条款。通则③不加宽。

**[X-10] 全 ticket 语义自扫无交叉校验**
- 来源：对抗镜1
- 裁掉理由：该自扫是出票模式的既有条款（spec-review-amendment M15），本 change 未修改。且双轴审即独立校验。通则③不加宽。

**[X-11] 跨阶段累计不做统一计数**
- 来源：对抗镜2
- 裁掉理由：两个阶段各自独立设计是合理的架构边界。通则④——低概率（需两阶段都命中同文件），代价有界（defer 进 buglist 仍可追溯）。

**[X-12] ①③④⑥ 叠加诊断能力下降**
- 来源：Codex
- 裁掉理由：这是四项改动的已知代价，design Risks 段已隐含。但措辞可以更显式——降级为 R-12 建议在 Risks 补一句。

### 接地镜结果

| # | 项目 | 状态 |
|---|---|---|
| 1 | `:328-330` 单一盘面 | ✅ 一致（实际 328-332） |
| 2 | `:313-322` 聚合套件发现 | ✅ 一致（实际 313-324） |
| 3 | `:270` 出票验收标准 | ✅ 一致 |
| 4 | `:509` red-before-green | ✅ 一致 |
| 5 | `:583` review package | ✅ 一致 |
| 6 | `:651-657` review-loop-breaker | ⚠️ 偏移（实际 654-660） |
| 7 | `:349,353` code-review fix 循环 | ❓ 需实现时核实 |
| 8 | `:616-621` Tests are code | ✅ 一致 |
| 9 | `code-review:181` 无 re-review | ✅ 一致 |
| 10 | `code-review:314-316` reviewed_sha | ✅ 一致 |
| 11 | `code-review:7-8` 一份报告 | ✅ 一致 |
| 12 | `adr/0035` 存在 | ✅ 存在 |
| 13 | `sdflow-devenv/references/` | ✅ 存在（6 文件） |
| 14 | `config.template.yaml` test-suites | ⚠️ 键不存在（确认 task 1.1 为新增） |

**行号偏移建议**：proposal/design 的行号引用在实现时需复核更新（`:651-657` → `:654-660`）。

---

## 决策登记区

### 自动决策（autoplan 广审，默认接受可覆盖）

| ID | 决策 | 理由 |
|---|---|---|
| [自动决策] AD-1 | 接受 D0（8 项范围） | blast radius 量级不同，⑪ 单开合理 |
| [自动决策] AD-2 | 接受 D1（确定信息界定） | fail-safe > fail-open |
| [自动决策] AD-3 | 接受 D2（复审 1 轮硬上限） | 闭合修复无人审缺口 |
| [自动决策] AD-4 | 接受 A1-A3 三条假设 | 启发式可落地后调 |

### 需拍板（设计门一次性过）

| ID | 问题 | 推荐 |
|---|---|---|
| [已拍板] Q-1 | 跨文件同根因逃逸：补全局硬顶(A) vs 记为已知风险(B) | **人拍板 → B**——低概率、①②⑤⑥ 已收窄 |
| [已拍板] Q-2 | 聚合套件 fix 循环管辖：复用 breaker(A) / 专属硬顶(B) / 观察(C) | **人拍板 → C**——①② 已缩窄成本 |
| [已拍板] Q-3 | T1 路径：新增 helper(a) vs 移入无测试桶(b) | **人拍板 → (b)**——消费方是模型运行时，无 runtime parser；devenv 负责发现与写入 |

### 已裁掉（反静默压制 · 原始发现 + 裁掉理由供复核）

见上方 X-1 至 X-12。

---

## Outside Voice 结果

design-voice 站点：exec exit=1 → 同族 fallback（claude 子代理，reason_code=exec-error）。findings=3，已纳入合并池。

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="claude" reason_code="exec-error" findings="3" truncated="false" -->

---

## 收敛建议

**建议进设计 HARD-GATE**。需修改 11 条采纳项（R-1~R-11），3 条需人拍板（Q-1~Q-3），12 条已裁掉可审计。

修改优先级：R-1（歧义消除，影响 5 份文档）、R-2（矛盾消除）、R-3（测试覆盖图诚实性）、R-4/R-5（熔断可行性）最高。R-6~R-11 为措辞/边界明确化，可随实现同步修正。

拍板后进入实现阶段（用户批准 → writing-plans）。

## Lens Metric（pre-gate 草稿值，拍板时最终化）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="13" 采纳="6" 裁掉="5" defer="2" 独立="3" sev="致0/高4/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="14" 采纳="7" 裁掉="5" defer="2" 独立="4" sev="致0/高4/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="1" 采纳="0" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="claude" site="design-voice" findings="3" 采纳="1" 裁掉="1" defer="1" 独立="1" sev="致0/高0/中1/低0" -->
