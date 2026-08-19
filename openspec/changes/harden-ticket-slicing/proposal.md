## Why

票的切分（tracer-bullet 垂直切片）是阶段三最承重的规划判断，但它当前落在全流程模型档位最弱、且无任何独立审查的位置：出票由 ship 主 session inline 执行（模型 = 阶段三 session 档），切片建议节是 MAY（常缺席 ⇒ 弱档模型全量自由裁量），T10-choice 对抗镜复核仅在粒度争议时触发。同时 T141（change 拆分标准融入 workflow）开了七周未收口，拆分/切片这同一片「分解」一致性面缺单一源。

## What Changes

- **P0** 切片建议升档：design.md「切片建议」节 MAY→SHOULD（缺席须写一句为何不需要）；spec-review 新增 BASE-31 审项（切片建议存在性/内聚质量），经镜表默认规则归 strategy 镜，零路由改动。切片判断由此前移到强模型 + 受审 + 人门可见的位置。
- **P0** 出票消费语义升级：`sdflow-implement` 出票模式对切片建议从「建议输入」→「默认采纳；偏离逐条记 `impl-reports/planning-decisions.md` + 理由」。
- **P0** T10-choice 复核必触发：触发条件从「仅粒度争议」扩为「无切片建议 ∨ 出票偏离草图 ∨ 草图与 design 正文矛盾」（第三条兜住「评审 amendments 改设计但切片节残留旧切分」的节级失鲜缺口）。
- **P1** T141 收口：新增单一源 `sdflow-init/assets/workflow/reference/change-decomposition-standard.md`（拆分 4 规则 + why），roadmap（每 phase = 完整阶段结果）/ sdflow-spec 相位 B（scope 内聚检查）/ 执行期（implementer 撞 related 票外问题 → 上报编排层按 BASE-18 AND 门判 fold/defer，MUST NOT 自行扩 scope）三处指针引用不复制。做完 T141 set-status DONE。
- 不改的：出票步的位置与 gate 契约零改动（`plan_first_sha` 窗口、design 域失鲜监视集、第四道 plan 校验原样）；strong 档模型维持 opus（fable 覆盖已拍板不做）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `impl-orchestration`: 出票模式对切片建议的消费语义（默认采纳 + 偏离审计落 planning-decisions.md）、T10-choice 必触发条件集、执行模式 implementer 票外问题上报 fold/defer 判定。
- `spec-authoring`: 相位 C 生成 design.md 时切片建议 SHOULD（缺席须记理由）；相位 B 拷问加 scope 内聚检查（引拆分标准单一源）。
- `roadmap-planning`: roadmap 拆分显式引用拆分标准（每 phase/change = 一个完整阶段结果）。

## Impact

- **workflow bundle（权威源 `sdflow-init/assets/workflow/`）**：`ff-generation-constraints.md`（切片建议节升档）、`spec-checklists/spec-quality-base.md`（BASE-31）、新增 `reference/change-decomposition-standard.md`；随 `sdflow-init update` 推给所有消费仓；`openspec/INDEX.md` 需同步新增文件。
- **SKILL 指令**：`sdflow-implement`（消费语义 + 必触发 + 上报纪律）、`sdflow-spec`（相位 B 检查项）、`sdflow-spec-review`（无路由改动，靠默认规则）、`sdflow-code-review`（fold/defer 判定指针）、`sdflow-roadmap`（拆分规则引用）。
- **spec-workflow 无 delta**：评审期 fold-vs-defer 已有既有条款（`spec-workflow/spec.md` 的 fold-vs-defer Scenario，BASE-18 口径），BASE-31 归镜走「未列明 base R 项归 strategy 镜」默认规则、spec 文本泛指「base 清单 R 项」不硬编码清单——本次对 `sdflow-code-review`/`sdflow-spec-review` 的改动是 SKILL 层对既有 spec 条款的对齐与 bundle 内容新增，spec 级行为零变化。
- **零改动**：`ship_gate.py` 及全部机械层脚本；`openspec/config.yaml`。
- **issues 池**：T141 关闭（resolved_by = 本 change，用开发 checkout 脚本操作）。

## Success Metrics

- 目标态下每个非平凡 change 的切分方案在人工设计门（HARD-GATE）前可见且被 strategy 镜审过；缺席时 design.md 有显式理由。
- 出票落盘后，`planning-decisions.md` 对「无草图 / 偏离 / 矛盾」三种情形均有 T10-choice 复核记录行（有触发即有记录，可 git 审计）。
- T141 状态 = DONE；拆分标准文本在 bundle 中仅存一份，三处消费点均为指针引用（grep 可验无复制）。

## Non-Goals

- 不搬出票步到 spec-review 之前（评审 amendments 几乎必落 ⇒ 每 change 白付一次出票；gate 契约重造爆炸半径大）。
- 不做「偏离草图」的机械判定（票数增减 ≠ 偏离，无确定性信号 ⇒ 必触发是指令层约束，诚实边界如实标注）。
- 不改 strong 档模型映射（fable 覆盖、版本钉死均不在本次范围；后者已确认是一行 config 的将来旋钮）。
- 不在 spec-review 侧加「切片同步核」审项（矛盾显形点在出票，单点兜住即达目标态）。

## Compliance

N/A——纯 workflow 规则与 skill 指令变更，不涉及 PII、数据居留或第三方数据外发。
