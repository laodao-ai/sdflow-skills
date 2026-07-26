# 降级阶梯 · 诊断契约 · 失败模式表

> 被 `sdflow-spec/SKILL.md` 引用。**撞到任何失败先查本表，别现场发明处置。**

## 1. 诊断契约（三要素，每一条降级/失败报告都要写满）

**problem + cause + fix**，缺一即不合格。

| 要素 | 内容 | 反例（MUST NOT） |
|---|---|---|
| **problem** | 发生了什么、哪一步 | 「出了点问题」 |
| **cause** | 判定依据：exit code / 缺失文件绝对路径 / **实际版本号** / stderr 原文 | 「可能是环境问题」 |
| **fix** | 可直接照做的下一步命令 | 「建议检查一下安装」 |

> ❌ 「spec-writer 失败，已亲写」 —— 零信息量。安装问题会长期隐藏在「能跑但更贵更慢」的降级模式里。
> ✅ 「相位 C 生成 design.md 失败（problem）；`subagent_type: sdflow-spec-writer` 派发返回
> `agent type not found`，`~/.claude/agents/` 下无 `sdflow-spec-writer.md`（cause）；
> 修：在运行 checkout `~/.skills/sdflow-skills` 跑 `bash setup.sh`（fix）。本次已由主 session 亲写。」

## 2. 降级阶梯

| 层 | 触发 | 降级到 | 允许静默？ |
|---|---|---|---|
| 检索 | researcher 不可用 / 超时 / 失败 | **主 session 亲查** | ❌ 报告必写 |
| 生成 | spec-writer 失败 | 按失败类型：瞬时错误重试一次 → **主 session 亲写**；schema/契约错误**不重试**直接亲写 | ❌ 报告必写 |
| agent 定义缺失 | 未跑 setup / Windows / Codex 宿主 | **主 session 亲查/亲写** | ❌ 报告必写 |
| openspec CLI | 不存在 / 非零退出 / `instructions --json` schema 断言不过 | **fail-closed 中止**（唯一 fail-closed 面） | ❌ 必须中止并报 |

🔴 **MUST NOT 用通用子代理当 fallback。** 通用 Agent 路径**无法限制工具集** ⇒ 该 fallback
撤掉了唯一的工具权限边界 = **降级即提权**，且 agent 正文承载的角色纪律（researcher 的
「材料不回传」、writer 的「禁 AskUserQuestion」）在该路径下全部消失。降级方向只有一个：**亲做**。

🔴 **降级前 MUST 确认替代路径不复用同一故障依赖。** 「联网检索超时 → 主 session 亲查」若亲查
同样要联网，那不是降级，是同一个故障再撞一次 —— 此时 SHALL 如实说明该限制，而非宣告已降级成功。

## 3. 外部检索的退避与错误分类

- **总时间预算**：单次外部检索 ≤ 3 分钟；相位内累计 ≤ 10 分钟，超出即停并如实报。
- **429 / 5xx**（瞬时）：**一次**带 jitter 的有界重试（退避 2–5s 随机）。
- **401/403 认证错误、schema 不兼容**：**立即 fail-closed**，MUST NOT 重试（重试只会再失败一次，且掩盖真因）。
- **重试次数为什么是 1**：无强依据，按通则④判为可接受边角。判据不是「几次」，而是
  **「瞬时错误重试一次；契约错误不重试」**。MUST NOT 为此单独返工。

## 4. 失败模式表

| 失败模式 | 检测 | 处置 | 回滚 |
|---|---|---|---|
| **工作树不洁进入相位 B** | B 起手 `git status --porcelain` | **halt 报告给人**（stash / 先提交 / 确认带过来三选一）；MUST NOT 静默 `add -A` | 未提交，无需回滚 |
| **人在相位 B 中途放弃** | 无（人主动） | memo 草稿留在 feature 分支内；**删分支即净**——⚠️ 仅当 B 起手时工作树曾干净，否则用户的无关改动已被 `checkout -b` + `add -A` 裹挟进来 | 删分支 |
| **在其它 feature 分支上开新 change** | FF-0 三分支判定 | 「其它」→ **halt 问人**（从当前切出 / 回 base 切出 / 就地继续） | 未建目录 |
| **`git checkout -b` 失败（分支已存在）** | 命令 exit code | fallback `git checkout feat/{change}`（存在则复用）；再失败即如实报告让人决定 | — |
| **陈旧 `decision-memo.md`** | 相位 C 起手核身份字段（change/branch）对不上当前盘面 | **拒绝进 C**，呈现旧 memo 摘要给人确认；MUST NOT 静默复用 | — |
| **writer 写半截/垃圾** | `status --json`（存在态）+ `validate --strict`（合格态）**分开判** | validate 不过即判该产物**未完成**，进重试/亲写阶梯（**非**「文件存在即跳过」）；写入用临时文件 + 原子替换 | 按 preimage 精确回滚该文件 |
| **CLI schema 漂移（版本对、行为变）** | `instructions --json` 后做最小 schema 断言 | **fail-closed 中止**，报实际版本 + 修复命令 | 未写产物 |
| **agent 定义解析失败** | 派发报错 | 主 session **亲查/亲写**；报告标注 | 无状态 |
| **openspec CLI 不可用/报错** | 命令 exit code | **fail-closed 中止**（含版本与修复命令） | `new change` 前后各记一次 change 目录快照；非零退出后核 `.openspec.yaml`/`status`，**精确报告 partial state，MUST NOT 假定其原子性** |
| **生成中断（部分产物完成）** | `status` + `validate` 对账 | 如实报告完成/未完成清单；按相位状态机重入 | 分支内 git 状态即真相 |
| **纪要缺失/必填为空进入相位 C** | C 起手核验 | 拒绝生成，退回相位 B | — |

## 5. `validate --strict` 的真实覆盖面（诚实边界，实测锚定）

`openspec validate <change> --strict`（CLI 1.5.0）**只校验 `specs/*/spec.md` 的 delta 结构**
——至少一条 delta、`## ADDED/MODIFIED/REMOVED/RENAMED Requirements` 头、每条 Requirement
含 SHALL/MUST 与 ≥1 个 `#### Scenario:`。

实证：`dist/core/validation/validator.js` 全文无 `design` 字样；change 路径实际只跑
`validateChangeDeltaSpecs`——**把 `proposal.md` 整份删掉，它照样报 `Change 'demo' is valid`**。
`hack/tests/test_decision_memo_gate.py::test_validate_strict_only_covers_delta_specs` 机械钉住此事实。

⇒ **`design.md` / `proposal.md` / `tasks.md` 被截断时，`status` 报 done、`validate --strict` 也报绿。**
四件套里只有 `specs/` 有机械合格门。另外三份的「未截断」**没有机械门**，只能由主 session 在
**终审**读回时人判：文末是否收束（最后一节写完、无半句话）、`## ` 小节是否齐全、有无「TODO/待补」残留。

MUST NOT 在任何文档中声称「`validate --strict` 挡得住半截 design.md」。
