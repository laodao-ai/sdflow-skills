# T10 标签按决策语义拆分，不再共用单一编号

> 状态：**Accepted**（2026-07-27，`harden-implement-review-loop` 拷问阶段收敛）· 关联 change：`harden-implement-review-loop`

"T10"最初是 `2026-07-03-sdflow-ship` change 里一条 todo 追踪 ID（与 T11/T20 同批，结项后仍被沿用当规则简称），随后被阶段三"遇 ≥2 方案自动选"canonical 场景（`workflow.md`/`sdflow-ship`/`sdflow-code-review`/`spec-workflow` spec.md 等 5 处）与 `sdflow-implement` 借用同一处置形状的"熔断仲裁"（同一发现连续 2 轮 re-review 仍未消解）共同引用。两者处置形状相似（自动选/复核/defer），但触发条件截然不同——前者是"多个候选方案选一个"，后者是"同一问题反复解决不了、要不要继续"。继续共用同一个标签，会让未来编辑者误判"改一处等于改全部"——`harden-implement-review-loop` 自己起草阶段就险些如此。

## Considered Options

- **拆分为两条独立规则，`sdflow-implement` 的熔断仲裁场景不再引用"T10"（选中）**：依据 = 两者语义本质不同，共用标签会隐藏这个事实。代价 = 牺牲"一个标签查全部引用点"的便利性，未来理解两条规则需要分别定位各自落点。
- **维持沿用"T10"统一措辞**：未选。查证成本低、改动小；但掩盖触发条件不同的事实，且已实证会让编辑者误判改动范围。
- **把 T10 重构为真正的单一源 + 指针引用架构（如 `model-tiers.md` 的机读块模式）**：未选，超出本次范围。能同时解决"多处复述漂移"问题，但这次没人提出要做，是更大的架构改造（通则③禁止顺手加宽），留待独立立项。

## Consequences

- 以后改"阶段三 ≥2 方案自动选"的处置细节，只需要动 canonical 落点（`workflow.md`/`sdflow-ship`/`sdflow-code-review`/`spec-workflow` spec.md/`impl-orchestration` spec.md 里"粒度争议"与"矛盾裁决"两处）；改 `sdflow-implement` 的熔断仲裁，只需要动它自己那一处，两者互不牵连。
- 未来若有第三个场景想复用这套"自动选/复核/defer"处置形状，应各自独立描述，不该再往"T10"这个名字底下塞——标签只用于语义真正相同的场景。
- `openspec/CONTEXT.md` 需要加一行术语说明，防止"T10"被误解为放之四海而皆准的单一协议（见术语表条目）。

> 〔追记，`harden-implement-review-loop` Task 2〕两条具名规则最终定名 `T10-choice`（Group A，15 处规范性落点，②步统一派 strong 档）与 `review-loop-breaker`（Group B，独立成文，不再出现"T10"字样）；落点清单与统一计数口径见 `openspec/changes/harden-implement-review-loop/design.md`「T10 scope-check」表。
