# 收尾票承担聚合回归执行点（实现期聚合门，非最终完整性门）

> 状态：**Accepted**（2026-07-28，`harden-implement-review-loop` 拷问阶段收敛，用户拍板 Q2/Q3/Q6）· 关联 change：`harden-implement-review-loop`

## Context

`sdflow-implement` 每 feature ticket 原契约是"结束前跑一次全套件"——不分粒度、对每票无差别付全套件成本。与此同时，链路里（`sdflow-implement` → `sdflow-code-review` → `sdflow-done`）**没有任何一步执行"全部票完成后的聚合回归"**（`decision-memo.md` C3 实证）：每票的测试范围收窄之后，这个空洞更需要补上，否则"每票都局部绿"不等于"合起来仍然绿"。

评审 C1 进一步指出：即便补上聚合回归执行点，若该执行点落在 `sdflow-code-review`（会自动修改并提交源码，但不重跑聚合套件）**之前**，其证据锚相对最终代码就不是最新的。这条残余风险必须被显式承认、而不是掩盖。

## Decision

**新增一张不计入 3–6 张预算的强制「实现验证」收尾 ticket**，由出票模式在全部功能垂直切片之后恒产出：

- `Blocked-by` = 全部其余 ticket 号（逐一列全）；`R-ID: all`（覆盖本 change 全部需求的聚合验证语义）。
- 验收标准 = 按「聚合套件发现契约」（见下）运行本 change 的单元+集成+e2e 测试套件并全部通过。
- 执行位置**维持在 `sdflow-implement` 内部**，即 `sdflow-code-review` 及其自动修复循环**之前**——不前移、不后移。
- 该票的**定位**是"实现期聚合回归门"：回答"全部功能票实现完毕这一刻，聚合套件是否通过"，**不声称**"最终代码通过聚合套件"。既有 Requirement「verify 为收尾最终门，位于所有修复之后」不受触碰。
- **聚合套件发现契约**（复用 `sdflow-devenv` 的既有答案，基准 5：MUST NOT 解析 Makefile/package.json）：命令来源优先级（config 显式配置 → implementer 依仓内既有约定判定并写明依据）→ 真跑一遍看退出码 → 缺层记「未覆盖」不罢工 → 证据落确定性 schema（`<层>|<命令>|<退出码>|<SHA>`）→ 四类失败分诊（本 change 回归/既有红测/flaky/环境故障）。
- **存在性与位置由机械门保证**：`ship_gate` 新增第四道 plan 校验——当且仅当计划文件名为 `tickets.md` 时，MUST 恰含一张该票且其 `Blocked-by` ⊇ 全部功能票号；旧名 `superpowers-plan.md` grandfather 跳过。
- **`sdflow-done` 的 verify** 引用该票 impl-report 作为「实现期聚合覆盖」需求的证据锚，锚语义限定为「实现期结束时聚合套件通过」，**按管线条件化**（仅 tickets 轨要求，superpowers 轨判「不适用」而非 gap）。

## Considered Options

- **本方案（收尾票留在 `sdflow-implement` 内，选中）**：见上 Decision。代价 = 证据锚相对 code-review 之后的修复不是最新（下条 Consequences 详述），但换来的是"实现期结束这一刻，聚合套件真的跑过一次"这个此前完全没有的保证，且不侵入 code-review/verify 既有职责边界。
- **verify 主动执行聚合套件（砍掉）**：让 `sdflow-done` 的 verify 步骤自己跑一遍聚合套件，而不是引用 implement 阶段留下的证据。理由砍掉：① verify 现有定位是"读证据判定"，不是"执行测试"——把执行力塞进 verify 会让它从"门禁"变成"又一个实现步骤"，职责越界；② verify 在 `sdflow-done` 里只有一次强档子代理调用，临时决定要不要重跑全套件、跑多久、如何处理 flaky，都会让这唯一的终门变得不确定，且本 change 的 Non-Goals 明确排除"重新设计 verify 的执行模型"；③ 即便 verify 主动跑了，仍然只是把"聚合回归执行点"从 A 处挪到 B 处，没有解决"该不该在 code-review 之后再跑一次"这个更根本的问题（见下一条）。
- **把聚合回归移到 `sdflow-code-review` 之后（砍掉）**：即在 code-review 通过、代码定稿之后再跑一次聚合套件，这样证据锚就是"相对最终代码"新鲜的。理由砍掉：① `sdflow-code-review` 的定位是"分支级冷层主审"，其自身已有双轴/领域镜 + 置信过滤 + 对抗裁决 + fix 循环这一整套保障机制，本 change 要解决的是**实现期间**（`sdflow-implement` 内部）的覆盖空洞，不是给 code-review 再叠一层执行步骤——叠加会让 code-review 的边界模糊，且相当于新增一个"code-review 之后、verify 之前"的隐藏阶段，与本 change 明写的"不修改 verify 位置、不新增阶段"的既有 Requirement 冲突；② 若真要在 code-review 之后强制重跑聚合套件，等价于把"全部功能票完成后聚合回归"这件事复制成两份（一份在 implement 内、一份在 code-review 后），双份维护成本与本 change 的简化取向（基准 4）相悖；③ 该方案仍不能完全消除"聚合套件通过之后 verify 本身或收尾流程又引入改动"这一理论上无穷递归的时效缺口——与其追着这条尾巴无限后移执行点，不如显式承认并接受当前这个更早的时效缺口（见 Consequences）。

## Consequences

- **接受的残余风险（已知且接受，非疏漏）**："收尾票锚点相对 code-review 修复而言不是最新"——`sdflow-code-review` 会自动修改并提交源码，但不重跑聚合套件；这段时效缺口由 code-review 自身的保障机制（双轴/领域镜 + 置信过滤 + 对抗裁决 + fix 循环）覆盖，不由收尾票兜底。五问分析（根因/概率/影响/完美成本/简化方案）见 `decision-memo.md`「接受的边角」一节。
- **证据锚措辞的强约束**：任何引用该票的地方（`sdflow-done/SKILL.md` 的 verify 步骤、verify-report.md 的逐需求核对表）MUST 把锚语义写成「实现期结束时聚合套件通过」，**MUST NOT** 写成「最终代码通过全量回归」——这是防止本决策的已知边界被后续文档悄悄抹平、变成一个未兑现的更强承诺。
- **verify 锚的管线条件化是必须实现项，非可选**：`sdflow-implement` 的 canonical 缺省管线是 `writing-plans → subagent-dev`（superpowers 轨），收尾票只由 tickets 轨产出；若 verify 无条件要求该锚，走 superpowers 轨的 change 会被判假 gap。本仓自身 `openspec/config.yaml` 是 `impl-pipeline: tickets`，dogfood 天然照不到这条分支，`tasks.md` §7.6 为此单列一条 superpowers 轨回归验证。
- **"不计入 3–6 预算"与 expand–contract 迁移批次共同构成两个预算外后门**：已知会稀释"3–6 张票"这个数字本身的约束力，本次接受，记 todo（改为约束总执行单元数或总 frontier 成本，而非单纯垂直切片张数）。
- **收尾票的存在与 `Blocked-by` 覆盖由 `ship_gate` 第四道校验机械保证**，不依赖人工记得加这张票或记得把依赖号写全——机械门的判据只认计划文件名（`tickets.md` 触发校验、`superpowers-plan.md` grandfather），不读 config/marker，因此与轨道路由权威（config 键 + plan frontmatter marker）解耦，不会因为判据来源不一致而互相打架。
- **回滚代价**：revert 本次 commit 集合后，`ship_gate` 的第四道校验与 `sdflow-implement`/`sdflow-done` 相关文本一并回退；已经按新契约落盘、含收尾票的在途 `tickets.md` 不会自动改回旧形态，其收尾票会成为该 plan 里一张"多余但无害"的普通 ticket（回滚不需要额外清理动作）。
