# host-adaptive-execution Specification

## Purpose
TBD - created by archiving change add-codex-host-support. Update Purpose after archive.
## Requirements
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

outside voice 的 runner SHALL 恒为**当前宿主之外的另一个机队的强档**：`SDFLOW_HOST=claude` ⇒ runner 为 Codex 机队强档；`SDFLOW_HOST=codex` ⇒ runner 为 Claude 机队强档（`claude -p --model <强档> --output-format text --tools "Read,Grep,Glob" --strict-mcp-config --add-dir <repo_root>`，**只读全仓非交互**——对称 codex 的 `-C repo_root -s read-only`，见「出境安全」需求）〔spec-review-r3 C4：撤回 r2 零工具（其前提「codex 只发 context」实测为错——codex 是 `-C repo_root` 全仓只读），恢复对称：给 claude 只读工具集 + `--add-dir` 增量授权确保覆盖仓库（非收窄边界，见「只读姿势诚实边界」）〕。

`outside-voice.sh` MUST NOT 硬编码任一 runner——`preflight` SHALL 探测**目标 runner 的 CLI**（`command -v "$SDFLOW_VOICE_RUNNER"`），`exec` SHALL 按 runner 分叉。宿主为 `unknown` 时 SHALL **不跑 voice**（无从确定"另一个机队"），锚行记 `host="unknown"` + `reason_code="host-unknown"`。

**宿主每轮判定一次、voice runner 与锚 host 同源（ADR-9）**：编排 SKILL 每轮 eval 一次 `resolve-models.sh` 并 export 六变量；`outside-voice.sh` SHALL **只从环境读 `$SDFLOW_VOICE_RUNNER`**，**MUST NOT 自行调 `resolve-models.sh` 重判宿主**——否则锚行的 `host`（emitter `--host`）与 voice 实际 `runner` 可能不同源。

**MUST NOT** 在任何情况下让 outside voice 与主审同机队而仍声称跨模型——**宁可标降级 fallback，也 MUST NOT 冒充跨模型**。

#### Scenario: Codex 宿主下 voice 走 Claude
- **WHEN** `SDFLOW_HOST=codex` 且 `claude` CLI 可用
- **THEN** `outside-voice.sh preflight` 返回 `ready`（探测的是 `claude`，不是 `codex`）；`exec` 调 `claude -p --tools "Read,Grep,Glob" --strict-mcp-config --add-dir <repo_root>` 只读全仓非交互；锚行记 `host="codex" runner="claude" reason_code="ok"`〔spec-review-r2 D5：成功跨模型路径 `reason_code` 写固定哨兵 `ok`，非 `none`〕

#### Scenario: Claude 宿主下 voice 走 Codex（现有行为不变）
- **WHEN** `SDFLOW_HOST=claude` 且 `codex` CLI 可用
- **THEN** `exec` 调 `codex exec -s read-only --ephemeral`；锚行记 `host="claude" runner="codex"`

#### Scenario: 目标 runner 未装则同族 fallback 且如实标注
- **WHEN** `SDFLOW_HOST=codex` 但 `claude` CLI 未安装（preflight 返回 `not_installed`）
- **THEN** 以同一 prompt 派**同宿主**的只读子代理兜底，评审继续不中断；锚行记 `host="codex" runner="codex" reason_code="not-installed"`（`runner == host` ⇒ 该轮 voice 非跨模型，如实可见）

#### Scenario: 宿主 unknown 则不跑 voice
- **WHEN** `SDFLOW_HOST=unknown`
- **THEN** 本轮不跑 outside voice；锚行记 `host="unknown" runner="none" reason_code="host-unknown"`〔spec-review-amendment D6：无执行用 `runner="none"`，MUST NOT 任选 claude/codex 伪造"谁执行"〕；报告显著标注「宿主判不出，本轮无跨模型第二意见」，MUST NOT 随便挑一个 runner 跑了当作跨模型

#### Scenario: 禁止自审（合法组合矩阵同族行子句）〔spec-review-amendment D1 · spec-review-r2 C1〕
- **WHEN** 任一实现路径试图在 `runner == host` 时把 findings 当作跨模型第二意见（豁免置信过滤 / 复用守卫认作跨模型段 / 锚行不标降级）
- **THEN** 该实现为违规；`anchor_lint` SHALL 对 **`sdflow:outside-voice` 锚**（非 lens-metric 锚——只有 outside-voice 锚同时承载 `runner`/`host`/`reason_code`）判「`runner == host` ∧ `reason_code ∉ {not-installed,preflight-error,timeout,exec-error}`」为自审、报错阻塞（此即下方**合法组合矩阵**的同族行子句，非并列第二条规则）；`anchor_lint` **SHALL 新增 outside-voice 锚的 KV 字段解析**（现状只记该锚存在性、零字段解析），且该校验 **MUST always-on、不受 `metrics.enabled` 门控**（读真实性信号非价值度量）

### Requirement: 锚行合法组合矩阵是「跨模型性」的机械单一源〔spec-review-r2 C1/Q1〕

「跨模型性」SHALL NOT 由散落多处的 `runner ≠ host` 各判一遍——因 `runner="none"`（D6 无执行值）满足 `none ≠ host`，会被误判为跨模型（击穿本能力核心不变式）。`anchor_lint` SHALL 以一条 **always-on 的合法组合矩阵**统一定义 `sdflow:outside-voice` 锚的合法 `(host, runner, reason_code, findings)` 组合，其余组合报错阻塞；**派生语义、置信过滤豁免（`spec-workflow`）、复用守卫（`outside-voice-reuse-guard`）SHALL 引用矩阵的「跨模型」判定，MUST NOT 各自重写 `runner ≠ host`**。矩阵：

- **跨模型 voice**：`host ∈ {claude,codex} ∧ runner ∈ {claude,codex} ∧ runner ≠ host ∧ reason_code = "ok"`（成功哨兵 `ok`，D5，不复用 `none`）
- **同族 fallback**：`host ∈ {claude,codex} ∧ runner == host ∧ reason_code ∈ {not-installed,preflight-error,timeout,exec-error}`（`missing-deps` 归约入 `preflight-error`，D7）
- **无执行**：`runner = "none" ∧ findings = 0 ∧ ( host="unknown" ∧ reason_code="host-unknown" ∨ host ∈ {claude,codex} ∧ reason_code ∈ {secret-hit, fallback-unavailable} )`

「跨模型」判定 = 矩阵第一行成立。此校验 **MUST always-on、独立成函数、不接受 `metrics_on` 参数**（D11，照 `check_hr_tg` 先例）。

**矩阵为跨工具单一源：逻辑本地重实现 + 全笛卡尔 golden 守，非可 parse 的「同构 enums」块〔spec-review-r3 C2-cross-tool · r3-narrow 修正〕**：`anchor_lint`（判自审）与 `outside_voice_guard`（判可复用）是**两个独立工具**，且 `outside_voice_guard.py` 有 **`MUST NOT import`** 边界（D5 铁律：跨模块口径本文件内重实现）——∴「引用同一矩阵」做不到用共享函数。**且矩阵是关系式谓词**（`host∈{}∧runner∈{}∧runner≠host∧reason_code="ok"`、不等式、行内析取），**`lens-metric-enums` 那种平铺 `key: 逗号值` 块表达力装不下**（r3-narrow 冷层纠正 r3 初稿「与 enums 同构」的措辞错）。∴：**① 枚举域**（host/runner/reason_code 各自取值集）SHALL 由 `lens-metric-contract.md` 机读块承载（既有单一源，两工具各自读）；**② 矩阵的关系式判定逻辑**（三态分类 illegal/cross-model/same-family/no-exec）SHALL 由两工具**各自本地重实现**（承 D5「重实现非 import」，MUST NOT 硬凑一个表达力不足的可 parse 块）；**③ 防漂移靠强 golden**：一条跨工具 golden 测试 SHALL 对 **host×runner×reason_code×findings 全笛卡尔积**（含边界 + mutation：坏值/越域/缺字段）喂两工具，断言二者的**完整分类**（非仅「跨模型」布尔）逐条一致，任一漂移即红。**MUST NOT** 让 golden 只比有限输入的布尔值（那样两工具同源同错测不出，r3-narrow 冷层点名）。

#### Scenario: 矩阵逻辑两工具各自重实现且全笛卡尔 golden 守
- **WHEN** `anchor_lint` 与 `outside_voice_guard` 都需要合法组合分类
- **THEN** 二者 SHALL 从契约机读块读**枚举域**、各自本地重实现**关系式分类逻辑**（`outside_voice_guard` 承 `MUST NOT import` 边界不 import `anchor_lint`）；一条 golden 测试 SHALL 对 host×runner×reason_code×findings 全笛卡尔积（含 mutation）断言二者**完整分类**逐条一致，MUST NOT 只比有限输入的布尔值

#### Scenario: runner="none" 不被判为跨模型
- **WHEN** 某 outside-voice 锚 `runner="none"`（无论 host 为何）
- **THEN** 矩阵判定「跨模型」为**假**，MUST NOT 享跨模型豁免 / MUST NOT 被复用守卫认作跨模型段；且 SHALL 校验 `findings=0` 与 `reason_code ∈ {host-unknown,secret-hit,fallback-unavailable}`，否则报错（如 `runner="none" findings="5"` ⇒ 违规）

#### Scenario: 非法组合当场报错
- **WHEN** 出现矩阵外的组合（如 `host="unknown" runner="claude"`、`runner="none" reason_code="ok"`、`runner==host reason_code="ok"`）
- **THEN** `anchor_lint` SHALL 报错阻塞（合法组合矩阵违规）

### Requirement: 出境安全三件套对两条 runner 路径一视同仁

`outside-voice.sh` 的 secret 扫描（`secret_scan`）、不可信上下文硬分隔与四条通则注入（`render_prompt` 的 FRAME）、体积上限截断（200KB 保头尾）SHALL 为**两条 runner 路径共用的同一份代码**。反向路径（Codex 宿主 → Claude）MUST NOT 另起炉灶组装 prompt。

理由：新增的 runner 意味着**新的数据出境端点**；任何"给该路径单独写一套 prompt 组装"的实现都会绕过扫描器，是安全回归。runner 之间的差异 SHALL 只体现在最终 `exec` 的命令行分叉一处。

**只读姿势诚实边界（spec-review-r3 C4：反向路径与 codex 对称的只读全仓）**：codex 路径 `-C repo_root -s read-only --ephemeral` 是**内核级**沙箱（seccomp/sandbox-exec，封写 + 网络），**且全仓只读可读**（FRAME 明请读仓库代码找漏，非"只发 context"）；claude 路径 `--tools "Read,Grep,Glob" --strict-mcp-config --add-dir <repo_root>` 是**只读全仓 + 应用层尽力对齐**（可被 settings/hook/plugin 削弱），**非内核级**。∴ 二者 **SHALL NOT 声称"对等"**，只声称「应用层尽力 + 残余非内核级」，但**读全仓找漏的能力对称**。**反向 `claude -p` SHALL 三旗齐全：`--tools "Read,Grep,Glob"`（只读工具集，无 Write/Bash/WebFetch）+ `--strict-mcp-config`（隔离 ambient MCP）+ `--add-dir <repo_root>`（**增量授权**确保可读到整个仓库根——`--add-dir` 语义是"加可读目录"非"收窄边界"，但因 `repo_root` 由 `git rev-parse --show-toplevel` 从 cwd 反求、`cwd⊆repo_root`，故只补齐到仓库、不引入仓外目录，r3-narrow 已证），三者 SHALL 视为安全承重墙**，测试从单一契约片段断言三旗齐全且工具集只读、回归即红。**Read 无硬 FS 边界的诚实登记**：claude `Read` 可读仓外文件（如 `~/.ssh`/`.env`）——**codex `-s read-only` 同样可读任意文件**（其 sandbox 管的是 shell 命令写/网络，非文件读白名单，r3-narrow 实测 `codex exec --help`）；二者此面**同构**，均无硬 FS 读边界、均靠 FRAME「不要读 .env/密钥」缓解、非铁桶。**r2 的零工具 `--tools ""` SHALL 废除**：其前提「codex 只发 context」实测为错（codex `-C repo_root` 全仓只读），零工具单边削弱了 claude voice 的检索能力（读不了 diff 外的调用点/类型定义）、且 FRAME「依据仓库代码本身」喂给零工具 claude 结构性做不到 → 加剧幻觉。**双边预存残余如实登记**：voice runner 读仓库内容→随请求出境到各自模型商（claude→Anthropic、codex→OpenAI），此面**两条路径同构、预先存在**，由 FRAME「不要读 .env/密钥」缓解、非铁桶、非内核级；round-2 挖的「网络禁则无法外传」论证错——那条批评对 codex 同样成立，故是双边残余而非单边砍工具的理由。**范围**：本约束只管**跨模型 `claude -p` 反向路径**，不改同族 fallback 子代理（Codex 不可用时派的 fresh Claude 只读子代理与主审同信任级、本就该有工具）。

> **实现后订正（add-codex-host-support code-review A1，据实登记两处偏差）**：
> **① claude 侧已升为「四旗」承重墙**：上文「三旗」+ **第四旗 `--settings <读围栏>`**（`permissions.deny` 挡 `.ssh`/`.aws`/`.gnupg`/gcloud/kube/docker/netrc/`id_rsa*`/`~/.claude`/`~/.sdflow` 等凭证库路径）。本机 Claude Code 2.1.211 **实测有效**：deny 规则是 Read 工具执行前的**硬门**、模型绕不过。∴ claude 侧从「无任何读边界」升为「**应用层负向 deny-list 读边界**」。**诚实限定**：仍是**应用层负向枚举**（列出的拒读、未列的仍可读），**非**内核级正向 allowlist——Claude Code 原生做不出正向 allowlist（`dontAsk`+allow 不 auto-deny 未列项、`deny//**`+allow-repo 让 deny 优先连仓内一起拦，均本机实测证伪）。另加**出境侧 secret_scan**（回传含密钥拒发 exit 3）作兜底。见 `outside-voice.sh` v1.3.0 `OV_CLAUDE_READ_FENCE`。
> **② codex `-s read-only` 的读边界行为「未真机验证」**：上文「codex `-s read-only` 同样可读任意文件、二者均无硬 FS 读边界」的断言**依据是 `codex exec --help` 文本，非运行期实测读行为**；本 change code-review 的 A1 finding 反过来断言「codex 内核沙箱真拒仓外读」，**同样未在真 Codex 宿主实测**（本 change 全程 Claude 宿主，验不了）。∴ **codex 侧读边界究竟是「全放开」还是「内核限仓内」= 未决**，**并入 A1/A3 效能门的 Codex-host 待验批**（见 hand-off「🔴 未验即合并」段）。在验证前，本 spec **不确定断言两路径对称/不对称**——只如实登记：claude 侧已有应用层 deny-list 读围栏（实测），codex 侧读边界待真机验证。

#### Scenario: secret 命中时两条路径都拒发（且不泄进日志）〔spec-review-r2 D8〕
- **WHEN** context 文件命中 secret 模式（AWS / GitHub / Slack / Anthropic / OpenAI key / JWT），无论目标 runner 是 codex 还是 claude
- **THEN** `exec` SHALL 退出码 3 拒发，密钥既不出境也不进 fallback 子代理的 prompt；锚行记 `runner="none" reason_code="secret-hit"`（D6：拒发即无执行），**MUST NOT fallback**；**`secret_scan` 的 stderr 诊断 SHALL 只输出规则类型 + 行号，MUST NOT 打印命中原行 / 匹配值**〔D8：现状 `outside-voice.sh` 把 `grep -n` 命中整行原样打进 stderr = 日志泄密〕，测试 SHALL 断言测试密钥不出现在 stdout/stderr/临时日志

#### Scenario: 组合失败（目标 CLI 缺且子代理也起不来）落 fallback-unavailable〔spec-review-r2 D9〕
- **WHEN** 目标 runner CLI 未装（F1）或 preflight-error（F1b）后，同宿主 fallback 子代理**也起不来**（无处落已执行的 runner）
- **THEN** 锚行 SHALL 记 `runner="none" findings=0 reason_code="fallback-unavailable"`，MUST NOT 生成同族 findings、MUST NOT 任选 `runner=codex/claude` 伪造"谁执行"（承合法组合矩阵无执行行）

#### Scenario: 反向路径复用同一 FRAME 与截断
- **WHEN** `SDFLOW_HOST=codex`，向 `claude` 发起 voice
- **THEN** prompt SHALL 由同一个 `render_prompt` 产出（含四条通则、UNTRUSTED CONTEXT 硬分隔、200KB 保头尾截断），MUST NOT 存在第二份 prompt 组装实现

#### Scenario: 只读约束按 runner 落到对应机制（反向路径只读全仓，对称 codex）〔spec-review-r3 C4〕
- **WHEN** 向 claude 发起跨模型 voice（`claude -p`）
- **THEN** 命令行 SHALL 三旗齐全：**`--tools "Read,Grep,Glob"`**（只读工具集，无 Write/Bash/WebFetch）**+ `--strict-mcp-config`**（隔离 ambient MCP）**+ `--add-dir <repo_root>`**（增量授权确保可读到仓库根，对称 codex `-C repo_root`；非"收窄边界"——见「只读姿势诚实边界」）；**MUST NOT 给 Write/Bash/WebFetch 等非只读工具**、**MUST NOT 用 `--tools ""` 零工具**（单边削弱检索、加剧幻觉）、**MUST NOT 用 `--disallowedTools` denylist**、**MUST NOT 用 `--allowedTools`**（与 settings `permissions.allow` 合并可穿透）；读全仓能力与 codex 对称；此形态为**应用层尽力对齐**（非声称与内核级沙箱对等）

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
- **AND〔spec-review-r2 D10〕** `resolve-models.sh` 读嵌套 `config.yaml` 的 model-tiers 覆盖（`model-tiers.{claude,codex}.{strong,mid,light}`）SHALL 与 `config_lint` **共用同一解析实现 + 畸形输入测试**（MUST NOT 各手搓一套导致口径漂移），或把该覆盖收缩成有界机器块——这是一个**受控有界的 config 解析面**（键路径可穷举），非「无界语法禁手搓」所指的 make/shell/通用语言

### Requirement: 落锚/调 emitter 前探 tools 能力，陈旧则 fail-loud 降级〔spec-review-r2 C3+D1 统一 skew 策略〕

编排 SKILL SHALL 在 fan-out / 调 `lens_metric_emit` / 落 v2 锚**之前**探测本仓 tools 是否已认识 v2 契约，陈旧则 fail-loud 降级——因 bundle 内 SKILL（symlink 即时生效）与 tools（copy，须 `sdflow-init update` 刷新）**更新不原子**，存在「新 SKILL × 旧 tools」窗口，旧 tools 有两个同根罢工症状：旧 `lens_metric_emit.py` 不认 `--host`（argparse exit 2 → lens-metric 整段静默清零）；旧 `anchor_lint.py` 枚举无 `none`（`runner="none"` 锚 → out-of-enum 罢工）。

**探测判据钉死（具体命令，非留白）〔spec-review-r3 C3-probe〕**：SHALL 为两条具体检测——① emitter 认不认 `--host`：`lens_metric_emit.py --help` 输出 grep `--host`；② anchor_lint 枚举含不含 `none`：读本仓 `lens-metric-contract.md` 的 `lens-metric-enums` 机读块、grep `runner:` 行是否含 `none`（与 emitter 侧 `--help` grep 同等具体度，MUST NOT 停留在"读契约块或探针"的模糊限定）。

**陈旧的处置 = fail-loud 硬停在落锚之前（不产出被 lint 的报告），非"产出无锚报告"〔spec-review-r3 C3-A/B：解 MANDATORY 冲突〕**：`anchor_lint` 的 outside-voice 锚是**无条件必查**（`MANDATORY`，`anchor_lint.py:148`）——∴ "陈旧则不落 v2 锚**但仍产出报告**"会撞 MANDATORY 阻塞、"落回 v1 旧锚（无 host）"又被读作 Claude 宿主 = Codex 轮次重新假绿。二者皆不可取。**正解**：探到陈旧 ⇒ 编排 SKILL 在**开始 fan-out / 落任何锚之前**硬停该评审步，**不产出待 lint 的报告**，终端/hand-off **响亮提示「tools 陈旧，请先跑 `sdflow-init update` 再重跑评审」**（fail-loud、actionable、非假绿、非静默清零、不撞 MANDATORY、不落会让旧 lint 罢工的 `runner="none"` 锚）。

**残余诚实登记（探测漏网窗口）〔spec-review-r3 C3-C〕**：SKILL 侧探测是**主守**。若探测被跳过/漏网（`metrics.enabled=false` 消费仓本就不调 emitter，此路径主要护 metrics-on 仓），旧 `lens_metric_emit.py` 撞 `--host` argparse 罢工、旧 `anchor_lint.py` 撞 `runner="none"` out-of-enum 罢工——**二者皆 fail-loud 罢工（非假绿）**，如实登记该残余窗口未被第二道机械覆盖（对比 emitter 侧：`parse_known_args` 兜底**只对新 emitter × 旧调用方成立**，对"已部署旧 emitter"结构上够不着，见下 Scenario）。

#### Scenario: 探到 tools 陈旧则 fail-loud 硬停（不产出报告）
- **WHEN** 编排 SKILL 探测发现本仓 `lens_metric_emit.py --help` 无 `--host` 或 `lens-metric-contract.md` 的 runner 枚举无 `none`（消费仓 pull 新 bundle 未 `sdflow-init update`）
- **THEN** SHALL 在落任何 v2 锚之前**硬停该评审步、不产出待 lint 的报告**，终端/hand-off 响亮提示 `sdflow-init update`；MUST NOT 产出无锚报告（撞 MANDATORY）、MUST NOT 落 v1 旧锚（假绿）、MUST NOT 静默清零

#### Scenario: 受控 fail-closed 只护「新 emitter × 旧调用方」，不护「旧 emitter」〔spec-review-r3 C3/D1 诚实拆分〕
- **WHEN** 调用方（旧 SKILL）不传 `--host` 给**新** `lens_metric_emit.py`
- **THEN** 新 emitter SHALL `parse_known_args` + 缺 `--host` 受控 fail-closed（可读错误、非 argparse 崩栈，且 `if extras: fail-closed`），MUST NOT 默认填 `claude`。**注**：此兜底**只对新 emitter 成立**；「新 SKILL × **已部署旧 emitter**」方向旧 emitter 代码不会因本 change 改变，**只能靠上方 SKILL 侧探测拦截**（parse_known_args 够不着旧文件），MUST NOT 声称此兜底覆盖后者

### Requirement: 子代理不可用时镜数如实降级（探针语义核验 + always-on 一致性 lint，逐镜留语义层）

Codex 宿主默认不派子代理（须由 AGENTS.md / SKILL 显式授权）。`sdflow-init` 铺给消费项目的 AGENTS.md 段与两个评审 SKILL SHALL 显式声明该授权。

子代理确实不可用时，评审 SHALL **把 roster 缩到实际跑过的镜**并在报告显著标注「单镜降级」，MUST NOT 按计划的镜数照落 lens-metric 锚。

**探针 = 语义核验（非机械门）+ always-on 一致性 lint（spec-review-amendment Q1，adr/0023 已降格）**：「fan-out 机制活着没」有信号、**但无可机械捕获路径**——探针（trivial 子代理看回不回哨兵）只能由**主 session 自己**调用观察、把 `subagents=` 写进锚，`anchor_lint` 读那行锚**无从核验它对应一次真 spawn**（经被监管方自报，§0.0 防伪一侧）。∴ 探针 SHALL 作**机制活着的语义核验**、MUST NOT 冒充机械门。`SDFLOW_HOST=codex` ⇒ **MUST 探**；`claude` ⇒ 免探恒 available；`unknown` ⇒ 不 fan-out。结果落会话级锚 `<!-- sdflow:fanout-capability v1 host="…" subagents="available|unavailable" mirrors="domain,adversarial,grounding,history,broad|—" -->`，该锚 **MUST 落进被 `anchor_lint` 校验的那份报告文件内**（D8-orig：落别处则 lint 看不见）；`host=codex` 的报告中该锚**必须在场**（缺锚不得绕过）。**`mirrors=` = 本轮实际 fan-out 镜清单**〔spec-review-r2 C2〕，由 SHALL 由 SKILL 在 fan-out 时直接落**、不经 emitter/lens-metric 管线、不读 `config.metrics`**，故 `metrics.enabled=false` 时也在场。code-review 层的 Step1 scope 审计（broad 镜）为被派子代理时 SHALL 计入 `mirrors=`（token `broad`）。

**`fanout-capability` 锚严格文法 + 缺字段 fail-closed〔spec-review-r3 C5-mirrors · r3-narrow #5〕**（否则 C2 仍能诚实空转）：`fanout-capability` 锚 SHALL **每轮恰好一条**（重复锚 / 重复 KV → fail-closed）；**`subagents=` SHALL 必填且严格 ∈ `{available,unavailable}`**——**`subagents=""` / 未知值 / 缺字段 SHALL fail-closed 报错，MUST NOT 视作"非 unavailable"而放行**（否则坏 `subagents` 值携多镜绕过一致性 lint 的 `unavailable` 分支，r3-narrow #5）；**capability 锚的 `host=` SHALL 与报告 outside-voice/lens-metric 锚的 `host=` 唯一一致**，否则 fail-closed（防 `host="claude"` capability 锚混入 Codex 报告只为满足"锚存在"）；`mirrors=` 为 `host=codex` 报告的**必填字段**，取值文法 SHALL 为 **`—`（未 fan-out）XOR 非空的 `{domain,adversarial,grounding,history,broad}` 逗号分隔子集**；`anchor_lint` 对 **缺 `mirrors=` / 空值 / 未知 token / 重复 token** SHALL **fail-closed 报错**，MUST NOT 把缺失/坏值静默过滤成空集（否则 `subagents="unavailable"` + 空 `mirrors` 又判 CLEAN、C2 空转复发）。

`anchor_lint` SHALL 增一条 **always-on 一致性 lint**（**判据数据源亦独立于 `metrics.enabled`**，D7 + spec-review-r2 C2）：`subagents="unavailable"` 时，**`fanout-capability` 锚自身的 `mirrors=` 清单**中 `∈ {domain,adversarial,grounding,history}` 的去重计数 **MUST ≤ 1**，否则报错阻塞（违规类型 `dead-fanout-multi-mirror`）。**判据 MUST 读 `mirrors=`，MUST NOT 数 lens-metric 行**〔C2 纠正首轮致命洞：lens-metric 锚在生产端受 `metrics.enabled` 门控（默认消费仓 `metrics.enabled=false` ⇒ 零行 ⇒ lint 永判 CLEAN 空转）；`mirrors=` 由 SKILL 直接落、不受该门控〕。**`broad` MUST NOT 进 dead-fanout 计数集**——broad（Step1 scope 审计）在 `subagents="unavailable"` 时有**设计内的主 session 降级合法路径**（恒跑守卫），`unavailable` + `mirrors` 含 `broad` 不构成「机制死却报多镜」的自相矛盾；把它计入会将合法降级误判 fail。**它拦的是锚行自身的自相矛盾（诚实记录错误），不是伪造**——`mirrors=`/`subagents=` 仍是主 session 自报，写 `subagents="available"` 或只列 1 镜即绕过（无机械交叉核验，如实登记）；且是否触发仍受 `host` 自报信任边界约束（谎报 `host=claude` 则不要求该锚，与 ADR-1 同根、非本条新增）。此校验及其判据数据 MUST always-on，MUST 独立成函数、不接受 `metrics_on` 参数（D11）。

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
- **WHEN** `subagents="unavailable"` 且 `mirrors="broad,history"`（broad 由主 session 降级亲做、另有一镜独立完成）
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

### Requirement: outside-voice exec 的 dispatch 模式宿主自适应

**Requirement ID: HAE-08.** 编排评审 SKILL 调用 outside voice 的 **dispatch 模式 SHALL 按 `$SDFLOW_HOST` 自适应**（读 Step0 已解析值、MUST NOT 重判宿主，ADR-9 同源），使两宿主的跨模型 voice 均可离开同步关键路径并在真实评审负载下跑到终态：

- **`$SDFLOW_HOST=claude` ∧ harness 后台能力自探通过 ∧ 主 session 已确证**：SHALL 继续把 `outside-voice.sh exec` 通过 harness `run_in_background` 派出，dispatch 秒返，Step3 用既有完成通知 barrier collect。
- **`$SDFLOW_HOST=codex` ∧ Claude 2.1.169+ background-exec preflight ready**：SHALL 通过 `outside-voice-background-job` helper 调用本机验证过的 research-preview `claude --bg --exec` 执行形态，由 Claude per-user supervisor 托管现有 `outside-voice.sh exec`；dispatch 秒返，Step3 从 terminal sidecar await/collect。preflight SHALL 同时验证已安装 helper/data capability manifest 与受支持平台；真实 dispatch 是最终能力探针。**[grill-amendment] [spec-review-amendment]**
- 两条 async 路径的内层 timeout **SHALL** 使用 `outside-voice.async-timeout-seconds`（合法范围 1..3600，默认 900）。Claude-host harness 能力不可用时可保留 sync 300 秒降级；Codex-host background-exec 不可用时 **SHALL** 立即同族 fallback，MUST NOT 再走已知 efficacy=0 的同步 Claude 300 秒路径。**[grill-amendment] 该 Codex-host 快速降级是已拍板的兼容边界，不得以“尽力兼容旧版”为由恢复同步分支。**

#### Scenario: Claude 宿主既有 async 行为保持
- **WHEN** `$SDFLOW_HOST=claude` 且 harness background 可用、主 session 已确证
- **THEN** voice 经 `run_in_background` 跑到完成，dispatch 秒级返回，锚行按真实结果落 `reason_code="ok"` 或诚实降级

#### Scenario: Codex 宿主经 Claude supervisor 后台运行
- **WHEN** `$SDFLOW_HOST=codex`、Claude Code ≥2.1.169 且 background-exec preflight ready **[grill-amendment]**
- **THEN** `claude --bg --exec` SHALL 托管 `outside-voice.sh exec --timeout <async-timeout>`，Codex 发起 shell 5 秒内返回，任务跨 shell 生命周期继续运行，终态成功落 `host="codex" runner="claude" reason_code="ok"`

#### Scenario: 两宿主 dispatch 均不长阻塞
- **WHEN** 任一受支持宿主实际派发跨模型 voice
- **THEN** dispatch shell SHALL 在 5 秒内返回并允许主 session 继续 fan-out；总 barrier 可等待 voice 终态，但 MUST NOT 把整个模型运行塞在 dispatch 调用内

#### Scenario: Codex background-exec 不可用时快速降级
- **WHEN** `$SDFLOW_HOST=codex` 但 Claude CLI 版本过旧、agent view 被策略禁用、supervisor 启动失败或 job id 不可解析
- **THEN** SHALL 在 5 秒级走同族 fallback并落 `preflight-error`/`exec-error`，MUST NOT 同步调用 Claude 等待 300 秒，MUST NOT 假装跨模型成功 **[grill-amendment]**

#### Scenario: Claude harness 后台不可用则保留同步兼容降级
- **WHEN** `$SDFLOW_HOST=claude` 但 harness background 自探失败，或无法确证当前为主 session
- **THEN** SHALL 降级回 sync 300 秒、外层 ≥330 秒并显著标注同步降级，MUST NOT 沿用 async 900 秒导致假超时

### Requirement: async dispatch 不改变锚契约与诚实降级

**Requirement ID: HAE-09.** async dispatch SHALL 只改变执行时机与托管方——锚行契约、`reason_code` 枚举、`anchor_lint` 合法组合矩阵、outside-voice 的 FRAME/secret scan/200KB 截断与 Claude 四旗 MUST 保持语义不变。Claude-host collect **SHALL** 继续使用 harness 完成通知；Codex-host collect **SHALL** 使用 background job 的原子 terminal sidecar + 有界 await。两路径均须只按可信终态分支，MUST NOT 假绿。

#### Scenario: 锚契约与矩阵不变
- **WHEN** 本 change 落地后跑 `anchor_lint` 的 host×runner×reason_code×findings 全笛卡尔 golden
- **THEN** 结果 SHALL 与本 change 前逐条一致，跨模型成功仍只允许 `host≠runner ∧ reason_code="ok"` 的合法组合

#### Scenario: 两类 async 路径按各自可信终态 collect
- **WHEN** Claude-host harness 或 Codex-host supervisor job 到达终态
- **THEN** 前者按 harness task 终态、后者按 worker 原子 `.rc` sidecar 分支；成功 stdout 才进 findings，MUST NOT 从自由文本、agent summary 或未完成输出推断状态

#### Scenario: 撞天花板或异常退出诚实降级
- **WHEN** worker 实际 rc=124、rc=1/2/其他非零、terminal job 无 rc、job lookup 失败或 collect 读取失败
- **THEN** 124 SHALL 映射 `timeout`；其他非零/未知/丢失 SHALL 映射 `exec-error`；MUST NOT 静默当 `ok`、MUST NOT 落零锚

#### Scenario: 起了没收不得读作成功
- **WHEN** background voice 已 dispatch 但评审中止、尚未 collect 或 terminal sidecar 不完整
- **THEN** 该站点 SHALL 无 `reason_code="ok"` 锚，MUST NOT 因“起过一次”或 agent summary 看似完成而假绿

#### Scenario: barrier 时 RUNNING 不得早退落 timeout
- **WHEN** Step3 barrier 时某 dispatch 站点仍 RUNNING 且未撞内层 timeout
- **THEN** Claude-host SHALL 等完成通知，Codex-host SHALL 进入有界 await；两者均 MUST NOT 提前落 `timeout`，`reason_code="timeout"` 只允许由实际 rc=124 产生

#### Scenario: 外层等待被回收后可恢复 collect
- **WHEN** Codex-host await shell 被外层回收但 supervisor worker 仍在运行
- **THEN** 同一主评审 session SHALL 按保留的显式 job id/run dir 恢复 collect，MUST NOT 重派；若整个 session 已丢失，新评审只能通过显式 `reconcile --run-dir` 处理 abandoned run，MUST NOT 扫描“最新 run”猜测恢复目标；若 worker/job 已丢失且无 rc且子树已确认退出则诚实判 `exec-error` **[spec-review-amendment]**

#### Scenario: 退出码不可被 runner 伪造
- **WHEN** voice stdout 含退出码样式文本或恶意指令
- **THEN** Claude-host 继续读 runner 不可写的 wrapper sidecar；Codex-host 读 supervisor worker 在 child 结束后原子发布的 rc sidecar。runner 仅有只读工具，不能写这些文件；文件缺失/坏格式 SHALL 判 `exec-error`，MUST NOT 从 stdout 解析退出码

#### Scenario: per-site 完整性机械可审
- **WHEN** 任一宿主同轮 dispatch 2 个站点，其一未 collect、另一正常落锚
- **THEN** `declared-sites` 与实落 outside-voice 锚集合核 SHALL 报错，MUST NOT 因家族级“至少一行”而判 CLEAN

#### Scenario: 复用态不假红
- **WHEN** spec-review 复用已有 `design-voice` 产出而未重新 dispatch
- **THEN** declared 仍按“应有锚”站点集计算并包含 `design-voice`，MUST NOT 改成按 job dispatch 集计算，MUST NOT 解析站点语义不同的 `guard=` 承重

#### Scenario: 错误 stderr 不当 findings
- **WHEN** 任一后台 runner 非零退出并产生未过出境 scan 的 stderr
- **THEN** collect SHALL 只记录结构化退出状态与 stderr 行数/字节数，MUST NOT 把 stderr 原文当 findings 或写入 tracked 报告

#### Scenario: outer supervisor logs 不成为第二出境面 **[spec-review-amendment]**
- **WHEN** background worker 或 inner helper 产生 context、partial stdout、stderr 或 secret canary
- **THEN** 原始内容 SHALL 只写入 0600 run-dir 文件，`claude logs`/supervisor state 只能出现固定结构化状态；negative smoke 失败 SHALL 阻塞 Codex background transport

#### Scenario: helper 安全核心复用且隔离项可加固
- **WHEN** Codex-host background worker 执行 Claude voice
- **THEN** SHALL 调用同一 `outside-voice.sh exec`，FRAME、secret scan、截断与四旗保持同源；Claude runner SHALL 使用单一源解析的 strong 模型（目标仓为 `opus`）与 `--effort high --safe-mode --no-session-persistence`，但 MUST NOT 复制第二份 prompt/safety/model-tier 实现 **[grill-amendment]**

