# Verify Report — batch-triage-strategy

- **日期**：2026-07-07
- **change**：batch-triage-strategy
- **形态**：纯 markdown（无 scripts/、无 pytest）——锚点 = 交付物具体行/grep 命中，非测试名

## 结论：PASS
<!-- ship-gate: verify=PASS -->

8 条 ADDED Requirement 全部在交付物中有可机验证据锚点落地；核心 spec Requirement 无未落地项。
「本仓-local 不进 bundle」经机验确认（`grep -rl batch-triage sdflow-init/assets/workflow/` 退出码 1 = 零命中）。

---

## 逐需求核对表

| spec Requirement | 交付物证据（file:行 / grep 命中） | 状态 |
|---|---|---|
| **1. 待处理项分诊三分类** | `batch-triage-rules.md` §一 L21-59：三元分类「互斥且穷尽」(L23-24)；相关合批第三腿不可省 + REC-3 先例订正 (L31-34)；单开含「延迟绑定/搭便车」子态 (L52-54)；三问链互斥穷尽自检 (L56-59) | ✅ |
| **2. 大扫除批硬边界——禁装逻辑面** | `batch-triage-rules.md` §一.2 L40-42：硬边界 MUST NOT 装逻辑面 + 「边界优先于任何合批收益」+ 「降成本红线 MUST NOT 靠砍评审安全换取」 | ✅ |
| **3. issue 级判据 fail-closed（纯规则纪律）** | `batch-triage-rules.md` header L7-9（纯规则 checklist、不引入判器脚本/pytest）；§二输入面 pre-diff L67-71；fail-closed MUST 纪律 L73-80「无脚本自动兜底」「非机械可验证不变量」「未声称有自动化门禁兜底」 | ✅ |
| **4. 判据同类 Leg1 白名单且非同一脚本（+行为面路径硬排除）** | `batch-triage-rules.md` header L11-17 显式 cross-ref `trivial_shape.py`「同类判据、非同一脚本」+ pre-diff vs post-diff 区分；§二 L82-107 行为面路径硬排除 MUST + `BEHAVIOR_PATH_PATTERNS` 代码块 L88-95（`SKILL.md`/`*/assets/workflow/*`/`*ship_gate.py`/`*trivial_shape.py`）；L103-107「同类 Leg1 = 继承路径守卫、非人看描述放行」 | ✅ |
| **5. 大扫除批聚合上限** | `batch-triage-rules.md` §三 L111-154：有上限本身 MUST L116-120；数值 SHOULD 可调 ~10 文件/~8 项 + 重型 CI 排除 L122-128；含生成物硬 MUST 隔离走再生 commit L130-135；每项结构化判定记录 MUST + 字段模板 + 落点宽泛/证据不足→「存疑→单开」 L137-154 | ✅ |
| **6. 大扫除批一项一 commit（执行协议 + 验证锚）** | `batch-triage-rules.md` §四 L158-221：item 粒度硬 MUST（同文件两 item 仍两 commit）L160-165；执行协议串行→立即 checkpoint→确认干净 L167-182 + 生成物越界防线〔impl-review-fix〕L184-194；验证锚「候选 item 数==task 数==commit 数」+ 订正计数公式（item-checkpoint commit 去重计数，非 raw 总数）〔impl-review-fix〕L196-221 | ✅ |
| **7. consolidation-plan 三元标注** | `consolidation-plan.md` §5.1 三元标注表 L82-105（全量项含 07-06 新增 T54-T64/T56/T57）；§5.2 worked example 正反齐全 L107-148——反例A T50/T41/T42 排除（行为面路径）L109-113、反例B T51/T52/T63/T64 排除（逻辑面）L115-120、正例 T13 候选 L122-142、存疑 B5 边界 L144-148；§5.3 诚实标注「本仓大扫除批候选池薄=1」L150-164 | ✅ |
| **8. 批次判据规则落点——本仓-local（发布 deferred）** | `batch-triage-rules.md` §五 L225-246：本仓-local 落点 MUST NOT 进 bundle/下游 L227-234 + 不涉回灌/INDEX snippet/BASE-18 悬空；发布 deferred MUST 记录 L236-246（dogfood 后未来独立 change / 可退化为注记）。**机验**：`grep -rl batch-triage sdflow-init/assets/workflow/` → 退出码 1（零命中），bundle 未受污染 | ✅ |

---

## tasks.md 附带项核对

| task | 交付物证据 | 状态 |
|---|---|---|
| 4.1 `INDEX.md` 登记 batch-triage capability | `openspec/INDEX.md` L34 batch-triage 行存在，位于 spec 索引区（`opsx-init:rules:end` 在 L25 之后，非托管块内），指向 `specs/batch-triage/spec.md` | ✅ |
| 3.2 刷新 stale 状态 | `consolidation-plan.md` REC-1=gate-checkpoint-hardening 标✅已 ship（L34/56）、G7=sdflow-init-hardening 标✅已 ship（L25/45/93） | ✅ |
| 2.5 不进 bundle / 不动 trigger-catalog | grep 机验零命中（见 Req 8）；INDEX 行在 spec 区非 opsx-init snippet 区 | ✅ |

---

## 缺口清单

### 核心缺口（FAIL）
- 无。

### Minor / 可接受 / deferred
- **X1 前向引用（code-review 转交，非缺口）**：`INDEX.md` L34 指向 `openspec/specs/batch-triage/spec.md`，该路径当前尚不存在——这是**预期的前向引用**，archive 步会由 delta 同步创建。verify 已确认 INDEX 行存在且指向正确路径。**hand-off 记为 archive 后核查项**。
- **验证锚「候选数==task数==commit数」为未来 sweep 规则内容**：该验证锚是 `batch-triage-rules.md` §四写给未来大扫除批实现的规则文字（已落盘 L196-221），**非本 change 自身的自核指标**——本 change 3 task 不需等于 commit 数。核的是「规则文档写了这条锚」，已确认。
- **5.1 task 未勾选**（tasks.md L40）：验收核对项复选框未勾，但对应核对内容（三分类/硬边界/路径守卫/fail-closed/上限/一项一commit/三元标注/本仓-local）均已在交付物落地——复选框状态不影响判定（本报告不信任复选框）。

---

PASS —— 8 条 ADDED Requirement 全部有可机验证据锚点落地，「本仓-local 不进 bundle」经 grep 机验（退出码 1 零命中）确认，无核心 spec Requirement 未落地。X1 为归档步解决的预期前向引用，非缺口。
