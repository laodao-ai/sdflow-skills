# hand-off — enable-codex-background-outside-voice

**日期**：2026-07-26 · **verify**：PASS（`verify-report.md`，`reviewed_sha=e3450df8…`）
**issues 批次**：`enable-codex-background-outside-voice`（21 项，见 `openspec/issues/batches.md` / `INDEX.md`）

---

## ✅ 完成了什么

> 下列每条都**复核过锚点存在性**（测试名 / 文件:行 真的在），不是从 verify 报告直接搬运。

| 能力 | 交付 | 锚点 |
|---|---|---|
| **后台派发** | 无副作用 preflight + `O_CREAT\|O_EXCL` reserve + 5 秒 monotonic dispatch deadline + 跨发起 shell 存活的 worker | `outside-voice-job.py` `cmd_dispatch`/`cmd_worker`；`test_outside_voice_job.py`（331 例） |
| **终态派生** | 状态**从盘面派生**而非另存可变字段；rc/liveness 笛卡尔归类；终态前不读 stdout；幂等 collect | `derive_status` / `build_collect_payload`；126 格笛卡尔用例 |
| **恢复与清理** | `reconcile --run-dir` 显式恢复（禁猜「最新 run」）+ identity-safe cleanup（stop → 子树退出核验 → rm） | `reconcile_site` / `run_cleanup` / `probe_subtree` / `verify_identity` |
| **runner 隔离** | Claude 反向 runner 显式带 `--effort high --safe-mode --no-session-persistence`；runner pid sidecar（0600、`umask 077`+`mv -f` 原子）；`claude logs` canary 证明 context/stderr 不进 supervisor transcript | `outside-voice.sh` 1.5.0；`test_outside_voice.py` argv golden |
| **宿主自适应调度** | 两份评审 SKILL 的 `sdflow:async-branch` 段逐字节等值；**删除 Codex sync 300 秒兼容分支**；`unknown_cost` 命中即禁自动同族 fallback | `check_async_branch_parity.py` ✅ 2 处逐字节一致 |
| **同代安装快照** | `setup.sh` 装 `*.py` + 由 helper 自己的 `install-manifest` 子命令写 manifest（shell 侧无第二份 hash 口径，`grep -in "sha\|shasum\|md5\|digest\|generation" setup.sh` 零命中） | `test_setup_sdflow.py` |
| **efficacy 检查器** | 确定性三门（G1 站点集**双向**相等 / G2 严格 `>300` / G3 字段可机读）+ 闭合 key 白名单挡 context/stderr 外泄 | `check_codex_efficacy_evidence.py`；`test_codex_efficacy_evidence.py` |

**门禁实跑**（本轮亲跑，非引用）：全量 `2634 passed, 10 skipped, 3 xfailed` ·
parity ✅ · principles ✅ 18 投放面 · `git diff --check` 干净 · `openspec validate --strict` valid。

**质量层实况**：六张票每张都过双轴审，累计挖出 **6 Critical + 13 Important**，无一条来自「读代码觉得不对」——
全是构造场景真跑出来的（真起 `gtimeout` 子进程、把生产 argv 回放给真 CLI、定点删门看是否变红）。
随后的冷层代码审又独立挖出 4 条（其中 1 条高危两源命中），当场修 3 条并补 5 条经变异验证的锚。

---

## ⏳ 未完成 / 延后

### 🔴 头号缺口：**Codex 真实 efficacy 未证**（`proposal.md` 的 Success Metric #1）

**状态未变，MUST NOT 读成「已验证」**：

- `tasks.md` **6.1 / 6.2 保持未勾**；`superpowers-plan.md` Task 6 的验收框 1/2/3 **保持未勾**。
- **T162 保留 OPEN**；`design.md` / `openspec/CONTEXT.md` 里的「Codex efficacy=0」陈述**一字未改**。
- 全仓**零** efficacy evidence.json 产出。

**原因**：本机 Codex CLI 的 ChatGPT 额度在实现期耗尽（两次 `codex exec` 均返 usage limit，
最早 2026-07-29 10:11 恢复），四条替代路径逐条查证不可行。
**处置**：真人用户于 2026-07-26 在被完整告知「头号指标未证」后**明确拍板选项 A**——降级合并，
缺口移交后续 change。这是**人的范围决定**，不是质量放行。

**已取得的两条真证据**（不足以关闭缺口，但可作后续对照）：
1. transport 全链路走通：真实 opus + high、自然 **436 秒**、rc=0、digest 齐全 ——
   旧同步 300 秒天花板会把它砍成 rc=124。但它**不是 Codex 宿主产出的**（`host` 字段实为 `null`），
   不满足 6.2「该完整层必须含」的限定。
2. 真实混配下 **OVBG-01 skew fail-closed 首次触发**。

> **反向硬锚**（verify 亲跑）：把上面那份 436 秒证据喂进 `check_codex_efficacy_evidence.py check`
> → **exit=1，当场判红**（`host=None ≠ 'codex'`）。`host` 是从 `<site>.job.json` **盘面派生**的，
> 检查器连 `--host` 入参都没有 ⇒ 伪造不了。**这是「没有假绿」的机械证明，不是自述。**

### 延后项（批次 `enable-codex-background-outside-voice`，21 项）

**本轮冷层代码审新增 7 项**：

| ID | 内容 | 归属 |
|---|---|---|
| **T225** | 额度恢复后（≥2026-07-29）跑真实 Codex 宿主评审补证 efficacy 三门 | 承接头号缺口 |
| **T226** | 给 efficacy 检查器 `check` 补 `--run-dir` 逐站点交叉核验 | **与 T225 同批做** |
| **B21** | `acquire_reservation` slot-limit TOCTOU（30 轮实测 12 轮 0 存活预留） | 目标态至多 2 站点、走不到该分支 |
| **B22** | `migrate_legacy.py` 迁移写入与 reindex 不在同一锁事务内 | **不属本 change 范围**（见下方 scope drift） |
| **T227** | worker 无信号转发 + cleanup 从不 kill `runner_pid` | 实现符合 OVBG-05 原文，属加宽 |
| **T228** | `secret_scan` 被 NUL 切断 + 二进制命中时 stderr 措辞 | 既有代码，非本 change 引入 |
| **T229** | 🔴 三处 spec 措辞订正 —— **见下方「archive 遗留」** | archive 阶段本应做 |
| **T230** | 出境 `.stdout` 无大小上限 | 廉价加固 |

**实现期累积 13 项**：T212–T224（各票双轴审的 Minor defer）。

### 🔴 T226 单列：**efficacy 检查器不是防伪门**

两个独立来源同时命中（冷层对抗镜实跑复现 + 跨模型 code-voice）：`verify()` 只核 evidence.json 的
**内部自洽性**，从不打开 `<site>.collected.json` 去对 `job_id` / `attempt_nonce` / `stdout_sha256`；
`layer`/`repo`/`change` 纯来自 CLI。⇒ **一份全手工伪造的 JSON 能让三条门全过**（已实跑）。
它挡的是「手抄失误」，不是「自报为真」——而它存在的理由（adr/0018）恰恰是后者。

**当前无假绿风险**（从未产出过任何 evidence.json，且缺口如实保留），已在该文件 docstring 的
「诚实边界」节写死这段声明防后人误读。**加固与 T225 同批做**——T225 会产出**第一份真实 run-dir**，
新绑定只有对着真证物才验得了；现在做只能用自造 fixture 验，等于用被测对象自身的假设去验它。

### ⚠️ scope drift：分支带了 3 个本 change 范围外的提交

| 提交 | 内容 | 问题 |
|---|---|---|
| `de549f4` | `sdflow-issues/scripts/migrate_legacy.py`(+384) + 测试(+198) + SKILL.md(+20) | **`openspec/` 下查无对应 change/spec**（`grep -rl migrate_legacy openspec/` 零命中） |
| `2a587a1` / `edf2ff9` | `docs/sdflow-context-policy.md`(+288) + `docs/subagent-definitions-plan.md`(+328) | 除自引用外无消费者 |

三者均落在设计门批准之后、plan 落盘之前，**会随本 change 一起上 main**。
风险低（有测试、被全量 pytest 覆盖），但它绕过了 change 流程。
**未自行摘除**——摘除等于我单方面改范围，且改写已提交历史属破坏性操作；处置权在人。

### 🔴 archive 遗留：T229 的三处 spec 措辞**本轮未订正**

`openspec archive` 走的是 **`--skip-specs` fallback**（本仓主 specs 为中文遗留格式，CLI 重建会
校验失败），随后由归档子代理**按代码实况**手动同步 delta。下列三处是**已知的 spec 措辞落后于实现**，
需在后续 change 里订正（本轮如实登记为 T229，未静默带过）：

1. **OVBG-01「dispatch MUST 在 monotonic 5 秒 deadline 内返回」** —— 实现是 communicate ≤5s +
   收流 ≤5s + **独立的** nonce lookup grace，端到端上界不是 5 秒。这是**代码里写明理由的有意设计**
   （核验用独立 grace，不与 dispatch 抢同一份预算；`duration` 覆盖到核验结束，正是为了让拿它跟
   deadline 比的断言不恒真）。
2. **OVBG-05「破坏性操作前 MUST 重新核验四项 identity；无法核验时只允许告警」** —— 实现只有
   `canonical-id` 必须**肯定**核验，`repo`/`site`/`attempt` 是「矛盾即一票否决、缺席不阻塞」。
   依据写在 `verify_identity` docstring：真机上 `state="done"` 的 roster 条目**没有 `name` 字段**
   （Task 1 实测），四项都要求肯定证据的话正常完成的 job 永远 rm 不掉。
3. **`host-adaptive-execution/spec.md` 与 `spec-workflow/spec.md` 仍只写「四旗」** ——
   OVBG-04 已含三面隔离旗（Task 4 起就交接的项）。

---

## ▶ 下一阶段建议

**优先级 1 —— 开一个 `close-codex-efficacy-gap` change（≥2026-07-29 额度恢复后）**
一次做完整（基准 4「一个 change 一个完整阶段结果」）：
① 跑真实 Codex 宿主评审取三门证据（**T225**）；
② 同批给 `check` 补 `--run-dir` 交叉核验并对着那份真 run-dir 验（**T226**）；
③ 三门过则关闭 **T162** 并同步 `design.md` / `CONTEXT.md` 的 efficacy 陈述；不过则继续如实保留。

**优先级 2 —— 开一个 `align-background-job-specs` change**
订正 **T229** 的三处 spec 措辞（本轮 archive 未订正，见上）。纯文本，可与优先级 1 合并做。

**优先级 3 —— 处置 scope drift**
`migrate_legacy.py` 补一个追溯性 change/spec，并一并修 **B22**（锁事务）。

**不建议现在做**：**T227**（前提未验——`claude --bg` 的 stop 走 per-pid 还是 killpg 没核实过，
走 killpg 则整条不成立；MUST 先用一次真实后台 agent 把前提验掉）· **B21**（目标态至多 2 站点，
走不到该分支；站点集若扩容到 3+ 再立即升级为阻断项）。

**合并后立刻要做的一件事**：在运行 checkout 重跑 `bash ~/.skills/sdflow-skills/setup.sh` ——
全局 `~/.sdflow/hack/outside-voice.sh` 目前仍是 **1.4.3**，而本 change 已升 **1.5.0**，
且新增的 `outside-voice-job.py` 尚未安装。不重跑 = 新 SKILL 调旧脚本。
