# spec-workflow Specification (Delta)

## MODIFIED Requirements

### Requirement: 阶段三过设计门后连续自动跑到 merge

阶段三 SHALL 在阶段二设计门之后无任何阻塞人类门地连续运行 `实现管线 → sdflow-code-review → sdflow-done`；实现管线为可选双轨——缺省 `writing-plans → subagent-dev`，或经 `impl-orchestration` 能力的手动路由（config 键 + 盘面 marker，缺省/非法值一律 superpowers）选择 `sdflow-implement 双模式（出 ticket → 执行）`；**编排层入口 = `/sdflow-ship`**（一次调用驱动 5.5→9，按「阶段三编排台账确定性」需求经 ship_gate 推进；手动逐步仍为合法 reference 路径）。管线选择 MUST NOT 引入模型自动判断，MUST NOT 新增人类门。能修的自动修；**遇 ≥2 方案 MUST 按三级决策协议**〔T10，替换旧"有把握自动选"自评表述〕：①有客观判据（测试/断言/基准可判）→ 自动选并记理由；②无客观判据 → 派对抗镜复核推荐项，通过方自动选（复核记录进报告）；③复核不过或无从复核 → defer 进 buglist/todolist 并由 hand-off 引导另开 change 清理。MUST NOT 以自评置信（"有把握"）作为自动选定的唯一依据。修不了或需拍板的 MUST 进 buglist/todolist 延后。

#### Scenario: 修不了的问题延后而非阻塞

- **WHEN** sdflow-code-review 发现一个本 change 修不掉的问题
- **THEN** 它进 buglist/todolist(defer) 并写入 hand-off，流程继续跑到 sdflow-done，不设人类门阻塞

#### Scenario: 无客观判据的两方案走对抗复核

- **WHEN** 阶段三某步遇两个可行方案且无测试/断言可判优劣
- **THEN** 派对抗镜尝试证伪推荐方案：未被证伪 → 自动选并记复核记录；被证伪或复核无法开展 → defer，MUST NOT 凭"有把握"直接选

#### Scenario: 一次调用驱动到 merge 建议

- **WHEN** 对已过设计门的 change 调用 /sdflow-ship 且各步门禁全通过
- **THEN** 链依 gate 判定逐步推进至 sdflow-done 完成（含 merge 缺省语义），输出最终摘要；全程无 AskUserQuestion

#### Scenario: ship 零 git 写操作、merge 意图透传〔grill-amendment〕

- **WHEN** 用户以"跑到 merge 前停"类意图调用 /sdflow-ship
- **THEN** ship 将 opt-out 原样透传给 sdflow-done（merge 由 done 一处执行/跳过）；ship 自身 MUST NOT commit/merge/push，MUST NOT 自动 push（摘要提醒手动 push；toolkit 源仓附激活提示）

#### Scenario: 实现管线按手动确定值路由

- **WHEN** gate 判定 RUN_PLAN 且 config 键值为 `tickets`
- **THEN** ship 派发 sdflow-implement 出 ticket 模式；键缺省/非法/为 superpowers 时派发 writing-plans，行为与本变更前一致；CONTINUE_IMPL 一律按 plan 文件 marker 路由

## ADDED Requirements

### Requirement: 阶段一讨论按雾量三段分流并约定 wayfinder→ff 衔接契约

阶段一入口 SHALL 按讨论雾量三分：问题清晰 → 直接 `opsx:ff`；单 session 可收敛的模糊 → `/opsx:explore`；预估超单 session 的大雾 → wayfinder chart 铺图逐 ticket 决议。wayfinder 收敛后接 ff SHALL 遵守衔接契约三条：① ff 起手逐区读 map——Destination 喂 proposal 动机与 Success Metrics（D-5）、Decisions-so-far 逐 ticket zoom 到决议全文（MUST NOT 只读 map 摘要行，防 ff「prefer making reasonable decisions」对已决项重新决歪）、Out-of-scope 喂 Non-Goals 可证伪假设（D-3）；② TG 判命中 SHALL 前置到 chart 阶段写入 map Notes；③ proposal SHALL 回链 map 供溯源。

#### Scenario: 大雾讨论走 wayfinder 后 ff 不重决已决项

- **WHEN** 某议题经 wayfinder 多 ticket 决议收敛、随后触发 opsx:ff
- **THEN** ff 生成的 design 决策与 map Decisions-so-far 指向的决议全文一致；已决项不出现「合理重新决策」的偏移

#### Scenario: 清晰问题不强制前置讨论

- **WHEN** 需求边界与方案在触发时已清晰
- **THEN** 直接 opsx:ff，不强制 explore/wayfinder 仪式

### Requirement: grill 对上游已决分支瘦跑

grill（阶段一对抗压测步）SHALL 对上游 wayfinder 已决分支瘦跑：引用该 ticket resolution 快速核对（决议是否仍与代码 ground truth 一致）即过，MUST NOT 对已决内容重复全深度死磕；ff 新生成或未经上游决议的部分 SHALL 照常全深度死磕。grill 对象是 ff 烘焙产物 vs 代码 ground truth，与 wayfinder grilling ticket（生成前决策拷问）非冗余，MUST NOT 因上游已跑 grilling 而整跳 grill。

#### Scenario: 已决分支快速核对

- **WHEN** grill 遇到 design.md 中某决策、其在 map 有对应 resolved ticket
- **THEN** 引 resolution 核对决议与代码事实仍一致后放行该分支，转入未决分支死磕

#### Scenario: 无上游决议时不瘦跑

- **WHEN** change 未经 wayfinder（直接 ff 或仅 explore）
- **THEN** grill 按既有全深度口径执行，无瘦跑路径
