---
schema_version: 1
change: harden-ticket-slicing
branch: feat/harden-ticket-slicing
generated_at: 2026-08-19T17:18:04+08:00
decision_hash: f68baf7f6705
---

# 决策纪要 · harden-ticket-slicing

## 目标态

票的切分判断前移到强模型 + 受审 + 人门可见的位置（design.md 切片建议 SHOULD + spec-review 审项），出票步降级为「物化已审草图」（默认采纳 + 偏离审计 + 无草图/偏离/矛盾时 T10-choice 必触发），change 拆分标准成单一源被 roadmap / 相位 B / 执行期三处引用（T141 收口）。

## 拍板决策

- **D1 不搬出票步位置，切片判断前移到阶段一/二** — 依据：C1（出票步档位焊死在阶段三主 session）+ C2（design.md 住所白捡失鲜保护）；**砍掉的候选**：出票整体移到 spec-review 之前（评审 amendments 几乎必落 ⇒ 每 change 白付一次 RUN_PLAN；且需重造 `plan_first_sha` 窗口与 gate 契约，爆炸半径大）。人 2026-08-19「开搞」确认。
- **D2 切片建议 MAY→SHOULD** — 缺席须在 design.md 写一句为何不需要；依据：单文件小修强制产草图是样板税，SHOULD + 审项兜底已堵死静默缺席；**砍掉的候选**：按 TG 规模分档 MUST（引入 TG 依赖复杂度，不值）。人 2026-08-19 Q3 拍板。
- **D3 出票消费语义升级** — 「建议输入」→「默认采纳；偏离逐条记 `impl-reports/planning-decisions.md` + 理由」（落点复用 M15 既有文件）；**砍掉的候选**：维持「建议非契约」（弱档模型保留全量自由裁量 = 痛点原样保留）。
- **D4 T10-choice 复核必触发条件集** — 无切片建议 ∨ 出票偏离草图 ∨ 草图与 design 正文矛盾（第三条是 C2 攻出的缺口的兜底位）；触发时派 strong 档对抗镜复核切分方案（既有协议，仅扩触发条件）；**砍掉的候选**：仅粒度争议触发（现状，覆盖不了「无草图自主切」的高风险路径）。
- **D5 不做 fable 覆盖** — strong 档维持 opus；**砍掉的候选**：本仓 config 覆盖 / bundle 缺省覆盖为 fable。人 2026-08-19 Q2 明确拍板。
- **D6 T141 全量收口** — 新增单一源 `sdflow-init/assets/workflow/reference/change-decomposition-standard.md`（4 规则 + why），三处指针引用不复制文本（查表式规则，对照 CLAUDE.md 托管机制段的 DOC-1 论证）；T141 原文的「workflow.md:83 grill 调用 prompt」落点已随架构消失，翻译到 sdflow-spec 相位 B 拷问的检查项。做完后 T141 set-status DONE（用开发 checkout 脚本，resolved_by 指本 change）。
- **D7 spec-review 审项 = 新增 BASE-31（切片建议存在性/内聚质量）** — 依据：镜表「未列明的新增 base R 项默认归 strategy 镜」⇒ 零路由改动；**砍掉的候选**：扩写 BASE-18（该项已很长，change 拆分与 ticket 切片是分解面的两个粒度，混写降低可读性）。
- **D8 fold 纪律执行形态** — implementer 撞到 related 票外问题 → 上报编排层，编排层按 BASE-18 AND 门（同 capability ∧ 高耦合 ∧ 低增量）判 fold（并入当前/下一票）或 defer；**MUST NOT 由 implementer 自行扩 scope**；依据：implementer 无扩 scope 权是既有结构，T10 仲裁位在编排层；**砍掉的候选**：implementer 顺手修（绕过双轴审的 scope 契约，票的验收标准失去边界）。

## 承重约束

- **C1 出票步模型档位无法就地升档** — 验证方式：读 `sdflow-implement/SKILL.md` + `sdflow-ship/SKILL.md`；出票模式自身要派 T10-choice strong 档对抗镜（SKILL.md:256），子代理不能再派子代理 ⇒ 出票必须留在主 session 位置，模型 = 阶段三 session 模型；**证据锚**：`sdflow-implement/SKILL.md:158-159`（inline 执行 + MUST NOT 子代理派发）、`sdflow-ship/SKILL.md:168`（RUN_PLAN 派发契约「ship 主 session inline 执行」）。
- **C2 design.md 住所换来文件级失鲜保护，但文件级新鲜 ≠ 节级一致** — 切片建议入设计门失鲜监视集（机械保证出票时 design.md 整体新鲜），但 amendments 只改其他节时切片节可残留旧切分而不触发任何门 ⇒ 缺口由 D4 第三触发条件兜；**证据锚**：`sdflow-implement/SKILL.md:557`（design 域监视集 = proposal/design/tasks.md/specs）。
- **C3 fable 作为 config 覆盖值技术可行（但 D5 拍板不用）** — 验证方式：读 resolver 源码；`_valid_model_id` 仅字符集校验 `[A-Za-z0-9._-]`；**证据锚**：`~/.sdflow/hack/resolve-models.sh:102`、非法值告警回落 `:216`。
- **C4 「偏离草图」判定无确定性信号** — 票数增减 ≠ 偏离（合并/拆分可合理），无机械 diff 判据 ⇒ D4 的必触发是指令层约束、非机械门，MUST NOT 声称机械保证（基准 1 残余划分 + 「有信号≠有可机械捕获路径」）；**证据锚**：本条为负向论证，锚 = `spec-quality-base.md` 机械/语义切分惯例与 CLAUDE.md 基准 1。
- **C5 BASE-18 已落地，T141 只剩四块** — fold-vs-defer 两级判定已在 `spec-quality-base.md:42`，strategy 镜已覆盖（`sdflow-spec-review/SKILL.md:248`、`sdflow-roadmap/SKILL.md:472`）⇒ 剩余 = 单一源文件 + ff 内聚约束 + implement/code-review fold 纪律 + roadmap 显式规则；**证据锚**：上列三处 file:line，2026-08-19 grep 实查。
- **C6 与在途 add-frontend-checklists 零冲突** — 该 change 目录为空壳（无 artifact 文件），本 change 触碰面（spec-quality-base.md / ff-generation-constraints.md / 四个 SKILL.md / reference/ 新文件）与之无交集；**证据锚**：`ls openspec/changes/add-frontend-checklists/` 空 + `openspec list` 显示 No tasks（2026-08-19 实查）。
- **C7 现状消费语义与触发条件（改造起点）** — 切片建议现为「建议，非契约；节缺席时自主出 ticket」，T10-choice 现仅粒度争议触发；**证据锚**：`sdflow-init/assets/workflow/ff-generation-constraints.md:40-42`、`sdflow-implement/SKILL.md:255-256`。

## 接受的边角

- **amendments 改动波及切片但评审侧不强制同步修草图** — 概率中、影响小（D4 第三触发条件在出票时兜底，矛盾显形点本来就在出票）；完美方案（spec-review 终审加「切片同步核」）成本 = 又一条审项 + 每轮评审税；**为何接受**：出票侧单点兜住即达目标态，双侧防御是防御深度不是目标范围（通则④）。
- **D4 触发判定靠出票方自报** — 无确定性信号（C4），机械化不可行；**为何接受**：与既有能力探针同类的合法语义残余，诚实边界如实标注即可。

## 三镜代价

本次无 TG-23 命中（方案选择已在 explore + 相位 A 由人逐项拍板，无遗留 ≥2 方案待选）。
