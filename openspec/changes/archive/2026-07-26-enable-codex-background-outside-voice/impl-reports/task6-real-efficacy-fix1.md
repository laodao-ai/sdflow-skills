# Task 6 fix1 —— 双轴审轮 1 双 FAIL 的修复报告

**上轮报告**：`task6-real-efficacy.md`（**未覆盖**，只按 Critical 改了其中 1 行措辞）
**起手 HEAD**：`3c7ff5e`
**范围**：Critical ×1（两轴独立抓到同一条）· Important ×3 · Minor ×2 · 已裁定不修项 ×4（原样保持）

---

## 0. 结论先行

| 项 | 状态 |
|---|---|
| Critical（守卫在 tracked 集上必红） | ✅ 已修，`git add -A` 后全仓绿 |
| I1 顶层 `host` 门无锚 | ✅ 已补锚，反向变异 **7 failed** |
| I2 克隆见证可伪造 per-site 完整性 | ✅ 三字段各自加检测 + **逐字段**反向变异各 1 failed |
| I3 `host` 有可机械捕获路径却没捕获 | ✅ **做了**（dispatch → job.json → collect → 证据全链盘面派生），blast radius 实测 = **既有用例零回归** |
| Minor `duration<=0` / `schema_version` 无锚 | ✅ 已定向断言，各 1 failed |
| Minor 摘要 `crossed` 谓词比 `_crossed` 松 | ✅ 已收敛到单一谓词，1 failed |
| 不修项（第 2 条判 ❌ / 第 3 条 ⚠️ / 不加 `evidence_kind` / T162 与 design 不动） | ✅ 全部原样保持 |
| **G1 三条门** | **仍未达标 ⇒ T162 保留，`design.md` / CONTEXT / hand-off 的「Codex efficacy=0」陈述一字未改** |

**本轮没有跑 Codex 宿主评审**：账户额度仍限流至 2026-07-29 10:11（上轮 §2.2 两次实录）。
本轮全部工作是**把门本身做扎实**，不是去关门。

---

## 1. 🔴 Critical —— 守卫在 tracked 集上必红

### 1.1 复现（修前基线，实跑）

```
$ /usr/bin/python3 -m pytest sdflow-issues/tests/test_downstream_reference_guard.py -q
E       AssertionError: 合并 3→1 后仍有活跃托管点引用旧 skill 目录/脚本路径/slash 名（…）：
E           openspec/changes/enable-codex-background-outside-voice/impl-reports/task6-real-efficacy.md: <旧 bug 池 skill 名>
E           openspec/changes/enable-codex-background-outside-voice/impl-reports/task6-real-efficacy.md: <旧 todo 池 skill 名>
1 failed, 2 passed in 0.03s
```

### 1.2 根因（记住这个形态，不是「我不诚实」）

守卫扫的是 **`git ls-files`（tracked 集）**。上轮跑门禁时报告**尚未 `git add`** ⇒ 守卫看不见它 ⇒ 绿；
`checkpoint-commit.sh` 的 `git add -A` 把它纳入 tracked 之后，**同一条守卫立刻红**。
⇒ **这类「扫 tracked 集」的守卫上，未 `git add` 就跑出来的自报门禁结果结构性不可信。**
本轮起，跑全量前 MUST 先 `git add -A`，让**观测时点与门禁输入集对齐**。

### 1.3 修法

`task6-real-efficacy.md:33` 改写措辞，**去掉两个 legacy skill 名的字面串**（**没有**动 allowlist——
往 allowlist 加条目是把门禁改松）：

```diff
-（含 <旧 bug 池 skill 名> / <旧 todo 池 skill 名> 两条 Jul 21 的旧链）
+（含合并前 bug/todo 双池 skill 遗留的两条 Jul 21 旧链）
```

### 1.4 ⚠️ 连带面（Spec 轴 F3）—— 我处理了，请编排层知悉

`impl-reports/task6-review-package.diff` 把报告正文原样复制了一份，**同一行也带着那两个串**。
上轮它是 untracked ⇒ 守卫看不见；`git add -A` 之后它进 tracked 集 ⇒ **守卫会在它身上再红一次**。

**我做了什么**：把该 `.diff` 里**那一行**（唯一命中行）同步scrub成与修后报告一致的措辞，
行数不变、其余字节未动。理由 = 基准 3「面治优先于点补」：它是**同一处正文的派生副本**，
只修源不修派生，`git add -A` 后依然红。

> 🔔 **给编排层**：该包本轮由我 scrub 了一行，**不是**重新生成的完整快照。
> 若编排层要按惯例产出 `task6-review-package-fix1.diff`（前 5 票都是这个形态），
> 请正常生成——**修后的源里已无 legacy 名，重新生成的包自然干净**。
> 另：**我自己新写的所有文件（本报告在内）均不含那两个 legacy 名。**

---

## 2. I1（Standards）—— 顶层 `host` 门无锚

### 2.1 问题

`test_top_level_host_must_be_codex` 原本写成
`_evidence(host="claude", sites=[_site(host="claude", runner="codex")])`
—— **同时**改坏了顶层与 site 的 host/runner。site 级三元组先把它杀了 ⇒
把 `check_codex_efficacy_evidence.py:227` 的 `if evidence["host"] != REQUIRED_HOST:` 改成 `if False:`，
**60 条测试依然全绿**。这就是「断言被无关门满足」的恒真锚形态。

### 2.2 修法

- `test_top_level_host_must_be_codex`：**sites 保持完全合法**（host 仍是 `codex`），只动顶层 ⇒
  失败原因只能出自顶层那一行；断言定向到 `"本证据只对 Codex 宿主有意义"` 这句原文。
- 新增 `test_top_level_host_rejects_every_non_codex_value`，参数化 `claude / unknown / mixed / "" / None`。

### 2.3 反向变异（实跑）

```
=== M-I1: 顶层 host 门 -> if False ===
7 failed, 71 passed in 0.26s
```

---

## 3. I2（Standards）—— 克隆见证可伪造 per-site 完整性

### 3.1 问题

`verify()` 只查了**站点名**重复，没查**身份**重复。把同一份 witness 复制成 3 个站点名
（`job_id` / `attempt_nonce` / `stdout_sha256` **全相同**，只改 `site`）⇒ `verify()` 返回 `[]`，**全绿**。
这正是 HAE-09「漏收站点」的镜像：前者少一个真站点，后者多 N−1 个假站点，**单看站点名两者都自洽**。

### 3.2 修法

比照 `names` 那三行，对三个身份字段各加一次重复检测：

```python
for field, label in (("job_id", "canonical job id"),
                     ("attempt_nonce", "attempt nonce"),
                     ("stdout_sha256", "stdout digest")):
    values = [s[field] for s in sites if isinstance(s, dict) and isinstance(s.get(field), str)]
    if len(set(values)) != len(values):
        ...
```

配套测试：
- `test_cloned_witness_across_site_names_is_rejected[job_id|attempt_nonce|stdout_sha256]` ——
  **逐字段单独撞车**（其余身份都不同）。三条一起撞的话，删掉任意两条检测用例仍绿，证不出各自有锚。
- `test_a_fully_cloned_witness_layer_is_rejected` —— 整份 witness 复制 3 份。
- `test_distinct_identities_across_sites_still_pass` —— 对照组必须绿。
- 新增测试辅助 `_distinct(name, tag)`（身份三件各不相同的合法站点底座）。

### 3.3 顺带修掉的两个同族恒真锚（自捕）

加完检测后发现两条既有用例是**被新门顺手满足**的：

| 用例 | 问题 | 修法 |
|---|---|---|
| `test_two_site_layer_passes`（对照组） | 两站点共用同一个 `stdout_sha256` ⇒ 加检测后**它自己会红** | 给第二站点独立 digest |
| `test_g1_rejects_when_one_of_two_sites_degraded` | 两站点身份全同 ⇒ 断言 `CE.verify(ev)` 会被「身份重复」满足，G1 的 `reason_code` 门被顶着 | 用 `_distinct` 造降级站点 + 断言定向到 `"reason_code"` |

### 3.4 反向变异（实跑，逐字段）

```
=== M-I2a: 三条身份重复检测整体 -> if False ===
4 failed, 74 passed
=== M-I2[job_id]: 从检测表里摘掉 job_id ===
FAILED …::test_cloned_witness_across_site_names_is_rejected[job_id]
1 failed, 77 passed
=== M-I2[attempt_nonce]: 摘掉 attempt_nonce ===
FAILED …::test_cloned_witness_across_site_names_is_rejected[attempt_nonce]
1 failed, 77 passed
=== M-I2[stdout_sha256]: 摘掉 stdout_sha256 ===
FAILED …::test_cloned_witness_across_site_names_is_rejected[stdout_sha256]
1 failed, 77 passed
```

---

## 4. I3（Spec）—— `host` 改成盘面派生量【**做了，不是降级**】

### 4.1 我上轮错在哪

上轮 §4.3 / Concern#4 称「host 不是盘面可派生量、要机械化得改 SKILL，属本票范围外」。
**`collect` 侧那半句是对的，dispatch 侧是错的**：

- `resolve-models.sh:50-51` 判宿主用的就是 `CLAUDECODE=1` / `CODEX_THREAD_ID`；
- 而 **`outside-voice-job.py dispatch` 就跑在宿主自己的 shell 里** —— 实查
  `sdflow-spec-review/SKILL.md:416` ≡ `sdflow-code-review/SKILL.md:416`：SKILL **直接**调
  `python3 ~/.sdflow/hack/outside-voice-job.py dispatch …`，**不经 `outside-voice.sh`**
  （`grep -n "outside-voice-job.py" sdflow-init/assets/hack/outside-voice.sh` 只有 3 处注释提及，零调用）。

⇒ 信号就在 dispatch 进程自己的环境里，**最便宜的锚在 helper dispatch，不在 SKILL**。
不做的话，将来关 T162 时唯一的决胜门仍要靠 `--host` 自报 —— **正是本 change 要消灭的东西**。

### 4.2 实现（四处，全链）

| 位置 | 改动 |
|---|---|
| `outside-voice-job.py`（新增 `detect_host()` + `HOST_CLAUDE/CODEX/UNKNOWN`） | 与 `resolve-models.sh` 第 1 段**逐条同口径**：正信号判定；两信号同现 = 冲突落 `unknown`；缺失 **MUST NOT** 推断成另一方；`CLAUDECODE` 严格判 `"1"` |
| `cmd_dispatch` 的 job metadata | `+ "host": detect_host()` |
| `JOB_REQUIRED_FIELDS` | `+ "host"` —— 旧格式 job.json 缺它即 **CORRUPT**，MUST NOT 猜一个出来 |
| `derive_status` 的 base | `+ "host": job["host"]` ⇒ 经 `build_collect_payload` 原样透传进 `<site>.collected.json` |
| `check_codex_efficacy_evidence.py` | **删掉 `--host` 入参**（连接口都不留后门）；`emit` 从 witness 搬 `host`；各站点不一致 ⇒ 顶层落 `MIXED_HOST`；旧 witness 无该字段 ⇒ `None` ⇒ 判红（**fail-closed，MUST NOT 回落自报**） |

### 4.3 blast radius —— 先 grep 后动，实测**零回归**

- `JOB_REQUIRED_FIELDS` 的消费者：`load_job` 一处（缺字段 → CORRUPT）。
- 造 job.json 的测试夹具：**只有 `_seed_site` 一处**（`sdflow-init/tests/test_outside_voice_job.py`）。
- **没有任何既有用例断言 job.json / collect payload 的「精确 key 集」**
  （`grep "set(payload)\|== set(\|COLLECT_KEYS"` 零命中）⇒ 加字段不破既有断言。
- delta spec `OVBG-02` 的措辞是「`job.json` **MUST 至少记录** …」——**至少**，加字段合规，**未改任何 spec**。
- **是否 bump `SCHEMA_VERSION`：不 bump。** 该 schema 属本 change 的新增面、**从未发布过**，
  没有在飞的旧 job.json 需要迁移；bump 只会白白让 Task 1/2 的 golden 全体改期望值（④）。

**实测**（改完 helper + 只动夹具那 1 行，**尚未加任何新用例**时）：

```
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice_job.py -q
317 passed in 99.69s
```

⇒ **既有 golden 一条都没回归**，改动面 = 生产代码 4 处 + 夹具 2 行（签名 + payload）。远低于
「牵动 >5 个既有用例期望值」的降级线 ⇒ 按基准 1（机械化优先）+ 通则③（不缩水）**做掉，不降级**。

### 4.4 新增锚

`sdflow-init/tests/test_outside_voice_job.py`（+3 个用例 / 10 个参数化实例）：

- `test_dispatch_records_the_host_it_actually_runs_in[6 例]` —— `CLAUDECODE=1`→claude ·
  `CODEX_THREAD_ID`→codex · **两者同现**→unknown · 都没有→unknown · `CLAUDECODE=0`→unknown ·
  `CODEX_THREAD_ID=""`→unknown。
  ⚠️ 配套 `_host_env()` **先把继承来的宿主信号清干净再注入** —— 否则在 Claude Code 里跑 pytest 时
  `CLAUDECODE=1` 会从 `os.environ` 漏进去，测试结果随「谁在跑 pytest」而变。
- `test_job_metadata_without_host_is_corrupt_not_guessed` —— 旧格式 job.json ⇒ `(CORRUPT, exec-error)`。
- `test_collect_carries_the_dispatch_host_verbatim[codex|claude|unknown]` —— collect 出参与
  `collected.json` witness 双查，原样透传不美化。

`hack/tests/test_codex_efficacy_evidence.py`（+5 个用例）：
`test_emit_has_no_host_parameter_at_all`（签名 + CLI 双查）·
`test_emit_takes_host_from_the_witness` ·
`test_emit_cannot_upgrade_a_non_codex_witness[claude|unknown]` ·
`test_emit_leaves_host_none_when_the_witness_predates_the_field` ·
`test_emit_marks_a_mixed_host_layer_and_the_gate_reds`。

### 4.5 反向变异（实跑）

```
=== M-I3a: emit 重新引入 --host 自报覆盖 ===
FAILED …::test_emit_has_no_host_parameter_at_all
FAILED …::test_emit_cannot_upgrade_a_non_codex_witness[claude]
FAILED …::test_emit_cannot_upgrade_a_non_codex_witness[unknown]
FAILED …::test_emit_leaves_host_none_when_the_witness_predates_the_field
FAILED …::test_emit_marks_a_mixed_host_layer_and_the_gate_reds
5 failed, 73 passed

=== M-I3b: detect_host 恒返回 codex（自报形态）===
5 failed, 30 passed      （6 例中 5 例红；[codex] 那例本就期望 codex，变异与真值同值，无从区分）
=== M-I3c: 缺失即推断成 claude（负信号推断）===
4 failed, 31 passed
=== M-I3d: host 移出 JOB_REQUIRED_FIELDS ===
FAILED …::test_job_metadata_without_host_is_corrupt_not_guessed        1 failed, 34 passed
=== M-I3e: derive_status 不透传 host（collect 侧断链）===
FAILED …::test_collect_carries_the_dispatch_host_verbatim[codex|claude|unknown]   3 failed, 32 passed
=== M-I3f: dispatch 不落 host 字段 ===
9 failed, 26 passed      （含 3 条端到端 dispatch→collect 用例连带红）
```

### 4.6 连带处理：`task6-transport-probe-evidence.json` 已按新口径重新 emit

旧文件的 `host: "claude"` 是**上轮用 `--host claude` 自报**写进去的 —— 而 `--host` 现已不存在，
**该文件已无法由发布出去的 emitter 复现**。∴ 用新 emitter 从**同一份真实 witness** 重新生成：

```
$ python3 hack/check_codex_efficacy_evidence.py emit \
    --run-dir <zhws_ops_api archive>/.outside-voice/20260725T170004Z-szMlwM \
    --layer spec-review --repo zhws_ops_api \
    --change 2026-07-25-manage-permission-catalog-items \
    --declared-sites design-voice --out <…>/task6-transport-probe-evidence.json
[efficacy] 已写出证据 …（1 站点）                                          exit=0

$ python3 hack/check_codex_efficacy_evidence.py check --evidence <…>
[efficacy] ❌ 未通过（2 条）：
   · host=None ≠ 'codex' —— 本证据只对 Codex 宿主有意义
   · site[design-voice].host=None ≠ 'codex' —— G1 要求该层每个站点都是可信跨模型成功
   ⇒ tasks.md 6.3：保留 T162 并如实记录，MUST NOT 以编排 smoke 假绿
exit=1
```

**`host` 从 `"claude"` 变成 `null`，是对的、不是丢信息**：那份 witness 由**改动前**的 helper 产出，
盘面上**根本没有 `host` 字段**（实查 32 个 key，无 `host`）⇒ **盘面派生的诚实答案就是「无锚」**。
「这次探针跑在 Claude 宿主里」这个事实的权威在上轮报告 §3（`ps` 实抓 + dispatch 出参），
不在这份机器判定用的 JSON 里。两种形态**都判红**，本票结论不变。

### 4.7 诚实边界现在剩下什么（收窄了，但没消失）

| 项 | 状态 |
|---|---|
| `host` | ✅ **已机械化**（dispatch 读宿主信号 → job.json → collect → witness → 证据），无自报入口 |
| `declared_sites` | ❌ **仍是必填入参，仍是真诚实边界**。它是「这一层**应该**有哪些锚」，权威在评审报告锚行；run-dir 只知道「实际 dispatch 了哪些」——拿实落集当 declared 集会让「漏收站点」自动自洽，正是 HAE-09 要杀的。**MUST NOT 声称它有机械捕获路径。** |

### 4.8 ⚠️ 运行时生效条件（不静默）

`sdflow-init/assets/hack/outside-voice-job.py` 由 `setup.sh` **拷贝**（非 symlink）进 `~/.sdflow/hack/`。
本轮**没有**在开发 checkout 重跑 `setup.sh` —— 上轮 §8.2 刚把全局链还原回运行 checkout，
再接管一次会把还原白做。⇒ **新的 `host` 锚要等本 change 合并、运行 checkout 重跑 `setup.sh` 后才在真机生效**，
与上轮结论一致。本轮所有实测都在仓内源上跑（测试夹具直接指向 `assets/hack/`）。

---

## 5. Minor（一并 fold）

### 5.1 `duration <= 0` 与 `schema_version` 两条门无锚

- **`duration`**：`test_g3_rejects_bad_duration_types[0]` 的裸 `assert CE.verify(ev)` 是**被无关门满足**的
  —— 把 `duration <= 0` 改成 `< 0` 后，`0` 会掉进「与时刻不自洽」那条分支，照样红，断言照样绿。
  **修法**：拆成两条定向断言 ——
  `test_g3_rejects_non_numeric_duration`（`"440"` / `None` / `True` / `[440]` → `"MUST 为数字"`）与
  `test_g3_rejects_non_positive_duration`（`0` / `-1` / `-440.0` → **`"MUST > 0"`**）。
- **`schema_version`**：新增 `test_schema_version_drift_is_rejected`（sites 保持合法，只漂顶层）。

```
=== M-Min1: duration <= 0  ->  < 0 ===          1 failed, 77 passed
=== M-Min2: schema_version 门 -> if False ===    1 failed, 77 passed
```

### 5.2 成功摘要的 `crossed` 谓词比 G2 松

`main()` 的摘要行只看 `duration_seconds > 300`，会把 `model="sonnet"` 的站点列进
「自然 >300s 的站点」。**摘要行是人会直接引用的证据句，松了就是把结论说宽。**

**修法**：把 `verify()` 内的闭包 `_crossed` 提到模块级 `crossed_ceiling(site)`，
G2 判定与摘要行**共用这一个谓词**（单一源）。
新增 `test_cli_success_summary_lists_only_sites_that_really_crossed`：opus 站点 440s（真跨）+
sonnet 站点 400s（>300 但非强模型）⇒ 摘要 MUST 只列前者。

```
=== M-Min3: 摘要 crossed 退回只看 duration ===    1 failed, 77 passed
```

---

## 6. 不修项 —— 全部原样保持（已裁定，未顺手做）

| 项 | 本轮动作 |
|---|---|
| 第 2 条（>300s）自我否定判 **❌** | **保持 ❌**。6.2 主语是「该完整层」，锚在 6.1 的 Codex 宿主层；436s 站点 `host` 不属该层。判 ✅ 就是把 transport 证据当 efficacy 证据（6.3 明禁） |
| 第 3 条判 **⚠️** 而非 ✅ | 上轮 §五 G3 栏的标注与之一致（机制已交付，被判对象是 probe 不是 efficacy 证据），**结论未改**；粒度差异不构成改动理由 |
| `layer="spec-review"` 不加 `evidence_kind` | **未加**（④：`host≠codex` 已把门关死，多一个字段多一处口径要守） |
| T162 保留 · `design.md` / `openspec/CONTEXT.md` / hand-off / `openspec/issues/todolist/` | **一字未改**，`git status` 亲验（§7.2） |
| `proposal.md` / `design.md` / `specs/` / `tasks.md` / `openspec/specs/` | **零改动** |
| 复选框 / `task6-` 完成标签 | **未勾 / 未打** |

---

## 7. 门禁全量输出（**均在 `git add -A` 之后跑**）

### 7.1 命令与实际输出

```
$ git add -A && /usr/bin/python3 -m pytest -q
2584 passed, 11 skipped, 3 xfailed in 262.63s (0:04:22)          ← 零 failed

        修前基线（同样 git add -A 后）：1 failed, 2556 passed
        差额 +28 passed = 本轮新增用例（checker 60→78 共 +18；job helper +10）

$ /usr/bin/python3 -m pytest hack/tests/test_codex_efficacy_evidence.py -q
78 passed in 0.24s

$ /usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice_job.py -q
317 passed in 99.69s                                     ← I3 改动后、加新用例前的零回归基线

$ python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致                exit=0

$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 18 个投放面全部与真相源一致                          exit=0

$ git diff --check ; git diff --cached --check
（均无输出）                                                            exit=0 / exit=0

$ openspec validate enable-codex-background-outside-voice --strict
Change 'enable-codex-background-outside-voice' is valid                  exit=0
```

### 7.2 ⚠️ skip 数 10 → 11：**已查证，与本轮改动无关**

上轮 10 skipped、本轮 11 skipped。**不是回归**，是两条**自述环境敏感**的用例之一本轮没复现出前提：

- `test_outside_voice_child_lifecycle.py:436`（高频混合信号风暴复现率环境敏感）
- `test_outside_voice_utf8.py:822`（磁盘写满场景，本环境撞见 coreutils 自己的满盘诊断）

**实测证明其非确定性**（同一棵工作树连跑三轮）：

```
--- run 1 ---  75 passed, 2 skipped
--- run 2 ---  76 passed, 1 skipped
--- run 3 ---  76 passed, 1 skipped
```

两者都与 `host` / `job.json` / 检查器无任何交集；两条用例的 docstring 均明写
「MUST NOT 因为常 skip 就删掉它」。xfail 数 3 一条未变。

### 7.3 工作树（`git status --porcelain`，全部已 staged）

```
M  hack/check_codex_efficacy_evidence.py
M  hack/tests/test_codex_efficacy_evidence.py
A  openspec/changes/…/impl-reports/task6-real-efficacy-fix1.md         ← 本文件
M  openspec/changes/…/impl-reports/task6-real-efficacy.md              ← 仅 Critical 那 1 行
A  openspec/changes/…/impl-reports/task6-review-package.diff           ← 仅 scrub 1 行（§1.4）
M  openspec/changes/…/impl-reports/task6-transport-probe-evidence.json ← 按新 emitter 重生成（§4.6）
M  sdflow-init/assets/hack/outside-voice-job.py
M  sdflow-init/tests/test_outside_voice_job.py
```

> 上面这 8 项就是本轮全部改动 —— 含本报告在内，`git add -A` 后的全量实测即
> **2584 passed, 11 skipped, 3 xfailed，零 failed**（§7.1 的数字与本状态同一次观测口径）。

`git diff --cached --stat` 亲验：四件套（proposal / design / specs / tasks）**零改动**。

---

## 8. 反向变异的执行纪律

全部变异跑在 scratchpad 的**唯一命名副本** `…/scratchpad/mut-task6-fix1/`（`rsync` 全仓 + 独立
`git init` 作还原基线，每条变异后 `git checkout -- .` 复位）。**仓内 MUST NOT 留变异** ——
本仓工作树的 7 个文件即 §7.3 全部内容，`git diff --cached --stat` 逐个核对过，无任何变异残留。

---

## 9. 未做 / 仍降级项（如实报告）

1. **【最要害】Codex 宿主完整一层评审：仍未跑成。** 外部账户额度限流至 2026-07-29 10:11，
   本轮未再尝试（上轮已实跑 2 次留 session id，成本纪律「连续两轮不成即停」）。
   ⇒ **G1 ❌ ⇒ 三条门未同时达标 ⇒ T162 保留，efficacy 陈述一字未改。**
2. **HAE-08 的 Codex 宿主分流仍未经真机走通** —— 与上轮同，仍是本 change 最大未验面。
3. **新的 `host` 锚未在真机 Codex 宿主上取过 `host="codex"`** —— 只有 6 例参数化的
   `CODEX_THREAD_ID` 注入证明**判定逻辑**对。真机取值要等额度恢复后那一轮。
4. **`~/.sdflow/hack/` 的新 helper 未安装**（§4.8）—— 有意不装，避免撤销上轮的全局还原。
5. **`declared_sites` 仍是自报入参**（§4.7）—— 这是真诚实边界，不是可修的洞。
6. **`task6-review-package.diff` 是 scrub 过的快照、不是重新生成的**（§1.4）—— 已交编排层知悉。

---

## 10. Concerns（交给轮 2 双轴审）

1. **`host="unknown"` 的语义**：判不出宿主时落 `unknown` 而非报错。理由 = dispatch 不该因为
   「宿主判不出」就拒绝派发（那会把一条本来能跑的 voice 打死），而 efficacy 门里
   `unknown ≠ codex` 天然 fail-closed。**若评审认为 dispatch 应对 unknown 直接 fail-loud，
   我判不该**——那是拿一个只有 efficacy 门在意的量去卡整条 transport（④）。
2. **`MIXED_HOST = "mixed"` 是个哨兵串**：它落在 `host` 字段里，与真实宿主名同域。
   目前靠 `REQUIRED_HOST == "codex"` 把它挡死，且 `detect_host` 永不产出 `"mixed"`
   （只产 claude/codex/unknown）⇒ 无碰撞面。登记为已知形态。
3. **`detect_host` 与 `resolve-models.sh` 是同口径的两份实现**（Python 一份、sh 一份）。
   没做成单一源：跨语言且各自只有 6 行，抽公共层的成本远高于漂移风险（④）。
   两边的判据都写在注释里互指。**若评审要求机械守住等价，可加一条比对测试** —— 我判暂不加。
