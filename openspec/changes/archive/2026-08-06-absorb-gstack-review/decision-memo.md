---
schema_version: 1
change: absorb-gstack-review
branch: feat/absorb-gstack-review
generated_at: 2026-08-06T10:51:06+08:00
decision_hash: 0fa4a7f9aae9
---

# 决策纪要 · absorb-gstack-review

## 目标态

`sdflow-code-review` 全链路零 gstack 依赖：Step1 自持 scope-drift + 完成度审计（fresh 子代理执行，
意图源锚 OpenSpec 四件套）；gstack checklist 真空缺口吸收进 `code-checklists/`（含新 domain `llm.md` +
TG-27）；pre-emit verification gate 操作化进 Step2/Step3；锚名/broad 镜/恒跑守卫语义全保留，
spec-review 侧（autoplan 依赖）不动。

## 承重约束

- **C1 · 锚名不变，mode 枚举无机械门阻碍**：`step1-broad-review` 锚在 code-review 层只被
  `anchor_lint.py` 核存在性（`MANDATORY` 元组，anchor_lint.py:73,203）；mode 值枚举校验
  （`native|simulated`）只存在于 spec-review 侧 `outside_voice_guard`（specs/outside-voice-reuse-guard/spec.md:64，
  作用对象是 `gstack-review.md` 产物，非 code-review-report.md）⇒ 吸收后锚名保留、mode 值可换新枚举，
  归档报告与 ship_gate 零扰动。
- **C2 · broad 镜必须保留**：`MIN_LENS_ROWS = ("broad", "outside-voice")`（anchor_lint.py:204）——
  metrics 开时报告必有 broad lens 行 ⇒ 吸收后 Step1 继续以 broad 镜身份产 lens-metric 行。
- **C3 · raw 镜名变更必须同步 contract**：`lens_metric_emit.py:99-102` 对未知 raw 镜名 fail-closed
  （不静默塞 broad）；折叠映射单一源 = `lens-metric-contract.md` 的 `lens-metric-fold` 机读块
  （现有行 `gstack-adv: broad`，contract:64）⇒ Step1 改 raw 名（gstack-adv → 新名）时 contract 同 change 更新，
  SKILL 与 contract 同 bundle 分发、skew 窗口=既有 setup/update 纪律。
- **C4 · spec 级 Requirement 需出 delta**：`openspec/specs/spec-workflow/spec.md:68`——
  「Step1（gstack/review：scope-drift + 计划完成度）MUST 每次必跑…验白名单形状诚实性的守卫」——
  恒跑 + trivial_shape 守卫语义 MUST 保留，实现主体改为自持；本 change 须含 specs delta。
- **C5 · spec-review 侧不受影响**：`sdflow-spec-review` 的 autoplan 依赖、`outside_voice_guard.py`
  及其专属 spec（outside-voice-reuse-guard）作用于 `gstack-review.md` 产物——本 change 不触碰
  （姊妹依赖另行处置，记 todo）。
- **C6 · 消费点清单（改动面）**：`sdflow-code-review/SKILL.md`（Step1 重写 + Step2/3 pre-emit gate）·
  `prompts/step8-code-review.md`（一行 dispatch 提示词）+ needle `hack/tests/test_workflow_split.py:49` ·
  `workflow.md:76/91/123` · `reference/quality-layering.md:33/36/106/131` · `lens-metric-contract.md:44/64` ·
  `docs/workflow-skills/*`、`docs/external-dependencies.md` 等文档提法。
- **C7 · checklist 吸收清单（两边逐条比对定案，对话内双方确认）**：真空缺口 = DB 层竞态（新 CR-BE-03）·
  LLM 输出信任边界 + LLM prompt issues（新 domain `llm.md`，CR-LLM-*）· shell 注入（base 新 CR-10）·
  枚举/取值完备性含「必须读 diff 外代码」（base 新 CR-11）· XSS/不安全 HTML（并入 CR-BE-02 检查点）。
  已覆盖不搬：SQL 注入/N+1（CR-BE-01）、进程内并发（CR-05）、类型转换（CR-06/CR-GO-05）、
  Fix-First 启发式（Step4 已有）、置信分级显示（Step3 已有）。ID 纪律：全新 ID 不复用；措辞改写为
  语言无关 + 括号多语言示例 idiom。
- **C8 · 阶段三无人类门不动摇**：gstack 的 AskUserQuestion 门（HIGH-impact discrepancy gate、
  Fix-First batch-ask）MUST NOT 吸收——由既有 Step3 裁决 + Step4 自动修/T10-choice/defer 协议替代；
  完成度审计定位为 informational shift-left（发现 NOT DONE → 进 Step3 合并池按普通 finding 裁决），
  不与 sdflow-done verify 的门禁职责重叠。
- **C9 · pre-emit verification gate 落点**：gstack `review/SKILL.md:1241` 的「finding 必须引出触发行
  原文，引不出 → 强制降置信」按实测 FP 类目校准过——吸收进 Step2 fan-out 子代理 prompt 模板
  （产出纪律）+ Step3 置信过滤规则（引不出触发行 → 置信上限 50，落已裁掉区可审计）。

- **C10 · mirrors= token 枚举需扩 `broad`**：`check_fanout_consistency` 对 `mirrors=` 未知 token
  fail-closed（anchor_lint.py:704-706，现枚举 {domain,adversarial,grounding,history}）——Step1 变
  被派子代理后 MUST 纳入 mirrors 清单与 dead-fanout 一致性检查（不加 = 一致性 lint 盲区）⇒
  anchor_lint token 枚举 + golden 测试同 change 更新。

## 拍板决策

- **D1 · Step1 执行形态 = 恒跑 fresh 子代理（中档）**〔人拍板 2026-08-06〕：scope 审计由 fresh
  子代理执行（输入 = proposal/tasks/design + diff，返回结构化 findings 进 Step3 合并池），消除
  「主 session 携带生成历史自查顺手多改」的结构性偏置（SKILL 明写主 session 接受合成层偏置 +
  ship 链序 G1 禁 /clear ⇒ code-review 主 session 常为跑完实现管线的同一 session）。
  `trivial_shape` EXEMPT 时恒跑守卫语义不变（C4）；子代理不可用（host=codex 探针 unavailable）
  降级主 session 亲做、报告显著标注——与既有能力探针协议同构。锚 mode 换新枚举（C1 无机械门阻碍）。
- **D2 · llm.md 挂新 TG-27（LLM 集成面）并收进 HR-TG**〔人拍板 2026-08-06〕：与 TG-01~03 同族
  （栈/面选域），不挂 TG-17（那是设计期触发带 design 必填槽，语义不同）。触发措辞收窄为「代码
  **消费 LLM/agent 产出**并持久化/执行/外呼（输出解析、锚行 parse、工具 wiring、RAG 写入）」——
  纯 prose/SKILL.md 编辑不触发。HR 收录依据：SSRF/存储型注入/未校验持久化命中「安全泄漏 +
  数据污染难回退」判据；命中率/产出走既有 Q5 复评机制（跑满 10 次可摘出）。
- **D3 · Pass-2 剩余条目处置 + raw 镜名替换**〔人拍板 2026-08-06〕：
  ① Async/Sync 混用（Python）→ defer 记 todo（归属不存在的 python.md domain，超本 change 内聚范围）；
  ② 通用 Suppressions 可泛化的条目（阈值常量不强制注释、无害冗余助可读性不标）→ 吸收进 Step3
  明确滤除类目；③ Time Window / Column-Name / 类型跨界 hash / View-Frontend / CI-CD 发布 /
  VERSION-CHANGELOG → 放弃（低频/栈不匹配/已有部分覆盖，通则④五问不过线），写进 proposal Non-Goals；
  ④ raw 镜名 `gstack-adv` → `scope-audit`，contract `lens-metric-fold` 块**直接替换不共存**
  （SKILL 与 contract 同 bundle 分发，skew 窗口即既有 setup/update 纪律）。
- **（自判注记）** B.7 回扫：D1/D2/D3 均不满足 ADR 三条件（皆可逆、权衡已记录于本纪要）——不落 ADR；
  术语无冲突（CONTEXT.md「复用产出物 vs 依赖内部」边界与本 change 方向一致且更彻底：code-review 侧
  归零 gstack 调用，spec-review 侧的产出物复用不受影响，术语定义无需改）。

## 接受的边角

- **归档报告里的旧 mode="native|simulated" 与 raw 名 gstack-adv 不迁移**——概率：仅影响回溯阅读；
  影响：小（归档锚 lens= 均为 canonical 值，聚合不受 raw 名影响，retro 读 canonical）；完美成本：
  重写归档 = 破坏审计不可为。**为何接受**：历史报告是冻结审计件，锚语义随其时代自洽。
- **bundle skew 窗口**（消费仓旧 SKILL raw=gstack-adv × 新 contract 无该行 → emitter fail-closed）——
  概率：低（SKILL 与 contract 同 bundle 同步分发）；影响：fail-loud 非假绿，修法即重跑 update；
  **为何接受**：既有 setup/update 纪律已覆盖，不为此造共存期。
- **gstack Pass-2 放弃条目**（Time Window / Column-Name / 跨界 hash / View-Frontend / CI-CD /
  VERSION 一致性）——低频 or 栈不匹配 or 已有部分覆盖；通则④五问不过线，写 proposal Non-Goals。

## 三镜代价

D1（Step1 执行形态：fresh 子代理 vs 主 session 亲做）为本纪要唯一 ≥2 方案的非显然选择：
- **系统镜**：多一个子代理调用点，但与 Step2 fan-out 同构复用能力探针/降级协议，无新机制；可回退
  （改回主 session 亲做 = 删一段 dispatch 指令）。
- **用户镜**：评审报告的 scope-drift 结论可信度上升（消除自查偏置）；对人无新交互面。
- **开发循环镜**：每轮代码审多一次中档 dispatch（数千 token）；换来 scope 镜与其它镜统一的
  冷视角纪律，心智模型更简单（所有镜都是 fresh 子代理）。
- **主次判定**：系统镜为主——消除「写了顺手多改的 session 自查顺手多改」的结构性偏置是本 change
  对评审可信度的实质增益，token 成本次要。
