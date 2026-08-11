# 裁决地基改造:机械前置 + 二元裁决替代自报置信硬滤

评审裁决协议不再以镜自报置信 <80 作滤除硬门(sdflow-code-review Step3),改为三层各司其职:① validator 引用真实性复核作机械前置门(机械脚本,逐条核 file:line 存在与引文命中——有确定性信号,按基准 1 优先机械化;不过 ⇒ 落「已裁掉」区留痕);② 对抗裁决二元化(强档,每条 采纳/裁掉/defer + 一句 critique 理由);③ 自报置信保留但降级为排序信号,不再滤除任何条目。severity 保留为输出字段、不作门(同为自报,作门即同一地基病换字段重装)。地基依据:LLM 自报标量置信系统性 overconfident(arXiv 2508.06225),而 critique-then-judge 的二元裁决形态校准显著更好(G-Eval/JudgeLM 一系)。

随数值滤消失,code-review 的跨模型豁免矩阵条款(SKILL Step3「豁免直通」)整体废除——豁免存在的唯一理由是跨模型自评会被同族数值标尺误杀,无数值门即无误杀面。anchor_lint 的合法组合矩阵**保留**:它服务 lens-metric 跨模型性度量,与滤除门无关。

同构边界:spec-review / code-review 只在「裁决动作层」收敛同构(validator 引用核——spec-review 侧核对象为四件套文档+代码——+ 二元裁决 + critique + 无数值滤);spec-review 的「拿不准 → 决策登记区」人门路由保留(与置信数字脱钩)——阶段二有 HARD-GATE、阶段三无人门,是层间真实结构差异,不追求 Step3 条款全文同构。

## Considered Options

- **机械前置 + 二元裁决 + 置信降排序(选中)**:三候选的合成——T112 validator 与 T106 二元裁决本就同 change 同片面,拆开是人为的;引用真实性是唯一有确定性信号的门,自报信号(置信/severity)一律不作门只作排序/字段。代价:强档裁决输入量变大(原 <80 先滤一批),由机械前置先杀引用失实项对冲;归档语料实证数值滤独立击杀本就极少(多数裁掉出自对抗裁决验证性理由),行为面变化小。
- **纯 T106 原案(二元 + critique,validator 另做)**:validator 反正在同 change scope,拆开无收益。
- **severity 三级作门**:自报地基同病,否。
- **维持 <80 硬滤**:地基被文献动摇,跨模型豁免通道已是补丁之上的补丁,否(roadmap design.md 决策 2 方案 B)。

## Consequences

- `sdflow-code-review` Step3 重写:删数值滤与豁免矩阵条款,置信封顶(≤50)条款由 validator 机械核替代;「已裁掉」区留痕语义不变(CONTEXT.md「不得静默丢弃」强化而非削弱)。
- `sdflow-spec-review` Step3 裁决动作层对齐;高/中/低分流的人门路由保留,措辞与置信数字脱钩。
- lens-metric 锚 schema 不动(采纳/裁掉/defer 三计数与二元裁决三态同构,锚本就无置信字段);`lens_metric_emit.py` 输入侧兼容处理。validator 输出遵循消费型信号校验器输出诚实原则(CONTEXT.md「信号内诚实」条目)。
- 验证:部署前历史重放(误杀率红线;噪声重入率因滤除项原文不落盘仅参考)+ 部署后 3-change 前瞻窗口(采纳率方向性偏移归因裁决协议);裁决协议改动独立 commit,可单独 revert。
- 回退 = revert 裁决协议 commit,roster 处置不连带。
