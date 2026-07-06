# spec-review 报告 — batch-triage-strategy

> 阶段二编排评审（连续跑）：Step1 广审(缩 autoplan 为本质·主session原生) + Step2 冷镜(对抗×3 + 接地×1 + outside-voice codex) → 本报告。
> 结论：**建议进设计 HARD-GATE，但有 2 个需拍板项（Q1/Q2 是实质重构）+ 6 项已采纳 amendment**。冷层这轮大丰收，dogfood「冷独立层 load-bearing」再次坐实。

## 命中范围
- 栈：无代码领域命中（纯 markdown 流程规则，backend/embedded/frontend 全 N/A）→ 无领域镜。
- HR-TG：`hit=none`（非运行时/并发/数据/安全面，安全性由 fail-closed+硬边界纪律承载）。
- 镜：广审(broad) + 对抗×3(执行契约/规则一致性/下游回灌) + 接地×1 + outside-voice(codex,design-voice)。
- gstack/autoplan：缩到广审本质（见 gstack-review.md 降级声明，mode=simulated，主 session 原生，冷层不砍）。

<!-- sdflow:hr-tg v1 hit="none" evidence="纯 markdown 流程规则，无运行时代码/并发/数据/安全面；安全由 fail-closed+硬边界纪律承载、非运行时不变量" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="ok" findings="5" truncated="false" -->

---

## 决策登记区

```
┌────────────────────────────────────────────────────────────────────────┐
│ [需拍板] Q1  worked example / 判据「同类 Leg1」口径矛盾（致命级重构）      │
│ [需拍板] Q2  batch-triage = 本仓-local 规则 vs bundle-published（架构选择）│
│ [自动决策/已采纳] A1  D7 一项一commit 补执行协议+验证锚（MAJOR-3）          │
│ [自动决策/已采纳] A2  三分类第一腿补全 BASE-18「低增量」（MED-4，双源）      │
│ [自动决策/已采纳] A3  延迟绑定/搭便车 作单开子态（MED-6）                   │
│ [自动决策/已采纳] A4  聚合上限「有上限」升 MUST + 每项判定记录（MED-7）      │
│ [自动决策/已采纳] A5  cross-ref spec-workflow bundle 契约（MED-9）          │
│ [自动决策/已采纳] A6  术语统一「三分类」（LOW-8）                          │
│ [已裁掉] X1  大扫除批 vs AND门 重叠（B4 判 clean partition，接地属实）      │
└────────────────────────────────────────────────────────────────────────┘
```

### 【需拍板 Q1】worked example 与「同类 Leg1」自相矛盾 —— 致命级
**来源**：对抗镜1-F1（独立，致命）；接地镜复证 debt 标签属实。
**问题**：proposal/design 的旗舰 worked example 把 **T50/T41/T42** 定为「无逻辑面→大扫除批候选」。接地证实其**内容**确是 cosmetic（决策区边框/可点击链接/多图表）。**但**这三项**落点全是行为面路径**——T50→`sdflow-spec-review/SKILL.md`、T41→`SKILL.md`、T42→`workflow bundle`。Leg1 `trivial_shape.py` 的 `BEHAVIOR_PATH_PATTERNS`（`SKILL.md`/`*/assets/workflow/*`）**无条件判 NOT_EXEMPT**（"bundle markdown 承载行为"，trivial_shape.py:15-16,33-40）。
即：「无逻辑面」有两种口径打架——**内容 cosmetic（人看 issue 描述）vs 路径承载行为（Leg1 保守机判）**。本 change 宣称判据「同类 Leg1」，但旗舰示例恰是 Leg1 会**排除**的。要么判据悄悄比 Leg1 松（违背"同类"承诺 + 弱化安全：sweep SKILL.md 改动稀释评审、正是红线怕的），要么示例判错——两者都证伪 Success Metric「worked example 正确二分」。

**两方视角 + 三面后果**：
- **系统镜**：Leg1 路径保守是有理由的——SKILL.md/bundle 是 load-bearing，机判分不清 cosmetic 改与行为改。sweep 放行这类项 = 把 Leg1 拒绝机械放行的东西靠人纪律放行，破防面在"behavior-面被稀释审"。
- **用户镜**：若采纳路径守卫，本仓大部分 debt 落 SKILL.md/scripts → **大扫除批候选池在本仓其实很薄**（这是重要 ROI 真相：本仓 cosmetic 债多在行为面文件里，纯文档/注释/README 落点的琐碎项才是安全候选）。
- **开发循环镜**：路径守卫可复用 Leg1 的 `BEHAVIOR_PATH_PATTERNS`（概念，非脚本）——判据文档直接引其路径清单作硬排除信号。

**推荐（主）= 采纳 Leg1 行为面路径守卫**：issue 级判据 MUST 把「落点命中 Leg1 `BEHAVIOR_PATH_PATTERNS`（SKILL.md/*/assets/workflow/*/ship_gate.py/…）」作为**硬排除**信号（无论描述多 cosmetic）。后果：T50/T41/T42 **移出候选栏**，worked example 换成真正落非行为面路径的项（纯 docs/README/注释/tests）；并**诚实标注本仓大扫除批候选池薄**（多数 debt 落行为面）。次选（不推荐）：把「同类 Leg1」降格为"共享目标、口径更松"——但弱化安全、违 dogfood 红线。

### 【需拍板 Q2】batch-triage = 本仓-local 规则 vs bundle-published —— 架构选择
**来源**：outside-voice codex-1/-2（接地）+ 对抗镜3-F1/-F2（接地）四facet 收敛。
**问题**：design D6 主张「判据规则落 bundle 权威源、`sdflow-init update` 回灌下游」。冷源接地扒出这套发布故事**整体破裂**：
1. **回灌事实错**（codex-1）：`copy_bundle(full=False)` 只复制 `tools/`，完整规则 markdown 仅 `full=True`/`update --dev` 才铺；test_init.py:138 钉死普通 update 不部署 workflow.md。**D6 措辞「普通 update 回灌规则」事实性错误**（真 canonical = setup.sh 软链 `~/.sdflow/workflow`）。
2. **INDEX 同步指错文件**（对抗镜3-F1）：`openspec/INDEX.md` 是静态 snippet `sdflow-init/assets/snippets/index-section.md` 的渲染副本，`inject()`（init.py:514-518）每次 update **无条件整体替换**。手改 INDEX.md → 下游看不到 + 下次 update 静默覆盖丢失（**正是本 change 红线"禁只改副本"同一坑，坑在 tasks 自己身上**）。tasks 2.4 该指 `index-section.md`。
3. **下游悬空引用 + 孤儿**（对抗镜3-F2）：发布进 bundle 的规则引用「BASE-18 AND 门」，但 BASE-18 只在**本仓私有 roadmap**（grep 全仓：不在 assets/workflow/）；且真正应用它的 `consolidation-plan.md` 是本仓 issues/ 手工产物，**无任何 skill 生成/消费/引用**（sdflow-issues 把"该不该建批次"划为模型判断非读规则），workflow.md 无锚点。→ 发布进 bundle = 下游读不到 BASE-18 的孤儿文档。
4. **接入点错**（codex-2）：issues 分诊入口在 workflow.md 的 sweep 段/sdflow-done，非 trigger-catalog（后者是内容触发单一源）。

**推荐（主）= 本仓-local 规则**：batch-triage 判据落**本仓**（`workflow.md` issues-sweep 段引用 + consolidation-plan 应用），**不发布进共享 bundle**——因真实消费者是本仓、下游无 issues 池/consolidation/sweep 对应机制。净收益：无回灌、无 INDEX snippet、无下游孤儿、无 BASE-18 悬空。若未来下游长出 issues 池机制再发布。**契合 roadmap ethos（不为假想下游建设）**。次选：真发布进 bundle——则须一并落 BASE-18 定义 + 改 D6（用 update --dev/setup canonical，非普通 update）+ INDEX 走 index-section.md + workflow.md 加锚 + cross-ref spec-workflow。工作量大，仅当下游确会分诊 issues 池才值。

> **Q1/Q2 联动**：两者都指向"重估 scope"。Q2=本仓-local 会让 MED-5(trigger-catalog)/MAJOR-2 相关 amendment 大幅简化。建议设计门**先定 Q2（架构）再定 Q1（判据口径）**，我据拍板结果回写 specs（含 SR-M lens-metric 最终化）。

---

## 已采纳 amendment（本轮直接改，标 [spec-review-amendment]；独立于 Q1/Q2）

- **A1〔MAJOR-3·D7 可执行性〕**〔对抗镜1-F2 高 + codex-4 + 广审 B3 三源收敛〕：`checkpoint-commit.sh` 用 `git add -A`（接地×2 复证），D7「一项一commit」只声明结果、无执行协议、无验证锚；且 **buglist B1 记录同根因已真爆**（git add -A 把 superpowers-plan.md 裹进 task1 checkpoint，修复只改 ship_gate 未碰 add -A）；且 `ship_gate.py` `TAG_RE` 只认 `task<N>` 不认 item ID。**已改**：specs 补执行协议（逐 item 编辑→立即 checkpoint→确认 `git status --porcelain` 干净→再下一项）+ 验证锚 Scenario（`候选item数 == 独立 task数 == 独立 commit数`）+ sweep plan 每 item 一 `### Task N: <itemID>`。
- **A2〔MED-4·三分类漏第三腿〕**〔对抗镜2-F2 + codex-3 双源〕：决策流/specs 第一腿只写「同cap∧高耦合」，漏 BASE-18 第三腿「低增量」（REC-3 先例已踩：低增量✗仍列候选）。**已改**：第一腿写全 BASE-18（同cap∧高耦合∧低增量），高增量项即便同cap高耦合也 → 单开/拆分。
- **A3〔MED-6·延迟绑定〕**〔对抗镜2-F1 独立〕：三分类 MUST 穷尽互斥吞不下 consolidation-plan 现有「随手带/延迟绑定」（T47「随任何前端触碰带」）。**已改**：把「延迟绑定/搭便车」列为「单开」桶下显式子态（暂缓、等宿主 change 带），保留其省固定循环成本的价值。
- **A4〔MED-7·聚合上限有牙 + 问责〕**〔对抗镜2-F3 + codex-5〕：规模维全 SHOULD 无机械门；文件数是最可机判维却也只 SHOULD。**已改**：拆分——「**存在上限且超限 MUST 拆分或书面说明**」升 MUST（具体数值仍 SHOULD-可调，守 grill Q-b 无基线口径）；+ codex-5 问责机制：每大扫除候选在 consolidation-plan **落结构化判定记录**（ID/精确路径/为何无逻辑面/低危证据/生成物·CI·目录跨度检查/存疑排除理由），路径宽泛或证据不足即标「存疑→单开」。
- **A5〔MED-9·交叉引用〕**〔对抗镜3-F3〕：新 capability 与既有 spec-workflow「workflow bundle 改在权威源」Requirement 同域不交叉引用。**已改**：specs 加一句「参见 spec-workflow『workflow bundle 改在权威源』（部署机制真相 = index-section.md/copy_bundle）」。
- **A6〔LOW-8·术语〕**〔对抗镜2-F4〕：「二分」(proposal/design/spec标题×3/tasks) vs「三分类」(spec标题) 矛盾。**已改**：统一「三分类/三元标注」（相关批/大扫除批候选/单开），或注明"二分=对既有相关/否的一次追加"。

---

## 各镜 findings（去重后，带置信/严重度）

| 镜 | finding | 置信 | 严重度 | 去向 |
|---|---|---|---|---|
| 对抗1(执行契约) | 一项一commit×git add -A 无协议+B1先例 | 高 | 高 | A1 采纳 |
| 对抗1(执行契约) | worked example 落行为面路径矛盾 | 高 | 致命 | Q1 需拍板 |
| 对抗2(规则一致) | 三分类漏低增量第三腿 | 高 | 中 | A2 采纳 |
| 对抗2(规则一致) | 三分类吞不下延迟绑定/随手带 | 高 | 中 | A3 采纳 |
| 对抗2(规则一致) | 聚合上限文件数维只SHOULD | 中 | 低中 | A4 采纳 |
| 对抗2(规则一致) | "二分"vs"三分类"术语矛盾 | 中 | 低 | A6 采纳 |
| 对抗3(下游回灌) | INDEX 同步指错文件(index-section.md) | 高 | 高 | Q2 需拍板 |
| 对抗3(下游回灌) | bundle 规则悬空BASE-18+下游孤儿 | 高 | 中高 | Q2 需拍板 |
| 对抗3(下游回灌) | batch-triage vs spec-workflow 无交叉引用 | 中 | 低中 | A5 采纳 |
| 接地 | 8 类代码事实全属实、debt 标签正确 | 高 | — | 0 defect（复证 A1 的 git add -A、Q1 的 debt 标签）|
| outside-voice(codex) | 回灌事实错(copy_bundle full=False) | 高 | 高 | Q2 需拍板 |
| outside-voice(codex) | 接入点错放 trigger-catalog | 中 | 中 | Q2 需拍板(接入点) |
| outside-voice(codex) | 一项一commit gate验不了(TAG_RE) | 中 | 中 | A1 采纳(给了修法) |
| outside-voice(codex) | 纯规则判定证据无结构化落盘 | 中 | 中 | A4 采纳(问责) |
| 广审(broad) | scope-drift: stale刷新守卫 | 低 | 低 | 采纳(守卫note) |
| 广审(broad) | 大扫除批vsAND门 clean partition | — | — | X1 判 OK |
| 广审(broad) | 纯规则ROI有牙(3硬MUST) | — | 低 | 保留(A4强化问责) |

### 已裁掉（反静默压制，可审计）
- **X1**：广审 B4「大扫除批 vs AND门 是否重叠/双重计数」→ 裁定 **clean partition 成立**（相关→AND门 / 正交琐碎→sweep / 其余→单开，接地属实，对抗镜2 未能推翻）。裁掉=判"不成立为爆点"，非静默丢。

---

## 度量锚（lens-metric，config metrics.enabled=true；**pre-gate 草稿值，拍板时按 SR-M 最终化**）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="-" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="-" findings="8" 采纳="8" 裁掉="0" defer="0" 独立="4" sev="致0/高3/中4/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="-" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中4/低0" -->

> 反馈回路免责：本 skill 只落锚，不做聚合/复评/surfacing——跨 change 归档后由 /sdflow-maintain 或 /sdflow-retro 聚合、按采纳率+独立率复评（人决砍镜）。本轮观测：接地镜 findings=0 但复证 load-bearing（背书 A1 的 git add -A、Q1 的 debt 标签）；outside-voice codex 独立=0 但接地 facet（copy_bundle/TAG_RE）load-bearing——两者"独立=0"不等于"无价值"，是"corroborate/grounding 型贡献"。

---

## 结论 + 设计门拍板记录

- **设计 HARD-GATE 已通过**（用户拍板 2026-07-07）：
  - **Q2 = 本仓-local**（判据落 `openspec/issues/`，不进 bundle、不部署下游；**发布 deferred** 至本仓 dogfood 验证有效后作未来独立 change——对齐 Leg1）。
  - **Q1 = 采纳 Leg1 行为面路径守卫**（落 SKILL.md/bundle 的项硬排除，T50/T41/T42 改标排除，换真非行为面候选，诚实标本仓候选池薄）。
- **6 项 amendment（A1-A6）已采纳回写** specs/proposal/design/tasks；X1 裁掉。
- **SR-M lens-metric 最终化**：门后最终裁决 = 所有 finding 均采纳（Q1/Q2 按推荐落地、A1-A6 采纳）、X1 裁掉——上方 4 条 lens-metric 锚的 `采纳`/`裁掉`/`独立` 计数与门后一致，**本行确认为最终值**（非草稿）。
- **下一步**：进实现——`/sdflow-ship batch-triage-strategy`（SOP→plan→impl→code-review→done）或手动 `writing-plans`。

<!-- ship-gate: design-approved -->
