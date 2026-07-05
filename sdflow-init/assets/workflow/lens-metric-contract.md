# lens-metric v1 锚契约（评审价值度量单一权威源）

## 锚形（一行一 (layer,lens,runner,site,轮)）
<!-- sdflow:lens-metric v1 layer="…" lens="…" runner="…" site="…" findings="N" 采纳="N" 裁掉="N" defer="N" 独立="N" sev="致N/高N/中N/低N" -->

## 字段与取值域
- layer ∈ {spec-review, code-review}
- lens  ∈ {domain, adversarial, grounding, history, outside-voice, broad}（canonical 投影；折叠表见 §折叠）
- runner∈ {claude, codex, claude-fallback}
- site  ∈ {code-voice, hr-tg, design-voice, —}（可选消歧，仅 outside-voice，不进 lens enum；非 outside-voice 用 —）
- findings/采纳/裁掉/defer/独立 = int≥0
- sev = 致N/高N/中N/低N（四级定序、零也写 0、分隔符恒 /；仅采纳项计入）

## 归属规则（钉死）
findings/采纳/裁掉/defer 按「哪些镜报过该 finding」归属，共抓则每命中镜各记一次；
独立 仅在「唯一报过 ∧ 被采纳」时 +1；独立在折叠到 lens 类型之后计。
数值跨源一致性 = 主 session 信任边界（自做去重又写锚、自核无独立性），非机械门。

## 折叠表（canonical 投影）
领域镜→domain · 对抗镜1/2/3→adversarial · 接地镜/完整性镜→grounding · 历史镜→history ·
codex(任何 site)/claude-fallback→outside-voice · autoplan(CEO/Eng/DX/design)+gstack-adv→broad

## enum 扩展治理
新增镜类型（enum 未列）MUST 先升版本号至 v2 + 更新折叠表，MUST NOT 静默塞入 broad。

## config 门控
度量落锚受 config.yaml `metrics.enabled` 门控：源仓默认 true / 消费仓默认 false；关闭时不落锚、缺锚不阻塞。

## 示范锚 fence（防聚合器自指误取）
review 报告中如需示范/引用锚语法，MUST 包在 ``` fence 内。
