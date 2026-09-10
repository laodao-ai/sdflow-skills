# 演进依据与历史取舍

> 仅在审计历史取舍时读取。本文不参与默认阶段二执行。

## 1. 单批全并行 dispatch 取代两段串行（DD1/T20）

旧版评审流程分两段：外部广审工具产出 amendment 落盘，再由 spec-review 各自出报告、人工手动合并；
之后演进为「Step1 广审 → Step2 多镜」两段串行 dispatch——领域镜/对抗镜须等外部广审产出的 amendment
落盘才能起跑（旧「串行纪律〔T20〕分治」）。

当前设计（DD1）：广审（strategy/plan-eng）不再是外部工具原生执行，而是本 skill 自持的两个 fresh
子代理镜，与领域镜/对抗镜/接地镜/design-voice 同批一条消息内并行派出，互不依赖——新广审镜只回结构化
findings、不改盘面，等待理由随之消失。旧串行纪律与旧两段独立 checkpoint 一并退役。旧广审锚枚举
`mode="native|simulated"` 与广审产物独立落盘、复用判定机制随之整体删除，现枚举收窄为
`mode="subagent|main-session"`。

## 2. design-voice 复用守卫退役（DD3）

旧版 design-voice 是否触发经 `outside_voice_guard.py` 判定——调用广审产物落盘状态决定是否复用上一轮
结果，避免重复调用。DD3 将该回落路径转正：design-voice 现恒自跑（本步单批 dispatch 内一并派出），
复用守卫机制整体退役，不再需要额外的复用判定环节。

## 3. 数值置信滤退役对齐（与 sdflow-code-review 同期）

本层（spec-review）历史上从未有过数值置信滤门槛——决策登记区的路由判据一直是「是否真拿不准」而非
任何置信数字。该结论与 `sdflow-code-review` 同期把其自身的数值滤 + 跨模型豁免矩阵一并退役对齐，
此处只是显式重申既有事实，不代表本层曾经存在过、后又移除的门槛。
