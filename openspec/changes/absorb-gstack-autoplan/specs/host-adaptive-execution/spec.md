## MODIFIED Requirements

### Requirement: 子代理不可用时镜数如实降级（探针语义核验 + always-on 一致性 lint，逐镜留语义层）

Codex 宿主默认不派子代理（须由 AGENTS.md / SKILL 显式授权）。`sdflow-init` 铺给消费项目的 AGENTS.md 段与两个评审 SKILL SHALL 显式声明该授权。

子代理确实不可用时，评审 SHALL **把 roster 缩到实际跑过的镜**并在报告显著标注「单镜降级」，MUST NOT 按计划的镜数照落 lens-metric 锚。

**探针 = 语义核验（非机械门）+ always-on 一致性 lint（spec-review-amendment Q1，adr/0023 已降格）**：「fan-out 机制活着没」有信号、**但无可机械捕获路径**——探针（trivial 子代理看回不回哨兵）只能由**主 session 自己**调用观察、把 `subagents=` 写进锚，`anchor_lint` 读那行锚**无从核验它对应一次真 spawn**（经被监管方自报，§0.0 防伪一侧）。∴ 探针 SHALL 作**机制活着的语义核验**、MUST NOT 冒充机械门。`SDFLOW_HOST=codex` ⇒ **MUST 探**；`claude` ⇒ 免探恒 available；`unknown` ⇒ 不 fan-out。结果落会话级锚 `<!-- sdflow:fanout-capability v1 host="…" subagents="available|unavailable" mirrors="domain,adversarial,grounding,history,broad|—" -->`，该锚 **MUST 落进被 `anchor_lint` 校验的那份报告文件内**（D8-orig：落别处则 lint 看不见）；`host=codex` 的报告中该锚**必须在场**（缺锚不得绕过）。**`mirrors=` = 本轮实际 fan-out 镜清单**〔spec-review-r2 C2〕，由 SHALL 由 SKILL 在 fan-out 时直接落**、不经 emitter/lens-metric 管线、不读 `config.metrics`**，故 `metrics.enabled=false` 时也在场。**两评审层的 broad 镜——code-review 的 Step1 scope 审计与 spec-review 的广审镜（strategy/plan-eng）——为被派子代理时 SHALL 计入 `mirrors=`（token `broad`）**〔absorb-gstack-autoplan：spec-review 广审自持化后与 code-review 同口径〕。

**`fanout-capability` 锚严格文法 + 缺字段 fail-closed〔spec-review-r3 C5-mirrors · r3-narrow #5〕**（否则 C2 仍能诚实空转）：`fanout-capability` 锚 SHALL **每轮恰好一条**（重复锚 / 重复 KV → fail-closed）；**`subagents=` SHALL 必填且严格 ∈ `{available,unavailable}`**——**`subagents=""` / 未知值 / 缺字段 SHALL fail-closed 报错，MUST NOT 视作"非 unavailable"而放行**（否则坏 `subagents` 值携多镜绕过一致性 lint 的 `unavailable` 分支，r3-narrow #5）；**capability 锚的 `host=` SHALL 与报告 outside-voice/lens-metric 锚的 `host=` 唯一一致**，否则 fail-closed（防 `host="claude"` capability 锚混入 Codex 报告只为满足"锚存在"）；`mirrors=` 为 `host=codex` 报告的**必填字段**，取值文法 SHALL 为 **`—`（未 fan-out）XOR 非空的 `{domain,adversarial,grounding,history,broad}` 逗号分隔子集**；`anchor_lint` 对 **缺 `mirrors=` / 空值 / 未知 token / 重复 token** SHALL **fail-closed 报错**，MUST NOT 把缺失/坏值静默过滤成空集（否则 `subagents="unavailable"` + 空 `mirrors` 又判 CLEAN、C2 空转复发）。

`anchor_lint` SHALL 增一条 **always-on 一致性 lint**（**判据数据源亦独立于 `metrics.enabled`**，D7 + spec-review-r2 C2）：`subagents="unavailable"` 时，**`fanout-capability` 锚自身的 `mirrors=` 清单**中 `∈ {domain,adversarial,grounding,history}` 的去重计数 **MUST ≤ 1**，否则报错阻塞（违规类型 `dead-fanout-multi-mirror`）。**判据 MUST 读 `mirrors=`，MUST NOT 数 lens-metric 行**〔C2 纠正首轮致命洞：lens-metric 锚在生产端受 `metrics.enabled` 门控（默认消费仓 `metrics.enabled=false` ⇒ 零行 ⇒ lint 永判 CLEAN 空转）；`mirrors=` 由 SKILL 直接落、不受该门控〕。**`broad` MUST NOT 进 dead-fanout 计数集**——broad（code-review 的 Step1 scope 审计、spec-review 的广审镜）在 `subagents="unavailable"` 时有**设计内的主 session 降级合法路径**（两层同为恒跑守卫），`unavailable` + `mirrors` 含 `broad` 不构成「机制死却报多镜」的自相矛盾；把它计入会将合法降级误判 fail。**它拦的是锚行自身的自相矛盾（诚实记录错误），不是伪造**——`mirrors=`/`subagents=` 仍是主 session 自报，写 `subagents="available"` 或只列 1 镜即绕过（无机械交叉核验，如实登记）；且是否触发仍受 `host` 自报信任边界约束（谎报 `host=claude` 则不要求该锚，与 ADR-1 同根、非本条新增）。此校验及其判据数据 MUST always-on，MUST 独立成函数、不接受 `metrics_on` 参数（D11）。

**残余诚实边界（§0.0，无信号 ⇒ 语义层）**：① 探针为 available 之后「某镜是否真独立跑过」**无信号**（主 session 可谎报自代）；② `available` 且主 session 自代多镜（同「报告 N 镜实跑 1」症状）**一致性 lint 拦不住**（`available` 分支不触发）。∴ **这两半残余归语义层**，MUST NOT 声称有机械保证；机械层仅提供**事后可发现性**（`host` 进锚 ⇒ 复盘按 host 分组，独立率异常可见）。**MUST NOT 声称"头号假绿已事前拦截"**——一致性 lint 只拦「机制死变体」的自相矛盾，不拦「机制活+偷懒自代变体」。

#### Scenario: 授权声明存在
- **WHEN** `sdflow-init` 在消费项目铺设 AGENTS.md
- **THEN** 该文件 SHALL 含 Codex 子代理授权段，明示多镜 fan-out 与 model-tiers 构成 codex 要求的 task-specific reason

#### Scenario: Codex 宿主 fan-out 前探能力并落锚（语义核验）
- **WHEN** `SDFLOW_HOST=codex` 且评审即将 fan-out
- **THEN** SHALL 先派 trivial 探针子代理判定能力，落 `sdflow:fanout-capability` 锚（`subagents="available"|"unavailable"` + `mirrors=` 本轮实际镜清单）到被 lint 的报告文件内；`SDFLOW_HOST=claude` 时免探针、锚记 `subagents="available"`；探针值为主 session 自报（trust-based，非机械核验）

#### Scenario: 机制死却报多镜被一致性 lint 拦截（always-on，判据读 mirrors=）〔spec-review-r2 C2〕
- **WHEN** `sdflow:fanout-capability` 锚记 `subagents="unavailable"`，而**同锚 `mirrors=`** 清单中 `∈ {domain,adversarial,grounding,history}`（按值去重）的计数 > 1
- **THEN** `anchor_lint` SHALL 报错阻塞（违规类型 `dead-fanout-multi-mirror`）——此为锚行自身的自相矛盾（机制死却报多镜）；判据 MUST 读 `mirrors=`、MUST NOT 数受 metrics 门控的 lens-metric 行；此校验及其数据源 MUST always-on、不受 `metrics.enabled` 门控

#### Scenario: unavailable 时 mirrors 含 broad 不触发 dead-fanout（降级合法路径）
- **WHEN** `subagents="unavailable"` 且 `mirrors="broad,history"`（broad 由主 session 降级亲做——code-review 层为 scope 审计、spec-review 层为广审，两层同为恒跑守卫——另有一镜独立完成）
- **THEN** `anchor_lint` SHALL 判合法不阻塞——`broad` 不在 dead-fanout 计数集内（计数集内仅 `history` 一项，≤1）；`mirrors="broad,domain,history"` 时计数集内为 2 项，SHALL 照常报错

#### Scenario: metrics 关闭时一致性 lint 仍生效（解耦锁）〔spec-review-r2 C2〕
- **WHEN** `metrics.enabled=false`（默认消费仓）、`subagents="unavailable"` 且 `mirrors=` 列 >1 镜
- **THEN** `anchor_lint` SHALL 照常报错阻塞——因判据 `mirrors=` 由 SKILL 直接落、不经 emitter，`metrics.enabled=false` 不影响其在场；MUST NOT 因该轮无 lens-metric 行而放行

#### Scenario: host=codex 报告缺 fanout-capability 锚则报错
- **WHEN** `host="codex"`（可从 lens-metric/outside-voice 锚的 host 字段读到）的报告中**无** `sdflow:fanout-capability` 锚
- **THEN** `anchor_lint` SHALL 报错——否则"不落锚"即可绕过一致性 lint

#### Scenario: mirrors= 缺字段/坏值/多锚 fail-closed（防 C2 经空集空转）〔spec-review-r3 C5〕
- **WHEN** `host=codex` 报告的 `fanout-capability` 锚**缺 `mirrors=`**、或 `mirrors=` 为空、或含未知/重复 token、或存在多于一条 `fanout-capability` 锚
- **THEN** `anchor_lint` SHALL **fail-closed 报错**，MUST NOT 把缺失/坏值静默视作空集放行（否则 `subagents="unavailable"` + 空 `mirrors` 会再次被判 CLEAN、C2 空转复发）

#### Scenario: 子代理不可用则缩 roster
- **WHEN** 探针判 `subagents="unavailable"`，主 session 自行完成各镜工作
- **THEN** 报告 SHALL 显著标注「单镜降级（子代理不可用）」，lens-metric 的 roster SHALL 只含实际跑过的行键（fan-out 镜集 ≤ 1 行），MUST NOT 为未独立跑过的镜落锚

#### Scenario: 探针 available 后的逐镜谎报无机械守（残余语义层）
- **WHEN** 探针判 `subagents="available"`，但主 session 实际未派某镜而在锚中为其落了独立行
- **THEN** 机械层 **SHALL NOT** 保证发现（无确定性信号）；仅能经事后 `host` 分组的独立率异常供人复评——本条 MUST NOT 被实现为一道机械门（避免硬造假机械）

#### Scenario: 降级可事后经 host 分组发现
- **WHEN** 复盘聚合器按 `(layer, lens, host, runner, site)` 分组
- **THEN** Codex 宿主轮次 SHALL 可与 Claude 宿主轮次分开统计，供人复评其独立率是否异常；聚合器 MUST NOT 据此自动决策（只呈现不裁决）
