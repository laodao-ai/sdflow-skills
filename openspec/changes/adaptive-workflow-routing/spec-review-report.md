<!-- sdflow:step1-broad-review v1 mode="simulated" -->

# spec-review 报告 — adaptive-workflow-routing

> **诚实声明（反静默）**：本轮**未原生跑 autoplan**（CEO/design/eng/DX 管线）——广审角度由 fan-out 的对抗×2 + 接地 + codex outside-voice 承担（覆盖 eng/对抗/独立冷视角）。`broad` 锚 `mode="simulated"`。这是**显式降级、非静默跳过**。

## 命中范围

- 变更性质：**meta / workflow bundle 自身变更**（改路由机制 = 本 change 定义的 TG-27）→ 无 backend/embedded/frontend 领域清单命中（接地镜 §7 证实）。
- 冷源：对抗镜 A（claude）· 对抗镜 B（claude）· 接地/一致性镜（claude）· outside-voice（codex, site=design-voice）。领域镜 N/A（无清单命中）；autoplan broad 降级。
- config `metrics.enabled=true` → 落 lens-metric 锚。

## 总评（对抗裁决后）

**4 个独立冷源高度收敛，findings 绝大多数文本可证、几乎无可证伪项。** 独立冷审抓出了 grill（我+用户协作收敛）**没抓到的一批地基问题**——**反证了本 change 试图让其可跳的「独立冷镜」层的不可替代价值**（reflexive：正是它救了本 change）。

核心结论：**设计的「客观机判路由」前提在「省成本发生的阶段」（ff/grill/spec-review，全在 diff 之前）不成立**，且 D4/D6 收敛后**净收益已薄**。这不是补丁级问题，是**方向级拍板**（见决策登记区 Q1）。

---

## Findings（对抗裁决存活，按簇·严重度）

### 簇 A · 【致命·文本可证】谓词-diff 时序矛盾 + HR-TG 不可机判 → 「全机判路由」前提在前置阶段坍塌

- **A1〔对抗A-F0，最狠〕** 四谓词多为 **diff 派生**（P2 净行/新文件、P4 白名单「diff 仅动注释/tests/版本」），但路由/平凡声明/门核**全发生在 diff 不存在时**（ff→grill→spec-review 都在 apply 之前）。→ ff/grill 时 route.py 要么 (a) 缺 diff 信号→保守判非平凡→**主收益「跳 grill」机判不可达**；要么 (b) 拿 proposal 自述当代理→**退回自评**（全程在防的）。**打穿主收益路径 + 声明门核可核性。** 高置信/高严重。
- **A2〔codex#1〕** HR-TG「脚本判 path/content」**无机器可执行源**——trigger-catalog 是散文表、附录只列 ID；且 HR-TG 成员多为**语义触发**（TG-04 DB迁移/TG-17 信任边界/TG-26 并发），脚本无法从 diff 可靠判。**今天 HR-TG 命中是规划镜头（模型）判的，从来不是脚本** → **D7「四谓词全机判」对 P1 为假、「掏 L2 判断层」的前提坍塌**。高。
- **A3〔对抗A-F3〕** 设计门核 = 「声明 vs 脚本硬信号」一致性——只抓「作者相对脚本撒谎」，**与「脚本自身漏判」正交**：脚本把真非平凡算成平凡时，声明与脚本「一致」，门核放过。**共谋失效面 = 脚本漏判集（设计自认不可证完备，design.md:35）** → 反滥用门核对最危险失效**提供 0 保护**。高。

### 簇 B · 【高】收益/信任基础被自身决策掏空

- **B1〔对抗B-4，文本可证〕** **招牌 ROI 已被 D4/D6 抽掉 2/3**：Success Metric 1（proposal:42）说省「grill + spec-review 多镜 + code-review 多镜」，但 grill 被 D4 否、code-review 多镜被 D6 否 → **实际只剩 spec-review 多镜 + superpowers、命中窗口极窄**（HR-TG∅ ∧ 有逻辑面 ∧ known-pattern），却对价 route.py+四谓词+托管块+calibrator+BREAKING 永久成本。**Success Metric 1 相对 D4/D6 已过期。** 高。
- **B2〔对抗B-2，逻辑必然〕** calibrator **幸存者偏差**：LIGHT 漏的 bug 正因轻量化才漏、最不可能被独立发现、从不进 buglist → 「LIGHT 逃逸率」是**偏向 0 的下界**；FULL 空产出每次可观测、LIGHT 逃逸仅条件可观测，不对称。design 把「不完整」错当「仅滞后」（proposal:63）→ **D3「后向是信任前向的前提」不成立**。建议补 shadow-full 采样臂。高。
- **B3〔对抗A-F4〕** 「ff 漏跑靠设计门兜底」是**循环 + 相关失效**：ff-route 与设计门**用同一份 route.py**（相关，非纵深）；且设计门住在 spec-review，判平凡→spec-review 走 LIGHT → **用被这次判定亲手弱化的门去兜启动这次弱化的推荐**。真正独立兜底只有 code-review Step2（异质：fresh 冷镜非脚本）。高。

### 簇 C · 【高】白名单/谓词机判在本 repo 尤其危险

- **C1〔对抗A-F1，本repo致命〕** 「仅动 markdown 文档行」白名单——**本 bundle 的编排逻辑就写在 SKILL.md/workflow.md 等 markdown 里**。改一行 SKILL.md 指令 = 「仅动 markdown」→ 命中白名单 → 免 Step2 多镜。只有 TG-27 能兜，但 TG-27 靠 path/content 机判（A2 已证不可靠）。**「markdown 即行为」在本项目是伪命题的反面。** 高。
- **C2〔codex#2〕** **P2 自相矛盾**：「含 specs/ delta ∨ 新增文件 → 非平凡」，但**每个正常 change 都有 specs delta**（ff 生成）→ P2 恒触发→啥都非平凡（防呆但废功能）；且「新增文件」与「tests-only 白名单=平凡」直接打架。需重定义（改 canonical specs/公共契约、新增非测试生产 codepath）。高。
- **C3〔对抗A-F5/B-6〕** P2 净行**无定义且非确定性**（git rename 检测阈值跨 runner 不同 → 打脸 D2「跨 runner 稳定」）；**30 行精妙并发 bug 按构造判平凡**（低行+无结构信号+改既有函数）；「仅改版本常量」可夹带 load-bearing 常量（API_VERSION/SCHEMA_VERSION 切 code path）；「仅新增 tests/」放过「加错的测试锁死 bug/假绿」。中-高。

### 簇 D · 【高·机械】OpenSpec/契约落法欠规格（接地镜）

- **D1〔接地§3-A〕** code-review MODIFIED 块**标题改名**（原「…为每次全跑的独立强制主审」→「…两层深度按逻辑面自适应」）→ **OpenSpec 按标题匹配 MODIFIED，改名会定位不到原需求**（原需求孤儿残留/校验报错）。**机械 bug，我引入的。** 高。
- **D2〔接地§4〕** lens-metric 契约锚形字段全是「镜×finding」，枚举无「路由决策」对象/无 FULL/LIGHT/逃逸 槽 → **契约无槽可容**；workflow-metrics delta 未定义新锚 schema 如何落契约/是否升 v2 → 欠规格。高。
- **D3〔接地§6〕** route.py 类比 ship_gate 但**漏继承 fence-aware/声明式行级解析**——route.py 读「平凡声明/决策登记区空?」正是 ship_gate `tg02_hit` 花大力气防散文假阳的同类场景。中-高。
- **D4〔codex#3/#4〕** route.py **源路径未定**（应在 `assets/workflow/tools/`）+ CLI/退出码/JSON 字段未定义；平凡声明**无 ff 生成入口**（ff-generation-constraints.md 只覆盖 D-1~D-6）。中。

### 簇 E · 【中】系统性/引导期风险

- **E1〔对抗B-1〕** HR-TG∅ **中间带**：「有风险非灾难」类（折扣/财务舍入，输出错但不爆炸）——HR-TG 为方向①标定本就不覆盖，方向②却因此放它轻量化，P2/P3/P4 兜不住「有先例+面小+逻辑错」。中-高。
- **E2〔对抗B-3〕** TG-27 **自指引导期**：改路由机制自身的 change，由「永远落后一版的已部署路由」审；bundle 自升级窗口里元层改动可自豁免。建议**硬编码路径元层护栏**（diff 触 `assets/workflow/`/`ship_gate.py`/`route.py`/评审 skill → 无条件 FULL，不走 HR-TG 查表，与部署解耦）。中。
- **E3〔对抗A-F2〕** 先例门核「存在 ∧ 触同 capability」对**形似神不似失明**（指个远房亲戚放行）；design.md:35 自认。建议加先例当年路由判定/结构相似度比对。中-高。

### 已裁掉 / 部分证伪（反静默，可审计）

- **X1** 对抗 B-3「本 change 自身自豁免」——接地镜证伪其**具体实例**：本 change 这次靠 P2（≥2模块+specs delta+新文件 route.py+净行>100）独立强制 FULL 而幸免，**非靠 TG-27**。**一般引导期风险成立（E2 保留），具体实例 defer。**
- **X2** 对抗镜自陈两点公允（不计爆点）：D6 两层切是真做功（有逻辑面 Step2 恒跑，故 C 簇小 bug 非完全无审、丢的是 grill+FULL spec-review）；冷启动姿态方向正确。**采纳为「严重度封顶」的限定，不改 findings 本身。**

---

## 决策登记区（人在设计 HARD-GATE 拍板）

```
  ┌──────────────────────────────────────────────────────────────┐
  │ [需拍板·决定性] Q1  方向: A 收敛白名单-only vs B 修前向机制    │
  │ [需拍板] Q2  谓词-diff 时序: 前置阶段承认「预测非机判」?        │
  │ [需拍板] Q3  HR-TG 机判不可行→P1 回归模型判(撤 D7 对 P1)?      │
  │ [需拍板] Q4  calibrator 幸存者偏差→补 shadow-full 采样臂?      │
  │ [需拍板] Q5  LIGHT spec-review 硬地板 or 移出可轻量化集?       │
  │ [自动决策(依赖Q1)] D1-D6  机械修一批(改名/P2/契约/护栏…)       │
  └──────────────────────────────────────────────────────────────┘
```

### Q1【决定性】前向机制方向——收敛简化 vs 保留修复

冷审共识：前向机制在前置阶段**不可靠**（Q2/Q3）且**净收益薄**（B1）。两条路：

- **选项 A · 收敛为「白名单-only 机判轻量化」**（对抗 B-4 + A 力荐）：**砍掉整个前向谓词路由 + calibrator**，只在 **code-review 入口（diff 已存在）** 做**机判无逻辑面白名单**（注释/test/版本，配语言感知解析 + markdown=行为的 TG-27 路径清单）→ 免 Step2 多镜。即**只保留 D6 的 Step2 白名单豁免、砍掉前向全套**。消除时序矛盾（白名单在 diff 后判）、消除 calibrator 偏差、消除 HR-TG 机判难题。机制成本降一个量级。
- **选项 B · 保留前向 router，补时序/判断模型修复**：承认 ff/grill 路由是**预测非机判**（Q2）、P1 回归模型判（Q3）、补 shadow-full 采样（Q4）、定义 LIGHT 硬地板（Q5）、门核剥离为 LIGHT-independent 恒跑（B3）。修复面大，且 ROI 仍薄。

**三面后果**：
- **系统镜**：A 大幅降复杂度/维护面、消除 3 个致命簇（时序/HR-TG机判/门核正交多由前向而生）；B 保留自适应弹性但机制永久重、且多处仍不可证完备。
- **用户镜**：A 收益收窄为「白名单形状省 Step2」（小但真、零语义风险）；B 名义收益宽（省 spec-review 多镜）但命中窗口窄、且 LIGHT 有坍缩为自评之险。
- **开发循环镜**：A 一次性把「安全的省」落地、把「不安全的省」诚实放弃；B 把复杂度和一串未决判据长期背在 workflow 地基上。

**推荐 = A（收敛白名单-only）**。**主次判定**：本决策**系统镜为主**——冷审证明前向机制的三个致命簇（时序/HR-TG-机判/门核正交）**都源于「在 diff 前用脚本机判语义」这个不成立的前提**，B 的修复是给一个前提有裂缝的机制打补丁；而 A 把轻量化限定在**唯一真正机判可靠、diff 已在、语义面为空**的白名单形状上，是「安全的省」的最大诚实子集。用户镜的「B 名义收益更宽」是次要——B1 已证那收益被 D4/D6 抽掉、实际不宽。

### Q2〔A1/A2〕若保留前向（选项B）：谓词-diff 时序 MUST 显式承认「预测非机判」
pre-diff 阶段（ff/grill）只能用 specs-delta/proposal Impact 等预测信号，且 MUST 声明「grill-skip 推荐基于预测、非机判事实」；diff 派生谓词（P2/P4 白名单）机判推迟到 code-review 入口。**默认处理**：若选 A，此问消解。

### Q3〔A2〕HR-TG 机判不可行 → P1 回归模型判（撤 D7 对 P1 的「全机判」）
HR-TG 8/9 成员语义触发、今天由规划镜头判。**默认处理**：承认 P1 = 模型判（现状），仅 TG-27 path-decidable；D7「掏 L2」只对 P2/P3/P4 成立。**待核验事实**：确认现 workflow 无任何脚本判 HR-TG 的既有实现（接地镜倾向确认）。

### Q4〔B2〕calibrator 幸存者偏差 → 补 shadow-full 采样臂 or 降级主张
默认：承认 LIGHT 逃逸率是有偏下界，MUST NOT 单独作放松证据；补对 LIGHT 样本按比例事后 shadow full-review 校正基准，否则删 D3「后向是信任前向的前提」的强主张。

### Q5〔B5/A-F4〕LIGHT spec-review 硬地板 or 移出
「autoplan-lite/单遍自查」全文无定义 → 实现取最小值=自读=自评。默认：给硬地板（至少保留 eng 镜 + 一次接地读码，MUST NOT 坍缩纯自读），或从可轻量化集移除 spec-review（收益本薄）。

### 自动决策（机械修，**依赖 Q1 定向后执行**，此处登记不预改）
- **D-fix1**〔接地§3-A〕code-review MODIFIED 标题**沿用原名**「sdflow-code-review 为每次全跑的独立强制主审」（保 OpenSpec 定位）。
- **D-fix2**〔codex#2〕P2 重定义：specs-delta→改 canonical `openspec/specs/**`/公共契约套件；新增文件→限非测试非文档生产 codepath。
- **D-fix3**〔接地§4〕补 lens-metric 契约 schema 扩展条目（新锚形 or 新 layer 值 + 是否升 v2）。
- **D-fix4**〔接地§6/codex#3〕route.py 显式继承 ship_gate fence-aware/声明式解析 + 定源路径 `assets/workflow/tools/` + CLI/退出码/JSON 契约。
- **D-fix5**〔对抗B-3/E2〕加硬编码路径元层护栏（与 TG-27 部署解耦）。
- **D-fix6**〔codex#4〕平凡声明落 `ff-generation-constraints.md` + 机器锚格式。
- **D-fix7**〔B-6/C3〕版本常量白名单收窄为「证明无 code-path 依赖」；tests/ 免 Step2 加「过 Step1 scope-drift」。

> 若 Q1 选 A（收敛白名单-only），D-fix1/D-fix4（route→仅白名单判器）/D-fix7 仍需，D-fix2/D-fix3/D-fix5/D-fix6 及 Q2-Q5 大部**消解**（无前向谓词/无 calibrator/无 pre-diff 路由）。

## 度量锚（lens-metric，config metrics.enabled=true；采纳/裁掉为 pre-gate 草稿值，拍板回写最终化〔SR-M〕）

<!-- sdflow:hr-tg v1 hit="none" evidence="meta/workflow bundle 变更,现 HR-TG 子集(TG-04/06/07/08/09/16/17/26)无元层成员——正是 finding A2/E2 缺口;拟新增 TG-27 尚未部署" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="" findings="5" truncated="false" -->

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="12" 采纳="11" 裁掉="0" defer="1" 独立="7" sev="致0/高8/中4/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="3" sev="致0/高2/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="2" sev="致0/高3/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->

> `domain` 镜 N/A（无领域清单命中，不落锚）；`broad` mode=simulated（未原生 autoplan，见顶部诚实声明）。数值一致性 = 主 session 信任边界、非机械门。独立列：adversarial 高（时序/门核正交/循环/calibrator/ROI/LIGHT未定义/中间带多为其独有）、codex 独立 2（平凡声明-ff入口 + buglist逃逸字段为其独有）——**codex 与 claude 镜独立贡献并存，印证跨模型非冗余**。

## 结论

**不建议直接进设计 HARD-GATE 批准 → writing-plans。** 本轮冷审证明设计有**方向级问题**（Q1），需用户先拍 Q1（强烈建议**选项 A 收敛白名单-only**），据此大幅重写 design/spec 后**再走一轮轻量 spec-review 复核**方进实现。

□ 建议进 writing-plans　　■ **需设计门先拍 Q1 方向 + Q2-Q5，据此重写后复审**

## 设计门拍板记录（2026-07-06）

**Q1 = A（收敛白名单-only）**。用户在设计 HARD-GATE 裁定：**砍掉整个前向谓词路由 + calibrator + 托管块 + route.py-at-ff + HR-TG 双向化 + 四谓词 + 平凡声明**，收敛为——**只在 code-review 入口（diff 已存在）机判「无逻辑面白名单形状」，命中则免 Step2 多镜；Step1 恒跑守卫**。

**据此**：Q2/Q3/Q4 消解（无前向/无 pre-diff 路由/无 calibrator）；Q5 消解（不轻量化 spec-review）。保留并强化的 D-fix：**D-fix1**（code-review MODIFIED 沿用原标题）、**D-fix4**（判器沿 ship_gate 纪律、定源路径/契约）、**D-fix7**（版本常量收窄、tests/ 过 Step1）+ **C1 markdown=行为路径清单**（bundle SKILL.md/workflow.md/ship_gate.py/评审 skill 等属行为面，即便 diff 是 markdown 也 NOT 无逻辑面——这吸收了原 TG-27 元层护栏 E2）。

**未写 `design-approved` 锚**：A 需据此重写 design/spec/tasks 后走一轮**轻复审**（改动集中在一个机判判器 + 一条 MODIFIED 需求，remaining risk 低）方最终批准。

## 轻复审结论（A 重写后，自审·declared）

A 重写把 change 收敛为「code-review 入口无逻辑面白名单判器 + 一条 code-review 需求 MODIFIED」。**原 4 冷源的存活 findings 逐条核对已在 A 中消解或消失**：

- 时序矛盾/HR-TG机判/门核正交/calibrator偏差/ROI（簇A/B）→ **随前向机制整体删除而消失**（无对应组件）。
- C1 markdown=行为 → A3 行为面路径豁免清单（bundle 自身）+ 白名单①收窄为约定文档路径、任意其他 `.md` 默认 NOT（补消费仓行为-markdown 残洞）。
- C2 P2 specs-delta 矛盾 → P2 已删（无面谓词）。
- C3 净行非确定性/版本常量/tests helper → 版本常量整行拒 token、tests/ 排除 import helper、判器语言感知（非裸正则）。
- D1 MODIFIED 改名破匹配 → **沿用原标题**「sdflow-code-review 为每次全跑的独立强制主审」。
- D2 lens-metric 无槽 → 已删（无 calibrator）。D3 route.py fence-aware → 判器只读 diff 不读散文声明，假阳场景消解。
- E2 TG-27 引导期 → A3 硬编码路径护栏、与部署解耦。

**残余（已知、低危、实现期处理）**：语言感知判器的语言子集起手保守；tests/ 免多镜靠 Step1+helper 排除双收窄；消费仓文档路径扩展留 todolist。

**判定**：A 是「安全的省」的最大诚实子集，remaining risk 低。**建议设计门批准 A**（不 gate 实现的残余均保守默认偏 Step2 照跑）。

**设计门批准 concrete A（2026-07-06）**：用户在 HARD-GATE 批准收敛版 A（code-review 无逻辑面白名单免 Step2）。轻复审通过、冷审存活 findings 逐条消解、remaining risk 低。放行阶段三。

<!-- ship-gate: design-approved -->

