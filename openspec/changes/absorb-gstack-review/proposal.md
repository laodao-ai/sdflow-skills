## Why

`sdflow-code-review` 的 Step1 依赖第三方 gstack `/review` skill 原生执行（1853 行，其中约 800 行为
gstack 框架样板），存在三个结构性冲突：① gstack 的 AskUserQuestion 门（Fix-First batch-ask、
HIGH-impact gate、preamble 配置问答）与阶段三「无人类门」铁律按字面不可同时满足；② gstack 的
Step 5b auto-fix 发生在本 skill Step4/5 两段 checkpoint 工作树纪律之前，污染提交时序；③ 其计划
完成度审计的 plan 发现只搜 gstack 专属路径，不认识 `openspec/changes/<name>/`，实际运行退化为
commit-message 猜意图——最想要的能力在本工作流里恰是残废状态。同时 gstack 随 `gstack-upgrade`
第三方演进，Step1 行为不受本仓控制。gstack checklist 与本仓 `code-checklists/` 逐条比对后确认
五类真空缺口（DB 层竞态 / LLM 信任边界 / shell 注入 / 枚举完备性 / XSS），吸收后依赖残值归零。

## What Changes

- **Step1 自持化**：`sdflow-code-review/SKILL.md` Step1 重写为恒跑 fresh 子代理（中档）的
  scope-drift + 完成度审计——意图源改锚 OpenSpec 四件套（proposal scope/Non-Goals + tasks.md +
  design.md，确定性、零猜测），吸收 gstack 五态完成度分类词汇（DONE/PARTIAL/NOT DONE/CHANGED/
  UNVERIFIABLE + DONE 从严/CHANGED 从宽/UNVERIFIABLE 诚实）；子代理不可用时降级主 session 亲做
  （恒跑守卫语义不变）。锚名 `step1-broad-review` 保留，mode 枚举换新值。
- **code-checklists 吸收**：base 新增 CR-10（shell 注入）、CR-11（枚举/取值完备性，含「必须读
  diff 外代码」）；`domains/backend.md` 新增 CR-BE-03（DB 层竞态：唯一索引/原子 WHERE/状态迁移）、
  CR-BE-02 检查点扩 XSS/不安全 HTML；新增 `domains/llm.md`（CR-LLM-*：LLM 输出信任边界 +
  LLM prompt issues）。
- **trigger-catalog 新增 TG-27（LLM 集成面）**并收进 HR-TG 子集（触发措辞收窄为「代码消费
  LLM/agent 产出并持久化/执行/外呼」；命中率走既有 Q5 复评机制）。
- **pre-emit verification gate**：Step2 fan-out 子代理 prompt 模板 + Step3 置信过滤新增「finding
  必须引出触发行原文，引不出 → 置信上限 50、落已裁掉区」；Step3 明确滤除类目吸收 gstack
  Suppressions 可泛化条目。
- **机械消费点同步**：`lens-metric-contract.md` fold 块 raw 名 `gstack-adv` → `scope-audit`
  （直接替换不共存）；`anchor_lint.py` mirrors token 枚举扩 `broad`（只进合法 token 集、不进
  dead-fanout 计数集——broad 有主 session 降级合法路径）+ golden 测试；`prompts/step8-code-review.md`
  提示词 + `hack/tests/test_workflow_split.py` needle；`workflow.md` / `quality-layering.md` /
  `docs/workflow-skills/*` / `docs/external-dependencies.md` 提法更新。
- **不动**：`sdflow-spec-review` 的 autoplan 依赖及 `outside_voice_guard`（spec-review 侧姊妹
  依赖另行处置，记 todo）；归档报告旧锚不迁移。

## Capabilities

### New Capabilities

（无——checklist/TG 条目为 workflow bundle 数据资产，不引入新的行为级能力）

### Modified Capabilities

- `spec-workflow`: 阶段三 code-review Step1 的实现主体由「gstack/review 原生执行」改为「自持
  fresh 子代理 scope 审计」；恒跑 + trivial_shape 白名单守卫语义保留；新增五态完成度审计与
  pre-emit verification gate 的 Requirement 级描述。
- `host-adaptive-execution`: `fanout-capability` 锚 `mirrors=` 合法 token 集扩 `broad`
  （spec 级钉死于 §157/159；dead-fanout 计数集不变）；能力探针覆盖 Step1 scope 子代理。
- `workflow-metrics`: 折叠表 prose「autoplan/gstack 各子声折叠到 broad」改述为
  「autoplan 各子声与 code-review scope-audit 折叠到 broad」；dead-fanout Scenario 的
  mirrors token 文法同步（计数集语义不变）。

## Impact

- **代码/资产**：`sdflow-code-review/SKILL.md` · `sdflow-init/assets/workflow/`（code-checklists
  base+backend+新 llm.md · trigger-catalog.md · lens-metric-contract.md · tools/anchor_lint.py ·
  prompts/step8-code-review.md · workflow.md · reference/quality-layering.md）· `hack/tests/`
  golden 测试 · `docs/`。栈标注：markdown workflow 资产 + Python 工具（命中行为面路径
  bundle/SKILL.md，非 TG-01/02/03 业务栈）。
- **依赖**：移除 code-review 侧对 gstack skill 的运行时依赖；无新增外部依赖。
- **消费仓**：经 `sdflow-init update` 获得新 checklists/contract/tools；SKILL 经 setup.sh symlink
  即时生效——bundle skew 窗口为既有 pull→setup 纪律，emitter 对旧 raw 名 fail-closed 非假绿。

## 需求优先级

- **P0**：Step1 自持化 + spec 三 delta + contract/anchor_lint 机械消费点同步（依赖移除的完整闭环，
  缺任一则新旧混态）。
- **P1**：checklist 吸收（CR-10/11/BE-03/BE-02 扩点/llm.md + TG-27）+ pre-emit gate + Suppressions
  条目（能力增强，独立可验）。
- **P2**：docs 提法更新（workflow-skills/external-dependencies 等纯文档）。

## Success Metrics

- `grep -rn "gstack" sdflow-code-review/SKILL.md` 归零（历史注记除外）；code-review 全流程在未安装
  gstack 的机器上可完整跑通（Step1 无降级日志）。
- 全仓 pytest 绿（含 anchor_lint golden 新 token、test_workflow_split needle 更新）。
- dogfood：本 change 自身的代码审报告产出 `scope-audit` raw 名 broad 镜行 + 新 mode 锚，
  `anchor_lint` 通过。

## Non-Goals

- 不动 `sdflow-spec-review` 的 autoplan 依赖与 `outside_voice_guard.py`（姊妹依赖，记 todo 另行处置）。
- 不吸收 gstack 的 AskUserQuestion 门 / Fix-First 启发式（阶段三无人类门替代）。
- 不吸收 gstack Pass-2 剩余条目：Async/Sync 混用（Python）defer 记 todo（归属不存在的 python.md
  domain）；Time Window / Column-Name / 类型跨界 hash / View-Frontend / CI-CD 发布 /
  VERSION-CHANGELOG 一致性放弃（低频/栈不匹配/已有部分覆盖）。
- 不迁移归档报告中的旧 `mode="native|simulated"` 锚与 `gstack-adv` raw 名（冻结审计件）。
- 不建 python.md domain、不动 frontend domain 占位。

## Compliance

N/A（本仓为本地开发工具链，无外部合规面）。
