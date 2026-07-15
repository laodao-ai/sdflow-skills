## ADDED Requirements

### Requirement: 宿主判定靠正信号，判不出即 fail-loud

工作流 SHALL 以确定性脚本 `resolve-models.sh`（装于 `~/.sdflow/hack/`）判定执行宿主，判据 MUST 为**正信号**：Claude Code = 环境变量 `CLAUDECODE=1`；Codex = 环境变量 `CODEX_THREAD_ID` 非空。脚本 SHALL 经 `eval` 导出 `SDFLOW_HOST`、`SDFLOW_TIER_STRONG`、`SDFLOW_TIER_MID`、`SDFLOW_TIER_LIGHT`、`SDFLOW_VOICE_RUNNER`、`SDFLOW_VOICE_MODEL` 六个变量。

**MUST NOT 用「缺失即另一方」推断宿主**——两个正信号皆无时 SHALL 落 `SDFLOW_HOST=unknown`（fail-loud），MUST NOT 猜测。理由：CI / 裸终端 / 第三方宿主下猜测会把一方误认成另一方，制造**新的**假绿。

#### Scenario: Claude 宿主正信号命中
- **WHEN** 环境变量 `CLAUDECODE=1` 存在
- **THEN** `SDFLOW_HOST=claude`；三档位取 Claude 机队（`model-tiers.md` 的 Claude 行）；`SDFLOW_VOICE_RUNNER=codex`

#### Scenario: Codex 宿主正信号命中
- **WHEN** 环境变量 `CODEX_THREAD_ID` 非空
- **THEN** `SDFLOW_HOST=codex`；三档位取 Codex 机队；`SDFLOW_VOICE_RUNNER=claude`、`SDFLOW_VOICE_MODEL` 为 Claude 机队强档

#### Scenario: 两个正信号皆无则 unknown 且不猜
- **WHEN** `CLAUDECODE` 与 `CODEX_THREAD_ID` 均不存在（CI / 裸终端 / 第三方宿主）
- **THEN** `SDFLOW_HOST=unknown`；档位回落 canonical 缺省；`SDFLOW_VOICE_RUNNER` 为空（不跑 voice）；脚本 MUST 在 stderr 明示「宿主判不出」，MUST NOT 猜测任一宿主

#### Scenario: 两个正信号同时出现（异常环境）
- **WHEN** `CLAUDECODE=1` 与 `CODEX_THREAD_ID` 同时非空（如 Claude 里跑 codex 子进程时环境泄漏）
- **THEN** `SDFLOW_HOST=unknown` + stderr 明示信号冲突，MUST NOT 静默取其一（冲突下任一选择都可能把 voice 变成自审）

### Requirement: outside voice = 另一个机队的强档（跨机队不变式）

outside voice 的 runner SHALL 恒为**当前宿主之外的另一个机队的强档**：`SDFLOW_HOST=claude` ⇒ runner 为 Codex 机队强档；`SDFLOW_HOST=codex` ⇒ runner 为 Claude 机队强档（`claude -p --model <强档> --output-format text --disallowedTools Write Edit NotebookEdit`，只读非交互）。

`outside-voice.sh` MUST NOT 硬编码任一 runner——`preflight` SHALL 探测**目标 runner 的 CLI**（`command -v "$SDFLOW_VOICE_RUNNER"`），`exec` SHALL 按 runner 分叉。宿主为 `unknown` 时 SHALL **不跑 voice**（无从确定"另一个机队"），锚行记 `host="unknown"` + `reason_code="host-unknown"`。

**宿主每轮判定一次、voice runner 与锚 host 同源（ADR-9）**：编排 SKILL 每轮 eval 一次 `resolve-models.sh` 并 export 六变量；`outside-voice.sh` SHALL **只从环境读 `$SDFLOW_VOICE_RUNNER`**，**MUST NOT 自行调 `resolve-models.sh` 重判宿主**——否则锚行的 `host`（emitter `--host`）与 voice 实际 `runner` 可能不同源。

**MUST NOT** 在任何情况下让 outside voice 与主审同机队而仍声称跨模型——**宁可标降级 fallback，也 MUST NOT 冒充跨模型**。

#### Scenario: Codex 宿主下 voice 走 Claude
- **WHEN** `SDFLOW_HOST=codex` 且 `claude` CLI 可用
- **THEN** `outside-voice.sh preflight` 返回 `ready`（探测的是 `claude`，不是 `codex`）；`exec` 调 `claude -p` 只读非交互；锚行记 `host="codex" runner="claude"`

#### Scenario: Claude 宿主下 voice 走 Codex（现有行为不变）
- **WHEN** `SDFLOW_HOST=claude` 且 `codex` CLI 可用
- **THEN** `exec` 调 `codex exec -s read-only --ephemeral`；锚行记 `host="claude" runner="codex"`

#### Scenario: 目标 runner 未装则同族 fallback 且如实标注
- **WHEN** `SDFLOW_HOST=codex` 但 `claude` CLI 未安装（preflight 返回 `not_installed`）
- **THEN** 以同一 prompt 派**同宿主**的只读子代理兜底，评审继续不中断；锚行记 `host="codex" runner="codex" reason_code="not-installed"`（`runner == host` ⇒ 该轮 voice 非跨模型，如实可见）

#### Scenario: 宿主 unknown 则不跑 voice
- **WHEN** `SDFLOW_HOST=unknown`
- **THEN** 本轮不跑 outside voice；锚行记 `host="unknown" reason_code="host-unknown"`；报告显著标注「宿主判不出，本轮无跨模型第二意见」，MUST NOT 随便挑一个 runner 跑了当作跨模型

#### Scenario: 禁止自审
- **WHEN** 任一实现路径试图在 `runner == host` 时把 findings 当作跨模型第二意见（豁免置信过滤 / 复用守卫认作 codex 段 / 锚行不标降级）
- **THEN** 该实现为违规；`anchor_lint` SHALL 对「声称跨模型但 `runner == host`」的锚行报错阻塞

### Requirement: 出境安全三件套对两条 runner 路径一视同仁

`outside-voice.sh` 的 secret 扫描（`secret_scan`）、不可信上下文硬分隔与三条通则注入（`render_prompt` 的 FRAME）、体积上限截断（200KB 保头尾）SHALL 为**两条 runner 路径共用的同一份代码**。反向路径（Codex 宿主 → Claude）MUST NOT 另起炉灶组装 prompt。

理由：新增的 runner 意味着**新的数据出境端点**；任何"给该路径单独写一套 prompt 组装"的实现都会绕过扫描器，是安全回归。runner 之间的差异 SHALL 只体现在最终 `exec` 的命令行分叉一处。

#### Scenario: secret 命中时两条路径都拒发
- **WHEN** context 文件命中 secret 模式（AWS / GitHub / Slack / Anthropic / OpenAI key / JWT），无论目标 runner 是 codex 还是 claude
- **THEN** `exec` SHALL 退出码 3 拒发，密钥既不出境也不进 fallback 子代理的 prompt；锚行记 `reason_code="secret-hit"`，**MUST NOT fallback**

#### Scenario: 反向路径复用同一 FRAME 与截断
- **WHEN** `SDFLOW_HOST=codex`，向 `claude` 发起 voice
- **THEN** prompt SHALL 由同一个 `render_prompt` 产出（含三条通则、UNTRUSTED CONTEXT 硬分隔、200KB 保头尾截断），MUST NOT 存在第二份 prompt 组装实现

#### Scenario: 只读约束按 runner 落到对应机制（allowlist deny-by-default）
- **WHEN** 向 claude 发起 voice
- **THEN** 命令行 SHALL 用 **allowlist**（`--allowedTools Read Grep Glob` 等最小只读集，deny-by-default），与 codex 路径的 `-s read-only --ephemeral` 沙箱姿势**对等**；**MUST NOT 用 denylist `--disallowedTools Write Edit NotebookEdit`**——denylist 会留着 Bash/WebFetch/WebSearch，未受信 context 可经其写盘或外传（secret_scan 只认已知模式、拦不住任意外传），是安全回归

### Requirement: 模型档位按机队分列，skill 引用变量不内联模型名

`model-tiers.md` SHALL 按**机队**分列档位映射（Claude 机队：强/中/弱 = opus / sonnet / haiku；Codex 机队：强/中/弱 = gpt-5.6-sol / gpt-5.6-terra / gpt-5.6-luna），承 adr/0006(c) 机队锚定。编排 skill SHALL 引用 `resolve-models.sh` 导出的 `SDFLOW_TIER_*` 变量，MUST NOT 内联具体模型名。

Codex 宿主下向 `spawn_agent` 显式指定 `model` SHALL 附理由「本工作流的 model-tiers 即 codex 所要求的 clear task-specific reason」（门禁步不得降档是硬约束，非偏好）。

#### Scenario: 同一 skill 在两宿主下各取本机队档位
- **WHEN** `sdflow-done` 的 verify 步（强档）分别在 Claude 宿主与 Codex 宿主运行
- **THEN** 前者取 Claude 机队强档、后者取 Codex 机队强档；两者 MUST NOT 降档到中/弱档（verify 是唯一终门）

#### Scenario: 消费仓覆盖段按机队分键生效〔grill G4〕
- **WHEN** 消费仓 `config.yaml` 的 `model-tiers.codex` 段提供 per-repo 覆盖，且当前 `SDFLOW_HOST=codex`
- **THEN** 该 codex 段覆盖优先于 `model-tiers.md` 的 Codex 机队缺省；无 codex 段时用 Codex 机队缺省，MUST NOT 报错、MUST NOT 落到 claude 段

#### Scenario: 扁平旧格式覆盖兼容读作 Claude 机队〔grill G4〕
- **WHEN** 消费仓 `config.yaml` 是扁平旧格式 `model-tiers.strong: <某 Claude 模型>`（无机队分键）
- **THEN** 在 Claude 宿主下 SHALL 读作 Claude 机队覆盖并生效；在 Codex 宿主下该扁平覆盖 SHALL NOT 生效（回落 Codex 机队缺省），MUST NOT 把其中的 Claude 模型名用于 Codex 子代理

### Requirement: 子代理不可用时镜数如实降级（机制活着有机械下限，逐镜留语义层）

Codex 宿主默认不派子代理（须由 AGENTS.md / SKILL 显式授权）。`sdflow-init` 铺给消费项目的 AGENTS.md 段与两个评审 SKILL SHALL 显式声明该授权。

子代理确实不可用时，评审 SHALL **把 roster 缩到实际跑过的镜**并在报告显著标注「单镜降级」，MUST NOT 按计划的镜数照落 lens-metric 锚。

**机械下限（有确定性信号 ⇒ 机械守，adr/0023）**：「fan-out 机制活着没」**有**确定性信号——fan-out 前派一个 trivial 探针子代理、看它是否回哨兵值（让工具自己回答）。`SDFLOW_HOST=codex` ⇒ **MUST 探**；`SDFLOW_HOST=claude` ⇒ Task tool 是核心、免探针恒 available；`unknown` ⇒ 不 fan-out。探针结果 SHALL 落会话级锚 `<!-- sdflow:fanout-capability v1 host="…" subagents="available|unavailable" -->`（每轮一行）。`anchor_lint` SHALL 增一条红线：`subagents="unavailable"` 时，lens-metric 锚中 `lens ∈ {domain,adversarial,grounding}`（fan-out 镜集）的**去重行数 MUST ≤ 1**，否则报错阻塞——机制死却报多面独立 fan-out 镜是矛盾，这道下限把「报告 7 镜、实跑 1 镜」的头号假绿从事后可发现变为**事前拦截**。

**残余诚实边界（§0.0，无信号 ⇒ 语义层）**：探针为 available 之后，「某个镜是否真的作为独立子代理跑过」**没有确定性信号**——主 session 自报、可谎报某镜独立跑过而实际自代。∴ **这一半残余归语义层**，MUST NOT 声称有机械保证；机械层能提供的**仅是事后可发现性**：`host` 进 lens-metric 锚 ⇒ 复盘按 host 分组，Codex 宿主轮次若独立率异常（自审高度重合）数据会露出来。**下限是门、残余是残余，MUST NOT 把残余说成有门、也 MUST NOT 把下限说成没门。**

#### Scenario: 授权声明存在
- **WHEN** `sdflow-init` 在消费项目铺设 AGENTS.md
- **THEN** 该文件 SHALL 含 Codex 子代理授权段，明示多镜 fan-out 与 model-tiers 构成 codex 要求的 task-specific reason

#### Scenario: Codex 宿主 fan-out 前探能力并落锚
- **WHEN** `SDFLOW_HOST=codex` 且评审即将 fan-out
- **THEN** SHALL 先派 trivial 探针子代理判定能力，落 `sdflow:fanout-capability` 锚（`subagents="available"` 或 `"unavailable"`）；`SDFLOW_HOST=claude` 时免探针、锚记 `subagents="available"`

#### Scenario: 机制死却报多镜被红线拦截（机械下限）
- **WHEN** `sdflow:fanout-capability` 锚记 `subagents="unavailable"`，而 lens-metric 锚中 `lens ∈ {domain,adversarial,grounding}` 的去重行数 > 1
- **THEN** `anchor_lint` SHALL 报错阻塞（违规类型 `dead-fanout-multi-mirror`）——机制不可用时不可能有多面独立 fan-out 镜，此为矛盾

#### Scenario: 子代理不可用则缩 roster
- **WHEN** 探针判 `subagents="unavailable"`，主 session 自行完成各镜工作
- **THEN** 报告 SHALL 显著标注「单镜降级（子代理不可用）」，lens-metric 的 roster SHALL 只含实际跑过的行键（fan-out 镜集 ≤ 1 行），MUST NOT 为未独立跑过的镜落锚

#### Scenario: 探针 available 后的逐镜谎报无机械守（残余语义层）
- **WHEN** 探针判 `subagents="available"`，但主 session 实际未派某镜而在锚中为其落了独立行
- **THEN** 机械层 **SHALL NOT** 保证发现（无确定性信号）；仅能经事后 `host` 分组的独立率异常供人复评——本条 MUST NOT 被实现为一道机械门（避免硬造假机械）

#### Scenario: 降级可事后经 host 分组发现
- **WHEN** 复盘聚合器按 `(layer, lens, host, runner, site)` 分组
- **THEN** Codex 宿主轮次 SHALL 可与 Claude 宿主轮次分开统计，供人复评其独立率是否异常；聚合器 MUST NOT 据此自动决策（只呈现不裁决）
