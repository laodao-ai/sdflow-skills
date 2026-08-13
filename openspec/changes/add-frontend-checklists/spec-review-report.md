---
ship-gate:
  design_approved: true
  reviewed_sha: 32eef0604f5bf3c3a5ba584bdfd493bcd01904f0
---

# Spec Review Report · add-frontend-checklists

- 日期：2026-08-13 · 宿主 host=claude（strong=opus / mid=sonnet / light=haiku；effort high/medium/low）
- 评审对象：proposal / design / tasks + decision-memo（specs 合法 skip：`.openspec.yaml` `skip_specs: true`）+ `research/absorption-candidates.md`（条目内容源）
- 镜阵：广审双镜（strategy / plan-eng）+ 领域镜 ×2（devex〔TG-28〕、frontend 内容准确性）+ 对抗镜 ×2（隐藏假设 / 失败模式与乐观估计）+ 接地镜 ×1 + design-voice（跨模型，codex/gpt-5.6-sol）

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="broad,domain,adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-19,TG-22,TG-23,TG-28" -->

HR-TG 判定：命中 TG-19（多条需求，P0/P1 已在场）、TG-22（假设列表在场）、TG-23（D1~D7 ≥2 方案决策）、TG-28（developer-facing 交付面：checklist 资产 + TG-03 选用记法 + README/guide）；∩ HR-TG = ∅（纯 Markdown 规则资产、可 `git revert`，无运行期爆炸/数据损坏面）⇒ 本轮无领域专属 hr-tg voice。TG-03 本身未命中（本 change 不是前端 UI 变更；其交付物的前端知识准确性由 frontend 内容领域镜覆盖）。

<!-- sdflow:declared-sites v1 declared="design-voice" -->
<!-- sdflow:outside-voice v1 site="design-voice" host="claude" runner="codex" reason_code="ok" findings="6" truncated="false" -->

---

## 拍板三问（决策登记区最顶端，人在设计 HARD-GATE 逐项勾选认/不认）

- **Q-scope 范围划界认不认？**
  自答：锚 proposal Non-Goals——a11y/多端冻结存档、不建其他框架 delta、不动 base/父层、发布不在交付面；评审对「不改评审 SKILL」加了**栈枚举文本失鲜修正例外**（见 Q1，可否决回滚）。 [ ] 认  [ ] 不认
- **Q-deps 依赖/顺序认不认？**
  自答：锚 tasks 任务边界——1 条目落盘 → 2 接线（新增 2.4/2.5）→ 3 同步（3.1 已展开为逐块清单）→ 4 收尾核验，组间线性、组内无 Blocked-by 交叉，P0/P1 分层清晰。 [ ] 认  [ ] 不认
- **Q-risk 风险赌注与对策认不认？**
  自答：锚 `sdflow:hr-tg` hit=none（declared=TG-19,TG-22,TG-23,TG-28，无高风险触发）+ 对策条目：纯 Markdown 单提交可 revert；最大残余风险面 guide.html 手工编辑已由 task 3.1 逐块圈定 + 4.1 补核验锚。 [ ] 认  [ ] 不认

<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->

## 决策登记区

### [自动决策]（高置信采纳，默认接受，设计门可覆盖；对应 amendment 已落盘）

| # | 发现 | 命中镜 | 严重度 | 裁决与已做修订 |
|---|---|---|---|---|
| D1 | **CR-BE-02 IOU 兑现后原句失鲜**：proposal 称「接走 IOU」但 `backend.md:11`「待 frontend domain 覆盖」无任一任务触及，落地后构成新矛盾文本 | strategy+devex+对抗1+voice（4 源收敛） | 中 | 采纳。新增 task 2.4（改交叉引用 CR-FE-01）；Success Metrics 加 `grep "待 frontend domain 覆盖"` 归零；memo 约束 4 补漏 |
| D2 | **guide.html 同步范围过窄**（6 镜收敛，本轮最高收敛面）：失鲜面 = §一 ASCII 树(L286-287)、§二矩阵+缺口 callout(L358/380)、domain cards(L394-450)、§四整节（其示例表 CR-FE-01~05 与实际交付同 ID 不同义，CR-FE-05=可访问性与人拍板排除 a11y 直接矛盾；`<h2>` 硬编码序号级联）、§五教程（唯一 worked example 前提失效）——原 task 3.1「覆盖表与文案」措辞可被窄读半做 | strategy+plan-eng+devex+对抗1+对抗2+voice | 高 | 采纳。task 3.1 重写为逐块清单 + 内容一致性通读要求 |
| D3 | **收尾核验缺 P1 交付面锚**：4.1 的 grep 照不到 guide/INDEX（用词「缺失」非「如有」），P1 metric 无对应核验项、可静默半做 | plan-eng+对抗1 | 中 | 采纳。4.1 扩：guide grep+人工通读、IOU grep、枚举行、注册表行数修正 |
| D4 | **栈枚举文本失鲜（活派发指令）**：`sdflow-spec-review/SKILL.md:223`（领域镜 roster 指令）、`sdflow-init/SKILL.md:195`、`config.template.yaml:24` 均列 backend·go/芯片 delta 独缺 frontend-react；不改则 React 项目评审照字面只开 frontend 镜 | 对抗1+voice | 高 | 采纳（fold）。新增 task 2.5；proposal What Changes/Non-Goals 相应修订（见 Q1）。`sdflow-code-review/SKILL.md:680` 为「…」省略式列举，不改 |
| D5 | **Success Metrics「两侧注册表各 2 行」对 spec 侧不成立**：spec 侧 `README.md:77` 已有 frontend.md 行（就绪），本 change 只 +1（frontend-react）；照字面核验会失败或误改既有行 | 对抗2 | 中 | 采纳。metric 改「spec +1 / code +2」（design 结构图原本就写 +1，属 proposal 内部不一致） |
| D6 | **B7/B8 无正式条文可落盘**：候选表 B 组只有 B1~B6 全文，捞回的 #3/#5 在 E1 仅一行描述，「纯键盘口径」最终检查点不存在——实现期将临场发挥 | voice（独家） | 高 | 采纳。已在候选表 B 组起草 B7/B8 正式条文（标 [spec-review-amendment 起草]，见 Q2）；task 1.3 指明条文源 |
| D7 | **候选表无「触发条件」列，落盘需显式提炼步骤**：26 条中约半数无现成触发短语，套四列模板时若不提炼则各条松紧不一、命中判定失锚 | frontend 领域镜（独家） | 高 | 采纳。tasks §1 头部加共同要求（沿 FE-01~05/CR-BE 句式逐条提炼） |
| D8 | **code 侧 README 无扩展约定节**：design Context「两侧 README 各有…扩展约定」经实读证伪（code README 68 行，注册表后即尾注）；memo 约束 1「code 侧同构」半假 | voice（独家） | 中 | 采纳。design Context / memo 锚订正；task 2.3 加**指针行**指向 spec 侧（初版拟复制五步，复评自纠：查表式规则按仓内纪律用指针不复制，避免 +1 漂移面——人拍板 2026-08-13 指针式） |
| D9 | **INDEX.md:23-24 定性误记**：该两行无 frontend 失鲜文本，task 3.2 实为**新增**括注；但「含 devex」先例在场，行号锚正确（对抗镜原判 high 降级） | 对抗1（降级采纳） | 低 | 采纳（降级）。task 3.2 / memo 约束 4 定性澄清，沿 devex 先例扩注 |
| D10 | **RSC 触发条件边界模糊**：「项目使用 RSC 框架」会对 Pages Router 项目误触发/对 App Router 按框架名漏判 | 对抗2 | 低 | 采纳。design D6 措辞细化（「实际启用 RSC，非仅使用支持 RSC 的框架」） |
| D11 | **D1/D7 命中 TG-23 但缺三镜主次判定书面**（BASE-12） | strategy | 低 | 采纳。design D1/D7 补一句主次判定（轻量，不展开全格式） |
| D12 | **8 条〔未核实〕已复核准确**（含 B3 `VITE_`/`NEXT_PUBLIC_` 前缀语义）：frontend 领域镜逐条模型知识核验无过时/错误/误导；同时回应对抗镜「转写保真≠事实正确」之忧（本轮已做其要求的重新核对） | frontend 领域镜+对抗2 | 低 | 采纳。候选表 §F 与 proposal 假设更新复核结论 + 诚实边界（模型知识核验，非逐字权威页核对） |
| D13 | **B5 与 CR-BE-02 的 open-redirect 分工未反向声明** | frontend 领域镜 | 低 | 采纳（并入 task 2.4 同批：落盘 B5 时加「呼应 CR-BE-02 服务端侧，本条覆盖客户端侧」一句） |

### [需拍板]（人工设计门确认）

- **Q1 · Non-Goal 边界修订认不认**：原 Non-Goal「不改评审 SKILL 与 workflow 机制」字面覆盖了 D4 的三处枚举文本。评审已按「后产物问题根因在前产物」惯例修订 proposal（加边界澄清句 + task 2.5），理由 = 该 Non-Goal 的立意是「机制/流程零改动」，枚举字符串失鲜修正不改任何机制。**推荐：认可 fold**。三面后果——系统镜：不改则派发指令与 TG 目录自相矛盾（React 项目漏 frontend-react 镜），改则 3 行文本、`git revert` 可回退；用户镜：不改则下游评审静默漏镜（不可感知的质量损失），改则无感知；开发循环镜：另开 change 修 3 行文本 = 一整轮 workflow 固定成本，fold 增量≈0。**主次判定：用户镜（漏镜不可感知）主导 ⇒ fold。** 不认可则删 task 2.5 + 撤 proposal 两处修订句即可回滚。
- **Q2 · B7/B8 代笔条文认不认**：「纯键盘交互口径」是人拍板的方向，但最终条文文本此前不存在，评审已在候选表 B 组代笔起草（模态框焦点四段 / 表单错误焦点移动与即时消错，来源留 W3C 原链）。文本是否达意请设计门过目；不满意可只改措辞，落点与编号（CR-FE-07/08）不受影响。

**拍板记录（2026-08-13 17:11，用户「都同意」）**：Q1 认可（Non-Goal 边界修订 + task 2.5 fold 维持）；Q2 认可（B7/B8 代笔条文维持，措辞可后续微调）；task 2.3 修订为指针式；两项 defer 优化（注册一致性机械守、guide.html 长期治理）记入 todo 池。**注**：此为对 Q1/Q2/2.3 修订的拍板，设计 HARD-GATE 的批准（拍板三问勾选 + 进 `/sdflow-ship`）另行显式确认。

**设计门已拍板批准，日期 2026-08-13（17:15，用户「批准」）**——批准盘面 = `32eef06`（拍板前二次修订已按 ADR-7(b) 单独落盘），机判锚见本文件头部 frontmatter `ship-gate` 块。〔SR-M〕lens-metric 锚随本次拍板最终化：拍板未翻改任何裁决（13 采纳 / 2 裁掉 / 0 defer 维持），下方锚行数值即门后最终值，原地确认、未重算。

### [已裁掉]（反静默压制留痕，供复核「裁得对不对」）

- **X1 · voice#5「收尾缺 `bash setup.sh` 全局安装验证门」**：裁掉。理由：proposal Non-Goals 第 6 条已显式将发布/推送划出交付面，Migration Plan 已写明 push → 运行 checkout pull+setup 的发布链；`AGENTS.md:104` 的 setup.sh 要求属**发布边界动作**——实现期在开发 checkout 跑 setup.sh 会翻全局指针（测试三层纪律的「全局窗口层」，机器级影响），恰是本仓明令避免的。原始发现与出处已核实（AGENTS.md 原文属实），裁的是「把它放进本 change 任务面」这一去向。
- **X2 · frontend 领域镜 F2「A3/B1/B4 与 BASE-28 的特化关系未逐条内注」**：reviewer 自判「非缺陷，仅记录」——BASE-28 已在 base 层一句话声明前端特化方向（XSS/CSRF/CSP），无需逐条内注。无动作。
- **X3 ·（降级说明）对抗镜1 H1 原判「INDEX 消费面凭空、high」**：半边不成立（行号锚正确、「含 devex」先例在场），残余半边（定性应为新增非失鲜）已降级为 D9 采纳。此行留痕裁决过程，非独立裁掉项。

---

## 各镜 findings 摘要（详情见各镜结构化回传，低置信项一行带过不省略）

- **strategy 镜**（3 条）：F1 IOU 接线缺口（→D1）；F2 guide 教程区块失鲜（→D2）；F3 D1/D7 三镜格式（→D11，自报置信 55 仍上抛）。其余职责 R 项（BASE-08/09/10/13/14/18/22/26/27/30）过检无违反。
- **plan-eng 镜**（3 条）：PE-1 guide 同步范围过窄含 a11y 矛盾表（→D2）；PE-2 4.1 缺 P1 核验锚（→D3）；PE-3 guide 无机械回归网（置信 55，低置信一行带过：已并入 D2 的「通读+目视」缓解，不另立项）。BASE-05/06/16/17/19/25/28 过检合理。
- **devex 领域镜**（DX-01/02/05 N/A；2 条）：DX-1 IOU 文本失鲜（→D1）；DX-2 guide 教程示例脱节（→D2）。DX-03 命名一致性 PASS。
- **frontend 内容领域镜**（5 条）：F1 触发条件提炼缺口（→D7）；F2 BASE-28 关系（→X2）；F3 B3 前缀准确可摘标（→D12）；F4 B5/CR-BE-02 分工（→D13）；F5 全部 8 条〔未核实〕复核准确（→D12）。**26 条技术内容整体核验通过**。
- **对抗镜1·隐藏假设**（5 条）：H1 INDEX 定性（→D9/X3）；H2 SKILL 枚举活指令漏改（→D4）；H3 guide 范围+核验盲区（→D2/D3）；H4 config.template 枚举（→D4）；H5 IOU（→D1）。已试证伪未爆：backend-go 记法同构（与 react delta 对称的既有非形式化，非新洞）、13 行表形制、B/D 组数量、research 归档随行。
- **对抗镜2·失败模式与乐观估计**（5 条）：F1 guide §四/§五+序号级联（→D2）；F2 ASCII 树对齐风险（→D2）；F3 注册表 +2 错（→D5）；F4 转写保真≠事实正确（→D12 消解）；F5 RSC 边界（→D10）。已试证伪未爆：ID 零冲突、附件归档合法、§二矩阵行更新机制。
- **接地镜**（0 不符项）：11 项代码事实锚全数核验通过（含 README:82-88/53/77、trigger-catalog:44-46、backend.md:11 原文、CR-04、guide 失鲜行、devex 先例无 capability、E1 12 行、`skip_specs: true`）。
- **design-voice（跨模型，codex）**（6 条）：#1 B7/B8 无条文（→D6，独家）；#2 IOU（→D1）；#3 枚举面含 init SKILL（→D4）；#4 guide（→D2）；#5 setup.sh 门（→X1）；#6 code README 扩展约定节不存在（→D8，独家）。6 条中 2 条独家采纳。

**机械引用核**（`findings_ref_check.py`，合并池 15 条）：11 pass / 4 uncheckable（evidence-pack，直进对抗裁决、标注未经机械核：D2/D4/D6/X1 对应条）/ 0 fail——无机械裁掉项。

## 度量锚（lens-metric · config `metrics.enabled: true`；采纳/裁掉为设计门拍板前临时裁决，拍板回写时最终化〔SR-M〕）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="8" 采纳="8" 裁掉="0" defer="0" 独立="3" sev="致0/高2/中3/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="6" 采纳="5" 裁掉="1" defer="0" 独立="2" sev="致0/高2/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="6" 采纳="5" 裁掉="1" defer="0" 独立="2" sev="致0/高3/中2/低0" -->

残余信任边界声明：分类归属正确性、roster 完备性、findings 誊写准确仍是主 session 信任边界；emitter 只保证给定输入的确定性归约。`findings=N` 与合并池实收数的数值一致性同为信任边界、非机械可验。接地镜 findings=0 = 该镜 11 项核验全过、无不符项上报（非未跑）。

## 已应用的 amendment 清单（均标 `[spec-review-amendment]`，`git diff` 可核）

1. `proposal.md`：What Changes 接线补项（backend.md IOU + 三处枚举）、Success Metrics 修正与扩锚、Non-Goals 边界澄清句、假设复核注记。
2. `design.md`：Context code-README 断言订正、D1/D7 主次判定、D6 触发条件细化、接线图补 5 处评审补入面。
3. `tasks.md`：§1 触发条件提炼共同要求、1.3 条文源、2.3 扩展约定补节、新增 2.4/2.5、3.1 逐块清单重写、3.2 定性澄清、4.1 核验锚扩充。
4. `decision-memo.md`：承重约束 1 锚订正、约束 4 消费面清单补漏 + INDEX 定性订正。
5. `research/absorption-candidates.md`：B 组补 B7/B8 正式条文（起草）、B6 拍板结果更新、E1 注记更新、§F 复核结论追加。

## 图与流程注记

- 命中画图触发仅 design「结构与接线图」（ASCII 文件树）——存在、正确（评审后已补 5 处新增面），未过时。无状态机/序列图触发。
- 流程偏离留痕：单批 dispatch 因单条消息输出上限拆为 4 条**连续**消息完成（期间零盘面改动，全部镜审同一快照）——偏离「一条消息内」字面，保住「不等前置 amendment、同盘面并行」语义。host=claude 免探针；design-voice 走 async·harness 分支（探针 PROBE_OK + 主 session 确证），sidecar rc=0。
- 站点↔任务记账：design-voice=已 dispatch（harness 任务 `bp2q7el5d`，nonce=none，manifest 已落 `.outside-voice/20260813T074744Z-3kE0Kz/dispatch-manifest.tsv`）；hr-tg=未 dispatch（HR-TG∩=∅，合法不派）。

## 收敛口

**建议进设计 HARD-GATE**：13 条采纳发现的 amendment 已全部落盘、2 条裁掉留痕、无 defer；待人拍板项仅 Q1（Non-Goal 边界修订）与 Q2（B7/B8 代笔条文）+ 拍板三问。核心内容面（26 条条目）经领域镜全量复核准确，接地镜 11 项锚全过——批准后走 `/sdflow-ship`。

🔴 拍板前若再改四件套（实质改动），须先单独 checkpoint 提交、再按拍板回写协议落 `ship-gate` frontmatter（`reviewed_sha` = 被批准盘面的 40 位 OID）。
