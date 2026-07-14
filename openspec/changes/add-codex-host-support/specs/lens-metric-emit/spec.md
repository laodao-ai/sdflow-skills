## MODIFIED Requirements

### Requirement: lens-metric 计数由确定性 emitter 从结构化 findings 归约

lens-metric 锚的计数（`findings`/`采纳`/`裁掉`/`defer`/`独立` + `sev` rollup）SHALL 由确定性脚本 `lens_metric_emit.py` 归约，MUST NOT 再由主 session 手数手写。所有计数 SHALL 以**行键 `(lens, host, runner, site)`** 为单位、与锚落锚键一致〔add-codex-host-support：由 `(lens,runner,site)` 升维加 `host`；锚唯一键相应为 `(layer,lens,host,runner,site,轮)`，layer=`--layer` 单一源、轮=一次 emit〕。

emitter SHALL 接受 **`--host`** 参数（取值 `claude|codex|unknown`，由调用方从 `resolve-models.sh` 的 `SDFLOW_HOST` 传入），作为本轮所有行的 `host` **单一源**——**MUST NOT** 有 per-finding 或 per-roster-row 的 `host`〔add-codex-host-support：与 `--layer` 同构；一轮评审只有一个宿主，per-row host 会制造无意义的自相矛盾态〕。

emitter 的**输入** SHALL 含两部分，字段名按契约权威 input schema（英文键名，取值中文）〔spec-review-amendment ADR-6〕：
- ① `roster`：`(lens,runner,site)` **行键**列表，本轮跑过的每个行键各一条（含零-finding 行）；非 outside-voice 行 `site="—"` 且 `runner` 取当前 host（主审自己的机队），outside-voice 行显式带 `runner`∈{claude,codex} 与 `site`∈{code-voice,hr-tg,design-voice}。
- ② `findings`：每条携带 `hits`（命中行的引用列表，每 hit 带原始镜名 `raw` + outside-voice 命中时的 `runner`/`site`）、裁决 `verdict`∈{采纳,裁掉,defer}、严重度 `sev`∈{致,高,中,低}（`verdict==采纳` 时必填非空）。**无 per-finding `layer`、无 per-finding `host`**〔layer/host 均为 CLI 单一源〕。

emitter SHALL 按 `lens-metric-contract.md` 的 **`lens-metric-fold` 机读块** 折叠每 hit 的 `raw`→canonical `lens`：`fold(raw)= raw if raw∈lens_enum（恒等 pass-through）; elif raw∈fold_map; else fail-closed`〔spec-review-amendment ADR-7〕，得行键 `(lens, host, runner, site|—)`；按**归属规则**（`findings/采纳/裁掉/defer` 每命中**行键**各记一次；`独立` 仅「去重行键集 size==1 ∧ 被采纳」时 +1）逐行键归约，**为 `roster` 中每个行键恒输出一行**字段齐全（含 `host`）、取值在域内、`sev` 子格式为 `致N/高N/中N/低N`（仅采纳项计入、零也写 0、分隔恒 `/`）的合规锚行。

emitter SHALL 只做机械归约，MUST NOT 做去重（是否同一 finding）、对抗裁决、严重度定级——这三者 SHALL 保留给模型/主 session（产出结构化输入）。emitter SHALL **门控外置**——不读 config，被调即视 metrics-on〔spec-review-amendment ADR-10：门控归 SKILL 层〕。emitter **MUST NOT 自行判定宿主**——`host` 一律由 `--host` 传入〔add-codex-host-support：宿主判定的单一实现在 `resolve-models.sh`，emitter 再判一次即第二个实现 = 漂移面〕。

#### Scenario: 结构化 findings 归约出合规锚与计数
- **WHEN** 主 session 把一轮已裁决的 `roster`（行键列表）+ 结构化 findings（每条带 `hits`/`verdict`/`sev`）+ `--host <本轮宿主>` 喂给 `lens_metric_emit`
- **THEN** emitter SHALL 按折叠表 + 归属规则逐**行键**输出一行合规 lens-metric 锚（每行带同一个 `host`），计数与所给输入一致、`sev` 仅计采纳项、`独立` 按去重行键集计

#### Scenario: 共抓 finding 每命中行各记但不计独立
- **WHEN** 一条被采纳的 finding 的 `hits` 折叠出 `(domain,claude,—)` 与 `(outside-voice,codex,hr-tg)` 两行键（host=claude）
- **THEN** emitter 归约后此两行的 `采纳` 各 +1，两者 `独立` 均 SHALL NOT +1（行键集 size≥2、非唯一贡献）

#### Scenario: 同类型多实例折叠到同一行键仍算独立〔spec-review-amendment ADR-8〕
- **WHEN** 一条被采纳的 finding 的 `hits` 原始镜名为 `对抗镜1` 与 `对抗镜2`
- **THEN** emitter 折叠后二者同为行键 `(adversarial, host, host, —)`、去重后集 size==1 → 该行 `独立` +1（保「同类型多实例算独立」）

#### Scenario: 折叠恒等 pass-through 与非恒等映射〔spec-review-amendment ADR-7〕
- **WHEN** 输入 hit 的 `raw` 为 `domain`（∈lens_enum）或 `对抗镜2`/`完整性镜`/`codex`/`claude`（非恒等 outside-voice runner 名）
- **THEN** emitter SHALL 对 `domain` 恒等直通、对其余分别折叠为 `adversarial`/`grounding`/`outside-voice`，MUST NOT 产出枚举外 `lens` 值；未在 lens_enum 且未在 fold_map 的未知 `raw` → fail-closed（不静默塞 broad，SR-E）

#### Scenario: roster 中零-finding 行落全零行〔grill-amendment〕
- **WHEN** `roster` 含某行键（如 `(outside-voice,claude,code-voice)`，host=codex）但本轮无任何 finding 命中它
- **THEN** emitter SHALL 仍为该**行键**落一行全零锚（`findings=采纳=裁掉=defer=独立=0`、`sev=致0/高0/中0/低0`，`host`/`runner`/`site` 取自 `--host` 与 roster 行键），MUST NOT 省略该行（反静默：跑了没抓到也留痕）

#### Scenario: finding 命中行键不在 roster 则 fail-closed〔spec-review-amendment C4 反方向〕
- **WHEN** 某 finding 的 `hits` 折叠出合法 canonical 行键 `X`（fold 成功、非未知 raw）但 `X` 不在 `roster`
- **THEN** emitter SHALL fail-closed 报明「finding 命中行 `X` 不在本轮 roster」，MUST NOT 静默把该 finding 计数丢弃（roster 须是所有 finding 命中行键的超集）

#### Scenario: metrics 开时强制 broad/outside-voice 行〔grill-amendment〕
- **WHEN** emitter 被调用（即视 metrics-on）而输入 `roster` 缺 `broad` 或 `outside-voice`（任一 site 的 outside-voice 行）
- **THEN** emitter SHALL fail-closed 报明缺失（因 `anchor_lint` 的 `MIN_LENS_ROWS` 强制此二行存在，缺则输出必被拒），MUST NOT 产出会被 anchor_lint 拒的部分锚

#### Scenario: 缺 --host 或取值越域则 fail-closed〔add-codex-host-support〕
- **WHEN** 调用方未传 `--host`，或传入 `claude|codex|unknown` 之外的值（含已废弃的 `claude-fallback`）
- **THEN** emitter SHALL fail-closed 非零退出并报明原因，MUST NOT 默认填 `claude`（静默默认会把 Codex 宿主的轮次伪装成 Claude 宿主，正是本能力要杀的假绿）
