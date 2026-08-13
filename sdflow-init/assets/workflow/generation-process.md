# 生成过程规则（Generation Process）

> **定位**：「生成好 spec」三杠杆中 **③ 生成过程**的规则。①结构、②约束已固化进
> `openspec/config.yaml`（机械可执行）；③是**唯一无法固化**的杠杆——它本质是
> human-in-loop 的对话判断。本文规定：用哪些对话 skill、什么相位、什么顺序。项目无关。

---

## 一、为什么 ③ 固化不了

```
  ① 结构/模版  → config.yaml 槽位        （机械,空槽自检）
  ② 生成约束    → config.yaml rules       （机械,生成时守）
  ③ 生成过程    → 对话判断:reframe / 选方案 / 把门 / 对抗
                = 分类里的 R 桶（焊不进任何槽位）
                → 只能固化成「规则文档」（本文）,不能固化成 config
```

所以 ③ 不进 config，进本文档。

## 二、③ = 两个相位 + 两个 skill

不是"选一个 skill"，而是两个**相位**，各有专用 skill：

| 相位 | skill | 干什么 | 产物 / 门禁 |
|------|-------|--------|------------|
| **发散** | `opsx:explore` | 想清要不要 / 是什么；reframe 问题，防过早收敛 | 无（思考即价值） |
| **收敛 + 拷问 + 生成** | `/sdflow-spec` | 澄清(A) → 拷问(B) → 生成(C) 一次连续跑；拷问结构性前置于成文 | 四件套 + decision-memo.md + **HARD-GATE** |

```
   发散 ──────────────────────► 收敛 + 拷问 + 生成
   opsx:explore                /sdflow-spec
   (问题模糊时)                  (产四件套 + 拷问前置 + 把门)
```

## 三、①② 固化后 ③ 收窄到 R 桶（历史论证见 workflow-history.md A5）

`/sdflow-spec` 相位 B 拷问是收窄后 R 桶的对话执行器；`brainstorming` 与 `grill-me` / `grill-with-docs`
两工具期的完整论证（config 固化①②后机械步如何被吸收、grill 逐项命中哪些标准与锚）已移入
[workflow-history.md](./workflow-history.md) A5。

## 四、推荐流水线（唯一入口）

```
  opsx:explore〔条件：问题模糊 / 方向未定〕   发散,想清要不要 / 是什么
        ↓ 问题已清晰则跳过
        ↓ 人示意收敛(如"开搞"/"做吧"/"开 change") → 模型自动 invoke
  /sdflow-spec                          澄清(A) → 拷问(B) → 生成(C) 一次连续跑
        ↓                               拷问结构性前置于成文；产四件套 + decision-memo.md
        ↓ /clear → /sdflow-spec-review（阶段二设计审）
  HARD-GATE 批准                        保留「未批准不实现」门禁
        ↓
  /sdflow-ship（sdflow-implement 等）
```

`sdflow-spec` 把「发散 + 对抗 + 生成」收进一个入口，且**拷问在成文之前**——改想法比改四份成文便宜。
出口序列由该 skill 原样贴出（`/clear` → 换档 → `/sdflow-spec-review`，对 [workflow.md](./workflow.md)
§三.2 的 G1 构成一处具名例外，理由见该处）。

### 自动触发规则（explore → sdflow-spec）

模型 SHALL 在以下情形自动 invoke `/sdflow-spec`：
① explore 中人示意收敛（如「开搞」「做吧」「开 change」）；
② 用户描述需求且需要开 change 时。

**模型 MUST NOT 自主判断「该开 change 了」**——须有人的示意信号才触发；explore 讨论仍在发散、用户
未表达收敛信号时，MUST NOT 自动跳转。触发方式的改变**不影响**相位 B 的拷问协议（呈现与拍板
分离协议提问、承重约束逐条站稳、停止信号需证据锚）——见 spec-authoring 的 SA-01。

### 何时跳过 explore

问题已经清晰（无需 reframe、只有一种合理框定）时，直接触发 `/sdflow-spec`，不必先过 explore。
`opsx:explore` 与 `/sdflow-spec` 互补不重叠：前者是发散工具（想清楚"要不要 / 是什么"），
后者是收敛管线（拷问结构性前置于成文的生成管线）。

### project-local schema 的作用边界

本仓及由 bundle 下发的消费项目使用 `sdflow-spec-driven` project-local schema（CLI 版本门通过时）。
schema 是阶段一入口的**结构与提示层**：它声明四件套的 artifact、依赖、委派 instruction 与
`skip_specs` 状态；官方入口读到委派 instruction 后，应按上方自动触发规则决定直接 invoke 或提示人
触发 `/sdflow-spec`。委派只改变提示与引流，**不是模型执行的机械保证**，因此仍须遵守本节规则。

版本门未通过时，安装器保持内置 `spec-driven`，并以 fail-loud 结果说明未铺设 project-local schema；
不得把旧路径默认为已经具备委派能力。迁移时必须先完成在途 change 的 schema 补写，再切换
`config.schema`，顺序不可颠倒；补写失败不得切换配置。schema fork 是一次性快照：上游
`spec-driven` 后续更新不会自动同步，本仓当前不实现 fork 漂移检测或自动 rebase。

## 五、各 skill 何时用

| skill | 触发 / 选择条件 |
|------|----------------|
| `/sdflow-spec` | **唯一生成入口**：一个入口跑完澄清 → 拷问 → 生成，拷问前置于成文。人可直接触发，模型按上方自动触发规则在人示意收敛时自动 invoke |
| `opsx:explore` | **条件**：问题 / 方向模糊、有多种框定、方案未定时先跑。清晰的变更跳过 |

## 六、与体系其余部分的关系

- **①② 在 `config.yaml`，③ 在本文**：三杠杆分工不重叠（结构+约束守机械正确，过程守判断正确+人把门）。
- **explore 的"问题模糊"是过程决策，不入 [`trigger-catalog.md`](./trigger-catalog.md)**（TG 是"按变更内容"的触发；相位选择是"按不确定性"的元决策，性质不同）。
- **拷问落的产物回流标准**：ADR ↔ BASE-12、术语 ↔ BASE-09、代码核验 ↔ D-1。`/sdflow-spec` 相位 B 拷问是这些 R 项的**对话执行器**。

## 七、检查清单（用 ③ 时）

- [ ] 问题 / 方向是否清晰？不清晰先 `opsx:explore`，人示意收敛才自动接 `/sdflow-spec`
- [ ] project-local schema 已通过版本门吗？确认委派是提示层效果，并核对迁移顺序（先补写、后切配置）
- [ ] `/sdflow-spec` 触发方式（人手动 / 模型自动）是否有明确的人示意信号？模型未自主判断「该开 change」？
- [ ] 相位 B 的拷问是否照常全深度执行（触发方式改变不缩减拷问），而不止机械自检？
- [ ] 设计是否过 HARD-GATE（用户批准）后才进阶段三？

*规则 v1 · 项目无关 · 配套 trigger-catalog.md / config.yaml / ff-generation-constraints.md*
