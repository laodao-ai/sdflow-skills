---
change: mlh-p4-maintain-scan
layer: spec-review
mirrors: 6
verdict: 需重审设计（多 HIGH，核心机制受挑战）
---

# spec-review-report · mlh-p4-maintain-scan

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="只读报告工具，无运行期爆炸/数据损坏/安全泄漏面，命中∩HR-TG=∅" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="claude-fallback" reason_code="exec-error" findings="6" truncated="false" -->

> **Step1 广审 scope 诚实注**：本 change 为 ~200 行内部 Python 工具（无 UI 面、无产品/战略面、premise 已由 grill 深挖）。按 autoplan 自身条件跳过（无 UI→跳 Design；内部机械工具→CEO premise 归 grill 覆盖），Step1 聚焦**载重相位 = Eng 双声**：codex 跨家族 design-voice（**撞使用限额 exit 1 → 回落 claude-fallback**，跨家族独立性本轮丢失、fresh-context 补偿）+ Claude 冷 eng 子代理。非全四相位 autoplan。
> **串行纪律注（T20）**：Step1 广审此处只收集 findings、Step2 前未落任何 amendment，故 Step2 五镜与广审审**同一份 design 快照**，无遗漏 amendment 之虞。

## 一览

6 冷镜（broad-eng / outside-voice-fallback / domain-base / 对抗×2 / grounding）并行审同一快照，**39 条原始 finding 去重合并为 15 条、全部采纳、0 裁掉**（多镜纪律好、收敛高，无假发现可裁）。**3 条 HIGH（含 1 致）多镜独立命中**，直指 grill 四修正的**相邻未治面**——这是一次典型「点驱动修补留下相邻面」（grill 焊了「跳托管块 / fail-closed 方向」两个点，冷审揪出「怎么算一个条目 / 怎么匹配 marker / 怎么真堵少读 / R2 口径 / 文案漂移」整片相邻面）。

**结论：设计需在实现前重审**——核心反静默机制（H2）被证结构性不达、marker 处理（H1）照字面实现会炸 dogfood。已把机械可改的 12 条落 `[spec-review-amendment]`，2 条 ≥方案决策进登记区待设计门拍板。

---

## 决策登记区

```
┌──────────────────────────────────────────────────────────────────────┐
│ [需拍板] Q1  H2「少读→假一致」怎么堵：≥2 方案，反转 grill D2 的 N 对账否决  │
│ [需拍板] Q2  H1 后 R-guard 结构：token 子串取代 MARK_IDX 守卫（推荐直接采）  │
│ [自动决策] D1..D12  机械可改的 12 条已落 amendment（见下），默认接受         │
│ [已裁掉] （空）——6 镜 39→15 条全部采纳，无假发现可裁；2 条低概率项保留非裁   │
└──────────────────────────────────────────────────────────────────────┘
```

### [需拍板] Q1 — H2:「少读→假一致」的堵法（反转 grill D2 对 N 对账的否决）

**问题（4 镜收敛：对抗/outside-voice/domain/broad）**：grill A4 把 fail-closed 重锚到「结构不可信→防假一致」，但**「少读」（坏链接/微畸形行被解析器跳过）没有正向信号可 fail**——一个 fails-entry-regex 的行与普通散文行不可区分，解析器无从知道「这行本该是条目」。骨架校验只抓整段丢失，抓不到逐行少读。而少读→漏报「已删未清理」→报「一致」正是 adr/0016 §2 亲口点名的假绿。**grill D2 恰恰否决了唯一能堵此洞的机制（机器锚行「共 N 条」对账），理由「过度设计」——该否决即漏洞。**

| | 选项 A（推荐）严格逐行 + 链接路径 join | 选项 B 机器锚行 N 对账 |
|---|---|---|
| 机制 | ①「已列条目」= 托管块外、链接目标匹配 `specs/*/spec.md`\|`rules/*.md` 的行（对 pipe/cell 畸形鲁棒，顺带堵 H3）；② 表体内 `\|` 起头但解析不出合法条目的行 → **fail-closed**（把「少读」变响亮 fail） | INDEX 放机器锚行声明「共 N 条」，解析数 vs 声明数对账，不等→fail |
| 反转 grill | 部分——不需 N 声明，靠「每 `\|` 行必解析或 fail」达同效 | 直接反转 D2 否决 |
| 代价 | 无需改 INDEX 格式；解析器需严格模式 | 需 producer（谁写 INDEX?）维护 N 声明——又一处易漂锚 |
| 三面后果 | 系统:真堵少读；用户:偶发合法但非条目的 `\|` 行需白名单；开发:实现明确 | 系统:堵少读；用户:INDEX 多一行机器锚；开发:多一个 producer 契约 |

**推荐 A**（主次：**开发循环镜主导**——A 不新增 producer 契约/不改 INDEX 格式，把「防少读」收敛成解析器内可机验的「每表体 `|` 行必解析或 fail」，比 B 的「再养一个 N 声明锚」少一处漂移源）。设计门须**自觉反转 grill D2 的「N 对账=过度设计」结论**——冷审证明它不是过度设计，是核心目的的唯一达成机制（A 是其等效轻量形态）。

### [需拍板] Q2 — H1 后 R-guard 结构（推荐直接采 token，无真正分歧）

**问题（5 镜收敛：对抗×2/broad/grounding + 字节实测）**：spec/design/adr 通篇写裸短形 marker `<!-- opsx-init:rules:start -->`，但真实 `init.MARK_IDX[0]` 是**带中文尾注的长形** `<!-- opsx-init:rules:start —— 由 sdflow-init 维护，勿手改本区块 -->`（init.py:45，真 INDEX.md:5 同）。字节实测**裸串非真 INDEX 行子串**。而 init 自己定位托管块**从不用全串**——按 token `start.split()[1]` = `opsx-init:rules:start` 逐行 `token in line` 匹配（init.py:100-107），对尾注鲁棒。test_init.py:381 证野外消费仓存在旧 marker 文案。

- **照 spec 字面（裸串精确/全串）实现** → START 永不匹配 → 只配到 end → D7「不配对→fail-closed」→ **每个 init 托管的真实仓 + 本仓 dogfood 8.2 直接假红不可用**；
- **而一致性守卫是绿的**（两副本 MARK_IDX 都是当前全串）→ 守卫给假信心（护常量不护匹配逻辑），tmp fixture 永不覆盖遗留态。

**推荐（无真正分歧，可直接采为 amendment）**：maintain 托管块定位**镜像 init 的 token 语义**（稳定子串 `opsx-init:rules:start`/`:end`），**删除 MARK_IDX 全串一致性守卫**（token 是文档化稳定契约、比整行注释串稳），改为断言「maintain token == init.MARK_IDX[0].split()[1]」；并加**端到端 fixture 守卫**（喂本仓真实 INDEX.md 验托管块被识别+跳过，护匹配逻辑）。RULE_MARKERS 无稳定子串替身、守卫保留。已按此落 D3 amendment（见下），列 Q2 供设计门确认「删 MARK_IDX 守卫」这一结构变更。

---

## Findings（按收敛度 · 6 镜合并去重）

> 反静默压制：无 finding 被静默丢弃；低概率项（M8 托管块内误置、M2 齐漂）保留为采纳、非裁掉。

### HIGH

**H1〔致〕marker 用全串而非 token → 消费仓 + dogfood 8.2 fail-closed 假红，守卫假绿**
命中：对抗①F2 / 对抗②F1 / broad-eng F2·F4 / grounding #2（5 镜）。证据 init.py:45/100-107、test_init.py:381、INDEX.md:5 字节实测、archive rebrand-F1 同坑。→ **amendment D3**（token 化 + 删 MARK_IDX 守卫 + 端到端 fixture）+ 登记 Q2。

**H2〔高〕fail-closed 防假一致 结构性不达（少读无正向信号）**
命中：对抗①F1 / outside-voice F1 / domain F2 / broad-eng F3（4 镜）。证据 design.md:33 否决 N 对账、adr/0016:19-23。→ **登记 Q1**（≥2 方案，反转 grill D2）。

**H3〔高〕join-key 未定 → retro-report 本仓 dogfood 假阳**
命中：对抗①F3 / outside-voice F2 / broad-eng F1（3 镜）。证据 INDEX.md:34 `retro-report`→`retro/report.md`（非 specs/rules），FS 6 specs vs INDEX 7 条目。→ **amendment D1**（链接路径 join + 排除非 specs/rules 行 + dogfood scenario）。

### MEDIUM

**M1 R2「CLAUDE.md 过时引用」检测启发式完全未定义**（outside-voice F3 / domain F3 / broad 补充，3 镜）——本仓 CLAUDE.md 泛指路径/占位符 `{name}`/code-fence 提及会误报，同 gate 子串 dogfood 自指坑。grill 全跳过 R2。→ **amendment D4**（界定匹配契约 + 跳 fence/占位符 + 误报负例）。

**M2 一致性守卫自身假绿面**（outside-voice F4 / 对抗②angle1）——import-skip 真空 vs collect-error、「常量相等」≠「解析器真用」、副本齐漂。→ **amendment D5**（导入失败 hard-fail 非 skip + 端到端行为测；H1 的 token 化已消 MARK_IDX 守卫半场）。

**M3 文案/checkpoint 第三漂移点无守卫**（对抗②F2 / broad-eng F5）——stale_shadow_warnings 告警文案 + checkpoint 孤儿路径抄进 maintain，R-guard 只守两常量。grill 焊常量漏文案（点驱动修补残渣）。→ **amendment D6**（显式 defer 登记，对齐 bash 第 3 份；文案不强守，避免脆）。

**M4 「代码路径缺失」第三类被无声删除（行为回归）**（domain F1 独立）——现行 SKILL 步骤 2-3 有该类，新 R1 只保 2 类，违反 Success Metric「不回归」。→ **amendment D7**（显式 Non-Goal + 修 Success Metric 措辞；本仓无该表、消费仓罕见，判 YAGNI 退役）。

**M5 边界失败模式缺失**（domain F4 独立）——CLAUDE.md/workflow//hack/ 缺失未规定。→ **amendment D8**（补失败模式行，统一「缺失=空集 benign / 存在不可读=fatal」）。

**M6 数据类化分类文档连带**（outside-voice F5 / 对抗②F3）——tasks 7.3 只改一处，漏 CLAUDE.md「两类 skill」枚举 + README:29-30。→ **amendment D9**（tasks 7.3 扩三处）。

**M7 fence 盲区继承 + 升级为硬 fail**（对抗②F4 / 对抗①F5）——init 容忍畸形 marker（取首块），maintain 却「不配对→硬 fail」，本仓是 marker 示例雷区。→ **amendment D10**（marker 检测 fence-aware + 解析范围严格限 INDEX.md，CLAUDE.md 扫描只匹路径不匹 marker）。

**M8 托管块内误置真 spec = 无人区静默**（对抗①F4 独立，低概率）——maintain 整段跳、init 不审非 bundle 内容。→ **amendment D11**（跳块时若块内探到 specs/*/spec.md 模式→告警，低成本堵盲区）。

### LOW

- **L1** D2/D4/D7 属 TG-23 缺三镜主次判定（domain F5）→ **D12**：给 D4 补主次一句。
- **L2** design 说 resolve-workflow.sh:46 第 3 份副本，实为行 40-42/70-72、:46 是告警 echo、内联非具名常量（grounding #3）→ **D12** 顺带订正行号。
- **L3** 只读断言宜「快照对比无新增 diff」非「git status 绝对干净」（outside-voice low）→ **D12** 修 spec 6.3 措辞。
- **L4** 守卫 test 对 sdflow-init 有硬 collect-time 依赖，缺席→ModuleNotFoundError 非 graceful（对抗②angle1 low）→ **D5** 内 defer 记（importorskip 兜底）。

---

## lens-metric 度量锚

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="9" 采纳="9" 裁掉="0" defer="0" 独立="3" sev="致1/高2/中5/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="0" sev="致1/高2/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" runner="claude" site="—" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="3" sev="致0/高1/中3/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="1" sev="致1/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="claude-fallback" site="design-voice" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="1" sev="致0/高2/中3/低1" -->

> 残余信任边界声明：分类正确性 / roster 完备性 / findings 誊写准确仍是主 session 信任边界，emitter 只保证给定输入的确定性归约。度量只落锚不聚合、不复评、不砍镜——跨 change 聚合由 `/sdflow-retro` 人决。

## 收敛口

**不建议直接进设计 HARD-GATE 批准原设计**——H1/H2/H3 三条 HIGH（含致）证明原设计照字面实现会炸 dogfood（H1）、核心反静默目的结构性不达（H2）。已落 12 条 `[spec-review-amendment]` 修正机械面；**Q1（少读堵法，反转 grill D2）+ Q2（删 MARK_IDX 守卫）两个决策需设计门拍板**。建议设计门先过 Q1/Q2，amendment 落定后**对 H1/H2 两处核心机制补一轮轻 grill 或接地复核**再批准实现。
