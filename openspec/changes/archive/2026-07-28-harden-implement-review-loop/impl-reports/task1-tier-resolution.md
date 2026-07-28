# Task 1：四个编排 skill 的宿主/档位解析第零步 + 机械 parity 守卫

状态：`DONE`

## 范围核对（tasks.md §1 全 12 项 + §7.2 + §7.7）

| 项 | 内容 | 落点 |
|---|---|---|
| 1.1 | `sdflow-implement/SKILL.md` 新增「第零步：宿主/档位解析」，四步语义对齐姊妹 skill，跨文件引用一律具名锚点（「见预检步」类，本步已消除「本步第 N 项」这类位置派生序号） | `sdflow-implement/SKILL.md` 新增 `## 第零步：宿主/档位解析（两入口共用、无条件执行）` |
| 1.2 | 第零步置于文件最前（principles 块之后、模式派发契约之前）、两入口共用、无条件执行；出票模式的 `T10-choice` 仲裁步消费 strong 档不在本步内，只在此声明依赖关系 | 同上，intro 段第一句 |
| 1.3 | `host=unknown` 与子代理不可用两态均 fail-loud 硬停，不缩 roster | 同上「能力探针 + 不可用则硬停」段 |
| 1.4 | 八类失败 problem+cause+fix 表，沿用五要素 halt envelope（ticket 号字段固定「—（起手失败，无票上下文）」） | 同上「八类失败分支」表格 |
| 1.5 | implementer dispatch 段新增档位声明，引用 `$SDFLOW_TIER_MID` | 「每 ticket 派 fresh implementer」节新增一句 |
| 1.6 | Standards 轴 / Spec 轴 dispatch 段同样新增档位声明 | 「每 ticket 双轴审」节首句括注 |
| 1.7 | fix 子代理无独立 dispatch 段——就地在「裁决处置」bullet 内声明同 mid 档，避免与 1.5/1.6 重复计数 | 「裁决处置」bullet |
| 1.8 | `sdflow-done/SKILL.md` `### 0.4` 由裸 `eval` 一行升级为同一套四步语义 | 同上 |
| 1.9 | 新增 `hack/check_tier_resolution_parity.py` + `hack/tests/test_tier_resolution_parity.py`，对四个 SKILL.md 的核心段逐字节比对（marker：`<!-- sdflow:tier-resolution:start v1 -->` / `<!-- sdflow:tier-resolution:end -->`） | 见下「机械守卫」节 |
| 1.10 | 变异实测：4 文件 × 4 子步 = 16 次删除，全部必红；两种恒真成因均排除 | 见下「变异实测」节 |
| 1.11 | `AGENTS.md`/`CLAUDE.md`/`sdflow-init/assets/snippets/claude-section.md` 补 `sdflow-implement` 进授权范围，「仅限这两处」→「仅限这三处」；`sdflow-init/tests/test_codex_subagent_authorization.py` 同步改断言 | 三份文档 + 一份测试 |
| 1.12 | `sdflow-ship/SKILL.md` 枚举补 `implement` | 同上 |
| 7.2 | `grep -n "SDFLOW_TIER" sdflow-implement/SKILL.md` 不再零命中 | 见下 |
| 7.7 | Success Metric 1 证据：Codex 宿主下实跑档位解析 | 见下「Success Metric 1」节 |

## 归一化核心段的设计取舍

design 明写「对齐目标为四步语义，MUST NOT 要求与任一姊妹 skill 逐字相同」，但 parity 守卫（1.9）
要求「逐字节比对核心段」——两者的解法是把**核心段收窄**到真正站点无关的机制文本（清脏 unset →
预检 → 捕获退出码 eval → eval 后校验），marker 只圈住这一段；引出该段的标题/编号（"3."/"4."/
"### 0.4"/`## 第零步`）与其后的 skill 专属处理（host=unknown 是硬停还是缩 roster、8 类失败表、
能力探针细节）都留在 marker 之外，允许因 skill 而异。

改动中发现并清理的非必要漂移面：
- `sdflow-code-review`/`sdflow-spec-review` 原文里 `(d)` 步含「同本步第 3/5 项」「同本步第 2/4 项」
  这类**依文件本地编号派生**的交叉引用——两份原文因编号不同已经不是逐字一致（4 步语义相同但序号
  不同）。这些引用现移出核心段，改写成具名锚点（「规则根解析」「skew 探测」），核心段本身不再含
  任何位置相关的序号。
- 「本轮评审」→「本轮工作」、「供下方「模型选择」节引用」→「供本轮后续所有派子代理动作引用」：
  两处措辞原本假设了 code-review/spec-review 特有的结构（"评审"一词、"模型选择"小节），
  `sdflow-implement`/`sdflow-done` 没有对应结构，改成中性措辞后四份可以真正逐字相同。

## 机械守卫

`hack/check_tier_resolution_parity.py` 仿 `hack/check_async_branch_parity.py`：只认两个 marker
token、单行字面量匹配（有界语法面，基准 5），MUST NOT 演化成解析 Markdown 结构。已接入
`setup.sh`（独立守卫，不挂在 `sync_principles.py` 条件下——理由与既有 async-branch 守卫一致：
自己的脚本存在即跑，不因另一工具缺失而静默不跑）。

`hack/tests/test_tier_resolution_parity.py` 36 个用例，覆盖：真仓四处逐字节一致、marker 存在性、
空段防护、漂移检测（含三向比较：前两侧一致不能掩盖第三侧漂移）、marker 畸形各类报错、
`FORBIDDEN_IN_SEGMENT`（圈内不许出现四个 skill 名字自身）、CLI 契约、以及段内内容 golden
（六变量清脏、fail-loud 硬停措辞、host 空值/unknown 分家判据、eval 只跑一次）。

```
$ /usr/bin/python3 -m pytest hack/tests/test_tier_resolution_parity.py -q
36 passed in 0.10s
```

全仓回归（含本票改动）：

```
$ /usr/bin/python3 -m pytest -q
2893 passed, 11 skipped, 3 xfailed in 283.64s
```

（跳过/xfail 项与本票无关，为既有已知项。）

## 变异实测（1.10）

对四个 SKILL.md 各自的核心段逐一删除 (a)/(b)/(c)/(d) 四个子步（共 4 文件 × 4 子步 = 16 次），
每次删除后立即跑 `hack/check_tier_resolution_parity.py`，记录退出码，再恢复原文件：

```
site                             step  exit
sdflow-implement/SKILL.md        a     1     RED
sdflow-implement/SKILL.md        b     1     RED
sdflow-implement/SKILL.md        c     1     RED
sdflow-implement/SKILL.md        d     1     RED
sdflow-done/SKILL.md             a     1     RED
sdflow-done/SKILL.md             b     1     RED
sdflow-done/SKILL.md             c     1     RED
sdflow-done/SKILL.md             d     1     RED
sdflow-code-review/SKILL.md      a     1     RED
sdflow-code-review/SKILL.md      b     1     RED
sdflow-code-review/SKILL.md      c     1     RED
sdflow-code-review/SKILL.md      d     1     RED
sdflow-spec-review/SKILL.md      a     1     RED
sdflow-spec-review/SKILL.md      b     1     RED
sdflow-spec-review/SKILL.md      c     1     RED
sdflow-spec-review/SKILL.md      d     1     RED

ALL MUTATIONS CAUSED RED: True
```

16/16 全红。删除动作直接对仓内真实文件做字符串替换（非 fixture 拷贝），跑的是与
`test_repo_sites_are_byte_identical`（间接经 `P.main([])`）完全相同的代码路径，跑完立即用
`try/finally` 恢复原文，`git status --short` 复核确认无残留改动。

**两种恒真成因排除**：
- 「门被别的断言满足」——抽样对 `sdflow-spec-review` 删除 (a) 步后直接看 `check_tier_resolution_parity.py`
  的 stderr 输出，`_print_first_diff` 打出了具体的「首个不同在段内第 2 行」+ A/B 两侧原文，证明是
  这次删除本身造成的字节差异触发红，不是别的检查项恰好同时失败。
- 「压根没用例走到那行」——本次直接调用 `main([])`（无参数，走仓内真实四文件），与 pytest 里
  `test_repo_sites_are_byte_identical` 调的是同一行代码 `P.main([])`；不存在「测试从未执行到删除的
  那一支」的可能。

## 附：Codex 子代理授权 + sdflow-ship 枚举（1.11/1.12）

`AGENTS.md`、`CLAUDE.md`（均为 `opsx-init` 托管块内容）与其单一源
`sdflow-init/assets/snippets/claude-section.md` 三处同步改动，`diff` 核对逐字一致；
`sdflow-init/tests/test_codex_subagent_authorization.py` 的 `test_snippet_declares_codex_subagent_authorization`
断言同步改为 `"sdflow-implement" in t` + `"仅限这三处" in t`。`sdflow-ship/SKILL.md` 枚举串
`spec-review/code-review/done` → `spec-review/code-review/done/implement`。

```
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_codex_subagent_authorization.py -q
52 passed in 0.09s   # （与 hack/tests/test_async_branch_parity.py 合并跑）
```

## Success Metric 1 证据（7.7，[e2e]）

**取哪种**：按 brief 二选一，选择「只走到档位解析步即止」——不跑完整 `sdflow-implement
tickets-plan`（会写 `superpowers-plan.md`/`tickets.md`，触发本 change 自身的 `plan_first_sha`
窗口锚风险），只在真实 Codex 宿主进程内执行 Step 0 的实际机制（`eval
"$(~/.sdflow/hack/resolve-models.sh)"`），核验解析结果。

**环境说明（诚实边界）**：本机 `codex` CLI（`codex-cli 0.145.0`）已装且已认证鉴权，可用
`codex exec` 非交互调用。首次直接调用时，因本 agent 运行在 Claude Code 会话内（其 shell 环境
自带 `CLAUDECODE=1`），该变量被 `codex exec` 派生的子 shell 继承，与 Codex CLI 自身设置的
`CODEX_THREAD_ID` 同时出现，触发 `resolve-models.sh` 的**宿主信号冲突检测**（`HOST=unknown`，
回落 Claude 机队缺省 opus/sonnet/haiku）——这本身是该脚本设计正确工作的证据，但不是我们要的
「纯 Codex 宿主」读数。用 `env -u CLAUDECODE codex exec …` 去掉这个从父进程继承来的干扰变量后
（这不是伪造 Codex 身份——`CODEX_THREAD_ID` 仍由 Codex CLI 自己的运行时设置，只是消掉了因
`codex exec` 被 Claude Code 的 Bash 工具启动而额外带入的 `CLAUDECODE` 泄漏），拿到干净读数：

```
$ timeout 90 env -u CLAUDECODE codex exec 'Run exactly this shell command and print its
  full stdout verbatim, nothing else: eval "$(~/.sdflow/hack/resolve-models.sh --root
  "$(pwd)")"; echo "HOST=$SDFLOW_HOST"; echo "STRONG=$SDFLOW_TIER_STRONG"; echo
  "MID=$SDFLOW_TIER_MID"; echo "LIGHT=$SDFLOW_TIER_LIGHT"; echo
  "CLAUDECODE_set=${CLAUDECODE:+yes}"; echo "CODEX_THREAD_ID_set=${CODEX_THREAD_ID:+yes}"'

HOST=codex
STRONG=gpt-5.6-sol
MID=gpt-5.6-terra
LIGHT=gpt-5.6-luna
CLAUDECODE_set=
CODEX_THREAD_ID_set=yes
```

（session id `019fa6ed-d5f5-71b2-bb93-2558bd02b14f`；先前一次带冲突的读数 session id
`019fa6ed-4d06-7c60-9bcd-a72665916c94` 一并留痕，作为「冲突检测确实生效」的对照。）

**结论**：本 change 的四类 dispatch（implementer / Standards 轴 / Spec 轴 / fix）均引用同一次
Step 0 eval 出的 `$SDFLOW_TIER_MID`（设计上「本轮全程只 eval 这一次」）。在真实 Codex 宿主进程
内，该值解析为 `gpt-5.6-terra`——**∈ Codex 机队缺省集**（`{gpt-5.6-sol, gpt-5.6-terra,
gpt-5.6-luna}`，见 `model-tiers.md` 机读块），**零命中 Claude 机队专名**（`{opus, sonnet,
haiku}`）。`$SDFLOW_TIER_STRONG`/`$SDFLOW_TIER_LIGHT` 同样落在 Codex 机队集合内，未验证到
Claude 专名污染。

未做的部分：未实跑完整 `sdflow-implement tickets-plan`（含 implementer 子代理实际 fan-out）——
brief 明确这两个选项二选一，且完整跑会写这个 change 自身的 plan 文件，与 Global Constraints
的重命名/覆盖红线冲突。若后续需要「四类 dispatch 真的各自派出一次 Codex 子代理」级别的证据，
需要另开一次性 fixture change，留给编排层裁决是否需要、是否记 todo。

## 未做/裁剪的部分

无。tasks.md §1 全部 12 项 + §7.2 + §7.7 均已完成并有对应证据；D2b（review-loop-breaker 两项
机制修正）属 Task 3 范畴，本票未触碰，符合 brief 范围。
