## MODIFIED Requirements

### Requirement: 度量锚契约 sdflow:lens-metric v1 为结构化行级机读锚

评审**价值** SHALL 以结构化锚行 `sdflow:lens-metric v1` 记录，一行对应一（层, 镜, **宿主**, runner, 轮）**五**元组〔add-codex-host-support：原四元组不含 host，导致 Codex 宿主的自审轮次与 Claude 宿主的真跨模型轮次**无法区分**〕，MUST NOT 以自由 prose 承载（否则跨 change 聚合须 parse 自由文本，措辞漂移即腐坏——ROADMAP adr/0006(b) 禁「prose 治 prose」）。契约字段与取值域 SHALL 由 `sdflow-init/assets/workflow/` 下的**单一权威规范**定义，各生产者 SKILL 引用而 MUST NOT 复制字段清单。

字段：`layer`（`spec-review`|`code-review`）、`lens`（`domain`|`adversarial`|`grounding`|`history`|`outside-voice`|`broad`）、**`host`（`claude`|`codex`|`unknown`——谁在跑这次评审，由 `resolve-models.sh` 按正信号判定，见能力 `host-adaptive-execution`）**、`runner`（`claude`|`codex`|`none`|`unknown`——**谁执行了这个镜，只记机队家族**；`none` = 该轮无执行〔D6：host-unknown/secret-hit/fallback-unavailable 用之，伴 `findings=0`〕；`unknown` = host=unknown 时普通镜的主审机队〔spec-review-r3 codex#1，**仅合法于非-outside-voice 普通镜行 ∧ host=unknown**；outside-voice 锚 runner 恒 ∈{claude,codex,none}，受合法组合矩阵约束不取 unknown〕）、`site`（**可选消歧**：`code-voice`|`hr-tg`|`design-voice`|`—`，**仅 `outside-voice` 用、不进 `lens` enum**——消同轮多次 voice 调用的撞键，保 hr-tg 定向复核 vs 泛检信号区分〔SR-D 决策门 Q1=A〕）、`findings`（int≥0，去重前自报数）、`采纳`/`裁掉`/`defer`（int≥0）、`独立`（int≥0）、`sev`（`致N/高N/中N/低N`，仅采纳项）。〔grill-amendment：原含 `dur_s`，因无诚实数据源砍除，成本另立 T29——见 design ADR-3〕

**「跨模型性」SHALL 为派生量、由能力 `host-adaptive-execution` 的合法组合矩阵机械判定（`host,runner 均∈{claude,codex} ∧ runner≠host ∧ reason_code="ok"`），MUST NOT 编码进 `runner` 枚举值、亦 MUST NOT 简写为裸 `runner ≠ host`**〔add-codex-host-support · spec-review-r2 C1：裸 `runner≠host` 被 `runner="none"`（`none≠host` 恒真）击穿〕。`claude-fallback` **枚举值废弃**——它把"跨模型性"藏进了枚举值，在 Codex 宿主下必然说谎。矩阵三态：跨模型第二意见（上式）/ 同族 fallback（`runner==host`）/ 无执行（`runner="none" ∧ findings=0`，非跨模型）。

`lens` 字段 SHALL 为 **canonical 投影**（非报告「源」列逐字）：按规范映射折叠——完整性镜并入 `grounding`、编号对抗镜（对抗镜1/2/3）折叠到 `adversarial`、**spec-review 广审镜（raw 名 `strategy`/`plan-eng`）与 code-review 的 scope 审计（raw 名 `scope-audit`）折叠到 `broad`**、**任一 runner 的 outside voice 折叠到 `outside-voice`**（映射表见契约 `lens-metric-fold` 机读块；raw 名 `gstack-adv` 已随 code-review Step1 自持化退役、由 `scope-audit` 替换，raw 名 `autoplan-ceo`/`autoplan-design`/`autoplan-eng`/`autoplan-dx` 已随 spec-review Step1 自持化退役、由 `strategy`/`plan-eng` 替换——归档报告的锚行为 canonical 值不受影响）。`独立` SHALL 在**折叠到类型之后**计算。

**归属规则 MUST 钉死**：`findings/采纳/裁掉/defer` 按「哪些镜报过该 finding」归属，共抓则每命中镜各记一次；`独立` 仅在「唯一报过 ∧ 被采纳」时 +1。`sev` 子格式 MUST 钉死为 `致N/高N/中N/低N` 四级**定序、零也写 0、分隔符恒 `/`**（禁省略某级或改序，防自由子格式脆弱——F1-T2 类）〔spec-review-amendment SR-I〕。

**〔mlh-p4-lens-metric-emit〕计数归约由确定性 emitter 执行、非手数**：上述折叠（原始镜名 → canonical `lens`）+ 归属（`findings/采纳/裁掉/defer` 每命中**行键**各记一次）+ `独立`（唯一报过 ∧ 被采纳、折叠到**行键**后计）+ `sev` rollup（仅采纳项）SHALL 由 `lens_metric_emit.py` 对**主 session 给的结构化 findings + 本轮行键 roster**确定性归约产出，MUST NOT 再由主 session 手折叠手数手写锚。**行键 SHALL 为 `(lens, host, runner, site)`**〔add-codex-host-support：由 `(lens,runner,site)` 升维，与锚唯一键对齐〕。折叠映射 SHALL 由契约 `lens-metric-fold` 机读块**单一源**承载、`fold(raw)=raw if∈lens_enum elif fold_map else fail-closed`〔spec-review-amendment ADR-7 恒等 pass-through〕；`load_fold` 后 SHALL 自校验 codomain⊆`lens-enum`〔spec-review-amendment C3〕。emitter **门控外置、不读 config**（关时 SKILL 不调 emitter）〔spec-review-amendment ADR-10〕；layer 单一源=`--layer`、无 per-finding layer〔ADR-9〕。emitter 详细契约见能力 `lens-metric-emit`。**去重（是否同一 finding）+ 对抗裁决 + 严重度定级** SHALL 保留给模型（产出结构化输入），emitter 只做机械归约、MUST NOT 越权做判断。

〔spec-review-amendment SR-E〕**enum 扩展治理**：新增镜类型（6 值 `lens` 枚举未列的）MUST 先升契约版本号至 `v2` 并更新折叠表，**MUST NOT 静默塞入 `broad`**（`broad` 是低区分度兜底桶，新镜价值信号被广审噪声稀释 = 反噬「数据驱动优化评审架构」本命题）。**新增宿主（第三个机队）MUST 扩 `host`/`runner` 枚举**，MUST NOT 复用 `unknown` 承载已知的第三方宿主〔add-codex-host-support：`unknown` 的语义是"判不出"，不是"其他"〕。

〔spec-review-amendment SR-D · 决策门 Q1=A 已定〕**同轮多次 outside-voice 调用以 `site` 消歧**：`outside-voice` 同轮的 `code-voice`/`hr-tg`（或 `design-voice`/`hr-tg`）各落**独立一行**、以 `site` 区分（唯一性键为 `(layer,lens,host,runner,site,轮)`），MUST NOT 加总成一行抹掉 hr-tg vs 泛检的区分。非 outside-voice 镜 `site=—`。

#### Scenario: 每镜落一行合规锚
- **WHEN** 一轮 spec-review 或 code-review 的 Step3 裁决完成
- **THEN** 每个参与镜 SHALL 在对应 review 报告落一行 `sdflow:lens-metric v1` 锚，字段齐全（**含 `host`**）、取值在域内，且 `findings` 与该镜合并池实收数一致

#### Scenario: 锚字段缺失或取值越域被自检阻塞
- **WHEN** 出报告后机械核验发现某镜锚缺必填字段（如漏 `独立` 或**漏 `host`**），**或 `layer`/`lens`/`host`/`runner`/`sev` 取值不在枚举域/子格式内**（如 `lens=对抗镜1` 未折叠成 `adversarial`，或 `runner=claude-fallback` 用了已废弃的值）
- **THEN** 本步 SHALL 报错阻塞（复用现有锚存在性自检机制扩一类，**含枚举域 + sev 子格式校验**），MUST NOT 静默放行

#### Scenario: 自审锚行被自检阻塞〔add-codex-host-support · spec-review-amendment D1/D2〕
- **WHEN** 某 **`sdflow:outside-voice` 锚**（**非 lens-metric 锚**——只有 outside-voice 锚同时承载 `runner`/`host`/`reason_code`；绑到无 `reason_code` 的 lens-metric 锚会使红线静默永不触发）的 `runner == host` 且 `reason_code ∉ {not-installed, preflight-error, timeout, exec-error}`（即非合法同族降级、却声称拿到跨模型第二意见）
- **THEN** `anchor_lint` SHALL 报错阻塞——`runner == host` 的 voice 依定义**不是**跨模型，MUST NOT 作为跨模型证据落账（此即**合法组合矩阵**同族行子句，spec-review-r2 C1）。**合法降级码集 SHALL 钉死为 `{not-installed, preflight-error, timeout, exec-error}`**〔D2：grill G5 初钉漏了 `preflight-error`；`missing-deps` 现定死归约入 `preflight-error`（D7），不留实现期裁量〕；成功跨模型路径 `reason_code="ok"`（D5，非 none）；`anchor_lint` SHALL **新增 outside-voice 锚的 KV 字段解析**（现状零字段解析）；此校验 **MUST always-on、独立成函数、不受 `metrics.enabled` 门控**（D7/D11：读真实性信号）

#### Scenario: fan-out 机制死却报多镜被一致性 lint 阻塞（always-on，判据读 mirrors=）〔add-codex-host-support · spec-review-amendment Q1 · adr/0023 · spec-review-r2 C2〕
- **WHEN** 会话级 `sdflow:fanout-capability` 锚记 `subagents="unavailable"`，而**同锚 `mirrors=`** 清单中 `∈ {domain,adversarial,grounding,history}`（**按值去重**）的计数 > 1
- **THEN** `anchor_lint` SHALL 报错阻塞（违规类型 `dead-fanout-multi-mirror`）——这是**锚行自身的自相矛盾**（机制死却报多镜），**不是伪造拦截**（主 session 写 `subagents="available"` 或只列 1 镜即绕过）；判据 **MUST 读 `fanout-capability` 锚的 `mirrors=`、MUST NOT 数 lens-metric 行**〔spec-review-r2 C2 纠正首轮致命洞：lens-metric 行在生产端受 `metrics.enabled` 门控，默认消费仓 metrics=false ⇒ 零行 ⇒ lint 空转；`mirrors=` 由 SKILL 直接落、不受该门控〕；此校验及其判据数据 **MUST always-on、与 `metrics.enabled` 解耦**。MUST NOT 声称「头号假绿事前拦截」——只拦机制死变体，机制活+偷懒自代变体留语义层。`broad`（code-review scope 审计、spec-review 广审镜）不入计数集——其主 session 降级为设计内合法路径，见能力 `host-adaptive-execution`

#### Scenario: 宿主分组可事后区分真跨模型与自审轮次〔add-codex-host-support〕
- **WHEN** 复盘聚合器读取跨 change 的 lens-metric 锚
- **THEN** SHALL 可按 `host` 分组统计，使 Codex 宿主轮次与 Claude 宿主轮次的采纳率/独立率分别可见，MUST NOT 混算（混算会让一方的自审数据污染另一方的真跨模型信号）

#### Scenario: 广审镜新 raw 名折叠到 broad〔absorb-gstack-autoplan〕
- **WHEN** spec-review 报告的 findings 命中镜为 raw 名 `strategy` 或 `plan-eng`
- **THEN** emitter 按 fold 表折叠到 canonical `broad` 落锚；旧 raw 名 `autoplan-*` 不再在 fold 表内，emitter 对其 fail-closed（非静默塞 broad），归档报告的既有 canonical 锚行不受影响
