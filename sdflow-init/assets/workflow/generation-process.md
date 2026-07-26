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

## 二、③ = 三种对话相位 + 四个 skill

不是"选一个 skill"，而是三个**相位**，各有专用 skill：

| 相位 | skill | 干什么 | 产物 / 门禁 |
|------|-------|--------|------------|
| **发散** | `opsx:explore` | 想清要不要 / 是什么；reframe 问题，防过早收敛 | 无（思考即价值） |
| **收敛** | `brainstorming` | 逼出 2-3 方案 → 逐段批准 → 落设计 | design doc + **HARD-GATE** |
| **对抗压测** | `grill-me` / `grill-with-docs` | 把设计往死里问，逐分支死磕薄弱处 | 共识（docs 版还落 ADR/术语） |

```
   发散 ──────────────► 收敛 ──────────────► 对抗验证
   explore           brainstorming        grill(-with-docs)
   (问题模糊时)        (产出+把门)           (死磕分支+对齐术语+落ADR)
```

## 三、关键洞见：①② 固化后，③ 收窄到 R 桶，grill 价值反超 brainstorming

config 固化①②后，brainstorming 的机械步被吸收（方案落 BASE-12 槽、自检靠 S 扫描、写文档靠 ff），只剩 R 桶。而 **grill 正是专锤 R 桶的工具**——逐项命中标准与锚：

| grill（尤其 -with-docs）的动作 | 命中的标准 / 锚 |
|------|------|
| 揪模糊 / 重载术语 → 定准 | BASE-09 歧义 / 术语定义 |
| 代码 vs 主张 不一致就揭穿 | D-1 代码事实（Accurate · 锚① 代码库） |
| 编边界场景压测 | BASE-01 四类场景 + BASE-06 错误路径 |
| 逐分支死磕决策树 | BASE-27 时序可执行性（实现者会卡哪） |
| 落 ADR + 词汇表 | BASE-12 ADR + 锚③ 既有决策 / ADR |

结论：**brainstorming 是"产设计"的收敛器，grill 是"锤设计"的对抗器。** 结构与约束已被 config 守住后，真正稀缺的是**对抗压测**——grill 比再跑一遍 brainstorming 的机械自检更值钱。

## 四、推荐流水线（**两条分支，先判装没装 `sdflow-spec`**）

### 分支 A —— 已装 `sdflow-spec`：单入口（**默认路径**）

```
  /sdflow-spec                          澄清(A) → 拷问(B) → 生成(C) 一次连续跑
        ↓                               拷问结构性前置于成文；产四件套 + decision-memo.md
  HARD-GATE 批准                        保留「未批准不实现」门禁
        ↓
  opsx:apply
```

`sdflow-spec` 把「发散 + 对抗 + 生成」收进一个入口，且**拷问在成文之前**——改想法比改四份成文便宜。
它 `disable-model-invocation: true`，**只能人触发**。出口序列由该 skill 原样贴出（`/clear` → 换档 →
`/sdflow-spec-review`，对 [workflow.md](./workflow.md) §三.2 的 G1 构成一处具名例外，理由见该处）。

### 分支 B —— 未装 `sdflow-spec`：旧三步（沿用，未被删除）

```
  〔问题模糊 / 方向未定〕opsx:explore     发散,想清要不要 / 是什么
        ↓
  opsx:ff（config 守①②）               生成,结构 + 约束已固化
        ↓
  grill-with-docs                       对抗压测:死磕分支 + 对齐术语 + 查代码 + 落 ADR
        ↓                               （吃掉 brainstorming 大部分剩余价值）
  HARD-GATE 批准                        保留 brainstorming 的「未批准不实现」门禁
        ↓
  opsx:apply
```

净分工（分支 B 内）：**explore 发散（条件）· grill 对抗（主力）· brainstorming 收窄为「产设计 + 把门」。**

### 四入口选择规则（**规则，不是建议**）

- **默认走 `/sdflow-spec`**：装了它就用它；MUST NOT 默认拿 `opsx:ff` 起手。
- **仅下列三种情形用旧三步**：① 需要 wayfinder 跨会话铺图（`sdflow-spec` 不覆盖该职责）；② 用户明确要求分步执行；③ `sdflow-spec` 因环境原因不可用（未跑 setup / Codex 宿主降级不可接受）。走旧三步的那次运行 SHALL 在完成报告里说明为何未走单入口。
- **模型侧**：模型 MUST NOT 自行选 `opsx:ff` 绕过拷问；判断需要开 change 时 SHALL 提示用户触发 `/sdflow-spec`，MUST NOT 直接调 `opsx:ff`。
- **旧三步仍是合法路径**：三个原入口未被删除；分支 B 里 grill 一律全深度，MUST NOT 因「反正以后会换单入口」而瘦跑。

## 五、各 skill 何时用

| skill | 触发 / 选择条件 |
|------|----------------|
| `/sdflow-spec` | **默认**（装了就用）：一个入口跑完澄清 → 拷问 → 生成，拷问前置于成文。只能人触发 |
| `opsx:explore` | **条件**：问题 / 方向模糊、有多种框定、方案未定。清晰的变更跳过。走分支 B 时用 |
| `brainstorming` | 需要从零产出设计 + 要 HARD-GATE 时；config 固化后**瘦着跑**（只做澄清/选方案/把门，跳过机械自检） |
| `grill-me` | 无领域文档基建时的轻量对抗压测（纯拷问） |
| `grill-with-docs` | 有领域文档（术语表 / ADR）时：对抗压测 + 对齐术语/领域模型/代码 + 落档（维护长期真相源） |

## 六、grill-with-docs 路径适配（重要）

`grill-with-docs` 默认领域文档约定为 `CONTEXT.md`（术语表）+ `docs/adr/`（ADR）。
**复用到本框架前，先把它的路径约定对齐到你的 repo 结构**，否则它会另起一套 `docs/adr/`，
与你已有的 ADR / 术语源形成**第二套真相源**（正是我们一路在消除的漂移）。

> 本仓库示例：ADR 在 `docs/gstack/`（如 Product_Boundary_ADR）、术语 / 规格在 `openspec/specs/`、
> 设计强制规范索引在 `openspec/INDEX.md`。用 grill-with-docs 时让它读写这些位置，而非新建 `docs/adr/`。

## 七、与体系其余部分的关系

- **①② 在 `config.yaml`，③ 在本文**：三杠杆分工不重叠（结构+约束守机械正确，过程守判断正确+人把门）。
- **explore 的"问题模糊"是过程决策，不入 [`trigger-catalog.md`](./trigger-catalog.md)**（TG 是"按变更内容"的触发；相位选择是"按不确定性"的元决策，性质不同）。
- **grill 落的产物回流标准**：ADR ↔ BASE-12、术语 ↔ BASE-09、代码核验 ↔ D-1。grill 是这些 R 项的**对话执行器**。

## 八、检查清单（用 ③ 时）

- [ ] 装了 `sdflow-spec` 吗？装了就走**分支 A 单入口**；走旧三步须命中 §四 三种例外之一并在报告说明
- [ ] 问题/方向是否清晰？不清晰先 `opsx:explore`，别直接 ff（分支 B）
- [ ] 生成后是否做过**对抗压测**（grill），而不止机械自检？
- [ ] 设计是否过 HARD-GATE（用户批准）后才进 apply？
- [ ] grill-with-docs 是否读写本 repo 的 ADR/术语位置，未另起第二套？
- [ ] brainstorming 是否"瘦着跑"（未与 config 的机械自检重复）？

*规则 v1 · 项目无关 · 配套 trigger-catalog.md / config.yaml / ff-generation-constraints.md*
