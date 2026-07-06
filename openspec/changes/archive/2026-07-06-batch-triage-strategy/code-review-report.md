## code-review 报告 — batch-triage-strategy

> 阶段三代码评审编排器（每次全跑·独立冷·强制主审）。多镜 fan-out（领域×1 + 对抗×2 + 历史×1）+ code outside-voice（codex）。
> diff base = `1321407`（merge-base origin/main HEAD）。本 change = 纯 markdown（判据规则 + 规划文档 + INDEX 登记 + change artifacts）。

### 命中范围
- **栈**：无代码（纯 markdown / 规划纪律文档）。通用 code CR-01~09 多不适用——评审重心转为**规则文档忠实度 / 内部一致性 / 红线（不砍评审安全）守卫 / 事实性声明核验**。
- **无逻辑面白名单判定**：`trivial_shape.py` → **NOT_EXEMPT**（`non-doc-markdown:openspec/INDEX.md` + openspec 下多 markdown 非白名单形状）→ 照常 fan-out。
- **Step1 gstack/review（scope-drift + 完成度，原生）**：diff 只碰 change artifacts + 3 交付物（`batch-triage-rules.md` / `consolidation-plan.md` / `INDEX.md`），**无 scope-drift**（无 bundle / 无脚本 / 无 SKILL.md 顺手改）；完成度：tasks.md 组1+2→rules 文档、组3→consolidation-plan、组4→INDEX，全覆盖。
<!-- sdflow:step1-broad-review v1 mode="native" -->
- **HR-TG 判定**：本 change 纯文档/规划，无高风险代码触发（无 gate 逻辑/并发/安全/资源）→ 不单开领域专属 cross-model。
<!-- sdflow:hr-tg v1 hit="none" evidence="纯markdown判据+规划文档,无gate/并发/安全/资源改动" -->

### Findings（置信 ≥80，均已自动修 [impl-review-fix]）

- **[中] F-A 完整性 overclaim** | `consolidation-plan.md` §5.3 | 声称「T1-T64 全量」但漏标 OPEN 的 T56/T57（落 T1-T64 区间、从未三元归属）——正是本 change 要防的「存疑未查却被当已查」。**3 源收敛**（domain / adversarial#2 / codex）| 置信 95 | 已修：§5.1 补 T56/T57 两行**排除**（T56 触 `trivial_shape.py` 行为面路径+判器逻辑面；T57 触 `*/assets/workflow/*` 行为面路径+功能增强），§5.3 改诚实口径「PROPOSED+OPEN 全量核对，候选池薄=1(仅T13) 不变」。
- **[高] F-H proposal/design 残留 pre-Q2 bundle 叙事 + 误纳率0 机械口径** | `design.md:101/:106` + `proposal.md:8/:35/:50` | Migration/Compliance 仍写「bundle 回灌 / sdflow-init update 推下游」与 D6 本仓-local 定案矛盾；Success Metric「误纳率=0…恒为0」与 D4+spec.md:26「MUST NOT 声称机械兜底保证误纳率0」矛盾。codex 独家 | 置信 90 | 已修：design Migration/Compliance + proposal What-Changes/Impact/Compliance 全改本仓-local 现实（未动 D6 决策正文）；误纳率改纪律目标口径。
- **[中] F-adv1 生成物混入单 item commit（git add -A 同源缺口）** | `batch-triage-rules.md` §三.3/§四 + 仓根 `.gitignore` | 红线镜**实测复现**：执行 T13（改测试→跑 pytest→`__pycache__/`）时 `checkpoint-commit.sh` 的 `git add -A` 会把字节码裹进手写 commit，破坏「含生成物硬 MUST 隔离」；规则只防「多 item 裹一 commit」、没防「生成物裹进 item commit」。adversarial 独家 | 置信 90 | 已修：`.gitignore` 补 `__pycache__/`/`*.pyc`/`.pytest_cache/`；规则加「生成物越界防线 MUST」（sweep 前确认 gitignore 覆盖运行期产物 / checkpoint 前校验）。
- **[中] F-B T13「同类 Leg1」类比字面不成立** | `consolidation-plan.md` T13 worked example | Leg1 `trivial_shape.py` 只豁免**新增** tests 文件，T13 改**既有** test_*.py（Leg1 会落 logic-line 不豁免）。codex + adversarial#1 | 置信 85 | **T10 自动选（对抗镜复核通过，见台账）**：红线镜裁定红线**未破**（纯测试断言、无生产路径、CI 兜底=batch-triage 自身定义下的合法候选）→ 保留 T13，修正措辞诚实注明比 Leg1 更宽 + 三点安全论证。
- **[中] F-C 一项一commit 验证锚 raw count 不精确** | `batch-triage-rules.md` + `spec.md:78` | sweep 作为 change 还含 ff/plan/review-fix 等非 item commit，`git log base..HEAD | wc -l` ≠ item 数。codex 独家 | 置信 82 | 已修：两处改「item 实现 checkpoint commit 数（含 item ID、去重）== 候选 item 数」，保留 N item=N commit 设计决策本身。
- **[低] F-D consolidation-plan 头部「bug 全 FIXED」stale 自相矛盾** | `consolidation-plan.md:6` | 头部称 bug 全 FIXED，但 §5.2 讨论的 B5 当前 OPEN（本次订正了 REC-1/G7 却漏此第三处）。adversarial#2 独家 | 置信 90 | 已修：头部改「B1-B4 FIXED，B5 OPEN（存疑→单开，见§5.2）」。
- **[低] F-F T47 排除理由用弱框架** | `consolidation-plan.md:95` | T47（`engine.js` 落 `*/assets/workflow/*`）用「存疑从严」，应与 T50/T41/T42 一致用「行为面路径硬排除」。adversarial#2 独家 | 置信 80 | 已修（结论不变）。
- **[低] F-G T42「未列精确文件」轻度失实** | `consolidation-plan.md:110` | todolist 实列 `generation-process.md`/`design-diagrams.md`（仅「产物模版」笼统）。adversarial#2 独家 | 置信 80 | 已修（路径硬排除结论不变）。

### 已裁掉（反静默压制，可审计）
- **X1 [codex#4 中 + history#1 高] INDEX 指向 `openspec/specs/batch-triage/spec.md` 当前不存在** → **裁掉为 verify-time 核查项、非缺陷**。理由（三镜+主次）：INDEX spec 索引区**每一行**都指向归档后的 `specs/<name>/spec.md`（系统镜：这是 INDEX 的既定语义）；本 change 归档（ship 下一步 done→archive）会把 delta 同步创建该路径、解掉悬空（用户镜：末态一致）；tasks.md 4.1 明文要求「登记（归档后 spec 同步）」（开发循环镜：设计如此）。悬空窗口是 ship 单次运行内的瞬态（archive 紧随 code-review）。**主次**：主=末态正确性（archive 解悬空）> 次=瞬态悬空。**转 verify 显式核**：done 阶段确认 archive 真建了 `openspec/specs/batch-triage/spec.md`（已写入 hand-off 关注点）。
- **X2 [history#Q2] 「INDEX 登记推翻发布 deferred」** → **裁掉为误读**。history 镜混淆两个「INDEX」：Q2 排除的是 **bundle 的 INDEX snippet**（`index-section.md`→下游 `opsx-init:rules` 托管块）；Task3 登记的是**本仓自己的** `openspec/INDEX.md` spec 索引区（第34行，`opsx-init:rules:end` 之后、非托管块、非 bundle 源），正是 tasks.md 4.1「本仓-local dogfood 生效」明文要求。本仓 INDEX 不部署下游，无矛盾。
- **X3 [F-adv1#2 分析性] T13「同类 Leg1」** 已升格为 F-B 采纳修复（非裁掉，见 Findings）。
- **<80 滤除**：无独立低于阈值项（各镜 findings 均达阈或已并入上方）。CI/linter 范围（markdown 排版）不进镜。

### 修复 / defer 台账
- **自动修 8 项 [impl-review-fix]**（commit `627640f` 修 F-A/F-H(design部分)/F-adv1/F-B/F-C/F-D/F-F/F-G）+ **F-H 补修**（proposal.md What-Changes/Compliance 两处 stale，主 session 补 edit，标 [impl-review-fix]）。
- **T10复核: 保留 T13 为唯一候选 + 修正「同类 Leg1」措辞** | 对抗镜结论 **通过**（红线镜专项攻击 T13 后裁定「红线未破，纯测试断言无生产路径、CI 兜底，是 batch-triage 自身『无逻辑面=不新增生产路径』定义下的合法候选；仅类比措辞不严谨」）| 理由（三镜+主次）：系统镜=T13 客观测试-only、CI 可兜；用户镜=保留一个带诚实 caveat 的 worked example 比「候选池=0」更具教学价值；开发循环镜=修措辞成本 < 丢样本损失。**主次**：主=诚实披露与 Leg1「仅新增 tests」的分歧（已修措辞）> 次=保留样本（已保留）。
- **defer：0 项**（本轮无拿不准/修不了项——所有确认 finding 均当场修）。
- **verify 关注点**（转 hand-off，非 defer）：done 阶段核 archive 是否创建 `openspec/specs/batch-triage/spec.md`（解 X1 悬空）；核「候选数==task数==commit数」（本 change 非 sweep，实为 3 task/3+fix commit，验证锚是给未来 sweep 的规则、非本 change 自核）。

### 度量锚（lens-metric，config `metrics.enabled=true`）
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="step1" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="4" sev="致0/高0/中3/低2" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="2" 采纳="0" 裁掉="2" defer="0" 独立="0" sev="致0/高0/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="5" 采纳="4" 裁掉="1" defer="0" 独立="2" sev="致0/高1/中4/低0" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="none" findings="5" truncated="false" -->

> 注：F-A 由 3 镜（domain/adversarial/codex）收敛，故各镜 findings 计入但 F-A 不计任一镜「独立」；F-B 由 codex+adversarial 双报，不计独立。adversarial 独立4 = 生成物/B5/T47/T42；codex 独立2 = F-H/F-C。字段口径见规则根 `lens-metric-contract.md`。

### 结论
- ☑ **建议进 /sdflow-done**——8 项 finding 全当场修（[impl-review-fix]），T13 经对抗复核保留，红线（不砍评审安全）经专项攻击守得住；defer=0。verify 须核 X1 悬空在 archive 解掉。

<!-- ship-gate: code-review=pass -->
