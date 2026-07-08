---
ship-gate:
  code_review: pass
---

<!-- sdflow:step1-broad-review v1 mode="simulated" -->

## code-review 报告 — implement-mechanical-layer-hardening-p4-lens-metric-emit

> **每次全跑·独立冷·强制主审**。8 独立源（gstack/review 广审 simulated + 领域 + 对抗×2 + 历史 + codex code-voice + codex hr-tg），全程 fresh-context。trivial_shape=NOT_EXEMPT（有真实逻辑面）。metrics.enabled=true → 度量锚由本 change 新建的 `lens_metric_emit.py` 归约产出（dogfood 闭环）。

### 命中范围
- 栈：Python 确定性脚本（纯 stdlib bundle tool）。清单：CR-01~09 base。
- gstack/review（simulated 广审）：**scope 干净**（sdflow-init 代码 + 两 SKILL 改动严格限本 change 范围，未越界改 anchor_lint/aggregator/ship_gate；openspec 四件套+CONTEXT+adr/0012 是设计物已过设计门不算 drift）；**完成度达标**（7 组任务/8 Task 逐条有实现+pytest 锚点，223→231 绿）。
- HR-TG：命中 **TG-06**（跨模块共享契约边界）→ 已开 codex hr-tg cross-model。
- 冷审独立捕获（循环内 SDD 8 次任务审未尽挖出的）**2 类结构缺陷**（CR-C1 类型收窄 / CR-C2 幽灵行）——印证冷 code-review 层 load-bearing。

### Findings（置信 ≥80，均已自动修 [impl-review-fix]）

- **[高] CR-01 CR-C1 字段级类型未收窄 → 裸 TypeError 逃逸 fail-closed** | `lens_metric_emit.py:76/88/90/104-108` | 置信 95 | **已修**：`reduce` roster + `fold_hit` 对 lens/runner/site/raw 加 `isinstance(str)` 收窄，非字符串走干净 EmitError；`fold_hit` site 拆「先类型后注入」（原非 str site 悄过注入检查再塞行键致下游 set 推导裸炸）。**4 镜命中 + 多镜实跑复现**（site=123/lens=["broad"]/raw=["broad"] 均曾裸 traceback）。
- **[高] CR-01 CR-C2 roster 非-outside-voice 行 runner/site 未与 lens 交叉校验 → 幽灵行击穿强制行承诺** | `lens_metric_emit.py:100-117` | 置信 90 | **已修**：加镜像约束「非 ov 行 MUST runner=claude site=—」否则 fail-closed。原 `{"lens":"broad","runner":"codex","site":"x"}` 幽灵行满足 MANDATORY_LENS 而真实 (broad,claude,—) 行可不存在，击穿 ADR-0012 强制行诚实留痕承诺（对抗2+hr-tg 实证）。
- **[中] CR-01 CR-C3 `_read_block_pairs` 未闭合 fence 不 fail-closed** | `lens_metric_emit.py:19-40` | 置信 88 | **已修**：加 `closed` 标志，EOF 前无闭合围栏 → EmitError（区分「缺块」与「未闭合」）。（anchor_lint 同盲区平行项 → defer todolist，非本 change 文件。）
- **[中] CR-08 CR-C4 ADR-6「机读 input schema 块」未落地、SKILL 引用不可达** | `sdflow-spec-review/SKILL.md`/`sdflow-code-review/SKILL.md` | 置信 85 | **已修**：契约 `lens-metric-contract.md` 加 `lens-metric-input-schema` 机读块（bundle 分发可达），两审 SKILL 引用改指该块（原指「lens-metric-emit 能力 input schema 机读块」实不存在于 bundle、消费仓 404）。3 镜命中（code-voice/广审/历史）。
- **[中] CR-01 CR-C6 sev 仅 `verdict=采纳` 时校验、裁掉/defer 带非法 sev 静默接受** | `lens_metric_emit.py:131-133` | 置信 82 | **已修**：sev 若存在则任何 verdict 都须合法级、采纳额外要求非空。
- **[中] CR-06 CR-C5 fold 块多列「完整性接地镜: grounding」超 ADR-7/prose 范围** | `lens-metric-contract.md:47` | 置信 80 | **已修**：删除该行，对齐 §折叠表 prose（接地镜/完整性镜→grounding）。
- **[低] CR-09 CR-C7 `reduce` 尾部 Σsev==采纳 不变量当前结构性不可达** | `lens_metric_emit.py:146-148` | 置信 80 | **已修**：加注释澄清「同函数内自防御、当前不可达、非跨模块校验」（保留不删=防御深度）。

### 已裁掉（反静默压制·可审计）

- **X1 [裁掉] 对抗2 F3：`test_fold_codomain_subset_lens_enum` 冗余** — 裁掉理由：`load_fold` 内部已 `raise` codomain 越域，此测试是内部不变量的外部复检（回归防护），非假绿；提供增量价值低但非缺陷。保留。
- **X2 [裁掉·<80] 广审 #2：fail-closed EmitError 消息内容未被 `match=` 断言** — 测试严谨度改进项（代码本身 f-string 已带字段名，功能满足），非缺陷；一行带过。
- **X3 [裁掉·<80] 历史 F3：SKILL 旁路声明措辞改进未标 [impl-review-fix]** — 标注遗漏、非功能问题；一行带过。
- **X4 [裁掉·<80] 广审 #3：task 3.3「finding 无 layer」无显式独立测试** — reduce 从不读 finding.layer（符合 ADR-9），行为正确、仅缺专项断言；一行带过。

### 修复 / defer 台账

- **自动修 7 项 [impl-review-fix]**：CR-C1~C7（commit `77b6906` 代码类 + `<本轮 impl-review commit>` 契约/SKILL 类）。全部 [impl-review-fix]，subject 前缀 `impl-review`（设计域失鲜豁免）。
- **defer 3 项 → todolist**（技术债/治理层，非本 change 阻塞）：
  - **CR-D1** anchor_lint `load_enums` 未闭合 fence 同盲区（与 CR-C3 平行，但 anchor_lint 非本 change 文件）→ todolist。
  - **CR-D2** `lens-metric-enums` 重复键静默覆盖（emitter+anchor_lint 一致，与 fold 重复键 fail-closed 口径不一）→ todolist。
  - **CR-D3** 仓库无 CI/pre-commit → 单一源守卫（load_enums 等价/aggregator enum/MIN_LENS_ROWS 一致性测试）仅手动 `pytest` 生效、drift 需下次跑测试才暴露 → todolist（治理层）。
- 无 ≥2 方案需 T10 复核（findings 修法均有客观判据=测试/实证）。

### 度量锚（lens-metric，config metrics.enabled=true，由 `lens_metric_emit.py --layer code-review` 归约产出）

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="none" findings="3" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="none" findings="4" truncated="false" -->
<!-- sdflow:hr-tg v1 hit="TG-06" evidence="新增 lens_metric_emit 为共享契约套件第5成员且改契约(加 fold+input-schema 块)" -->

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="7" 采纳="4" 裁掉="1" defer="2" 独立="1" sev="致0/高2/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="2" 采纳="1" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="3" 采纳="2" 裁掉="0" defer="1" 独立="0" sev="致0/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="3" 采纳="2" 裁掉="1" defer="0" 独立="1" sev="致0/高0/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="hr-tg" findings="4" 采纳="3" 裁掉="0" defer="1" 独立="0" sev="致0/高2/中1/低0" -->

> 锚形示范（fence 内防聚合器误取）：
```
<!-- sdflow:lens-metric v1 layer="…" lens="…" runner="…" site="…" findings="N" … -->
```

> **残余信任边界声明**：上述计数由 emitter 对主 session 给的结构化 findings 确定性归约；分类正确性（哪些镜报了哪条/裁决/sev）+ roster 完备性 + findings JSON 誊写准确仍是主 session 信任边界，emitter 只保证「给定输入的确定性归约」。**反馈回路**：跨 change 归档后由 `/sdflow-retro` 按 per-(层,镜) 采纳率+独立率复评，本报告只落锚不聚合不决策。

### 结论
- ☑ **建议进 /sdflow-done**（verify → hand-off → archive → commit → merge）。
- ☑ defer 残差（CR-D1/D2/D3）已入台账 → hand-off 引导另开 todolist 清理 change。

（机判锚见报告**头部** frontmatter `ship-gate.code_review: pass`。）
