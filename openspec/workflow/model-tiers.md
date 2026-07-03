# model-tiers — 模型档位映射（单一真相源）

> 机队锚定〔adr/0006(c)〕：档位是**相对执行机队**的相对词（机队会换血），不绑具体产品名。
> 消费仓覆盖：`openspec/config.yaml` 的 `model-tiers` 段仅作 per-repo 覆盖映射，缺省勿填。
> 编排 skill 一律以一句引用指向本文件，MUST NOT 内联模型名。

| 档位 | 职责（谁必须用它） | canonical 缺省 |
|---|---|---|
| **强档 strong** | verify 终门 / 对抗裁决（Step3 主审）/ final whole-branch 终审 | opus |
| **中档 mid** | 领域镜·对抗镜（判断/对抗推理）/ 生成 / 实现 / archive 对码 | sonnet |
| **弱档 light** | 纯机械步：接地镜 grep 核验 / 历史镜 / 置信打分 / commit message | haiku |

铁律：带门禁、无人逐条复核的步 MUST NOT 降档（假绿会放不完整的活过关）；
纯机械步可下放弱档（失败可重试、无判断权重）。
