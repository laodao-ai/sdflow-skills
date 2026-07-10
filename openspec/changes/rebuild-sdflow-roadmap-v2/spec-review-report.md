# spec-review-report — rebuild-sdflow-roadmap-v2

> 评审对象：`openspec/changes/rebuild-sdflow-roadmap-v2/` 四件套 @ grill 后 `f9753ce`。
> 三步链：Step1 autoplan 广审（native，六声 58 条，落盘 `gstack-review.md` @ `9be41a3`）→ Step2 多镜 fan-out（对抗×2 + 接地×1 + HR-TG cross-model）→ Step3 合并对抗裁决（本报告）。
> 合并池：58（六声）+ 6（对抗A）+ 8（对抗B）+ 13 项接地核验 + 3（hr-tg voice）+ 4（主 session S 系）→ **36 条 canonical（采纳 20 / 需拍板 5 / 已裁掉 9 / defer 2）**，全部修补已以 `[spec-review-amendment SR-N]` 落四件套。

## Step 1 · autoplan 广审

<!-- sdflow:step1-broad-review v1 mode="native" -->

原生执行（native 佐证：3 次 `codex exec` 全 EXIT=0 + 3 个 Claude 独立子代理真实运行痕迹，见 `gstack-review.md` 头注）。六声 = CEO/Eng/DX × Claude 子代理/codex；Phase 2（UI）跳过（0 命中）。findings 全文见 `gstack-review.md`（C1-C7 / X1-X11 / E1-E10 / XE1-XE7 / D1-D12 / XD1-XD11 + 三张共识表 + 审计线索）。

**outside-voice 复用守卫（三前置）**：①来源 native ✓ ②新鲜度：gstack-review.md 晚于 change_dir 最新改动 ✓ ③结构：codex 段解析出 29 条（X11+XE7+XD11）✓ → **复用 autoplan outside voice 29 条，不重开 design-voice**。

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="none" findings="29" truncated="false" -->

## Step 2 · 规划镜头与 fan-out

- **TG 判定**：命中 TG-06/08/10/12/14/19/21/22/23/25；不命中 TG-01/02/03（纯 Markdown，**零领域镜**）、TG-18（零脚本）、TG-17（N/A 已声明）。
- **镜配置**：对抗镜 ×2（隐藏假设 / 失败模式边界）+ 接地镜 ×1（13 项事实核验，含跨仓声明裁决）。防重叠：autoplan 已含 eng 视角，本层不重复。
- **HR-TG 判定**：命中集 ∩ HR-TG 子集 = {TG-06, TG-08} ≠ ∅ → 单开领域 cross-model（site="hr-tg"，codex，3 条 findings）。

<!-- sdflow:hr-tg v1 hit="TG-06,TG-08" evidence="删除共享契约文件 requirements.md 改三方共享数据模型边界(TG-06) + 新增 matt 套件跨 skill 运行时依赖(TG-08)" -->

<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="none" findings="3" truncated="false" -->

**接地镜关键裁决事实**（13 项：10 CONFIRMED / 2 REFUTED / 1 关键新事实）：
- C1 跨仓消费 **CONFIRMED**（zhws_ops_api 归档 staff-review-report.md:62 实质消费 requirements.md；10-michi spec:16 MUST 场景要求四文件；路径与 CEO 子代理原引略有出入但实锤成立）。
- REFUTED ×2：references/ 实为 **6** 个模板文件（原清单计 5，漏 long-flow-skill-paradigm.md）；setup 种子 Explore 步查 docs/agents/ **及** .scratch/（E7 细节失准，但「检不出 openspec/matt/ 定制」结论仍立）。
- 新事实：`~/.codex/skills/` **无 wayfinder**（matt 套件仅 Claude 宿主装载）→ Codex 宿主上长档路由必然降级。
- `metrics.enabled: true` → 本轮落 lens-metric 锚。

## Step 3 · 裁决表（canonical findings）

> hits 记命中镜集合（B=broad 六声 Claude 侧+主 session；DV=outside-voice/design-voice（codex 六声）；HV=outside-voice/hr-tg；A=对抗镜；G=接地镜）。修补全部已落盘。

| # | sev | 问题 | hits | 修补落点 |
|---|---|---|---|---|
| SR-1 | 致 | 「零消费」前提证据面仅本仓；跨仓 8+ 存量包+实质消费实锤+全局 symlink 即时生效+升级不兼容窗 | B(C1,C3)+DV(XD11)+HV(V3)+G | proposal BREAKING 作用域限定+Impact；specs R1 兼容 Scenario；design D1 证据修正+失败表升级窗行 |
| SR-2 | 高 | 结晶不 gate 未决票：frontier 非空可宣告定稿，孤儿票零巡检指回；直接结晶无依据显示 | B(E5,D6)+DV(XE3,XD4) | specs R6 checklist ④项+frontier Scenario+直接结晶依据 |
| SR-3 | 致 | 路由身份不持久（续跑双根）、命名权竞争、map/包再入无约定、判别非可观察 | DV(XE1,XE7)+B(E2,E3,D2) | specs R1 生命周期+R4 命名权/持久字段/再入/续跑 Scenario；design D3 补强；tasks 1.3/3.1/4.1 |
| SR-4 | 致 | wayfinder 链硬调 domain-modeling「当场写」共享 CONTEXT.md/adr——讨论未定稿决策永久入全局真相源；演练噪声同污染（adr/0010 推翻先例） | A(A1,A2) | specs R6 checklist ⑤项+ADR 冲突 Scenario；design D4 写入纪律；tasks 4.1 基线+revert |
| SR-5 | 高 | 事中触发升级在最需要时不可判定（压缩后信息已有损；D6 撤走唯一持久载体）——grill Q1 修正案残余面 | DV(XE2)+A(A3,B5) | specs R3 压缩 flush Scenario（该场景 memo 转必需+双来源承认）；tasks 1.2/2.3 |
| SR-6 | 高 | 「四件套」sweep 撞 change 四件套概念（spec-workflow:420-424 活规范勿触）+漏 01-goals:153 | B(E1)+G | design scope-check 排除名单+补漏；tasks 6.1 语境判读 |
| SR-7 | 高 | review 契约束缺失：整体 plan 话术无存活保证、跳过无授权边界、无逃生舱、依赖失败零 UX、默认无覆盖条款 | B(D5,D1,D7)+DV(XD2,XD3)+A(A4) | specs R5 全面重写+R1 逃生舱；design 失败表 review 行；tasks 1.1/1.4 |
| SR-8 | 高 | 补细绕过质量门（野心信号中途出现无重判）+前序部分放弃永久阻塞 frontier | DV(XE4)+A(B3,B8) | specs R7 补细重判+终局放弃 Scenario |
| SR-9 | 高 | 可用性探测硬编码 Claude 路径破坏双宿主契约（接地：Codex 侧现无 wayfinder）+上游套件语义漂移无检测行 | DV(XE5)+HV(V2)+G+B(S1) | specs R3 宿主降级 Scenario；design 失败表宿主中立+漂移行；tasks 6.2 |
| SR-10 | 高 | R4 是全局能力规范但前置只落本仓 tracker doc——消费仓无 tracker 时无 fail-closed | HV(V1) | specs R3 preflight fail-closed；design 失败表新行；tasks 1.2 |
| SR-11 | 中 | 无雾自降级分支推理无处沉淀（两头都没有）+chart 先建后删执行顺序冲突 | A(B4)+DV(XD6) | specs R3 无雾 Scenario 补留痕+预检 |
| SR-12 | 中 | 收尾 checklist 非可判定契约（引用完整无引用图定义、失败不报行号）+无完成边界提示 | DV(XD7)+A(A5)+B(D10) | specs R6 ②项钉死最小引用图+报行号+commit 软提示 |
| SR-13 | 中 | R2 头部章丢失旧 requirements 核心承载槽（验收总纲/需求清单）+二分不穷尽（混合/探索型） | DV(XD8)+A(B2) | specs R2 验收门槛槽+占位槽+兜底 Scenario；tasks 2.1 |
| SR-14 | 中 | 近细远雾对 3 阶段无决定规则、雾区备注空泛、长周期依赖例外缺失 | DV(XD9)+DV(X9 部分) | specs R7 选择理由+缺失信息+例外条款；tasks 2.2 |
| SR-15 | 高 | 迁移工程面：design 编号级联位移、下游归档 change 死引用类别遗漏、活跃演进窗对撞、清点表无落盘、scan 排末尾、考古注记不可发现 | A(B6,B7)+B(E6)+DV(XE6,XD10)+HV(V3 部分) | specs R2 不占编号；design Migration 全面重写+scope-check 补类别；tasks 5.1-5.3 |
| SR-16 | 中 | drill 测错对象（预供路径测不到路由）+claimed 票搁浅无重认领+Task 票型与规则 5 未对齐 | B(E8,E4,E9,D12)+DV(XE1 尾) | tasks 4.1 重构（真实调用起步+中断恢复）；specs R4 重认领 Scenario；tasks 1.2/3.1 |
| SR-17 | 中 | 回退落 matt/ 的 wayfinder 票会被 triage 当 Unlabeled 误吞改写状态机 | A(A6) | specs R4 triage 边界 Scenario；design 失败表注记；tasks 3.1 |
| SR-19 | 低 | 事实失准三处：假设 3 读点表述、模板计数 5→6、setup 重跑行为描述（含 `git checkout` 整目录恢复不安全） | B(E10,E7,D11)+DV(XD5)+G | proposal 假设 3 修正；design 组件清单+失败表 setup 行（非破坏恢复） |
| SR-20 | 中 | Success Metrics 乐观偏置：≤2 处被现存 duplication 自证伪、100% 存活性未限定范围、阶段数易误读为提速 | A(B1)+DV(X1 部分)+B(D9) | proposal 三行指标各补机械口径/范围/脚注 |
| SR-21 | 低 | footage 术语无面向包内浏览者的路标 | B(D8) | specs R4 map 顶部路标行；tasks 1.3 |

## 决策登记区

**〔自动决策〕**（高置信默认采纳，设计门可覆盖）

- AD-1 前提门：三前提仓内实证成立（证据 scope 修正另由 SR-1 落盘）。
- AD-2 0C-bis 三方案对比选 A（=grill 后现设计；B 留两大实证痛点、C 被 D1/Non-Goal 2 先决）。
- AD-3 SELECTIVE EXPANSION 扩张扫描零新增候选（Non-Goals 可证伪假设已穷举）。
- AD-4/AD-7 autoplan 模式锁定与双声全跑（细节见 gstack-review.md 审计线索）。
- AD-5 office-hours 前置 offer 判「实质已满足」（change 自带 design.md）——注意与 Q-D（office-hours 分支去留）是两回事。
- AD-6 gstack 升级 1.58.5→1.60.1 推迟至评审后（工具链稳定优先）。
- AD-8 SR-1..SR-21 共 20 条采纳修补按上表落盘（本报告即变更说明，设计门逐条可翻）。

**〔需拍板〕**（设计门一次过）

- **Q-A · 规则 3 禁引 footage/memo vs 受控带类型引用**〔X7，UC：挑战 grill Q2 拍板〕
  codex 主张禁引「以禁止可追溯性掩盖双写问题」——精炼写入丢证据/反例/被拒方案，半年后没人知道约束为何存在。
  **推荐：维持禁令（grill Q2 原拍板）**。理由：①考古层 git 永存+map Decisions-so-far 本身就是结构化决策索引，「为何存在」查 footage 即得（禁的是**正文引用**非物理销毁）；②本仓「权威源纯净」一贯纪律（memo 规则 3 数年惯性）；③受控引用需要定义引用类型词表=新机制面。三面后果：系统镜——维持则引用图简单、翻则需类型词表与 lint 面；用户镜——维持则查证据多跳一步、翻则正文变长；开发循环镜——维持零新机制。**主判定：系统镜为主**。
- **Q-B · review 分档轴：产品野心 vs 不可逆性/承诺量**〔X8+C2〕
  **推荐：维持野心轴 + 试点观察**。样本偏斜已在 D1 披露（SR-1）；SR-8 已补「补细命中信号重判」堵中途漏洞；试点期若单审实漏重大不可逆决策，届时升轴（有实证再改，不预设计）。
- **Q-C · 存量迁移执行前置「首个新流程 roadmap 已走通」**〔X11 折中〕
  **推荐：接受**（已写入 design Migration 前置②与 tasks 5.1，拍板确认即生效；不接受则删该句，迁移只受「无在飞实施 change」约束）。
- **Q-D · office-hours 分支去留**〔D3：现行 SKILL.md:92-101 有、新蓝图零提及，属重写连带丢失非拍板决定〕
  **推荐：保留为讨论层第三分支**（产品野心信号 → 前置 /office-hours 验证需求真实性；与 review 分档共用同一信号词表，逻辑自洽零新判据）。已在 proposal Impact 与 tasks 1.2 挂「按 Q-D 拍板落实」钩子。
- **Q-E · 战略 gut-check（告知级，不改盘面）**〔C5+X1〕
  双模型同问：7 天 31 归档 change 多为流程自指精化，下一个最高杠杆动作是否应为消费仓外部可见交付？本 change 动机实证充分、照常推进；此问供 roadmap 层面思考，无需本 change 内动作。

**〔已裁掉〕**（反静默压制：原始发现+裁掉理由，供设计门复核）

- X-1〔X2〕「≤2 处=允许漂移，应先定义每类事实归属再定文件数」——机械口径已由 SR-20 落盘（禁同值重复只准引用）；「先归属后文件数」时序翻案无增量证据，D1 消费侧不对称仍是决定性证据。
- X-2〔X3〕「去壳去掉生命周期边界，soft checklist 六个月后=可忽略文本」——D2 四收益逐项核查未被新事实推翻；checklist 可判定化（SR-12）+五项扩展（SR-2/4）已实质加固；「保留状态记录」诉求由 task-log 留痕承接。
- X-3〔X5〕「包内自声明替代全局 tracker doc」——机制不可达（wayfinder 只读 tracker doc，包内声明它看不见）；其精神已被 SR-3 map 持久字段吸收（首次落点 tracker doc 分流、身份活在包内）。
- X-4〔X6〕「分档判据应含不可逆性/依赖度/失败代价」——轴之争入 Q-B；「跨 session 升级=信息已丢」已被 SR-5 吸收。
- X-5〔X9 整体〕「承诺层级+滚动复盘替代近细远雾」——例外条款已采纳（SR-14 长周期依赖）；整体框架替换无本仓反例支撑（adr/0010 实证站在近细远雾一边）。
- X-6〔X10〕「先产品型试点再宣称支持产品型」——Non-Goal 5 可证伪假设已覆盖（首个实例触发再深化）；SR-13 已补槽位+兜底，模板骨架风险受控。
- X-7〔C7〕「design 增长判据引用了同 design 判过长的文件」——修辞层弱点，D1 主论证是消费面不对称非长度对比；无行动价值。
- X-8〔XD1 强制入场问答/routing card〕——与「低仪式」目标冲突；可观测性已要求判定点显式陈述一行（+SR-2 直接结晶依据 = 第四点），等价轻量物已在。
- X-9〔C2 重采样要求〕——跨仓样本存在性已由接地镜证实并入 SR-1 披露；专项重采样成本不成比例，试点观察承接（Q-B）。

**〔defer → todolist〕**（done 阶段 sweep 时落池，显式挂 change=rebuild-sdflow-roadmap-v2）

- DF-1 maintain_scan（或独立 preflight 脚本）机械断言 tracker doc footage 分流句在场〔C6+X3 部分——机械固化哲学的完整落地，超本 change scope〕。
- DF-2 消费仓 tracker doc 初始化资产入 sdflow-init bundle〔V1 后半——铺设面变更另立 change〕。

**低置信一行带过（不静默滤）**：B2（混合型判档，中置信）已并 SR-13；B4/B7（中置信）已并 SR-11/SR-15；A6 条件性（依赖回退先触发）已并 SR-17——均已采纳，无遗留低置信项。

**杂项 note**：本分支 CONTEXT.md footage 词条与 matt-workflow-integration 分支 ticket 词条同位追加 → merge 时保留双方（S10b）；两 change 归档串行约束（openspec/specs 能力表尾）本 change 侧已由此行登记（S10a）。

## 图验证（design-diagrams：只验不重画）

- 组件依赖图：正确，SR-3/SR-10 后仍成立（tracker doc 注入点+第二锚关系未变）。
- 序列图：已随评审补 preflight/持久字段/五项 checklist 三处注记（原图缺前置与闭环步，过时点已修）。
- 分档路由决策图：grill Q1 重绘版正确；SR-5 压缩 flush 属 R3 文本细则，不改图形结构。

## lens-metric（Step3 裁决锚，设计门拍板后最终化〔SR-M〕）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="10" 采纳="10" 裁掉="0" defer="0" 独立="2" sev="致1/高4/中5/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="18" 采纳="12" 裁掉="2" defer="4" 独立="1" sev="致2/高5/中3/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="0" sev="致1/高2/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="27" 采纳="15" 裁掉="7" defer="5" 独立="1" sev="致2/高6/中6/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="hr-tg" findings="5" 采纳="4" 裁掉="0" defer="1" 独立="1" sev="致1/高3/中0/低0" -->

残余信任边界声明：分类正确性（finding 归镜）、roster 完备性、findings JSON 誊写准确仍是主 session 信任边界；emitter 只保证确定性归约。采纳/裁掉/defer 为设计门拍板前临时裁决，拍板回写时最终化〔SR-M〕。

## 收敛口

20 条采纳修补已全部落盘（specs 7 处 Requirement 强化 + design 8 处 + proposal 5 处 + tasks 全组），5 项需拍板（Q-A..Q-E，均带推荐）。**建议进设计 HARD-GATE**：过本报告逐项拍板（重点 Q-A 维持/翻、Q-D office-hours 去留）后即可批准进入实施。
