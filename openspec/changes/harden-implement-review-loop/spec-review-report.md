# 设计评审报告 · harden-implement-review-loop

> 阶段二 `/sdflow-spec-review` 编排评审。Step1 autoplan 广审（原生）+ Step2 并行多镜 + Step3 对抗裁决，合并为本报告。
> **中途不打断（G2）**：撞到「≥2 方案 / 核验不了的事实」不 AskUserQuestion，写进下方**决策登记区**，人工在设计 HARD-GATE 一次性拍板。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-19,TG-23,TG-25" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->

## 本轮阵容

| 层 | 镜 | runner | 产出 |
|---|---|---|---|
| Step1 广审（autoplan） | CEO / Eng / DX 各一对双声（Claude 独立子代理 × Codex voice） | claude + codex | 52 |
| Step2 领域镜 | `spec-quality-base.md` R 项 + TG-19/23/25 激活槽 | claude | 2 |
| Step2 对抗镜 A | 逐条实现期执行推演 | claude | 3 |
| Step2 对抗镜 B | 正面攻击 D2a/D2b 判断本身 | claude | 5 |
| Step2 接地镜 | 24 条代码事实机械核验 | claude | 0（**全部属实**） |
| Step1.5 outside-voice | `site=design-voice`（跨模型） | codex | 3 |

**规划依据**：无 backend/embedded/frontend 栈命中（纯 Markdown 编排类）⇒ 领域镜跑通用基线而非栈清单；autoplan 已含 eng 镜 ⇒ 领域镜与对抗镜均明确避开 eng 视角（防重叠 1.4）；HR-TG∩ = ∅ ⇒ 不开 hr-tg cross-model。

**outside-voice 复用守卫**：`outside_voice_guard.py` 判 `section-not-found`（exit 1）⇒ 不复用 autoplan 的 codex 产出，**回落自跑 design-voice**（`.rc`=0 ⇒ `reason_code="ok"`，`OV_TRUNCATED=false`）。

---

## 收敛口：**不建议按现状进设计 HARD-GATE**

两条 **Critical** 与十五条 **High** 中，有两条不是「写漏了」而是**机制放错了位置 / 论据取错了组**，改法涉及 D2a 与 D3 的结构，不是补句子能收敛的：

- **C1**：D3 新增的「实现验证」收尾票跑在 `sdflow-implement` 内部，即 code-review 及其 fix 循环**之前**，正面违反一条**本 change 未触碰的既有 Requirement**。
- **H2**：D2a 用来支撑 Group A 升 strong 的核心外部依据，实际是 **Group B 语义**；且其标注的出处 C7 记的锚点与该论据毫无关系。

建议：先就下方 **Q1–Q6** 拍板，按拍板结果修订 design/decision-memo/两份 delta，再进门。

---

## 决策登记区

```
┌──────────────────────────────────────────────────────────────────────┐
│ [自动决策] D1–D6   高置信,附理由,默认接受可覆盖                        │
│ [需拍板]  Q1–Q6   ≥2 方案 / 核验不了的事实 → 人一次性拍                │
│ [已裁掉]  X1–X2   reviewer 原始发现 + 裁掉理由(反静默压制,可审计)      │
└──────────────────────────────────────────────────────────────────────┘
```

### [自动决策]（高置信，默认采纳）

| # | 决策 | 理由 |
|---|---|---|
| **D1** | 全部 findings 不做数值置信过滤 | `spec-review.md` §四点五：设计侧优化**召回**不优化精度，低置信项一行带过、不静默丢 |
| **D2** | 接地镜 24 条全 ✅ ⇒ 记为**正面结论**，不当 finding | 事实核验属实是 Accurate 维度的通过，不是问题 |
| **D3** | Codex Eng voice 的「不应通过设计门」建议 → 采信为收敛口结论 | 与 Claude 侧 High 集群、对抗镜 B 的 H2 独立收敛，非单声 |
| **D4** | 「该拆成 3 个 change」不自动裁 → 转 Q1 | autoplan 规则：两模型均建议改变**用户已定的 scope** ⇒ User Challenge，**永不自动决策** |
| **D5** | lens-metric 的 broad 行把 autoplan 内部 Codex 双声折叠进 `runner="claude"` | emitter fail-closed 拒绝「非 outside-voice 行键 `runner≠host`」；见下方**诚实边界** |
| **D6** | 本轮不修正任何四件套 | 修订属 Step4 `[spec-review-amendment]`，且多数改法依赖 Q1–Q6 的拍板结果 |

### [需拍板]

---

**Q1 —— User Challenge：是否把本 change 拆成 3 个？**

> ⚠️ **两个模型都建议改变你已定的 scope。你的原方向是默认值，除非你明确改口。**

- **你说的**：三个子问题（档位声明 / T10 拆分 / 测试范围分层）同属「sdflow-implement 的审查环节」这一个内聚交付面，一起做。
- **两模型建议**：拆成「宿主/档位解析」「仲裁协议治理」「聚合测试执行点」三个 change。
- **理由**：三者没有共同的可证伪假设，只是都碰到 `sdflow-implement`；当前回滚是整体 revert ⇒ 聚合测试设计失败时无法只撤测试策略而保留档位修复，指标也无法归因。D3 的行为风险量级明显高于 D1/D2（design 自己的 Risks 段体量最长）。
- **我们可能没看到的**：你的既定拆分标准是「一个 change = 一个完整阶段结果，别拆散跨多 change」，且 workflow 循环固定成本高——按这个标准，三者同属一个内聚面、一起做是**符合**你的标准的，Codex 的「回滚粒度」是另一套标准。两套标准都自洽，取舍在你。
- **如果我们判错了，代价是**：白白多付两轮 propose→review→done 循环成本，且三份 change 之间还要互相引用。
- **推荐**：**维持一个 change**（你的原方向），但把 D3 的**风险敞口**在 design 里单独成节，让它的评审带宽可见。
- **三镜**：系统镜——合一则回滚粒度粗、分开则跨 change 引用面增加；用户镜——分开会让「阶段三改造」这件事在 roadmap 上碎成三条；开发循环镜——分开多付两轮固定成本，这是主要代价。**主次：开发循环镜为主。**

---

**Q2 —— 收尾票放在哪？（C1 的修法，≥2 方案）**

现状：收尾票在 `sdflow-implement` 内 ⇒ 其聚合结果被其后的 `sdflow-code-review` 自动修复弄 stale，而这正是既有 Requirement「verify 位于所有修复之后，否则结果 stale」要防的。

| 方案 | 做法 | 代价 |
|---|---|---|
| **A（推荐）** | 保留票在 implement 内做**首轮**聚合，另在 code-review 修复循环**之后**加一个确定性「聚合回归执行门」（可由 `sdflow-done` 之前的一步承担），失败则显式路由回 fix | 系统镜：链路多一步；用户镜：末尾多等一次套件；开发循环镜：需定义该门的证据 schema |
| **B** | 把收尾票整体移到 code-review 之后 | 系统镜：破坏「ticket 只在 implement 阶段产出」的既有边界；开发循环镜：改动面更大 |
| **C** | 维持现状，接受 stale，并显式**修改**那条既有 Requirement | ③ 风险：这是拿现状给目标松绑，且要改一条本 change 声称不碰的 Requirement |

**推荐 A。主次：系统镜为主**——这条既有 Requirement 是阶段三「唯一终门」的地基，不该被绕过。

---

**Q3 —— 功能票的测试禁令要不要留中间档？**

现状 delta 写死「MUST NOT 跑全量 e2e/集成套件」。Codex CEO 指出这是**虚假二选一**：中间策略（受影响模块的集成测试 / 依赖边界测试 / 风险标签触发扩大范围）被一并禁掉了，implementer 会因为「超出票面」而跳过一项便宜且高信号的相关集成测试。

- **推荐**：措辞从「MUST NOT 跑全量 e2e/集成套件」放宽为「MUST NOT 跑**与本票无依赖关系**的集成/e2e；本票 `Blocked-by` 链上的模块集成测试**可跑**」。
- **备选**：维持绝对禁令（更简单、更可机判，但半年后大概率被例外侵蚀）。
- **三镜**：系统镜——放宽后「该跑什么」的判定从机械变判断；用户镜——每票耗时略增；开发循环镜——放宽能让跨票问题早发现，减少末尾聚合的排查成本。**主次：开发循环镜为主。**

---

**Q4 —— `sdflow-done` 自身的裸 `eval` 要不要在本 change 一并修？**

实测：`sdflow-done/SKILL.md:195-197` 的 `### 0.4` 是**裸 `eval` 一行**，没有 unset 清脏 / `[ -x ]` 预检 / 退出码捕获 / eval 后校验——恰是 `sdflow-code-review`/`sdflow-spec-review` 模板里明文警告的 **V1 陷阱**（「裸 `eval` 会被脚本缺失静默吞」）。

这直接影响 D1 的「逐字对齐三个姊妹」怎么落地：**照着 done 抄 = 把已知不安全形态传播成第四份。**

- **推荐**：**本 change 只修「对齐目标」的措辞**（明确对齐 code-review/spec-review 那版四步，done 是既有债务），`sdflow-done` 本体的修复**另记 todo**。理由：通则③不加宽——它不在本 change 声明的范围内。
- **备选（面治）**：一并修 `sdflow-done`。理由：这是同一片一致性面，且第四份拷贝正要生成，此刻修最便宜。
- **三镜**：系统镜——一并修则四份统一、漂移面收敛；用户镜——无感知；开发循环镜——一并修多一处编辑 + 一次回归，但省掉未来单开一个 change。**主次：系统镜为主。此题两个方向都成立，取舍在你。**

---

**Q5 —— 「逐字一致」这个承诺怎么改？**

已被 **5 个独立镜**（Claude Eng / Claude DX / Codex Eng / Codex DX / 对抗镜 A）收敛证伪：三份现存模板本就不一致（done 是裸 eval；code-review 与 spec-review 四步文案相同但内部「本步第 N 项」交叉引用不同，那是**依文件本地结构派生的量，不是可搬运的常量**），而 `sdflow-implement` 目前根本没有编号起手步骤列表。

| 方案 | 做法 |
|---|---|
| **A（推荐）** | 措辞改为「对齐 code-review/spec-review 的四步**语义**；交叉引用改用**具名锚点**（『见预检步』）而非序号」+ **补一条机械 parity 守卫**（仿 `hack/tests/test_async_branch_parity.py`，抽归一化核心段做逐字节比对） |
| **B** | 只改措辞，不加机械守，并在 decision-memo 显式记「接受手工复制、不做第 4 份的机械守，理由是……」 |
| **C** | 抽「共同算法契约」到 bundle 单一源，各 skill 只留上下文相关的失败边界 |

**推荐 A。** 依据：本仓对**同类问题已有先例要机械守**（`test_async_branch_parity.py` 的理由原文即「复制是必要的，但复制不能靠手」），而 tasks 5.1–5.4 无一条核验模板一致性。C 是更彻底的解，但属加宽（通则③）。
**三镜**：系统镜——A 把第 4 份拷贝的漂移风险机械封住；用户镜——无感知；开发循环镜——A 多写一个测试，一次性成本。**主次：系统镜为主。**

---

**Q6 —— 事实核验不了：「聚合测试套件」在任意下游仓怎么确定？**

这是本轮唯一一条**我们查不出答案、只能由你定**的事实缺口：`sdflow-implement` 是要铺给**任意**下游项目的，而「单元+集成+e2e 聚合套件」的发现方式没有契约——命令从哪取（Makefile target？package.json script？config 键？）、**没有集成层或 e2e 层的仓怎么办**、flaky 怎么判、退出码与日志怎么落成可机验锚点。

⚠️ 这一条与 `openspec/rules/` 的**基准 5**（无界语法面 MUST NOT 手搓，让工具自己回答）直接相关：如果打算「解析 Makefile 找 target」，那正是 `add-sdflow-devenv` 已经付过学费的路（脚本 562→119 行、7 个 fail-closed 罢工分支）。

- **推荐**：**复用 `sdflow-devenv` 的既有答案**——「target 能不能跑」由**真跑一遍**让工具自己判，缺层则该层记「未覆盖」而非罢工；并给收尾票定一个确定性证据 schema（命令原文 + 退出码 + 测试时 SHA）。
- **风险（默认处理）**：若不定契约，模型会生成一张**文字正确但执行范围错误**的票，而现有三道 gate（fence/标题/重号）与三条 Success Metrics 全部放行。
- **三镜**：系统镜——定契约要新增一点机械层（与「本次不改脚本」的声明冲突，需你确认是否放宽）；用户镜——缺层仓不再罢工；开发循环镜——一次性定义，长期省。**主次：系统镜为主。**

### [已裁掉]（反静默压制：原始发现 + 裁掉理由，供你复核「裁得对不对」）

| # | 原始发现（来源） | 裁掉理由 |
|---|---|---|
| **X1** | 「model-tier 的收益前提没有成立；证据只有『不一致』，没有因果收益。方案反而新增一个 fail-hard 依赖，可用性成本确定、质量收益无基线」（Codex CEO #4，high） | **驳回结论，采纳半个论据。** 真正硬的理由不是架构对称，而是**跨宿主正确性**：`sdflow-implement` 无第零步 ⇒ Codex 宿主下拿不到本机队档位，而 `model-tiers` Requirement 明写「MUST NOT 在 Codex 宿主下把 Claude 机队的模型名用于 Codex 机队子代理」。这是正确性缺陷，不是「为一致性而一致性」。⇒ 「该做」成立；但 decision-memo D1 的**论证**确需补这条（已落 L7） |
| **X2** | 「Group B 的①档（有客观判据自动选）应当删除——触发前提已是『连续 2 轮不消解』，能客观判定的话第 1 轮就修好了」（对抗镜 B F2 的强版本，medium） | **降级为建议，不采纳删除。** ①档保留成本近零（一句话），删掉反而制造「两组处置不对称」的新维护面（通则④：不为低概率小影响纠结）。⇒ 改为「design 补一句『Group B 的①档预期极少触发，原因是……』」，已落 M19 |

---

## Findings 明细

> 置信度全部经**主 session 对抗裁决**；标 ✅ 的表示我**亲自复核过原文/跑过命令**。低置信项一行带过、不静默丢（escalate-not-drop）。

### Critical

**C1 · 聚合验证票的位置违反一条本 change 未触碰的既有 Requirement** ✅
`openspec/specs/spec-workflow/spec.md` 有 Requirement「verify 为收尾最终门，位于所有修复之后」——原文「`sdflow-done` 的 verify MUST 在本 change 全部修复之后运行……**SHALL NOT 前移进 sdflow-code-review（否则修复后 verify 结果 stale）**」。而 D3 的收尾票跑在 `sdflow-implement` 内，即 code-review 及其 fix 循环**之前**；`sdflow-code-review` 随后会自动修改并提交源码（`sdflow-code-review/SKILL.md:282,306`）且**不重跑聚合套件**；`sdflow-done` 的 verify 又只 Grep/Read 证据、不执行测试（`sdflow-done/SKILL.md:213`）。⇒ 终门引用的聚合锚点必然 stale。
来源：Codex Eng voice #1。置信度 **高**。→ **Q2**

**C2 · 聚合回归只覆盖非默认 tickets 轨，而 verify 锚点是无条件的** ✅
canonical 缺省是 `writing-plans → subagent-dev`（`spec-workflow/spec.md:83`「缺省/非法值一律 superpowers」），收尾票只由 `sdflow-implement` 出票模式产出。而 tasks 4.4 要 `sdflow-done/SKILL.md` 无条件补「verify 引用该收尾票 commit/报告作为聚合覆盖证据锚」⇒ **默认轨的仓既没有聚合回归、又会被这条锚判出假 gap**。这是把非默认管线的证据契约泄漏进了两轨共用的终门。（本仓 `openspec/config.yaml:64` 是 `impl-pipeline: tickets`，所以源仓自测照不到这个洞——典型的 dogfood 盲区。）
来源：Codex CEO voice #1 + Codex DX voice。置信度 **高**。建议：给该 verify 锚加管线条件化语义。

### High

| # | 发现 | 来源 | 置信 |
|---|---|---|---|
| **H1** | 「第零步模板与三个姊妹 skill 逐字一致」**不成立**：`sdflow-done:195-197` 是裸 `eval`（无四步防护，且是模板自己警告的 V1 陷阱）；code-review 与 spec-review 四步文案相同但内部「本步第 N 项」交叉引用不同（依文件本地结构派生）；`sdflow-implement` 无编号起手步骤列表 ⇒ 照抄会产出悬空引用 ✅ | Claude Eng·Claude DX·Codex Eng·Codex DX·对抗A **五镜收敛** | 高 |
| **H2** | **D2a 的核心外部依据实为 Group B 语义，且引用的出处对不上** ✅：decision-memo D2a 用「superpowers 的 fix-loop 在第 4–5 轮换更强模型」支撑 Group A 升 strong，但该原文（`superpowers/6.2.0/subagent-driven-development/SKILL.md:174-175,328-333`）讲的是**同一 task 反复修不好换模型**＝本 change 自己定义的 Group B；而 D2a 标注「见 C7」，C7 记的锚是 `:230`「Never dispatch multiple implementation subagents in parallel」+`:258-259`「Per-task reviews are task-scoped gates」，**与该论据无关**。真正该引用它的 D2b 反而没提 | 对抗镜 B | 高 |
| **H3** | 熔断的身份键是「**同 file:line** + 同问题」，而修复几乎必然移动行号 ⇒ 同一未解决问题被认成新 finding、轮次计数清零，`MUST NOT 无限循环` 兑现不了 | design-voice（跨模型） | 高 |
| **H4** | 熔断仲裁复核的是「finding 是否成立」，但触发它的原因是「**成立但连续修不掉**」；确认成立后既无新修复动作、也无互斥终态 ⇒ 可绕回原循环 | design-voice（跨模型） | 高 |
| **H5** | Migration Plan 的**部署渠道写错** ✅：改动行为在 `sdflow-implement/SKILL.md`（skill，靠 `setup.sh` 分发：Unix symlink / Windows copy），而 `design.md:76-77` 写「跑 `sdflow-init update` 后生效」——`sdflow-init update` 只刷 workflow bundle、明确不装 hack 脚本。新第零步一旦 fail-hard 依赖 `resolve-models.sh`，单跑 update 会造成「新指令 + 缺 helper」skew | Codex Eng + Codex DX **跨模型双命中** | 高 |
| **H6** | **delta 没忠实保留被替换 Requirement 的 untouched 语义** ✅：主 spec `impl-orchestration/spec.md:60` 是「盘面无答案时按 **T10** 处理（defer 或停）」，delta 第 31 行改成了「按 defer 或停处理」——T10 被静默删除；而 `design.md:48` 明确把这一行列在【不动】、tasks 5.1 要求核对「未被误改」。MODIFIED Requirement 归档是整段替换，不是无害省略 | Codex Eng | 高 |
| **H7** | 「本 change 的聚合测试套件（单元+集成+e2e）」**无确定性定义**：命令从哪取、哪些仓缺层、覆盖哪些 workspace、flaky/环境故障怎么处理、退出码与日志怎么落锚，全无契约；而本 change 明确不改脚本，gate 只验 fence/标题/重号 ⇒ 一张「文字正确、执行范围错误」的票可全门通过 | Codex CEO·Codex DX·Codex Eng | 高 |
| **H8** | 三项 Success Metrics **全是文本存在性检查**（grep 到变量 / 若干落点措辞一致 / plan 含收尾票），三个战略前提一个都验不了；三项改动零收益也能全绿 | Codex CEO + Codex DX | 高 |
| **H9** | 「实现验证票」与普通票**执行契约不兼容**：普通票强制 red-before-green 逐 slice 实现，而聚合套件一次绿则**无 red、无 diff**，agent 不知该直接 DONE / 造空提交 / 只提报告；且 `checkpoint-commit.sh` 在干净树上**直接成功退出、不建 commit** ⇒ 「引用该票自身 commit」可能根本没有 commit。失败时也未区分 change regression / 历史红测 / flaky / 环境故障，Standards 轴只禁「删除或弱化断言」，挡不住加 skip、改测试配置 | Codex DX·Codex Eng·Codex CEO | 高 |
| **H10** | **档位解析状态机自相矛盾** ✅：delta `:5` 允许 `host=unknown` 时三档为空，失败 Scenario `:14` 却对「`$SDFLOW_HOST` 非空但三档任一为空」硬停且未排除 unknown ⇒ 合法的 unknown 态被判硬停。更深：`unknown` 对本 skill 的语义**根本没定义**——code-review 的处置是「不 fan-out」，但 `sdflow-implement` 不 fan-out 就跑不了任何 ticket | Codex DX | 高 |
| **H11** | **Codex 子代理授权未覆盖 `sdflow-implement`** ✅：`AGENTS.md`/`CLAUDE.md` 的授权明文「**仅限**`sdflow-spec-review`/`sdflow-code-review` 两处」，且 `sdflow-init/tests/test_codex_subagent_authorization.py` 机械断言这一点。新第零步把 Codex 宿主变成字面上被支持的路径（会 eval 出 Codex 机队 `$SDFLOW_TIER_MID`），但四类 dispatch 不在授权内；`sdflow-implement` 也没有 code-review 那样的能力探针与单镜降级契约。四件套通篇未提，Non-Goals 也没列 | Claude DX + Codex Eng **跨模型双命中** | 高 |
| **H12** | 「最后一票」**无拓扑/gate 机械保证**：`frontier` 只服从显式 `Blocked-by`、不理解「验证票必须最后」；`ship_gate` 不检查验证票的唯一性/位置/全依赖。且 expand–contract 的迁移批次是否算「全部功能 ticket」未定义 ⇒ 验证票可能提前执行 | Codex Eng + Claude Eng | 高 |
| **H13** | **「拆标签防未来漏改」与「不做单一源」因果矛盾**：造成 C8「差异 B 丢字」的根因是**复述架构本身**（手抄进多文件、无 lint 兜底），不是「两种语义共用一个标签」。拆分只消除了「跨语义误改」，「同语义多落点漏改」原样保留——而 Group A 重新盘点后落点数**不降反升**，人工核对负担更重。proposal 的措辞把两件事混为一谈 | 对抗镜 B + Codex CEO | 高 |
| **H14** | **tasks 内部执行序互踩**：1.1 要在 `sdflow-implement/SKILL.md` 靠前处**新增**一整段第零步，而 2.6（203,271）/2.7（282,545）/3.1（490-493）写死的绝对行号全在其后 ⇒ 顺序执行会整体下移、按行号定位读到错位内容。5.1 的 grep 兜底发生在全部编辑之后，过程期的误判有实际返工成本 | 对抗镜 A | 中高 |
| **H15** | **ADR 判定不一致**：`adr/0031` 是本 change 为 D2b 开的，但 D1/D3 同样满足其引用的三条判据（难逆转 / 缺上下文意外 / 有真实权衡）却都没开 ADR、也没记一句「为何判定不需要」。而同批 todo（T247）恰恰自曝这个「该不该开 ADR」的钩子会静默漏判 | Claude CEO | 中高 |

### Medium

| # | 发现 | 来源 |
|---|---|---|
| M1 | Group A 清单**非穷尽** ✅：漏 `sdflow-init/assets/workflow/ff-generation-constraints.md:68`（「切片粒度争议走既有 T10」＝Group A 语义）与 `docs/workflow-overview.md:257`（人读的**并列定义**，非指针，②步仍未声明 strong） | Claude Eng + Codex Eng + 主审复核 |
| M2 | T10 落点计数**五种口径** ✅：proposal Why「其余 4 处」/ design「6 个引用落点、其余 5 处」/ Success Metrics「6 个落点、其余 4 处」/ 设计图「9 处落点」/ 已落盘的 `adr/0031:5`「等 5 处」。根因是「落点」按文件、Requirement、语义规则还是字符串 occurrence 计数从未定义 | Codex CEO + Codex DX + 主审复核 |
| M3 | **修漂移的同时新造漂移**：impl delta 两次展开三级协议（`:59`）都**漏了** canonical 的「按三镜+主次」，而 spec-workflow delta（`:5`）带了 | Codex Eng |
| M4 | design 的 T10 scope-check 表**漏了本 change 自己产出的两个落点**：`openspec/CONTEXT.md:299`（T10 术语澄清）与 `openspec/adr/0031`（commit `c4ea1b1`）——它们讨论的正是 T10 议题，却既不在 Group A/B 也不在【不动】；proposal Impact 同样没列。BASE-29 原文警告的正是「未列入比未完成更危险」 | 领域镜 |
| M5 | proposal Impact 与 design 回滚清单**都漏了 `sdflow-done/SKILL.md`**（tasks 4.4 实际要改它） | Claude CEO + Claude Eng |
| M6 | 「实现验证」票**缺 R-ID 归属**，与 Spec 轴「对照 R-ID 溯源需求逐条核验」的裁决依据冲突（填空？`all`？`N/A`？） | Claude Eng |
| M7 | 「本票声明的 e2e 场景」在 ticket 骨架里**没有对应字段**（骨架只有 `Blocked-by:`/`R-ID:`/行为描述/验收标准复选框），两种合理解读（复选框即 e2e 场景 vs 本票未声明 e2e ⇒ 只跑单元）产生实质不同的测试覆盖 | Claude DX |
| M8 | 第零步在「一文件两入口」（`tickets-plan` / `tickets-exec`）的 `sdflow-implement` 里的**插入位置与适用范围未定义**，三个姊妹 skill 无此结构、无先例可抄 | Claude DX + Claude Eng |
| M9 | fail-loud 的 `problem+cause+fix` **文案留给现场发明**；至少 7 类失败分支（resolver 不存在 / 不可执行 / 非零退出 / 输出无法 eval / host 非法 / host 空 / tier 缺失 / unknown）未区分；也未说明是否复用 `sdflow-implement` 既有的五要素 halt envelope（该格式有 ticket 号字段，而起手失败无票上下文） | Codex DX + Claude DX |
| M10 | **T10 运行时无消歧 aid**：Group A/B 对照表只活在本 change 的 design 里；执行 agent 读真实 skill 时看到的仍是裸 `T10`，也没有 `T10-choice`/`review-loop-breaker` 这类稳定规则名或 glossary | Codex DX + Claude DX |
| M11 | `impl-orchestration/spec.md:60` 与 `sdflow-implement/SKILL.md:372` 是**第三类场景**（问题问出来了但盘面查不到答案，天然跳过①②直取③）。按 `CONTEXT.md:299` 刚写的术语澄清（T10「只对『阶段三遇 ≥2 方案自动选』成立」），这两处就不该继续贴 T10——**D2b 的判据被选择性应用** | 对抗镜 B + Claude DX |
| M12 | `sdflow-ship/SKILL.md:165` 的「取值经各被链序调度的子 skill（**spec-review/code-review/done**）各自 eval」枚举，改完即陈旧——正是本 change 要消灭的不对称，却在文字层留了一处「三个」 | Claude Eng |
| M13 | proposal **无 P0/P1/P2 优先级标注**（BASE-23，TG-19 激活）：What Changes 有 4 条重量级明显不同的需求（①③是行为性变更，④只是补一句清单），全仓 grep `P0\|P1\|P2\|优先级` 零命中 | 领域镜 |
| M14 | tasks 1.2/1.3/1.4 用「**改为**引用 `$SDFLOW_TIER_MID`」措辞，但文件里**没有任何可替换的内联模型名或「派发 Agent（model: …）」调用模板**（三处 dispatch 全是纯 prose 清单）；且 1.4 的 fix 子代理**没有独立 dispatch 段** ⇒ 是复用 1.2 的编辑点（那 1.2/1.4 重复计数？）还是另新增一句，只能猜 | 对抗镜 A |
| M15 | D2a 把出票阶段的粒度争议/矛盾裁决纳入 T10，但 T10 要求「复核记录写进报告」，而**出票模式没有报告产物**（唯一明确落点是尚未生成的 `code-review-report.md`）⇒ strong 仲裁结果无审计落点 | design-voice（跨模型） |
| M16 | strong 仲裁的依据**外推过度**：类比对象是「fix-loop 到第 4–5 轮才换强模型」，本设计却把 strong 扩到**任何**「≥2 合理方案且无客观判据」的**首次**选择（含出票粒度、ticket 语义矛盾、outside-voice tension）。「低频高杠杆」只是声明，实际落点从最初统计持续膨胀（与 H2 同源、不同角度） | Codex CEO |
| M17 | 在途迁移把「必须关闭的结构性缺口」降成了「**若需要**，手动补一张」，与「**强制**收尾 ticket」自相矛盾，且无 grandfather policy、无「谁负责识别、何时必须补」 | Codex CEO + Codex DX |
| M18 | 两组语义已判定「本质不同」，**处置形状却逐字相同**（①②③三级）；design 从未单独论证 Group B 是否需要①档。历史语料实证：40 余份归档 change 里只找到 **1 次**真实②档仲裁记录（`archive/2026-07-07-mlh-p5-gate-frontmatter/code-review-report.md:43`），且那次是 **Group A** 语义 | 对抗镜 B |
| M19 | C8 声称「grep 命中均为巧合时间戳或 fixture 文本」被**证伪** ✅：`sdflow-done/scripts/roadmap_writeback_draft.py:88` 是真实**生产代码注释**引用一次历史 T10 裁决。不影响「无机械依赖」的核心结论（该注释不解析字符串，脱钩仍零成本），但直接证伪该验证性声明的措辞 | 对抗镜 B + 主审 grep |

### Low（一行带过，可审计不静默丢）

- **L1** 「不计入 3–6 预算」正在掏空票数约束（已有 expand–contract 迁移批次 + 收尾票**两个后门**）；建议改为约束总执行单元或总 frontier 成本。〔Codex CEO，**defer**〕
- **L2** 验证票的修复工作量 ex-ante 不可控，design 未把既有「plan 结构不可变、只能追加新号」这条逃生阀显式接上。〔Claude CEO〕
- **L3** `sdflow-implement/SKILL.md` frontmatter description 仍写「产出 3-6 张……落盘即返回」，未同步新增的强制收尾票。〔Claude Eng〕
- **L4** 建议补 golden fixture 钉住新票形状（`test_tickets_plan_golden.py` 现为 3 票、未覆盖「末尾一张 Blocked-by 全部前置票」）。〔Claude Eng，**defer**〕
- **L5** 纯 expand–contract 类 change（0 张垂直切片）下「Blocked-by 全部功能票」语义不明。〔Claude Eng，**defer**〕
- **L6** `adr/0031` 承诺的「T10 单一源化留待独立立项」未落成任何 todolist 条目——而该类漂移**已真实发生过一次**。〔Claude CEO〕
- **L7** decision-memo D1 的收益论证只讲架构对称，未用更硬的**跨宿主正确性**做主论据（见 X1）。〔Claude CEO〕
- **L8** `decision-memo.md:13`「目标态」段仍写「把全量聚合回归**挪成 `sdflow-done` verify 新增的一类证据锚点**」，与 D3/C9 修正后的结论（放进收尾票、verify 不扩张职责）矛盾；「三镜代价」段（`:45,:47`）也仍是修正前的口径。〔**主审自查，无镜命中**——故未计入 lens-metric〕
- **L9** 出票模式（不派子代理）是否也无条件跑第零步未讲清；无条件跑等于一个不消费其结果的空转步。〔Claude Eng，**defer**〕

### 正面结论（不是 finding，是通过项）

- **接地镜 24 条全部 ✅ 属实、零偏差**：decision-memo 的 C1–C9 证据锚全真（含 superpowers 6.2.0 的两句逐字引文）、设计图 9 处 T10 行号锚全准、「不改脚本」声称成立、tasks 5.2 的「当前零命中」属实。**这份设计的考据底子是硬的，问题全在机制设计层。**
- **机械层通用支持新增票**：`parse_blocked_by` 已由 `test_parse_diamond` 覆盖多依赖形态；`ship_gate` 三道校验不设票数上下界、无 3/6 硬编码 ⇒ 新增票不会绊倒 gate/frontier（但也**不会**保障 H12 所说的特殊语义）。
- **ADR-9「每轮恰好一次」未被违反**：ship 自身从不 resolve，各下游步各自解析一次是既有一致模式；且 harness 每次 Bash 调用是独立 shell，下游必须各自 eval。
- **C8 差异 B 经独立复核属实**：`spec-workflow/spec.md:83`/`:93` 确实缺「按三镜+主次」，`:638` 与 `workflow.md:106` 带；delta 的修复准确。
- **未找到「strong 升档明显不划算」的反例**（对抗镜 B 如实报告）：②档历史触发频率极低 ⇒ 边际成本近零；但**收益侧同样缺乏实证**（无任何历史记录显示 mid 档在②档场景做出过错误裁决）。这是一个成本低、收益未证的低风险平局决策。

---

## 度量锚（lens-metric）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="9" 采纳="8" 裁掉="1" defer="0" 独立="5" sev="致0/高4/中3/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="37" 采纳="30" 裁掉="1" defer="6" 独立="27" sev="致2/高11/中13/低4" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="2" sev="致0/高0/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="3" sev="致0/高2/中1/低0" -->

### 诚实边界（MUST 显著登记）

1. **broad 行低估了跨模型贡献**〔D5〕：autoplan 的三个 **Codex** voice（CEO/Eng/DX）贡献了两条 Critical 里的两条、以及 High 里的大多数，但 `lens_metric_emit.py` **fail-closed 拒绝**「非 outside-voice 行键 `runner ≠ --host`」，契约的行键模型无法表达「broad 层内部含跨模型双声」⇒ 它们被折叠进 `broad/runner="claude"` 行。**该行的 `runner` 值不反映实际执行机队。** 建议记 todo 改进 lens-metric 契约。
2. **数值一致性是主 session 信任边界**：`findings=N` 与合并池实收数、分类正确性（某条该归哪个 lens）、roster 完备性、findings JSON 誊写准确，均非机械可验——`anchor_lint` 只核锚行文法自洽。
3. **`subagents="available"` 由主 session 自报**：host=claude 免探针，锚行的一致性 lint 只核文法自洽，核不了它对应一次真 spawn。
4. **L8 未计入 lens-metric**：它由主 session 自查发现，无镜命中，而 roster 不含「主 session」行键。
5. **autoplan 的台账侧产物未执行**：TODOS.md 自动写入、`gstack-review-log`/`gstack-question-log` 落盘、Implementation Tasks JSONL 聚合器均未跑——不在 `/sdflow-spec-review` 的产出契约内。
6. **偏离声明**：Codex DX voice 只拿到 CEO 相共识、未拿到 Eng 相共识（两者并行派出以省墙钟）。实测其独立挖出两条无人重复的高价值 finding，未见该偏离造成损失。

### 反馈回路免责

本 skill **只落锚**，不做聚合、不做复评判断、不主动 surfacing。跨 change 的锚聚合、按采纳率+独立率复评、「出现轮数≥10」的显著提示，一律由 `/sdflow-retro` 承担；是否保留/降采样/收紧触发/淘汰某镜一律人决。

---

## 图的验证（`design-diagrams.md` §五：只验存在/正确/未过时，不重画）

| 图 | 触发 | 状态 |
|---|---|---|
| T10 标签拆分前后对照（design.md:33-48） | TG-25（契约文档套件变更） | ⚠️ **不完整** —— 漏 `ff-generation-constraints.md:68`、`docs/workflow-overview.md:257`（M1）与本 change 自产的 `CONTEXT.md:299`/`adr/0031`（M4）；标题「9 处落点」与其它四处计数口径不一致（M2）。行号本身**经接地镜逐个核验全准** |
| 出票模式 frontier 依赖图（design.md:51-62） | TG-19 | ⚠️ **与目标态不符** —— 图把 `sdflow-done verify` 直接画在收尾票之后，省略了中间的 `sdflow-code-review` 及其自动修复循环，正是 C1 所指的失鲜路径被图**掩盖**了 |

---

## 下一步

1. 就 **Q1–Q6** 拍板（设计 HARD-GATE，阶段二唯一人类门）。
2. 按拍板结果修订 `proposal.md` / `design.md` / `decision-memo.md` / 两份 delta spec，改动处标 `[spec-review-amendment]`。
3. 拍板后由主 session 立即把 `ship-gate.design_approved` + `reviewed_sha` 写入本文件**头部 frontmatter**（同一次写入），并把 lens-metric 锚按门后最终裁决重算。
   🔴 若拍板前四件套相对镜子审过的提交（`50d5a48`）有实质改动，MUST 先跑一次**窄复核**（只审增量）、再**单独 checkpoint 提交**该修订、取得其 sha，然后才回写锚——否则第一次跑 gate 就会判 design 失鲜 `REFUSE_START`。
