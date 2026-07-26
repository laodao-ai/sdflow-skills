# Task 3 双轴审存档 — 中断恢复与 identity-safe 清理

**票**：Task 3（R-ID: OVBG-03, OVBG-05）
**轮次**：轮 1（`ec0d690`）**双 FAIL** → fix1（`1a75fa5`）→ 轮 2 双 PASS

## 领域清单覆盖声明（Standards 轴，两轮均原样重述）

本 change 的 `proposal.md` 明确声明「不命中 backend、frontend、embedded 技术栈领域清单」，而
`code-checklists/domains/` 下只有 `backend*.md` / `embedded*.md` —— 故**领域清单未覆盖**，
Standards 轴以 `code-review-base.md` + 仓内 `CLAUDE.md` 基准 + Fowler code smell 为标准源。
**这是诚实降级，不是「全覆盖通过」。**

## 轮 1 发现 —— 两条 Critical 是**同一类错误的两种形态**

两轴各自独立抓到一条，且都是**实测复现**而非读码推断；两条同源：
**`cleanup` 的子树核验在两条不同路径上都能给出假的「已清理」**，后果一致 ——
一次**仍在计费**的 voice 被判死后再叠一次 fallback，正是 OVBG-05 与 `design.md:224` 要杀的。

### Critical 1（Standards）· `probe_subtree` 组长分支假阳——premise 被本仓自己的 helper 契约证伪

`probe_subtree` 的 docstring 断言「worker → bash helper → claude 都是同步 fork，**不换组** ⇒
`killpg(pgid,0)` 是子树是否有活口的直接答案」。**这个前提是假的**：
`outside-voice.sh:428-431 / 474-481` 白纸黑字写着「GNU timeout 会 `setpgid` 把自己放进**独立进程组**，
PGID 恒等于 timeout 自己的 PID」——**真正烧额度的 runner 整棵在别的组里**。

实测（本机 gtimeout）：worker 组 19517 建组 → 子 `gtimeout` 落到组 **19518**；worker 死后
`killpg(19517,0)` → `ProcessLookupError` ⇒ 判 `EXITED`，而 `19518 gtimeout / 19519 sleep` **仍存活**。

> **这是一个被本仓自己的代码注释证伪的前提，被当成推理地基写进了 docstring。**
> 只有真起一个换组子进程才能照出来——读代码读不出来。

### Critical 2（Spec）· roster ABSENT 时 cleanup 无条件返回成功

而 **LOST 最主要的产生路径恰恰就是 `probe_liveness` 返回 `missing`**（roster 无此条目）。
亲跑复现（liveness=missing / roster=[]、worker pid 真活着）：
`{"state":"LOST","ok":true,"action":"absent","unknown_cost":false,"orphan_warning":null}` ——
**一个仍在跑、已计费的 worker 被 reconcile 报成干净通过。**
反向后果同源：子树确已退出时 `fallback_allowed` 也恒 False ⇒ orphan warning 承诺的
「跑 cleanup 解闸」对该路径**永不解闸**。

**测试盲区**：全部 LOST 用例的 roster 都仍列着该 job，**`missing` 通道从未穿过 cleanup**——
283 条测试对这条主路径完全失明。

### Important（两轴同报）· `run_reconcile` 站点集为空时静默报绿

`reconcile --run-dir <空目录> --site design-voice` → `{"ok": true, "sites": []}`、exit 0
（`all([])` 为真且无 warning）。操作者敲错 site 名 / 点错 run-dir，拿到「一切正常」——
**而这正是成本未知的场景**。853 行新增测试无一覆盖「零站点」。

## 轮 2 复审（双 PASS）

**Spec 轴**：5 条验收标准全 ✅（轮 1 判 ⚠️ 的第 3 条、判 ❌ 的第 4 条均升级）。亲跑复现四种形态：
A 真活 worker + 空 roster ⇒ `orphan-warning / unknown_cost=True / ok=False`；B 无信号 ⇒ `unverifiable` + 抑制；
C `runner.pid` 指死 pid ⇒ `exited` + `fallback_allowed=True`（**「永不解闸」一并修好**）；
D 活 runner + terminal witness ⇒ 仍 `alive`（④ 压过 ⑤）。三条反向变异一起打回 ⇒ **7 failed**。

**Standards 轴**：Critical 1 变异 ⇒ 3 failed；**换组锚是真的**——`test_..._when_a_child_escaped`
起真 `gtimeout`，变异跑时五条前置断言（`getpgid(runner) != leader` / 组已空 / runner 仍活）
**全部通过**、只在 verdict 处红，∴ 换组是运行期机械核实的事实，不是 mock 返回值。
Critical 2 变异 ⇒ 3 failed（含 CLI 级用例）；Important 变异 ⇒ 2 failed。

### 面治独立复扫（Standards 轴自己列出口，不采信 fix 自查）

全文件 `fallback_allowed=True` 仅 6 处：dispatch 侧 3 处均在「nonce 未检出外部 job ⇒ 未计费」之后
（检出即 `unknown-cost` + False）✅；cleanup 侧 3 处 —— 两处门在 `probe_subtree==EXITED` /
`wait_subtree_exited==EXITED` ✅，一处无子树门但前提是 rc 已发布且已 collect（额度已落袋，裁定保留）。
`ok=True` 侧亦逐个核过。**未发现新的未证放行路径。**

## Spec 轴对新引入状态值的独立判定：**正解，非加宽非缩水**

- `unverifiable` **不是新造范畴** —— OVBG-05 原文就写着「清理失败**或子树终止不可证** MUST 作为
  orphan warning 可见，并抑制会叠加费用的自动 fallback」；OVBG-03 写着「无法证明子树已退出时
  SHALL 标记 unknown-cost/orphan-warning」。实现是把 spec 的词直接落成 verdict。
- ABSENT 分流 1:1 对应 spec；`load_roster` 返回 None 时是 `UNAVAILABLE` 而非 ABSENT，走 fail-closed，
  **未被绕过**（亲验）。
- 组探针降为「只判 alive、永不判 exited」是**收紧防御深度**，不动目标范围（通则④边界内）。

## 两轴对 implementer 自认缺口的独立裁断：**合理范围解读，非缺口**

自认缺口是「`status` 只补了 repo 维度交叉核验，未接完整四项 roster 核验」。
两轴**独立**引原文判定成立：`design.md:76` 与 spec 原文均限定「在**破坏性操作前**」，
`status` 零破坏性动作，且一切破坏性调用都在 `run_cleanup` 内各自重新核验（`rm` 前还有第二次）；
全量四项核验会与 Task 2 刚落的 `LIVENESS_PROBE_INTERVAL_SECONDS` 节流直接冲突。

## 🔴 跨票交接（Task 4 MUST 兑现，漏了洞仍在）

1. **`outside-voice.sh` MUST 把 `OV_RUNNER_PID`（纯十进制）原子写入 `SDFLOW_VOICE_RUNNER_PID_FILE`**
   —— worker 已下发该环境变量路径，消费侧 `read_runner_pid` / `probe_runner_pid` 与契约 docstring
   均已就位，**Task 4 只需在 `.sh` 里写这个文件，不必回改本票代码**。
   漏做的后果（Spec 轴实证）：无 terminal witness 的站点**恒 `unverifiable`** ⇒ `cleanup --cancel`
   **永不解闸 fallback**。这是诚实 fail-closed（OVBG-03 允许），但 LOST 站点永远拿不到同族 fallback。
2. **该 pid 文件建议 0600** —— 当前 Task 4 契约未规定权限（内容仅一个 pid、非 payload 面，
   但与本 change 其余 sidecar 的 0600 口径一致更好）。
3. `probe_subtree` 的「terminal witness ⇒ exited」窄口（helper 被 SIGKILL 的情形）只能靠 Task 4
   的信号关掉，已在 docstring 显式登记 —— 属诚实降级，**须 Task 4 兑现**。

## 编排层记录：并行评审的变异互踩（本轮暴露的流程缺陷）

Standards 轴首跑曾 2 failed，查明是**两个评审子代理并行做变异验证时互相污染同一工作树**
（源文件 mtime 落在其运行期间），树稳定后同两条即绿。**这次是假红且被识破，但同一机制也能产出假绿。**
⇒ 后续票的 dispatch prompt MUST 要求「变异在 scratchpad 独立副本进行，MUST NOT 修改仓内文件」。
不改成串行（串行翻倍墙钟，而副本隔离零成本）。

实跑：`pytest sdflow-init/tests/test_outside_voice_job.py -q` → **291 passed**；
全量 **2441 passed / 8 skipped / 3 xfailed**。
