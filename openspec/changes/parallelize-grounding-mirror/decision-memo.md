---
schema_version: "1"
change: parallelize-grounding-mirror
branch: feat/parallelize-grounding-mirror
generated_at: "2026-07-31T23:15+08:00"
decision_hash: "113179365615"
---

# 决策纪要 — parallelize-grounding-mirror

## 承重约束

### C1 · 接地镜不依赖 autoplan 产出

接地镜核的是 spec 里已有的代码事实（函数名/字段/API 路径）vs 仓内真实代码，不读 `gstack-review.md`。
autoplan amendment 改的主要是设计约束和措辞（实测 7 个 change 的 amendment：措辞/约束/任务拆分为主），
不影响「这个函数存不存在」的判定。

证据锚：`sdflow-spec-review/SKILL.md:238` 接地镜描述 = 「grep/读真实代码，核验 spec 里所有代码事实」；
实测 7 个 change 的 amendment 内容以设计约束为主、新增代码事实引用极少。

### C2 · 领域/对抗镜仍须等 autoplan

领域镜过 `spec-checklists/domains` 的 R 项、对抗镜从设计角度找爆点——二者依赖 autoplan amendment
对 design/specs 的修订。提前跑会读到改前的设计，产出失焦的 findings。

### C3 · 净收益为正（交叉审 #18 成本诚实）

省：墙钟 = autoplan 持续时间（接地镜并行而非串行等待后才跑）。
付：零额外 token（不补跑）。
缺口：amendment 新增代码事实引用时，接地镜对该部分漏覆盖——由 code-review 的 grounding/history 镜兜底。

## 拍板决策

### D1 · amendment 后不补跑接地镜

**选定 A（不补跑）**，理由：
- code-review 接地镜是天然兜底（每个 change 必经，漏不了）
- amendment 新增代码事实引用的频率低（多数改措辞/约束）
- 补跑判据需要语义 diff spec 变更、区分「措辞改」和「新代码事实」——完美成本过高（通则④）
- 备选 B（无条件重跑）会把省下的并行墙钟又补回来，在 amendment 真发生时净收益归零
