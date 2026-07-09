# 0016 · maintain_scan 职责边界 + 报告工具反静默方向

> 状态：Accepted（2026-07-09，grill `mlh-p4-maintain-scan` design 收敛）
> 关联：MLH roadmap 阶段4·4.B · adr/0006（机械 prose MUST 脚本化）· adr/0011（目标态论证）· adr/0013（记录维护 vs 正确性门）· CONTEXT「反静默守卫」「机器锚行」「终态集」

## Context

MLH 阶段4·4.B 把 `sdflow-maintain` 手做的 set-diff 下沉为 `maintain_scan.py`（该 skill 升数据类）。grill design 时揭穿四处，共性收敛为两条跨 change 可复用的决策：**① maintain 与 sdflow-init 的 INDEX 职责边界 + 共享判据如何不漂**；**② 只读报告工具的反静默方向与「门」不同**。

## Decision

### 1. maintain / sdflow-init 的 INDEX 分治，跨 skill 共享常量用「一致性守卫」不物理单一源

- `openspec/INDEX.md` 里「rules」撞两义：**workflow bundle 规则**（`openspec/workflow/*.md`）索引在 `<!-- opsx-init:rules:start..end -->` **托管块**、归 **sdflow-init**（`update` 刷新）；**消费仓通用规则**（`openspec/rules/*.md`，可选）在托管块之外、归 **maintain**。
- maintain_scan 解析 INDEX MUST **用机器锚行界定、跳过 init 托管块**（盘面即状态/机器锚行范式）——不跳则 workflow bundle 条目被误当「已删未清理」+ 诱导越界改 init 领地。
- maintain 依赖 init 两常量（`RULE_MARKERS` 陈旧遮蔽判据、`MARK_IDX` 托管块 marker）。**canonical 留 `init.py`；maintain 保自包含副本 + 跨脚本一致性守卫 pytest**（断言相等，不等即 fail）。跨 skill import 破自包含且运行时脆（独立 symlink、sys.path 不共享），物理单一源在跨 skill 下**不可达**。
- **T17 的真闭合 = 机验同步（守卫测试），非「删到只剩一份」**——照 determ-guards 终态集跨脚本守卫范式。跨语言副本（`resolve-workflow.sh` bash 第 3 份）难同守 → defer 登记，不假装已收敛。

### 2. 只读报告工具的反静默方向 = 防「假一致」，读 0 条属响亮合法

- 报告工具（read-only diff，如 maintain_scan）的两方向失效**危险度不对称**：「解析读到 0 条 → 报全部新增未索引」是**响亮自纠**（人一眼见幻影去查）；「误读少读 → 漏报某条已删未清理 → 报『一致』」才是**假绿同构**（该红报绿）。
- 故 fail-closed 判据 MUST **锚在「解析不可信 → 防假一致」方向**，而非机械纠结「空 vs 畸形」：结构骨架可信但**读到 0 条 = 合法响亮态**（不 fail）；**结构骨架缺失 / 机器 marker 不配对 / 行畸形到解析器无法确信** = fail-closed，绝不带半信半疑的解析输出「一致」。
- 与「门」的 all-or-nothing 有别（呼应 adr/0013 记录维护 vs 正确性门）：报告工具不为「有差异」而 fail（有差异是正常产出、退出 0），只为「无法自证解析可信」而 fail。

### 3. 目标态锚定 rules/ 可选（adr/0011 落地）

- `openspec/rules/` 是**可选**目标态目录（`sdflow-init/SKILL.md:105`「不在 bundle，按需自行加」）。maintain 处理之；**缺失 = 合法空集非 fatal**。本仓（bundle 源仓）无 rules/ 是非典型特例，**MUST NOT 据现状快照砍 rules 半场**——避免以迁移现状否定设计目标。

## Consequences

- maintain_scan 与 init 有真耦合（双共享常量），由两处一致性守卫兜底；换取自包含 + 抗漂移，优于跨 skill import。
- 「报告工具反静默方向」成为可复用判据：未来任何只读对账/差异工具，fail-closed 锚「防假一致」、0 条属响亮，不照搬门的 all-or-nothing。
- rules/ 可选语义写进 spec，下游消费仓（含无 rules/ 的）均适用。

## Alternatives rejected

- **物理单一源（maintain import init 常量）**：破自包含、运行时脆、无先例。
- **R3 整个留 init、maintain 不兜底**：init 检查只在 init/update 动作跑，maintain 周期性兜底能抓「手塞规则副本没跑 update」的 gap，有独立价值。
- **fail-closed 锚「畸形当空」**：锚错方向——放过真正的「误读→假一致」静默风险。
- **据本仓无 rules/ 砍半场**：现状快照谬误（adr/0011）。
