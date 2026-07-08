# roadmap 回写重构：编号统一投影链取代起手锚 best-effort

`done-roadmap-writeback` 经 spec-review 7 镜冷审 + 两次用户目标态基准纠正，从「起手锚 + best-effort 回写」（`adr/0013`）重构为「编号统一 + producer 机械生成投影链」。本 ADR 记录该转向，**部分 supersede `adr/0013`**。

## Context（spec-review 根因 + 两次目标态纠正）

**spec-review 根因**：7 镜（广审/对抗×3/接地/哲学/codex）收敛到——关联锚 producer 契约**无机械闭环**：L1/L2 全靠 grep 起手写死的 proposal 锚，但「起手 MUST 带锚」只是 prose 声明、无 lint/gate。哲学镜锋利判定：grill 时把 L1 从「解析自然语言」纠正到「读机器锚」**只走了一半**——「producer 会带锚」这个目标态假设若无机械支撑，就是把 `adr/0011` 目标态论证（解析器语义）误套到「人是否遵守无门禁 prose MUST」（行为合规），恰是 `adr/0006` 点名的静默跳步。对抗镜另揭**致命误勾**：锚 subtask 集起手写死，实现期 defer 一项则「全定位→勾全部」把从未交付的子任务机械勾成 `[x]`，污染「复选框=真相源」不变量。

**两次目标态纠正（用户）**：① MUST NOT 用现状（opsx:ff 官方不可改、tasks 现用局部编号 1.1、约定靠自觉）反驳/限制目标；② **编号统一洞察**——roadmap 子任务号与 change tasks 号统一，则映射消失、真相源 = 归档实况盘面。

## Decision

1. **真相源 = 归档实况盘面（change tasks.md 完成态），非起手锚快照**。起手锚固化的 subtask 集是「可变状态写死的第二真相源」（CONTEXT『盘面即状态』明令反对）；归档时 change tasks.md 完成态是**现成盘面**（`sdflow-done` 第 0.3 步已对账复选框）。
2. **编号统一**：roadmap 子任务号（`4.D.1`）= 唯一编号体系（跨 change 全局）；roadmap 驱动 change 的 tasks.md **顶层组采用之**（`## 4.D.1 …`）。roadmap 回写 = **镜像** tasks 组完成态 → roadmap 复选框（同号、零映射、组内全 `[x]`→勾）。
3. **producer 机械生成投影链**（四环，每步确定性产出、不靠人写对）：① roadmap 生成侧结构化（子任务号 + 阶段状态 enum + task-log 机器锚）② **change scaffold**（从 roadmap 指定子任务机械生成 tasks 骨架 + `roadmap: {name}` 锚 + proposal 引用）③ 实现勾 tasks（defer 组留 `[ ]`）④ done 镜像回写。
4. **关联判据收缩**：L1（关联哪个 roadmap）= 读 tasks 的 `<!-- roadmap: {name} -->` 锚（scaffold 机械写）；漏锚兜底 = lint（tasks 用 roadmap 式编号 `N.X.Y` 却无 name 锚 → **fail-closed 拦，非静默**——tasks 编号形态是「这是 roadmap 驱动 change」的机械可判信号）。L2（哪些子任务 + 完成没）= 扫 tasks 顶层组完成态（靠盘面，**不靠锚 subtask**）。
5. **best-effort 大幅简化**：同号镜像消除「散文层 id 误命中 / subtask 校验 / 起手声明≠交付」一堆补丁；残余 best-effort 仅「roadmap 复选框号与 tasks 组号不匹配（roadmap 改号）→ 降级标注留人工」，概率低。

## supersede adr/0013

- `adr/0013` D-1（锚 `name+phase+subtask` schema）→ 本 ADR 收缩为**仅 name 锚**，subtask/完成靠 tasks 盘面。
- `adr/0013` ADR-4（best-effort 三级作**主**机制）→ 本 ADR 降为**残余兜底**（主机制 = 同号镜像）。
- `adr/0013` 生成侧结构化 / 机械-判断切分 / 旧 2 迁移 → **保留 + 强化**（增 scaffold 环、enum 机械化）。

## Considered Options

- **编号统一投影链（选中）**：真相源 = 盘面、producer 机械生成、Q1（锚校验）/Q2（误勾）消解、编号映射消失。代价：新 producer 能力（change scaffold）+ roadmap 驱动 change 的 tasks 编号约定（但**机械生成、非自觉**）。目标态正解。
- **起手锚 + best-effort（`adr/0013`，弃）**：spec-review 揭穿锚 producer 契约无机械闭环（哲学镜）+ 误勾（对抗镜）；靠「人记得写对锚」= 与原痛点同构、`adr/0006` 静默跳步。
- **保留起手锚但补一堆 lint/校验（弃）**：打补丁而非根治；用户目标态基准否决「靠约定+lint 兜底」的妥协。

## Consequences

- design/proposal/specs/tasks 按新骨架重写 `[spec-review-amendment]`。
- 新 producer 能力 **change scaffold**（`sdflow-roadmap` 子命令或 `roadmap-scaffold` 脚本，从 roadmap 子任务生成 change tasks 骨架 + name 锚 + proposal 引用）。
- spec-review D1–D10 在新骨架下：**D3 定位鲁棒大半消解**（同号结构化、无散文误命中）、D4 enum 机械化保留、D5（SKILL:195 误引删）/D6（3.5 步 model 档位）/D7（bundle 纪律改 assets/workflow）/D8（幂等键）/D9（enum 单一源）保留、D1/D2 fail-safe 简化（漏锚 lint 拦、降级标注落 task-log）、D10 漂移对账（阶段 enum 派生可加 reindex 式校验或 todolist 记）。
- CONTEXT：新术语「编号统一投影」「producer 机械生成链」。
- **与 `adr/0011` 真正对齐**：目标态论证的正确用法 = producer 契约机械保证，非「人遵守 prose MUST」——这是本次 grill→spec-review 走完的完整纠偏。
