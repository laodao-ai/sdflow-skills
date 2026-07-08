# lens-metric v1 锚契约（评审价值度量单一权威源）

## 锚形（一行一 (layer,lens,runner,site,轮)）
<!-- sdflow:lens-metric v1 layer="…" lens="…" runner="…" site="…" findings="N" 采纳="N" 裁掉="N" defer="N" 独立="N" sev="致N/高N/中N/低N" -->

## 字段与取值域
> **机读取值域单一源见下方 `## 机读取值域` 的 ```lens-metric-enums``` 块**——消费脚本（`anchor_lint` 读、`lens_metric_aggregate` 硬编码由一致性测试守卫）MUST 从该块取 layer/lens/runner/sev，MUST NOT 在脚本内另复制清单〔mlh-p2-anchor-lint grill〕。以下散文条目为人读语义注记（折叠/消歧说明），取值以机读块为准。
- layer ∈ {spec-review, code-review}
- lens  ∈ {domain, adversarial, grounding, history, outside-voice, broad}（canonical 投影；折叠表见 §折叠）
- runner∈ {claude, codex, claude-fallback}
- site  ∈ {code-voice, hr-tg, design-voice, —}（可选消歧，仅 outside-voice，不进 lens enum；非 outside-voice 用 —）
  **〔impl-review-fix CF-补2〕site 仅分组消歧、不纳入越域自检**：任意取值只多一个分组行，不阻塞（与 layer/lens/runner/sev
  四个受自检约束的必检字段不同，两 SKILL 的锚行存在性自检 MUST NOT 因 site 值另类而报错）。
- findings/采纳/裁掉/defer/独立 = int≥0
- sev = 致N/高N/中N/低N（四级定序、零也写 0、分隔符恒 /；仅采纳项计入）

## 机读取值域（消费脚本单一源·勿在脚本内复制）
> 机读枚举权威区〔mlh-p2-anchor-lint grill〕。格式钉死：fence info-string 恒为 `lens-metric-enums`；块内每行 `key: 逗号分隔值`（`sev-format` 为字面模板，`N` 表任意非负整数）。`site` **不入本块**——它不受越域自检约束（CF-补2），消费脚本 MUST NOT 校验 site 取值。新增/改枚举 MUST 只改此块（散文注记同步更新），并按 §enum 扩展治理 升版本。
```lens-metric-enums
layer: spec-review, code-review
lens: domain, adversarial, grounding, history, outside-voice, broad
runner: claude, codex, claude-fallback
sev-format: 致N/高N/中N/低N
```

## 归属规则（钉死）
findings/采纳/裁掉/defer 按「哪些镜报过该 finding」归属，共抓则每命中镜各记一次；
独立 仅在「唯一报过 ∧ 被采纳」时 +1；独立在折叠到 lens 类型之后计。
数值跨源一致性 = 主 session 信任边界（自做去重又写锚、自核无独立性），非机械门。
〔mlh-p4〕计数由 `lens_metric_emit.py` 从结构化 findings + 行键 roster 确定性归约产出（非手数）；
「独立在折叠后计」精化为「折叠到**行键 `(lens,runner,site)`** 后计」。

## 折叠表（canonical 投影）
领域镜→domain · 对抗镜1/2/3→adversarial · 接地镜/完整性镜→grounding · 历史镜→history ·
codex(任何 site)/claude-fallback→outside-voice · autoplan(CEO/Eng/DX/design)+gstack-adv→broad

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
完整性接地镜: grounding
codex: outside-voice
claude-fallback: outside-voice
autoplan-ceo: broad
autoplan-design: broad
autoplan-eng: broad
autoplan-dx: broad
gstack-adv: broad
```

## enum 扩展治理
新增镜类型（enum 未列）MUST 先升版本号至 v2 + 更新折叠表，MUST NOT 静默塞入 broad。

## config 门控
度量落锚受 config.yaml `metrics.enabled` 门控：源仓默认 true / 消费仓默认 false；关闭时不落锚、缺锚不阻塞。

## 示范锚 fence（防聚合器自指误取）
review 报告中如需示范/引用锚语法，MUST 包在 ``` fence 内。
