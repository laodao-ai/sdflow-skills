---
ship-gate:
  design_approved: true
---
# spec-review-report — done-roadmap-writeback（第三轮·最小核）

<!-- sdflow:step1-broad-review v1 mode="simulated" -->

> Step1 广审 mode="simulated"（autoplan 原生流程 gstack plan 专用、不适配 OpenSpec change dir，留档见 `gstack-review.md`）。
> 编排评审：Step1 广审(simulated)+ outside-voice(design-voice, claude-fallback) → Step2 并行多镜(领域 backend / 对抗A 隐藏假设 / 对抗B 失败模式 / 接地 核码) → Step3 合并对抗裁决。metrics.enabled=true → 落 lens-metric 锚。
> **裁决主结论**：最小核消掉了前两轮的机械回写致命（C1/C2），但**三条独立镜 + 广审 + outside-voice 高度收敛**砸向同一簇残余面——**「机械搬运/判断」的切分线画错了位置**：`定位哪些复选框` 被误划机械侧（实为判断，且在异构语料上机械定位根本不成立），叠加**时序矛盾**（步2 读步3/步5 才存在的盘面）与**异步无闭环**。判为 **2 致命 + 3 高 + 系统性面**，**不建议按现状进设计门**——建议再一轮 amendment 重画切分线后再拍板。

---

## 决策登记区

```
  spec-review-report.md · 决策登记区
  ┌──────────────────────────────────────────────────────────────────────┐
  │ [需拍板] Q1  C-1 时序矛盾：草稿在 hand-off(步2) 读 archive路径(步3)/merge(步5)  │ 致命
  │ [需拍板] Q2  C-2 切分线错划：name-only 标记无法机械定位复选框，判断渗机械侧      │ 致命
  │ [需拍板] Q3  C-3 两存量 roadmap 格式实测分裂(grep 54 vs 0)，定位对半数落空       │ 高
  │ [需拍板] Q4  C-4 异步回填无闭环：经 ship 全自动链人被支走，草稿埋归档没人 apply   │ 高
  │ [需拍板] Q5  C-5 dogfood 自指坑：本 change 8 处字面含 marker 串，朴素检测必假阳    │ 高
  │ [自动决策] D1 C-6/C-8/C-9/C-12/C-15 五条低风险修法(见下,建议随重写一并落)          │ 中/低
  │ [已裁掉] （无）——对抗镜对 C-7 自标 refuted=true=不直接崩,已降级为低而非裁掉,留档   │
  └──────────────────────────────────────────────────────────────────────┘
```

**拍板记录（人读）**：设计门已拍板**批准**，日期 **2026-07-09**。Q1–Q5 全部**采纳**（经第三轮 amendment 切分线重画落地，checkpoint `6f15c8f`：P-1 时序占位 / P-2 定位到 phase 机械·勾哪几行判断 / P-3 格式分形态 fail-loud / P-4 异步闭环第六步摘要抬行+残差登记 / P-5 detection fence-aware 防自指）+ D1 五条一并落。机判锚已写头部 frontmatter `ship-gate.design_approved: true`。

**〔SR-M〕lens-metric 锚最终化**：门后最终裁决 = 15 采纳 / 0 裁掉 / 0 defer——与 Step3 pre-gate 临时裁决**一致**（所有 finding 经 amendment 采纳落地、无翻改），下方各镜 lens-metric 锚**即最终值**，无需原地重算覆盖。

---

## 各镜 findings（合并去重·canonical·带命中镜集/置信/严重）

### 致命（gate 前必修，否则实现期第一次跑就爆）

**C-1 时序矛盾：草稿在 hand-off(done 步2) 生成，但 archive 路径(步3)+merge(步5) 盘面尚不存在，spec 却把未来锚当「确定性盘面·机械可读」**〔命中 broad+adversarial+grounding+outside-voice｜置信 高｜致命〕
- 接地 CONFIRMED（`sdflow-done/SKILL.md`）：hand-off=第二步、archive=第三步、merge=第五步。草稿生成时刻，archive 路径（含 `{date}`，openspec CLI 步3 才生成）与 merge 结果（步5，缺省 ff-only 无 merge commit）**尚不存在**，只能预测。
- 加重实证：① 本 session 系统日期实测从 07-08 跳 07-09——hand-off 与 archive 跨零点则预填 archive 日期段直接错、指向死链；② merge 若 opt-out/skip/冲突 abort（SKILL.md:251/262），步2 冻进归档的 hand-off 已写「已 merge」→ 人异步读归档草稿把「已 merge」当机械事实回填 = roadmap 记一次从未发生的 merge。
- 建议（三选一，Q1）：(a) 从步2 草稿锚清单**移除 archive/merge**，只留步2 已实现锚（verify=PASS/tasks 完成态/change 名/分支）+ archive/merge 留占位「待归档后由人补」；(b) 草稿生成**下沉到步5 后**（代价：不再随本次归档进 archive/，需另存）；(c) 坚持步2 则 spec **显式声明 archive/merge 为预测值、非确定性盘面**，禁止人当 ground truth 直填。当前「把预测值伪装成确定性盘面」是最危险措辞。

**C-2 切分线错划：`<!-- roadmap: {name} -->` 只带 roadmap 名，无法机械定位「本 change 交付哪些复选框」→ 定位需 change→子任务判断，渗进 D-1 声称的「只搬运盘面」机械侧，与 adr/0015 盘面-判断切分自相矛盾**〔命中 broad+adversarial+outside-voice+domain｜置信 高｜致命〕
- 核心产出「候选复选框」是 proposal P0（:52）；但其定位所需的 change→subtask 信号**在设计的确定性盘面里缺失**。实现时必然二选一：猜（违反 spec「MUST NOT 猜写/判断留人」）或产整阶段全量候选（人逐行删、摩擦没降反增）。
- **最锋利点**（对抗A）：change 命名约定 `implement-{roadmap}-pN-*`（trigger-catalog 附录C）**本已确定性编码 roadmap+阶段双粒度**，设计却弃之不用、另立更粗的手写 name-only 标记。
- 建议（Q2）：(a) 标记扩粒度 `<!-- roadmap: {name}#{phase} -->`；(b) 从 change 名前缀确定性解析 roadmap+phase；(c) 明确把「定位哪些复选框」划入**判断留人**，助手只产阶段级锚不产 per-行建议。三者都比现状「name-only 当机械定位输入」自洽。

### 高

**C-3 两存量 roadmap 格式实测分裂，定位算法对半数存量整体落空**〔命中 adversarial+grounding+outside-voice｜置信 高｜高〕
- 接地 grep CONFIRMED：`mechanical-layer-hardening/roadmap.md` `^- \[` = **54**（`- [x] 1.A.1` 带稳定 id）；`workflow-cost-optimization/roadmap.md` = **0**（表格 + `✅` 标记 + 散文 bullet，**零复选框零 id**）。
- design Non-Goal 明写「不迁移存量 roadmap，现状散文即可，**助手适配**」——但定位机制只认 `- [ ] {id}`，对 wco 式**整条落空**。「漏=退现状」退化不是边界个案而是**半数存量 roadmap 常态**；「候选复选框」概念对 `✅` 表格式无处安放。这是设计内部不一致（承诺助手适配现状、机制只适配一种格式），**非现状快照谬误**。
- 建议（Q3）：(a) 草稿生成前探测目标 roadmap 完成态承载形态（per-subtask 复选框 / 概览表状态列 / 状态散文）分形态出草稿；(b) spec 显式收窄「只支持复选框式 roadmap，散文式 fail-loud 告知留人工」并写进 Scenario；(c) 先做 roadmap 格式收敛（前置于本 feature）。

**C-4 异步回填无闭环/无追踪 → 经 `/sdflow-ship` 全自动链人被支走，草稿埋归档没人 apply，feature 价值趋零**〔命中 adversarial+outside-voice｜置信 中｜高〕
- design 兜底「人本就在归档后独立回填」假定**手动跑 done、注意力在场**；但 ship 一链跑到 merge（done 是末端 proposal:61），阶段三无人类门人被显式支走，草稿沉在**随归档冻结**的 hand-off.md 里，merge 后 `/clear` 无人再被提醒 → roadmap 漂移（本 feature 要消的问题）无闭环 = 产一堆没人 apply 的草稿。
- 建议（Q4）：(a) 给异步回填可追踪落点（如写 todolist 一条 `roadmap 回填待确认` 而非仅埋 hand-off）；(b) ship 链 merge 后把「未 apply 的 roadmap 回填草稿」显式抬到人眼前（landing 提示）；(c) 明确承认「产草稿即止、不保证 apply」残差并在 design 显式登记（别宣称降摩擦却留断头路）。

**C-5 dogfood 自指坑：本 change 8 处产物字面含 `<!-- roadmap: {name} -->` 标记串 → 朴素子串检测必假阳，对 MEMORY 已记录同型事故零防御**〔命中 adversarial(独家)｜置信 高｜高〕
- CONFIRMED：grep 命中 proposal:12 / design:69,87,108 / tasks:21,29 / spec:27,30（8 处，含字面 `{name}`）。detection（spec:29-30）若实现为朴素 grep（最省写法），对**这个 change 本身** done 时假阳命中 → 为不存在的 roadmap `{name}` 生成草稿。design:103 dogfood 计划「本 change 无关联→跳过」**根本跳不过去**，第一个 dogfood 就撞自指。
- MEMORY「gate 子串检测 dogfood 自指坑」同型（ship_gate.py 在讨论 gate 自身的 change 上假阳；修法=行锚定+fence-aware+头部声明区）。本设计对同一坑零防御。
- 建议（Q5，修法已知）：检测 MUST fence-aware（跳过 code fence/行内 code）+ 行锚定（标记独占一行、非嵌散文/引用）+ 排除 change 自身讨论区；tasks 加显式测试「标记串在 code fence 内 → 不误检测」。

### 中 / 低（自动决策 D1：建议随重写一并落，低风险）

- **C-6 [中] 双通道 marker vs `--roadmap` 无优先级 + ship 不透传 --roadmap**〔broad+adversarial+grounding+outside-voice〕：接地 CONFIRMED——ship SKILL grep `roadmap`=0（只透传 merge 意图）、done SKILL grep `--roadmap`=0（未落地新约定）。→ **marker 定为主通道**，`--roadmap` 仅直调 done 覆写；不一致 warn（反静默）。
- **C-8 [中] 「pytest 数」机械锚无既存单一真相源，违 tasks 1.1「不新造真相源」**〔domain(BE-07)+adversarial+broad〕：ship_gate 盘面三字段仅 verify PASS/FAIL、**无测试计数**；且纯 Markdown 编排类 change 无 pytest（锚为 0/N/A 误导）。→ 或让 verify 步把 test 计数写进 verify-report frontmatter 成契约字段（助手只读），或从草稿删「验证数字」锚只留 change/merge/archive 三个真有单一源的。
- **C-9 [中] 坏输入契约只二分(absent/定位不到)，漏 malformed-present 分支**〔domain(BE-04, 独家)〕：ship_gate 已有严格三态 good/absent/malformed 可作口径。→ 契约三分：absent→留人工、**malformed(重复键/大小写/引号值)→fail-closed 标「盘面畸形、留人工」不静默出草稿**、verify≠PASS→不出「完成」候选；写成与载体（脚本/纯指令步）无关的可判定行为规范，使指令步路径也有场景核对锚。
- **C-12 [中] 反静默弱化为 MAY**〔adversarial(独家)〕：spec:35「未声明 MAY 提示」= 允许不提示 → 人以为助手判定无关联、roadmap 永久漏勾。proposal:46 红线写「反静默」却用 MAY，自相矛盾。→ 「未声明但疑似 roadmap 驱动」提示从 MAY 升 **SHOULD**（hand-off 留一行「未检测到关联标记；若属某 roadmap 请手动回填」），使「无草稿」与「判定无关联」可区分。
- **C-15 [低] design.md:10 `state.js:artifactOutputExists` 定位偏差**〔grounding(独家)〕：接地 CONFIRMED——函数**定义在 `outputs.js:36`**（`resolveArtifactOutputs(...).length>0`），state.js:29 只 import+调用。语义正确、定位偏。→ 已随本轮 [spec-review-amendment] 修正（纯事实订正）。

### 已裁掉（反静默压制·留档不静默丢）

- **C-7 [降级低·非裁掉] 「与 §2.1 sweep 对称」框架误导**〔broad+adversarial〕：对抗A 自标 **refuted=true**（不直接崩代码）。但仍是立项论证的误导性对称——sweep 机械终写机器独占文件（INDEX，DO-NOT-EDIT）、本 change 助人确认散文草稿，**写入语义相反**，会诱导实现者复用 sweep 确定性落盘心智 → 滑回机械改 roadmap（正是 C1/C2 要消的）。**降级为低、不裁掉**（措辞收紧「对称」→「同位不同性：同属 done 收尾盘面消费，但一个机械终写、一个助人确认」）。
- 说明：本轮**无真裁掉项**——15 条 finding 全过对抗裁决存活（设计确有这些缺口）；escalate-not-drop 下无静默丢弃。

---

## 补充观察（非独立 finding，供设计门参考）

- **C-10/C-11/C-13/C-14（面治提示）**：一 change→多回填位点（子任务复选框+验收标准复选框+概览表状态+里程碑+task-log，「候选复选框行」单数措辞低估回填面，C-10）· 异步窗口漂移无 apply 时重校验/freshness 戳（C-11）· task-log 插入位置未定义（倒序 prepend？C-13）· marker 采纳 chicken-egg（sdflow-roadmap 划出 scope 不注入 → 触发常态缺失，C-14）。**四条与 C-2/C-4 同根**——都指向「关联/定位/闭环」这一欠设计面，建议 Q2/Q4 的重画一并面治（系统扫，非逐条补丁），别留相邻残面。
- **C-2 solution ↔ C-14**：若 Q2 采「change 名前缀确定性解析」，C-14 的 chicken-egg 自然消解（无需人手标 marker）——两条应联动裁决。

---

## lens-metric 度量锚（metrics.enabled=true；emitter exit 0 落，anchor_lint 门后自检）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="13" 采纳="13" 裁掉="0" defer="0" 独立="2" sev="致2/高3/中6/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="0" sev="致2/高0/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" runner="claude" site="—" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="1" sev="致1/高0/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="1" sev="致1/高1/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="claude-fallback" site="design-voice" findings="9" 采纳="9" 裁掉="0" defer="0" 独立="0" sev="致2/高2/中4/低1" -->

> **残余信任边界声明**：分类正确性（某条 finding 归哪个/哪些 lens）+ roster 完备性 + findings JSON 誊写准确仍是主 session 信任边界，emitter 只保证「给定输入的确定性归约」。`采纳/裁掉/defer` 为设计门拍板前临时裁决，MUST 在拍板回写时最终确定（〔SR-M〕）。
> **反馈回路免责**：本 skill 只落锚，不做聚合/复评/主动 surfacing——跨 change 归档后聚合、采纳率+独立率复评、镜去留一律 `/sdflow-retro` + 人决。

## outside-voice 锚

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="claude-fallback" reason_code="exec-error" findings="9" truncated="false" -->

> codex exit 1 = usage limit（恢复 1:34 AM）→ 按 helper 协议回落只读 Claude 子代理（同源同 prompt render-prompt）。stderr 摘要：`ERROR: You've hit your usage limit`。

## HR-TG 判定

<!-- sdflow:hr-tg v1 hit="none" evidence="Markdown skill+可选轻脚本读盘面生成建议性草稿进hand-off,非机械写、删步即回现状,无运行期爆炸/数据损坏/安全泄漏且难回退的成员命中" -->

---

## 收敛口（阶段二唯一人类门前置）

**不建议按现状进设计 HARD-GATE。** 最小核方向（机械搬运 + 判断留人）经三轮已稳、无「推倒重来」级问题，但残留 **2 致命 + 3 高** 且高度收敛于**同一根因**：切分线画错位置——`定位哪些复选框` 被误划机械侧（实为判断，异构语料上机械定位根本不成立），叠加时序矛盾与异步无闭环。这不是「看着过」，是三条独立冷镜 + grep 接地砸出的真面。

**建议路径**：再一轮 design amendment，就 Q1–Q5 重画切分线（尤其 Q2 定位归属 + Q1 时序锚清单 + Q3 格式分形态），并把 C-6/C-8/C-9/C-12/C-15 五条低风险修法一并落；D1 五条无争议。重写后**可直接过设计门**（无需第四轮全量 spec-review，因根因已定位、修法已给）。或——你若判断这些缺口可在实现期迭代解决、接受残差，亦可在设计门一次性拍板 Q1–Q5 的去向后放行（人机同权，你的 sovereignty）。

> 本报告 15 条 finding 全部登记（无静默丢弃）；采纳率 100%（无裁掉，设计确有缺口）；冷镜独立贡献 adversarial=2(C-5 自指/C-12 反静默)、domain=1(C-9 坏输入)、grounding=1(C-15 事实)——印证「冷 code/spec-review 层 load-bearing」（MEMORY），三条独家致命/中项非合成层能挖出。
