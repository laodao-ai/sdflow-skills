## ADDED Requirements

### Requirement: lens-metric 计数由确定性 emitter 从结构化 findings 归约

lens-metric 锚的计数（`findings`/`采纳`/`裁掉`/`defer`/`独立` + `sev` rollup）SHALL 由确定性脚本 `lens_metric_emit.py` 归约，MUST NOT 再由主 session 手数手写。emitter 的**输入** SHALL 为主 session 给的结构化 findings（每条至少携带：命中镜集 `lenses`、裁决 `verdict`∈{采纳,裁掉,defer}、严重度 `sev`∈{致,高,中,低}、`layer`、`runner`、可选 `site`）；emitter 按 `lens-metric-contract.md` 的**折叠表**将原始镜名投影到 canonical `lens`、按**归属规则**（`findings/采纳/裁掉/defer` 每命中镜各记一次；`独立` 仅「唯一报过 ∧ 被采纳」时 +1、折叠到类型后计）逐 canonical lens 归约，输出**每 lens 一行**字段齐全、取值在域内、`sev` 子格式为 `致N/高N/中N/低N`（仅采纳项计入、零也写 0、分隔恒 `/`）的合规锚行。

emitter SHALL 只做机械归约，MUST NOT 做去重（是否同一 finding）、对抗裁决、严重度定级——这三者 SHALL 保留给模型/主 session（产出结构化输入）。

#### Scenario: 结构化 findings 归约出合规锚与计数
- **WHEN** 主 session 把一轮已裁决的结构化 findings（每条带 `lenses`/`verdict`/`sev`/`layer`/`runner`/`site`）喂给 `lens_metric_emit`
- **THEN** emitter SHALL 按折叠表 + 归属规则逐 canonical lens 输出一行合规 lens-metric 锚，计数与所给输入一致、`sev` 仅计采纳项、`独立` 折叠后计

#### Scenario: 共抓 finding 每命中镜各记但不计独立
- **WHEN** 一条被采纳的 finding 的 `lenses` 含 `domain` 与 `outside-voice` 两镜
- **THEN** emitter 归约后 `domain` 与 `outside-voice` 的 `采纳` 各 +1，两者 `独立` 均 SHALL NOT +1（非唯一贡献）

#### Scenario: 折叠表投影原始镜名到 canonical lens
- **WHEN** 输入 finding 的镜名为 `对抗镜2` 或 `完整性镜` 或 `codex`
- **THEN** emitter SHALL 分别折叠为 canonical `adversarial`/`grounding`/`outside-voice` 后再归约，MUST NOT 产出枚举外的 `lens` 值

### Requirement: emitter 坏输入 fail-closed 不静默

emitter 对坏输入（非法 JSON、缺必填字段、`verdict`/`lens`/`layer`/`runner` 越域、`sev` 级别非法）SHALL **fail-closed**：非零退出 + stderr 携带**可读 reason（含被拒字段名 + 失败类别）**，MUST NOT 静默产出空锚或部分锚、MUST NOT exit 0。枚举/折叠 SHALL 从契约 `lens-metric-enums` 机读块**单一源读取**，MUST NOT 在脚本内复制枚举清单；因 emitter 作 bundle tool 铺进消费仓、而 `sdflow-retro/scripts` 不在消费仓，emitter MUST NOT `import lens_metric_aggregate`/`ship_gate`，SHALL 脚本内重实现同款折叠/归约逻辑（非 import 复用）。

#### Scenario: 越域枚举非零退出
- **WHEN** 输入某 finding 的 `verdict=通过` 或 `lens=对抗镜1`（未折叠）或 `layer=review`（越域）
- **THEN** emitter SHALL 非零退出，stderr 报明被拒字段名 + 失败类别，MUST NOT 产出锚行

#### Scenario: 契约枚举单一源读取
- **WHEN** emitter 需要 layer/lens/runner/sev-format 取值域
- **THEN** SHALL 从 `lens-metric-contract.md` 的 `lens-metric-enums` fenced 块读取，MUST NOT 在脚本内另复制清单（与 `anchor_lint` 同源）

### Requirement: emitter 输出按构造通过 anchor_lint 且信任边界诚实收窄

emitter 的输出锚行 SHALL 按构造通过 `anchor_lint`（二者同读契约 `lens-metric-enums` 单一源、同 fence-aware 纪律）——即 emitter 落锚后再跑 `anchor_lint` MUST NOT 因字段/枚举/sev/计数类型报违规。emitter 归约**收窄**但**不消灭**信任边界：脚本 SHALL 保证「计数是所给结构化输入的正确归约」，MUST NOT 谎称保证「输入 findings 集与合并池实收 finding 吻合」——后者（模型分类每条 finding 的 `lenses`/`verdict`/`sev` 是否正确）SHALL 显式声明为**残余主 session 信任边界**（judgment，非机械可验）。

#### Scenario: emitter 输出过 anchor_lint
- **WHEN** emitter 对合法输入产出锚行、随后对同报告跑 `anchor_lint --layer <L>`
- **THEN** `anchor_lint` SHALL 退出 0（字段/枚举/sev/layer==--layer/计数 int≥0 全过），二者无口径分歧

#### Scenario: 残余信任边界诚实声明
- **WHEN** 问「emitter 是否保证锚计数与合并池实际 finding 数吻合」
- **THEN** 答 SHALL 为否——emitter 只保证「对所给输入的归约正确」；输入是否忠实反映合并池（分类正确性）是残余主 session 信任边界，脚本 MUST NOT 谎称机械保证
