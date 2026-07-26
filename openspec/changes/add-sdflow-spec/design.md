# add-sdflow-spec · Design

## Context

阶段一现状：`opsx:explore`（思考伙伴，CLI 官方 skill）→ `opsx:ff`（四件套生成，CLI 官方 skill）→ `/grill-with-docs`（对抗拷问，Matt Pocock skills 集合 `~/.agents/skills`，非 git 管理）。三入口拼接的缺陷与动机见 proposal。

本设计基于四路实证调研：①既有 fan-out 编排模式（sdflow-spec-review/code-review 的 dispatch 三要素、principles 注入、`resolve-models.sh` 档位变量）；②成本基线（retro 报告 + workflow-cost-optimization roadmap）；③openspec CLI 机制实测（`instructions --json` 幂等只读、单产物载荷 3.5-6KB、四件套产出 7-27KB/件）；④agent 定义文件调研（`docs/subagent-definitions-plan.md`：`effort` frontmatter 经 claude-security 插件 7 实例核验、`model: inherit` 合法、per-agent effort 缓存中性）。外部权威输入：Anthropic multi-agent 研究（多代理 ≈15× token 溢价，仅子任务独立时划算；强 lead + 廉价 subagent 比单强模型高 90.2%）。

约束：产物契约不变（标准四件套 + openspec CLI + FF-0）；下游阶段二/三不动；通则托管单一源机制不可绕过。

## Goals / Non-Goals

**Goals：**
- 单一入口管线：澄清 → 拷问 → 生成，拷问结构性不可跳过、前置于成文。
- 判断不出主 session；检索与生成外派子代理，主上下文只进结论。
- 决策纪要为承重件：对话中的 why 100% 落盘，`/clear` 无损。
- 档位相对化：主 session 档位人选（高价值 change 用最强档），子代理经档位变量。

**Non-Goals：** 见 proposal Non-Goals（含可证伪假设，此处不重复）。

## 组件清单〔BASE-25〕

| 组件 | 类型 | 职责 | 依赖 |
|---|---|---|---|
| `sdflow-spec/SKILL.md` | 新增·编排指令 | 三相位管线、dispatch 契约、降级矩阵、出口序列 | openspec CLI、agent 定义（带 fallback） |
| `sdflow-spec/agents/sdflow-researcher.md` | 新增·agent 定义 | 检索/调研/供证；只读 | 通则托管块（sync 渲染） |
| `sdflow-spec/agents/sdflow-spec-writer.md` | 新增·agent 定义 | 四件套单产物生成（单一职责）[grill-amendment] | 通则托管块、openspec CLI |
| `setup.sh` | 修改 | 新增 agents 铺设段：`sdflow-spec/agents/*.md` → `~/.claude/agents/`（symlink + 所有权守卫，对齐 `install_into` 模式） | — |
| `hack/sync_principles.py` | 修改 | agent 定义正文纳入投放面（skill 味源渲染——受众为下发的 mid/light 档子代理） | `PROJECT_TARGETS`/`skills()` 既有结构 |
| `hack/tests/test_sync_principles.py` | 修改 | 投放面守卫覆盖 agents 文件（`HEADLINES` 四子串机械守） | — |
| `sdflow-init/assets/snippets/claude-section.md` | 修改 | 归属错误修正（superpowers → Matt Pocock），经托管机制刷新本仓区块；「ff 之后是 grill」保留管旧路径 [grill-amendment] | 托管区块刷新机制 |
| CLAUDE.md/AGENTS.md/README.md | 修改 | **非托管区**新增 sdflow-spec 使用路径与出口序列 + README 列表 [grill-amendment] | — |

**组件/依赖图**〔TG-14〕：

```
人 ──触发──▶ SKILL.md（主 session·判断层）
                │
    ┌───────────┼──────────────┬────────────────┐
    ▼           ▼              ▼                ▼
 openspec CLI  sdflow-researcher  sdflow-spec-writer   checkpoint-commit.sh
 (new/status/  (agentType 派发,    (agentType 派发,      (全局 ~/.sdflow/hack/)
  instructions) fallback=内联)     fallback=内联)
                    ▲两个 agent 定义正文含通则托管块
                    │
        sync_principles.py ──守──▶ hack/tests/test_sync_principles.py
                    ▲
        setup.sh ──铺──▶ ~/.claude/agents/
```

## 三相位管线〔TG-10 序列图〕

```
人          主session(判断)        researcher        spec-writer       openspec CLI
│ 触发 ─────▶│
│            │ CLI 查上下文 ─────────────────────────────────────────────▶│
│◀─ 一次一问 │ (需证据时) ──派──▶│grep/读码/调研
│  每问附推荐│◀────结论+出处──────│
│  …若干轮…  │
│            │ ══ Phase A→B：共识初成 ══
│            │ 亲笔压缩共识为锚点纪要(对话内呈现,作拷问靶)
│◀─ 拷问(攻承重约束,一次一问) ──依据 researcher 供证
│  …至共识+承重约束全站稳…
│            │ ══ Phase B 收敛：FF-0 检查 → openspec new change ────────▶│
│            │ 主档亲笔落决策纪要(change 目录 decision-memo.md)→checkpoint
│            │ ══ Phase B→C ══
│            │ ──串行逐产物派(纪要随 prompt 下发)──▶│自调 instructions ──▶│
│            │                                     │读依赖产物→写产物
│            │◀──────────完成/失败──────────────────│
│            │ 终审:读回四件套,核纪要↔产物一致性(判断性偏差改,措辞放过)
│            │ 纪要内容并入 design.md 决策记录;checkpoint
│◀─ 出口提示原样贴:/clear → 换档 → /sdflow-spec-review
```

行为要点（specs 承载正式 requirement，此处记设计意图）：
- **Phase A**：grilling 技法固化——一次一问、每问附推荐、事实自查/决策问人、沿设计树逐分支解依赖。成熟可提前进 B；**B 不可跳过**。
- **Phase B**：拷问以锚点纪要为文本锚（调和「先拷问省返工」与「有锚更接地」两派）；锚点纪要由主 session 亲笔 [grill-amendment]——原材料（A 阶段对话共识）只在主上下文，外派压缩须先序列化共识进 prompt（等于亲写一遍）再经 writer 重述（两跳失真），且多一次 dispatch 往返；**优先攻承重约束**（一撤则候选整列塌缩）；停止信号 = 共识 + 承重约束清单全部站稳。domain-modeling 判据吸收：命中 ADR 三条件（难逆转 + 缺上下文意外 + 真实权衡）→ 提议落 `openspec/adr/`（格式锚同目录现状，冷启动用 SKILL.md 内一行最小模板）；术语冲突 → 提议 CONTEXT.md。只提议不自动写。
- **Phase C**：产物间依赖链（proposal → design/specs → tasks）决定**串行**；生成子代理 fresh context 三输入 = 决策纪要（prompt 下发）+ instructions（自调 CLI，防主 session 转述漂移）+ 依赖产物全文（自读）。终审只兜判断层。

## 数据模型与生命周期〔BASE-24〕：决策纪要

| 字段 | 内容 |
|---|---|
| 目标态 | 一句话 |
| 拍板决策[] | 决策 + 依据 + 砍掉的候选 + 砍的理由 |
| 承重约束[] | 约束 + 验证方式/证据锚 |
| 接受的边角[] | 通则④显式记录（风险 + 为何接受） |
| 三镜代价 | 仅命中 TG-23 的方案选择决策 |

生命周期 [grill-amendment]：Phase B 收敛 → FF-0 分支检查 + `openspec new change`（此时目标态已清晰、change 名可定）→ 主 session 亲笔写入 `openspec/changes/<name>/decision-memo.md`（change 目录放流程附件是既有惯例，同 hand-off.md / impl-reports/）→ B checkpoint 在 feature 分支提交该文件 → Phase C 作为每个生成子代理的输入 → 终审后**内容并入 design.md 决策记录节**（OpenSpec 原生槽位），memo 文件保留（footage 性质，审计锚）。**验收 = /clear 无损**：纪要在 git 内，session 崩溃/换 session 重入不丢拷问成果；清上下文后阶段二若丢失任何 why，即管线 bug。

## Decisions〔TG-23·BASE-12〕

**D1 拷问前置于生成**（备选：现状式先生成后拷问；Spec Kit 式生成初稿再 clarify）。改想法比改四份成文便宜；锚定效应实证（dedupe-issues：错误 premise 活过成文）；跳过风险结构性消灭。锚点纪要吸收了「有文本锚更接地」派的好处。三镜：系统镜——管线更长但无回改循环，可回退（B 产出纪要独立成立）；用户镜——拷问体验不变，免手动衔接；开发循环镜——省整轮「成文→拷问→回改」返工。主次：开发循环镜主导（返工是实证痛点）。

**D2 判断/机械分层外派**（备选：薄编排=主 session 全做；重管线=全阶段大 roster fan-out）。判断（澄清/拷问/纪要/终审）不出主 session；检索与生成外派。依据：官方 lead+subagent 实证 90.2%；15× 溢价警告 → 子代理少而定向、单一职责短命；CLI 幂等自取实测扫清生成外派障碍。薄编排是本方案的合法降级形态；重管线与拷问的顺序对话性错配、且与阶段二对抗镜职责重叠。三镜：系统镜——多一层纪要中间件与 dispatch 面，每件独立可测；用户镜——生成阶段等待略增（串行子代理），拷问体验同档；开发循环镜——复用既有 dispatch 模式零新机制，生成输出从主档价降 mid 档价。主次：开发循环镜（成本结构）主导，系统镜代价可控。

**D3 agent 定义文件承载角色**（备选：纯 prompt 内联，现有各 skill 做法）。`sdflow-researcher`（`model: inherit`·`effort: low`·`tools: Read, Glob, Grep, Bash, WebFetch, WebSearch`——联网调研属其本职（通则②「主动联网找权威最佳实践」），六者皆只读、不破无写权边界 [grill-amendment]）、`sdflow-spec-writer`（`model: inherit`·`effort: medium`·`tools: Read, Glob, Grep, Bash, Write`）。收益（docs/subagent-definitions-plan.md 四维表）：通则传播从指令变机制 + 每次派发省 ~2KB 重复注入；工具白名单挡 researcher 写权；per-agent effort 缓存中性（主 session effort 整场不动）。代价照单收：投放面 +2 必须纳入 sync_principles（否则正是该机制防的漂移）。派发写法：`agentType` 优先，解析失败 fallback prompt 内联通则（host-adaptive）。三镜：系统镜——新增 `~/.claude/agents/` 铺设面与所有权守卫；用户镜——无感；开发循环镜——effort 分档与通则免重复注入双收益。主次：开发循环镜主导。

**D4 档位相对化**（备选：SKILL.md 写死 Fable 5）。主 session = 人选档；子代理引用 `$SDFLOW_TIER_MID`/`$SDFLOW_TIER_LIGHT`（`resolve-models.sh` 既有机制）。遵守 host-adaptive-execution「skill 引用变量不内联模型名」requirement。使用纪律写入 SKILL.md：高价值 change 建议最强档主 session；产/审错档（见 D6）。

**D5 吸收技法、锚仓内格式、运行时零第三方 skill 依赖**（备选：运行时调用 grilling/domain-modeling/grill-with-docs）。三者均在仓外非受控（Matt 集合，更新即覆盖）；grilling 全文 ~12 行已全吸收；domain-modeling 只吸收触发判据，写入格式真相源 = 仓内既有 `openspec/adr/*.md` 与 CONTEXT.md 现状。唯一运行时外部依赖 = openspec CLI。

**D6 出口序列 `/clear` → 换档 → `/sdflow-spec-review`**（备选：同 session 直接跑阶段二）。三重依据：主审裁决冷视角（controller 被说服放过是 code-review 实证教训）；cache 按模型隔离，拖旧上下文切档 = 全价重付偏见；产/审错档纪律（同模型自审盲点相关，跨模型/异模型独立性有 F3/F1 独家发现实证）。出口提示 MUST 原样贴序列（对齐「ff 后贴 grill prompt」的既有强制模式）。

**D7 命名 `sdflow-spec`**（备选：sdflow-forge/sdflow-explore）。与 sdflow-spec-review 构成「产 spec → 审 spec」对仗；explore 只覆盖第一相位职责。前缀重叠经查无触发面冲突。

**D8 生成失败降级阶梯**（备选：fail-closed 整体中止）。检索败 → 主 session 亲查；生成子代理败 → 重试一次 → 主 session 亲写该产物；每级降级 MUST 如实报告。openspec CLI 不可用是唯一 fail-closed（产物契约单一源，手搓目录 = 契约漂移）。

**D9 纪要落盘 change 目录、FF-0 与 `openspec new` 前移至 B 收敛** [grill-amendment]（备选：scratchpad 暂存 + Phase C 起手建 change——被否：①scratchpad 为 per-session 目录，session 崩溃/换 session 即丢承重件，「可重入」被击穿；②B 收敛 checkpoint 时仓内零变更，checkpoint-commit.sh 静默跳过，SA-09 空转；③即使纪要进仓，feature 分支 Phase C 才建，B checkpoint 落错分支）。代价：change 名在 B 尾即定（此时信息已足够）；拷问后放弃则留带纪要的空 change 目录（feature 分支内，删分支即净）。

## 失败模式表〔BASE-06·TG-08/15〕

| 失败模式 | 检测 | 处置 | 超时/回滚〔D-4〕 |
|---|---|---|---|
| `agentType` 解析失败（未跑 setup / Codex 宿主） | 派发报错 | fallback prompt 内联通则路径；Codex 宿主整体降级主 session 亲做 | 无状态，无需回滚 |
| researcher 超时/失败 | Agent 工具错误返回 | 主 session 亲查（薄编排形态），报告标注 | 子代理默认超时由宿主管理；不重试检索（可亲查） |
| spec-writer 失败/产物缺失 | 写后核验 `resolvedOutputPath` 存在 + status 复查 | 重试 1 次 → 亲写；报告标注降级 | 产物文件可 git checkout 丢弃（feature 分支内，天然可回滚） |
| openspec CLI 不可用/报错 | 命令 exit code | **fail-closed 中止**，报错给人 | 未产生半成品（new change 失败即无目录） |
| 生成中断（部分产物完成） | status --json 对账 | 如实报告完成/未完成清单；可重入（ready 产物继续） | 分支内 git 状态即真相 |
| 纪要缺失/不完整进入 Phase C | Phase C 起手核验 `decision-memo.md` 存在且必填字段非空 | 拒绝进入生成，退回 Phase B | — |

## 可观测性〔BASE-11〕

- 各相位完成打 checkpoint commit（全局 `checkpoint-commit.sh`，slug 含相位名）——补 retro「阶段一无独立打点」缺口，retro 墙钟归因即可用。
- 降级事件（fallback/亲写/亲查）MUST 出现在对人的完成报告中，不静默。
- token 观测：v1 用 `/usage` 前后对比（粗粒度，proposal 已如实标注），不建 per-子代理归因（Non-Goal）。

## NFR 数字化〔BASE-16〕

| NFR | 数字 |
|---|---|
| 生成环节输出单价 | 主档价 → mid 档价（Fable $50/M → Sonnet $15/M，-70%；Opus 主 session 时 $25→$15，-40%） |
| 单次阶段一总成本 | 强档全包 ~$15-20 → 本方案 ~$10-13（Fable 主）/ ~$5-6（Opus 主） |
| 拷问覆盖率 | 管线内建默认路径（非机械保证）；机械审计信号 = `decision-memo.md` 存在 + 决策记录砍掉候选可 grep [grill-amendment] |
| /clear 无损 | 阶段二「上下文缺失」finding = 0 |
| dispatch 开销阈值 | 材料 ≳ 数百行且结论可压缩才外派，其余主 session 直做 |

## Risks / Trade-offs

- [sonnet 成文质量低于强档亲写] → 纪要下发承载 why + 终审兜判断层 + 阶段二 spec-review 安全网不变；若 dogfood 显示产物质量不合格，降级为亲写（D8 阶梯本身就是回退路径）。
- [agentType/effort 机制未在本仓实测] → proposal 假设列表登记；fallback 内联路径保底，失效仅收益打折不阻塞。
- [终审只核「纪要↔产物」，抓不到「纪要漏记的对话 nuance」] → 纪要由主档亲笔（质量责任集中在判断层）；/clear 无损验收使漏记在阶段二显性化，反馈回纪要纪律。
- [新增 `~/.claude/agents/` 铺设面 = 新漂移面] → 铺设走 setup.sh 所有权守卫模式；通则块由 sync_principles 机械守。
- [15× token 溢价风险] → 子代理单一职责、短 context、外派阈值；生成串行非大 fan-out。

## Migration Plan

部署：merge 后在开发 checkout 跑 `setup.sh`（铺 agents + 校验 sync `--check`）；运行 checkout 照常 `/sdflow-upgrade`（pull + setup）。回滚：revert commit + 重跑 setup.sh（孤儿链接清理机制自动移除 agents 链接）。CLAUDE.md 规范区改写随 revert 还原。三个原 skill 未动，回滚后旧流程原样可用。

## Open Questions

见 proposal〔TG-21〕：token 实测基线（人，首个 dogfood 后）；agent 定义是否纳入 sdflow-init 铺设物（dogfood 后另 change）；bundle workflow.md 下游推广（另 change）。

## Compliance〔D-6〕

- **adr/0005 dev/runtime checkout 纪律**：遵守——setup.sh 改动在开发 checkout 跑 setup 验证，测完运行 checkout 重跑还原。
- **通则托管单一源**：遵守——agent 定义正文的通则块由 `sync_principles.py` 渲染（skill 味源，受众为下发子代理，符合「按受众定措辞」），MUST NOT 手改块内部；投放面与守卫测试同 change 更新。
- **host-adaptive-execution「档位按机队分列、skill 引用变量不内联模型名」**：遵守——agents `model: inherit` + 调用时传 `$SDFLOW_TIER_*`；SKILL.md 不出现具体模型 id。
- **DOC-1（正文即最终态）**：遵守——本文无考古层，调研过程仅在 Context 以出处锚形式引用。
- **跨模块共享数据模型边界**：不涉及（决策纪要为本 skill 私有中间产物，唯一跨界产物是标准四件套，契约未变）。
- **基准 5（无界语法禁手搓）**：遵守——不解析任何 Markdown/YAML 语法面；产物存在性与完成态一律问 openspec CLI（让工具自己回答）。
