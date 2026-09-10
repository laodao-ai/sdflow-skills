# 执行协议细节

按需路由自 `SKILL.md` 对应步骤；仅在实际执行到该步骤、需要展开判据表或背景细节时读取本文件。

## 0.2 档位解析：为什么四步一步不能少

裸 `eval "$(…)"` 会被脚本缺失静默吞（`eval ""` 返回 0），且同 shell 上一轮的 `SDFLOW_*` 旧值
原样留存 ⇒ 拿旧宿主假绿。步骤 (c)「捕获退出码再 eval」尤其关键
〔impl-review-fix FIX-3 · 面治：resolver 输出可以先设好合法 host/tiers、再跟一条非法命令
⇒ eval 退 127 而 (d) 全 PASS；本 SKILL 的 (c) 与四个编排 SKILL 同缺陷同修〕——`eval` 自身
的退出码也 MUST 立即检查，`EVAL_RC` 非 0 时 MUST NOT 带着半成品环境继续做 (d)。

## FF-0 三分支判定：全局 hook 的匹配 grammar

全局 FF-0 hook 只在整条 Bash 命令完整匹配**单条直接 literal**创建调用时，才用 payload
`cwd` 执行三分支判定。正向有限 grammar 只包含 `openspec new change <合法字面量>` 与
`openspec change new <合法字面量>`，容忍水平空白、单/双引号与单个 `--json` 变体。未命中该
grammar 的 wrapper、目录切换、compound、换行、前后散文、无效 literal/option 或动态名
一律记录 `command-unverifiable`，不尝试细分原因或解释 shell。此未判定路径只输出
`additionalContext`，**MUST NOT 解析 shell**，也不设置 `permissionDecision`；多处创建调用的
stacking deny 先于 cwd 未判定。

## C.2 生成阶段强制阅读清单（schema 依赖图优先，缺口回退超集）

| 生成 | MUST 先全文读 |
|---|---|
| `proposal.md` | `decision-memo.md` |
| `design.md` | `decision-memo.md` + `proposal.md` |
| `specs/**` | `decision-memo.md` + `proposal.md` + **`design.md`** |
| `tasks.md` | `decision-memo.md` + `proposal.md` + `design.md` + `specs/**` |

每步读 `dependencies` 对象列表（含 `id`/`done`/`path`/`description`）并比较上表。
图已覆盖按图读；图不足则回退**写死超集**：`specs` 读 `proposal.md`+`design.md`，`tasks` 读
`proposal.md`+`design.md`+`specs/**`，不得跳过；纪要输入。

## 0.3 重入探测：isComplete 三态判定表

| `isComplete` | 纪要 | 态 | 动作 |
|---|---|---|---|
| `false` | **无** | `B-draft`（草稿都没落成） | 继续 ⇒ **回相位 B**：A 的共识随上下文丢了，先重述锚点纪要再拷问 |
| `false` | **有** | `B-draft`/`B-finalized`/`C-partial` | 问话附分支名 + 纪要已有 N 条承重约束；继续 ⇒ 跳过 A，核验纪要（C.1）后进入 C |
| `true` | 任意 | `complete` | **拒绝重生成**，呈现该 change 与出口序列；要改走评审或新 change |

🔴 **MUST NOT 拿「有没有 `decision-memo.md`」当探测前提**——B 起手建完目录到第一次落盘之间崩溃，
留下的正是第一行那种**没有纪要**的在途 change；**MUST NOT 只探 `isComplete=false`**，那让
`complete` 只剩一句声明、没有对应的操作判定。

## C.4 已知限制：CLI 1.5.0 `validate --strict` 覆盖边界

CLI 1.5.0 的 `validate --strict` 只校验 `specs/*/spec.md` delta；其余三份（proposal / design /
tasks）截断仍可能双绿，只能靠终审读回判定，MUST NOT 声称它能挡住半截 design.md。
