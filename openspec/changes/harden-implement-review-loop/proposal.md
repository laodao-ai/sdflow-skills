## Why

`sdflow-implement` 是阶段三 tickets 管线唯一没有做"宿主/档位解析"的编排 skill——`implementer`/Standards 轴/Spec 轴/fix 子代理全部继承主 session 当前模型,没有显式声明,跟 `sdflow-code-review`/`sdflow-spec-review`/`sdflow-done` 三个姊妹 skill 的既定模式脱节。同时,T10 三级决策协议在多个落点被当作"同一件事"复述,但实际比对发现 `sdflow-implement` 借用的"熔断仲裁"场景与其余 4 处的"≥2 方案选择"场景触发条件不同,继续沿用同一个标签容易在未来编辑时只改一处、漏改另一处。此外,每 ticket "结束前跑一次全套件"未区分测试粒度,导致每票都要付全量 e2e/集成测试成本,而链路里又没有任何一步真正执行"全部票完成后的聚合回归",两头都不对。

## What Changes

- 给 `sdflow-implement` 补齐跟三个姊妹 skill 一致的"第零步:宿主/档位解析"(清脏→预检→捕获退出码→eval 后校验四步),`implementer`/Standards 轴/Spec 轴/fix 子代理声明为 mid 档。
- T10 协议拆成两条独立规则,不再共用同一个标签:
  - 阶段三"遇 ≥2 方案自动选"canonical 场景(`workflow.md`/`sdflow-ship`/`sdflow-code-review`/`spec-workflow` spec.md 四处同步复述)的"派对抗镜复核"步升级为 strong 档仲裁。
  - `sdflow-implement` 自己的"熔断仲裁"(同一发现连续 2 轮 re-review 仍未消解)场景独立成文,不再引用"T10"标签,其仲裁步同样升级为 strong 档。
- 每 feature ticket 的测试执行范围从"结束前跑一次全套件"收窄为"单元测试 + 本票声明的 e2e 场景";出票模式新增一张强制的"实现验证"收尾 ticket(`Blocked-by` 全部功能票,不计入 3–6 张垂直切片预算),专门运行聚合套件(单元+集成+e2e)并走标准 implementer + 双轴审 + fix 循环;`sdflow-done` 的 verify 按既有"逐条需求配机验锚点"模型引用这张收尾票自身的 commit/报告,不扩张 verify 职责。
- `spec-workflow` 的"模型档位映射(model-tiers)"Requirement 里补上 `sdflow-implement`(现有措辞只列了 `sdflow-ship`/`sdflow-done`/`sdflow-spec-review`/`sdflow-code-review`)。

## Capabilities

### New Capabilities

(无新增 capability)

### Modified Capabilities

- `impl-orchestration`: "每 ticket 双轴审加修复环,领域清单注入 Standards 轴"Requirement 补充档位声明与解析机制;新增测试执行范围与强制验证 ticket 的 Requirement;"试点回退与熔断哨兵"附近补充 `sdflow-implement` 熔断仲裁场景独立成文、不再引用"T10"标签的说明。
- `spec-workflow`: "阶段三过设计门后连续自动跑到 merge"Requirement 的 T10② 步补充 strong 档仲裁;"模型档位映射(model-tiers)"Requirement 补上 `sdflow-implement` 到编排 skill 清单。

## Impact

- 改动文件:`sdflow-implement/SKILL.md`(新增第零步 + 双轴审档位声明 + 熔断仲裁段落独立改写,弃用"T10"标签 + 出票模式"粒度争议"与"矛盾裁决"两类共 4 处 T10 引用升 strong + 测试范围段落改写 + 出票模式新增收尾 ticket 规则)、`sdflow-init/assets/workflow/workflow.md`(T10 canonical 定义补 strong)、`sdflow-ship/SKILL.md`(T10 复述补 strong)、`sdflow-code-review/SKILL.md`(T10② 复述补 strong)、`openspec/specs/spec-workflow/spec.md`(delta,含~83/~638 两处升 strong + 修回丢失的"按三镜+主次"措辞)、`openspec/specs/impl-orchestration/spec.md`(delta,含"出ticket模式"Requirement 的 T10 引用升 strong + 新增测试范围/验证ticket Requirement)。
- 不改动任何脚本逻辑(`impl_route.py` 等零改动),纯指令文本 + 两份 delta spec。
- 下游影响:任何仓库跑 `sdflow-init update` 拉取新版 bundle 后,`sdflow-implement` 执行模式会多出一张"实现验证"收尾 ticket;需要额外一次聚合测试套件执行时间,但每张功能票的单次执行成本下降。

## Success Metrics

- `sdflow-implement/SKILL.md` 全文可 grep 到 `$SDFLOW_TIER_MID`/`$SDFLOW_TIER_STRONG` 的合法引用,不再是零命中(现状 C1)。
- T10 相关的 6 个落点中,`sdflow-implement` 自己的熔断仲裁段落不再出现"T10"字样,其余 4 处 canonical 落点措辞一致(含"按三镜+主次"限定词,修复 C8 差异 B)。
- 出票模式产出的 `superpowers-plan.md` 恒含一张不计入 3–6 预算的"实现验证"收尾 ticket。

## Non-Goals

- 不把 T10 的"各处复述"架构重构成真正的单一源+指针引用——继续复述,只是拆清楚哪些复述描述的是同一件事、哪些不是。
- 不做任务复杂度动态选 implementer 档位(超出本次范围,需独立立项调研复杂度分类器)。
- 不改动 design D8"implementer 档位钉死 mid"的既有试点期变量控制决定本身(本次只是给它补齐档位解析机制,不改变它取值为 mid 这个决定)。
- 不追加"熔断前先 resume 原 implementer 做一次同档重试"这类 superpowers 式额外中间步——未在本次讨论范围内,涉及重开 design D8 的试点期变量控制决定,留待独立立项。

## Compliance

N/A——本次改动为纯指令文本与 delta spec,不涉及数据合规、隐私或安全边界变化。
