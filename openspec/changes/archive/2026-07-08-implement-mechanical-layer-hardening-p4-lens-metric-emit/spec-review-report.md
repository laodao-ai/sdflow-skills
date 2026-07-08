---
ship-gate:
  design_approved: true
---

# Spec-Review 报告 · implement-mechanical-layer-hardening-p4-lens-metric-emit

> **设计 HARD-GATE 已拍板批准 · 2026-07-08**（用户过本报告批准 → writing-plans）。ship-gate 机判锚见头部 frontmatter；下方 lens-metric 锚已按〔SR-M〕最终化。

<!-- sdflow:step1-broad-review v1 mode="simulated" -->

> **评审构成**：Step1 广审（模拟 autoplan CEO/design/eng/DX + 真实 codex design-voice）→ Step2 并行 6 镜（领域·backend / 对抗×3 / 接地 / codex hr-tg）→ Step3 合并对抗裁决。**8 个独立源**（6 子代理镜 + 2 codex 声音 + 广审），全程 fresh-context、无 `/clear` 依赖。
>
> **TG 命中**：TG-25（契约套件变更）· TG-06（跨模块共享数据模型边界→D-6，**∈ HR-TG**）· TG-14（新组件）· TG-11（数据管道）· TG-23（≥2 方案）· TG-18（测试计划）。
>
> **T20 串行纪律说明**：Step2 多镜与 Step1 广审并行 fan-out（省墙钟）。已核对——Step1 广审只产 `gstack-review.md` findings 报告、**未 amend design/specs**，故无「autoplan amendment 增量」被多镜漏审；实质合规。
>
> **总裁决**：**不建议进设计 HARD-GATE**。收敛揭出 **4 条结构性缺陷**（C1 roster 粒度 / C2 折叠恒等语义 / C3 漂移守卫空转 / C4 反方向静默漏计）+ **4 条 fail-closed 边界缺口**（C6 config / C7 site 注入 / C11 空 lenses / C12 采纳缺 sev），多为**回改 spec R1/R2 与 ADR** 才能补、非补测试可弥。建议先过一轮设计 amendment 再拍板。

---

## 决策登记区

```
  spec-review-report.md · 决策登记区
  ┌───────────────────────────────────────────────────────────────────────┐
  │ [需拍板] Q1  roster schema：canonical lens 列表 → (lens,runner,site) 三元组？ │  结构性·7 镜命中
  │ [需拍板] Q2  折叠恒等语义：fold(raw)=raw if∈enum elif map else fail-closed？  │  结构性·4 镜命中
  │ [需拍板] Q3  漂移守卫方向：4.2 改断言 fold_codomain⊆lens-enum + agg==enum？   │  核心卖点·守卫空转
  │ [需拍板] Q4  finding 折叠出 lens∉roster → fail-closed（反方向不变量）？        │  反静默·静默漏计
  │ [需拍板] Q5  config 门控归属 + 坏块 fail-closed（emitter 自读须复刻四态）？    │  dogfood 分治盲区
  │ [需拍板] Q6  --layer vs finding.layer 口径（建议删 finding.layer、单一源）？   │  design 无 ADR
  │ [自动决策] D1  广审 F1+F2 默认接受阻断（= C17+C1）                            │  高置信→默认采纳
  │ [自动决策] D2  接地订正 design:6 行号 / design:9 aggregator 假事实（已 amend）  │  已回流
  │ [已裁掉] X1  adv3 F-H 新旧混合锚跨轮口径（refuted=true·aggregator caveat 兜底） │  记录不丢·view-only
  └───────────────────────────────────────────────────────────────────────┘
```

---

## 合并去重 findings 池（对抗裁决后）

> 命中镜集折叠到 canonical lens：广审→broad · design-voice/hr-tg→outside-voice · 领域→domain · 对抗1/2/3→adversarial · 接地→grounding。裁决：采纳=直接采信 / 需拍板=进 Q 区 / 裁掉=反驳成立。**escalate-not-drop**：判不成立者也落「已裁掉」区留痕。

### 结构性缺陷（HARD·需拍板）

**C1〔采纳·高·7 镜命中〕roster 粒度只到 canonical lens，无法承载零-finding 行必需的 (runner,site)**
命中镜：broad·domain·adversarial(adv1/2/3)·outside-voice(design-voice+hr-tg)。
- 锚唯一键 = `(layer,lens,runner,site,轮)`（契约:3），`anchor_lint.REQUIRED_FIELDS` 强制每行含 `runner`（:24）。但 ADR-1/ADR-5 定义 roster = 纯 canonical lens 列表（design ADR-1 / spec lens-metric-emit:5），**不带 runner/site**。
- emitter 为零-finding 镜落行（roster 存在的唯一理由）时**无 finding 可反推 runner/site**：`outside-voice` 零行 runner∈{codex,claude-fallback}、site∈{code-voice,hr-tg,design-voice} 均无源 → 只能瞎编（如 runner=claude，但 outside-voice 恒非 claude → 锚语义假、污染 aggregator 按 runner 聚合）。
- **与自身 SR-D 冲突**：若 codex(design-voice) 与 codex(hr-tg) 两次都零 finding，SR-D 要两行，roster 只列 `outside-voice` 一次 → site 拆分在零-finding 路径**不可实现**。
- **附 adv1 F4**：独立计数按 canonical lens 但 site 拆多行 → 独立数归到哪 (lens,site) 行未定义（归属粒度 lens vs 落锚粒度 lens,runner,site 错配）。
- **推荐修**（Q1）：roster 元素升为 `{lens, runner, site?}` 三元组列表，emitter 按三元组落零行；归属/独立键统一到 `(lens,runner,site)`。改 ADR-1/ADR-5/数据流图 + spec R1 roster 定义 + 零行 Scenario 补 site。

**C2〔采纳·高·4 镜命中〕折叠「恒等项可省略」建立在 raw==canonical 的类别错误**
命中镜：broad·domain·adversarial(adv1)·outside-voice(hr-tg)。
- tasks 1.4 称 fold 块「恒等项 domain/grounding/history/broad 可显式或省略」。但契约折叠表实为**中文→英文非恒等**映射：`领域镜→domain · 历史镜→history · 接地镜/完整性镜→grounding`（contract:32-33）——raw 名是「领域镜/历史镜/接地镜」，domain/history/grounding 是 canonical 目标、**根本不是恒等 raw 项**。
- 若实现按 1.4 省略这些，则 reviewer 报的常见 raw 名 `fold("领域镜")` 查不到 → 按 tasks 2.2「未知 raw→fail-closed」→ **emitter 对最常见输入非零退出**。反之加「raw∈enum 则恒等」兜底又与 SR-E「未知 raw 不静默」口径打架。二义未决=实现掷硬币。
- **推荐修**（Q2）：钉死 `fold(raw) = raw if raw∈lens_enum（恒等 pass-through，复用 enum 块不复制清单）; elif raw∈fold_map; else fail-closed`；fold 块只列**非恒等**映射；写进 spec+task。

**C3〔采纳·高·3 镜命中〕漂移守卫方向反了——4.2 断言在目标漂移下恒真（空转）**
命中镜：adversarial(adv3 最锐)·outside-voice(hr-tg)·adversarial(adv1 F6)。
- tasks 4.2 断言 `aggregator 的 canonical lens 集(6 硬编码) ⊆ fold_codomain`。但它声称防的漂移是「fold 块新增 `某镜: newlens`，newlens∉lens-enum」——此时 fold_codomain=7 值，`aggregator(6) ⊆ fold(7)` **仍成立** → 4.2 绿 → 漂移未拦。**本 change 核心「根治漂移」卖点的唯一机械守卫是空转的**。
- emitter `load_fold` 自身不校验「fold 输出∈lens-enum」（spec/design 未要求）；唯一兜底 anchor_lint 运行期 out-of-enum(:178) 要等该 raw 真出现在某轮 findings 才触发。
- **附 F-G**：v1 不升版本 + fold 块加映射到新 canonical 无机械门拦（治理靠人判）。
- **推荐修**（Q3）：4.2 改断言 `fold_codomain ⊆ enums.lens`（双向）+ `aggregator.LENS_ENUM/LAYER_ENUM == enums`（把 aggregator 硬编码纳漂移守卫，兼收 hr-tg#4/C23）；emitter `load_fold` 后自校验 codomain⊆lens-enum fail-closed。

**C4〔采纳·高·2 镜命中〕finding 折叠出的 canonical lens ∉ roster → 静默漏计（反方向未处理）**
命中镜：domain·adversarial(adv3 F-B)。
- tasks 2.8 只处理 roster⊇findings 方向（补零行）。反方向：一条 finding 的 lenses 折叠成合法 canonical X（fold 成功、非未知 raw）但 X∉roster → emitter「为每个 roster lens 落一行」下，X 的计数进内部累加器却**无输出行** → findings/采纳/独立/sev **静默蒸发**，违反本 change 反复援引的反静默元原则。
- **推荐修**（Q4）：不变量「所有 finding 折叠后 canonical 集 MUST ⊆ roster，否则非零退出报明」+ 失败测试。

### fail-closed 边界缺口（需拍板/采纳）

**C6〔采纳·中(高潜在)·4 镜命中〕config metrics 门控归属未定 + 坏块 fail-closed 缺失**
命中镜：broad·domain·adversarial(adv2)·outside-voice(design-voice)。
- ADR-5 Scenario「metrics 开时强制 broad/outside-voice 行」判据 = `metrics.enabled 为真`，emitter 须自求 `metrics_on`；但 CLI `--layer --input`（design:37）**无 `--metrics-on` 旗标** → emitter 只能自读 config.yaml，而禁 import yaml → 须**重实现** anchor_lint `read_metrics_enabled` 四态（:109-131：缺文件→关/无块→关/**块坏→MetricsError fail-closed**/解出→bool）。tasks 3.4 只测「关→exit0」、**漏坏块**（MEMORY dogfood「缺失=放行 vs 存在坏=fail-closed 要分治」盲区）。若图省事把「非 true」当关→坏 config 上 fail-open 静默 no-op，与 anchor_lint 走 EXIT_ERROR **口径分歧**，破 ADR-4。
- **推荐修**（Q5）：钉死 gate owner。若 emitter 自读→复刻四态（坏块 fail-closed 非零退出）+ 坏-config 测试；若信 SKILL 门→删 emitter config 读取、proposal 改「由 SKILL 门控」。二选一，勿两不管。

**C7〔采纳·中·2 镜命中〕site 值未消毒 → 注入破坏锚语法且绕过 anchor_lint**
命中镜：adversarial(adv2)·outside-voice(design-voice)。
- site 是自由文本（来自 finding），anchor_lint 明文对 site 免检（REQUIRED_FIELDS 不含 site，:24）。emitter 直接拼进 `site="..."`。site 含 `"` → anchor_lint `_KV=([^\s=]+)="([^"]*)"`(:19) 在内嵌引号处截断、吃掉/错位后续字段（如 findings=），锚被腐蚀却仍「过」lint；含换行→锚跨两行；含 `-->` → 提前闭合注释、后半泄进正文。下游校验者恰对该字段免检 = 无守卫。
- **推荐修**：emitter 拒绝 site 含 `"`/换行/`-->`/`=` → fail-closed；spec R2 坏输入清单补此类。（可与 Q5 一并纳入 R2 扩充）

**C11〔采纳·高·1 镜〕`lenses:[]` present-but-empty 绕过缺字段检查 → 静默丢失**
命中镜：adversarial(adv2 F4)。空数组过了「缺 lenses」检查，折叠后 canonical 集空→无 lens 记 +1、独立不计→该 finding 贡献 0 静默吞。**推荐修**：`lenses` 必须非空数组为 fail-closed 条件 + 测试。

**C12〔采纳·高·2 镜命中〕采纳项缺 sev → sev rollup 静默少计（条件必填未定义）**
命中镜：adversarial(adv2 F5)·domain(F7)。sev rollup 仅计采纳项，故 sev 是条件必填(iff verdict=采纳)，但 spec/design 未定义。采纳项缺/空 sev → rollup 从四级全漏，产格式合法但 Σsev<采纳 的错锚（anchor_lint 只查子格式不查 Σsev==采纳）。**推荐修**：`verdict=采纳 ⟹ sev∈{致,高,中,低} 必填非空 else fail-closed`；加不变量 `Σ(致+高+中+低)==采纳` 自检 + 测试。

### 收窄类 / 一致性 / 测试健全（采纳·中低）

**C5〔采纳·中·4 镜命中〕「emitter 输出过 anchor_lint exit 0」过度声明**
命中镜：broad·adversarial(adv1/adv3)·outside-voice(design-voice)。`anchor_lint.main` 无条件先跑 `check_existence`(:217)，强制 MANDATORY=(outside-voice,hr-tg,step1-broad-review) 三**非-lens 锚族**存在(:148-150)；emitter 只产 lens-metric 锚 → check_existence 报 3 missing → exit 1，绝不 exit 0。ADR-4 正文已正确收窄到 `check_lens_metric`，但 spec Scenario(:45-47)+task 4.1 写「跑 anchor_lint 断言 exit 0」不一致。**推荐修**：task 4.1 fixture 补三族 MANDATORY 锚（模拟真报告）**或** 断言改为「check_lens_metric 无违规」；spec Scenario/ADR-4 措辞同步收窄。

**C8〔采纳·中·4 镜命中〕--layer vs per-finding layer 双源口径未拍板**
命中镜：broad·domain·adversarial(adv1/adv2)。spec:5 要 finding 带 layer、CLI 又 --layer、anchor_lint 硬查 layer==cli(:176)；tasks 3.3 甩「钉死一种口径」给实现、design 无 ADR。**推荐修**（Q6）：design 补 ADR——锚 layer 一律取 --layer，finding.layer 若带 MUST==--layer 否则 fail-closed（推荐直接从 schema 删 finding.layer、单一源）。

**C9〔采纳·中·2 镜命中〕输出行序确定性未定义 + 幂等测试 PYTHONHASHSEED 同进程假绿**
命中镜：domain(F5)·adversarial(adv2 F8)。折叠产「canonical 集(去重)」为 set，按 set 迭代落行 → 跨进程 PYTHONHASHSEED 使行序变；tasks 4.3 若同 pytest 进程内跑两次→序恒定→**假绿**，跨会话不确定漏网。**推荐修**：显式排序键（如 lens enum 序+runner+site）写死 + 幂等测试改**跨 subprocess**（或参数化 PYTHONHASHSEED）。

**C10〔采纳·中·1 镜〕两份 load_enums 独立重实现无「同源同解」等价性测试**
命中镜：adversarial(adv3 F-E)。tasks 1.2 明写「重实现、可与 anchor_lint 同构但独立」；「同读一个文件」≠「同一解析器」，二者对 fence 缩进/trim/闭合判定的细微分歧可读出不同 enum 集，无测试断言 `emitter.load_enums(contract)==anchor_lint.load_enums(contract)`；`load_fold` 更无对照物。**推荐修**：加逐字段等价性测试 + load_fold codomain⊆enums.lens 自校验（并入 Q3）。

**C13〔采纳·中·1 镜〕「绝不产部分锚」仅 prose、无 all-or-nothing 时序 + 非零退出 stdout 未约束**
命中镜：adversarial(adv2 F7)。无 Scenario/ADR 规定「全 findings 校验通过才落任一行」；emitter 输出去向(stdout？直写文件？)+ 非零退出时 stdout 是否空均未写；SKILL「落其输出」(5.1) 未说「先查 exit code」。**推荐修**：硬 Scenario「任一校验失败⟹stdout 无锚行+exit≠0（validate-all→emit）」；SKILL 落锚步 MUST「exit 0 才用 stdout」。

**C14〔采纳·中低·1 镜〕fold 块重复/冲突键、roster 重复 lens 未定义**
命中镜：adversarial(adv2 F9)。`load_fold` 遇同 raw 两次或冲突映射行为未定义；roster 含重复 lens→落两行同键→aggregator 键撞。**推荐修**：load_fold 重复/冲突键 fail-closed；roster 去重或重复即 fail-closed + 测试。

**C16〔采纳·中·2 镜命中〕输入 JSON schema 无单一权威定义、键名中英混杂**
命中镜：outside-voice(design-voice)·broad(F8)。proposal:7 用 `命中镜集`/`裁决`，design/tasks/spec 用 `lenses`/`verdict`，spec 正文又混中文别名指代同字段。模型每轮现拼 JSON、字段名一猜错即 fail-closed 阻塞评审流。**推荐修**：spec 或契约给权威 input JSON schema 块（字段名/类型/域/示例）+ golden fixture，SKILL 落锚步直引。

**C17〔采纳·高·1 镜〕MIN_LENS_ROWS 是 anchor_lint 第二份硬编码、不在契约机读块**
命中镜：broad(F1)。emitter 若为满足 ADR-5 再硬编码强制集=第二拷贝——正是 ADR-2 为折叠表消灭的漂移源、对 MIN_LENS_ROWS 重犯。**推荐修**：把 MIN_LENS_ROWS 提升为契约机读块（如 `lens-metric-mandatory-rows`）anchor_lint+emitter 同读；**或**至少一致性测试断言「emitter 强制集==anchor_lint.MIN_LENS_ROWS」。

**C15〔采纳·低·1 镜〕verdict 枚举未纳入契约机读单一源**
命中镜：broad(F7)。verdict∈{采纳,裁掉,defer} 会成脚本内第三份硬编码。**注**：verdict 是 emitter 输入独有、不写进锚、不与 anchor_lint 共享（跨消费者单一源纪律不严格适用）→ 可作脚本内常量但 design **须显式声明豁免理由**；sev 输入级建议从 sev-format 模板解析（不硬编码）。

**C19〔采纳·高(判断层)·2 镜命中〕「不使其变糟」是乐观账——新错误面未诚实计入**
命中镜：adversarial(adv3 F-C)·broad(F9)。design Risk 断言「不使其变糟、只消计数错误面」是只减不加的账：emitter 引入 **roster 完备性**（漏/多列镜，emitter 无从校验）+ **结构化 JSON 誊写**（verdict 采纳↔裁掉写反、sev 填错，都在枚举域内 fail-closed 抓不到）两道新手工工序。诚实结论应为「算术错误面消除，但分类+誊写+roster 错误面从 1 处终态锚**迁移并细化**到每条 finding，非总错误面单调下降」。**推荐修**：design Risk/ADR-3 补此诚实账（不阻断，但影响本 change 净收益判断=「以更复杂手工输入换算术确定性」）。

### 接地核验（grounding）

**D2 已回流〔自动决策·已 amend〕**
- design:9 aggregator「硬编码折叠逻辑」= 假代码事实（真相：只 group 不 fold，被 ADR-2 自身证伪）→ **已订正**〔spec-review-amendment〕。
- design:6 落锚步行号 :79/:124 落在自检门、非 emission 步 → **已订正**为 :73/:99-101、:110-112/:116〔spec-review-amendment〕。
- **其余代码事实全部核实为真**：MIN_LENS_ROWS@:135 ✓、group_key@:116 只 group ✓、lens-metric-fold 块确不存在 ✓、折叠表映射 ✓、enums 内容 ✓、REQUIRED_FIELDS ✓、exit 码 ✓、零依赖 ✓。

### 已裁掉区（escalate-not-drop 留痕）

**X1〔裁掉·refuted=true〕adv3 F-H：新旧混合锚跨轮口径不可比**
- 原始发现：归档旧锚是手数产、新锚 emitter 归约产，aggregator 混聚二者，历史手数若归属/独立口径有错则跨轮趋势不可比。
- **裁掉理由**：镜自身标 refuted=true；`lens_metric_aggregate.py:176` 已有「独立率跨轮不保证同口径」caveat 兜底，且 aggregator 只呈现不决策（view-only）→ 不构成硬爆点。**建议**：Migration Plan 可加一句「emitter 锚与历史手数锚跨轮不保证口径一致、比对以 emitter 起始轮为准」（记录不阻断）。

**X2〔裁掉·refuted=true〕adv3 F-I：task 7.1 措辞把 prose 断言与可测 Scenario 混为「均有测试锚点」**
- 裁掉理由：非设计爆点、属措辞不精。**建议**（并入 Q 区可选）：task 7.1 区分「机械测试锚点」vs「文档保留锚点」，避免 verify 阶段拿诚实声明 Scenario 当假绿。

> **对抗镜显式放过（refuted=true·确认 spec 已封）**：未知 raw→fail-closed 不塞 broad（SR-E，含负路径断言）✅ · 同类型多实例算独立（对抗镜1+2→{adversarial} size1）✅ · 共抓不计独立（domain+outside-voice）✅ · metrics 关→exit0 空产出（坏块除外见 C6）✅。

---

## 度量锚（lens-metric v1）

> config `metrics.enabled=true` → 落锚。**本轮锚由主 session 手折叠归约**（本 change 提议的 emitter 尚未实现）——正是本 change 要消除的手数环节；计数含 judgment（哪些镜报了哪条、裁决），属残余信任边界。roster：broad·domain·adversarial·grounding·outside-voice(design-voice)·outside-voice(hr-tg)。**〔SR-M 已最终化·2026-07-08〕**：设计门拍板后核对——全部采纳项已落 amendment（无中置信项翻改去向）、X1 维持裁掉，故 pre-gate 计数即最终值、原地不新开行。

<!-- sdflow:outside-voice v1 site="design-voice" guard="simulated-source" runner="codex" reason_code="none" findings="6" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="none" findings="4" truncated="false" -->
<!-- sdflow:hr-tg v1 hit="TG-06" evidence="design 明写 D-6 声明+契约套件 scope-check 表；lens-metric 为跨模块共享契约、本 change 加第 5 消费者且改契约本身(加 fold 块)" -->

<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="9" 采纳="9" 裁掉="0" defer="0" 独立="2" sev="致0/高4/中4/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" runner="claude" site="—" findings="7" 采纳="7" 裁掉="0" defer="0" 独立="0" sev="致0/高4/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="17" 采纳="16" 裁掉="1" defer="0" 独立="5" sev="致0/高7/中7/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="2" sev="致0/高0/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="0" sev="致0/高2/中4/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="hr-tg" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="1" sev="致0/高3/中1/低0" -->

> 锚形示范（勿被聚合器误取，包 fence 内）：
```
<!-- sdflow:lens-metric v1 layer="…" lens="…" runner="…" site="…" findings="N" 采纳="N" 裁掉="N" defer="N" 独立="N" sev="致N/高N/中N/低N" -->
```

> **反馈回路免责**：本报告只落锚，不做聚合/复评/surfacing——跨 change 归档后的锚聚合、按采纳率+独立率复评、出现轮数≥10 提示，一律由 `/sdflow-retro` 聚合，是否保留/降采样/淘汰某镜一律人决。

---

## 收敛口

**初裁（评审当轮）：不建议进设计 HARD-GATE**——8 源高收敛揭出 C1–C4 结构性缺陷 + C6/C7/C11/C12 fail-closed 缺口，需回改 ADR/spec 而非补测试。

### Amendment 回流已完成（用户就分叉①②拍板：①B ②A）

用户同意「两次面治 pass」+ 分叉①B（MIN_LENS_ROWS 一致性测试）②A（折叠恒等 pass-through）。已回流（标 `[spec-review-amendment]`）：

- **Pass 1（输入契约）**：design 新增 **ADR-6~10**（权威 input schema / 恒等 pass-through / 归属键=行键 / 删 per-finding layer / 门控归 SKLL）；spec `lens-metric-emit` R1 升行键粒度 + R2 坏输入穷举（hits:[] / 采纳缺 sev+Σ不变量 / site 注入 / all-or-nothing / 重复键 / C4 反方向）+ R3 收窄 check_lens_metric；workflow-metrics MODIFIED 归属键升行键；proposal 门控措辞改 SKILL；tasks 2.x/3.x 重排。→ 收 C1/C2/C4/C6/C7/C8/C11/C12/C13/C14/C16/C18。
- **Pass 2（单一源）**：design 新增 **ADR-11**（单一源边界清单）+ Risks C3 守卫方向修正（fold_codomain⊆lens-enum 双向 + aggregator enum 一致性 + emitter 自校验）；tasks 4.2~4.5 补 codomain/load_enums 等价性/MIN_LENS_ROWS 一致性/跨 subprocess 幂等测试。→ 收 C3/C10/C15/C17/C23。
- **诚实账/记录类**：C19（ADR-3/Risks 补新错误面账）· X1（Migration caveat）· X2（tasks 7.1 区分机械 vs 文档锚点）。
- **已回流验证**：`openspec validate --strict` ✓ · `anchor_lint` CLEAN。

### 待用户决定：设计 HARD-GATE
amendment 已落，C1–C4 结构缺陷 + 边界缺口均已收口。**是否批准进设计 HARD-GATE（→ writing-plans）由用户拍板**。批准后主 session 须：① 回写 `ship-gate.design_approved` 至本报告头部 frontmatter；② 按〔SR-M〕最终化 lens-metric 锚采纳/裁掉/defer；③ 正文补人读拍板记录行。
