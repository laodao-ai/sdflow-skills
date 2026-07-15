# model-tiers — 模型档位映射（单一真相源）

> 机队锚定〔adr/0006(c)〕：档位是**相对执行机队**的相对词（机队会换血），不绑具体产品名。
> 当前机队由 `resolve-models.sh` 按宿主正信号判定（见能力 `host-adaptive-execution`）。
> 消费仓覆盖：`openspec/config.yaml` 的 `model-tiers` 段仅作 per-repo 覆盖映射，**按机队分键**
> `model-tiers.{claude,codex}.{strong,mid,light}`；扁平旧格式（`model-tiers.{strong,mid,light}`）
> 兼容读作 Claude 机队覆盖，在 Codex 宿主下不生效（回落 Codex 机队缺省，MUST NOT 把 Claude
> 模型名塞给 Codex 机队）。缺省请勿填。
> 编排 skill 一律以一句引用指向本文件，MUST NOT 内联模型名。

| 档位 | 职责（谁必须用它） | Claude 机队缺省 | Codex 机队缺省 |
|---|---|---|---|
| **强档 strong** | verify 终门 / 对抗裁决（Step3 主审）/ final whole-branch 终审 | opus | gpt-5.6-sol |
| **中档 mid** | 领域镜·对抗镜（判断/对抗推理）/ 生成 / 实现 / archive 对码 | sonnet | gpt-5.6-terra |
| **弱档 light** | 纯机械步：接地镜 grep 核验 / 历史镜 / 置信打分 / commit message | haiku | gpt-5.6-luna |

铁律：带门禁、无人逐条复核的步 MUST NOT 降档（假绿会放不完整的活过关）；
纯机械步可下放弱档（失败可重试、无判断权重）。

## 机读缺省（消费脚本单一源·勿在脚本内复制）

> 格式钉死同 `lens-metric-contract.md` 机读块惯例：fence info-string 恒为
> `model-tier-defaults`；块内每行 `<fleet>.<tier>: <model-id>`，键路径固定 6 条
> （2 机队 × 3 档，可穷举）——`resolve-models.sh` 按有界键路径行锚定提取本块，
> MUST NOT 把此解析长成通用 YAML/Markdown 解析器（基准 5）。新增机队/档位 MUST
> 只改本块（上方表格同步更新，两处 MUST NOT 漂移）。

```model-tier-defaults
claude.strong: opus
claude.mid: sonnet
claude.light: haiku
codex.strong: gpt-5.6-sol
codex.mid: gpt-5.6-terra
codex.light: gpt-5.6-luna
```
