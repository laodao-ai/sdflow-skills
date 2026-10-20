# model-tiers — 模型档位映射（单一真相源）

> 机队锚定〔adr/0006(c)〕：档位是**相对执行机队**的相对词（机队会换血），不绑具体产品名。
> 当前机队由 `resolve-models.sh` 按宿主正信号判定（见能力 `host-adaptive-execution`）。
> 消费仓覆盖：`openspec/config.yaml` 的 `model-tiers` 段仅作 per-repo 覆盖映射，**按机队分键**
> `model-tiers.{claude,codex}.{strong,mid,light}`；扁平旧格式（`model-tiers.{strong,mid,light}`）
> 兼容读作 Claude 机队覆盖，在 Codex 宿主下不生效（回落 Codex 机队缺省，MUST NOT 把 Claude
> 模型名塞给 Codex 机队）。缺省请勿填。
> 编排 skill 一律以一句引用指向本文件，MUST NOT 内联模型名。

| 档位 | 职责（谁必须用它） | Claude 机队缺省 | Codex 机队缺省 | effort 档 |
|---|---|---|---|---|
| **强档 strong** | verify 终门 / 对抗裁决（Step3 主审）/ final whole-branch 终审 | opus | gpt-6-astra | high |
| **中档 mid** | 领域镜·对抗镜（判断/对抗推理）/ 生成 / 实现 / archive 对码 | sonnet | gpt-6.1-sol | medium |
| **弱档 light** | 纯机械步：接地镜 grep 核验 / 历史镜 / 置信打分 / commit message | haiku | gpt-6-luna | low |

铁律：带门禁、无人逐条复核的步 MUST NOT 降档（假绿会放不完整的活过关）；
纯机械步可下放弱档（失败可重试、无判断权重）。

## 主 session 档位（resolver 不切换主 session）

`resolve-models.sh` 只解析**子代理**的档位，不切换主 session 的模型与 effort。
`/sdflow-spec-review`、`/sdflow-code-review`（含经 `/sdflow-ship` 调度）的主 session 承担门禁裁决，
MUST 运行在当前宿主机队的 strong 档模型上，effort MUST NOT 低于 high。

| 宿主 | 进入阶段二 / 阶段三前的动作 |
|---|---|
| Claude Code | `/model` 切到 `claude.strong` |
| Codex | `/model` 切到 `codex.strong`，reasoning effort 选 `codex.strong` 对应档（不低于 high）。`~/.codex/config.toml` 的 `model` / `model_reasoning_effort` 只是主 session 缺省，低于此档时须手动切 |

诚实边界：主 session 无法可靠自检当前模型，本条是给人的提示，不是机械门。

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
codex.strong: gpt-6-astra
codex.mid: gpt-6.1-sol
codex.light: gpt-6-luna
```

## 机读缺省 · effort 维（消费脚本单一源·勿在脚本内复制）

> effort 是宿主派发的独立维度。Claude 值域为 `low/medium/high/xhigh/max`；Codex 值域额外支持
> `ultra`。格式钉死同上方 `model-tier-defaults` 惯例：fence info-string 恒为
> `effort-tier-defaults`；键路径固定 6 条（2 机队 × 3 档，可穷举）
> ——`resolve-models.sh` 按同款有界键路径行锚定提取，MUST NOT 长成通用解析器（基准 5）。
> 与上方表格「effort 档」列同源，两处 MUST NOT 漂移。

```effort-tier-defaults
claude.strong: high
claude.mid: medium
claude.light: low
codex.strong: high
codex.mid: medium
codex.light: low
```
