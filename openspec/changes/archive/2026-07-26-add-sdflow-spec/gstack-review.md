<!-- sdflow:step1-broad-review v1 mode="native" -->

# add-sdflow-spec · Step1 广审（autoplan 原生执行）

**执行方式**：主 session 经 Skill 机制**原生执行** `autoplan`（其 SKILL.md 内容直接进主 session 执行，非子代理转述模拟）。

**native 侧信道佐证**：本轮真实跑过 autoplan 自身的 preamble 探测链（`gstack-repo-mode` → `REPO_MODE=solo`、`gstack-session-kind` → `interactive`、`gstack-slug` → `SLUG=laodao-ai-sdflow-skills`）与 Phase 0.5 codex preflight（`codex-cli 0.145.0`，`codex_reviews=enabled`），并按其 Phase 1/3/3.5 的 prompt 模板逐字派出 3 次 `codex exec`（经 `_gstack_codex_timeout_wrapper 600`，三次 exit 0）+ 3 个 Claude 独立子代理。

**G2 适配（sdflow-spec-review 铁律）**：autoplan 的两个人类门（Phase 1 premise gate、User Challenge gate）与 Phase 4 Final Approval Gate **不弹窗**，其内容一并登记进 `spec-review-report.md` 的「决策登记区」，由设计 HARD-GATE 一次性拍板。gstack 自身的运维提示（telemetry / routing 注入 / feature discovery）本轮跳过——与本次评审目标无关。

**如实标注的偏离**：
1. **Phase 2（Design Review）跳过** —— Phase 0 UI scope 检测未命中（本 change 无 view/component/screen 等渲染面）。
2. **Phase 3（Eng）与 Phase 3.5（DX）并行跑，未严格串行** —— autoplan 要求「CEO → Design → Eng → DX 严格串行」。本轮 DX 的 prompt 只携带 CEO 阶段的 findings 摘要，**未携带 Eng 阶段结论**。实质影响 = DX 少一路输入；两者维度独立，未观察到因此漏项（DX 独家命中的 `/clear` 冲突与 Eng 的架构面无交集）。
3. **未写 gstack 的 restore point / plan-file 审计行 / tasks-*.jsonl 聚合** —— autoplan 假定评审对象是单个 "plan file"，本轮对象是 OpenSpec 四件套；结论按 sdflow-spec-review Step1 规约落本文件，不改四件套。

---

## 双声可用性

| 声 | 状态 | 备注 |
|---|---|---|
| Codex outside voice | ✅ 三次全部 exit 0 | `codex-cli 0.145.0`，`-s read-only --enable web_search_cached` |
| Claude 独立子代理 | ✅ 三次全部返回 | fresh context，prompt 原文携带四条通则区块 |

⇒ 无降级，非 `[codex-only]`、非 `[subagent-only]`。

---

## Phase 1 · CEO Review（战略与范围）

### CODEX SAYS（CEO — strategy challenge）

10 条，摘要：

| # | 严重度 | 结论 |
|---|---|---|
| C-1 | critical | 重构目标应是「阶段一具备**持久状态与受控转换**」（`clarified → grilled → generated → reviewed`），单入口只是交互优化，不该是战略目标 |
| C-2 | critical | 「不可跳过」是**虚假承诺**：proposal 自认非机械门；旧路径与旧规范继续存活；`decision-memo.md` 非空不足以证明发生过对抗拷问（模型可直接合成一份满足字段要求的 memo） |
| C-3 | high | 廉价替代方案没被认真比较：真正便宜的 80% 方案 = 拷问前移 + 结构化 memo + spec-review 对 memo/阶段状态 fail-closed 检查 + 复用现有 explore/ff/grill 能力，**暂不引入 agent 定义/全局安装/模型路由/双 fallback** |
| C-4 | critical | 成本论证**混淆 token 数、单价与总成本**：四个串行 fresh-context writer 重复读 instructions/memo/依赖产物、主 session 最后又读回四件套 ⇒ **总 token 很可能上升**，只是因模型便宜而美元成本下降。这与 "token reduction" 不是同一主张 |
| C-5 | high | 「判断/机械分层」**切错了边界**：写 design 会发现架构缺口、写 spec 会发现不可验收表述——这些发现本身就是判断工作。writer 又被禁止询问用户 ⇒ 遇缺口只能猜/漏写/失败，随后主 session 读回直接修正 ⇒ 实际形成「双写」 |
| C-6 | high | 六个月后最愚蠢的范围决定 = 「先新增，再把整合都列为 Non-Goal」：下游 canonical 推广、spec-review 门禁、Codex 适配、agent 分发层级、旧入口退役、成本归因**全部移出范围**——而这些恰是决定能否被采用、能否兑现价值的事项 |
| C-7 | high | 第 16 个 skill 的边际成本被严重低估（顶层 skill + 2 全局 agent 定义 + 安装/所有权/孤儿清理 + principles 新投放面 + agentType/fallback 双路径 + 双宿主行为 + 三档模型映射 + 新旧双流程文档 + CLI 版本兼容 + checkpoint 语义 + memo↔design 双份漂移）；旧入口继续存活 ⇒ 维护成本是**永久叠加**而非替换 |
| C-8 | high | 验收指标会**制造假成功**：grep「砍掉的候选」不能证明发生了 grill；一次轻量 dogfood 不能证明覆盖率；spec-review 没报「上下文缺失」不代表 why 完整；`/usage` 前后差无法归因 |
| C-9 | high | 本仓非托管区宣传新路径、托管区继续宣传旧路径 ⇒ **两个真相源** |
| C-10 | critical | 当前 change **同时押注**新交互、新顺序、新状态产物、两类 agent、模型分档、全局安装、成本优化 ⇒ 任何结果都无法归因。建议拆三步：①可靠性（拷问前移 + memo + canonical 更新 + spec-review 门禁，不用 subagent）②成本实验（同管线 A/B 测 writer/researcher）③产品化（实验达标才新增公共入口 + 下游分发 + 旧入口退役） |

Codex CEO 结论原文：**「当前版本应退回重写 proposal，而不是进入 implementation。」**

<!-- sdflow:outside-voice v1 site="ceo-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="10" truncated="false" -->

### CLAUDE SUBAGENT（CEO — strategic independence）

10 条（F1–F10），独家高价值项：

| # | 严重度 | 结论（含证据锚） |
|---|---|---|
| F1 | **critical** | 核心动机①（grill 可静默跳过）在本方案下**完全未被解决**，而仓内已有一条为它专门设计、成本低两个数量级的解法**从未被比过**：`openspec/issues/todolist/2026-07-todolist.md:232`（**T132，OPEN，2026-07-11**）「spec-review 起手机械核验『grill 已收敛』信号，无信号→REFUSE_START」；载体、fail-closed 语义、先例（ship_gate 设计门新鲜度）全都已定。`design.md:94` 的 D1 备选表**一个字未提**。且新 skill 自己也 `disable-model-invocation: true`（`spec.md:7`）、三原 skill 全保留（`proposal.md:9,57`）⇒ **新管线比它要替代的路径更难被触发，不是更难被绕过** |
| F2 | **critical** | 与 bundle 内既有真相源 `sdflow-init/assets/workflow/generation-process.md` **正面冲突**：该文件 `:47-58` 已规定推荐流水线 = `explore→ff→grill`，`:81-84` 原文警告「否则它会另起一套……形成第二套真相源，正是我们一路在消除的漂移」。四件套**无一处提到该文件**（不在 Context / Decisions / 组件清单 / Impact / tasks）。本仓运行时经 `resolve-workflow.sh` 解析到全局 canonical ⇒ **本仓 agent 读到的仍是旧流水线**。这不是「下游推广」问题，是**即时的、本仓内的**冲突 |
| F3 | high | 成本论证的数字对不上：声称节省是其唯一机制能提供的 **6–8 倍**。单价核实全对（Fable $50/M、Opus $25/M、Sonnet $15/M；`proposal.md:27`、`design.md:133` 的 -70%/-40% 正确），但四件套 42KB、归档中位数 62–65KB ≈ 20–30K output tokens ⇒ 生成环节节省上限 ≈ **$0.88**（Fable 主）/ **$0.25**（Opus 主），而声称节省 $5-7。**且本方案还增加主 session 轮次**（拷问前置 + 亲笔锚点纪要全在主 session）。附：Sonnet 现有 $10/M 促销价 **2026-08-31 到期**，8/31 前的 dogfood 会高估稳态节省约 33% |
| F4 | high | 仓内已有**形状完全相同、悬了 10 天未闭合**的降档省 token 主张：`openspec/roadmaps/workflow-cost-optimization/roadmap.md:84`「核心实现已交付，阶段尚未验收闭合……尚缺①机械镜实际 token/轮下降且墙钟不回归的基线对比」。本 change 既未引用，也未说明为何这次的 `/usage` 粗粒度对比会比上次更可信 |
| F5 | medium | proposal P2 立项理由与仓内数据**直接矛盾**（premise-verification 违规）：`proposal.md:35` 称「补 retro 数据阶段一无独立打点的缺口」，但 `openspec/retro/report.md:77` 有 `\| ff \| 1691.5 \| 9% \|`、`:79` 有 `\| grill \| 345.4 \| 2% \|` —— 打点存在且已参与聚合。真实缺口是 `unknown` 桶占 **56%**（`report.md:72`） |
| F6 | medium | 优化的是 **11%** 的阶段（ff 9% + grill 2%），代价可能落在下游更贵的阶段（spec-review 13%，另一口径 43%）。`design.md:141` 的缓解「spec-review 安全网不变」恰好承认了下游要兜，却把兜的成本算作零。**净方向未论证** |
| F7 | medium | 两份决策记录并存且无优先级规则。实跑 `openspec instructions design --change add-sdflow-spec --json` 核验：design 原生 Sections 只有 `Context / Goals-Non-Goals / Decisions / Risks-Trade-offs / Migration Plan / Open Questions` —— memo 的「**承重约束[]**」在 design.md 里**没有对应槽位**，而它正是 D1/SA-03 里最承重的东西 |
| F8 | medium | `~/.claude/agents/` 是全新安装面、本仓零先例（本机该目录**不存在**；15 个 SKILL.md **无一使用** `agentType`）；`setup.sh:35-70` 的所有权守卫是**目录形状**的（Windows 靠目录内 `.sdflow-skills` marker），散装 `agents/*.md` 在 Windows copy 路径**放不进 marker** ⇒ SA-07 的「含所有权守卫」按既有模式**无法实现**。且命名无 namespace，装进全局后对所有项目可见 |
| F9 | medium | 竞争/替代风险：官方 `claude-plugins-official/plugins/feature-dev` 已发布同形态 7 相位管线 + `code-explorer`（≈researcher）/`code-architect`（≈writer）agent 定义，且**官方打包方式是 `<plugin>/agents/`（与插件同包），不是全局 `~/.claude/agents/`**。差异化不在管线，在 sdflow 自有资产（四件套契约 / 通则托管 / 决策纪要 / TG 目录 / 双机队档位）⇒ 应把 SKILL.md 里「通用管线编排」的部分写薄 |
| F10 | low | `effort` 这个官方首要成本杠杆全程未被考虑：`docs/subagent-definitions-plan.md:235,244-245` 自己写了「主 session effort 开会话时定好、整场不动」，但四件套里 `effort` 只出现在 agent frontmatter，主 session 侧零讨论 |

**CEO subagent 明确核过、判定无问题的维度**（避免误伤）：模型单价与百分比全对；`effort:` frontmatter 真实（官方 claude-security 插件 7 实例实测）；`disable-model-invocation` 真实字段；档位变量与 Agent 工具 `model` 枚举兼容；**D9（纪要落 change 目录而非 scratchpad）三条论证全部成立——是四件套里最扎实的一条决策**；归属修正（superpowers → Matt Pocock）正确；`sync_principles.py` 用 `iterdir()` 自动发现无硬编码地雷；tasks↔requirements 追溯抽查无遗漏；D8 fail-closed 边界划在 openspec CLI 上是对的。

### CEO DUAL VOICES — CONSENSUS TABLE

```
═══════════════════════════════════════════════════════════════
  Dimension                            Claude  Codex  Consensus
  ──────────────────────────────────── ─────── ─────── ─────────
  1. Premises valid?                   ❌      ❌     CONFIRMED(否)
  2. Right problem to solve?           ⚠️部分  ⚠️部分 CONFIRMED(问法切错)
  3. Scope calibration correct?        ❌      ❌     CONFIRMED(否)
  4. Alternatives sufficiently explored?❌      ❌     CONFIRMED(否)
  5. Competitive/market risks covered? ❌      —      单侧(Claude F9)
  6. 6-month trajectory sound?         ❌      ❌     CONFIRMED(否)
═══════════════════════════════════════════════════════════════
6 维中 5 维 CONFIRMED 为负，1 维单侧。零 DISAGREE。
```

---

## Phase 2 · Design Review

**跳过** —— Phase 0 UI scope 检测未命中（本 change 无 view/component/screen/modal/layout 等渲染面；纯 Markdown 编排 + Python/Bash 构建脚本）。

---

## Phase 3 · Eng Review（架构与实现风险）

### CODEX SAYS（eng — architecture challenge）

11 条：

| # | 严重度 | 结论（含证据锚） |
|---|---|---|
| E-1 | **critical** | **脏工作树会被无差别提交，第二个 change 会被摞到当前 feature 分支**。FF-0 只要求「已在 feature 分支就跳过」（`ff-generation-constraints.md:14`），`openspec/CONTEXT.md:107` 明确记录这允许 stacking；B checkpoint 最终执行 `git add -A`（`checkpoint-commit.sh:38,51`）⇒ 用户原有 staged/unstaged/untracked 文件都会随 memo 一起提交 |
| E-2 | high | **「可重入」与「每次 B 收敛都执行 `openspec new change`」互相矛盾**：`spec.md:59`（SA-05）无条件建 change，`spec.md:103`（SA-08）又要求从 ready 项继续。同名 change/branch 已存在时 `new` 或 `checkout -b` 会失败；B 收敛前的 grilling 完全不落盘 |
| E-3 | high | `setup.sh` 现有安装协议**只适用于目录型 skill**：`install_into` 枚举含 `SKILL.md` 的目录（`setup.sh:35`）；Windows marker 写在复制目录内部（`:44`）；孤儿判断固定检查 `$REPO_DIR/$entry_name`（`:102`），而 agent 源实际在 `sdflow-spec/agents/<name>.md`。Unix 分支也会**无条件替换任何同名 symlink**（`:60`），并非真正的所有权守卫 |
| E-4 | high | **回滚方案是假的**：revert 后恰好删掉了负责清理 agent 的代码。当前 setup 只遍历两个 skills 目录（`setup.sh:211`），完整 revert 后旧 setup 根本不会访问 `~/.claude/agents/` |
| E-5 | high | **D3 的「六个工具全只读」是事实错误**（`design.md:98`、`spec.md:87`），且 `proposal.md:69` 宣称不涉信任边界变化也随之失实。Bash 可跑 `rm`/`sed -i`/`git commit`/网络命令，工具 allowlist **不能限制 Bash 子命令**；仓库读取权 + 网络工具叠加还产生**外传风险** |
| E-6 | high | writer 写垃圾或半文件时**现有完成判据产生假绿**：失败表只检查 `resolvedOutputPath` 存在 + `status`（`design.md:118`、`spec.md:69`），但仓库已把 `openspec validate` 定义为四件套结构门（`docs/criteria-mechanization-tracker.md:25`），**计划完全没有调用它** |
| E-7 | high | CLI 部分成功与**陈旧 `decision-memo.md`** 都无可信恢复协议：`design.md:119` 直接假设「未产生半成品」；Phase C 对 memo 只检查「存在且字段非空」（`spec.md:59`）⇒ 早期 abandoned run 的非空 memo 会被无条件当作当前决策 |
| E-8 | high | `$SDFLOW_TIER_*` 从 Bash 到 Agent dispatch **没有实现契约**：`tasks.md:20` 要求 eval 一次后传给 Agent，但 `resolve-models.sh:4` 的接口是向当前 shell `export`；Agent 工具调用不在该 shell 中，仓内已有同根问题记录（`2026-07-todolist.md:35`） |
| E-9 | high | primary `agentType` 与 inline fallback 是**两套行为实现**，但 fallback 永不在健康冒烟里被测（`tasks.md:31` 只在 primary 失败时顺带验证）。仓内最接近的双路径先例不是「自然保持正确」，而是专门建立**字节等值门**（`hack/check_async_branch_parity.py`）+ 大量合成测试，即便如此漂移仍是 OPEN 债 |
| E-10 | high | tasks §4 把大量**自报**行为写成「验证」：完全没有机械测试的是 **SA-01、SA-02、SA-03、SA-04、SA-06、SA-08、SA-10**；SA-05 只验最终存在态；SA-09 只能验 commit 不能验出口文本；SA-07 的 model/effort/fallback 是否生效仍是自报 |
| E-11 | medium | principles 投放的**味源可能错配**：`sync_principles.py:119` 的 `targets()` 只给顶层 skills 配 `SOURCE`，`PROJECT_TARGETS` 固定用 `SOURCE_PROJECT`；若把 agents 直接加进 `PROJECT_TARGETS` 会注入**错误版本**。另：setup 的 `--check` 失败只打印 warning、最终仍 exit 0（`setup.sh:261`），与 SA-07 所称的「门」不一致（`spec.md:97`） |

Codex Eng 附注：所有状态机与入口规则 MUST 在**同一 change 内**更新项目无关的 canonical `generation-process.md:3`，否则 primary、fallback、旧入口会形成**三套行为合同**。并实跑确认 `openspec validate add-sdflow-spec --strict --json` 当前通过（仅说明结构合法，不消除运行期问题）。

<!-- sdflow:outside-voice v1 site="eng-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="11" truncated="false" -->

### CLAUDE SUBAGENT（eng — independent review）

14 条（F1–F14），独家高价值项：

| # | 严重度 | 结论（含证据锚） |
|---|---|---|
| F1 | **critical** | **`openspec status` 的「完成」= 文件存在**，写后核验与可重入建在这个假前提上。CLI 源码实证：`dist/core/artifact-graph/state.js:25-29` — *"Checks if an artifact is complete by checking if its generated file(s) exist."*；实跑输出字段就叫 `existingOutputPaths`。三条决策叠成闭环漏洞：writer 写半截 → 文件存在 → status 报 complete → `spec.md:69` 禁止看内容 → `spec.md:109` 明令「不重写已完成产物」⇒ **坏产物永久锁死**。而 `design.md:162` 还把这套记为「遵守基准 5：让工具自己回答」——**问对了工具，问错了问题**（CLI 回答「存在吗」，设计需要「合格吗」）。仓内**已有** `openspec validate` 结构门（`sdflow-done/SKILL.md:360`、`docs/criteria-mechanization-tracker.md:25`），四件套零处提及 |
| F2 | **critical** | **`agentType` 是 Workflow JS 的参数，不是 Agent 工具的**。设计自己引的来源 `docs/subagent-definitions-plan.md:320` 写明它属 Workflow JS 路径（③），而同文 `:145` 明记 ③ **不采纳** ⇒ 本方案走的必然是 ① Agent 工具，参数名应是 `subagent_type`（本仓三处一致：`.claude/skills/openspec-archive-change/SKILL.md:69` 等）。照 `agentType` 写 ⇒ 派发必然失败 ⇒ SA-07 的 fallback **当场吸收** ⇒ 管线照跑、报告最多一行「降级」。**这是设计好的静默失败通道**：agents 文件铺了、sync 守着、setup 装了，唯独没人在用它，而机械层全绿 |
| F3 | high | 「六者皆只读」不成立（同 Codex E-5）。补充：这句话是 `[grill-amendment]` 标记的——**拷问轮反而把一个错误论断固化成了 spec 里的 SHALL 级描述**。且同一错误在设计引的源里就有先例（`docs/subagent-definitions-plan.md:145` 把 `Read, Glob, Grep, Bash` 标为「只读」）——别拿它当依据。修法推荐：用作用域参数收窄（`:223-224` 实测 `tools` 支持作用域参数）写成 `Bash(git log:*)` 之类；备选是如实改称「检索取向；`Bash` 非只读，只读性由角色纪律约束，属指令层非机械门」 |
| F4 | high | 铺设/守卫/回滚三处声明与 `setup.sh` 实际不符（同 Codex E-3/E-4，证据更细）：`setup.sh:27-32` 的 `is_our_marker_copy()` 判据 `[ -f "$1/.sdflow-skills" ]` 对散装文件是**路径谬误、恒 false**；`setup.sh:106` 的非软链分支判据 `[ ! -d "$REPO_DIR/$entry_name" ]` 对 `sdflow-researcher.md` **恒真**。回滚后两个悬空软链**永久留下**（skills 的 `cleanup_orphans` 是通用的、不随单个 skill 被 revert，agents 的不是）。建议：新写 `install_agents()`，守卫降级为「只接管软链且 readlink 指向本仓」（对齐 `setup.sh:128-134` 处理 `$sdflow/workflow` 的既有 idiom）；**Windows 分支 MUST 明写取舍**（建议不铺 agents、走 fallback），别写做不出来的东西 |
| F5 | high | tasks §4 逐条判：**SA-01~SA-10 中九条零机械测试**（SA-01/02/03/04/05/06/08/09/10）；**4.2 是恒绿门**（原文「失败则按 fallback 路径验证」⇒ 成功算过、失败也算过，**不可能红**）；**全仓无任何 setup.sh 测试**（`hack/tests/` 实查只有 4 个文件）；覆盖图 over-claim（`tasks.md:42` 把 SA-02/03/10 算进没有任务标签支撑的格子） |
| F6 | medium-high | tasks 2.5 的「`resolve-models.sh` eval 一次」是对本仓**已加固协议的回退**：既有协议是五步带防护的且逐条写了为什么（`sdflow-spec-review/SKILL.md:173`：「裸 `eval "$(…)"` 会被脚本缺失静默吞…`eval ""` 返回 0 且旧值原样留存 ⇒ 拿旧宿主假绿」）。且 `resolve-models.sh:74/61/209` 三种失败面都 **exit 0** 只在 stderr 告警 ⇒ 不做 (d) 校验就会拿到空档位。**本轮评审自身即为实证**：本 SKILL 第零步就必须走这套带防护次序 |
| F7 | medium-high | FF-0 幂等规则在「同一分支上开第二个 change」时**失效**：`ff-generation-constraints.md:16-17` 原文「已在 feature 分支 → 跳过（幂等）」，`ff0-branch-guard.py:23,70` 硬拦只看 `{main, master}` ⇒ change B 会落在 `feat/change-A` 分支上。原流程一次一个 change 中间隔 `/clear` 和 merge，新管线**单一入口、会话内可连跑**且 D9 把建分支提到 B 收敛 ⇒ 这个状态变得常见得多。建议改三分支判定（保护分支→建；`feat/{本 change}`→跳过；**其它 feature 分支→停下问人**） |
| F8 | medium | 工作树脏时 `checkout -b` 把脏改动带上新分支 + `git add -A` 全提交 ⇒ D9 的「删分支即净」**失真**（会连用户被裹挟进来的活一起删）。`design.md:110` 的整条推理**只考虑了干净工作树**。且失败模式表六行全是工具失败，**没有「人在 B 中途放弃」这一行**，而 D9 恰恰把它变成常态可达 |
| F9 | medium-high | **fallback 不是等价路径**：`tasks.md:20` 的 fallback 只有「内联通则」，而 agent 定义正文承载的远不止通则（researcher 的「材料不回传」、writer 的「自调 instructions / 禁 AskUserQuestion」在 fallback 下**全部消失**）。结合 F2：若 `agentType` 名字是错的，**fallback 就是唯一实际路径，而它是被减配的那条** |
| F10 | medium | sync_principles 投放面若按「两个 agents 文件」硬编码，SA-07 声称的守卫场景（「新增 agent 定义未纳入投放面 → 变红」）**做不出来**。对比 `skills()`（`hack/sync_principles.py:58-60`）用的就是 `REPO.iterdir()` glob 发现，正是为了这个语义 |
| F11 | medium | 全局 `~/.claude/agents/` 与设计**自己引的调研结论相反**：`docs/subagent-definitions-plan.md:303-308` 倾向「先放本仓验证」，`proposal.md:46` 直接定了相反的却**未给理由** ⇒ 悄悄改了调研结论。且 SKILL 有 `disable-model-invocation` 挡自动触发，**agent 定义没有对应机制**——全局 agent 会进入每个 session 的可选名册，而 `sdflow-spec-writer` 持有 `Write` |
| F12 | medium | 可重入被断言，但**重入的入口判定没有任何 requirement 定义**：change 名从哪来？既有 memo 怎么判「是本次的」？相位 A/B 要不要重跑？现 SA-01 的核验只查「存在且必填非空」，**对陈旧 memo 是全绿的** |
| F13 | low | 新增第 16 个 skill 会让 `CLAUDE.md:192`「投放面 \| **15 个 SKILL.md**」过期，tasks §3 没覆盖。修法按既有：**删掉数字让脚本自己报**（`sync_principles.py:144` 已在打印 `len(targets())`） |
| F14 | low | SA-07 说 `--check` 是「setup.sh 每次执行 → 变红」的门，实际 `setup.sh:261-266` 的 `if !` 结构使 `set -e` 不触发、**退出码恒 0** ⇒ 是**提示不是门**。真正会红的是 `hack/tests/` |

**Eng subagent 明确核过、判定安全的维度**：checkpoint slug 与 `ship_gate.py:1187` 的 `TAG_RE` 不冲突；`decision-memo.md` 不在 ship_gate 设计门监视集内（`sdflow-ship/tests/test_gate_freshness.py:500`）；档位 ID 与 Agent `model` 枚举兼容；openspec CLI 1.5.0 的 `status`/`instructions` 接口存在（proposal「已实测」属实）；`ff0-branch-guard.py:62` 按 `tool_name=="Bash"` 拦，对子代理同样生效（F7 之外的一层兜底）；拷问覆盖率指标的诚实边界划得对，不另开 finding；SKILL.md 体量 168–633 行 / 10.7–75.5KB，落在区间内。

### ENG DUAL VOICES — CONSENSUS TABLE

```
═══════════════════════════════════════════════════════════════
  Dimension                            Claude  Codex  Consensus
  ──────────────────────────────────── ─────── ─────── ─────────
  1. Architecture sound?               ❌      ❌     CONFIRMED(否)
  2. Test coverage sufficient?         ❌      ❌     CONFIRMED(否·九条零机械测试)
  3. Performance risks addressed?      —       ⚠️     单侧(总 token 可能上升)
  4. Security threats covered?         ❌      ❌     CONFIRMED(否·Bash 非只读)
  5. Error paths handled?              ❌      ❌     CONFIRMED(否·陈旧 memo/半写)
  6. Deployment risk manageable?       ❌      ❌     CONFIRMED(否·回滚失效)
═══════════════════════════════════════════════════════════════
6 维中 5 维 CONFIRMED 为负，1 维单侧。零 DISAGREE。
高收敛项：Bash 非只读(E-5≡F3) · 双路径 fallback 无守(E-9≡F9) · 档位变量传递(E-8≡F6)
        · setup.sh 机制不可迁移(E-3/E-4≡F4) · 机械覆盖虚高(E-10≡F5) · 陈旧 memo(E-7≡F12)
```

---

## Phase 3.5 · DX Review（开发者体验）

### CODEX SAYS（DX — developer experience challenge）

8 条：

| # | 严重度 | 结论（含证据锚） |
|---|---|---|
| X-1 | **blocker** | **新旧两套「权威流程」会同时生效**。canonical `workflow.md:13,76` 仍规定 `explore→ff→grill→spec-review`；`workflow.md:5` 规定**全流程不用 `/clear`**，而新 spec `spec.md:113` 要求出口 `/clear`；生成的 `WORKFLOW-GUIDE.md:16` 也继续教旧流程。**人看 README 得到新入口，AI 从 bundle/托管块得到旧入口；两者对 `/clear` 还直接冲突** |
| X-2 | **blocker** | 「拷问不可跳过」仍只是**可伪造的文本约定**：SA-01 的机械条件只是「存在非空决策纪要」（`spec.md:7,13`）。proposal 已承认非机械保证（`:28`），design 又声称「跳过风险结构性消灭」（`design.md:94`）—— **内部自相矛盾** |
| X-3 | high | **首次磁盘价值无上限**：Phase A/B「若干轮」之后才 `openspec new change` 并首次写 memo（`design.md:53,64,90`），成本模型按 **40 轮**估算（`proposal.md:51`）。用户在 B 收敛前退出，仓里什么都没有；SA-04 的可重入只保护「已经收敛」的成果 |
| X-4 | high | 新入口**不可被模型推荐**，旧入口又保持同等可见。计划只要求把新名字加入 README 列表（`tasks.md:26`），没有可靠的首次发现路径；「适用场景」只是任务描述，proposal/spec 并未定义选择规则 |
| X-5 | high | 失败路径**只有处置，没有 actionable diagnostic contract**：CLI 缺失只规定「中止并报错」（`spec.md:59,65`），没要求报告版本/失败命令/根因/修复命令。安装问题会长期隐藏在「能跑但更贵、更慢」的降级模式中。验证任务也没有故障注入 |
| X-6 | high | 迁移计划**没有覆盖真实的 pull→setup skew**：`design.md:147` 只写「pull + setup」，而 `CLAUDE.md:177,182` 明确承认二者之间存在危险窗口。且从开发 checkout 跑 `setup.sh` 会把**全局 skill 链接整体指向 WIP checkout**（`setup.sh:38,68`），而非只测新 skill |
| X-7 | high | **一个超长 SKILL.md 会把关键状态机交给模型记忆**：`tasks.md:14` 要求单文件同时承载三相位、停止条件、dispatch、档位解析、CLI 协议、重试阶梯、Codex 降级、checkpoint、ADR/术语钩子、出口序列。现有 `sdflow-spec-review/SKILL.md` 已 **490 行 / 72,731 bytes**。典型失效 = lost-in-the-middle、提前宣告阶段完成、漏掉降级报告、重入走错分支 |
| X-8 | medium | 成本收益尚未验证，却已决定**最复杂的架构**。建议拆两步：①先交付薄版单入口（拷问前置 + 早期持久化 + 统一文档 + 可操作错误，仍由主 session 生成）②用同一真实 change 做 legacy/thin/subagent **三路 A/B** |

Codex DX 结论原文：**「先修 1–6，再决定是否保留子代理优化。否则这个 change 会让『入口数量』从三个看似降到一个，却把选择、状态和故障复杂度转移到了文档冲突与 AI 指令内部。」**

<!-- sdflow:outside-voice v1 site="dx-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="8" truncated="false" -->

### CLAUDE SUBAGENT（DX — independent review）

6 条，独家最重项：

| # | 严重度 | 结论（含证据锚） |
|---|---|---|
| D-1 | **critical** | **`/clear` 出口序列与 bundle 权威流程的 G1 正面冲突，且四件套完全未处理**。`workflow.md:5-6`「三阶段尽量连续自动运行——`/clear` 由子代理 fresh-context 独立性替代……全流程只在阶段二设计门停一次人类」；`workflow.md:91` 把它标为「**关键设计决策 2. 子代理 fresh-context 替代 `/clear`（最关键，G1）**……故**全流程不用 `/clear`**」；`reference/quality-layering.md:107,117` 同。而 `design.md:104`（D6）的「主审需要冷视角」论证，**恰恰是 G1 已经正面回答过的问题**（`quality-layering.md:101-107`：sdflow-code-review 的裁决冷靠独立编排器 + fresh 子代理 fan-out，不靠 `/clear`），D6 **没有引用、没有反驳、没有说明为何不适用**。且现有 grill→spec-review 过渡（`workflow.md:79-81`）本身就**没有** `/clear`，印证 G1 是当前真实在跑的规则。`design.md:155-163` 的 Compliance 逐条核了 adr/0005、通则托管、host-adaptive、DOC-1、基准 5，**唯独没核 G1** ⇒ 这是**漏查，不是权衡后的显式偏离** |
| D-2 | high | Phase B 收敛前**无任何增量落盘**，且 SA-03 明确禁止用固定轮数兜底（`spec.md:35`）⇒ 轮数无上限。而 D9 否决 scratchpad 的理由正是「session 崩溃即丢承重件」（`design.md:110`）—— **同一脆弱性在 B 收敛前分毫未减**，只是丢失窗口从「到 C 起手」挪到「到 B 收敛」。失败模式表没有一行覆盖「session 在 A/B 收敛前中断」 |
| D-3 | medium-high | 三入口并存但**选择规则完全未定义**：`tasks.md:25` 的「适用场景」四个字是全部四件套里唯一提到选择规则的地方，且没有任何具体标准。对照本仓其它编排器的 description 都写清了何时触发、覆盖什么、与相邻 skill 如何分工 |
| D-4 | medium-high | SKILL.md 体量大概率**创全仓新高**。实测基线：最短 `sdflow-upgrade` 168 行 / 10.7KB；最长两个（均为**单一职责**编排器）`sdflow-spec-review` 490 行 / 72.7KB、`sdflow-code-review` 572 行 / 75.5KB。sdflow-spec 的行为面明显更宽，量级大概率突破 700-800 行 / 80-90KB。且 `design.md` 的 D 系列九条决策里**没有一条谈 SKILL.md 自身的体量控制**；`sdflow-code-review` 达到 75KB 的关键手段之一是把领域清单**外置**到 `code-checklists/domains`，design 没有类似设计 |
| D-5 | medium | 失败/降级报告**只要求「要报」，不要求 problem+cause+fix**（`spec.md:65-67,93-95,101-103`；`design.md:112-121` 的「处置」列全是动作描述）。很容易退化成「spec-writer 失败，已亲写」这种无信息量的一句话 |
| D-6 | low（已检查·非缺口） | Migration Plan 属 `CLAUDE.md` 已知「反向窗口」的具体实例；因 `disable-model-invocation: true`，唯一后果是「敲命令提示不存在」，**无静默误调风险**，不像 `impl-pipeline: tickets` 那例。建议非必须 |

### DX DUAL VOICES — CONSENSUS TABLE

```
═══════════════════════════════════════════════════════════════
  Dimension                            Claude  Codex  Consensus
  ──────────────────────────────────── ─────── ─────── ─────────
  1. Getting started < 5 min?          ❌      ❌     CONFIRMED(否·首落盘无上界)
  2. API/CLI naming guessable?         —       —      N/A
  3. Error messages actionable?        ❌      ❌     CONFIRMED(否)
  4. Docs findable & complete?         ❌      ❌     CONFIRMED(否·双真相源)
  5. Upgrade path safe?                ⚠️      ❌     部分(Claude 判已被通用规则覆盖)
  6. Dev environment friction-free?    ❌      ❌     CONFIRMED(否·超长 SKILL.md)
═══════════════════════════════════════════════════════════════
4 维 CONFIRMED 为负，1 维 N/A，1 维部分分歧（→ 裁决时按 Claude 判定：属已知通用规则实例）。
```

---

## 跨相位主题（2+ 相位独立命中 = 高置信信号）

| 主题 | 命中相位 | 说明 |
|---|---|---|
| **T-A：「拷问不可跳过」不成立** | CEO(C-2, F1) + DX(X-2) | 三处独立命中。且 CEO-Claude 找出仓内已有更便宜的机械解（T132） |
| **T-B：与 bundle canonical 规则冲突（双真相源）** | CEO(F2, C-9) + Eng(Codex 附注) + DX(X-1, D-1) | **五处独立命中**，且分别指向**三个不同文件**：`generation-process.md`（流水线）、`workflow.md`（`/clear` G1 + 流水线）、`WORKFLOW-GUIDE.md`（生成物）。本轮最高收敛项 |
| **T-C：成本论证不成立** | CEO(C-4, F3, F4, F6) + DX(X-8) | 三种独立算法都得出「不支持」：混淆 token/单价（Codex）、绝对值差 6–8 倍（Claude）、优化 11% 阶段而代价落下游（Claude） |
| **T-D：机械覆盖虚高 / 验收会制造假成功** | CEO(C-8) + Eng(E-10, F5) | 收敛于「九条 requirement 零机械测试」+「4.2 是恒绿门」 |
| **T-E：scope 过大、应拆分** | CEO(C-3, C-10) + DX(X-8) | 三处独立给出**几乎相同的拆分建议**（可靠性 → 成本实验 → 产品化） |
| **T-F：状态机缺失（重入/陈旧 memo/脏树/第二 change）** | CEO(C-1) + Eng(E-1, E-2, E-7, F7, F8, F12) + DX(D-2) | 收敛于「阶段一需要持久状态与受控转换」 |

---

## Decision Audit Trail（autoplan 自动决策）

| # | 相位 | 决策 | 分类 | 原则 | 理由 |
|---|---|---|---|---|---|
| A1 | Phase 0 | UI scope = 否 → 跳过 Phase 2 | Mechanical | P3 | 无 view/component/screen 渲染面 |
| A2 | Phase 0 | DX scope = 是 → 跑 Phase 3.5 | Mechanical | P1 | 交付物是开发者工具（skill/CLI/agent 定义），命中 SKILL.md / Claude Code / CLI / agent 多项 |
| A3 | Phase 0.5 | 双声全开 | Mechanical | P6 | codex 0.145.0 可用、auth 通过 |
| A4 | Phase 1 | **premise gate 不弹窗** | — | G2 铁律 | sdflow-spec-review 规定中途不 AskUserQuestion；premises 结论一并进「决策登记区」由设计门拍板 |
| A5 | Phase 3/3.5 | Eng 与 DX 并行（偏离严格串行） | Taste | P3 | 省一轮墙钟；代价 = DX 少 Eng 输入。已如实标注，未观察到漏项 |
| A6 | Phase 4 | **Final Approval Gate 不弹窗** | — | G2 铁律 | 同 A4；User Challenge 一并上抛 |
| A7 | 全程 | 跳过 gstack 自身运维提示（telemetry/routing/feature discovery） | Mechanical | P3 | 与本次评审目标无关，且均需 AskUserQuestion（违 G2） |

## User Challenge（两个模型都认为用户的既定方向应改变 —— 从不自动裁决）

**UC-1：两个模型都建议把本 change 拆分，而非按当前形态整体推进。**

- **用户/上游说的**：一个 change 交付 `sdflow-spec` 完整管线（skill 本体 + 2 个 agent 定义 + setup 铺设 + sync 投放面 + 文档改写）。
- **两个模型都推荐**：拆成「①可靠性（拷问前移 + 结构化 memo + canonical 规则更新 + spec-review fail-closed 门，**不用 subagent**）→ ②成本实验（同管线 A/B 测 writer/researcher）→ ③产品化（实验达标才新增公共入口 + 下游分发 + 旧入口退役）」。
- **为什么**：当前 change 同时押注新交互、新顺序、新状态产物、两类 agent、模型分档、全局安装、成本优化 ⇒ 任何结果都无法归因；且成本收益（唯一支持「上 subagent」的理由）本身未被证实（T-C）。
- **可能缺的上下文**：用户已在 CLAUDE.md 基准 4 明确「拆分标准 = 一个 change 一个完整阶段结果，**不按同批来源/顺手/凑票数**」，并明确「碎片化是反复对现状提疑问 + 给妥协方案的根因」。**两个模型都不知道这条约束。** 若用户认为「阶段一单一入口管线」本身就是一个完整内聚阶段结果，则当前 scope 是对的，拆分反而违反基准 4。
- **如果我们错了，代价是**：把一个内聚交付物拆成三个 change，多付两轮 workflow 循环固定成本（本仓已记录该成本很高），且 ① 单独交付的价值有限。
- ⚠️ 两个模型均未把此标为安全/可行性风险，属**取向分歧**，非风险警报。
- **用户原方向为默认。**

---

*Step1 广审完成 · autoplan 原生 · 双声全开 · 无降级*
*findings 总计：Codex 29 条（CEO 10 / Eng 11 / DX 8）+ Claude 子代理 30 条（CEO 10 / Eng 14 / DX 6）= 59 条（未去重）*
