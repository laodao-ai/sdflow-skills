# lens-metric v1 锚契约（评审价值度量单一权威源）

## 锚形（一行一 (layer,lens,host,runner,site,轮)）〔add-codex-host-support：行键由 (layer,lens,runner,site,轮) 升维，插入 host〕
<!-- sdflow:lens-metric v1 layer="…" lens="…" host="…" runner="…" site="…" findings="N" 采纳="N" 裁掉="N" defer="N" 独立="N" sev="致N/高N/中N/低N" -->

## 字段与取值域
> **机读取值域单一源见下方 `## 机读取值域` 的 ```lens-metric-enums``` 块**——消费脚本（`anchor_lint` 读、`lens_metric_aggregate` 硬编码由一致性测试守卫）MUST 从该块取 layer/lens/host/runner/sev，MUST NOT 在脚本内另复制清单〔mlh-p2-anchor-lint grill〕。以下散文条目为人读语义注记（折叠/消歧说明），取值以机读块为准。**本块同时是 `sdflow:outside-voice` 锚的 `host`/`runner`/`reason_code` 枚举单一源**〔add-codex-host-support：两类锚共用同一份枚举权威，见 design TG-05〕。
- layer ∈ {spec-review, code-review}
- lens  ∈ {domain, adversarial, grounding, history, outside-voice, broad}（canonical 投影；折叠表见 §折叠）
- host  ∈ {claude, codex, unknown}（**谁在跑这次评审**，由 `resolve-models.sh` 按正信号判定；`unknown` = 两个正信号都无）〔add-codex-host-support〕
- runner∈ {claude, codex, none, unknown}（**谁执行了这个镜，只记机队家族**；`claude-fallback` **废弃**——它把跨模型性藏进了枚举值，Codex 宿主下必然说谎，见 §跨模型性。`none` = 该轮无执行〔D6：host-unknown/secret-hit/fallback-unavailable 用之，MUST 伴 `findings=0`〕；`unknown` = `host=unknown` 时普通镜的主审机队，**仅合法于非-outside-voice 普通镜行 ∧ `host=unknown`**——`sdflow:outside-voice` 锚的 `runner` 恒 ∈{claude,codex,none}，不取 `unknown`）〔add-codex-host-support〕
- reason_code ∈ {ok, not-installed, preflight-error, timeout, exec-error, host-unknown, secret-hit, fallback-unavailable}（**仅 `sdflow:outside-voice` 锚必填，`sdflow:lens-metric` 锚无此字段**——本轮 voice 结局：成功跨模型固定哨兵 `ok`〔不复用 `none`，防与 `runner="none"` 词面重载混判〕；同族降级 ∈{not-installed,preflight-error,timeout,exec-error}；无执行 ∈{host-unknown,secret-hit,fallback-unavailable}）〔add-codex-host-support〕
- site  ∈ {code-voice, hr-tg, design-voice, —}（可选消歧，仅 outside-voice，不进 lens enum；非 outside-voice 用 —）
  **〔impl-review-fix CF-补2〕site 仅分组消歧、不纳入越域自检**：任意取值只多一个分组行，不阻塞（与 layer/lens/host/runner/sev
  五个受自检约束的必检字段不同，两 SKILL 的锚行存在性自检 MUST NOT 因 site 值另类而报错）。
- findings/采纳/裁掉/defer/独立 = int≥0
- sev = 致N/高N/中N/低N（四级定序、零也写 0、分隔符恒 /；仅采纳项计入）

### 跨模型性 = 派生量，MUST NOT 编码进枚举值、MUST NOT 简写裸 `runner≠host`〔add-codex-host-support · spec-review-r2 C1〕
「跨模型性」（本轮是否拿到另一机队的真第二意见）SHALL 由**合法组合矩阵**（design TG-05「数据模型与生命周期」段；能力 `host-adaptive-execution`）统一判定：`host,runner 均∈{claude,codex} ∧ runner≠host ∧ reason_code="ok"`。**矩阵的关系式判定逻辑 MUST NOT 落成本文件的可 parse 机读块**——平铺 `key: 逗号分隔值` 结构装不下 `runner≠host`、`findings=0` 这类关系式谓词（r3-narrow 修正）；本文件的机读块**只承载枚举域**，矩阵逻辑由 `anchor_lint` 与 `outside_voice_guard` 各自本地重实现、以全笛卡尔 golden 互相守一致（见 tasks 2.3/4.5）。**MUST NOT 简写为裸 `runner≠host`**——`runner="none"` 时 `none≠host` 恒真，会把一切无执行轮次误判为跨模型（C1 击穿）；矩阵要求 `host,runner` 均落在 `{claude,codex}` 内才谈跨模型。

## 机读取值域（消费脚本单一源·勿在脚本内复制）
> 机读枚举权威区〔mlh-p2-anchor-lint grill〕。格式钉死：fence info-string 恒为 `lens-metric-enums`；块内每行 `key: 逗号分隔值`（`sev-format` 为字面模板，`N` 表任意非负整数）。`site` **不入本块**——它不受越域自检约束（CF-补2），消费脚本 MUST NOT 校验 site 取值。**合法组合矩阵的关系式判定逻辑（`runner≠host`、`findings=0` 等谓词）同样不入本块**——本块只承载**枚举域**，关系式逻辑由 `anchor_lint`/`outside_voice_guard` 各自本地重实现（见上「跨模型性」段、design TG-05）〔add-codex-host-support〕。新增/改枚举 MUST 只改此块（散文注记同步更新），并按 §enum 扩展治理 升版本。
```lens-metric-enums
layer: spec-review, code-review
lens: domain, adversarial, grounding, history, outside-voice, broad
host: claude, codex, unknown
runner: claude, codex, none, unknown
reason_code: ok, not-installed, preflight-error, timeout, exec-error, host-unknown, secret-hit, fallback-unavailable
sev-format: 致N/高N/中N/低N
```

## 归属规则（钉死）
findings/采纳/裁掉/defer 按「哪些镜报过该 finding」归属，共抓则每命中镜各记一次；
独立 仅在「唯一报过 ∧ 被采纳」时 +1；独立在折叠到 lens 类型之后计。
数值跨源一致性 = 主 session 信任边界（自做去重又写锚、自核无独立性），非机械门。
〔mlh-p4〕计数由 `lens_metric_emit.py` 从结构化 findings + 行键 roster 确定性归约产出（非手数）；
「独立在折叠后计」精化为「折叠到**行键 `(lens,host,runner,site)`** 后计」〔add-codex-host-support：行键由
`(lens,runner,site)` 升维，插入 `host`，与锚唯一键 `(layer,lens,host,runner,site,轮)` 对齐——`site` 消同轮多次
outside-voice 调用的撞键，`host` 消同一 runner 在不同宿主下自审 vs 跨模型的撞键〕。

## 折叠表（canonical 投影）
领域镜→domain · 对抗镜1/2/3→adversarial · 接地镜/完整性镜→grounding · 历史镜→history ·
codex/claude(任何 site，任一 runner 的 voice)→outside-voice · autoplan(CEO/Eng/DX/design)+gstack-adv→broad
〔add-codex-host-support：`claude-fallback→outside-voice` 废弃行删除、新增 `claude→outside-voice`——host-adaptive
下反向路径由 `claude` runner 执行 voice 时，原始镜名同样落 `claude`，需与 `codex` 同样折叠到 `outside-voice`〕

## 机读折叠（消费脚本单一源·勿在脚本内复制）〔mlh-p4-lens-metric-emit〕
> 折叠单一源。格式同 `lens-metric-enums`：fence info-string 恒为 `lens-metric-fold`；每行 `原始镜名: canonical-lens`。**只列非恒等映射**——恒等（raw 已 ∈ lens enum，如 domain/grounding/history/broad）由 emitter `raw∈lens_enum` pass-through 承载、不列本块（ADR-7）。canonical 值 MUST ∈ `lens-metric-enums` 的 lens 域（emitter `load_fold` 读入即自校验）。
```lens-metric-fold
对抗镜1: adversarial
对抗镜2: adversarial
对抗镜3: adversarial
领域镜: domain
历史镜: history
接地镜: grounding
完整性镜: grounding
codex: outside-voice
claude: outside-voice
autoplan-ceo: broad
autoplan-design: broad
autoplan-eng: broad
autoplan-dx: broad
gstack-adv: broad
```

## 机读输入 schema（emitter 输入单一权威源·bundle 可达）〔impl-review-fix mlh-p4：ADR-6 落地〕
> `lens_metric_emit.py` 的输入 JSON 权威 schema。两审 SKILL 落锚步引用**本块**（bundle 分发可达，
> 不依赖源仓 `tools/tests/` fixture——消费仓非 full 拷贝不含 tests/）。字段名英文、取值中文。
```lens-metric-input-schema
{
  "roster": [
    {"lens": "<canonical ∈ lens enum>", "runner": "<∈ runner enum>", "site": "<code-voice|hr-tg|design-voice|—>"}
  ],
  "findings": [
    {"hits": [{"raw": "<原始镜名>", "runner": "<outside-voice 时必填>", "site": "<outside-voice 时必填>"}],
     "verdict": "采纳|裁掉|defer", "sev": "致|高|中|低"}
  ]
}
```
> 约束（emitter fail-closed 强制）：① roster 每个 `(lens,runner,site)` 行键各一条（含零-finding 行）；
> 非 outside-voice 普通镜行 MUST `runner==host`（本轮宿主/主审机队，取自 `--host`；`host="unknown"` 时该行
> `runner` 同为 `"unknown"`）、`site="—"`。② finding `hits` 非空；`verdict=采纳` 时 `sev` 必填非空、
> 其余 verdict 若带 sev 也须合法级。③ **无 per-finding `layer`**——锚 layer 单一源 = `--layer`。
> ④ 所有字段类型 MUST 为字符串（非字符串 fail-closed，非静默）。

## enum 扩展治理
新增镜类型（enum 未列）MUST 先升版本号至 v2 + 更新折叠表，MUST NOT 静默塞入 broad。

## config 门控
度量落锚受 config.yaml `metrics.enabled` 门控：源仓默认 true / 消费仓默认 false；关闭时不落锚、缺锚不阻塞。

## 示范锚 fence（防聚合器自指误取）
review 报告中如需示范/引用锚语法，MUST 包在 ``` fence 内。
