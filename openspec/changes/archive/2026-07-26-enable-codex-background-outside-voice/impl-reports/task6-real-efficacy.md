# Task 6 impl report —— 真实 efficacy 门与 T162 处置

**R-ID**：OVBG-01 / OVBG-03 / HAE-08 / HAE-09（落笔前已逐条通读四条 delta spec 的 SHALL + 全部 Scenario）
**Blocked-by**：Task 5（已 checkpoint，起手 HEAD = `6dc9919`）

---

## 🔴 结论先行：**G1 未达标 ⇒ T162 保留，design/CONTEXT/hand-off 的「Codex efficacy=0」陈述一字未改**

**阻断原因不是实现缺陷，是外部账户额度**：本机 Codex CLI 的 ChatGPT 登录**已耗尽用量配额**，
最早 **2026-07-29 10:11** 才恢复（今天 2026-07-26）。∴ **无法起任何一轮 Codex 宿主评审**，
tasks.md 6.1 要求的「该层全部 declared 站点取得 `host="codex"`」在本轮**根本无从产生**。

按 tasks.md 6.3 明文：「若任一站点未可信 collect/未 `ok`、没有自然 >300 秒成功证据或证据字段
不可机读，则**保留 T162 并如实记录，不得以编排 smoke 假绿**」——本报告即该如实记录。

> ⚠️ **MUST NOT 把下文的 transport 证据读作 efficacy 证据。** 我做的是**后台通道探针**，
> 它跑在 **Claude 宿主的 shell 里**，`host="claude"`。确定性检查器**当场把它判红**（见 §四）。
> 「helper 的行为与宿主无关，所以 codex 下也一样」——这是推断，**不是证据**，MUST NOT 拿它关缺口。

---

## 一、`setup.sh` 前后的全局状态快照（含还原后亲验）

### 1.1 跑之前（`/private/tmp/.../global-state-before.txt` 同源）

```
~/.sdflow/               workflow -> /Users/cheneyzhao/.skills/sdflow-skills/sdflow-init/assets/workflow
~/.sdflow/hack/          checkpoint-commit.sh · outside-voice.sh(52254B) · resolve-models.sh
                         · resolve-workflow.sh · skill-principles.md
                         ❗ 无 outside-voice-job.py、无 capability-manifest.json（Task 1–5 的成果尚未落地）
~/.claude/skills/·~/.codex/skills/   17 条 sdflow 系 symlink，全部 -> /Users/cheneyzhao/.skills/sdflow-skills/*
                                     （含合并前 bug/todo 双池 skill 遗留的两条 Jul 21 旧链）
```

### 1.2 `bash setup.sh`（开发 checkout）后

`v0.10.0 ready`，38 项 installed。关键差异：

```
~/.sdflow/workflow  -> /Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-init/assets/workflow   ← 接管到 dev
~/.sdflow/hack/     + outside-voice-job.py (118687B, 0755)
                    + capability-manifest.json (388B)
                      outside-voice.sh 52254B → 59928B（Task 4 的 isolation flags + runner pid sidecar）
15 条 sdflow 系 symlink -> /Users/cheneyzhao/Documents/04-sdflow-skills/*
setup.sh 自带三门当场绿：sync_principles ✅18 · gen_workflow_guide ✅ · async-branch-parity ✅
```

**从已安装快照跑 preflight（`cwd` = `zhws_ops_api`）—— Task 5 遗留的「真实 HOME 未验」项在此兑现：**

```json
{"ok": true, "reason_code": "ready", "claude_bin": "/Users/cheneyzhao/.local/bin/claude",
 "job_dir": "/Users/cheneyzhao/.sdflow/hack",
 "checks": {"claude-version": {"ok": true, "detail": "2.1.220"},
            "agents-json":    {"ok": true, "detail": "3 个会话"},
            "capability-manifest": {"ok": true, "detail": "generation=3bb91090fbad2115…"},
            "posix-shell":    {"ok": true, "detail": "darwin / /bin/sh"}}}
exit=0
```

四项**全部**在真实 HOME 上过，`job_dir` 是安装路径、不含仓根 ⇒ 走的确是安装态而非仓内源。

### 1.3 还原后（在运行 checkout `~/.skills/sdflow-skills` 重跑 `bash setup.sh`）

见 §八「收工亲验」——已还原并逐条 `ls -l` 核对。

---

## 二、Codex 宿主评审的实际执行方式与失败实录

### 2.1 判据先行：spec-review 还是 code-review？（②：调研后给结论，不甩开放题）

- `zhws_ops_api` 在 `master`、工作树干净、`openspec/changes/` 下**只有 archive、无活跃 change**。
- `sdflow-code-review` 第零步硬要求「代码已实现且**在 feature 分支**」+ `merge-base` diff base ⇒ 无对象。
- `sdflow-spec-review` 只需 `{change_dir}` 的四件套，**归档目录里四件套俱全**。

⇒ **结论：走 spec-review**，对象取最新归档 change `2026-07-25-manage-permission-catalog-items`
（proposal 87 行 / design 425 行 / 6 份 delta spec，体量足以产生真实评审负载）。

### 2.2 实跑命令与输出（原文）

先做 host 探测 smoke（**确认 `CODEX_THREAD_ID` 真能让 `resolve-models.sh` 判出 `codex`**，
再决定要不要投整轮成本）：

```
$ cd /Users/cheneyzhao/Documents/20-projects/10-appbuilder/zhws_ops_api
$ codex exec --dangerously-bypass-approvals-and-sandbox -C "$PWD" \
    'Run exactly this one shell command and paste its raw stdout+stderr verbatim, then stop: …'

OpenAI Codex v0.145.0
workdir: /Users/cheneyzhao/Documents/20-projects/10-appbuilder/zhws_ops_api
model: gpt-5.6-sol   provider: openai   approval: never   sandbox: danger-full-access
reasoning effort: high   session id: 019f9a3f-f078-7000-98a3-407560b47a07
--------
ERROR: You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage
       to purchase more credits or try again at Jul 29th, 2026 10:11 AM.
```

**复现一次以排除瞬时抖动**（最小 prompt `print OK`）：同一条 `ERROR: You've hit your usage limit`，
`session id: 019f9a40-2659-7873-a45c-2a1814640442`。⇒ 账户级硬拦，不是本次调用的问题。

### 2.3 有没有别的路子拿到 Codex 宿主？（①：能查的自己查完再下结论）

| 候选 | 实查结果 | 可行性 |
|---|---|---|
| 换 API key 计费 | `env \| grep -iE '^(OPENAI\|CODEX)'` **零命中**；`~/.codex/config.toml` 只有 `model` / `model_reasoning_effort`，**无 `model_provider` / `api_key`** | ❌ 无凭据；且改用户 auth 配置不在本票授权内 |
| `codex login status` | `Logged in using ChatGPT`（就是被限流的那条） | ❌ |
| `--oss` 本地 provider | `command -v ollama lmstudio` **零命中**，两者均未安装 | ❌ |
| 用弱模型顶替编排层 | 即便装上，评审是**门禁步**，`model-tiers.md` 明写禁降档 | ❌ 换来的会是假绿，正是本 change 要消灭的东西 |

⇒ **本机在 2026-07-29 之前不存在任何真实 Codex 宿主路径。** 这是外部约束，**MUST NOT** 靠工程手段绕开。

### 2.4 成本纪律

按本票约束「失败就分析原因、最多重试一轮；连续两轮不成即如实记录并停」——
codex 侧**实跑 2 次**（正式 + 最小复现），均同一账户级错误，**就此停**，未做第三次、未做无界重跑。

---

## 三、后台通道探针（**transport 证明，不是 efficacy 证明**）

投 codex 整轮成本之前，先用**一次真实 opus voice** 验证最险的那道接缝——
「`claude --bg --exec` + 真实模型 runner 能不能跨过 300 秒跑到可信终态」。
（这次调用在 codex 被拦之前就已发起；它**不是**为了替代 efficacy 证据而补的。）

### 3.1 dispatch（真实、非 shim）

```
$ python3 ~/.sdflow/hack/outside-voice-job.py dispatch \
    --run-dir <archive change>/.outside-voice/20260725T170004Z-szMlwM \
    --site design-voice --context-file <同目录>/design-voice-context.md \
    --repo-root /Users/cheneyzhao/Documents/20-projects/10-appbuilder/zhws_ops_api \
    --runner claude --model opus --effort high --timeout 900

{"ok": true, "state": "dispatched", "reason_code": "ok",
 "job_id": "3d3695d5", "session_id": "3d3695d5-c1cb-45d1-8072-fce268cfe5e0",
 "attempt_nonce": "4b85f30b20fcedb5c2de990fe46b9dbc",
 "dispatch_duration_seconds": 1.257, "runner": "claude", "model": "opus",
 "effort": "high", "timeout_seconds": 900}
exit=0
```

context 是**真实评审负载**：proposal「What Changes」+ design「Decisions」全文，**25751 字节**。
dispatch **1.257 s** ≪ 5 秒 monotonic deadline（OVBG-01 / NFR）。

### 3.2 实际落到 argv 上的 runner（`ps` 实抓，非推断）

```
timeout -k 10 900 claude -p --model opus --output-format text \
  --tools Read,Grep,Glob --strict-mcp-config \
  --add-dir /Users/…/zhws_ops_api --settings {"permissions":{"deny":[…11 条 read-fence…]}} \
  --effort high --safe-mode --no-session-persistence
```

⇒ OVBG-04 的四旗 + strong model + `--effort high --safe-mode --no-session-persistence`
**逐项在真实进程上兑现**，工具集精确为 `Read,Grep,Glob`，无 Write/Edit/Bash/WebFetch。
进程树四层俱在（supervisor pty host → `worker` → `outside-voice.sh exec` → `timeout` → `claude -p`）。

### 3.3 终态与 collect

```
$ …collect --run-dir <同上> --site design-voice
{"ok": true, "state": "SUCCEEDED", "reason_code": "ok", "terminal": true, "rc": 0,
 "runner": "claude", "model": "opus", "effort": "high",
 "dispatched_at": "2026-07-25T17:00:24Z", "started_at": "2026-07-25T17:00:25Z",
 "terminal_at":  "2026-07-25T17:07:41Z", "collected_at": "2026-07-25T17:08:00Z",
 "duration_seconds": 436.0,
 "stdout_sha256": "7d1b28145114f39de2c91f8cc51d10b04d216a653c3cf093c0079707d8cbf2d2",
 "stdout_bytes": 5129, "stdout_lines": 27, "stderr_bytes": 19, "stderr_lines": 1,
 "unknown_cost": false, "orphan_warning": null}
exit=0
```

**自然耗时 436 秒 > 300 秒且 rc=0** —— 旧同步天花板会在 300 秒把它砍成 rc=124
（`optimize-device-access-authorization` 的 5/5 rc124 正是这么来的）。**这一条是本票最有价值的实测。**
产出是真评审意见（`## Findings`，high 级，带 `resource/query/auth/check-permission.toml:14-17`
这类可核 file:line 引用），不是空转。

### 3.4 cleanup（identity-safe）

```
{"ok": true, "state": "removed", "removed": true, "stopped": false, "subtree": "exited",
 "orphan_warning": null, "unknown_cost": false, "fallback_allowed": true,
 "identity": {"ok": true, "checks": {"canonical-id": "ok(唯一命中)", "repo": "ok(cwd == repo_root)",
              "site": "ok", "attempt": "ok(盘面 witness 与 roster 命令串 nonce 一致)"}}}
```

四项 identity 核验全过 → `claude rm` → roster 复查该仓 job **零残留**（§八）。

### 3.5 这条探针**证不了**什么（诚实边界，MUST NOT 越界读）

| 证到了 | 没证到 |
|---|---|
| 安装态 preflight ready；dispatch ≤5s 拿到 canonical id | **`host="codex"` 锚**——本次是 Claude 宿主 shell 发起 |
| 真实 opus+high runner、四旗、read-fence 在真进程上兑现 | **一层完整评审**——只跑了 1 个站点，没有 declared 集、没有报告、没有 anchor_lint |
| **自然 436s > 300s 跑到 rc=0**，rc 原子发布、collect 幂等字段齐全 | **Codex 编排层**按 SKILL 的 ②④⑤⑥⑦ 分支真的调得对（HAE-08 的宿主分流未经真机走通） |
| cleanup identity 四项核验 + 子树退出 + roster 清空 | — |

---

## 四、确定性检查器与它的实际输出

### 4.1 落点与形态

| 文件 | 作用 |
|---|---|
| `hack/check_codex_efficacy_evidence.py` | 检查器本体（`emit` 生成证据 / `check` 判定） |
| `hack/tests/test_codex_efficacy_evidence.py` | 60 条测试 |
| `openspec/changes/…/impl-reports/task6-transport-probe-evidence.json` | 本轮探针的结构化证据（**不是 efficacy 证据**） |

与 `check_async_branch_parity.py` / `sync_principles.py` 同级同 idiom（仓级机械门放 `hack/`）。

**三条门逐条对应 tasks.md：**

- **G1〔6.1〕** 每个站点 `host="codex" runner="claude" reason_code="ok"`，且
  `set(declared_sites) == set(证据站点)`（**双向**相等——单向包含会放过「漏收一个站点」，
  正是 HAE-09「per-site 完整性机械可审」那条）。
- **G2〔6.2〕** ≥1 站点 `duration_seconds > 300`（**严格大于**，等于 300 证不出「跨过」）
  ∧ `model=opus` ∧ `effort=high` ∧ `reason_code=ok` ∧ `runner=claude`。
- **G3〔6.1 末句〕** 四个时刻可解析且单调、`duration` 与 `terminal-started` 自洽（容差 1s）、
  digest 为 64 位小写十六进制、`stdout_bytes/lines ≥ 1`。

**「不含 context/stderr」怎么做成机械保证**（而非「我没写进去」）：
顶层与 site 的 key 集合 **MUST 精确等于白名单**（多一个即红 ⇒ `stderr_text` 这类字段**无落脚点**），
且任意字符串值**无换行、长度 ≤ 256**（⇒ 正文塞不进任何合法字段）。
stderr 只以 `stderr_bytes` / `stderr_lines` 两个**计数**出现（OVBG-04 写出面约束）。
`emit` 从 `<site>.collected.json` 机械派生并**丢弃** `detail` / `stdout_path` / `state` 等非白名单字段。

**语法面（基准 5）**：输入是 JSON，由 `json.load` 解释——**MUST NOT** 演化成「从 Markdown 报告里
正则抠证据」。证据单一源就是那个 `.json`，报告只引路径。

### 4.2 检查器对本轮证据的**实际输出**（红，且红得对）

```
$ python3 hack/check_codex_efficacy_evidence.py emit --run-dir <run-dir> --host claude \
    --layer spec-review --repo zhws_ops_api \
    --change 2026-07-25-manage-permission-catalog-items \
    --declared-sites design-voice --out <…>/task6-transport-probe-evidence.json
[efficacy] 已写出证据 …/task6-transport-probe-evidence.json（1 站点）        exit=0

$ python3 hack/check_codex_efficacy_evidence.py check --evidence <…>
[efficacy] ❌ 未通过（2 条）：
   · host='claude' ≠ 'codex' —— 本证据只对 Codex 宿主有意义
   · site[design-voice].host='claude' ≠ 'codex' —— G1 要求该层每个站点都是可信跨模型成功
   ⇒ tasks.md 6.3：保留 T162 并如实记录，MUST NOT 以编排 smoke 假绿
exit=1
```

**这正是本票要的形状**：证据被机械拒收，`--host claude` 是我如实填的，
检查器不接受「Claude 宿主的成功」顶替 Codex efficacy。

### 4.3 诚实边界：`host` **不是**盘面可派生量

> 🔴 **本节结论已被 fix1 推翻（保留原文作轮 1 实录，MUST NOT 据此写新代码）。**
> 轮 1 双轴审的 I3 指出：`dispatch` **就跑在宿主 shell 里** ⇒ `host` 有确定性信号也有捕获路径。
> fix1 已把它做成盘面派生（dispatch 读 env → `job.json` → collect 透传 → 证据），
> **`emit` 的 `--host` 入参随之删除**。当前口径见 `task6-real-efficacy-fix1.md` §4.5–4.6。
> 仍成立的只有 `declared_sites` 那半句。

`collect` 的 payload 里**没有** `host` 字段——helper 只知道 `runner`，不知道自己被哪个宿主的编排层调用。
∴ `emit` 的 `--host` 是**必填入参**，谁跑谁负责；检查器机械守的是「一旦声明成 codex，就必须处处自洽且达标」。
`declared_sites` 同理（权威在评审报告锚行）。**MUST NOT 声称这两项有机械捕获路径。**

### 4.4 测试与**反向变异实证**（防「宣称有锚实则假绿」）

`pytest hack/tests/test_codex_efficacy_evidence.py -q` → **60 passed**。
逐条把检查器改坏一处，确认对应断言**真的会红**（全部实跑，非推断）：

| 变异 | 结果 |
|---|---|
| `MIN_NATURAL_DURATION_SECONDS 300 → 0` | 3 failed |
| duration 自洽检查 `if abs(…) > 容差:` → `if False:` | 2 failed |
| 站点集相等 `!=` → 单向包含 `not <=` | 1 failed |
| site key 白名单 `set(site) - SITE_KEYS` → `frozenset()` | 1 failed |
| 换行守卫 `if "\n" in node…` → `if False:` | 1 failed |
| G1 三元组 `if site[field] != expected:` → `if False:` | 2 failed |
| `MAX_STRING_LEN 256 → 10**9` | 3 failed |
| `DURATION_CONSISTENCY_TOLERANCE_SECONDS 1.0 → 10000.0` | 3 failed |

> 🔴 **一次自捕**：`MAX_STRING_LEN → 10**9` 的**首轮变异是绿的**——因为超长断言写成
> `"x" * (CE.MAX_STRING_LEN + 1)`，**随常量一起缩放 ⇒ 恒真锚**（正是 task5-review 主线发现的同族）。
> 已修：改用绝对字面量 `PROSE_SIZED = "x" * 4096`（「4096 字符的东西一定是正文」），
> 并把 `MAX_STRING_LEN == 256` / 容差 `== 1.0` 钉进常量测试。修后该变异 3 failed。

---

## 五、三条门逐条判定

| 门 | 判定 | 依据 |
|---|---|---|
| **G1** 该层全部 declared 站点 `host="codex" runner="claude" reason_code="ok"` | ❌ | Codex 账户额度耗尽至 2026-07-29，**一轮 Codex 宿主评审都没跑成**（§2.2 两次实录）⇒ 不存在任何 `host="codex"` 锚。检查器实跑 exit=1（§4.2） |
| **G2** ≥1 站点 `opus`+`high` 自然 >300 秒且成功 | ⚠️ **实质已证，但不在 codex 层内** | 真实 opus+high、自然 **436 s**、rc=0、digest 齐全（§3.3）。但它**不是 Codex 宿主产出的**（该证据的 `host` 字段实为 `null` —— probe 跑在 Claude 宿主、且早于 host 盘面派生落地）⇒ **不满足 6.2「该完整层必须含」的限定**，MUST NOT 单独记作达标 |
| **G3** 字段可机读、不含 context/stderr | ✅ | 检查器的 G3 段对该证据**零报错**（§4.2 只报了 host 两条）；白名单 + 无换行 + ≤256 三重机械守，60 条测试 + 8 组变异 |

**G1 ❌ ⇒ 三条不同时达标 ⇒ 按 tasks.md 6.3：保留 T162。**

---

## 六、T162 的处置

**保留（未关闭）。** 依据 tasks.md 6.3 的「仅当 6.1/6.2 同时达标且确定性 evidence checker 通过后关闭」。

- `openspec/issues/todolist/2026-07-todolist.md` 的 `## T162` **一字未改**（本票只授权在**达标时**改
  design/CONTEXT/hand-off 的 efficacy 陈述，未达标 ⇒ 连那一处也不改）。
- `design.md` / `openspec/CONTEXT.md` / hand-off 里的「Codex efficacy=0」相关陈述**全部保持原样**
  —— `git status` 亲验：本票工作树只有 3 个新增文件，**零修改行**（§七）。
- **达标后要改的那几处陈述在哪**（本轮**一处未动**，替将来重跑的人先定位好）：
  `design.md:159`（ADR-3「`zhws_ops_api` 五个真实站点均为 rc124」）·
  `design.md:244`（Test Coverage 段的真实 efficacy 门口径）·
  `design.md:270`（Open Questions 的收敛陈述）·
  `sdflow-spec-review/SKILL.md:398` ≡ `sdflow-code-review/SKILL.md` 同行
  （「该兼容分支已知 efficacy=0」——⚠️ 在 `sdflow:async-branch` 等值段内，
  **改一侧必须两侧同改**，否则 `check_async_branch_parity.py` 当场红）。
- **重开条件（可机械复核）**：2026-07-29 10:11 之后 Codex 额度恢复 ⇒ 重跑 §2.2 的
  `codex exec` 起一轮 spec-review，用 §4 的 `emit` + `check` 判定即可关门。
  ⚠️ **`emit` 没有 `--host` 入参**（fix1 起 `host` 改为盘面派生：dispatch 在宿主 shell 里读出
  → `job.json` → collect 透传 → 证据；见 `task6-real-efficacy-fix1.md` §4.5–4.6）。
  照旧写法带 `--host codex` 会 argparse **exit 2**。
  **本票已把「怎么判」做成脚本，剩下的只是「在真 Codex 宿主里跑一轮」。**

---

## 七、全部门禁命令的实际输出

```
$ /usr/bin/python3 -m pytest -q
2557 passed, 10 skipped, 3 xfailed in 261.54s (0:04:21)
        基线 2497 passed / 10 skipped / 3 xfailed；差额 = 本票新增 60 条，skip/xfail 数一条不变

$ /usr/bin/python3 -m pytest hack/tests/test_codex_efficacy_evidence.py -q
60 passed in 0.20s

$ python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致                        exit=0

$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 18 个投放面全部与真相源一致                                  exit=0

$ git diff --check
（无输出）                                                                       exit=0

$ openspec validate enable-codex-background-outside-voice --strict
Change 'enable-codex-background-outside-voice' is valid                          exit=0
```

**本票工作树（`git status --porcelain`）—— 3 个新增、零修改：**

```
?? hack/check_codex_efficacy_evidence.py
?? hack/tests/test_codex_efficacy_evidence.py
?? openspec/changes/enable-codex-background-outside-voice/impl-reports/task6-transport-probe-evidence.json
```

未勾任何复选框、未打 `task6-` 完成标签、未改四件套（`git diff --stat` 空）。

---

## 八、`zhws_ops_api` 与全局安装状态的收工亲验

### 8.1 下游仓（验收标准第 6 条）

```
$ git -C <zhws_ops_api> status --porcelain
（空 —— 工作树进来时干净，出去时同样干净）

$ git -C <zhws_ops_api> status --porcelain --ignored <archive change>/
!! openspec/changes/archive/2026-07-25-manage-permission-catalog-items/.outside-voice/

$ git -C <zhws_ops_api> diff --stat HEAD -- openspec/workflow/
（空 —— canonical workflow 规则零改动）
```

- 唯一产物是 **gitignored** 的 `.outside-voice/<run-id>/`（`.gitignore` 的 `**/.outside-voice/` 覆盖）。
  **有意保留**：OVBG-05 明写「不得删除 `.outside-voice/<run-id>/` 的本轮审计证据」，
  且 §4 的证据文件引用它。它不入库、不污染下游仓。
- **canonical workflow 规则未被直接手改**（上面 `diff --stat` 空即证）；
  Codex 评审因额度未跑成 ⇒ 也没产生任何报告/锚写入。
- supervisor roster 对该仓 job 残留：`claude agents --all --json` 过滤 `cwd` 含 `zhws_ops_api` → `[]`。

### 8.2 全局安装还原（在**运行 checkout** 重跑 `bash setup.sh`）

```
$ bash ~/.skills/sdflow-skills/setup.sh
✓ workflow @ ~/.sdflow — 接管：…/Documents/04-sdflow-skills/… → …/.skills/sdflow-skills/…
[sync_principles] ✅18 · [gen_workflow_guide] ✅ · [async-branch-parity] ✅
```

**逐条 `ls -l` 与跑前快照 diff：唯一差异是 mtime（Jul 25 17:18 → Jul 26 01:18）。
全部 32 条 symlink 的 target 一条不差地指回 `/Users/cheneyzhao/.skills/sdflow-skills/*`，
`~/.sdflow/workflow` 亦然；`outside-voice.sh` 从 59928B 退回 52254B（旧版）。**

#### ⚠️ 残留两个文件（**不静默**，显式登记）

运行 checkout 的 `setup.sh` 是**旧版**（无 `*.py` 安装循环）⇒ 它**不认识**、也就不会清掉这两个：

```
~/.sdflow/hack/outside-voice-job.py        118687B  Jul 26 00:58   ← dev setup 装的
~/.sdflow/hack/capability-manifest.json       388B  Jul 26 00:58   ← 对「新 outside-voice.sh」算的
```

**实跑确认它们不会造成假绿——反而当场自证 OVBG-01 的 fail-closed：**

```
$ python3 ~/.sdflow/hack/outside-voice-job.py preflight
preflight 未通过 [capability-manifest]: 安装 skew: outside-voice.sh 内容与快照不符
  → 安装快照不一致——在运行 checkout 重跑 `bash setup.sh` 刷新 ~/.sdflow/hack/
{"ok": false, "reason_code": "preflight-error", …}                              exit=1
```

⇒ 新 job helper × 旧 shell helper 的混配被 manifest **当场识破**，落 `preflight-error`，
按 HAE-08 走 5 秒级同族 fallback。**这是 Task 5 只在 tmp HOME 上测过的那条 skew 门，
在真实 HOME 的真实混配上第一次得到验证。**

**为什么不删掉它们**（而不是「忘了删」）：
- **载荷性的还原已完成**——本票明令要防的是「把全局链留在 dev checkout 上」，
  32 条 symlink 全部已指回运行 checkout。这两个是**多出来的文件**，不是被改坏的链。
- **留着与删掉，可观察行为等价**：删掉 ⇒ preflight 报「job helper 未安装」→ fallback；
  留着 ⇒ preflight 报「安装 skew」→ fallback。**都是 fail-closed，且留着的那条 hint 更准**
  （它直接点名修法 = 重跑 setup.sh，而那正是本 change 合并后要做的事）。
- 全局 CLAUDE.md 的安全规则是「**未经真人明确确认不删文件**」，而上游 agent 的 prompt
  不构成真人确认。∴ 取「**响亮报告 + 不删**」——本票禁的是「**静默**留下不一致状态」，不是留下状态。

**要清干净，一条命令**（合并后本就会跑，届时自动变成正确的同代快照）：
`bash ~/.skills/sdflow-skills/setup.sh`（在运行 checkout 已含本 change 的代码之后）。

---

## 九、未做 / 降级项（如实报告）

1. **【最要害】Codex 宿主的完整一层评审：未跑成。** 原因 = 外部账户额度耗尽至 2026-07-29（§2.2 两次实录 + §2.3 四条替代路径全查过）。
   ⇒ G1 ❌、T162 保留、efficacy 陈述不改。**这不是「我觉得可能不行所以没跑」——两次真实调用都留了 session id。**
2. **HAE-08 的 Codex 宿主分流未经真机走通**：SKILL 段内 ②④⑤⑥⑦ 的 codex 分支只有 Task 3/5 的
   段内 golden 守着，**没有一次真实 Codex 编排层执行过它**。这是本 change 剩下的最大未验面。
3. **G2 的证据不在 codex 层内**：436 s 的成功是 Claude 宿主 shell 直调 helper 拿到的。
   按 6.2 字面（「该完整层必须至少含一个…」）**不计达标**。
4. **`--effort high` 与 `--model opus` 是我在 dispatch 命令行显式给的**，不是 Codex 宿主下
   `resolve-models.sh` 解析出来的（本机 `CLAUDECODE=1` ⇒ 它只会解析出 `SDFLOW_VOICE_RUNNER=codex`）。
   两者数值与 canonical 缺省一致，但「解析链在 codex 下确实吐出 claude/opus」**未经真机验证**。
5. **`~/.sdflow/hack/` 残留两个文件未删**（`outside-voice-job.py` + `capability-manifest.json`）。
   理由与实测行为见 §8.2 —— fail-closed、hint 精准、可观察行为与删掉等价；
   全局 CLAUDE.md 禁未经真人确认删文件。**已响亮登记，非静默残留。**
6. **未改 `openspec/issues/todolist/`**：本票要求「保留 T162」，如实记录落在本报告。
   把「额度 2026-07-29 恢复」这条时效信息写进 T162 会更耐久，但那是本票未授权的范围外改动 ⇒ 交编排层裁决。

---

## 十、Concerns（交给双轴审判）

1. **`layer` 字段对本轮证据略显名不副实**：探针只跑了 1 个站点、没有报告与 anchor_lint，
   却在证据里写 `layer="spec-review"`（因为 `design-voice` 属 spec-review 的站点集）。
   检查器**不因此判红**（它靠 `host` 那条红），文件名 `task6-transport-probe-evidence.json` 与
   §3.5 的边界表承担区分职责。若评审认为「证据文件的存在本身就有被误读成 efficacy 证据的风险」，
   可考虑给 schema 加一个 `evidence_kind: probe|layer` 枚举 —— 我判**不加**：
   多一个字段就多一处要守的口径，而 `host≠codex` 已经把门关死了（④）。
2. **`MAX_STRING_LEN=256` 是拍的**：够装 `run_id`/`job_id`/`change` 名，装不下段落。
   若将来 change 名超长会误红——报错点名字段，fail-closed 方向正确，登记为已知刚性。
3. **检查器只在本仓被 pytest 调用，未接进 `setup.sh` 三门**：它判的是**一次性的 Task 6 证据**，
   不是每次安装都要复核的不变量。接进 setup 会让一份历史证据变成永久门 ⇒ 判**不接**。
4. ~~**`--host` 由调用者自报**（§4.3）：这是真诚实边界，不是可修的洞。
   若要机械化，得让评审 SKILL 在落锚时把 `host=` 一并写进 run-dir 的某个 sidecar——
   那是改 SKILL 的活，属本票范围外。**MUST NOT 声称当前已机械捕获。**~~
   🔴 **已被 fix1 推翻**（同 §4.3 的批注）：捕获点不在评审 SKILL，而在 `dispatch` 自己所在的
   宿主 shell —— fix1 已做成盘面派生并删掉 `--host`。此条的「不是可修的洞」判断**是错的**。
