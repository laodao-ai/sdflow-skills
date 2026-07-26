# Task 5 · 阶段二成本与质量判定（A/B 三路 + 论证密度比对）

> 票面：tasks 7.1–7.4 + 阶段二验收门 · **R-ID：SA-02**
> 前置：Task 1–4 已收票；5.1 GO/NO-GO 实测门已判 **GO**（`task4-agents-step1/step2.md`）。
> **未动** `proposal.md` / `design.md` / `specs/` / `tasks.md` / `superpowers-plan.md`。

## 0. 结论摘要

| 门条件 | 状态 | 依据 |
|---|---|---|
| **5.1 GO** | ✅ 达标 | Task 4 主 session 判 GO + step2 §4.1 独立复现（全新 `claude -p` 派 `sdflow-local-researcher` 成功） |
| **7.4 S3/S4/S5**（安全前提） | 🟡 **S4 机械达标；S3/S5 仅「指令在场锚 + 语义残余」** —— 我判**满足验收门的合法形态**，理由见 §7 | `task4-agents-step2.md` §6 · `task4-agents-fix1/fix2.md` |
| **7.2 subagent 路成本与质量均不劣于 thin 路** | ❌ **不达标** —— 成本：**未观察到 subagent 更便宜**（$11.68 vs $9.06；**幅度不作结论依据**，见 §3.2）；质量**不优于**（冷审 Important 1 vs 0） | 本报告 §3 |
| **7.1 机械层全量** | ✅ 全绿 | §8 |

⇒ **门判定：不达标 ⇒ 按 tasks.md 已声明的失败分支「回退到阶段一薄编排形态」。**
回退动作已执行（§9），agent 定义**作为未启用资产保留**。
🔴 **放行与否是人的决定** —— 本节只给逐条状态与依据，**未宣告启动阶段三**，也**未删除**任何阶段二资产。

### 0.1 数据出处与可复核性（先读这条）

**原始 JSON 已归档进仓**：`openspec/changes/add-sdflow-spec/impl-reports/task5-logs/`
（12 轮 `turn*.json` + 3 份冷审 `review.json` + 作废轮 + 全部 prompt + 驱动脚本 `harness/`）。
§3 的五项指标**全部可从该目录重算**——本轮已重算一次，与表内数字**逐位吻合**。

⚠️ **两条已订正的过度声称**（原稿有误，现已改写，理由见 §3.2）：

1. 原稿称两轮被「驱动脚本外层 10 分钟上限 **SIGKILL**」——**三处均不成立**。实为 `claude` CLI
   自行 `aborted_streaming`；驱动脚本的唯一上限是 `timeout 3000`（50 分钟），**未触发**。
2. 原稿称该污染「只会抬高 thin/legacy，∴ 方向稳健」——**该论证只走了一支**。现改为**双向不确定**，
   **成本幅度（+28.9% / +42.7%）不再作为结论依据**。

⚠️ **不可复跑的那部分**：三个沙箱 clone 已 `rm -rf`，∴ §5 引用的 `design.md` 行与 §3.4 的
`grep`/`diff` 输出**不能再对源文件复跑**（补救路径见 §10 第 10 条）。**指标可复核，文件级举证不可复跑**——两者要分开读。

---

## 1. 逐条验收标准 → 证据

| # | 验收标准 | 状态 | 证据 |
|---|---|---|---|
| 1 | 三路各跑一次同一真实复杂 change，五项指标齐全且可复核（不是估算） | ✅ 四项实测 / 1 项口径降级 | §2 实验设计 · §3 指标表；每一次调用的完整 JSON（含 `usage` / `modelUsage` / `total_cost_usd` / `duration_ms`）**已归档进仓** `impl-reports/task5-logs/`，指标可逐位重算（§0.1）。⚠️ **文件级举证**（§5 的 `design.md` 行、§3.4 的 `grep`/`diff`）跑在已删除的 clone 上，**不可复跑** |
| 2 | 论证密度比对有具体举例（哪条砍掉的候选丢了/留了），不是形容词级结论 | ✅ | §5：**D0b「运行时指针」候选 + 其反例在 subagent 路的 `design.md` 里整条消失**，而 thin/legacy 两路都留住了（贴了三份文件的实际行） |
| 3 | 阶段二验收门结论落纸：安全前提是否满足、成本质量是否不劣于 thin、判 GO 还是回退 | ✅ | §0 表 + §7（安全前提逐条）+ §6（我的判定与依据） |
| 4 | 判回退时：回退动作已执行到位，agent 定义去留有明确处置，hand-off 如实记录 | ✅ | §9（`sdflow-spec/SKILL.md` 外派协议节改为「未启用资产」+ C.3 交叉指针；三个定义保留） |
| 5 | 成本结论标注样本量与统计显著性边界（N=1 不得表述为已证实） | ✅ | §3 表头 + §10 诚实边界第 4 条，全文一律写「N=1，方向性证据，非统计显著」 |

---

## 2. 实验设计

### 2.1 实验对象（同一个真实复杂 change，非玩具）

从 `openspec/issues/todolist/2026-07-todolist.md` 选 **T163（并连带 T161）**，均为 `OPEN`、挂 change
`async-outside-voice`、**不属于本 change**：

- **T163**（`:23`）：`sdflow-spec-review` / `sdflow-code-review` 的 async host 调度段是两份物理副本，
  靠 `hack/check_async_branch_parity.py`（162 行）的逐字节等值门守住；要求做 DRY 全抽取。
- **T161**（`:21`）：该等值门只覆盖 marker 段，圈外 preflight / fallback / 锚行段两层也高度相似但漂了不会红。

选它的理由：① 有**承重约束**（「skill 是独立分发单元」——一旦被证伪，整个「注入 vs 指针」的候选表塌缩）；
② 有 ≥3 个真实候选（注入式 / 运行时指针 / 扩大等值门）与多处落点取舍；③ 仓内有同构先例
（`hack/sync_principles.py`）可供接地核验；④ 体量适中，一轮内能出完整四件套。

**三路用完全相同的需求文本**（`scratchpad/ab/prompts/req.txt`），否则不可比。

### 2.2 三条路的形态

| 路 | 形态 | 起手 |
|---|---|---|
| **legacy** | 旧三入口：`/opsx:explore` → `/opsx:ff` → `/grill-with-docs` | 逐步由「人」敲，prompt **原样取自** `sdflow-init/assets/workflow/prompts/step1/2/3-*.md` |
| **thin** | 阶段一薄编排：`/sdflow-spec`，检索与生成**均主 session 亲做**，全程不派子代理 | `/sdflow-spec` + 需求 + 「按阶段一薄编排形态跑」 |
| **subagent** | 阶段二外派：`/sdflow-spec`，仓内检索派 `sdflow-local-researcher`(light)、逐产物生成派 `sdflow-spec-writer`(mid)，判断仍主 session | 同上 + 外派指令 + 本机队档位解析结果（strong=opus / mid=sonnet / light=haiku） |

🔴 **一个与票面预设不同的实测事实（影响「真实性上限」的判断）**：
票面写「`/sdflow-spec` 与 `/grill-with-docs` 因 `disable-model-invocation: true` **模型唤不起**
⇒ 只能读 SKILL 文本按其指令逐步执行」。**实测：作为「人敲的那一条 prompt」时，斜杠命令照常展开。**

```
$ claude -p --permission-mode dontAsk <<< "/sdflow-spec\n\n…你的上下文里现在有没有出现小节标题「相位 A · 澄清」？"
(1) 有——上下文里出现了小节标题「相位 A · 澄清」（sdflow-spec 的 SKILL.md 全文已被展开进本轮上下文）。
```

对照实测：**模型自己**判断能否唤起时答「不能」（`disable-model-invocation` 对模型侧生效）。
⇒ `disable-model-invocation` 挡的是**模型自主调用**，不挡**用户输入里的斜杠命令**。
∴ 三路都是**真跑了 SKILL 全文指令**，不是「读文件模仿」——比票面预期的保真度更高。

### 2.3 「人」由谁扮演（结构性边界，不可绕过）

三路的需求方由本 Task 5 的实验驱动 agent 扮演（票面明写「澄清/拷问的对端由你扮演」）。
**拍板文本三路完全一致**（`prompts/decide.txt`），只在各路自己提出的额外问题上分叉。
⇒ **「判断质量」这一维本轮结构上无法验证**，与 `tasks.md` 覆盖图把 7.3 标为「**人核**」的口径一致。

### 2.4 harness 与落盘

- 每路 = 一个**独立 git clone**（`--no-hardlinks`）到 scratchpad，分支 `main` @ `3b7c8d0`，
  FF-0 hook / 全局 skills / `~/.sdflow/hack/*` 与真实环境同。
- 每一轮 = `claude -p --model opus --output-format json --permission-mode acceptEdits
  --allowedTools Bash Read Write Edit Agent WebFetch WebSearch TodoWrite -r <sid>`，prompt 走 **stdin**
  （`--allowedTools` 是可变长参数，跟位置参数会吞掉 prompt ⇒ 实测报
  `Error: Input must be provided either through stdin or as a prompt argument`）。
- **主 session 档位 = opus 三路一致**（`resolve-models.sh` 本机队 `STRONG=opus`），子代理按外派协议取
  mid=sonnet / light=haiku ⇒ 「生成环节降档省钱」这条假设才有被检验的机会。
- **三路 12 轮共用同一个驱动脚本 `harness/turn.sh`，唯一外部时限 = `timeout 3000`（50 分钟）**
  〔`task5-logs/harness/turn.sh:14,17`〕。**harness 全程未改**：`turn.sh` 的 mtime（`01:34:16`）
  早于**最早**一轮日志（`01:37:42`）⇒ 三路条件一致，**不存在实验中途变更时限**。
  ⚠️ 原稿多处写的「外层 10 分钟上限」**在脚本里不存在**，已订正（§3.2）。
- 全部 JSON **已归档进仓**：`impl-reports/task5-logs/logs/<lane>/turn*.json`
  （另有 `*.out` = 各轮 result 文本、`*.err` = shell stderr、`logs-discarded-permfail/` = 作废轮、
  `prompts/` = 三路全部输入、`harness/` = 驱动脚本）。**沙箱 clone 本身按纪律未带回，且已删除。**
- **一处条件不对称（如实记录）**：保留的 12 轮里只有 **thin turn02 有 1 次 Bash `permission_denials`**
  （`git checkout -b` + `openspec new change` 那条），legacy / subagent 全程 0 次
  〔`task5-logs/logs/*/turn*.json` 的 `permission_denials` 字段可复核〕。thin 在 turn03 完成了建分支与
  四件套，未见工作丢失，但**三路并非逐轮零差异**。
- **被作废并重跑的一轮（如实记录）**：首次三路 turn1 用 `--permission-mode dontAsk`，Bash 被逐命令
  分类器拒（thin/subagent 连 `openspec --version` 都跑不了，legacy 只拿到受限 Bash）⇒ **三路条件不一致**，
  整轮作废、clone 全部 `reset --hard` 后按 §2.4 的配置重跑。该轮花费 **$4.19**（legacy $1.90 /
  subagent $1.41 / thin $0.88），**不计入 §3 的任何指标**，日志留在 `logs-discarded-permfail/`。
  另有 3 次 harness 能力探针（斜杠命令展开 / 权限配置 / usage 字段）约 $0.97，同样不计入。

---

## 3. 五项指标（实测）

### 3.1 主表

> 🔴 **N=1（一个 change、一次跑、单一模型机队）。以下是方向性证据，MUST NOT 表述为「已证实」。**
>
> 🔴 **「subagent vs thin」一列的百分比 = 原始观测差，不是效应量。** thin / legacy 各含一轮被中止的
> 轮次（§3.2），**两个方向的偏差都不能排除** ⇒ **幅度不作结论依据**，只支持「未观察到 subagent 更便宜」。
> 数字保留是为可复核，不是为下结论。

| 指标 | legacy | thin | **subagent** | subagent vs thin |
|---|---:|---:|---:|---|
| 与人的往返轮次（实质拍板） | 3 | **1** | 2 | 更多 |
| 模型侧总轮次（`claude -p` 调用） | 6 | 3 | 3 | — |
| **总 token**（in+out+cacheRead+cacheCreate） | 15,197,279 | **8,807,313** | **12,571,980** | **+42.7%** |
| ├ opus（主 session） | 15,197,279 | 8,807,313 | 7,139,532 | **−18.9%** ✅ |
| ├ sonnet（spec-writer） | — | — | 1,878,501 | +新增 |
| └ haiku（local-researcher） | — | — | 3,553,947 | +新增 |
| **总美元**（harness `total_cost_usd` 实价） | $14.8596 | **$9.0622** | **$11.6796** | **+28.9%** |
| ├ opus | $14.8596 | $9.0622 | $8.0210 | −$1.0412 ✅ |
| ├ sonnet | — | — | $2.6824 | +$2.6824 |
| └ haiku | — | — | $0.9762 | +$0.9762 |
| **墙钟**（Σ `duration_ms`，模型侧） | 1655 s (27.6 min) | 1416 s (23.6 min) | **1308 s (21.8 min)** | **−7.6%** ✅ |
| **人工返工量**（§3.3 定义） | 3 | **2** | 3 | 更多 |
| **冷审 findings**（§3.4 口径） | 1 Important | **2 Minor（0 Important）** | 1 Important | 更差 |
| 冷审 findings 采纳判定率 | 1/1 | 2/2 | 1/1 | 持平 |
| 四件套总行数（不含 memo） | 700 | 454 | 407 | — |

**这张表最要紧的一行是 token 的三段分解**：外派**确实**把主 session（opus）的 context 压下去了
**−1.67M token / −$1.04**；但 researcher + writer 自己烧掉的 **5.43M token / +$3.66** 把它吃穿了，
**净 +$2.62**。⇒ D2 押注的「外派省钱」在本样本上**未见兑现**。

⚠️ **这两个数的可信度不同，别混着读**：
**「+$3.66 的外派开销」是 subagent lane 内部的自有账**（三轮全部正常结束、无中止轮），
**不依赖与 thin 的比较** ⇒ 不受 §3.2 污染影响。
而**「−$1.04 的 opus 侧节省」是 subagent 与 thin 相减得来的**（$9.0622 − $8.0210）⇒ **受污染影响**，
幅度不作结论依据。两者相减得到的「净 +$2.62」因此**同样只是观测差**。

### 3.2 逐轮原始数据

```
=== legacy (6 turns)                    === thin (3 turns)                   === subagent (3 turns)
   turn01  $ 1.1633   210s                 turn01  $ 1.1232   183s               turn01  $ 1.6444    30s
   turn02  $ 2.8426   599s  err=True*      turn02  $ 2.9439   599s  err=True*    turn02  $ 1.7937    78s
   turn03  $ 2.4544   142s                 turn03  $ 4.9951   634s               turn03  $ 8.2415  1200s
   turn04  $ 2.7816   153s                 TOTAL   $ 9.0622  1416s              TOTAL   $11.6796  1308s
   turn05  $ 0.6200    87s
   turn06  $ 4.9976   464s
   TOTAL   $14.8596  1655s
```

`*` **两轮被中止（`is_error=true`）—— 机制已核，原稿归因是错的**

thin/legacy 的 turn02 各被中止一次（subagent 三轮均正常结束）。**原稿写「被驱动脚本外层 10 分钟上限
SIGKILL 掉」，三处均不成立**，实际情形如下（全部可在 `task5-logs/` 复核）：

| 事实 | 证据 |
|---|---|
| 驱动脚本的唯一外部时限 = `timeout 3000`（**50 分钟**），**不可能在 ~10 分钟触发** | `harness/turn.sh:14,17` |
| **不是 SIGKILL** —— SIGKILL 不留任何输出，而这两轮都留下了**完整 JSON** | `logs/{thin,legacy}/turn02.json` |
| 两轮的 shell stderr **均 0 字节**（无信号 / 超时消息） | `logs/{thin,legacy}/turn02.err` |
| CLI 自报 `terminal_reason=aborted_streaming` · `subtype=error_during_execution` · `stop_reason=tool_use` · `errors=["[ede_diagnostic] …"]` | 同上 |
| **不是 turn 上限**：legacy turn06 跑到 `num_turns=34` 正常结束 | `logs/legacy/turn06.json` |

⇒ **实际情形 = `claude` CLI 在流式执行中途自行中止（`aborted_streaming`），非外部信号、非驱动脚本限时。**

🔴 **触发源无从确证**：`duration_ms=598753`（≈598.75 s）紧邻 600 s，且**恰好这两轮**的 wrapper stdout
为 0 字节（其余十轮均非空）——**指向**「编排层那次 Bash 调用自身的 600 s 上限终止了 wrapper」。
但这是**推断，不是实测**，本轮无从证实，**不写成结论**。

⚠️ **这两轮的 `duration_ms` 不可当实测墙钟**：两条独立 lane 报出**逐位相同**的 `598753`，
且 `num_turns` 同为 26 —— 独立进程不可能如此吻合。（对照：`duration_api_ms` 两轮**不同**，
553824 / 567501。）∴ 含它的 legacy / thin 墙钟合计（1655 s / 1416 s）相应偏软。

**计费是否丢失 —— 已核，未发现丢失**：两轮的 `total_cost_usd` **不是 0**，且与其自报 token
在标准 Opus 价位上**闭合**。把 12 轮全部按 in \$5 / out \$25 / cacheRead \$0.5 / cacheWrite-1h \$10
每 MTok 折算，**含这两轮在内 12/12 轮的 `costUSD` 与折算值之比 = 1.0000**（脚本化复核，见 §0.1 数据）。
⇒ 「中断轮计费整体丢失」这一支**在本数据上不成立**。
**残余（不可排除）**：上式只证明「费用与**自报**用量一致」，**不能**证明自报用量覆盖了该轮全部 API 活动
——若用量计数器提前停止，费用与 token 会**一起**少报，比值仍是 1.0000。本轮无法排除这一支。

**⇒ 污染对成本结论的影响：双向不确定（两支证据强度不对称）**

| 支 | 方向 | 证据状态 |
|---|---|---|
| ① 中断轮的开销**部分是白花的**（工作在 turn03 经 `-r` 续跑时部分重做），且多一次 turn 边界 | **抬高** thin/legacy ⇒ subagent 的相对劣势被**高估** | 有证据：两轮各计入 \$2.84 / \$2.94，其产出未直接进入终态 |
| ② 中断轮用量**少报** | **压低** thin/legacy ⇒ subagent 的相对劣势被**低估** | 无正面证据（比值闭合），但**不可排除**，且偏差量**无界** |

🔴 **∴ 幅度（+28.9% / +42.7%）含不可信轮次，MUST NOT 作为结论依据。**
成本轴本轮能说的只有一句：**未观察到 subagent 路更便宜。**
MUST NOT 读成「已证实 subagent 更贵」，也 MUST NOT 读成「已证实两者持平」。

### 3.3 「人工返工量」的口径（三路同一口径）

**定义 = 产物成文后被下游环节推翻、需要改写的判断性偏差条数**（措辞压缩不计；下游环节 = 本路径
自带的终审/拷问 + 统一冷审）。

| 路 | 条目 |
|---|---|
| legacy = **3** | grill 推翻 2 条自己 ff 阶段写的事实（① marker 行属真相源、非注入器生成 ⇒ tasks 3.1 的「109 行正文」错；② `render()` 在块前后强插空行 ⇒ **当场推翻 tasks 4.5「搬运保真 diff 必须为空」硬门**）+ 冷审 1 条（proposal 的「已实证」diff 命令用了错误行号偏移） |
| thin = **2** | 终审无成文后改动；冷审 2 条（`host-adaptive-execution` 实为 **9** 条 requirement 而三份产物都写「10 条」；proposal 无独立 Success Metrics 节） |
| subagent = **3** | 主 session 终审抓出 **writer 产出的 2 条事实错误**（`tasks.md` 5.1 的 grep 判据「凭空造」、8.1 说「照抄字段」而 `todolist.py add` 实吃 JSON）+ 冷审 1 条（前置门判据过严） |

🔴 subagent 那两条是**直接支持 design D2「未被原设计正视的反证」的实证**：writer 拿着纪要写 tasks
时**编了两条不存在的接口事实**，主 session 读回修正 = **双写**。

### 3.4 「findings 数与采纳率」的口径（**已降级，与真 spec-review 不同**）

跑三次完整 `/sdflow-spec-review`（autoplan + 多镜 fan-out + outside-voice）成本会数倍于实验本身。
**降级为**：三路各跑**一次形态完全相同的冷启动独立评审子进程**（`claude -p --model sonnet`，无对话历史，
同一份 prompt 模版 `prompts/review.txt`，五镜：完整性 / 可验收性 / 论证密度 / 接地（**要求真开文件核对**）
/ 对抗）。**MUST NOT 把它读成「spec-review findings 数」**——镜数与深度都远小于真 spec-review。

| 路 | Critical | Important | Minor | 内容 |
|---|---:|---:|---:|---|
| legacy | 0 | **1** | 0 | design/proposal 声称 code-review 侧行号 `+2` 偏移，实为 **0**；据此写的「已实证」diff 命令不成立 |
| thin | 0 | **0** | 2 | ① `host-adaptive-execution` 说「10 条 requirement」实为 9；② proposal 缺 Success Metrics 节 |
| subagent | 0 | **1** | 0 | tasks 0.1 前置门以「整份 change 完成」为判据，比真实的函数级冲突严格得多，会无限期卡门 |

**采纳率的口径**：本轮**没有**把 findings 喂回去让各路修改（那会再引入一个变量）。
所报的是**我逐条机械核实后判定「是真缺陷、应采纳」的比例**：

```
$ grep -c "^### Requirement" thin/openspec/specs/host-adaptive-execution/spec.md
9                                        # ⇒ thin 的「10 条」确为事实错误，采纳
$ grep -n "outside-voice helper 调用协议" legacy/sdflow-{spec,code}-review/SKILL.md
…/sdflow-spec-review/SKILL.md:358:## outside-voice helper 调用协议…
…/sdflow-code-review/SKILL.md:358:## outside-voice helper 调用协议…     # ⇒ 偏移为 0，非 +2，采纳
$ diff <(sed -n '361,379p' legacy/sdflow-spec-review/SKILL.md) <(sed -n '361,379p' legacy/sdflow-code-review/SKILL.md)
(空，exit 0)                              # ⇒ 同行号区间才逐字节相同
```

三路均 **100%**（legacy 1/1 · thin 2/2 · subagent 1/1）⇒ 该指标本轮**不具区分力**，如实报告。

### 3.5 按 `design.md` NFR 表的 $15/M 折算

tasks 7.2 要求「8/31 前按 Sonnet 稳态价 $15/M 折算」。subagent 路的生成环节由 sonnet 承担，
输出 **35,654 token** ⇒ **$0.535**（输出侧）。对照 `design.md` NFR「生成环节节省上限 ≈$0.25（Opus 主）」：
本轮 opus 侧实际省下 **$1.04**，比 NFR 预估的上限更多——**但仍被 $3.66 的外派开销覆盖**。
⇒ NFR 那一格的估算方法（只算「生成环节输出 token 的档位差」）**系统性漏掉了子代理自身的 context 成本**，
这是本轮最有价值的一条方法论修正。

---

## 4. 三路的完整记录

### 4.1 legacy（`feat/dry-async-branch-block`）

| 轮 | 输入 | 产出 |
|---|---|---|
| t1 | `/opsx:explore` + 需求 | 区段地形实测表（ZoneA 19 / 站点枚举 2 / marker 87 / ZoneB 5 / ZoneC 8），5 处待拍板 |
| t2 | 拍板 + `step2-ff.md` 原文 | — （被外层 10 min 上限中断） |
| t3 | 「继续」 | 四件套 + `checkpoint(ff)` `8f07b88`，`validate --strict` 绿 |
| t4 | `step3-grill.md` 原文 | grill 提问 Q1（块边界要不要含 ` ``` ` 围栏）+ **两条事实自纠** |
| t5 | 「按 (a) 定」 | grill 提问 Q2（投放面写死清单 vs marker 发现）+ 一条风险面缩小实测 |
| t6 | 「按 marker 发现定，收敛」 | `[grill-amendment]` 落盘 + `openspec/adr/0031` + `CONTEXT.md` 术语，`checkpoint(grill)` `961cc3c` |

产物：`proposal.md` 96 / `design.md` 307 / `specs/managed-block-injection/spec.md` 197 / `tasks.md` 100 行。

### 4.2 thin（`feat/unify-ov-protocol-source`）

| 轮 | 输入 | 产出 |
|---|---|---|
| t1 | `/sdflow-spec` + 需求 + 薄编排 | 第零步（CLI 预检 / 档位 / 重入探测）+ 三条实测（**114/116 行两侧逐字相同，门只守 87 行**）+ 相位 A 第 1 问 |
| t2 | 拍板 | —（外层中断；期间已过 B.1 起手三步、建 change 目录、写 memo 草稿） |
| t3 | 「继续」 | `decision-memo.md` 定稿（`decision_hash=ae5e393764ee`）+ 四件套 + 两个 checkpoint + 终审 + **原样贴出口序列** |

产物：`decision-memo.md` 81 / `proposal.md` 60 / `design.md` 236 / `specs/determinism-guards/spec.md` 66 / `tasks.md` 92 行。
**全程零子代理、零降级事件**（与指定形态一致）。

### 4.3 subagent（`feat/dry-async-dispatch-block`）

| 轮 | 输入 | 产出 |
|---|---|---|
| t1 | `/sdflow-spec` + 需求 + 阶段二外派指令 | 派 `sdflow-local-researcher`(haiku) 做仓内检索并**只回传结论 + file:line**；相位 A 第 1 问 |
| t2 | 拍板 | 三条新事实（`setup.sh` 两门均 warn-only、`sync_principles.targets()` 是二元组、`specs/**` 无相关 Requirement）+ 范围边界追问 |
| t3 | 「只做 async 调度面」 | memo 定稿（`5241b49ae1ac`）+ **逐产物派 `sdflow-spec-writer`(sonnet)** 生成四件套 + 终审改 2 处 + 两个 checkpoint |

产物：`decision-memo.md` 89 / `proposal.md` 60 / `design.md` 165 / `specs/shared-block-injection/spec.md` 79 / `tasks.md` 103 行。
**外派链路全程可用，零降级**（三个 `subagent_type` 全部解析成功 ⇒ 与 5.1 的 GO 一致）。

---

## 5. 论证密度人工比对（tasks 7.3）

**比的是**：砍掉候选的**具体反例**是否留存 · 承重约束的**推导链**是否完整。**不是**查字段填没填。
**对照面**：subagent 路的 `design.md` 由 `sdflow-spec-writer` **只拿着 `decision-memo.md`** 写
（无拷问对话上下文）；thin / legacy 两路的 `design.md` 由主 session 在**完整上下文**里亲写。

### 5.1 🔴 具体举例：本 change 最承重的那条推导链，在纪要驱动路径上**从 design.md 整条消失**

承重约束 = **「skill 是独立分发单元 ⇒ 单一源只能 build-time 内联，运行时指针不可行」**。
它一旦被证伪，「注入式」与「指针式」的候选表整个塌缩 —— 是这份设计的地基。

**subagent 路的 `decision-memo.md` 完整写着它**（D0b）：

> **砍掉的候选**：运行时指针 + `resolve-*.sh` 式解析。**砍它的具体反例**：skill 是独立分发单元——
> `setup.sh` 把每个含 `SKILL.md` 的顶层目录 symlink 进 `~/.claude/skills/`，装完后它跑在**别的项目**里，
> `~/.sdflow/` 之外的本仓路径一律不可达；指针化 = async 调度协议对「装在别的项目里的 skill」失效。

**而 writer 写出来的 `design.md` 里，这条整条不见了**：

```
$ grep -n "指针\|独立分发\|symlink" subagent/…/dry-async-dispatch-block/design.md
157:- **回退路径**：`git revert` …（注入是内联，不是指针——回退动作直接恢复 revert 之前的文件内容…）
```

只剩「回退路径」里一句顺带的括注。design.md `:60` 明写
「另有 D0/D0b/D0c 三条范围性拍板列于 Context 一节，此处不重复展开」——**而 Context 一节
（`:1-30`）通篇没有这条约束、没有那个被砍的候选、更没有那个反例**（实读全文核对）。

**对照两条有完整上下文的路径，同一条约束都留住了，且更强**：

```
$ grep -n "指针\|独立分发\|symlink" thin/…/unify-ov-protocol-source/design.md
21:1. **消费者是读 SKILL.md 的模型，不是能 `import` 的解释器**。skill 以 symlink 装进 ~/.claude/skills/
   独立分发，跑在别的项目里读不到本仓任何文件（`hack/sync_principles.py:3-6`）。⇒ 单一源**只能
   build-time 内联**，运行时指针 / include 不可行。这是本 change 与 `adr/0027` 的**关键分野**。

$ grep -n "指针\|独立分发\|symlink" legacy/…/dry-async-branch-block/design.md
19:- **skill 是独立分发单元**——`setup.sh` 用绝对路径 symlink 装进 ~/.claude/skills/ 与 ~/.codex/skills/…
123:**砍掉 (a) 运行时指针 / include**（SKILL 里写「见 `shared/skill-blocks/ov-protocol.md`」）。
124:**具体反例**：…此时 `shared/skill-blocks/` 既不在 cwd 下、也不在 skill 目录下——指针指向一个
   当场不存在的路径。这与 `sync_principles.py` 头注释里已登记的理由同源。
129:**承重约束的证实**：「内联是必需的」这条前提由 symlink 分发机制**证实**——它**可被证伪**，只要
   能演示 skill 运行时可稳定解析回本仓路径；本 change 未找到该路径…
```

legacy 甚至多写了**证伪路径**（thin 有约束与反例、无显式证伪路径；subagent 三者全无）。

### 5.2 未丢的那部分（如实记录，别只挑坏的说）

subagent 路的 `design.md` 对 **D1–D6** 六条决策的「砍掉的候选 + 具体反例」**逐条照搬 memo 原文**，
密度与 memo 持平（D3 三个落点候选各带 `setup.sh:259-266` / `init.py:42,151,191` / `CLAUDE.md` 明文反例；
D4 两个候选各带「660 行成本实证」/「132 个文件」实测数）。
它甚至在开头写了「**本节与 memo 冲突时一律以 memo 为准**」——把双写的优先级问题显式处理掉了。

### 5.3 判定（**自评，非人核，N=1**）

**纪要承载得住「已经写进纪要的那些」，承载不住「纪要作者认为已属背景、只在 Context 里一笔带过的那条」。**
失效点不在 writer 的复述能力（照搬得很好），而在**纪要与 design.md 的分节映射**：
memo 把 D0/D0b/D0c 归成「范围性拍板」，writer 就照着把它们降级进 Context，
而 Context 是**叙述性**的、天然不带「候选 / 反例」结构 ⇒ 最承重的那条反例被结构性地挤掉了。
**而它恰恰是全场唯一一条「被证伪则整份设计报废」的约束。**

这与 `design.md` D2 自己写的反证同源，且比它更具体：不只是「writer 遇缺口只能猜」，
而是「**writer 会忠实地把纪要的分节结构复制成 design 的分节结构，于是纪要的归类错误被放大成论证缺失**」。

⚠️ **本项是 `tasks.md` 覆盖图明标的「人核」项。以上为材料准备 + 我的自评，N=1、单模型、单 change，
MUST NOT 当作已核。**

---

## 6. 阶段二验收门：逐条状态 + 我的判定与依据

门条件（`tasks.md`）= **5.1 GO ∧ 7.4 全过（安全前提）∧ 7.2 subagent 路总成本与质量均不劣于 thin 路**。

| 条件 | 实测 | 我的判定 |
|---|---|---|
| 5.1 GO | 派发链路可用，三个 `subagent_type` 全部解析成功、零降级（§4.3 实证） | **达标** |
| 7.4 S4 | `check_output_path` 纯函数 + 8 格 fixture（含 `<name>-evil` 前缀陷阱与 symlink 祖先逃逸），变异 M-D1/M-D2 红 | **机械达标** |
| 7.4 S3 / S5 | 只有「指令在场锚（删任一句即红）+ N=1 运行期观察」 | **满足验收门的合法形态**，理由见 §7 |
| 7.2 成本 | subagent **$11.68** vs thin **$9.06**；token 12.57M vs 8.81M（**幅度含不可信轮次、不作结论依据**，§3.2） | **未观察到更便宜** ⇒ 不满足「不劣于」 ❌ |
| 7.2 质量 | 冷审 Important 1 vs 0；返工 3 vs 2；论证密度 §5 有一条承重反例丢失 | **不优于**（三项均不占优） ❌ |

**⇒ 我的判定：阶段二验收门不达标，应按 tasks.md 的失败分支回退到阶段一薄编排形态。**

**依据（三条，按强度排序）** —— 🔴 **注意排序已因 §3.2 的订正而改变：质量轴现在是第 1 条。**

1. **质量三项无一占优**，且论证密度上有一条**可指名的承重反例丢失**（§5.1）。
   这一条**不依赖任何成本数字**，也不受 §3.2 污染影响。
2. **外派自身的开销是 lane 内部的自有账，不依赖与 thin 比较**：researcher(haiku 3.55M) +
   writer(sonnet 1.88M) 自己烧掉 **$3.66**，而 subagent 三轮**全部正常结束、无中止轮**（§3.2）
   ⇒ 这个数不受污染影响。要让外派划算，它必须把主 session 成本压低 **超过 $3.66**；
   本轮观测到的 opus 侧差额是 $1.04（**该差额受污染影响**）。
   附带产出：`design.md` NFR 的估算方法**只算了档位差、没算子代理自身 context**（§3.5）。
3. **成本轴：未观察到 subagent 更便宜**（$11.68 vs $9.06）。
   ⚠️ 两轮被中止（§3.2）**两个方向的偏差都不能排除** ⇒ 本条**只**支持「未观察到更便宜」，
   **MUST NOT** 读成「已证实 subagent 更贵」。**幅度不作结论依据。**

🔴 **成本轴即便退到「持平」，门结论不变。** 门是**合取式**——7.2 要求成本**与**质量**均**不劣于 thin。
质量轴（依据 1）**独立不达标**，∴ 下调成本轴的证据强度**不改变**回退判定。
反过来说：**本轮对 §3.2 的订正，修的是证据强度的表述，不是结论。**

**我不同意把「墙钟 −7.6%」当作放行理由**：它落在单次运行的自然抖动量级内，
且三路是**并行跑的**（API 侧无排队证据，但也没有排除），N=1 下这个差值不承重。

🔴 **放行是人的决定。** 上表是状态与依据，**不是**「已启动阶段三」或「已废弃阶段二」的宣告。

---

## 7. 7.4 是否算「全过」——判定与依据

票面点名要我判这个。`task4-agents-step2.md` §6 与 `fix1/fix2.md` 的真实状态是：

| 面 | 覆盖形态 | 是否有确定性信号 |
|---|---|---|
| **S4**（`resolvedOutputPath` 越界 / symlink 拒绝） | 纯函数 + 8 格 fixture（**连「被哪一道门拦下」一起断言**，防守着一道已不存在的门） | ✅ 有 |
| **S3**（网页指令性文本不被执行） | web 定义里三句处置的**在场锚**（删任一即红）+ 工具面只有 `WebFetch`/`WebSearch` 的旁证 | ❌ 无——「模型没照做」不可观测，沉默与合规同形 |
| **S5**（description 排他性生效） | 两句排他措辞的**在场锚** + N=1 运行期观察（无关任务下宿主选了 `Explore` 并自述「sdflow-* 仅限管线内派发」） | ❌ 无——取决于宿主的选择行为 |

**我判「满足验收门要求的合法形态」，三条依据**：

1. **S3/S5 属于 CLAUDE.md 基准 1 明确划出的「机械真够不着的残余」**——要机械验证 S3，得证明模型
   「没有执行注入指令」，而不作为不可观测；要机械验证 S5，得穷举宿主在任意项目任意任务下的选择。
   **诚实边界 = 合法的残余划分，不是弱点、不是妥协。**
2. **该给的机械面都给足了**：三个定义的工具面、frontmatter 档位、排他句在场、
   `tools` 无作用域括号、web 无 `Bash`/无仓库读取、secret-scan 的 exit 0/2/3 语义与 catch-all，
   共 28 个用例 + 14 条变异全红（`task4-agents-step2.md` §3、`fix1/fix2.md`）。
3. **门本身若要求 S3/S5 有机械证据，它就是一个永远无法达标的门**——那不是严格，是设计错误。

⚠️ **但这条判定只在「本门的语义 = 该做的机械化都做了 + 残余如实声明」时成立。**
若人的口径是「S3/S5 必须有机械证据才算过」，那 7.4 **不达标**，结论仍是回退（与 7.2 同向），
**门的最终结论不因这条的解读而改变**。

---

## 8. 7.1 机械层全量重跑

```
$ git add -A && /usr/bin/python3 -m pytest -q
2774 passed, 10 skipped, 3 xfailed in 277.59s (0:04:37)
PYTEST_RC=0

$ /usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice_job.py -q
332 passed in 98.27s          # 已知抖动用例本轮通过（单独复跑一次确认）

$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 22 个投放面全部与真相源一致

$ wc -l sdflow-spec/SKILL.md
599                            # D12 上限 600，余量 1 行
```

沙箱隔离核验（三个 clone `rm -rf` 之后）：

```
$ git status --porcelain
A  openspec/changes/add-sdflow-spec/impl-reports/task5-ab-comparison.md
M  sdflow-spec/SKILL.md

$ git worktree list
/Users/cheneyzhao/Documents/04-sdflow-skills  3b7c8d0 [feat/add-sdflow-spec]
```

⇒ 主工作树只含本票的两个文件；**无 worktree 残留、无沙箱产物带回**。

> 🔄 **fix 轮次 1 的口径变更（本节以上为原轮次的实跑记录，保留原样）**：
> 复审要求「原始数据可第三方复核」⇒ 本轮**主动把原始 JSON / prompt / 驱动脚本带回主仓**
> （`impl-reports/task5-logs/`，73 个文件 / 288 KB）。∴ 上面「无沙箱产物带回」这句
> **对 fix 轮次 1 之后的工作树不再成立**——现在带回的是**日志与脚本**（不含任何 clone 的
> 工作副本 / `.git`）。**三个 clone 仍是已删除状态，未恢复、也无法恢复。**
> 本轮的机械层重跑结果见 `task5-ab-comparison-fix1.md`。

---

## 9. 回退动作（已执行）与 hand-off 记录

**执行的回退**（最小、可逆、单点）：`sdflow-spec/SKILL.md`「外派协议」节的启用前提，
从「启用前提 = SA-07 的 GO/NO-GO 实测门判 GO」改为**明写本节 = 未启用资产**，
带上 A/B 数字、N=1 边界、报告指针，并加一句「**仅在人明确指示启用外派时生效，MUST NOT 自行启用**」；
相位 C.3 的「阶段二」段加一条交叉指针（防只读 C.3 的人看不到该结论）。

**为什么只改这一处**：原文把「启用前提」写成只由 5.1 的 GO 决定，而 spec SA-02 的原文是
「外派的启用以阶段二起手的派发实测门（SA-07）**与 A/B 对照结果**为前提」——∴ 这次修改是**把 SKILL.md
纠正回 spec 的字面**，不是新增约束。

**agent 定义的去留 = 保留为未启用资产**（tasks.md 明列的两个合法选项之一）：

| 资产 | 处置 | 理由 |
|---|---|---|
| `sdflow-spec/agents/*.md`（三个） | **保留** | 删除会连带撤掉 `sync_principles` 的 `AGENT_TARGETS` 投放面、`install_agents()` 及其 4+5 个用例；而 A/B 是 **N=1**，删掉即销毁复跑的基础设施 |
| `setup.sh install_agents()` + 守卫 | **保留** | 同上；且它已被 `test_install_agents.py`（全仓首个 setup.sh 测试）锁住，删除是净损失 |
| `~/.claude/agents/` 的三条软链 | **保留** | 定义在册不等于被派发——`sdflow-spec` 已明写不自行启用；S5 的 N=1 观察显示宿主在无关任务上不会误选 |

**hand-off 应记录的三条**（本报告即其证据源）：

1. 阶段二**外派未启用**，`sdflow-spec` 的正式交付形态 = **阶段一薄编排**（design D2 已声明其为合法交付形态）。
2. 复跑条件：若要重开阶段二，**MUST** 先修正 NFR 的估算方法（§3.5：漏算子代理自身 context），
   并把样本量提到 N>1；本轮的驱动脚本与 prompt 全部可复现（口径见 §2）。
3. 本轮**没有**做 tasks 8.x（阶段三）的任何动作，**没有**删除任何阶段二资产。

---

## 10. 诚实边界（结构性无法验证的项，逐条）

1. **「人」不在场。** 三路的需求方由本 Task 5 的实验驱动 agent 扮演（票面授权）。
   ⇒ **「判断质量」这一维本轮结构上无法验证**，与 `tasks.md` 覆盖图把 7.3 标为「人核」一致。
   拍板文本三路一致，但「一个真人会问什么、会在哪里叫停」无法模拟。
2. **7.3 的论证密度比对是自评，不是人核。** §5 提供的是**材料 + 一个可复核的具体例子**，
   MUST NOT 当作已核项。
3. **findings 口径已降级。** §3.4 的冷审是**单进程五镜**，不是 `/sdflow-spec-review`
   （无 autoplan、无多镜 fan-out、无 outside-voice、模型档位也更低）。
   两者的 findings 数**不可互相换算**。
4. **N=1，非统计显著。** 一个 change、一次跑、一台机器、一个模型机队、一天之内。
   §3 的所有百分比都是**单次观测差**，MUST NOT 表述为「已证实 subagent 更贵」。
   能说的只有：**在这一次观测里，未观察到 subagent 更便宜。**
5. **两轮被中止，机制已核、归因已订正（§3.2）。** 非 SIGKILL、非驱动脚本限时（脚本限时是
   `timeout 3000` = 50 分钟，未触发），而是 `claude` CLI 自行 `aborted_streaming`；**触发源未确证**。
   计费**未发现丢失**（12/12 轮价格-用量闭合），但「用量少报」一支**不可排除且无界**。
   ⇒ **成本幅度不作结论依据**；这两轮的 `duration_ms` 逐位相同（598753），**不可当实测墙钟**。
6. **三路并行跑**（同时发请求）。墙钟因此可能被 API 侧并发影响；三路条件相同，
   但**绝对值不可外推**，且 §6 已声明不把墙钟差当放行依据。
7. **token / 美元来自 harness 自报**（`claude -p --output-format json` 的 `usage` / `modelUsage` /
   `total_cost_usd`），非账单核对。子代理的用量出现在父进程的 `modelUsage` 里（haiku / sonnet 两行），
   这是**观测到的**、不是推算的；但它是否与最终账单逐分对齐，本轮未核。
8. **`--model opus` 是我替「人」选的档位**。真实使用中主 session 档位由人选；
   若人用 sonnet 跑阶段一，外派的档位差收益会进一步缩小（mid 也是 sonnet），
   ⇒ 本轮的档位选择对 subagent 路是**有利**的那一端。
9. **单个实验对象。** T163 是「机械抽取」型需求，检索量中等、判断量中等。
   对「检索量极大」的 change，researcher 的 context 隔离收益可能反转结论 —— 本轮测不到。
10. **原始 JSON 已归档可复核；三个 clone 已删除，文件级举证不可复跑。**
    §3 的五项指标**全部可从 `impl-reports/task5-logs/` 重算**（本轮已重算，逐位吻合）。
    但 §5 引用的 `design.md` 行、§3.4 的 `grep` / `diff` 输出跑在三个沙箱 clone 上，
    clone 已 `rm -rf` ⇒ 那些**文件级**证据只存**本报告誊抄** + 各轮 result 文本
    （`task5-logs/logs/*.out`）+ 三份冷审全文（`task5-logs/logs/*/review.json`）。
    - **problem**：`design.md` / `specs/` 原文不可再 grep，∴ §5.1「承重反例整条消失」这条
      **无法由第三方对源文件复验**，只能读冷审与 result 文本的转述。
    - **cause**：沙箱按纪律不带回主仓（§8 的隔离核验即为此），当时只誊了结论、未留文件快照。
    - **fix**：若人要求文件级复核 ⇒ 需按 §2 的口径**重跑三路**（prompt 与驱动脚本均已归档，可复现）。
      代价 = 约 **$35.6**（本轮三路合计实价）+ 约 1 小时墙钟，且仍是 N=1。
      **建议**：仅在「§5.1 是否成立」成为拍板分歧点时才值得重跑；门结论不依赖它（§6 依据 1 含返工量与冷审两项独立证据）。
11. **回退动作的完整性**：我只改了 `sdflow-spec/SKILL.md` 两处。
    `proposal.md` / `design.md` / `specs/` / `tasks.md` 一字未动（票面禁止），
    因此**四件套里仍有把阶段二写成「将启用」的表述** —— 这属于设计阶段产物，
    应在 archive 阶段随 delta 同步校正，本票不越权改。
