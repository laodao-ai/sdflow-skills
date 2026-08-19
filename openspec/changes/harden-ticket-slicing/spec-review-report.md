# spec-review-report · harden-ticket-slicing

- **评审对象**：`openspec/changes/harden-ticket-slicing/` 四件套 + decision-memo（盘面 commit f796527）
- **日期**：2026-08-19 · **宿主**：claude · **主审**：主 session（强档）
- **roster**：broad 双镜（strategy / plan-eng，sonnet·medium）+ devex 领域镜（sonnet·medium）+ 对抗镜 ×2（隐藏假设 / 失败模式，sonnet·medium）+ 接地镜（haiku·low）+ design-voice（codex · gpt-5.6-sol，async·harness，run `20260819T093638Z-OeB6zb`）
- **TG 判定**：命中 TG-19（多条需求）/ TG-23（非显然设计选择 D1/D4）/ TG-28（devex 交付面：新增 bundle reference 文件 + SKILL 语义变更）；HR-TG 交集 = ∅（脚本判定）。
- **机械引用核**：合并池 12 条 → 11 `pass` / 1 `uncheckable`（M2 证据包，直进对抗裁决）/ 0 `fail`。

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="broad,domain,adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-19,TG-23,TG-28" evidence="纯 workflow 规则与 SKILL 指令文本变更；命中的 TG-19/23/28 均不属 HR-TG 子集成员" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->
<!-- sdflow:outside-voice v1 site="design-voice" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->

---

## 拍板三问（决策登记区最顶端，人在设计 HARD-GATE 逐项勾选认/不认）

- **Q-scope 范围划界认不认？**
  自答：锚 proposal Non-Goals（`proposal.md:39-44`）——不搬出票步位置、不做偏离机械判定、不改 strong 档映射、不加评审侧切片同步核，四条排除与 What Changes 的 P0×3+P1×1 边界互补自洽。 [ ] 认  [ ] 不认
- **Q-deps 依赖/顺序认不认？**
  自答：锚 tasks 分组与 design 切片建议（`design.md:57-64`）——T-a(bundle 面) → T-b(出票侧)/T-c(三处引用) → T-d(收尾)，tasks 1.x→2.x/3.x→4.x 与之逐一对应，接地镜核验 3.x 落点（B.7 / roadmap / Step4 defer 流）全部真实存在。 [ ] 认  [ ] 不认
- **Q-risk 风险赌注与对策认不认？**
  自答：锚 sdflow:hr-tg 判定 hit=none（declared=TG-19,TG-23,TG-28，无高风险触发）+ design Risks 表五条（`design.md:66-72`）；本轮评审新增一个待拍板风险点 Q1（D4 条件① 的复核税，见下）。 [ ] 认  [ ] 不认

<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->

---

## 决策登记区

### [需拍板]

**Q1 · D4 必触发条件① 把「合规缺席（有理由）的小修」也卷进 strong 档复核，D2 的减负被复核税讨回**（对抗镜 A · Critical · 置信 85 · ref-check pass）

- **发现**：`specs/impl-orchestration/spec.md:9` 条件① 只看「无切片建议节」，不看是否已按 SA-17 写了成立的缺席理由——「无节+有理由（合规小修）」与「无节+无理由（违规疏漏）」同真值。SA-17（`specs/spec-authoring/spec.md`）明确单票小修可以「有理由」合规缺席，但 D4 让这类 change 出票时**仍必付一次 strong 档对抗镜复核**。memo D2 论证的是「生成草图的样板税」被免除，复核税未被讨论——既不在 design Risks，也不在 memo「接受的边角」。
- **选项 A（推荐）**：条件① 收窄为「design.md **既无**切片建议节、**也无**成立的缺席理由（= SA-17 违规态）」，并补一条护栏：缺席理由蕴含单票交付、而实际出票 >1 张 ⇒ 视同条件③「草图（此处为缺席声明）与盘面矛盾」触发复核。
- **选项 B**：维持现文（一切无节情形必复核）。
- **三面后果**：A：系统镜=触发面收窄但护栏保住 D4 原始动机（无草图**多票**自主切分仍必复核），零新机制；用户镜=人门语义不变；开发循环镜=最高频形态（合规小修）免一次 strong 复核。B：系统镜=条件最简；用户镜=不变；开发循环镜=每个合规小修永久付 strong 复核税，与 D2 意图直接冲突。
- **主次判定**：开发循环镜主导——小修是目标态下最高频形态，B 会把 D2 的减负全数吃掉；A 的「出票与理由矛盾即触发」护栏使高风险路径（自主多票切分）一张不漏。
- **默认处理**：本轮**不预改**该条件（人已拍板过 D4 触发集，改动属实质决策）；批准 A 后按 amendment 落 `specs/impl-orchestration/spec.md` + `tasks.md 2.2`。

### [自动决策]（高置信采信，已回改产物并标 `[spec-review-amendment]`，默认接受可覆盖）

| # | 发现（命中镜） | 裁决理由与修法 |
|---|---|---|
| D1 | **切片草图票数无 [3,6] 预算约束，与出票侧既有 SHALL 冲突**——草图 7 张票可被 strategy 镜+人门放行，出票被迫合并 = 「实质偏离」→ 复核，但**不返回人门**：人批准的方案从未被执行（对抗镜 B · 高 · uncheckable-证据包） | 成立：`ff-generation-constraints.md` 切片建议节与 BASE-31 描述均不查票数，`sdflow-implement/SKILL.md:262` 3–6 张为不可变 SHALL。修法 = 生成约束与 BASE-31 各补「草图票数与 3–6 预算（或 expand–contract 例外）兼容」→ tasks 1.1/1.2 |
| D2 | **三条必触发情形只写「派复核+落盘」，未定义复核证伪的出口**；「defer 一个整体切分方案」语义悬空且触达频率被本 change 大幅提高（plan-eng + 对抗镜 B 合并 · 中） | 成立：与同文件一致性自扫段「③复核不过或无从复核则停并上抛」不对称。修法 = 必触发复核显式接三级协议出口，证伪/无从复核 ⇒ **停并上抛**，新增对应 Scenario → specs/impl-orchestration + tasks 2.2 |
| D3 | **迁移窗口未声明**：本 change 发布前已过设计门、发布后才出票的在途 change，切片节未经 BASE-31 审即被「默认采纳」（devex 镜 DX-04 FAIL · 中） | 成立但按通则④ declared-accepted：一次性窗口、当前全仓在途此形态 change = 0、D4 条件②③在出票侧仍兜偏离/矛盾。修法 = design Migration Plan 显式声明该窗口 + 接受理由 |
| D4 | **BASE-31 会经默认规则漏进 roadmap 评审**，而 roadmap 三件套无「切片建议」生产契约 ⇒ 每次 roadmap 审查可能虚报缺节（design-voice · 高→中） | 成立：`sdflow-roadmap/SKILL.md:472` 镜表同文默认规则。修法 = BASE-31 条文显式限定适用域 = change 四件套评审的 design.md（roadmap 场景 N/A）→ tasks 1.2 |
| D5 | **proposal「全流程模型档位最弱」「前移到强模型」叙事无机制锚**：阶段三继承的是阶段二评审档（无降档指令），阶段一/审镜档位也未被机制钉死（对抗镜 A + design-voice 合并 · 中） | 成立（A-F2 已核验全仓无阶段二→三换档指令；strategy 镜为中档，强的是主审裁决）。不推翻 D1-D8（其依据是 C1/C2 结构性事实）。修法 = proposal Why/What 改为可证实表述「档位不受机制约束 + 无独立审查」「前移到受审 + 人门可见」→ proposal + design 图注 |
| D6 | **tasks 1.3「唯一合理 defer = 缺依赖模块」与 BASE-18 AND 门矛盾**——BASE-18 明定任一条件不满足即 defer（真独立/扩容大/需自身设计审查/高 blast-radius）（design-voice · 高→中） | 成立：新标准文若照此落笔会与其宣称的判定入口自相矛盾。修法 = 规则 4 改写为「fold 优先；defer 判定入口 = BASE-18 AND 门；缺依赖模块 = related 语境下的经典 defer 形态（占位+todo），MUST NOT 写成绝对句」→ tasks 1.3 |
| D7 | **分发措辞错误**：「随 `sdflow-init update` 推给所有消费仓」不成立——`init.py copy_bundle` 精简部署只铺 WORKFLOW-GUIDE.md + schema，规则本体（含 reference/）一律经全局 canonical（`~/.sdflow/workflow` → 运行 checkout `assets/workflow` 软链）解析（design-voice · 中 · **主审已读 `init.py:212-236` + `ls -la ~/.sdflow` 代码证实**） | 成立。修法 = proposal Impact + design Migration 1 改为「经全局 canonical 分发，运行 checkout push→pull 即生效，消费仓零动作」。voice 建议的「tasks 加 setup.sh」**不采**：canonical 是目录级软链，新增文件 pull 后即达，无需重跑 setup |
| D8 | **memo「本次无 TG-23 命中」与 D1-D8 全员携带「砍掉的候选」自相矛盾**；BASE-12 要求的三镜+主次判定缺位（strategy 镜 · 中） | 部分采纳：D1（架构位置）/ D4（触发扩面）为真非显然选择，补三镜+主次判定；D2/D3/D5-D8 按避样板税豁免。修法 = memo「三镜代价」节改口 + 补 D1/D4 两条 |
| D9 | **fold「并入当前票验收标准」未定义该票已在双轴审途中的时序处置**（对抗镜 B · 中） | 成立：中途改在审票的验收标准会造成审非所验。修法 = `spec.md:128` 加限定「尚未进入双轴审 ⇒ 可并入当前票；已在审/已完成 ⇒ 追加进后续 ready 票或新增 Blocked-by 当前票的票」 |

### [已裁掉]（反静默压制——原始发现 + 裁掉理由，供人复核裁得对不对）

- **X1**（对抗镜 B F4 · 低 · 置信 45）：「出票方仅改票内验收措辞可绕过偏离清单」——**裁掉理由**：切片草图的内容按定义 = 票划分 + 阻塞边（`design.md:59`「初步 ticket 划分…阻塞边草图」），不含票内验收措辞 ⇒ 该维度不构成对草图的偏离面，攻击对象不存在。
- **X2**（strategy 镜 F3 · 低 · 置信 35）：design.md 无 BASE-27 形式化「第 N 小时」推演段——**裁掉理由**：镜自判 substantially satisfied（tasks 依赖序 + Risks 表已覆盖实质），主审同意非缺口，补形式化段落是样板税。

### [低置信上抛]（一行带过，不静默滤除）

- **L1**（strategy 镜 F2 · 低 · 置信 52）：BASE-13 格式项——proposal Non-Goals 各条未附「若该假设不成立方案如何失效」的显式可证伪句；可选打磨，本轮不强制（避样板税），人门扫一眼即可。

---

## 各镜 findings 摘要

- **strategy 镜**（3 条）：F1→D8（采纳）；F2→L1（低置信上抛）；F3→X2（裁掉）。其余 BASE-01/08/09/10/22/26/30 逐项过、无 finding；memo C1/C5/C6/C7 证据锚全部实仓核验一致。
- **plan-eng 镜**（1 条）：PE-1→D2（采纳，与对抗镜 B F3 合并）。BASE-05/16/17/19/25/28 逐项过、无 finding；三份 delta 的 Requirement/Scenario ↔ tasks 双向追溯无幽灵任务。
- **devex 领域镜**（1 条 + 判定表）：DX-01 N/A · DX-02 N/A · DX-03 PASS · **DX-04 FAIL**→D3（采纳）· DX-05 N/A。
- **对抗镜 A · 隐藏假设**（2 条）：F1→Q1（需拍板）；F2→D5（采纳，与 voice V2 合并）。已试未破：strategy 镜负载稀释、C4 自报边界（memo 已显式承认）、C2 节级失鲜（D4③ 即兜底）、三处指针引用漂移（现存两处逐字一致）。
- **对抗镜 B · 失败模式**（4 条）：F1→D1（采纳）；F2→D9（采纳）；F3→D2（合并采纳）；F4→X1（裁掉）。已试未破：多条件叠加重复派发、4.1 脚本路径、tasks/切片依赖序自洽、C5 覆盖。
- **接地镜**（0 条）：16/16 代码事实断言全部 ✓（含 `sdflow-implement/SKILL.md:158-159/255-256/557`、`ff-generation-constraints.md:40-42`、`spec-quality-base.md:42`、`resolve-models.sh:102/216`、T141 存在且 created=2026-07-01、BASE-31/`change-decomposition-standard.md` 均确认尚不存在、INDEX 有 reference 登记位）。
- **design-voice**（codex · 4 条，全采纳）：V1→D4、V2→D5（合并）、V3→D6、V4→D7（主审代码复核证实）。无 voice 与主审分歧的 TENSION 条目。跨模型独家贡献 3 条（V1/V3/V4），再次符合「跨模型 voice 产出高于同族温镜」的历史模式。

**图表核验**（design-diagrams）：本 change 命中图 = design.md「切分判断流（变更前→变更后）」ASCII 图——存在、正确；随 D5 修正档位标注后未过时。无缺失图。

**度量锚（lens-metric · pre-gate 草稿值，拍板回写时按〔SR-M〕最终化）**：

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="6" 采纳="4" 裁掉="1" defer="1" 独立="2" sev="致0/高1/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="4" 采纳="2" 裁掉="1" defer="1" 独立="1" sev="致0/高0/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="3" sev="致0/高0/中4/低0" -->

> 残余信任边界声明：分类正确性 / roster 完备性 / findings 誊写准确仍是主 session 信任边界；emitter 只保证给定输入的确定性归约。`findings=N` 与合并池实收数的数值一致性同为主 session 信任边界，非机械可验。

---

## amendment 清单（已落盘，均标 `[spec-review-amendment]`）

1. `tasks.md 1.1/1.2` — 票数预算兼容检查（D1）+ BASE-31 适用域限定（D4）
2. `tasks.md 1.3` — 拆分标准规则 4 与 BASE-18 AND 门对齐（D6）
3. `tasks.md 2.2` — 必触发复核证伪出口（D2）
4. `specs/impl-orchestration/spec.md` — 必触发段三级协议出口 + 新 Scenario（D2）；fold 时序限定（D9）
5. `design.md` — Migration Plan 第 4 条迁移窗口声明（D3）；Migration 1 分发措辞（D7）；Context 图档位标注（D5）
6. `proposal.md` — Why/What 档位叙事（D5）；Impact 分发措辞（D7）
7. `decision-memo.md` — 三镜代价节改口 + D1/D4 三镜+主次判定（D8）

---

## 收敛口

**建议进设计 HARD-GATE**：核心结构（D1 不搬出票步、消费语义翻转、单一源收口）经六镜 + 跨模型 voice 检验后站得住——接地镜 16/16 全实、承重约束 C1-C7 零失实；本轮 13 条合并 findings 中 9 条已按自动决策回改产物、2 条裁掉、1 条低置信上抛，**唯一需人拍板的是 Q1（D4 条件① 是否豁免合规缺席的小修，推荐选项 A）**。人过本报告勾选拍板三问 + 裁决 Q1 后，即可按出口序列进 `/sdflow-ship`。

> 拍板前流程纪律〔harden-gate-git-layer 1.7〕：本轮 amendments 已改动四件套（相对镜子审过的 f796527）——上述改动全部源自本报告 findings 且逐条列于 amendment 清单，人拍板即是对「改后盘面」的批准；若人读报告后要求**再次**修改，须先单独 checkpoint 该二次修订、再回写 ship-gate 锚（ADR-7(b)）。
