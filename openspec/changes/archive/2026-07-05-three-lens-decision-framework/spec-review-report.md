# spec-review 报告 — three-lens-decision-framework (T46)

> 阶段二编排评审：Step1 广审（模拟降级 + codex design-voice）→ Step2 并行多镜（完整性/接地镜 + 对抗镜）→ Step3 对抗裁决 + 决策登记。**一份**报告，供设计 HARD-GATE 人工一次性拍板。

## 命中范围
- 栈：无（纯 workflow rules/docs 治理变更）｜TG：**TG-23**（≥2 方案，design 有 ADR-1/2/3）+ 软命中 TG-19（2 需求）/ TG-25·BASE-29（跨文档契约一致性）
- HR-TG 判定：命中集 ∩ HR-TG 子集{04,06,07,08,09,16,17,26} = ∅ → 未命中，不开领域 cross-model
  <!-- sdflow:hr-tg v1 hit="none" evidence="无栈领域命中,TG-19/23/25 均不在 HR-TG 子集" -->
- Step1 广审：模拟降级（原生 autoplan 不适配阶段二 OpenSpec 治理变更）+ 自跑 codex design-voice
  <!-- sdflow:step1-broad-review v1 mode="simulated" -->
  <!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="none" findings="4" truncated="false" -->
- 镜头：完整性/接地镜 1（全仓穷举落点）+ 对抗镜 1（落地爆点）；合并池 = 广审 4 + codex 4 + 完整性镜 + 对抗镜 2 真爆点

---

## 决策登记区

### [自动决策]（高置信，已 amend，默认接受可覆盖）

| # | 决策 | 依据 | 处置 |
|---|---|---|---|
| D1 | Step1 广审走**模拟降级**（非原生 autoplan） | 阶段二 OpenSpec 治理变更无 gstack plan file、CEO/产品策略镜近零值；已 honest 标 `mode="simulated"` + 按 C2/P2b 自跑 design-voice 补跨模型切片 | 接受 |
| D2 | **落点集 3 → 5**：补 `sdflow-spec-review/SKILL.md`（④）+ `sdflow-ship/SKILL.md:23` 台账（⑤） | **三源独立同证**（codex CV1 + 广审 F1 + 完整性镜）：spec-review SKILL 是决策登记区实际执行入口、内联硬编码旧格式；不改则归档后主 spec 与发布产品自相矛盾。ship:23 与 code-review:144 同串台账副本 | 已 amend proposal/design/tasks |
| D3 | code-review 落点扩至 frontmatter 7-8 + 导语 30（不止 Step4:96） | 完整性镜：产品自包含须全文一致 | 已 amend tasks 3.x |
| D4 | 修 spec delta 内部矛盾 + CV4 分列 | 对抗镜 F1：delta 行14「有客观判据」vs 行23「有把握」自相矛盾 → 去「有客观判据」新词（改中性）；CV4：「≥2 方案」（TG-23，走三镜）与「事实核验」（Q2，不走三镜）分列 | 已 amend delta |
| D5 | proposal「不再依赖私有记忆」软化为「书面层不再依赖」 | 广审 F4 + codex CV3：与「行为层记忆仍是真相源」张力，实为分层 | 已 amend proposal |

### [需拍板]（人工设计门勾选）

**Q1 — scope 决策：「有把握自动选」→ T10 三级协议对齐，顺手清 vs 纯三镜延后？**〔对抗镜 F2 + codex CV2〕

背景：主 spec:48 已用 T10 三级协议**取代**「有把握自动选」自评表述，但 code-review SKILL:96/7-8/30 仍写「有把握」（且该 SKILL 行 144 台账已是 T10，自身已不一致）。T46 正在编辑这些行（加三镜到「记理由」），是对齐 T10 的天然时机。

| 方案 | 系统镜（防漂移/一致） | 用户镜 | 开发循环镜（职责/回退/重复改） |
|---|---|---|---|
| **A. 顺手对齐 T10** | 一次消除 code-review/ship/主spec「有把握」债，全域一致 | 中性 | 避免未来"改同一行两遍"；但把「三镜格式」+「T10 判据语义」两个正交关注点耦进一个 change，评审/回退耦合、change 意图模糊 |
| **B. 纯三镜、T10 债延后**（推荐） | T46 单一职责（只动决策后果格式），债留存但被 todolist 独立追踪；delta 用中性措辞不引入矛盾 | 中性 | 单一职责清晰、易审易回退；代价=同一行未来可能再 touch 一次 |

**主次判定**：核心矛盾是 **T46 单一职责 vs 顺手清债**。本项目哲学（BASE-18 分解检查 / minimize-repo-footprint / 单一 capability）偏单一职责；且 T10 对齐涉及**判据语义**（非仅措辞），混入三镜 change 会让"这个 change 在改什么"模糊、放大 blast radius。**开发循环镜（单一职责、可回退、change 意图清晰）压倒系统镜（顺手一致）**——债由 todolist 追踪不丢，不构成静默漂移。→ **推荐 B**。（已按 B amend：delta 去「有客观判据」新词、判据词「有把握」原样保留、T10 对齐进 Out of Scope + todolist。若选 A，则需回改 code-review/ship/workflow.md:84/主spec delta 判据词为 T10，change 扩容。）

### [已裁掉]（反静默压制，可审计）

| # | reviewer 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | BASE-12 三镜与「最小可行 + 理想架构」语义打架 / domain-agnostic 硬套牵强（对抗镜攻击点1） | **refuted**：正交互补——「最小可行+理想架构」定生成哪些候选、三镜定如何评估每候选，可自然合并；纯技术选型「用户镜」可空（design ADR-3 dogfood 时「用户镜中性」即合法空镜样例）。tasks 1.2 已列「不打架」机械核对。降为低 sev 实现提示，非爆点 |
| X2 | TG-23 门漏判 /「琐碎决策 SHALL NOT 写满三镜」= 逃逸舱（对抗镜攻击点2、codex CV4 部分） | **refuted-as-blocker**：不对称逃逸确存在（想省事者声明"显然、无≥2方案"跳过），但已被 design ADR-2「当前方案代价」显式记录、落在本项目「prevention 焊不住的残差交对抗镜」哲学内，是**被接受的治理层软门**。可选优化：trigger-catalog 补「≥2 方案」判例 → 已进 todolist defer |
| X3 | 主次判定纯散文、不可机械验证、沦为套话（对抗镜攻击点4） | **refuted**：delta 已带反套话 clause「MUST 附一句主次判定（对**当前这个决策**，为何据此选定），MUST NOT 只罗列」——「为何据此选定」要 decision-specific 理由，套话违反该 clause。且属 R（评审判断）型，可验证性限度是 R 型固有，不比 BASE-09/10 等同侪更弱 |

---

## 各镜 findings 明细（合并去重后，均已裁决）

| 来源 | finding | 严重 | 裁决 |
|---|---|---|---|
| codex CV1 ≡ 广审 F1 ≡ 完整性镜 | 漏落点 spec-review SKILL | high | 采信 → D2 amend |
| 完整性镜 | 漏落点 ship SKILL:23 台账 | med-high | 采信 → D2 amend |
| 完整性镜 | code-review 落点扩 7-8/30 | med | 采信 → D3 amend |
| 对抗镜 F1 | delta 内部矛盾（有客观判据 vs 有把握） | med-high | 采信 → D4 amend |
| codex CV2 ≡ 对抗镜 F2 | Step4 保留已废弃「有把握」 | med | → Q1（推荐 B 延后） |
| codex CV4 | TG-23 误覆盖事实核验 | med | 采信 → D4 amend（分列） |
| 广审 F4 ≡ codex CV3 | proposal 措辞过绝对 | low | 采信 → D5 amend |
| 广审 F3 | docs/ 镜像陈旧 | low | defer（Out of Scope 显式声明 + todolist） |
| 对抗镜 X1/X2/X3 | 见已裁掉区 | — | refuted |

## 收敛
- 广审 + codex + 完整性镜 + 对抗镜四路，**独立同证漏落点**（3→5）+ 揪出 change 自身 delta 内部矛盾——层层加值验证。
- 已 amend 五项（D2-D5 落 proposal/design/tasks/delta，标 `[spec-review-amendment]`）；`openspec validate` 通过。
- 唯一 [需拍板] = Q1（scope）。

---

## 设计 HARD-GATE 拍板记录（2026-07-05）

**Q1 → 采 A（顺手对齐 T10）**。理由（主次翻转）：接地核实 T10 早已是既定行为（ship:23 / 主spec:48 / workflow.md:84 / code-review 台账:144 均 T10），code-review:7/30/96「有把握」是漏改陈旧散文、且与自身台账:144 自相矛盾 → A 是**纯一致性修复非行为变更**，blast-radius 担忧坍缩，系统镜（消除既有矛盾）压倒开发循环镜（单一职责）。已回改 B→A（design ADR-4；delta tension 判据对齐 T10；落点③含 T10 对齐）。

**追加决策 → fold「fold-vs-defer scope-triage 判据」进 T46（落点⑥ / ADR-5）**。用户指出该判据复用率高且 workflow 未成文，**且一次完整 workflow 循环固定成本极高、固守单一职责教条推高周期与成本**。用此判据递归判它自己：同 capability（workflow 决策治理）+ 高耦合（三镜在 scope 决策上的应用）+ 低增量 → fold。落 BASE-18 + delta scenario。

**增量微审（新增内容自检，反静默）**：① 与 BASE-18 原文互补非冲突（独立拆 / 相关合）；② 防吸积三条件（同 capability+高耦合+低增量）即防 BASE-10 蔓延闸；③ **吸积自警**：门上已 fold 两次（T10+判据），判据自限（下个新发现仍过三条件），就此打住不邀第三次 fold，进实现。

**落点集终态 = 6**：① BASE-12 三镜 · ② workflow.md G2 · ③ code-review（三镜+T10）· ④ spec-review SKILL · ⑤ ship 台账 · ⑥ BASE-18 scope-triage。

**门结论：设计已批准 → 进 writing-plans / 实现。**

<!-- ship-gate: design-approved -->
