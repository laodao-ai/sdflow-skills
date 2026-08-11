## Why

wco roadmap 阶段 2：13 面评审镜达到待复评轮数阈值（≥10 轮）却从未有过砍留拍板——决策端欠账；同时 code-review Step3 的裁决硬门建立在镜自报置信 <80 上，而 LLM 自报置信被证明系统性 overconfident（arXiv 2508.06225），豁免矩阵已是补丁摞补丁。阶段 1 判据（实修率 + token 维）已交付，复评与裁决地基改造同片一致性面，一次做完（roadmap 阶段 2 / design.md 决策 1、2）。

## What Changes

- **镜 roster 复评**：按独立率（主判据，实修率仅 2/13 面达样本量阈值，decision-memo D1）+ 人工复核对 13 面待复评镜逐一拍板（保留 / 降采样 / 淘汰），产出处置表；降采样 = SKILL roster 段条件化派发，条件限 dispatch 时机械可判信号（D6）。
- **裁决协议改造**（`adr/0041`）：validator 引用真实性复核作机械前置门（弱档）→ 二元裁决 采纳/裁掉/defer + critique（强档）→ 自报置信降级为排序信号；**BREAKING**：code-review Step3 数值 <80 滤除与跨模型豁免矩阵条款废除（anchor_lint 合法组合矩阵保留，只服务度量）。spec-review / code-review 仅在裁决动作层同构，spec-review 人门路由保留（D5）。
- **处置记录机械落点**：新增处置记录文件 + `retro_report.py` 读取后对已处置镜在待复评区块行内注记（decision-memo C8，验收标准隐含范围）。
- **lens-metric emitter 输入 schema 兼容** + retro 再生冒烟（锚 schema 不动，C6）。
- **sdflow-done 终态 token 快照**：收尾流程复用 `token_snapshot.py` 补采最后一次 checkpoint 之后的用量（收尾占墙钟 27%，尾巴系统性缺失；D4）。
- **dogfood 双轨验证**（D3）：部署前历史重放（3-5 份归档报告，误杀率红线）+ 部署后 3 个真实 change 前瞻窗口（漏检归 roster、采纳率偏移归裁决协议）。

## Capabilities

### New Capabilities

（无——处置记录并入 workflow-retro 能力面。）

### Modified Capabilities

- `spec-workflow`: **BREAKING**〔spec-review-amendment：与 What Changes 标记一致〕Step3 裁决协议 Requirement 变更——置信过滤豁免条款（现 spec「置信过滤豁免 SHALL 按合法组合矩阵…」及其 Scenario）整体替换为「机械前置 + 二元裁决 + 置信降排序」；镜 roster 支持条件化派发（降采样语义）。
- `workflow-retro`: 待复评区块新增处置记录消费——已处置镜行内注记处置结果，未处置镜照旧 flag。
- `token-snapshot-anchor`: 新增 done 收尾终态快照采集点（同口径、同锚文件、失败显式降级不挡收尾）。

## Impact

- 改动面：`sdflow-code-review/SKILL.md`（Step3 重写 + roster 段）、`sdflow-spec-review/SKILL.md`（裁决动作层对齐 + roster 段）、`sdflow-retro/scripts/retro_report.py`（处置注记）、`sdflow-done/SKILL.md`（终态快照接线）、新 validator 复核脚本或条款、处置记录文件、`sdflow-init/assets/workflow/` 相关规则（bundle 权威源先改，`sdflow-init update` 推下游）。
- 不动面：lens-metric 锚 schema（C6）、anchor_lint 合法组合矩阵（C7）、冷主审 / 冷全 diff 层（C1 护栏）。
- 栈：Markdown 指令 + Python 脚本，不命中 TG-01/02/03 领域清单。
- 回滚：roster 与裁决协议改动落独立 commit，可分别 revert（C3）。

## Success Metrics

- retro 报告待复评区块：13 面镜逐镜带处置注记（或清空）。
- 历史重放：误杀率红线〔设计门 Q2〕——重裁不一致项三类归因（①历史误标/口径漂移 ②模型方差 ③协议缺陷），③类（协议缺陷）= 0 才可部署；①②类如实报数不挡部署。
- 前瞻窗口（roadmap 层残项，不阻塞归档）：3 个真实 change 内漏检归因 roster 的缺陷 = 0；采纳率无持续方向性劣化（对照 retro 基线 code-review ~73% / spec-review ~87-93%）。
- 全仓 pytest 绿；anchor_lint 全绿。

## Non-Goals

- 不动冷主审 / 冷全 diff 层（C1）。
- 不做评审编排大改（Workflow 原语 / Stop hook 阶梯——T276 绑定触发条件另行重估，design.md 决策 4）。
- 不放宽实修率归属文法提覆盖率（D1）。
- 不做逐镜 token 机械承诺（wco P2 既有结论，harness 无 per-子代理 token）。
- 阶段 3/4/5 内容（上游吸收、effort 分档、人类门减负）不进本 change。

## Compliance

N/A（仓内工具链与流程规则改造，无外部合规面）。

## 需求优先级〔TG-19〕

- **P0**：裁决协议改造（adr/0041 落地：validator 前置 + 二元裁决 + 豁免矩阵废除）+ 历史重放验证——地基件，roster 复评的 dogfood 判读依赖新协议先站住。
- **P1**：13 面镜 roster 复评处置表 + 降采样条件化派发 + 处置记录机械落点（C8）。
- **P2**：sdflow-done 终态 token 快照（D4）+ emitter 输入兼容冒烟（2.A.4）。

## 假设〔TG-22〕

- **A1（承 roadmap 假设 A1）**：独立率 + 人工复核足以支撑 11 面未达实修率阈值镜的处置拍板。失效影响：误杀镜——由「弱产出镜优先降采样而非淘汰」+ 前瞻窗口 + 独立 commit revert 三层兜底。
- **A2**：归档报告的采纳/defer findings（file:line + 描述）足以支撑重放的 validator 引用核 + 二元重裁（C4 已实核三份样本）。失效影响：重放降级为部分样本，如实标注覆盖数。
- **A3**：删数值滤的行为面变化小（C4 实证：数值滤独立击杀项在样本中极少）。失效影响：误杀率红线在重放中暴露，部署前即拦住。

## 开放问题〔TG-21〕

以下三项均为**本 change design 相位内定案**（负责人 = design 相位，截止 = design.md 定稿）：

- 处置记录文件的格式与位置（C8）。
- 「按条件跳过」在 lens-metric 锚上的表达：复用 `runner="none"` 还是新 reason_code（D6）。
- 终态 token 快照的落盘位置与 anchor 标记（D4：archive 随件还是 token-log 追加）。

## 成本估算〔TG-24〕

历史重放为一次性 LLM 成本：3-5 份报告 ×（机械脚本引用核〔零 LLM 成本，design DD4 已由弱档模型升格为纯脚本，spec-review-amendment〕+ 强档二元重裁），量级 = 3-5 份报告的等量强档裁决，一次性、不进常驻成本。前瞻窗口复用正常评审轮，无增量成本。终态快照为本地脚本，零 LLM 成本。
