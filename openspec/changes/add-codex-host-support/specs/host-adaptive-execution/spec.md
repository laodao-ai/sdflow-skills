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

outside voice 的 runner SHALL 恒为**当前宿主之外的另一个机队的强档**：`SDFLOW_HOST=claude` ⇒ runner 为 Codex 机队强档；`SDFLOW_HOST=codex` ⇒ runner 为 Claude 机队强档（`claude -p --model <强档> --output-format text --tools "Read,Grep,Glob" --strict-mcp-config`，只读非交互——**allowlist deny-by-default，见「出境安全」需求**）〔spec-review-amendment Q2：由 `--disallowedTools` denylist 改 `--tools` 独占白名单 + MCP 隔离〕。

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
- **THEN** 本轮不跑 outside voice；锚行记 `host="unknown" runner="none" reason_code="host-unknown"`〔spec-review-amendment D6：无执行用 `runner="none"`，MUST NOT 任选 claude/codex 伪造"谁执行"〕；报告显著标注「宿主判不出，本轮无跨模型第二意见」，MUST NOT 随便挑一个 runner 跑了当作跨模型

#### Scenario: 禁止自审〔spec-review-amendment D1：绑定 outside-voice 锚〕
- **WHEN** 任一实现路径试图在 `runner == host` 时把 findings 当作跨模型第二意见（豁免置信过滤 / 复用守卫认作跨模型段 / 锚行不标降级）
- **THEN** 该实现为违规；`anchor_lint` SHALL 对 **`sdflow:outside-voice` 锚**（非 lens-metric 锚——只有 outside-voice 锚同时承载 `runner`/`host`/`reason_code`）判「`runner == host` ∧ `reason_code ∉ {not-installed,preflight-error,timeout,exec-error}`」为自审、报错阻塞；`anchor_lint` **SHALL 新增 outside-voice 锚的 KV 字段解析**（现状只记该锚存在性、零字段解析），且该校验 **MUST always-on、不受 `metrics.enabled` 门控**（读真实性信号非价值度量）

### Requirement: 出境安全三件套对两条 runner 路径一视同仁

`outside-voice.sh` 的 secret 扫描（`secret_scan`）、不可信上下文硬分隔与三条通则注入（`render_prompt` 的 FRAME）、体积上限截断（200KB 保头尾）SHALL 为**两条 runner 路径共用的同一份代码**。反向路径（Codex 宿主 → Claude）MUST NOT 另起炉灶组装 prompt。

理由：新增的 runner 意味着**新的数据出境端点**；任何"给该路径单独写一套 prompt 组装"的实现都会绕过扫描器，是安全回归。runner 之间的差异 SHALL 只体现在最终 `exec` 的命令行分叉一处。

**只读姿势诚实边界（spec-review-amendment Q2）**：codex 路径 `-s read-only --ephemeral` 是**内核级**沙箱（seccomp/sandbox-exec，封写 + 网络）；claude 路径 `--tools "Read,Grep,Glob" --strict-mcp-config` 是**应用层尽力对齐**（deny-by-default 独占白名单 + MCP 隔离），**非内核级**——可被 settings/hook/plugin 削弱。∴ 二者 **SHALL NOT 声称"对等"**，只声称「应用层尽力 + 残余非内核级」。`--tools`（非 `--allowedTools`，后者与 settings `permissions.allow` 合并、可被穿透）+ `--strict-mcp-config` 二者 SHALL 视为**安全承重墙**，测试从单一契约片段断言，回归即红。`Read` 无 FS 边界（可读 `~/.ssh`/`.env`）SHALL 经 `--add-dir` 限定或 ephemeral cwd 收紧，并**登记残余**（`secret_scan` 不扫运行时 Read 内容；缓解=网络禁则读到无法外传）。

#### Scenario: secret 命中时两条路径都拒发
- **WHEN** context 文件命中 secret 模式（AWS / GitHub / Slack / Anthropic / OpenAI key / JWT），无论目标 runner 是 codex 还是 claude
- **THEN** `exec` SHALL 退出码 3 拒发，密钥既不出境也不进 fallback 子代理的 prompt；锚行记 `runner="none" reason_code="secret-hit"`（D6：拒发即无执行），**MUST NOT fallback**

#### Scenario: 反向路径复用同一 FRAME 与截断
- **WHEN** `SDFLOW_HOST=codex`，向 `claude` 发起 voice
- **THEN** prompt SHALL 由同一个 `render_prompt` 产出（含三条通则、UNTRUSTED CONTEXT 硬分隔、200KB 保头尾截断），MUST NOT 存在第二份 prompt 组装实现

#### Scenario: 只读约束按 runner 落到对应机制（`--tools` 独占白名单 + MCP 隔离）〔spec-review-amendment Q2〕
- **WHEN** 向 claude 发起 voice
- **THEN** 命令行 SHALL 用 **`--tools "Read,Grep,Glob"`**（独占白名单，把其余内建工具从可用集移除）**+ `--strict-mcp-config`**（隔离 ambient MCP）；**MUST NOT 用 `--disallowedTools Write Edit NotebookEdit` denylist**（留 Bash/WebFetch 可外传），**也 MUST NOT 用 `--allowedTools`**（它配权限层、与消费仓 settings `permissions.allow` 合并 → `Bash(...)` 预批准可穿透，非 deny-by-default）；此形态为**应用层尽力对齐**（非声称与内核级沙箱对等）

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

#### Scenario: resolver 输出的模型覆盖值不得成为 eval 注入面〔spec-review-amendment D5〕
- **WHEN** 消费仓 `config.yaml` 的 model-tiers 覆盖值含 shell 元字符（`$()`、反引号、引号、换行等），而 `resolve-models.sh` 输出六变量供调用方 `eval`
- **THEN** `resolve-models.sh` SHALL 以可证安全的编码输出（`printf %q` / `declare -p`）并**拒绝换行/控制字符/非模型 ID 字符**；`config_lint` SHALL 校验 model-tiers 的**值**（非仅键）为合法模型 ID；MUST NOT 让覆盖值在 `eval` 时被执行（须有恶意值回归测试）。**SHOULD 优先考虑取消 `eval`**（改用 `source` 一个受控生成文件或数组读取）

### Requirement: 子代理不可用时镜数如实降级（探针语义核验 + always-on 一致性 lint，逐镜留语义层）

Codex 宿主默认不派子代理（须由 AGENTS.md / SKILL 显式授权）。`sdflow-init` 铺给消费项目的 AGENTS.md 段与两个评审 SKILL SHALL 显式声明该授权。

子代理确实不可用时，评审 SHALL **把 roster 缩到实际跑过的镜**并在报告显著标注「单镜降级」，MUST NOT 按计划的镜数照落 lens-metric 锚。

**探针 = 语义核验（非机械门）+ always-on 一致性 lint（spec-review-amendment Q1，adr/0023 已降格）**：「fan-out 机制活着没」有信号、**但无可机械捕获路径**——探针（trivial 子代理看回不回哨兵）只能由**主 session 自己**调用观察、把 `subagents=` 写进锚，`anchor_lint` 读那行锚**无从核验它对应一次真 spawn**（经被监管方自报，§0.0 防伪一侧）。∴ 探针 SHALL 作**机制活着的语义核验**、MUST NOT 冒充机械门。`SDFLOW_HOST=codex` ⇒ **MUST 探**；`claude` ⇒ 免探恒 available；`unknown` ⇒ 不 fan-out。结果落会话级锚 `<!-- sdflow:fanout-capability v1 host="…" subagents="available|unavailable" -->`，该锚 **MUST 落进被 `anchor_lint` 校验的那份报告文件内**（D8：落别处则 lint 看不见）；`host=codex` 的报告中该锚**必须在场**（缺锚不得绕过）。

`anchor_lint` SHALL 增一条 **always-on 一致性 lint**（**与 `metrics.enabled` 解耦**，D7——它读真实性信号非价值度量）：`subagents="unavailable"` 时，lens-metric 锚中 `lens ∈ {domain,adversarial,grounding}`（fan-out 镜集，**去重键钉死按 `lens`**）的行数 **MUST ≤ 1**，否则报错阻塞（违规类型 `dead-fanout-multi-mirror`）。**它拦的是锚行自身的自相矛盾（诚实记录错误），不是伪造**——决心谎报的主 session 写 `subagents="available"` 即绕过（无机械交叉核验，如实登记）。

**残余诚实边界（§0.0，无信号 ⇒ 语义层）**：① 探针为 available 之后「某镜是否真独立跑过」**无信号**（主 session 可谎报自代）；② `available` 且主 session 自代多镜（同「报告 N 镜实跑 1」症状）**一致性 lint 拦不住**（`available` 分支不触发）。∴ **这两半残余归语义层**，MUST NOT 声称有机械保证；机械层仅提供**事后可发现性**（`host` 进锚 ⇒ 复盘按 host 分组，独立率异常可见）。**MUST NOT 声称"头号假绿已事前拦截"**——一致性 lint 只拦「机制死变体」的自相矛盾，不拦「机制活+偷懒自代变体」。

#### Scenario: 授权声明存在
- **WHEN** `sdflow-init` 在消费项目铺设 AGENTS.md
- **THEN** 该文件 SHALL 含 Codex 子代理授权段，明示多镜 fan-out 与 model-tiers 构成 codex 要求的 task-specific reason

#### Scenario: Codex 宿主 fan-out 前探能力并落锚（语义核验）
- **WHEN** `SDFLOW_HOST=codex` 且评审即将 fan-out
- **THEN** SHALL 先派 trivial 探针子代理判定能力，落 `sdflow:fanout-capability` 锚（`subagents="available"` 或 `"unavailable"`）到被 lint 的报告文件内；`SDFLOW_HOST=claude` 时免探针、锚记 `subagents="available"`；探针值为主 session 自报（trust-based，非机械核验）

#### Scenario: 机制死却报多镜被一致性 lint 拦截（always-on，非机械防伪）
- **WHEN** `sdflow:fanout-capability` 锚记 `subagents="unavailable"`，而 lens-metric 锚中 `lens ∈ {domain,adversarial,grounding}`（按 `lens` 去重）的行数 > 1
- **THEN** `anchor_lint` SHALL 报错阻塞（违规类型 `dead-fanout-multi-mirror`）——此为锚行自身的自相矛盾（机制死却报多镜）；此校验 MUST always-on、不受 `metrics.enabled` 门控

#### Scenario: host=codex 报告缺 fanout-capability 锚则报错
- **WHEN** `host="codex"`（可从 lens-metric/outside-voice 锚的 host 字段读到）的报告中**无** `sdflow:fanout-capability` 锚
- **THEN** `anchor_lint` SHALL 报错——否则"不落锚"即可绕过一致性 lint

#### Scenario: 子代理不可用则缩 roster
- **WHEN** 探针判 `subagents="unavailable"`，主 session 自行完成各镜工作
- **THEN** 报告 SHALL 显著标注「单镜降级（子代理不可用）」，lens-metric 的 roster SHALL 只含实际跑过的行键（fan-out 镜集 ≤ 1 行），MUST NOT 为未独立跑过的镜落锚

#### Scenario: 探针 available 后的逐镜谎报无机械守（残余语义层）
- **WHEN** 探针判 `subagents="available"`，但主 session 实际未派某镜而在锚中为其落了独立行
- **THEN** 机械层 **SHALL NOT** 保证发现（无确定性信号）；仅能经事后 `host` 分组的独立率异常供人复评——本条 MUST NOT 被实现为一道机械门（避免硬造假机械）

#### Scenario: 降级可事后经 host 分组发现
- **WHEN** 复盘聚合器按 `(layer, lens, host, runner, site)` 分组
- **THEN** Codex 宿主轮次 SHALL 可与 Claude 宿主轮次分开统计，供人复评其独立率是否异常；聚合器 MUST NOT 据此自动决策（只呈现不裁决）
