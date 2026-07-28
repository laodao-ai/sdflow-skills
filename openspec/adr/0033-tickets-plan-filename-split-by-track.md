# 计划文件名按轨分列（`tickets.md` / `superpowers-plan.md`），双存在 fail-closed

> 状态：**Accepted**（2026-07-28，`harden-implement-review-loop` 拷问阶段收敛，用户拍板）· 关联 change：`harden-implement-review-loop`

`superpowers-plan.md` 是 sdflow 阶段三**superpowers-only 时期**的遗留文件名——`writing-plans` 生成它、`subagent-driven-development` 消费它、`ship_gate.py` 按字面名判定 `RUN_PLAN`。`matt-workflow-integration` 引入 tickets 实现管线（`sdflow-implement`）时，为了让 `ship_gate.py` **零改动**兼容，选择让 tickets 轨的出票文件也借用同一个文件名（`adr/0017` 的"试验期外衣"决策）。这个借壳从一开始就是已知的命名负债：文件名叫 `superpowers-plan.md`，内容却是 tickets 轨的行为级 ticket，对读者是明显的误导（`openspec/issues/todolist/2026-07-todolist.md` T135 记录了这条 todo）。

`adr/0017` 当时把"终局文件名迁移"明确留给"Phase B 拍板"（见 `docs/workflow-skills/impl-pipeline-matt-vs-superpowers.md` Q3 行），本 ADR 就是那次拍板的结果。

**关键事实（决定了不能简单改名）**：该文件名当前**两轨共用**——`ship_gate.py`（gate 按字面名判 `RUN_PLAN`）、`impl_route.py`（route 按字面名取 frontmatter marker）、`superpowers` 轨自己的 `prompts/step6-writing-plans.md`（提示 `/writing-plans` 生成该名）三处都依赖这个字面量。全局改名会把 superpowers 轨也改成 `tickets.md`，与其语义（该轨从未产出"ticket"，产出的是带码步骤的 plan）直接冲突。

## Considered Options

- **分轨命名 + gate/route 共享 resolver 探两名，双存在 fail-closed UNKNOWN（选中）**：tickets 轨新出的计划文件落盘为 `tickets.md`；superpowers 轨保持 `superpowers-plan.md` 不变。`ship_gate.py` 与 `sdflow-implement/scripts/impl_route.py` 改用同一个共享 resolver 函数（单一源，非各自手抄候选列表）按序探测两个文件名：命中其一即用；都不存在判 `RUN_PLAN`；**两者同时存在 ⇒ fail-closed 判 `UNKNOWN`**（不猜哪个有效，提示人工删除其一）。文件名本身**不参与轨道路由判定**——路由权威仍是 `config.yaml` 的 `impl-pipeline` 键 + plan frontmatter marker，文件名只用于"到哪个文件里找完成判据"这一件事，避免新增一个会与 marker 打架的冗余路由信号。
- **全局统一改成一个中性新名（如 `impl-plan.md`）（砍掉）**：理由——用户已明确指定 tickets 轨新名为 `tickets.md`；且中性名同样要面对"superpowers 轨也要不要改"的问题，若跟着改则连累 `writing-plans` 既有 prompt 契约（外部 skill，改名等于改变其调用约定），若不跟着改则仍是两名并存、只是换了个新名字，并未减少本质复杂度。
- **只改文档说明、不改脚本行为（砍掉）**：理由——`ship_gate.py` 与 `impl_route.py` 都是按**字面文件名**判定完成状态与路由的，不改脚本，tickets 轨新写的 `tickets.md` 根本不会被 gate 认到，`RUN_PLAN` 会永久判定"计划缺失"，管线直接锁死。文档说了等于没说。

## Consequences

- **两个合法文件名永久共存**：`tickets.md`（tickets 轨）与 `superpowers-plan.md`（superpowers 轨）都是当前合法产物，任何未来阅读代码/文档的人不应把"看到 `superpowers-plan.md`"当作"这是遗留错误"——它是 superpowers 轨的正确产物名，只有 tickets 轨的旧引用才是需要迁移的历史负债。
- **在途 plan 的 grandfather 条款**：升级发生在某个 tickets 轨 change 已经落盘 `superpowers-plan.md`（旧名）的中途时，该文件**MUST NOT 被重命名**——`ship_gate.plan_first_sha()` 用 `git log --diff-filter=A` 取完成判据窗口起点，该判据不跟随 `git mv`，强行改名会把窗口起点推到改名 commit 本身，导致改名前的全部 `checkpoint(<change>:task<N>-...)` 标签落在窗口外，已完成的 ticket 被 gate 判定为未完成、可能被重派。resolver 对这类在途旧名文件按原样识别，`ship_gate` 新增的收尾票校验（相关设计见本 change `design.md`「收尾票」专节）对这类文件 grandfather、不强制要求收尾票。
- **`ship_gate.py` 与 `impl_route.py` 的 import 关系**：resolver 是单一源（定义于 `ship_gate.py`），`impl_route.py` 经既有 sibling-import 机制引用同一个函数对象，禁止任何一方手抄一份候选文件名列表——否则两处候选列表迟早漂移。
- **回滚代价**：revert 本次 commit 集合后，resolver 一并回退到旧的单文件名判定；但**已经按新名 `tickets.md` 落盘的在途 change**不会跟着自动改回——需要人工 `git mv tickets.md superpowers-plan.md` 补一次改名操作，且同样要注意"在途 plan 不可重命名"的窗口风险（若该 change 已有 checkpoint 标签，这次回滚改名同样会推后窗口起点）。这条回滚代价已记入本 change `design.md` 的 Migration Plan。
- **全仓文件名措辞同步**：tickets 轨相关的指令文本（`sdflow-implement/SKILL.md`、`sdflow-done/SKILL.md`）、bundle 规则、文档、既有测试断言字面量，全部同步改为 `tickets.md`；superpowers 轨的引用（`prompts/step6-writing-plans.md`、`docs/workflow-skills/superpowers-writing-plans.md` 等）原样保留 `superpowers-plan.md` 不变；历史归档（`openspec/changes/archive/**`）与 issues 池的既有记录不回改（改写即伪造审计）。
