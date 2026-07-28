## MODIFIED Requirements

### Requirement: 阶段三过设计门后连续自动跑到 merge

阶段三 SHALL 在阶段二设计门之后无任何阻塞人类门地连续运行 `实现管线 → sdflow-code-review → sdflow-done`；实现管线为可选双轨——缺省 `writing-plans → subagent-dev`，或经 `impl-orchestration` 能力的手动路由（config 键 + 盘面 marker，缺省/非法值一律 superpowers）选择 `sdflow-implement 双模式（出 ticket → 执行）`；**编排层入口 = `/sdflow-ship`**（一次调用驱动 5.5→9，按「阶段三编排台账确定性」需求经 ship_gate 推进；手动逐步仍为合法 reference 路径）。**两轨的计划文件名 SHALL 分列**——tickets 轨 `tickets.md`、superpowers 轨 `superpowers-plan.md`，由 gate 与 route helper 经同一份共享 resolver 定位；两者同时存在 SHALL fail-closed 判 UNKNOWN；**文件名 MUST NOT 参与轨道路由判定**（路由权威仍是 config 键 + plan frontmatter marker）〔spec-review-amendment · adr/0033〕。管线选择 MUST NOT 引入模型自动判断，MUST NOT 新增人类门。实现管线内不可消解的 BLOCKED 停机属「defer-to-human 异常终态」而非人类门——与既有 BLOCKED_UPSTREAM 同构（停并上抛、人工再入口），不违背「无阻塞人类门」承诺（正常路径仍连续到 merge）〔spec-review-amendment F7〕。能修的自动修；**遇 ≥2 方案 MUST 按三级决策协议 `T10-choice`**〔具名规则，取代旧「T10」单一编号；"T10" 保留为历史别名。语义边界见 `adr/0031`：本规则**只覆盖「多个候选方案选哪个」**，`sdflow-implement` 的「同一发现反复未消解」熔断由 `review-loop-breaker` 独立定义，两者 MUST NOT 互相引用〕：①有客观判据（测试/断言/基准可判）→ 自动选并**按三镜 + 主次**记理由；②无客观判据 → 派 **strong 档**对抗镜复核推荐项，通过方自动选（复核记录进报告；出票模式无报告产物时落 `impl-reports/planning-decisions.md`）；③复核不过或无从复核 → defer 进 buglist/todolist 并由 hand-off 引导另开 change 清理。MUST NOT 以自评置信（"有把握"）作为自动选定的唯一依据。修不了或需拍板的 MUST 进 buglist/todolist 延后。

#### Scenario: 修不了的问题延后而非阻塞

- **WHEN** sdflow-code-review 发现一个本 change 修不掉的问题
- **THEN** 它进 buglist/todolist(defer) 并写入 hand-off，流程继续跑到 sdflow-done，不设人类门阻塞

#### Scenario: 无客观判据的两方案走 strong 档对抗复核

- **WHEN** 阶段三某步遇两个可行方案且无测试/断言可判优劣
- **THEN** 派 strong 档对抗镜尝试证伪推荐方案：未被证伪 → 自动选并按三镜+主次记复核记录；被证伪或复核无法开展 → defer，MUST NOT 凭"有把握"直接选，MUST NOT 用 mid 档同档互判代替 strong 档仲裁

#### Scenario: 一次调用驱动到 merge 建议

- **WHEN** 对已过设计门的 change 调用 /sdflow-ship 且各步门禁全通过
- **THEN** 链依 gate 判定逐步推进至 sdflow-done 完成（含 merge 缺省语义），输出最终摘要；全程无 AskUserQuestion

#### Scenario: ship 零 git 写操作、merge 意图透传〔grill-amendment〕

- **WHEN** 用户以"跑到 merge 前停"类意图调用 /sdflow-ship
- **THEN** ship 将 opt-out 原样透传给 sdflow-done（merge 由 done 一处执行/跳过）；ship 自身 MUST NOT commit/merge/push，MUST NOT 自动 push（摘要提醒手动 push；toolkit 源仓附激活提示）

#### Scenario: 实现管线按手动确定值路由

- **WHEN** gate 判定 RUN_PLAN 且 config 键值为 `tickets`
- **THEN** ship 派发 sdflow-implement 出 ticket 模式；键缺省/非法/为 superpowers 时派发 writing-plans，行为与本变更前一致；CONTINUE_IMPL 一律按 plan 文件 marker 路由

#### Scenario: 计划文件按轨定位且双存在即停

- **WHEN** gate 需要定位某 change 的计划文件
- **THEN** 经共享 resolver 依次探测 `tickets.md` 与 `superpowers-plan.md`：命中其一即用之；两者皆无判 RUN_PLAN；**两者同时存在判 UNKNOWN 并提示人工删除其一**，MUST NOT 猜测哪个有效

### Requirement: outside-voice tension 不静默采纳

outside voice 与主审分歧（tension）SHALL 中立并陈、标 TENSION：sdflow-spec-review 写入报告决策登记区（选项 + 推荐 + 两方视角 + **三面后果（系统 / 用户 / 开发循环）+ 主次判定**，设计 HARD-GATE 人一次性拍板）；sdflow-code-review 按 `T10-choice` 三级协议自动裁决（有客观判据自动裁 / 无则派 **strong 档**对抗镜复核 / 复核不过或无从复核则 defer 进 buglist/todolist + hand-off）并**按三镜 + 主次记理由**，MUST NOT 以自评置信（"有把握"）为自动裁决唯一依据〔impl-review-fix F1/CV2〕。outside voice 的建议 MUST NOT 被静默自动采纳（不直接改代码/设计而不留痕）。

**置信过滤豁免 SHALL 按合法组合矩阵的「跨模型」判定，MUST NOT 自写 `runner ≠ host` 或按 runner 枚举值硬编码**〔add-codex-host-support · spec-review-r2 C1〕：**矩阵判「跨模型」为真**（`host,runner 均∈{claude,codex} ∧ runner≠host ∧ reason_code="ok"`）的 outside-voice findings MUST NOT 经自评置信阈值（<80）预过滤——跨模型自评不可比、异见易被同族标尺误杀——一律直通对抗裁决，被裁掉的连理由落报告「已裁掉」区〔grill-amendment Q4〕；**其余**（同族 fallback `runner==host`、**及无执行 `runner="none"`**）照过同族置信滤（豁免理由对其不成立；`runner="none"` 的 findings 恒 0、豁免无意义）。

> 〔为何引用矩阵而非自写 `runner≠host`〕旧规则写死 `runner=codex` 豁免——该值在 Codex 宿主下恰恰是**自审**；而首轮改的 `runner ≠ host` 又被 `runner="none"` 击穿（`none≠host` 恒真 → 无执行轮被误豁免，spec-review-r2 C1）。∴ 判据 MUST 引用合法组合矩阵的单一「跨模型」判定，不在此重写关系式。

#### Scenario: 设计侧分歧进决策登记区
- **WHEN** outside voice 与 spec-review 主审对同一设计点结论相反
- **THEN** 报告决策登记区新增 TENSION 条目（两方观点 + 推荐 + 三面后果 + 主次判定），不中途 AskUserQuestion

#### Scenario: 代码侧分歧派 strong 档自动裁决或 defer
- **WHEN** outside voice 与 code-review 主审分歧且裁决无客观判据
- **THEN** 派 strong 档对抗镜复核，复核不过或无从复核则 defer 进 issues 池并写入 hand-off，不静默采纳任一方，MUST NOT 用 mid 档同档互判代替

#### Scenario: 低自评置信的跨模型 finding 不被预筛
- **WHEN** 某条 `runner ≠ host` 的 finding 自评置信低于 Step3 阈值（<80）
- **THEN** 该条仍进入对抗裁决（不被置信滤拦截）；若裁决不成立，连理由落报告「已裁掉」区

#### Scenario: 同族 fallback finding 照过同族滤
- **WHEN** 某条 `runner == host` 的 finding 自评置信低于阈值
- **THEN** 按同族 findings 常规处理（过滤规则一致），不享受跨模型豁免

#### Scenario: Codex 宿主下的 codex findings 不再误享豁免〔add-codex-host-support〕
- **WHEN** `host="codex"` 且某条 finding 的 `runner="codex"`（同族 fallback 产物）
- **THEN** 照过同族置信滤，MUST NOT 因 `runner` 值恰为 `codex` 而豁免（旧规则的假绿点）

### Requirement: 模型档位映射（model-tiers）

模型档位定义、职责清单与 canonical 缺省 MUST 以 workflow bundle 规则文件 **`model-tiers.md`** 为单一真相源（经 resolver 全局解析；强档=verify/对抗裁决/final 终审；中档=领域镜/生成/实现；弱档=纯机械步）〔grill-amendment：推翻"config 段真相源 + SKILL 内联缺省×4"——多处 copy 漂移面〕。**档位映射 MUST 按机队分列**〔add-codex-host-support〕：Claude 机队缺省 opus/sonnet/haiku、Codex 机队缺省 gpt-5.6-sol/gpt-5.6-terra/gpt-5.6-luna（机队锚定，adr/0006(c)——档位是相对执行机队的相对词，不绑单一产品线）。**当前机队 MUST 由 `resolve-models.sh` 按宿主正信号判定**（见能力 `host-adaptive-execution`），编排 skill MUST 引用其导出的 `SDFLOW_TIER_*` 变量。消费仓 `config.yaml` 的 `model-tiers` 段 MUST 仅作可选 per-repo **覆盖**，且 **MUST 按机队分键**〔add-codex-host-support · grill G4 · adr/0024〕：`model-tiers.{claude,codex}.{strong,mid,light}`，`resolve-models.sh` 按当前机队读对应段、无该段回落机队缺省；**扁平旧格式**（`model-tiers.strong: …`）MUST 兼容读作 **Claude 机队**覆盖（历史事实：存量覆盖皆写于 Claude-only 时期），MUST NOT 罢工、MUST NOT 在 Codex 宿主下把 Claude 机队的模型名（如 opus）用于 Codex 机队子代理。编排 skill（sdflow-ship/done/spec-review/code-review/**implement**）的模型选择 MUST 以一句引用指向规则文件与覆盖段，MUST NOT 内联具体模型名。**各编排 skill 的第零步解析 SHALL 语义一致而非逐字一致**，其一致性 SHALL 由机械 parity 守卫对归一化核心段逐字节比对保证〔spec-review-amendment Q5〕。

#### Scenario: 消费仓无覆盖段用 canonical 缺省
- **WHEN** 消费仓 config.yaml 无 model-tiers 段，跑任一编排 skill
- **THEN** skill 按规则根 `model-tiers.md` 中**当前宿主所属机队**的 canonical 缺省档位运行，MUST NOT 报错、MUST NOT 静默降级门禁步模型

#### Scenario: verify 档位来自映射（覆盖优先）
- **WHEN** 消费仓 config.yaml model-tiers 段把强档覆盖为某模型
- **THEN** sdflow-done 的 verify 子代理按覆盖映射选模型；无覆盖时用规则文件中本机队的强档缺省，MUST NOT 落到弱档

#### Scenario: 同一门禁步在两宿主下各取本机队档位〔add-codex-host-support〕
- **WHEN** verify 步分别在 Claude 宿主与 Codex 宿主运行且无 per-repo 覆盖
- **THEN** 前者取 Claude 机队强档、后者取 Codex 机队强档；两者 MUST NOT 因宿主切换而降档（门禁步禁降档是硬约束）

#### Scenario: sdflow-implement 同样引用规则文件取 mid 档

- **WHEN** `sdflow-implement` 派发 implementer/Standards轴/Spec轴/fix 子代理
- **THEN** 均引用规则文件中本机队的 mid 档缺省（或消费仓覆盖），MUST NOT 内联具体模型名，与其余编排 skill 同一套解析路径
