# 子系统详细设计 skill（`sdflow-subsystem`）：L2 方法论 · 落地形态 · 与 L1/roadmap 的关系

> 状态：**活文档**（explore 讨论基线，随后续逐题拍板回填结论；尚未接地试跑，多数决策为「倾向 + 待验」）。
> 来源：2026-07-12 `/opsx:explore`——承接 `00-methodology-discussion.md` §5「L2 空档」的 Q2（落地形态）/ Q4（沉淀 skill）。
> 定位：本文之于 L2，如 `02-architecture-skill-design.md` 之于 L1——是**子系统详细设计 skill 的设计讨论**（L2 方法论 + skill 形态合一）。
> 命名已定（2026-07-12 拍板）：skill = **`sdflow-subsystem`**（与 `sdflow-architecture`=系统级 构成 系统/子系统 层级对）；产物暂称 **SSD**（SubSystem Design）。
> 引用不复述纪律：L1 判据（R1–R11/AP1–4）、contract 五层、状态机等**引用 `sdflow-architecture/references/` 与 00/02**，本文只写 L2 的**增量与差异**。

---

## 0. 一句话定位

`sdflow-architecture`（L1）把**系统**切成子系统 + 定子系统间 contract；`sdflow-subsystem`（L2）把**一个子系统**切成子模块 + 定子模块间 contract + 说明**子模块如何共同实现子系统对外 contract** + 标注意事项。**同一个递归分解算法，下沉一层。**

```
        空间轴分解树                        skill              产物落点              状态
┌──────────────────────────────────────────────────────────────────────────────────┐
│ L1  系统 → 子系统 + 子系统间 contract     sdflow-architecture  architecture/sad.md   ✅ 已建
│         │  下钻单个子系统（just-in-time）
│ L2  子系统 → 子模块 + 子模块间 contract   sdflow-subsystem     architecture/         ❌ 本文要设计
│         │      + 子模块实现子系统对外 contract               subsystems/<sub>.md
│ L3  子模块 → task / change               opsx:ff             changes/               ✅ 已建
└──────────────────────────────────────────────────────────────────────────────────┘
```

业界坐标（承 00 §1 对照表）：L1=C4 Container / arc42 L1，**L2=C4 Component / arc42 Building Block View L2 / DDD Aggregate**，L3=C4 Code。

---

## 1. 判据复用 + L2 的四个增量

**复用（不重写）**：子模块分解与子系统分解用**同一套判据**——R1–R11（变化率/单写者/context 预算/依赖形状/仲裁序/粒度带 3–7/边界往上合内部往下拆）+ AP1–4 反模式黑名单 + contract 五层 + 假设显影 + 数值溯源三态 + 冷走查 + 人门。这是 L2 归 `sdflow-architecture` 家族（递归内核）而非另起炉灶的根本理由。

> 先例已埋伏笔：`decomposition-rules.md` R8.3 明确「同一语义域内的独立变化簇 → 记为该子系统的 **L2 内部模块候选**，不升子系统」——**L1 分解时已在替 L2 攒输入**。L2 的起点部分来自 L1 已挂账的候选。

**L2 相对 L1 的四个增量**（= 为什么不是「L1 原样再跑一遍」）：

| # | 增量 | L1 对应物 | 说明 |
|---|---|---|---|
| A | **输入不同** | L1 输入=系统事实三问 | L2 输入=**一个已 validated 的子系统对外 contract** + 该子系统在 L1 攒的 L2 候选 + 横切约定 |
| B | **前置门不同** | L1 前置=已 sdflow-init | L2 前置=**该子系统对外 contract 已 `validated`**（被骨架真穿过）——纸上 contract 上做 L2 是沙上盖楼（02 §414） |
| C | **核心不变量不同** | L1=穿越点集==子系统集 | L2=**子模块实现覆盖 ⊇ 子系统对外 contract 全集**（见 §3，L2 机械杀手锏） |
| D | **时机语义不同** | L1=一次切全系统空间 | L2=**just-in-time 单个子系统**，深度∝风险，不设「全部 L2 完成」全局 barrier（02 §404/415） |

---

## 2. D1（已定）：新 skill `sdflow-subsystem`，共享 references 判据真相源

三选一里排除 (b) 判据复制（双写发散违背 S11），实拍在 **(c) 新 skill + 共享判据真相源**——判据仍单一源在 `references/`（`decomposition-rules.md`/`quality-criteria.md`/`review-lenses.md`），L2 skill **引用它们**，只自带 L2 的编排 + §1 四增量。三镜佐证：

| 镜 | 判定 | 理由 |
|---|---|---|
| 系统 | 支持 (c) | 分解内核 100% 复用；判据单一源不双写 |
| 用户（操作者） | 支持 (c) | 触发面天然分开——「设计系统架构」(L1) vs「细化 X 子系统」(L2) 是两个意图动词，不必在一个 skill 内分流 `--level` |
| 开发循环 | 支持 (c) | 改一次 R 规则两层受益；无 `if level==...` 分支膨胀 sad_scaffold |

**主次判定**：主驱动 = 判据单一真相源 + 编排增量（§1 四项）确实不小，塞进 `sdflow-architecture` 会让脚手架长满 level 分支 → 独立编排更干净。**未决子项**：`sdflow-subsystem` 是否需要自己的脚本（`ssd_scaffold`/`ssd_lint`），还是能薄到只靠 SKILL.md 编排 + 复用 `sad_*` 的部分能力——待 §6 接地试跑定。

---

## 3. D3：L2 的机械杀手锏——contract 完备性不变量

L1 有「穿越点集==子系统集」。L2 的类比物更有价值，直接守住「**内部分解不得改变对外承诺**」：

```
子系统对外 contract 全集   ─┐
   c1  c2  c3  c4           │  完备性: {c1..c4} ⊆ ∪ impl(mᵢ)   每条对外 contract
   │   │   │   │            │           被 ≥1 子模块「实现指派」覆盖（无遗漏）
   ▼   ▼   ▼   ▼            │  无越权:  子模块不产生越界的对外承诺（内部 contract
 ┌────────────────────────┐ │           不外泄成系统级对外契约）
 │ 子模块 m1 m2 m3（各实现哪几条）│
 └────────────────────────┘ ▼
```

若子系统对外 contract 带**稳定 ID**，这条完备性可机械校验（scaffold/lint 直接验覆盖，无遗漏无越界）。**这可能是 `sdflow-subsystem` 最该先钉死的机械核**——L1 没有的、L2 独有的确定性价值。（依赖 D2 落点决定 contract ID 从哪读。）

---

## 4. D2（待拍）：L2 contract 落点 —— `architecture/subsystems/` 文档 vs `openspec/specs/`

00 §5 选项 c 是当前倾向：**子模块 contract 进 `specs/`（capability specs），L2 文档只放「决策 + 注意事项 + 引用」，contract 一律引用不复述**（复用 delta-spec 回流机制——最难的基建已存在）。但 explore 补出一条 00 未展开的**一致性张力**：

> L1 的子系统对外 contract 现在**写在 `sad.md` 第 5 节正文里**（mqtt-console 那份即是）。若 L2 子模块 contract 进 `specs/`，则 **L1 contract 在 `architecture/`、L2 contract 在 `specs/` —— 两层 contract 落点不一致**。

两条出路，待拍：
- **接受不对称**：L1=「系统骨架契约」留 SAD、L2=「能力契约」进 specs（各有其位，语义不同）；
- **统一回流**：L1 子系统 contract 也回流 specs、sad.md 只引用——但要**动已建的 L1**（成本 + 迁移）。

（现实佐证：mqtt-console 早期 `requirements.md` 已有「架构层契约见 capability `mqtt-console-architecture`」——contract 进 specs 的模式在该项目实践过。）

---

## 5. L2 与 roadmap：正交两轴，不是上下游

### 5.1 现实病灶（接地证据）：L2 现在寄生在 roadmap 里

mqtt-console 每个 roadmap 包都带一份 `technical-architecture.md`（"内部接缝：拓扑/分层/消息管线/Engine/连接/存储/变量/i18n"）——**这就是事实上的 L2**，只是没有正规 home，塞进了 per-effort 的 roadmap。由此长出的病：

```
「子系统内部怎么实现」散在 ≥3 处、互相漂移：
  ① roadmaps/mqtt-console-v2/technical-architecture.md   per-effort，绑 roadmap
  ② roadmaps/mqtt-console/technical-architecture.md      v1 那份，已加横幅「单向前指 v2」防漂移
  ③ architecture/sad.md 第5节                            SAD 过度下探（消息运行时已列 MessagePump/Router/Reconciler/Sink）
```
- **绑错轴**：详细设计跟 roadmap effort 走（v1/v2 各一份）→ 只能加横幅防漂移。**它是 per-system 的，不该 per-effort。**
- **M 阶段 owns 在 roadmap**：M1–M5 定义全在 `roadmaps/`；SAD 里的 `M2b/M4` 是借来的。

这正是 L2 空档的代价——**没有正规 home，详细设计到处寄生**。`sdflow-subsystem` 在成熟项目的第一个动作因此是**搬家**（从 roadmap `technical-architecture.md` 抽出 → 落 `architecture/subsystems/`），而非从零写（增量 E：存量迁移）。

### 5.2 正交两轴 + 驱动关系

roadmap（时间轴）与 L1/L2（空间轴）都是「从 SAD 往下细化」，但沿不同的轴——这是它们易混的根因：

```
                         L1 SAD  (architecture/sad.md, per-system 单例)
                       /         |           \
              沿时间轴 ↓   沿空间轴 ↓      沿决策轴 ↓
            ┌──────────┐  ┌──────────┐   ┌────────┐
            │ roadmap  │  │ L2 子系统 │   │  ADR   │
            │ 阶段/排期 │  │ 子模块细化 │   │ 决策链  │
            │per-effort│  │per-system │   │per-sys │
            └──────────┘  └──────────┘   └────────┘
         roadmaps/{name}/  subsystems/{sub}/  adr/
```

二维网格里看得最清（承 00 §140「阶段是时间切、子系统是空间切、正交」）：

```
        时间轴 (roadmap 阶段) ────────────────▶
       │  M1(已ship)  M2(命令资产)  M4(调试上下文)
  空 ──┼──────────────────────────────────────
  间 连接传输   │ L2✓        (稳定)      (稳定)
  轴 消息运行时  │ L2✓        (稳定)      (稳定)
  下 命令资产   │ planned    ◀L2细化中    (稳定)
  钻 调试上下文  │ planned     planned    ◀L2细化中
  ▼ 存储基座   │ L2✓        (演进)      (演进)
       近───────────细 | 远──────────────雾
```

- **roadmap = 水平切片**（一阶段 = 跨多子系统的一个交付价值，tracer bullet）；**L2 = 垂直纵深**（一子系统 = 跨多阶段的一条演进线）。二者正交，同 `decomposition-rules` §「两轴正交」几何。
- **驱动关系**：roadmap 阶段边界 = L2 的**入场券发放点**。阶段激活某子系统 → 才对它做 L2（just-in-time）。L2 细化程度沿时间轴衰减 = 「近细远雾」（02 §416 的成因）。
- **粒度错位**：阶段 : 子系统 = **M:N**（一阶段垂直穿多子系统），非 1:1——是「阶段激活一组子系统的部分 L2」。

### 5.3 编排洞察（待验）

既然 roadmap 阶段「激活」子系统、L2 才入场——**roadmap 可能是 L2 的调度器**：阶段进入实施窗口时，对该阶段激活的子系统触发 `sdflow-subsystem`（类比 `sdflow-ship` 编排 `sdflow-implement`）。但 M:N 错位意味着不是「一阶段=一子系统 L2」。是否要真做这层编排联动，待接地。

---

## 6. 时机门 + 接地试跑建议

- **前置门（增量 B）**：`sdflow-subsystem` 拒绝在对外 contract 仍 `planned`/`draft` 的子系统上启动（或响亮警告）——纸上 contract 上做 L2 是沙上盖楼。
- **just-in-time（增量 D）**：触发是「细化 **X** 子系统」，**不是**「细化所有子系统」；不设全局 barrier。

**接地先行（承 00 §172「先 Q1 后 Q2，拿真项目跑一遍再定形态」）**：拿 mqtt-console **消息运行时**子系统手跑一次 L2（它对外 contract 最重、子模块最明显：MessagePump / Router / Reconciler / Sink / gap），一次验三件事——① 判据递归是否顺手 ② 完备性不变量（§3）怎么落 ③「搬家 + roadmap 引用」（§5.1）的关系。避免纸上设计 L2 skill。

---

## 7. 开放决策清单（对标 00 的 Q 清单，逐题拍板回填）

| # | 问题 | 状态 | 指针 |
|---|---|---|---|
| D1 | skill 归属：递归参数化 vs 新 skill | ✅ 已定 | 新 skill `sdflow-subsystem` + 共享 references（§2） |
| D2 | L2 contract 落点：`specs/` vs `architecture/subsystems/`；L1/L2 落点不一致如何收 | ⏳ 待拍 | §4 两条出路 |
| D3 | 完备性不变量的机械实现（需 contract 稳定 ID，依赖 D2） | ⏳ 待拍 | §3 |
| D4 | L2 是否需自带脚本（`ssd_*`）还是薄编排复用 `sad_*` | ⏳ 待接地 | §2 未决子项 |
| D5 | T1：M 阶段成熟度谁 owns——SAD 现混入了时间轴（`draft(M2b planned)`），目标态应 SAD 只标空间成熟度、M 阶段引用 roadmap | ⏳ 待拍 | §5.1 |
| D6 | roadmap→L2 编排联动是否要做（阶段激活触发 L2，M:N） | ⏳ 待验 | §5.3 |
| D7 | contract 机械化档位（承 00 Q3：schema / contract test / CI fitness function 爬到哪档） | ⏳ 待拍 | 00 §Q3 |

**建议顺序**：先 §6 接地试跑（消息运行时）→ 回填 D2/D3/D4 → 再考虑开 `add-sdflow-subsystem` change 走设计门。

---

## 参考锚（增量部分；判据谱系见 00 §Q1 与 `references/`）

- Parnas 1972 信息隐藏（子模块层同样适用）· C4 Component 层 · arc42 Building Block View L2 · DDD Aggregate/战术设计
- 02 §404–416（骨架先行 / L2 just-in-time / 不全量先行 / `architecture/subsystems/` 落点）
- `decomposition-rules.md` R8.3（L2 内部模块候选挂账）· R9（边界往上合、内部往下拆）
- 00 §5（L2 空档三选项 abc）· §140（阶段/子系统正交）· §172（接地先行序）
