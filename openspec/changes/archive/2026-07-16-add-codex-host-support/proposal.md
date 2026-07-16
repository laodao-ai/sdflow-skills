# add-codex-host-support

> **触发判定（TG，起手一次性）**：TG-05（数据对象：锚行 schema）· **TG-06 ⚠️HR**（跨模块共享数据模型边界：锚行是 bundle 分发给消费仓的契约）·
> **TG-08 ⚠️HR**（外部依赖：反向 runner 新增 `claude` CLI 调用）· TG-10（跨 3+ 组件）· TG-14（新组件 `resolve-models.sh`）·
> **TG-17 ⚠️HR**（信任边界：outside-voice 的 context **出境对象**新增 Anthropic 端点）· TG-18（测试计划）· TG-19（多需求）·
> TG-21（开放问题）· TG-22（假设）· TG-23（≥2 方案 → ADR）· TG-24（LLM 计费）· TG-25（版本化契约套件：锚行改一处牵连一组文档+工具）
>
> **HR-TG 命中非空 {TG-06, TG-08, TG-17}** ⇒ spec-review 规划镜头 MUST 单开领域 cross-model。

## Why

**整套 sdflow 工作流隐含假设「宿主 = Claude Code」，这个假设一处也没被写下来、一处也没被检查——所以在 Codex 宿主下，它不是报错，是静默说谎。**

两个当场可复现的假绿：

1. **outside voice 变成自审，而报告照写「跨模型」。** `outside-voice.sh` 把 codex 硬编码进了 preflight 与 exec（`sdflow-init/assets/hack/outside-voice.sh:144` = `command -v codex`；`:121` = `codex exec …`）。在 Codex 宿主下这段代码**照常返回 `ready`**——codex 当然装着——于是**调 codex 去审 codex 自己刚写的东西**。锚行照样落 `runner="codex"`，`outside_voice_guard.py:93` 照样认它是合法的 codex 段，报告照样声称拿到了"跨模型第二意见"。**「独立第二意见」这条不变式当场破产，且没有任何机制会发现。**

2. **多镜评审静默退化成单镜，而报告照写「7 镜」。** Codex 默认不派子代理（须由 AGENTS.md / skill 显式授权，官方明确"depth / thoroughness / research 都不构成授权"）。`sdflow-spec-review` / `sdflow-code-review` 的 fan-out 会安静地不发生，主 session 自己把各镜的活干一遍——而 `lens-metric` 锚行仍按 roster 逐镜落，`独立`/`采纳率` 全是自己给自己打的分。

**为什么现在做**：`docs/sdflow-fable5/` 已在为 Codex 机队铺路，而上面两条**都是「机械层在防伪」**（§0.0 第一原则要杀的病）——它们产出的不是错误，是**看起来合格的证据**。工作流的价值全押在"独立性"上，独立性一旦能被静默伪造，所有 lens-metric 数据、所有 outside-voice findings 的可信度一并归零。**这个洞越晚补，被它污染的归档数据越多。**

## What Changes

- **新增 `resolve-models.sh`**（装进 `~/.sdflow/hack/`，与 `outside-voice.sh` / `checkpoint-commit.sh` 同列）：单一职责——判宿主 + 出机队档位映射。`eval` 出 `SDFLOW_HOST` / `SDFLOW_TIER_{STRONG,MID,LIGHT}` / `SDFLOW_VOICE_RUNNER` / `SDFLOW_VOICE_MODEL`。宿主判定靠**正信号**（Claude = `CLAUDECODE=1`，Codex = `CODEX_THREAD_ID=<uuid>`），**MUST NOT** 用"缺失即另一方"推断。
- **`outside-voice.sh` 去 codex 硬编码**：runner 由 `resolve-models.sh` 决定；`preflight` 检的是**目标 runner 的 CLI**，不是"codex 装没装"。新增反向路径：Codex 宿主 → 调 `claude -p --model <强档> --output-format text --tools "Read,Grep,Glob" --strict-mcp-config --add-dir <repo_root>`（**只读全仓**，对称 codex 的 `-C repo_root -s read-only`；spec-review-r3 C4：撤回 r2 零工具——其前提「codex 只发 context」实测为错）。**secret_scan / FRAME（含三条通则）/ 200KB 截断三件套对两条出境路径一视同仁**——反向路径 MUST NOT 另起炉灶。
- **不变式落成机械可判：outside voice = 另一个机队的强档。** Claude 宿主 → Codex 的 Sol；Codex 宿主 → Claude 的 Opus。判不出宿主 ⇒ `SDFLOW_HOST=unknown` ⇒ **fail-loud**：voice 如实标降级，**宁可标 fallback，也 MUST NOT 冒充跨模型**。
- **BREAKING（锚行 schema v2）**：`outside-voice` / `lens-metric` 两类锚行**新增 `host=` 字段**；`runner` 枚举 **= `{claude, codex, none}`**（机队家族 + `none`=无执行轮次，spec-review-r2 D3/D6）。**「跨模型性」从此由 anchor_lint 的合法组合矩阵机械判定**（`host,runner 均∈{claude,codex} ∧ runner≠host ∧ reason_code="ok"`），不再靠枚举值或散落的 `runner≠host` 硬编码（后者被 `runner="none"` 击穿，spec-review-r2 C1）。`claude-fallback` **废弃**（旧锚向后兼容：读作 `host="claude", runner="claude"`）。
- **Codex 子代理授权显式化**：`sdflow-init` 铺给消费项目的 `AGENTS.md` + 各评审 SKILL.md 写明"本工作流的 model-tiers 与多镜 fan-out 即 codex 要求的 clear task-specific reason"，并在 fan-out 前**机械核验子代理能力可用**——不可用则**报告如实降级为单镜**，MUST NOT 照落 roster 锚。
- **`model-tiers.md` 从「canonical 缺省 = opus/sonnet/haiku」升为按机队分列**（Claude: opus/sonnet/haiku；Codex: gpt-5.6-sol/terra/luna），skill 一律引用变量、**MUST NOT 内联模型名**（现规则已有此条，但没有变量可引）。

## Capabilities

### New Capabilities
- `host-adaptive-execution`: 宿主判定（正信号）· 机队档位解析 · 跨机队 outside-voice 不变式（含 fail-loud）· 子代理能力核验与如实降级。

### Modified Capabilities
- `spec-workflow`: 跨模型 outside voice 的核心需求——runner 选择从"codex 写死"改为"另一机队强档"；fallback 语义与锚行文法随之改（`spec.md:516,524,567,582`）。
- `workflow-metrics`: `lens-metric` 锚行字段集加 `host`，`runner` 枚举收缩（`spec.md:10`）。
- `lens-metric-emit`: roster 行键 `(lens,runner,site)` → 需容纳 `host`；emitter 的 runner 枚举校验（`spec.md:11`）。
- `outside-voice-reuse-guard`: 守卫判"是否真跨模型"的依据从 `runner == "codex"` 改为**引用合法组合矩阵的「跨模型」判定**（`outside_voice_guard.py:93` 是当前假绿的落点之一；spec-review-r2 C1：不自写裸 `runner!=host`，否则 `runner="none"` 被误判可复用）。
- `workflow-retro`: 聚合器（`lens_metric_aggregate.py`）读锚行时须同时吃 v1 旧锚与 v2 新锚，**MUST NOT 静默丢弃**任一代。

> **不改 `determinism-guards`**（查证后排除）：该 spec 里的 `anchor_lint` 只是被 `config_lint` **引用作实现范式**（"follow `anchor_lint.py::read_metrics_enabled` 范式"），它不是 `anchor_lint` 行为的 owner——后者的需求落点在 `workflow-metrics` 的自检 Scenario。

## Success Metrics

1. **自审不可能再静默发生**：在 Codex 宿主下跑一次 `outside-voice.sh preflight` + `exec`，runner 解析为 `claude`；若强行让 `runner == host` 且非合法降级码，`anchor_lint`（读 outside-voice 锚、always-on）**必须报错**（红线可复现）。
2. **降级必留痕**：宿主判不出（两个正信号都无）时，锚行落 `host="unknown" runner="none"` 且 voice 标 fallback；grep 归档报告可机械筛出所有降级轮次。
3. **多镜空转的「机制死变体」被拦、「偷懒自代变体」留语义层（诚实限定）**：Codex 宿主下**探针判 `unavailable` 却报多面 fan-out 镜**的自相矛盾轮次，`anchor_lint` 一致性 lint（always-on、与 metrics 解耦）报错拦截；**但探针 `available` 后主 session 自代多镜（同症状）无机械守、留语义层**。〔spec-review Q1 / adr/0023：探针是**语义核验非机械门**（主 session 自报）——**MUST NOT 声称"报告 7 镜实跑 1 镜"整类已事前拦截**，只拦机制死变体的自相矛盾，见 design ADR-4〕
4. **存量数据不丢**：`sdflow-retro` 对现有归档报告（含 `openspec/retro/report.md` 里已有的 `claude-fallback` 行）的聚合结果，改造前后**逐行一致**。
5. 全量测试绿；`bash setup.sh` 两道门（`sync_principles --check` / `gen_workflow_guide --check`）保持绿。

## 需求优先级（TG-19）

| 级 | 需求 | 理由 |
|---|---|---|
| **P0** | 宿主判定（正信号 + fail-loud）· outside-voice 去 codex 硬编码 · 跨机队不变式机械守（**合法组合矩阵**判定跨模型，非裸 `runner≠host`——被 `runner="none"` 击穿，C1） | 直接杀「自审假绿」，是本 change 的立项理由 |
| **P0** | 锚行 schema v2（`host=` + runner 枚举收缩）+ `anchor_lint` 校验 + 旧锚兼容 | 不变式的机械落点；没有它，P0 第一条无法被验证 |
| **P0** | secret_scan / FRAME / 截断三件套覆盖反向出境路径 | TG-17 信任边界，新端点不能裸奔 |
| **P1** | Codex 子代理授权 + 能力核验 + 如实降级 | 杀「7 镜假绿」；但即使降级为单镜，评审仍有价值（不阻断） |
| **P1** | `model-tiers.md` 按机队分列 + skill 引用变量 | 使 P0 的档位解析真正被消费；缺它则 skill 仍会内联 opus |
| **P2** | `sdflow-retro` 聚合器双代兼容 | 只影响复盘数据连续性，不影响正确性 |

## 利益相关方与外部依赖（TG-20）

- **上游依赖**：`codex` CLI（现有）· **`claude` CLI（新增依赖）**——反向 runner 用。两者都**不是安装前提**：缺失 ⇒ preflight 返回 `not_installed` ⇒ voice 降级，评审继续（承 spec-workflow 现有需求「一切失败均为 informational，MUST NOT 阻塞评审」）。
- **下游影响方**：所有经 `sdflow-init` 消费本 bundle 的项目（mqtt-console 等）。锚行 schema 是**跨仓契约**（TG-06 / D-6）：新工具读旧仓的旧锚必须不炸，旧工具读新仓的新锚会怎样——**须在 design 明确降级方向**（见开放问题 Q2）。
- **人**：本仓 owner（拍板机队档位映射与向后兼容策略）。

## 假设（TG-22）

| # | 假设 | 若失效 |
|---|---|---|
| A1 | `CODEX_THREAD_ID` 在 Codex 所有运行形态下都存在（交互 / headless / spawned subagent） | 宿主误判为 `unknown` → 全程 fail-loud 降级。**不会假绿**，但 Codex 里 voice 永远拿不到跨模型意见。**须在 design 给出核验方法。** ／ **实测（2026-07-16，真 Codex 宿主·交互形态）：✅ 证实**——`CODEX_THREAD_ID=019f696d-…` 在 Codex 命令执行环境在场，`resolve-models.sh` 正确判 `HOST=codex`（+ `VOICE_RUNNER=claude`/`VOICE_MODEL=opus`）。**剩 `headless` / `codex exec` / `spawned subagent` 三形态待各自实测**——见 `codex-verification-checklist.md` §1 边界。 |
| A2 | Codex 的 `spawn_agent` 在被 AGENTS.md 显式授权后**确实会派**子代理 | 「7 镜假绿」的修法失效——退路是 P1 的能力核验兜底（如实降级为单镜），故 A2 失效**不会退回假绿**，只是能力受限。 |
| A3 | `claude -p` 的非交互调用在 Codex 的沙箱/权限模型下可用（**能发出网络请求并拿到 findings**） | 反向 voice 全程 fallback（贴诚实标签的同族自审）⇒ **Codex 主力形态（headless/CI）下 efficacy=0、本 change 目标未达成**〔spec-review-r2 C5/D14：登记力度对齐 design 🔴〕。若 Codex 封出境网络则 A3 恒失效，**须考虑显著缩 scope 到"仅交互 Codex"或补 headless 替代信号**。已在 Claude 宿主冒烟（5.8s），但**未在真实 Codex 沙箱内验证**——组 0 前置门真机验（人门守，非机械锁 C5）；**若走过场则 BREAKING 契约建在未验假设上**。 ／ **实测（2026-07-16，真 Codex 宿主·交互形态）：✅ 证实**——preflight=`ready`（claude CLI + timeout 在场）＋ `outside-voice.sh exec` 退出码 `0`：反向 `claude -p --model opus …`（四旗承重墙 + `--settings` 读围栏）从 Codex 真发出、认证通过、返回真 findings（`OV_TRUNCATED=false`；且 reviewer 跑 `Glob **/demo.sh` 证仓库访问生效、FRAME/不可信上下文隔离生效）。**Codex 出境网络未被封、A3 交互形态成立。剩 `headless/CI` 形态待验**——那里若无 claude CLI/认证则 efficacy=0，须补 headless 替代信号或缩 scope。 |
| A4 | 三档模型名 `gpt-5.6-{sol,terra,luna}` 稳定 | 机队换血是常态（adr/0006(c) 已预见）——正因如此模型名只出现在 `model-tiers.md` 一处。 |

## 开放问题（TG-21）

| # | 问题 | 负责人 | 截止 |
|---|---|---|---|
| Q1 | 宿主判定放 shell 脚本（`resolve-models.sh`，与既有 hack/ 同构）还是 Python（可被 tools/ 直接 import，避免 shell/Python 两处各判一次）？**两处都要用它**——skill 走 shell、`anchor_lint` 走 Python。 | design | grill 前 |
| Q2 | 旧工具 × 新锚：消费仓 pull 了新 bundle 但没重跑 `sdflow-init update`（tools 陈旧）时，旧 `anchor_lint` 见到 `host=` 会不会 fail-closed 罢工？**罢工 = 一批仓被拒之门外**（基准 5 的病灶形态）。降级方向须定。 | design | grill 前 |
| Q3 | `claude-fallback` 废弃后，**同族 fallback**（Claude 宿主、codex 不可用 → 派 Claude 只读子代理）的锚行怎么写？按新文法应是 `host="claude" runner="claude"`——但这样它与"主审自己"就无法区分了。是否需要第三个字段（如 `voice_kind=cross|same-family`）？ | design | grill 前 |
| Q4 | 子代理"能力核验"怎么做才不是**又一个防伪机械**？（§0.0：写下"MUST 机械保证 X"前先问信号从哪来。）"子代理真的跑了"的确定性信号是什么——subagent 返回值？还是只能退到语义层？ | design | grill 前 |

## 外部服务成本估算（TG-24）

- **新增计费面**：Codex 宿主下的 outside voice 改调 **Anthropic Opus**（原先错误地调 codex 自己 = 免费但无效）。单次 voice ≈ 一次 200KB 上限的 prompt + 一段 findings 输出；按现工作流每 change 的 voice 调用位点（design-voice / code-voice / hr-tg）≤ 3 次。
- **净变化**：Claude 宿主下**无变化**（仍调 codex）。Codex 宿主下**从"零成本的假绿"变成"有成本的真跨模型"**——这正是要买的东西。
- 反向 runner 用 `-p` 非交互单轮，无多轮 agent 循环，成本可预期。

## Non-Goals

- **不做宿主抽象层**：不试图让所有 skill 在两个宿主下行为完全一致（工具集本就不同——Codex 无 Task tool、Claude 无 spawn_agent）。本次只保证**三件事**跨宿主正确：档位选择、outside-voice 的跨机队性、镜数如实。
- **不迁移存量归档报告的锚行**（不 rewrite history）。旧锚靠**兼容读**处理，不做数据迁移。
- **不新增软 off-switch**：承 spec-workflow 现有决策——是否启用 voice 由环境决定（CLI 装没装），工作流层不设开关。
- **不在本次支持第三个宿主**（如 Gemini CLI）。但数据模型（`host` 字段而非布尔 `is_codex`）须为其留门。

## Compliance

- **基准 1（机械化优先）**：宿主判定、档位映射、跨模型性（**合法组合矩阵**判定，非裸 `runner≠host`——C1）——**全部有确定性信号**（环境变量 / 锚行字段），一律归脚本 + `anchor_lint` 机械守。残余语义项：Q4 的"子代理真跑了"（信号存疑，design 须诚实划界）。
- **基准 2（目标态导向）**：本 change 的全部立项证据都是**目标态推演**（"Codex 宿主下会怎样"），而非现状统计——现状里**一次 Codex 宿主的评审都没跑过**，存量锚行里**一条 `host=` 都没有。这恰恰是必须做的理由，不是可以缓的理由。** MUST NOT 用"存量里没出现过"给目标松绑。
- **基准 3（面治优先）**：`runner` 枚举出现在 6 个 spec + 3 个 tool + 2 个 SKILL.md + contract + 聚合器 + workflow-map（已实测清单见 Impact）——**一次扫全**，MUST NOT 只改被点穿的那一处。
- **基准 4（一个 change 一个完整阶段结果）**：scope = "让工作流在 Codex 宿主下跑对"这一个完整能力。锚行 schema 改动虽大，但它是该能力的**机械落点**，拆出去则不变式无处可验。
- **基准 5（无界语法禁手搓）**：不涉及无界语法面。宿主判定读环境变量（有界）；CLI 能力探测**让工具自己回答**（`command -v` + 真跑 preflight），MUST NOT 解析 CLI 版本字符串去猜能力。
- **DOC-1**：本 proposal 正文即最终态。

## Impact

**新增**
- `sdflow-init/assets/hack/resolve-models.sh`（+ `setup.sh` 装入 `~/.sdflow/hack/`）
- 反向 runner 路径（`outside-voice.sh` 内）

**修改（实测清单，`grep -rn` 得到，非估计）**
| 面 | 文件 |
|---|---|
| helper | `sdflow-init/assets/hack/outside-voice.sh`（codex 硬编码 :121/:144）· `setup.sh` |
| 规则 bundle | `assets/workflow/model-tiers.md` · `assets/workflow/lens-metric-contract.md`（runner 枚举 :10/:22/:35/:48） |
| 工具 | `assets/workflow/tools/{anchor_lint,lens_metric_emit,outside_voice_guard}.py`（+ 各自 tests · fixtures） |
| SKILL | `sdflow-spec-review/SKILL.md`（:251/:253）· `sdflow-code-review/SKILL.md`（:172/:243/:245） |
| 聚合器 | `sdflow-retro/scripts/lens_metric_aggregate.py`（:125）· `retro_report.py` + tests |
| 主 spec | `spec-workflow`(:516/:524/:567/:582) · `workflow-metrics`(:10) · `lens-metric-emit`(:11) · `outside-voice-reuse-guard` · `determinism-guards` · `workflow-retro` |
| 消费项目铺设 | `sdflow-init/assets/snippets/claude-section.md` + AGENTS.md 段（Codex 子代理授权） |
| 文档 | `docs/workflow-map.md`(:141/:150) · `docs/workflow-map.html`(:555/:563) |
| **存量数据（只读兼容，不迁移）** | `openspec/retro/report.md`(:125/:145 已有 `claude-fallback` 行) · `openspec/changes/archive/**` 全部归档报告 |

**技术栈**：Bash（helper）+ Python（tools/聚合器）+ Markdown（规则/SKILL）。不命中 backend·go / embedded / frontend 任一领域清单。
