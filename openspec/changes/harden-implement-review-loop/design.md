## Context

`sdflow-implement` 是阶段三 tickets 管线的执行编排器,由 `sdflow-ship` inline 调用。三处现状问题经本 change 拷问阶段逐条查实(完整证据锚见 `decision-memo.md` C1-C9):

1. **零档位声明**——`sdflow-implement/SKILL.md` 全文 grep 不到 `model-tier`/`strong`/`mid`/`opus`/`sonnet`/`resolve-models` 任一命中,跟 `sdflow-code-review`/`sdflow-spec-review`/`sdflow-done` 三个姊妹 skill 都有的"第零步:宿主/档位解析"脱节(C1)。
2. **T10 标签遮蔽了真实的场景差异**——6 个引用落点里,`sdflow-implement` 借用的"熔断仲裁"(同一发现连续2轮 re-review 仍未消解)与其余5处的"≥2方案自动选"触发条件本质不同,继续共用一个标签会让未来编辑者误判"改一处等于改全部"(C8)。
3. **测试执行范围与实际覆盖脱节**——现有"结束前跑一次全套件"未分粒度,每票都要付全量 e2e/集成成本;而链路里(`sdflow-implement`→`sdflow-code-review`→`sdflow-done`)又没有任何一步真正执行"全部票完成后的聚合回归"(C3,`sdflow-done` verify 的锚点模型是逐条审计、非聚合执行)。

## Goals / Non-Goals

**Goals:**
- 给 `sdflow-implement` 补齐跟三个姊妹 skill 一致的档位解析机制,implementer/Standards轴/Spec轴/fix子代理声明为 mid。
- 把 T10 按语义拆成两条独立规则,消除"一个标签、两种触发条件"的隐患。
- 让每 feature ticket 的测试执行范围与"这一票该测什么"对齐,同时补上链路里缺失的聚合回归执行点。
- 把 `sdflow-implement` 补进 `spec-workflow` 的"模型档位映射"Requirement 现有编排 skill 清单。

**Non-Goals:**
详见 `proposal.md` Non-Goals 节——不重构 T10 复述架构为单一源、不做复杂度动态选档(D4)、不改 design D8 的既有钉死决定本身、不追加 superpowers 式"熔断前先同档重试一次"的中间步。

## Decisions

完整依据/被砍候选/代价见 `decision-memo.md`,此处只列结论指针,不重复论证:

- **D1**:`implementer`/Standards轴/Spec轴/fix子代理 → 声明 mid,补第零步档位解析四步(清脏→预检→捕获退出码→eval后校验),模板与 `sdflow-code-review`/`sdflow-spec-review`/`sdflow-done` 逐字一致。
- **D2a**:阶段三"≥2方案自动选"canonical 场景②步升级为 strong,**实际落点比最初拷问时统计的更多**——除 `workflow.md`/`sdflow-ship/SKILL.md`/`sdflow-code-review/SKILL.md`/`spec-workflow/spec.md`(~83/~638,顺带修回丢失的"按三镜+主次"措辞)外,复核发现 `impl-orchestration/spec.md:27`("出ticket模式"Requirement 的"粒度争议按T10处理")与 `sdflow-implement/SKILL.md` 自身另外 4 处(203/271/282/545——出票模式的"粒度争议"+"全ticket语义一致性自扫"矛盾裁决,均是"多种候选方案选一个"语义,不是循环熔断)同样属于 Group A,一并升 strong。`sdflow-implement/SKILL.md:372` 与 `impl-orchestration/spec.md:60` 是仅引用尾部处置("defer或停")、未提及②步的轻量引用,不需要改。
- **D2b**:`sdflow-implement/SKILL.md:490-493` 熔断仲裁场景独立成文,不再出现"T10"字样,②步同样升级为 strong——这是全仓唯一一处 Group B 语义,只改这一处。
- **D3**:每 feature ticket 测试范围收窄为"单元+本票e2e场景";出票模式新增一张不计入 3–6 预算的强制"实现验证"收尾 ticket(`Blocked-by` 全部功能票),跑聚合套件(单元+集成+e2e)走标准 implementer+双轴审+fix 循环;`sdflow-done` verify 只引用这张票自身的 commit/报告作为证据锚,不扩张 verify 职责。
- **D4(不做)**:任务复杂度动态选 implementer 档位——出票阶段的 size 上限 + T120 已过滤大部分先验信号,复杂度分类器是独立调研量级,这次不做。

## 设计图

```
T10 标签拆分前后对照(9 处落点 → 2 组独立规则,~29 为合法指针不单独编辑)

  【组A:"≥2方案自动选"语义(粒度争议/矛盾裁决/推荐项选择,继续复述,②步统一加 strong,D2a)】
    workflow.md:106
    sdflow-ship/SKILL.md:164
    sdflow-code-review/SKILL.md:283
    spec-workflow/spec.md:~83, ~638          (~29 是合法指针"引主spec T10需求",不单独编辑)
    impl-orchestration/spec.md:27            (出ticket模式·粒度争议)
    sdflow-implement/SKILL.md:203,271        (出ticket模式·粒度争议,同一话题两处提及)
    sdflow-implement/SKILL.md:282,545        (语义一致性自扫·矛盾裁决,规则+出处说明两处)

  【组B:sdflow-implement 熔断仲裁(语义独立,脱钩,②步独立加 strong,D2b)】
    sdflow-implement/SKILL.md:490-493 ── 不再提"T10"

  【不动:仅引用尾部处置,未提②步】
    sdflow-implement/SKILL.md:372、impl-orchestration/spec.md:60 ── "走T10(defer或停)"


出票模式 frontier 依赖图(新增收尾 ticket 位置)

  Task 1 ──┐
  Task 2 ──┼─Blocked-by──▶ Task N(实现验证,收尾)
  Task 3 ──┘                  │
  (功能票,3-6张,           跑聚合套件(单元+集成+e2e)
   各自:单元+本票e2e)         + 标准 implementer/双轴审/fix 循环
                              │
                              ▼
                    sdflow-done verify
                    (引用本票 commit/报告为证据锚,
                     不扩张自身职责)
```

## Risks / Trade-offs

- **[Risk]** 跨票 e2e/集成回归的发现时间从"当票发生时立即发现"推迟到"末尾聚合验证票才发现",排查需要一定回溯成本。
  **→ Mitigation**:排查范围有界(仅限本 change 自身 3-6 张票的 commit 集合);验证票复用完整的 implementer+双轴审+fix循环+D2b 熔断升 strong 机制,不是无处置能力的黑洞。
- **[Risk]** Standards/Spec reviewer 自判 severity,判断权重比 code-review 领域镜更重,mid 档可能误判。
  **→ Mitigation**:下游 `sdflow-code-review` 冷层是完全独立重审,不依赖 implement 阶段的 severity 标签,误判的代码本身仍会被冷层独立发现。
- **[Risk]** 已在途(尚未走完)的旧 `superpowers-plan.md` 不会自动获得新增的"实现验证"收尾 ticket。
  **→ Mitigation**:见下方 Migration Plan——按"追加新号"规则(F1)手动补一张,不影响新开 change。

## Migration Plan

- 本次改动全部是指令文本 + 两份 delta spec,不涉及脚本/代码逻辑,无需数据迁移或回滚脚本。
- 部署路径:合并本 change → 下游消费仓运行 `sdflow-init update` 拉取新版 bundle 后生效。
- **已在途 change 的兼容性**:`superpowers-plan.md` 有"首次提交后结构不可变,MUST NOT 重号/重排/删除/复用已出的 Task 号,只能追加新号"的既有约束(F1)。已出票但未走完的旧 plan 不会自动获得"实现验证"收尾 ticket——若需要,按追加新 Task 号的既有机制手动补一张,`Blocked-by` 指向该 plan 当前全部功能票号。新开的 change 从本次改动生效起,出票模式自动产出该收尾票,无需手动干预。
- 回滚:直接 revert 本次 commit 集合,`sdflow-implement`/`workflow.md`/`sdflow-ship`/`sdflow-code-review` 的文本回到改动前状态,delta spec 归档回滚由 `openspec archive` 既有机制处理。

## Open Questions

本次无遗留开放问题——B 阶段拷问已覆盖 severity 权重、每票必要性、superpowers 对照、T10 标签拆分、verify 职责边界、测试强度量化六个实质性问题,均已拍板并记入 `decision-memo.md`。D4 与"T10 复述架构重构"已在 Non-Goals 声明为本次不做,不是待定问题。

## Compliance

N/A——本次改动为纯指令文本与 delta spec,不涉及数据合规、隐私或安全边界变化。
