<!-- /autoplan restore point: ~/.gstack/projects/laodao-ai-sdflow-skills/feat-cross-model-outside-voice-autoplan-restore-20260704-103007.md -->
# gstack-review — cross-model-outside-voice（autoplan 广审）

> **执行方式披露（T25 纪律）**：本次 autoplan 由主 session 经 Skill 机制**原生执行**（`<!-- step1-broad-review: native -->` 语义，非子代理模拟）。
> 双声全跑：CEO/Eng/DX 三相位 × Claude 子代理 + codex exec（codex-cli 0.142.5，`-s read-only`），共 6 个独立视角。
> **编排适配（显式声明，非静默）**：autoplan 原生的两处 AskUserQuestion 人类门（premise 确认、最终批准门）按 sdflow-spec-review G2/C5 纪律改登记进「决策登记区」，由设计 HARD-GATE 一次拍板。
> **覆盖度披露**：双声与共识表 = 全深度；loaded-skill 的逐 section 清单（CEO 10 节等）以双声 findings 为载体压缩执行，未逐节独立产出 registry——此为编排取舍，不伪装全深度。
> Scope 判定：UI = 否（无前端面）；DX = 是（SKILL/CLI/agent-facing）→ Phase 2 跳过、Phase 3.5 执行。

## 共识表

### CEO（战略）
| 维度 | Claude | Codex | 共识 |
|---|---|---|---|
| 前提成立? | partial（盲区错开是断言非实测） | no（核心假设 asserted not proven） | **CONFIRMED 关切** |
| 该解决的问题? | partial（T25 真、捆绑稀释） | no（根问题是 T25） | **CONFIRMED 关切** |
| 规模校准? | partial/no（0 实测收益 vs 高永久维护面） | no（always-on 过早、五层升格过早） | **CONFIRMED 关切** |
| 备选充分探索? | no（metrics-loop 先行未论证） | no（同） | **CONFIRMED 关切** |
| 机会成本覆盖? | partial（solo 时间） | no（延迟+注意力成本未预算） | **CONFIRMED 关切** |
| 6 月轨迹? | partial（回滚扎实、价值悬空） | partial（同一懊悔场景） | **CONFIRMED 关切** |

### Eng（架构）
| 维度 | Claude | Codex | 共识 |
|---|---|---|---|
| 架构合理? | partial（划分清、地基假设未接地） | partial（helper 契约不严） | CONFIRMED 关切 |
| 测试充分? | no（最高风险面无自动化） | no（124 传播/真实格式未测） | CONFIRMED 关切 |
| 性能风险? | partial（大 payload 未定） | partial（上下文窗溢出） | CONFIRMED 关切 |
| 安全覆盖? | no（只读无 CLI 强制） | no（同 + stdin 注入） | **CONFIRMED（双声独立命中）** |
| 错误路径? | partial | partial（退出码丢失路径） | CONFIRMED 关切 |
| 部署风险? | yes（先例成熟） | medium（staleness 无技术检测） | 部分分歧→登记 |

### DX（体验）
| 维度 | Claude | Codex | 共识 |
|---|---|---|---|
| 上手无摩擦 | partial（解析规则未验证） | partial | CONFIRMED |
| 命名可猜 | partial（新子命令范式） | no（mode 一词两义） | CONFIRMED 关切 |
| 报错可行动 | partial（有意权衡） | no（诊断块缺失） | 分歧→登记 |
| 文档可查 | yes（除解析规则） | partial（锚行文法松） | CONFIRMED 关切 |
| 升级安全 | partial（staleness 纯纪律） | no（同） | CONFIRMED 关切 |
| 环境无摩擦 | yes | yes | CONFIRMED ✓ |

## 合并 findings 池（去重后，供 Step3 裁决；标注来源与严重度）

**A 组 · 战略/价值（CEO 双声共识）**
- **A1 [critical]** 价值前提不可证伪：Success Metrics 全是覆盖率/留痕型，无采纳率/命中率型；「跨模型盲区结构性错开」是断言非实测。〔CEO-Claude F1 + codex#1/#3〕
- **A2 [critical→需拍板]** T25 是根问题，与新层捆绑：建议 T25 部分可独立先行交付（拆 change 或至少独立可 merge 的实现顺序）。〔CEO-Claude F2 + codex#2〕
- **A3 [high→需拍板]** always-on code voice 过早：建议 HR-TG-only 或抽样起步，采纳率达标再升 always-on。〔codex#4，CEO-Claude F1 隐含〕
- **A4 [medium→需拍板]** HR-TG/五层升格过早固化：建议实验期（5-10 次运行）后凭命中率再入 canonical。〔codex#8 + CEO-Claude F3〕
- **A5 [high→TENSION]** codex 挑战用户 Q3 拍板：认为「卸载 codex 当开关」是坏控制面（按仓保密/故障/成本尖峰场景），建议 `auto|off|required` 显式配置。与 grill Q3「启停归环境层」用户决定相抵——**用户方向为默认，登记不改**。〔codex-CEO#5 + codex-DX#1〕
- **A6 [medium]** tension/defer 路径可制造债：无证据门槛/每次运行 defer 上限/过期清理。〔codex#10〕
- **A7 [medium]** 成本估算缺典型值与注意力预算：建议实测 codex 典型耗时 + p95 墙钟预算 + 每运行 defer 上限。〔CEO-Claude F5 + codex#7〕
- **A8 [low]** Success Metric 3 是回归项冒充新能力指标。〔CEO-Claude F6〕
- **A9 [medium]** 自维护拷贝 vs 贡献上游 gstack 未对比记录。〔CEO-Claude F4〕

**B 组 · 架构/正确性（Eng 双声共识）**
- **B1 [critical]** autoplan 原生执行的产物路径假设不成立：autoplan 原生写 **plan file**（plan-mode 机制），无「写任意路径 gstack-review.md」机制；所引 sdflow-ship「先例」实为 gstack /review 非 autoplan，文不对题。C2 复用的地基未接地。〔Eng-Claude F1〕
- **B2 [critical]** 只读无 CLI 层强制：`codex exec` 必须硬编码 `-s read-only`（+建议 `--ephemeral` `-C <repo_root>`），prompt 措辞只是第二道。〔Eng-Claude F2 + codex-Eng#1，双声独立命中〕
- **B3 [high]** stdout 非干净 findings 通道：需 `--output-last-message <f>`（或 --json+解析），helper stdout 只 cat 最终消息。〔Eng-Claude F4 + codex-Eng#2〕
- **B4 [high]** stdin 传 prompt 的复合失效：非只读沙箱下审批交互吃 stdin EOF → 挂死伪装成超时；且 diff 内容有注入面——显式 `codex exec ... - < "$prompt_file"` + 硬分隔符 + 上下文标注为不可信证据。〔Eng-Claude F3 + codex-Eng#4〕
- **B5 [high]** 退出码契约脆弱：timeout 124 经管道/子进程易丢；须无管道包 timeout、立即捕获 `$?`、测 0/1/124/127/信号杀。〔codex-Eng#3〕
- **B6 [high]** 锚行缺版本化文法：`reason="自由文本"`、`hit=…|none` 松散——建议 `<!-- sdflow:outside-voice v1 key="val" -->` 严格 KV + 单一 parser 测试套。〔codex-Eng#5 + codex-DX#8〕
- **B7 [high]** 大 diff 无预算契约：字节/token 上限、截断策略、锚行 `truncated=` 字段。〔Eng-Claude F7 + codex-Eng#6〕
- **B8 [high]** gstack-review.md「codex 段」解析规则全篇未定义（唯一线索 adr/0002 的 codex#N 标签未被引用核验）；降级原因码须分 `file-missing|section-not-found|zero-findings`。〔DX-Claude F1 + Eng-Claude F5〕
- **B9 [medium]** 并发/临时文件无规范：mktemp -d + trap 清理 + `--ephemeral`。〔Eng-Claude F8 + codex-Eng#7〕
- **B10 [medium]** 最高风险面（Step1 原生执行落地）无自动化验证，纯「下次运行核对」。〔Eng-Claude F6〕
- **B11 [medium]** helper 无 kind/schema 参数 vs 三种调用语义——与 D2「无 mode 参数」拍板相抵，登记复议。〔codex-Eng#8〕

**C 组 · DX/可执行性（DX 双声共识）**
- **C1 [high]** fallback 无法复用 helper 内嵌 prompt 框架（框架在脚本肚里，fallback 是模型侧 Task）——加 `render-prompt` 子命令，codex 与 fallback 同源消费。〔codex-DX#2〕
- **C2 [high]** copy 部署 staleness 不可检测（`[ -x ]` 挡不住旧版本）——`version` 子命令/源 hash + 前置比对。〔DX-Claude F3 + codex-DX#3〕
- **C3 [high]** 失败诊断块不足：helper 版本/codex 版本/rc/reason_code/stderr 尾/prompt hash。〔codex-DX#4〕
- **C4 [medium]** `mode=guard-degraded` 塌缩两个独立状态（guard 原因 × 实际 runner）——拆 `source/guard/runner/reason_code` 字段。〔codex-DX#5〕
- **C5 [medium]** 弱模型分支契约仍是 prose 非有限状态机：preflight 畸形输出/非零退出未定义——模板给 shell 级伪代码。〔codex-DX#6〕
- **C6 [medium]** codex findings 无可计数 schema（findings=N 数不出来）——固定块格式或 NO_FINDINGS 哨兵。〔Eng-Claude F4 关联 + codex-DX#7〕
- **C7 [medium]** exec 契约无单一源：写进 outside-voice.sh 头注释（resolve-workflow.sh 先例），SKILL 只引用。〔DX-Claude F2〕
- **C8 [low]** context-file 留痕：固定命名留 `{change_dir}`（调试证据）而非纯临时。〔DX-Claude F4，与 B9 mktemp 有张力→裁决〕
- **C9 [low]** 子命令范式新引入未说明取舍；helper 缺失文案 dev/runtime 指向错位（既有债）。〔DX-Claude F5/F7〕

**D 组 · 机械一致性（已自动修，见审计）**
- **D1 [fixed]** off-switch 残留 4 处：proposal Modified Capabilities「可 off-switch」、tasks R1 速查「可关」、design Goals「+ off-switch」、design 组件清单 tests 行「四态/off-switch」。〔codex-CEO#5 部分 + codex-Eng#9 + codex-DX#1〕

## 决策审计（autoplan 自动决策）

| # | 相位 | 决策 | 分类 | 原则 | 理由 |
|---|---|---|---|---|---|
| 1 | 合成 | D1 四处 off-switch 残留按 grill Q3 拍板方向清扫 | Mechanical | P5 | 用户已拍板，文档一致性属机械修 |
| 2 | 合成 | A/B/C 组实质性修改**不在本层自动改**，交 Step3 对抗裁决统一出 amendment | Mechanical | P3 | 单次修订面，避免两层重复改动 |
| 3 | 合成 | premise 门 + 最终批准门 → 决策登记区（编排适配） | Mechanical | G2/C5 | 见执行方式披露 |

## User Challenges（双模型共识挑战用户方向 → 决策登记区，用户方向为默认）

1. **metrics 先行/并行**（A1）：两模型一致建议价值度量前置或并入 P0；你说的顺序是「metrics-loop 缓一缓」。若我们错了，代价 = 精密管道跑数月无人知其值不值。
2. **T25 拆分先行**（A2）：两模型一致建议 T25 独立可交付；你把它并进本 change 作前置。若我们错了，代价 = 多一次 change 开销。
3. **always-on → 抽样/HR-only 起步**（A3）：codex 明确、Claude 隐含；你的 spec 写 always。若我们错了，代价 = 前 N 次运行少几条 voice 数据。
4. **off-switch 复活**（A5）：codex 单声强推 `auto|off|required`；**与你 grill Q3 显式拍板直接冲突**，按 user sovereignty 登记不改，设计门你再看一眼。

## 交叉相位主题（≥2 相位独立命中 = 高置信信号）

- **「契约是 prose 不是机器可验」**：CEO（metrics 仪式型）→ Eng（锚行/退出码/解析规则）→ DX（状态机/可计数 schema）三相位同根——本 change 给别人上「机器锚行」纪律，自己的 helper 契约却多处留白。
- **「未接地的先例/产物假设」**：Eng B1 + DX B8 独立命中 gstack-review.md 生成与解析两端都没实测样本。

*autoplan native run · 2026-07-04 · 双声 6/6 完成 · [gstack-amendment] 见 D1*
