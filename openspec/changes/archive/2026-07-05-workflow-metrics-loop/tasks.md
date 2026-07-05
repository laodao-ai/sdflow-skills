# Tasks — workflow-metrics-loop

> 变更性质：workflow bundle 规则 + 两 SKILL 编排指令（Markdown）+ 一个只读聚合脚本（Python + pytest）。
> 优先级承 proposal：P0=锚契约地基 · P1=聚合+独立导出 · P2=反馈+grill 留档。〔grill-amendment：成本维度撤出另立 T29〕
> 每任务 commit 步 MUST 用 `bash ~/.sdflow/hack/checkpoint-commit.sh workflow-metrics-loop:task<N>-<slug>`（命名空间格式，gate 只认本 change 标签）。

## 1. 锚契约权威源（P0）

- [x] 1.1 在 `sdflow-init/assets/workflow/` 下新建 `lens-metric` 锚契约规范（字段/取值域/归属规则/`sev` 子格式定序/版本 `v1` + **enum 扩展治理:新镜升 v2 勿塞 broad**〔SR-E〕），沿用 fence-aware 行级纪律；**契约加 MUST「review 报告中示范锚语法 MUST 包 ``` fence 内」**〔SR-N 闭合自指残差〕 [workflow-metrics: 度量锚契约]
- [x] 1.2 若 bundle 有 INDEX/托管块，登记新规范；确认 `sdflow-init update` 托管刷新覆盖此文件（权威源纪律）[spec-workflow: bundle 权威源]

## 2. 生产者落锚（P0）

- [x] 2.1 `sdflow-code-review/SKILL.md`：Step3 裁决后每镜落 `lens-metric` 锚；现 `voice分桶` prose 行被 outside-voice 镜锚**吸收取代**；报告格式台账区同步；只引用契约字段不复制 [spec-workflow: 评审每镜落度量锚 / workflow-metrics: 度量锚契约]
- [x] 2.2 `sdflow-spec-review/SKILL.md`：Step3 每镜（领域/对抗/接地/outside-voice/broad）落 `lens-metric` 锚；只引用契约不复制 [spec-workflow: 评审每镜落度量锚]
- [x] 2.3 两 SKILL：独立贡献在 Step3 去重时导出（记每条命中镜集合→`独立`标量）；锚存在性自检扩一类（**缺字段 或 `layer/lens/runner/sev` 取值越域 均阻塞**〔SR-C〕；数值一致性是主 session 信任边界、非机械门〔SR-B〕）；spec-review 采纳/裁掉**在设计门拍板回写时最终化**〔SR-M〕；旁路声明（锚有无 MUST NOT 改 findings 判定）[workflow-metrics: 独立贡献导出 / spec-workflow: 旁路不改判定]
- [x] 2.4 机械核对：grep 两 SKILL 全文无残留 `voice分桶` prose 指令、字段清单仅引用权威源 [spec-workflow: 取代 voice 分桶]

## 3. 只读聚合脚本 + 测试（P1，TG-18）

- [x] 3.1 写 `workflow/tools/` 下只读聚合脚本：扫所有 `archive/**/*-review-report.md` 的 `lens-metric` 锚 → 多列可排序表；**字段提取解析器为净新路径**（现有 `_line_scoped_hits` 只做存在性检测），**在本脚本内重实现 ~15 行 fence 核**（`in_fence` 翻转 + 锚独占行前缀 `<!-- sdflow:lens-metric v1` + 受限 kv 提取，**禁裸 `split`/substring**），**MUST NOT 跨 skill import `ship_gate`**；无锚老报告显式计「无锚样本 N，不纳入」；MUST NOT 产合成分、MUST NOT 写新持久文件 [workflow-metrics: 只读聚合 view]
- [x] 3.2 pytest 正例：≥2 归档锚聚合成表，各列取值正确 [workflow-metrics: 只读聚合 view]
- [x] 3.3 pytest 反例矩阵（**镜像 ship_gate fence 用例**）：锚在未闭合/闭合 fenced 代码块内不误取（**含 design 文档式示例锚**）· 措辞漂移 · 字段缺失 · 取值越域 · **`sev` 子格式健壮（省级/乱序/多空格）**〔SR-I〕 · 裸 substring 陷阱均不腐坏解析；无合成分断言 [workflow-metrics: 只读聚合 view]
- [x] 3.4 端到端断言：聚合表 `独立` 列非空（去重导出通路打通）[workflow-metrics: 独立贡献导出]

### 测试覆盖图（TG-18）

| code path | 测试类型 | 用例 |
|---|---|---|
| 锚行解析（fence-aware 行级） | 单元·反例矩阵 | 3.3：漂移/fence/缺字段 |
| 聚合成表（多列排序） | 单元·正例 | 3.2：≥2 锚 |
| 独立列导出端到端 | 集成 | 3.4 |
| 无锚样本计数 | 单元 | 3.3 内含老报告跳过显式计数 |

## 4. 反馈回路 + grill 留档（P2）

- [x] 4.1 泛化反馈：把「累计 10 次采纳率复评」从仅 outside-voice 扩到 per-镜，判据升采纳率+独立率双列；人决声明（回路供数不自动砍镜）[workflow-metrics: 数据驱动反馈]
- [x] 4.1b **surfacing hook（防死列）**〔SR-A〕：给 `/sdflow-maintain` 加机械收尾检查步——只读聚合表、`出现轮数≥10 且未复评` 的镜**显著提示**（不判断不自动砍）；MUST NOT 埋进长报告 [workflow-metrics: 数据驱动反馈]
- [x] 4.1c 〔决策门 Q1=A〕契约加可选 `site` 字段（仅 outside-voice，键升 `(layer,lens,runner,site,轮)`）；两 SKILL 落 outside-voice 锚时按调用位点填 `site`，聚合器解析 `site` 列 [workflow-metrics: 度量锚契约]
- [x] 4.1d 〔决策门 Q2=A〕`config.yaml` 度量开关（源仓默认 on / 消费仓默认 off）；两 SKILL 落锚+自检受其门控（关闭时不落锚不阻塞）；契约规范记默认值 [spec-workflow: 度量落锚 config 门控]
- [x] 4.2 grill 层不纳入：确认两 SKILL 不给 grill 落锚；把 grill「amendment 下游存活率」度量作**独立 deferred item** 写入 `openspec/issues/todolist`——明写「口径未定义（amendment 无 ID/无 ground truth 链接）、需自己的 explore、非本 change；裸数条数是误导指标不采；归 workflow-metrics-loop 伞下与 T29 并列」 [workflow-metrics: grill 留档边界] [/sdflow-todolist]

> 〔grill-amendment〕原 4.2「镜级 dur_s」任务已删——成本维度撤出另立 T29（per-镜 dur_s 无诚实数据源，见 design ADR-3）。T29 另立标准见本次 grill 调研结论（记入 todolist T29）。

## 5. delta 复核 + 部署

- [x] 5.1 按代码实况核 `specs/workflow-metrics/spec.md` + `specs/spec-workflow/spec.md` delta 与六落点措辞一致；`openspec validate workflow-metrics-loop` 通过 [全需求]
- [x] 5.2 开发 checkout 跑 `bash setup.sh`（改 `assets/workflow` 才让全局 canonical 生效、测得到）[spec-workflow: bundle 权威源]
