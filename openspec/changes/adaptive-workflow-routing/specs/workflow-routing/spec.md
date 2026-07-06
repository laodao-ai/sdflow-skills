# Spec Delta — workflow-routing

## ADDED Requirements

### Requirement: 路由地板由 HR-TG 双向化界定

编排深度的**硬地板** SHALL 由 `trigger-catalog.md §7` 的 HR-TG 子集（单一源）界定，语义为**双向**：命中任一 HR-TG 成员 → 该 change 判定为**非平凡**、强制全深度（FULL）编排，MUST NOT 轻量化；HR-TG 命中集为空（∅）→ 该 change 通过 P1 地板，**续判其余谓词**（P2/P3/P4，均脚本机判）以决定是否放行轻量化。命中判定 MUST 由确定性脚本按 change 的文件/路径/内容对 HR-TG 判定（机械活交脚本），MUST NOT 依作者自评。**路由器无模型判断层**——四谓词全脚本机判，需语义判断的残留（先例是否真同类/需求是否真无歧义）MUST NOT 由路由器自评、归 grill（人）承接。HR-TG 子集 SHALL 新增成员 **TG-27（评审机制 / gate 契约 / workflow bundle 自身变更）**——入选依据同 §7 判据（做错静默放过坏活且难回退）。

#### Scenario: 命中 HR-TG 强制 FULL 不可轻量化
- **WHEN** 某 change 的 diff 命中任一 HR-TG 成员（如改 `ship_gate.py` 命中 TG-27，或 DB 迁移命中 TG-04）
- **THEN** 路由 SHALL 判定非平凡、强制 FULL，MUST NOT 续判其余谓词以放行，MUST NOT 放行任何阶段轻量化

#### Scenario: HR-TG 空集才续判其余谓词
- **WHEN** 某 change 的 diff 不命中任何 HR-TG 成员
- **THEN** 路由 SHALL 续判其余谓词（P2/P3/P4 脚本机判），据结果决定是否放行轻量化

#### Scenario: 改 gate/bundle 自身命中 TG-27
- **WHEN** 某 change 改动 `sdflow-init/assets/workflow/` bundle 规则、`ship_gate.py`、或评审机制自身
- **THEN** 脚本 SHALL 判其命中 TG-27（∈ HR-TG）→ 强制 FULL，MUST NOT 因不命中产品码类 HR-TG（TG-04/06/07/08/09/16/17/26）而误判平凡

### Requirement: 非平凡由四谓词硬定义，任一成立即非平凡

「非平凡」SHALL 由**四条谓词**界定（沿复杂度/清晰度两轴），**任一成立即非平凡**；四条全不触发才「平凡」。HR-TG 只当其一（必要非充分）：

- **P1 命中 HR-TG**（复杂度轴，脚本判）：change 的 path/content 命中 HR-TG 子集（含 TG-27）任一成员。
- **P2 面超阈**（复杂度轴，脚本判，结构信号为主）：跨 ≥2 顶层模块 **∨** 含 `specs/` delta（改公共契约）**∨** 新增文件 / 新 codepath（非仅改既有行）**∨** 净改动行 > **100**（仅作兜底 backstop，防单文件巨改）。
- **P3 有开放决策**（清晰度轴，脚本 grep）：产物含显式 OQ / 决策登记条目 **∨** ≥2 方案未闭分叉（TG-23）**∨** proposal Open Questions 非空。
- **P4 非 known-pattern**（清晰度轴）：`known-pattern` 由**双来源**任一成立——①匹配 bundle 内「通用平凡形状白名单」（脚本判、项目无关、单一源，扩容即命中 TG-27 走 FULL）；②指名一个**可核归档先例** change ID（设计门核其存在 ∧ 触同 capability/模块）。两者皆不满足 → 非 known-pattern → 非平凡。**白名单初始三条形状**：`diff 仅动注释 / markdown 文档行` · `diff 仅新增 tests/ 下文件` · `diff 仅改版本常量`。

**冷启动姿态**：新项目空 archive → 先例来源（②）暂无 → 仅白名单（①）形状可 day-1 轻量化，其余保守判非平凡（正确：尚无 known 模式），随 archive 累积每类首次付 FULL 后暖机。此姿态与后向校准（`workflow-metrics`）冷启动共用同一暖机曲线。

#### Scenario: 单文件微妙算法 HR-TG∅ 仍判非平凡
- **WHEN** 某 change 单文件、HR-TG∅、面小，但为新算法逻辑、archive 无先例、不匹配白名单形状
- **THEN** 路由 SHALL 由 P4（非 known-pattern）判其非平凡 → FULL，MUST NOT 因 HR-TG∅ 且面小而误判平凡

#### Scenario: 新项目 typo 修改经白名单形状轻量化
- **WHEN** 全新项目（空 archive）某 change 的 diff 仅动注释/文档行
- **THEN** P4 SHALL 经「通用平凡形状白名单」判其 known-pattern（无需先例），四谓词全不触发 → 可轻量化

#### Scenario: 声称 known-pattern 但指不出可核先例
- **WHEN** 某 change 平凡声明称 known-pattern，但既不匹配白名单形状、又指不出存在且触同 capability 的归档先例
- **THEN** 设计门 SHALL 判 P4 触发（非 known-pattern）→ 非平凡，MUST NOT 采信无可核依据的 known-pattern 自证

### Requirement: 平凡声明显式且门核对齐脚本硬信号

判「平凡」MUST 在 ff 产物写一行**显式平凡声明**，指明四谓词各自不触发的依据（P4 若走先例来源 MUST 指名先例 change ID）。设计门 SHALL 核对声明与脚本 L0/L1 硬信号：**声明平凡但脚本算出任一谓词触发（HR-TG 命中 / 面超阈 / 有开放决策 / 指不出先例且非白名单形状）MUST 拒**（当场穿帮），MUST NOT 放过声明与硬信号矛盾的 change。

#### Scenario: 平凡声明缺失则不放行轻量化
- **WHEN** 某 change 未在 ff 产物写平凡声明即尝试走轻量化路径
- **THEN** 设计门 SHALL 拒绝轻量化、要求补声明或走 FULL，MUST NOT 静默放行

#### Scenario: 声明与脚本硬信号矛盾当场穿帮
- **WHEN** ff 产物声明「平凡·HR-TG∅」但脚本 L0/L1 算出该 change 命中某 HR-TG 成员或面超阈
- **THEN** 设计门 SHALL 判矛盾并拒绝（REFUSE），点名冲突谓词，MUST NOT 采信自评声明覆盖脚本硬信号

### Requirement: 编排深度按阶段路由信号自适应

各阶段 SHALL 按其路由信号独立判深度——**可自动轻量化集 = { spec-review, superpowers }**：spec-review 按复杂度（命中 HR-TG 或面超阈→FULL；否则可 autoplan-lite/单遍自查）；superpowers 按机械 vs 新逻辑（机械→inline TDD 不 fan-out）。**三个阶段不属可自动轻量化集**：①**grill**——路由器 MUST NOT 代跳，至多经推荐器**建议+征询用户**（承 `grill-not-skippable` 与 adr/0004「本性不可折叠」）；本能力 MUST NOT 把「何时可跳 grill」定成规则（T19 独立评估，勿预设结论）。②**code-review**——两层深度见 spec-workflow「sdflow-code-review 强制主审，两层深度按逻辑面自适应」：Step1 恒跑、Step2 仅对白名单机判无逻辑面形状免。③**done**——收尾门恒跑不放松。

#### Scenario: 清晰平凡 change 建议跳 grill 但只征询不自动跳
- **WHEN** 某 change HR-TG∅ ∧ 决策登记区空 ∧ 有 archive 先例 ∧ 需求无歧义
- **THEN** 阶段推荐器 SHALL 以**独立选择块**（动作之前、给真实否决窗口）建议跳 grill 并附依据，MUST NOT 由机器自动跳过 grill，MUST NOT 把建议埋进长报告

#### Scenario: grill 跳过决策权归用户
- **WHEN** 路由判定某 change 平凡且推荐跳 grill
- **THEN** 是否真跳 grill SHALL 由用户下一步动作决定（征询），MUST NOT 由路由器或编排器代为执行跳过

#### Scenario: done 阶段不因路由放松
- **WHEN** 任何 change（含判定平凡者）走到收尾
- **THEN** sdflow-done 收尾门 SHALL 恒跑（verify/archive/commit/merge 不 SKIP），MUST NOT 因平凡判定跳过收尾门

### Requirement: 路由器为单一源脚本，三层归口调用

路由器/推荐器 SHALL 落为**独立脚本**（`workflow/tools/route.py`，唯一真相源：四谓词机判 + 输出下一步推荐 + 可复制 prompt），谁调用都渲染同一份。调用**三层归口**：①自有编排 skill（`sdflow-spec-review`/`sdflow-ship`/`sdflow-code-review`/`sdflow-done`）入口 Step0 调；②ff→grill 边界经 `sdflow-init` 托管块（CLAUDE.md/AGENTS.md）加一行「ff 后 MUST 跑 route.py」驱动——MUST NOT 改 `opsx:ff` 等非本仓 skill；③workflow.md 阶段表人读兜底。推荐 MUST 标注「可人工覆盖」，MUST NOT 表述为强制路径。**边界诚实**：托管块驱动为 best-effort（非硬 hook），漏跑时**硬门在设计门**（平凡声明 vs 脚本硬信号）兜底。

#### Scenario: 自有 orchestrator 入口自评
- **WHEN** 用户调用 `sdflow-spec-review`
- **THEN** 其入口 Step0 SHALL 调 `route.py`；若判 LIGHT 则输出「本 change 可轻量化 + 依据 + 可复制 prompt」，MUST NOT 表述为强制

#### Scenario: ff→grill 边界经托管块驱动而非改 ff skill
- **WHEN** agent 完成 `opsx:ff` 产物生成
- **THEN** SHALL 依 `sdflow-init` 托管块指令跑 `route.py` 得路由推荐（含 grill 是否可跳并征询），MUST NOT 修改 `opsx:ff`/`grill-with-docs` 等非本仓 skill 本体

#### Scenario: ff 推荐漏跑仍被设计门兜底
- **WHEN** ff 后 route.py 未被跑（best-effort 漏）、一个实际非平凡的 change 试图轻量化
- **THEN** 设计门 SHALL 凭平凡声明 vs 脚本硬信号判矛盾并拒，MUST NOT 因 ff 推荐缺失而放过误路由

### Requirement: 后向校准消费路由度量调整地板与判据

路由的**后向校准** SHALL 消费 `workflow-metrics` 的路由决策度量（LIGHT 路由事后有 buglist 回指 = 判松；FULL 路由各镜零产出 = 判紧），据累积数据供人调整 HR-TG 边界 / 谓词判据。校准 MUST **供数不供裁决**（承 workflow-metrics 同名需求）——MUST NOT 依数据自动改路由地板或自动砍阶段，调整由人决。

#### Scenario: LIGHT 逃逸被校准回指
- **WHEN** 某类被判平凡走 LIGHT 的 change 事后在 buglist 有回指该 change 的缺陷
- **THEN** 校准 SHALL 显著呈现该类为「判松候选」供人评估是否纳入 HR-TG，MUST NOT 自动改地板
