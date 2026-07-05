# per-agent/per-lens 计时不可行：harness 不暴露 subagent duration，时长度量只能取 phase-grain（checkpoint 时间戳）

任何「记录子代理/评审镜耗时」的设想都撞同一堵墙：**本 harness（Claude Code）的 Agent 工具只把子代理最终文本回给主 session，不暴露结构化 `duration_ms`/`usage`**。关键实证（workflow-metrics-loop grill 2026-07-06）：全仓 grep `duration_ms`/`usage` 零捕获——从没有任何 SKILL/脚本/报告取到过子代理耗时；`usage` 命中全是 `outside-voice.sh` 的 help 函数。且评审镜是**一条消息内并行 fan-out**（一次 start / 一次 end 整批返回），主 session 即便自己掐墙钟也无法按镜隔离；子代理自报耗时不可靠（不含排队、掐不准自身起点、可造假）。据此确立：**per-agent / per-lens 计时在本 harness 不可行**，凡「时长/成本」度量只能退到 **phase-grain**——用 checkpoint commit 时间戳序列（`git log %ct`，该数据源真实存在、盘面即状态）推各阶段墙钟。

派生铁律：

- **(a) 幻影字段不入契约**：MUST NOT 在度量锚/schema 里放填不出诚实值的字段（如 per-agent `dur_s`）——它只会变成永远 `unknown` 的死列或诱导假数据污染聚合。workflow-metrics-loop 据此从 `lens-metric v1` 砍除 `dur_s`。
- **(b) 时长是墙钟非计算**：checkpoint 时间戳差含会话空闲/排队，git 无法恢复纯计算时长——度量措辞 MUST 声明「墙钟 elapsed」，**只信 N-change 聚合均值**（空闲噪声回归均值），单 change 数只作离群标记。
- **(c) 人类门须锚定剔除**：phase-grain 墙钟含人类门等待（grill 对话、设计门拍板）——MUST 按步类型 + 机器锚（`checkpoint(grill)` 类、`<!-- ship-gate: design-approved -->` 区间）单列剔除，绝不并进层成本；判据用锚定非 subject 文本（防脆弱）。

## Considered Options

- **phase-grain 墙钟（checkpoint 时间戳）+ 诚实声明（选中）**：唯一真实存在的数据源，零新插桩，盘面即状态。代价 = 粒度只到层/阶段（到不了镜/agent），且是墙钟非计算成本——但对「该不该留这**层**」够用。
- **硬撑 per-agent dur_s（子代理自报 / 主 session 掐表）**：未选——自报不可靠且并行 fan-out 无法按镜隔离；把不可信数写进契约违反"盘面即状态/堵假数据"。
- **给 harness 加 turn 级时间戳插桩**：未选（本轮）——需改 harness 能力、超出仓控范围；若将来 harness 暴露 duration 可重启该路径。

## Consequences

- **workflow-metrics-loop 落地本 ADR**：该 change 做**纯价值度量**（per-lens findings/裁决/独立/严重度），成本维度（原 T29）撤出**另立**，用 phase-grain checkpoint 时间戳 + 人类门锚剔除（标准见 todolist T29 grill 调研定稿）。
- **价值度量 vs 成本度量粒度分界**：价值 = per-lens（报告锚导出），成本 = per-phase/层（git log 导出）；二者数据源与粒度不同，**不能相除成 per-lens value/cost 比**。
- **与 adr/0006 同系**：均属「workflow 不押上游理想假设」哲学——0006 不押"强模型"、0008 不押"分支纪律"、本 ADR 不押"harness 会给 duration"。
- **CONTEXT.md 补术语**：独立贡献 / 价值度量·成本度量粒度分界。
