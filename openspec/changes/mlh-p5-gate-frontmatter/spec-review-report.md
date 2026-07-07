# spec-review 报告 — mlh-p5-gate-frontmatter

## 命中范围
- **栈**：Python 门禁脚本（ship_gate.py）+ Markdown SKILL（三 producer）+ pytest。不命中 backend·go / embedded / frontend 领域清单（纯机械层）。
- **镜**：领域镜（base R 项）×1 · 对抗镜 ×3（隐藏假设/失败模式/乐观估计）· 接地镜 ×1 · 跨模型 outside-voice ×2（design-voice + hr-tg，codex v1.0.0）· broad（autoplan-adapted，见 gstack-review.md）。
- **HR-TG 判定**：命中 TG-04（承载形态迁移 v_old/v_new）+ TG-08（fail-closed 失败模式表），二者 ∈ HR-TG 子集 → 单开 hr-tg cross-model。
  <!-- sdflow:hr-tg v1 hit="TG-04,TG-08" evidence="ship-gate 锚 inline→frontmatter 承载迁移(TG-04) + 坏frontmatter fail-closed 失败模式表(TG-08)，门禁误判难回退" -->

## Step1 broad + outside-voice 锚（详见 gstack-review.md）
<!-- sdflow:step1-broad-review v1 mode="adapted" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="none" findings="5" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="none" findings="3" truncated="false" -->

## 综述
冷审兑现 load-bearing：grill 后四件套仍被多镜挖出 **1 致命 + 3 高 + 多中**真缺陷，收敛度极高（同一爆点常 3-4 镜独立命中）。接地镜**全核实✓零不符**（88 文件/168 锚行、所有函数/常量/分流逻辑精确对上）——设计的代码事实扎实，但**迁移影响面被系统性低估**（尤其 live inline 读点数量、退出码契约、测试盘面）。全部 findings 经对抗裁决**均成立采纳**（无裁掉——对抗镜本就找爆点，接地镜确认了 F1 簇的代码事实），差别在严重度与落点。

---

## 决策登记区

```
┌─────────────────────────────────────────────────────────────────┐
│ [自动决策] D1  致命簇：live inline 读点不止 anchors_in（4+读点）    │  强收敛→采纳
│ [自动决策] D2  高：手写解析器须只认文件首行 --- 块（正文横线密布）   │  强收敛→采纳
│ [自动决策] D3  高：坏≠无语义空档 + 坏输入→退出码映射未定义         │  强收敛→采纳
│ [自动决策] D4  高：归档 frontmatter 读须共用严格核心 + 坏优先级     │  收敛→采纳
│ [自动决策] D5  中：D5「门禁语义不变」措辞订正（冲突承载已变）        │  采纳
│ [自动决策] D6  中：测试迁移盘面漏 8 个 gate 测试文件               │  采纳
│ [自动决策] D7  中：proposal/design safe_load 残留摇摆清理          │  机械订正
│ [自动决策] D8  中：三 producer 模板改动量拆细 + 字段名防漂移        │  采纳
│ [自动决策] D9  中：D2 拍板回写「末尾」vs frontmatter「文件头」冲突   │  采纳
│ [自动决策] D10 中：自指 dogfood 序陷阱（自身报告退役后读不出）      │  采纳
│ [自动决策] D11 中：anchor_set 熔断 helper 漏迁（并入 D1 读点集合）  │  采纳
│ [自动决策] D12 低中：fail-closed 可观测性（reason 点名缺陷字段）    │  采纳
│ [自动决策] D13 低中：88 硬编码脆裂 → 测试基于行为非计数           │  采纳
│ [需拍板]  Q1  归档「好frontmatter+残留inline FAIL」是否交叉一致检查 │  设计门定
│ [需拍板]  Q2  openspec validate/archive 对 report frontmatter 兼容 │  P0 决策门，动手前实测
│ [已裁掉]  （无）——全部 findings 经对抗裁决成立                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 裁决台账（13 合并簇）

### D1【致命】live inline 读点不止 `anchors_in`——只退役它会让迁移后 verify/code-review 静默失效
- **命中镜**：对抗A F1 + hr-tg#1 + 领域F4/对抗C F1（测试面佐证）。接地镜确认代码事实。
- **真相**：live 报告三类结论读点 = `anchors_in`(design-approved, ship_gate.py:506) + **`pick_exclusive`×3**(verify 早检:519/终门:588、code-review:563) + peek `anchors_in`(576) + **`anchor_set`熔断 helper**(250, sdflow-ship 熔断判据)。design D4/spec 只说「退役 anchors_in 的 live 半场」——若照此执行，`pick_exclusive` 继续对 live 读 inline → 迁移后 sdflow-done 写 `verify: PASS` 进 frontmatter 丢 inline → `pick_exclusive` 读不到 → 返回 None → **STEP_IN_PROGRESS 永卡、无法 SHIPPED**（3 类迁 2 类静默失效）；`anchor_set` 熔断也会把「已写有效 frontmatter」误判无进展。
- **裁决**：**采纳（致命）**。design/spec 的「退役边界」与「live 读点」MUST 显式枚举完整集合（anchors_in-design + pick_exclusive×3 + peek + anchor_set），全部纳入 frontmatter 化范围；tasks 起手先做「live 结论读点清单」。

### D2【高】手写解析器 MUST 只认文件第 1 行 `---` 起的唯一首块——否则正文横线复活 B4/B5
- **命中镜**：对抗A F3 + 对抗B F1 + 对抗B F6(BOM/CRLF) + codex-design#3 + hr-tg#2。
- **真相**：报告正文 `---` markdown 横线密布（实测归档 verify-report 正文 1-4 处、spec-review-report 第 5-6 行即 `---`）。松散「找首个---找下个---」会把正文横线块当 frontmatter → 若其中含 `ship-gate:` 即复活 B4/B5，且 YAML 块解析不再走 `_line_scoped_hits`，fence-aware 也救不了（**击穿本 change 立论**）。
- **裁决**：**采纳（高）**。spec/design/G4 补 MUST：frontmatter 仅识别文件第 1 行 `---`（去 BOM）起、到下一 `---` 止的唯一首块；正文任何 `---`/`ship-gate:` MUST NOT 参与；MUST 用 `splitlines()` 口径。补 pytest 负例（正文含 4 处横线的旧报告 + body 注入 `ship-gate: verify: PASS`）。G4 攻击面补 BOM/CRLF/空标量/嵌套>1层/内嵌---。

### D3【高】「坏≠无」语义空档 + 坏输入→退出码映射未定义（fail-closed 退化 fail-open）
- **命中镜**：对抗A F2 + 对抗B F2 + 对抗C F3 + 领域F3 + codex-design#1。
- **真相**：①过渡期回退规则只定义「无 ship-gate 键→回退 inline」，**坏 frontmatter（键在值坏）既非无键也非有效**——若实现把「解析不出有效值」等同「无键」→ 回退 inline 读正文 mention → **design-approved 假过门**。②「fail-closed 判无有效状态」重载了 exit 0(STEP_IN_PROGRESS)/exit 3(REFUSE)/exit 6(UNKNOWN) 三个退出码（spec 写「停下报告点名**或**判该步进行中」），未消歧。exit 0 会让 LLM 反复写坏 frontmatter 成死循环。
- **裁决**：**采纳（高）**。spec MUST：①过渡期回退**只**由「顶层无 ship-gate 键」触发，**解析失败/坏键永不回退、直接 fail-closed**（三分支：有效键→用之 / 键缺席→回退inline / 键存在但坏→fail-closed）。②补「(报告类型 × 坏法)→verdict/exit」映射表：越域/重复键/坏语法/类型不符 → UNKNOWN(6)；纯缺字段(半成品) → 既有无锚语义（spec-review REFUSE 3 / verify·cr STEP_IN_PROGRESS 0）。消除「或」，测试按分支分别断言退出码。

### D4【高】归档 frontmatter 读 MUST 共用同一严格解析核心 + 坏优先级
- **命中镜**：对抗B F3 + 对抗B F4 + hr-tg#3 + codex-design#1。
- **真相**：D4 说归档新增 frontmatter 读，但没要求它与 live frontmatter 读**共用同一严格核心**（重复键→conflict、越域→fail-safe none）。若归档 frontmatter 读写成简易「grep verify: 取值」，迁移后新归档的重复键/越域不判 conflict → D3 短路对 garbled 新归档判 pass → **假 SHIPPED**。且「frontmatter 优先→回退 inline」在「坏 frontmatter+好 inline」盘面未定义（吞掉 inline FAIL 冲突丢失现有保护）。
- **裁决**：**采纳（高）**。spec MUST：新增单一自持 helper（如 `parse_ship_gate_frontmatter_text(text)`），live 文件读与 `git show` 归档文本读**都调它**（复刻现 `_line_scoped_hits` 被两路共用的纪律，防漂移）；归档 frontmatter 坏→fail-safe none（MUST NOT 回退 inline 掩盖）。**Q1（需拍板）**：好 frontmatter=PASS + 残留 inline=FAIL 是否仍交叉检查 inline 冲突——设计门定（不做则登记「已知不覆盖」盲区）。

### D5【中】D5「门禁语义不变」措辞订正——冲突判定承载已从行级并存变重复键
- **命中镜**：对抗A F4 + 对抗B F5。
- **真相**：现 UNKNOWN 冲突依赖「同报告 PASS+FAIL 两条 inline 锚行级并存」（pick_exclusive:289）。frontmatter 单 `verify:` 键**物理上只能持一个值**，「并存冲突」除「重复键」外无法产生。D5 宣称「UNKNOWN 冲突判定不变」不准——语义载体已从行级并存退化为重复键（spec 自己在归档 fence Scenario 承认「live 冲突由 frontmatter 重复键处理」）。
- **裁决**：**采纳（中）**。D5 措辞订正：冲突判定**触发承载**从行级并存改为重复键，等价性仅「歧义即不放行」层成立；把「重复 verify/code_review/顶层 ship-gate 键 → UNKNOWN」提为**独立 MUST Scenario**（块内枚举全部同名键计数，非见第二个即覆盖），补专门重复键 pytest（键分散/键间夹注释/跨缩进干扰形）。

### D6【中】测试迁移盘面漏 8 个 gate 测试文件（~45 处 live inline fixture）
- **命中镜**：领域F4 + 对抗C F1。
- **真相**：tasks 4.1 只列 2 文件，且 `test_producer_parser_contract.py` **0 处 ship-gate 锚**（测 checkpoint TAG_RE，错配）。实际持 live inline fixture 的 8 个文件：test_gate_freshness(10)/tail(8)/anchor_scope(6)/terminal(5)/breaker(5)/anchor_contract(5)/preflight(4)/impl_progress(2)。退役 live inline 读（5.1）后集体 REFUSE/STEP_IN_PROGRESS 回归；且各文件混 live(须迁)/归档(留 inline) fixture，无分流指引。
- **裁决**：**采纳（中）**。tasks 4.1 改「审计全部 8 个 test_gate_* 文件，逐 fixture 标 live→迁frontmatter/归档→留inline」，移除错配的 test_producer_parser_contract.py，迁移前后 fixture 计数作退役 DoD。

### D7【中】proposal/design safe_load 残留摇摆清理（D3 已决手写 stdlib）
- **命中镜**：codex-design#5 + 领域F1 + 领域F2。
- **真相**：proposal.md:19（Modified Capabilities）残留「gate 解析改 safe_load」，与 D3 终态（手写 stdlib，MUST NOT import yaml）直接冲突；design v_old/v_new 对照表 live 列、失败模式表、Mitigation 多处仍「倾向/若选」摇摆语气，把已否决 safe_load 与选定方案并列。
- **裁决**：**采纳（机械订正）**。proposal.md:19 改手写 stdlib；design 三处清「倾向/若选」，safe_load 标「已否决存档」。契约测试加 `assert "import yaml" not in ship_gate.py 源码`。

### D8【中】三 producer 模板改动量拆细 + 字段名防 `code_review`/`code-review` 漂移
- **命中镜**：对抗C F6 + 对抗B F7 + codex-design#2。
- **真相**：tasks 3.1-3.3 把迁移写成一行，但每 producer 模板结构复杂：spec-review〔SR-M〕lens-metric 锚「与 ship-gate 拍板锚同步写入」交叉引用（而 Non-Goals 不迁 lens-metric，拍板须在头 frontmatter + 正文注释两处各写）；done「结论行下方紧跟锚」、cr「结论区末行锚」都要拆头/身；ship_gate docstring 契约块 + test_anchor_contract「双向钉死」两侧都改。字段名 `code_review`(下划线) vs 锚字面 `code-review`(连字符) 易串味。
- **裁决**：**采纳（中）**。tasks 3.x 每 producer 拆子任务（头 frontmatter 写入 + 正文保留人读结论行 + 交叉引用更新[尤其 SR-M] + docstring 契约双向钉死同步）；契约测试断言精确字段名（下划线）+ 枚举值防漂移；producer 模板与其契约断言**同 commit**。codex#2：D2 schema 示例拆三个「有效报告」单示例 + 负例（verify-report 同含 verify+design_approved 必须无效不回退）。

### D9【中】D2 拍板回写「末尾」vs frontmatter「文件头」结构冲突
- **命中镜**：对抗C F2。
- **真相**：现协议「拍板后锚写报告末尾」（spec-review SKILL.md:108），frontmatter 必须文件第 1 行。报告已成体（决策区+findings+lens-metric 多百行），拍板在 HARD-GATE 后 → 迁 frontmatter 意味着 **prepend/merge YAML 到文件头**（非追加一行）。
- **裁决**：**采纳（中）**。design 明确 frontmatter 写入 = 文件头 prepend（无既有 frontmatter）或 merge（有 title/date frontmatter 则往其加 ship-gate 键）语义；tasks 对应 producer 子任务写明此操作。

### D10【中】自指 dogfood 序陷阱 + skill symlink 即时生效中途窗口
- **命中镜**：对抗C F4。
- **真相**：mlh-p5 自身 spec-review-report（即本报告）现用旧 inline 拍板；退役后 gate 只读 live frontmatter → task 5.3 dogfood 自测会 REFUSE_START on itself（读不到自己 design-approved）。且 skill 全局 symlink 即时生效，改 sdflow-done/ship_gate 中途窗口波及并发 /sdflow-done。
- **裁决**：**采纳（中）**。tasks 5.3 加「把 mlh-p5 自身 spec-review-report 的 inline 锚迁 frontmatter」（合法迁移收尾，非越权补锚）；Migration Plan 补 skill symlink 即时生效的中途窗口纪律（先落 gate dual-read commit + 本地 setup 生效，再改 producer）。

### D11【中】anchor_set 熔断 helper 漏迁 → 并入 D1 读点集合
- **命中镜**：hr-tg#1。**裁决**：**采纳**，并入 D1 的 live 读点完整集合；tasks 补 `anchor_set` 迁「状态集合」解析 + 更新 sdflow-ship/SKILL.md 熔断文案 + `test_gate_breaker.py` 用例（before 无状态、after 仅 frontmatter PASS → 判有进展）。

### D12【低-中】fail-closed 可观测性——reason 串须点名具体缺陷字段/类别
- **命中镜**：领域F5。**裁决**：**采纳**。spec 补 MUST：fail-closed 的 `emit()` reason 携带被拒字段名 + 失败类别（语法/越域/重复键/类型），加测试断言 reason 含缺陷标识（adr/0006「可观测」落地）。

### D13【低-中】88 硬编码脆裂 → 测试基于行为
- **命中镜**：对抗C F5。**裁决**：**采纳**。tasks 4.2 测试基于行为（构造 inline-archived fixture 断言识别 + SHIPPED 不回归），MUST NOT 硬编码 88/168 或对真实 archive/ 全量计数；design「88」降为叙述性背景，从 Success Metric 断言语义移除（保留为核实落定的一次性数字）。

### Q2【需拍板·P0 决策门】openspec validate/archive 对 report ship-gate frontmatter 键兼容性
- **命中镜**：对抗A F6 + 领域F6 + 对抗C F2。
- **真相**：归档走 `openspec archive` CLI（禁手动 mv）。若 openspec CLI validate/archive 解析 report 的 frontmatter 并对未知 `ship-gate:` 键报错，迁移在归档步炸。风险实际偏低（validate 只吃 proposal/tasks/specs，report 非校验对象——接地/领域均判低风险），但未实测。
- **裁决**：**采纳**——tasks 1.1 从「核」**升为 P0 决策门**：动手写任何 producer 前，实测 `openspec validate`/`archive` 对带 `ship-gate:` frontmatter 的样例报告，拿 GO/NO-GO 再迁。

---

## 度量锚（lens-metric，config metrics.enabled=true）
> 数值一致性（findings/采纳/独立与合并池实收）是主 session 信任边界、非机械可验；采纳数为设计门拍板前临时裁决，拍板回写时最终化（SR-M）。

<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="autoplan-adapted" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" runner="claude" site="none" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="2" sev="致0/高0/中3/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="none" findings="19" 采纳="19" 裁掉="0" defer="0" 独立="7" sev="致1/高5/中9/低4" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="none" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="2" sev="致0/高1/中4/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="hr-tg" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="1" sev="致0/高2/中1/低0" -->

---

## 结论
- 全部 13 簇裁决**采纳**为 [spec-review-amendment]，应用到 proposal/design/specs/tasks（D1-D4 核心 MUST 进 specs，D5-D13 分落）。Q1/Q2 需人设计门确认（Q2 为 P0 动手前决策门）。
- 冷审拦下 1 致命（D1 迁移后 2/3 结论静默失效）+ 3 高，若未审直接实现会严重翻车——**冷审 load-bearing 再次兑现**。
- 建议：应用 amendment 后**进设计 HARD-GATE**，人工过本报告拍板 → 拍板回写 frontmatter 时代前用现行 inline 协议（`<!-- ship-gate: design-approved -->`，见下），批准后 → /sdflow-ship 续跑（plan → impl → code-review → done）。

<!-- 设计门拍板后由主 session 在此追加：ship-gate: design-approved 锚（当前 inline 协议，mlh-p5 自身迁移收尾时再转 frontmatter，见 D10） -->
