<!-- sdflow:step1-broad-review v1 mode="grill-substituted" -->

# Step1 广审层（gstack-review）— issues-pool-hardening

## 模式：grill-substituted（诚实标注，非 native、非 simulated）

本 change 的广审层**不是**经 autoplan 原生跑出，而是被本 change 已完成的**交互式 grill-with-docs on design.md**实质替代。诚实口径如下——不伪装 native、也不算 simulated：

- **grill 实际覆盖**：逐一深挖 design.md 的 4 个决策（D1 T2 reject / D2 T1 --strict / D3 T4 幂等 / D4 T5 抽取），每个都接地读真实 recorder 代码核验、给推荐、human-in-loop 拍板。深度**高于** autoplan 的 design/eng 镜（后者是一次性 fan-out，grill 是往复深挖）。产出 3 处实质改动（D1 escape→reject+broaden、D2 加 --strict、D3 收敛 match-or-error）+ ADR 0010。
- **grill 未覆盖（诚实缺口）**：autoplan 的 **CEO 镜（产品/战略价值）** 与 **DX 镜（开发者体验）** 未系统跑。评估：本 change 是内部工具健壮化（无产品面、无外部 DX 面），这两镜边际价值低，缺口可接受——但**明确记录为未跑，非"跑过且无发现"**。
- **独立性说明**：grill 是与主 session 往复（非 fresh-context 冷视角），故 Step2 的 fan-out 多镜（领域/对抗×2/接地，均 fresh context）承担 cold-independent 层——这层不可省，正是为补 grill 的"非冷"。

## 串行纪律（T20）满足

grill 的全部 amendment（`1a81bf3` D1 + `0d56f08` D2/D3/D4 + `cd149b9` ADR）已在 Step2 fan-out **之前**提交。故 Step2 多镜评审的对象包含广审层（grill）的 amendment，串行纪律满足。

## 降级声明

本层非 autoplan 原生执行 → 无 codex outside-voice 产物可复用。Step2 若判需 outside voice，走自跑设计 outside-voice 回落路径（site="design-voice"），不复用一个不存在的 autoplan 产物。

## 交 Step3 合并池的广审 findings

grill 已把 findings **就地消化**为 amendment（非留作待裁 findings）：escape 的 YAGNI/throwaway 问题（→ reject）、恒 exit0 的反静默口子（→ --strict）、无脑 skip 的静默吞坑（→ match-or-error）。这些不再作为 open finding 进 Step3 池，但其**结论**供 Step2 多镜独立复核（多镜被明确要求"别默认接受 grill 结论"）。
