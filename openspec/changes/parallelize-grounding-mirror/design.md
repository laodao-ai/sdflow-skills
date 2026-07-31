## Context

`sdflow-spec-review/SKILL.md:197` 的串行纪律〔T20〕要求 Step2 的所有镜 fan-out MUST 待 Step1（autoplan）checkpoint 完成后才启动。这是 P2 之前的保守设计——确保多镜评审对象包含 autoplan amendment。

P2 已闭合（档位矩阵 + resolver 就位），接地镜跑 light 档（haiku），运行时间短但被迫等 autoplan（强档或外部 codex）完成。

## Goals / Non-Goals

**Goals:**

- 接地镜与 autoplan 并行起跑，消除串行等待段的墙钟浪费
- 领域/对抗镜仍等 autoplan amendment，不损失设计判断质量
- 零额外 token 成本（不补跑）

**Non-Goals:**

- 不改 `sdflow-code-review`（它没有等价的串行约束）
- 不改 anchor/lens-metric 体系
- 不做 autoplan amendment 后的接地镜增量补跑

## Decisions

`## Decisions` → 见 `decision-memo.md`

## Approach

### 改动面

**仅 `sdflow-spec-review/SKILL.md`，三处条款改写：**

1. **串行纪律条款（:197）**：从「全部镜 MUST 等 Step1 完成」改为分治——
   - 接地镜：MAY 与 Step1 并行起跑（读当前盘面的 design/specs + 真实代码）
   - 领域/对抗镜：MUST 仍等 Step1 checkpoint 完成（它们依赖 autoplan amendment 对 design/specs 的修订）

2. **Step2 fan-out 编排（:232 表格上方）**：拆为两段 dispatch——
   ```
   Step1 开始
   ├── dispatch 接地镜（与 autoplan 并行）
   ├── autoplan 跑完 → checkpoint
   └── dispatch 领域镜 + 对抗镜（等 checkpoint 后）
   Step3 合并（接地镜结果 + 领域/对抗镜结果 + outside-voice）
   ```

3. **Step3 合并/裁决**：无改动——接地镜 findings 无论何时完成都进同一合并池。

### 不动的面

| 面 | 为什么不动 |
|---|---|
| `fanout-capability` 锚 | 记的是「跑了哪些镜」，不是「何时跑的」；`mirrors=domain,adversarial,grounding` 不变 |
| `lens-metric` 体系 | 接地镜仍跑、仍产 findings、仍被 emitter 归约 |
| `anchor_lint` | 不新增锚类型、不改已有锚的语义 |
| `sdflow-code-review` | 无等价串行约束、不受影响 |
| 能力探针 | 接地镜提前 dispatch 前仍须过能力探针（只是探针的时机从 Step2 前移到 Step1 开始时） |

### 历史运行兼容

现有条款 `:197` 末尾有一条兜底：「若历史运行已并行，Step3 裁决须 diff autoplan amendment 增量核对并在报告注明」。新设计下这条**正向化**：接地镜并行是默认行为，不再是需要额外注明的例外。该兜底条款删除。

## Risks / Trade-offs

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| autoplan amendment 新增代码事实引用，接地镜漏覆盖 | 低（实测 7 change 的 amendment 以设计约束为主） | 中（该代码事实不符直到 code-review 才被发现） | code-review 的 grounding/history 镜是天然兜底；接受残余风险（D1） |
| 能力探针时机前移导致 edge case | 极低（探针逻辑不变，只是提前跑） | 低（失败 = 缩 roster，与现有降级路径一致） | 无需额外缓解 |

## Success Metrics

1. 接地镜在 autoplan 运行期间即已 dispatch（可从报告时间戳/执行顺序观测）
2. 领域/对抗镜仍在 autoplan checkpoint 之后 dispatch（串行纪律未被放松到它们）
3. 无回归：anchor_lint / lens-metric / validate 全绿
