# lens-metric-emit Specification

## Purpose
TBD - created by archiving change implement-mechanical-layer-hardening-p4-lens-metric-emit. Update Purpose after archive.
## Requirements
### Requirement: lens-metric 计数由确定性 emitter 从结构化 findings 归约

lens-metric 锚的计数（`findings`/`采纳`/`裁掉`/`defer`/`独立` + `sev` rollup）SHALL 由确定性脚本 `lens_metric_emit.py` 归约，MUST NOT 再由主 session 手数手写。所有计数 SHALL 以**行键 `(lens, host, runner, site)`** 为单位、与锚落锚键一致〔add-codex-host-support：由 `(lens,runner,site)` 升维加 `host`；锚唯一键相应为 `(layer,lens,host,runner,site,轮)`，layer=`--layer` 单一源、轮=一次 emit〕。

emitter SHALL 接受 **`--host`** 参数（取值 `claude|codex|unknown`，由调用方从 `resolve-models.sh` 的 `SDFLOW_HOST` 传入），作为本轮所有行的 `host` **单一源**——**MUST NOT** 有 per-finding 或 per-roster-row 的 `host`〔add-codex-host-support：与 `--layer` 同构；一轮评审只有一个宿主，per-row host 会制造无意义的自相矛盾态〕。

emitter 的**输入** SHALL 含两部分，字段名按契约权威 input schema（英文键名，取值中文）〔spec-review-amendment ADR-6〕：
- ① `roster`：`(lens,runner,site)` **行键**列表，本轮跑过的每个行键各一条（含零-finding 行）；非 outside-voice 行 `site="—"` 且 `runner` 取当前 host（主审自己的机队）——**含 `host="unknown"` 时该普通镜行 `runner="unknown"`**〔spec-review-r3 codex#1：host=unknown（CI/裸终端/第三方）下评审退化单 session、普通镜仍由主审跑，其 runner 如实为 unknown；∴ runner 枚举含 `unknown`，但 **`unknown` 仅合法于非-outside-voice 普通镜行且 host=unknown 时**——outside-voice 锚的 runner 恒 ∈{claude,codex,none}（受合法组合矩阵约束，不取 unknown）〕；outside-voice 行显式带 `runner`∈{claude,codex,**none**}〔spec-review-r2 D4：含 `none`——host-unknown/secret-hit/fallback-unavailable 的无执行轮次〕 与 `site`∈{code-voice,hr-tg,design-voice}。
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

#### Scenario: 缺 --host 或取值越域则受控 fail-closed（非 argparse 崩）〔add-codex-host-support · spec-review-amendment D4〕
- **WHEN** 调用方未传 `--host`，或传入 `claude|codex|unknown` 之外的值（含已废弃的 `claude-fallback`）
- **THEN** emitter SHALL **受控 fail-closed**（非零退出 + **可读错误消息报明原因**，MUST NOT 靠 argparse 的 `unrecognized/required` 崩栈——用 `parse_known_args` 或显式必填校验，使"缺 host"成为受控降级而非崩溃），MUST NOT 默认填 `claude`（静默默认会把 Codex 宿主的轮次伪装成 Claude 宿主，正是本能力要杀的假绿）
- **AND〔spec-review-r2 D12〕** 用 `parse_known_args` 时 SHALL 显式 `if extras: fail-closed`（报明多余/拼错参数），MUST NOT 静默吞未识别参数——否则 `--laye` 之类拼写错误被静默忽略、弱化参数防护

#### Scenario: runner="none" 行合法（无执行轮次）〔spec-review-amendment D6〕
- **WHEN** 某 roster 行键的 `runner="none"`（host-unknown/secret-hit 的无执行轮次）
- **THEN** emitter SHALL 接受 `none` 为合法 runner 值并落行，该行 `findings/采纳/裁掉/defer/独立` 恒为 0；MUST NOT 判 `none` 越域

> **跨版本 skew（D1/C3 统一策略，详见 design ADR-3）**：新 SKILL 传 `--host` 给**旧 emitter**（exit 2 清零）与旧 `anchor_lint` 拒 `runner="none"`（out-of-enum 罢工）是**同根**（bundle 内 SKILL 与 tools 更新不原子）。统一策略 = **编排 SKILL 落锚/调 emitter 前探 tools 能力，陈旧则 fail-loud 降级 + 提示 `sdflow-init update`**（见能力 host-adaptive-execution）；本能力的受控 fail-closed（上一 Scenario，含 D12 拒 extras）是该策略的**工具侧第二道兜底**，非唯一手段。

### Requirement: emitter 坏输入 fail-closed 不静默（穷举）

emitter 对坏输入 SHALL **fail-closed**：非零退出 + stderr 携带**可读 reason（含被拒字段名 + 失败类别）**，MUST NOT 静默产出空锚或部分锚、MUST NOT exit 0、**MUST NOT 把未知镜名静默塞入 `broad`**（SR-E）。坏输入清单 SHALL 按 input schema 每字段 × {缺失 / present-but-empty / 越域 / 注入 / 边界} **穷举**〔spec-review-amendment：由 schema 驱动而非举例〕，至少含：

- 非法 JSON；缺必填字段（无 `hits`/`verdict`）；`verdict`/`lens`（折叠后）/`runner` 越域；`sev` 级别非法。
- **`hits:[]` present-but-empty**〔C11〕：空数组过「缺字段」检查但折叠出空行键集 → SHALL fail-closed（`hits` MUST 非空数组），MUST NOT 静默使该 finding 计数贡献 0。
- **`verdict==采纳` 缺/空 `sev`**〔C12〕：sev 是条件必填（iff 采纳）→ SHALL fail-closed；emitter SHALL 自校验不变量 `Σ(致+高+中+低)==采纳`（每行采纳数与 sev rollup 总和吻合），不符 fail-closed。
- **`site` 注入**〔C7〕：`site` 含 `"`/换行/`-->`/`=` → SHALL fail-closed（防破坏锚语法且绕过对 site 免检的 anchor_lint）。
- **`roster` 缺失 / 含枚举外 lens / 缺 broad 或 outside-voice / 重复行键**〔C14〕；**`lens-metric-fold` 块重复或冲突 raw 键**〔C14〕 → 均 SHALL fail-closed。
- **finding 命中行键 ∉ roster**〔C4〕 → SHALL fail-closed（见 R1 Scenario）。

emitter SHALL 采 **all-or-nothing** 时序〔spec-review-amendment C13〕：**全部 findings/roster 校验通过才 emit 任何锚行**；任一校验失败 → stdout 无任何锚行 + 非零退出（两审 SKILL 落锚步 MUST「exit 0 才用 stdout」）。

枚举 SHALL 从契约 `lens-metric-enums` 机读块、**折叠 SHALL 从契约 `lens-metric-fold` 机读块单一源读取**，MUST NOT 在脚本内复制枚举/折叠清单；`sev` 输入级 SHALL 从契约 `sev-format` 模板解析（不硬编码）〔spec-review-amendment C15〕。`verdict` 枚举为 emitter 输入独有、不写进锚、不与 anchor_lint 共享 → MAY 作脚本内本地常量，但 design MUST 显式声明豁免理由〔spec-review-amendment ADR-11〕。因 emitter 作 bundle tool 铺进消费仓、而 `sdflow-retro/scripts` 不在消费仓，emitter MUST NOT `import lens_metric_aggregate`/`ship_gate`，SHALL 脚本内重实现同款归约/fence 逻辑（非 import 复用）；MUST NOT `import yaml`、MUST NOT 读 config（门控外置，ADR-10）。

#### Scenario: 越域枚举非零退出
- **WHEN** 输入某 finding 的 `verdict=通过` 或 hit `raw` 折叠出越域 `lens` 或（若曾误带）`layer=review`
- **THEN** emitter SHALL 非零退出，stderr 报明被拒字段名 + 失败类别，MUST NOT 产出锚行

#### Scenario: present-but-empty 与条件必填 fail-closed〔spec-review-amendment C11/C12〕
- **WHEN** 某 finding `hits:[]`（空数组）**或** `verdict==采纳` 但 `sev` 缺失/空
- **THEN** emitter SHALL fail-closed 非零退出、报明字段名，MUST NOT 静默使该 finding 少计（`hits` 空→0 贡献、采纳缺 sev→rollup 少计）

#### Scenario: site 注入 fail-closed〔spec-review-amendment C7〕
- **WHEN** 某 outside-voice 行的 `site` 含 `"` 或换行或 `-->`
- **THEN** emitter SHALL fail-closed 拒绝，MUST NOT 产出会破坏锚语法/绕过 anchor_lint 的锚行

#### Scenario: all-or-nothing 不产部分锚〔spec-review-amendment C13〕
- **WHEN** 一批 findings 中第 N 条触发校验失败（前 N-1 条合法）
- **THEN** emitter SHALL stdout 无任何锚行 + 非零退出，MUST NOT 已把前 N-1 行锚写出（先全校验再整体 emit）

#### Scenario: 契约枚举/折叠单一源读取〔grill-amendment〕
- **WHEN** emitter 需要 layer/lens/runner/sev-format 取值域，或原始镜名→canonical lens 折叠
- **THEN** 取值域 SHALL 从 `lens-metric-contract.md` 的 `lens-metric-enums` 块读、折叠 SHALL 从 `lens-metric-fold` 块读，MUST NOT 在脚本内另复制清单；且 `load_fold` 后 SHALL 自校验 fold codomain⊆`lens-enum`、越界 fail-closed〔spec-review-amendment C3〕

### Requirement: emitter 输出按构造通过 check_lens_metric 且信任边界诚实收窄

emitter 的输出锚行 SHALL 按构造通过 `anchor_lint.check_lens_metric`（**非 anchor_lint 整门**）〔spec-review-amendment C5：`anchor_lint.main` 无条件先跑 `check_existence`、强制 outside-voice/hr-tg/step1-broad-review 三非-lens 锚族存在，emitter 不产之，故「emitter 单独输出过整门 exit 0」是过度声明、MUST NOT 如此断言〕——即 emitter 落锚后跑 `check_lens_metric` MUST NOT 因字段/枚举/sev/layer==--layer/计数类型报违规。emitter 与 anchor_lint 各自重实现的 `load_enums` SHALL 由**等价性测试**守（`emitter.load_enums(contract)==anchor_lint.load_enums(contract)` 逐字段相等）〔spec-review-amendment C10：「同读一个文件」≠「同一解析器」〕。

emitter 归约**收窄**但**不消灭**信任边界：脚本 SHALL 保证「计数是所给结构化输入的正确归约」，MUST NOT 谎称保证「输入 findings 集与合并池实收 finding 吻合」——后者（模型分类每条 finding 的 `hits`/`verdict`/`sev` 是否正确）SHALL 显式声明为**残余主 session 信任边界**（judgment，非机械可验）；且 emitter 引入的 `roster` 完备性 + 结构化 JSON 誊写两道**新**手工工序的错误面 SHALL 一并计入残余边界〔spec-review-amendment C19：诚实账，本 change 净效果非总错误面单调下降〕。

#### Scenario: emitter 输出过 check_lens_metric
- **WHEN** emitter 对合法输入产出锚行、随后对其跑 `check_lens_metric`（或对预置三 MANDATORY 锚族 + emitter 行的完整报告跑 `anchor_lint --layer <L>`）
- **THEN** `check_lens_metric` SHALL 无违规（字段/枚举/sev/layer==--layer/计数 int≥0 全过），二者无口径分歧；MUST NOT 断言「emitter 单独输出过 anchor_lint 整门 exit 0」

#### Scenario: load_enums 等价性〔spec-review-amendment C10〕
- **WHEN** 对同一契约文件分别跑 emitter 与 anchor_lint 的 `load_enums`
- **THEN** 二者返回的 layer/lens/runner 集合与 sev 正则 SHALL 逐字段相等，杜绝 fence 缩进/trim/闭合判定分歧读出不同 enum 集

#### Scenario: 残余信任边界诚实声明
- **WHEN** 问「emitter 是否保证锚计数与合并池实际 finding 数吻合」
- **THEN** 答 SHALL 为否——emitter 只保证「对所给输入的归约正确」；输入是否忠实反映合并池（分类正确性 + roster 完备性 + JSON 誊写）是残余主 session 信任边界，脚本 MUST NOT 谎称机械保证

