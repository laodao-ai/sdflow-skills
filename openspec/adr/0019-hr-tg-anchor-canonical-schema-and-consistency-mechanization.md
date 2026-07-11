# 0019 · hr-tg 锚 canonical schema + 一致性机械化面治（机械尽头才是语义残余）

> 状态：**Proposed**（2026-07-11，grill `harden-hr-tg-anchor-consistency` 收敛时立）——待该 change ship + dogfood 验证 M1/M2/M4/M-new 落地后升 Accepted。
> 关联：adr/0006(b)（机械 prose MUST 脚本化）· adr/0018（机械校验器输出诚实）· CONTEXT「目标态论证」· memory「机械化优先+目标态基准」「一个 change 一个完整阶段结果」。

## Context

`sdflow:hr-tg` 锚是 spec/code 两评审共享的契约（承「本变更命中的 HR-TG 子集」判定、门控领域 cross-model）。grill 揭出两组问题：

1. **schema drift**：主 spec `spec-workflow:550` 定义锚为 `hit=/evidence=`（无 declared），而 mlh-p4 的码 + `hr-tg-intersection-check` capability 已要求 `declared=` 必填——两套 schema 并存、未回灌，存量锚混杂 `evidence=`-only 与 `declared=` 两形态。
2. **机械化不彻底 + 碎片化妥协**：`anchor_lint.check_hr_tg` 只查字段在场（docstring 明写「字段值任意合法、不校验 CSV 内容」）；把加固拆成 T136/T138/T140 等 defer fragment 后，逐个对着现状（"存量多是手写 evidence=、重 lint 场景少"）提问，各自给出 WARN 降级 / `--allow-legacy` / 旧格式 grace 等**妥协**——这些妥协恰是碎片化 + 现状论证的产物。

## Decision

**一、canonical schema = 三字段并存**：hr-tg 锚 = `hit=`（脚本 emit）+ `declared=`（脚本 emit，承模型判定的完整命中集、**canonical 必填**）+ `evidence=`（人手填、`hit≠none` 时非空的判据触发点）。`declared=` 与 `evidence=` 正交并存（一个给机器重算、一个给人复核）。回灌 `spec-workflow:550` 统一口径。

**二、把 hr-tg 锚一致性一次机械化到目标态、全 fail-closed、零妥协**（面治，非逐 fragment 点补）：
- **M1** `declared=` 硬必填（无 grace / 无迁移旁路）；
- **M2** `hit = declared ∩ HR-TG` 确定性重算，逐元素一致否则违规；
- **M3** tg-set / 成员行边界严格解析，空 cell / 宽松 token fail-closed；
- **M4** `hit≠none ⟹ evidence=` 在场非空；
- **M-new** declared/hit 的每个 TG 须存在于 catalog 全 TG 集（拦手误/幻觉 TG 被静默丢出 hit）；
- `--trigger-catalog` **必需**、缺失 fail-closed（不 WARN 降级——降级=fail-open 架空门）。

**三、机械尽头才是语义残余（S1）**：`declared` 本身是否=真命中集**无确定性信号**（「命中哪些 TG」归模型，adr/0018），故留语义（模型判定 + `evidence=` 人读 + git 审计）。M2 只堵 `hit⟺declared` 内部一致性，**不使锚 tamper-proof**——这是完整机械化后剩下的**合法机械/语义边界，非缺口、非妥协**；实现/文档 MUST NOT 冒充 tamper-proof。

## 为何这样（判据）

- **机械化优先 + 目标态导向**：能确定性校验的一致性（M1–M4、M-new）MUST 机械化到位；锚目标态（所有锚经脚本产出必有 declared=），MUST NOT 用现状存量（evidence=-only 多）论证"覆盖薄、可不做"。
- **一次做完整根治碎片化妥协**：把一件事（hr-tg 锚一致性机械化）作为一个完整交付物一次做全、fail-closed，那些"对现状提问→给妥协（WARN/grace/flag）"根本不产生。
- **诚实边界非妥协**：S1 留语义是机械能力的真实尽头，不是为现状让步。

## Consequences

- **正**：hr-tg 锚一致性获确定性机械保证（拦手改单字段绕过、手误 TG、坏输入、schema drift）；口径单一源、零妥协；诚实边界清晰。
- **负 / 代价**：`--trigger-catalog` 必需 → 工具（`sdflow-init update`）与 SKILL（setup.sh）部署 skew 时 anchor_lint 会 fail-closed 硬失败——**这是有意的**（响亮暴露 > 静默降级），由 pull→setup 原子纪律兜（CLAUDE.md）。
- **残余**：declared 正确性仍靠模型 + git 审计（S1），非机械可保。
- **对 adr/0018**：本 change 是 0018 首形态 dogfood 之一，落地后为 0018 升 Accepted 补实证。
