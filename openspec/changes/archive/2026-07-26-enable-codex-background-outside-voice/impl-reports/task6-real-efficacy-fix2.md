# Task 6 fix2 —— 双轴审轮 2（Spec PASS / Standards FAIL）的修复报告

**前两轮报告**：`task6-real-efficacy.md`（轮 1）· `task6-real-efficacy-fix1.md`（fix1）——**均未覆盖**；
本轮只在轮 1 报告里就地补了 3 处「已被 fix1 推翻」的批注（§3，属本轮 F5 的 grep 连坐项）。
**起手 HEAD**：`a9ad091`
**范围**：Important ×3（F4 面治 · parity 门 · F5 陈旧 runbook）· Minor ×2 · 已裁定不修项 ×6（原样保持）

---

## 0. 结论先行

| 项 | 状态 |
|---|---|
| **F4 · G1 三元组 `runner` 维完全无锚** | ✅ 已修（needle 改定向串），三维各自反向变异**独立会红** |
| **面治：恒真锚在本 change 第三次出现** | ✅ **38 条门全量定点删门变异**，修前 **8 条无独立锚**、修后 **0 条**（§1 全表） |
| **`detect_host` ↔ `resolve-models.sh` 跨语言 parity 门** | ✅ 已做（6 例 env 双跑比对）；**实测两边语义完全一致，未发现真 bug**；两侧各 3 条变异**全红** |
| **F5 · 关 T162 的 runbook 已被本 change 改废** | ✅ 已修，并按 grep 连带处理 §4.3 / §八.4 两处同族陈旧断言 |
| Minor · `task6-review-package.diff` 与自称范围不符 | ✅ 已在文件头注明「有意回改」 |
| Minor · `any("host" in f)` needle 过宽（464/475） | ✅ 已收紧成顶层门 + site 级门**各自**断言 |
| 不修项（第 2 条 ❌ / 第 3 条 ⚠️ / 不加 `evidence_kind` / T162 / `design.md` / 跨代 CORRUPT / env 可伪造） | ✅ 全部原样保持 |
| **efficacy 三门** | **仍未达标 ⇒ T162 保留，`design.md` / CONTEXT / hand-off 的「efficacy=0」陈述一字未改** |

**本轮同样没有跑 Codex 宿主评审**（额度限流至 2026-07-29 10:11，轮 1 §2.2 两次实录）。
本轮全部工作是**把门本身做扎实 + 把陈旧指令修正**，不是去关门。

---

## 1. 🔴 面治 —— 「恒真锚」全量扫

### 1.1 为什么必须面治，而不是只补 F4

同一根因形态在本 change 已第三次出现（Task 5 主线 5 条 → Task 6 轮 1 自捕 2 条 → 本轮 F4）：

> `assert any(<needle> in f for f in failures)` 的 `<needle>` **被另一个无关门的失败文本满足**
> ⇒ 目标门即使整个删掉，测试照绿。

F4 是这个面上被点穿的**一处**。按 CLAUDE.md 基准 3（面治优先于点补），本轮把
`hack/tests/test_codex_efficacy_evidence.py` 覆盖的**每一条门**都过了一遍。

### 1.2 判定方法（机械的，不是读代码推断）

反向变异台：`<scratchpad>/task6fix2/mutate.py`（**scratchpad 唯一命名副本，仓内零残留**）。
对 `check_codex_efficacy_evidence.py` 的**每一条门**做定点删除（把守卫条件改成 `if False:`、
或从三元组/身份三件的元组里删掉那一项），跑整个测试文件：

- **红** ⇒ 该门有独立锚 ✅
- **绿** ⇒ 该门被删掉测试照过 ⇒ **恒真锚** ❌

变异台每轮跑完**自动还原源文件**（`try/finally`），且起手 `assert ORIG.count(old) == 1`
——锚点不唯一就当场炸，避免「以为删了其实没删」的假红。

### 1.3 「门 × 是否有独立锚」全表（38 条，修前 / 修后）

修前基线 `78 passed`，修后基线 `116 passed`。

| # | 门（`check_codex_efficacy_evidence.py`） | 变异 | 修前 | 修后 |
|---|---|---|---|---|
| 1 | G1 三元组 · `host` | 删 `("host", REQUIRED_HOST)` | 红 ✅ 1 failed | 红 ✅ **4 failed** |
| 2 | **G1 三元组 · `runner`** | 删 `("runner", REQUIRED_RUNNER)` | **绿 ❌ 78 passed** | 红 ✅ **1 failed** |
| 3 | G1 三元组 · `reason_code` | 删 `("reason_code", …)` | 红 ✅ 1 failed | 红 ✅ **4 failed** |
| 4 | site key 白名单（多 key） | `if False:` | 红 ✅ 1 | 红 ✅ 1 |
| 5 | site key 完整性（缺 key） | `if False:` | 红 ✅ 1 | 红 ✅ 1 |
| 6 | **site 名非空字符串** | `if False:` | **绿 ❌** | 红 ✅ **3 failed** |
| 7 | **site 的 `model`/`effort`/`job_id`/`attempt_nonce` 非空** | `if False:` | **绿 ❌** | 红 ✅ **12 failed** |
| 8 | G3 四时刻可解析 | `if False:` | 红 ✅ 5 | 红 ✅ 5 |
| 9 | G3 时刻单调 | `if False:` | 红 ✅ 1 | 红 ✅ 1 |
| 10 | G3 `duration` 是数字 | `if False:` | 红 ✅ 4 | 红 ✅ 4 |
| 11 | G3 `duration > 0` | `elif False:` | 红 ✅ 3 | 红 ✅ 3 |
| 12 | G3 `duration` 与两端时刻自洽 | `if False:` | 红 ✅ 2 | 红 ✅ 2 |
| 13 | G3 `stdout_sha256` 形状 | `if False:` | 红 ✅ 6 | 红 ✅ 6 |
| 14 | G3 计数器是整数 | `if False:` | 红 ✅ 1 | 红 ✅ 1 |
| 15 | G3 计数器下界 | `elif False:` | 红 ✅ 2 | 红 ✅ 2 |
| 16 | 顶层 key 白名单 | `if False:` | 红 ✅ 1 | 红 ✅ 1 |
| 17 | 顶层 key 完整性 | `if False:` | 红 ✅ 1 | 红 ✅ 1 |
| 18 | 字符串无换行（防正文夹带） | `if False:` | 红 ✅ 1 | 红 ✅ 1 |
| 19 | 字符串长度上界 | `elif False:` | 红 ✅ 3 | 红 ✅ 3 |
| 20 | `schema_version` | `if False:` | 红 ✅ 1 | 红 ✅ 1 |
| 21 | 顶层 `host` | `if False:` | 红 ✅ 7 | 红 ✅ **10 failed** |
| 22 | **顶层 `layer` ∈ LAYERS** | `if False:` | **绿 ❌** | 红 ✅ **5 failed** |
| 23 | **顶层 `repo`/`change`/`run_id` 非空** | `if False:` | **绿 ❌** | 红 ✅ **9 failed** |
| 24 | `declared_sites` 是非空字符串列表 | `if False:` | 红 ✅ 1 | 红 ✅ 1 |
| 25 | **`declared_sites` 无重复** | `elif False:` | **绿 ❌** | 红 ✅ **1 failed** |
| 26 | **`sites` 是非空列表** | `if False:` | **绿 ❌** | 红 ✅ **4 failed** |
| 27 | 站点名无重复 | `if False:` | 红 ✅ 1 | 红 ✅ 1 |
| 28 | 身份重复 · `job_id` | 删该项 | 红 ✅ 1 | 红 ✅ 1 |
| 29 | 身份重复 · `attempt_nonce` | 删该项 | 红 ✅ 1 | 红 ✅ 1 |
| 30 | 身份重复 · `stdout_sha256` | 删该项 | 红 ✅ 1 | 红 ✅ 1 |
| 31 | 身份重复检测整体 | `if False:` | 红 ✅ 4 | 红 ✅ 4 |
| 32 | G1 declared 双向集合相等 | `if False:` | 红 ✅ 2 | 红 ✅ 2 |
| 33 | G2 `any(crossed_ceiling)` | `if False:` | 红 ✅ 5 | 红 ✅ 5 |
| 34 | `crossed_ceiling` · `duration > 300` | `and True` | 红 ✅ 2 | 红 ✅ 3 |
| 35 | `crossed_ceiling` · `model` | `and True` | 红 ✅ 2 | 红 ✅ 3 |
| 36 | `crossed_ceiling` · `effort` | `and True` | 红 ✅ 1 | 红 ✅ 2 |
| 37 | `crossed_ceiling` · `reason_code` | `and True` | 红 ✅ 1 | 红 ✅ 2 |
| 38 | **`crossed_ceiling` · `runner`** | `and True` | **绿 ❌ 78 passed** | 红 ✅ **1 failed** |

**修前 8 条无独立锚 → 修后 0 条。** 变异台末尾的汇总行（实跑输出）：

```
（修前）=== 无独立锚（变异后仍全绿）===
  · G1.runner
  · site.name_nonempty
  · site.str_fields
  · top.layer
  · top.str_fields
  · declared.dupes
  · sites.nonempty
  · cc.runner

（修后）=== 无独立锚（变异后仍全绿）===
  （无）
```

### 1.4 面治的收获：**恒真锚有两种成因，评审只报了一种**

评审报的是「needle 被别的门的文本满足」（#2 G1.runner、#26 sites.nonempty、#38 cc.runner）。
面治扫出**另一种**：#6 / #7 / #22 / #23 / #25 —— **压根没有用例走到那一行**。
两者症状完全相同（定点删门照绿），但修法不同：前者收紧 needle，后者补用例。
**只按评审的描述去找「过宽的 needle」会漏掉一半。**

### 1.5 逐条修法

**#2 F4 · G1 三元组 —— 根因与修法**

`verify` 里 G2 未达标的消息把要求**逐条列了出来**：

```
G2 未达标：没有任何站点满足「自然 duration > 300.0s ∧ model=opus ∧ effort=high
∧ runner=claude ∧ reason_code=ok」……
```

⇒ 参数化的 5 个 case 里，`runner` / `reason_code`（3 例）的裸 needle 全被这句顶替，
5 例中 4 例恒真。修法：needle 改成 G1 那一行**独有**的定向串 + 字段前缀：

```python
G1_TRIPLE_MSG = "G1 要求该层每个站点都是可信跨模型成功"

def _g1_hit(fails, field):
    return any(G1_TRIPLE_MSG in f and f".{field}=" in f for f in fails)
```

`test_g1_rejects_when_one_of_two_sites_degraded` 一并收紧到 `_g1_hit(fails, "reason_code")`。

**后果不是纯测试问题**（评审原话，已复核成立）：多站点层里混一个 `runner="codex"`
（同族 fallback，**正是本 change 要消灭的形态**）只要另有站点跨 300s，G1 那一维形同虚设。

**#38 `crossed_ceiling.runner` —— 为什么它经 `verify` 打不到**

`runner ≠ claude` 会先被 G1 三元组红掉，整层无论如何不绿 ⇒ 经 `verify` 的断言无法区分。
而 `crossed_ceiling` **还被 CLI 成功摘要行单独消费**（那句是人会直接引用的证据句，
fix1 刚把它收敛成单一谓词）⇒ 新增 `test_crossed_ceiling_requires_every_conjunct`
**直接打谓词、不经 `verify`**，5 个合取项逐个验。

**#6 / #7 / #22 / #23 / #25 / #26** —— 分别补 `test_a_site_without_a_usable_name_is_rejected`、
`test_site_identity_strings_must_be_non_empty`、`test_layer_outside_the_declared_set_is_rejected`、
`test_top_level_identity_fields_must_be_non_empty_strings`（用**全等**而非子串，最强定向）、
`test_duplicate_declared_sites_are_rejected`、以及把 `test_empty_sites_is_not_green`
从裸 `assert CE.verify(ev)` 收紧成定向 needle + 参数化 4 种非法形态。

新增用例的**底座都刻意保持合法**（如 declared 重复那条，站点集恰好等于去重后的 declared），
让失败原因只能出自目标门 —— 这正是修前那 8 条踩的坑。

---

## 2. 🔴 Important · `detect_host` ↔ `resolve-models.sh` 跨语言 parity 门

### 2.1 接受评审的成本反驳（我上轮的否决论证针对的是更贵的方案）

上轮我以「抽公共层成本过高」否掉。评审指出成本论证错位：**不需要抽公共层**，
`test_resolve_models.py` 已有 `run_resolve()`（真跑 shell 取 `SDFLOW_HOST`）+ `parse_exports()` +
`make_bundle_repo()`，`test_outside_voice_job.py` 已有同一张 6 例真值表 ⇒ 双跑比对约 15 行。

这正是 CLAUDE.md 基准 5「**让工具自己回答**」：**MUST NOT 手搓「等价性证明」**
（那等于用一份解析器去猜另一个语言的语义），而是同一组 env 让两边各跑一遍、比结果。
**评审对、我上轮错，已改。**

### 2.2 落点

`sdflow-init/tests/test_resolve_models.py` 新增 `TestHostDetectionParityAcrossLanguages`
（+ 顶部用 `importlib` 载入 `outside-voice-job.py` 取 `detect_host`）。6 例 env：
正信号 ×2 · 冲突 ×1 · 缺失 ×1 · `CLAUDECODE=0` ×1 · `CODEX_THREAD_ID=""` ×1。

### 2.3 **实测结论：两边语义完全一致，未发现真 bug**

```
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_resolve_models.py -q -k Parity
......                                                     6 passed, 25 deselected in 0.17s
```

6 组 env 上 `resolve-models.sh` 的 `SDFLOW_HOST` 与 `detect_host()` 的返回值**逐例相等**。
∴ **不存在需上抛的语义分歧**；本门是**防将来漂移**的，不是修当下的洞。

### 2.4 反向变异：**两侧各 3 条，全红**（scratchpad 镜像树，仓内零变异）

```
P-a: Python 侧「缺失即推断成 claude」        红 ✅  3 failed, 3 passed
P-b: Python 侧冲突时静默取 claude          红 ✅  1 failed, 5 passed
P-c: Python 侧 CLAUDECODE 放宽成真值转换     红 ✅  1 failed, 5 passed
P-d: shell 侧冲突时静默取 codex            红 ✅  1 failed, 5 passed
P-e: shell 侧 CLAUDECODE 放宽成非空即真      红 ✅  1 failed, 5 passed
P-f: shell 侧缺失即推断成 codex            红 ✅  3 failed, 3 passed
```

**两个方向都锚住**了 —— 只改 Python 侧会红、只改 shell 侧也会红（单向变异会漏掉
「大家一起改错」以外的所有真实漂移场景，而漂移的定义就是单侧动）。

---

## 3. 🔴 Important F5 · 关 T162 的 runbook 已被本 change 自己改废

### 3.1 复现（修前）

`task6-real-efficacy.md:309`（轮 1 报告「重开条件（可机械复核）」）：

> 重跑 §2.2 的 `codex exec` 起一轮 spec-review，用 §4 的 `emit --host codex` + `check` 判定即可关门。

而 `--host` 在 fix1 已删（`host` 改盘面派生）。实跑核验：

```
$ python3 hack/check_codex_efficacy_evidence.py emit --run-dir /tmp --host codex \
    --layer spec-review --repo r --change c --declared-sites s --out /tmp/e.json
usage: check_codex_efficacy_evidence.py [-h] {check,emit} ...
check_codex_efficacy_evidence.py: error: unrecognized arguments: --host codex
exit=2
```

**性质**：与「改共享字符串漏了消费者」同族，且落在**本 change 留给未来的唯一关门指令**上
——将来那个关 T162 的人照着跑会直接撞墙。评审判 Important，成立。

### 3.2 修法

删掉 `--host codex`，并把「为什么没有这个参数」就地写清（指向 fix1 §4.5–4.6）。

### 3.3 grep 连坐 —— **同一份报告里还有两处**

按要求 `grep -rn -- "--host"` 全仓过了一遍。命中分三类：

| 位置 | 判定 |
|---|---|
| `openspec/specs/lens-metric-emit/` + `archive/2026-07-16-add-codex-host-support/*`（20 处） | **另一个工具** `lens_metric_emit.py` 的 `--host`，**至今仍存在**，与本 change 无关 ⇒ **不动** |
| `task6-real-efficacy.md:235 / 249`（§4.2 命令实录 + 紧随的解读） | **轮 1 实跑实录**，当时确实这么跑的 ⇒ **保留正确，未动**（依评审指示） |
| `task6-real-efficacy.md:309` | F5 本体 ⇒ **已修** |
| **`task6-real-efficacy.md` §4.3（253-256）** | 标题即「诚实边界：`host` **不是**盘面可派生量」，正文断言「`emit` 的 `--host` 是必填入参」「MUST NOT 声称这两项有机械捕获路径」——**fix1 已把 host 做成盘面派生**，此结论**已被推翻** ⇒ **补批注** |
| **`task6-real-efficacy.md` §八.4（459-461）** | 「`--host` 由调用者自报：这是真诚实边界，**不是可修的洞**」——同上，且这句判断**本身是错的**（洞可修、fix1 已修）⇒ **划删 + 批注** |

**为什么是「批注」而不是「改写」**：轮 1 报告是**那一轮的实录**（fix1 也遵此约定，未覆盖它），
直接改写会伪造历史；但留一条**未标记的错误规范性断言**正是 F5 的失效模式本身。
∴ 保留原文 + 顶上一条 🔴 supersede 批注指向 fix1 —— 读者拿到的是「轮 1 这么认为、后来被推翻」，
两个事实都不丢（DOC-1「只有读过上一版的人才需要的句子不属于正文」在这里不适用：
impl-report 是分轮实录，不是最终态设计文档）。

---

## 4. Minor（一并 fold）

### 4.1 `task6-review-package.diff` 与自称范围不符

fix1 §1.4 把该文件里 1 行 legacy 池名就地 scrub 掉了（守卫在 tracked 集上会红），
∴ 它不再是 `6dc9919..3c7ff5e` 的逐字节输出。已在**文件头**加 4 行说明：
「这是有意的回改，不是 diff 生成有误；要权威 diff 请直接跑 git」。
（放文件头而非行内：`git apply` 会跳过首个 `diff --git` 之前的前言，不破坏该文件的可读性。）

### 4.2 `any("host" in f)` needle 过宽（464 / 475）

`test_emit_cannot_upgrade_a_non_codex_witness` / `test_emit_leaves_host_none_when_the_witness_predates_the_field`
里，顶层 host 门与 site 级 host 门**互相顶替**。已收紧成两条独立断言
（顶层用 `"本证据只对 Codex 宿主有意义"`、site 级用 `_g1_hit(fails, "host")`）。
效果见 §1.3：#21 顶层 host 变异从 `7 failed` → `10 failed`，#1 site host 从 `1` → `4`。

---

## 5. 已裁定不修项（**原样保持，本轮一处未动**）

| 项 | 处置 |
|---|---|
| 轮 1 §八.2 判 ❌（`MAX_STRING_LEN=256` 是拍的） | 维持 |
| 轮 1 §八.3 判 ⚠️（检查器不接进 `setup.sh` 三门） | 维持 |
| 不加 `evidence_kind` 枚举 | 维持 |
| **T162 保留** | 维持 —— efficacy 三门仍未达标 |
| **`design.md` / `openspec/CONTEXT.md` / hand-off 的「efficacy=0」陈述** | **一字未改**（`git status` 亲验：本轮 4 个 M，无一是这些文件） |
| 跨代 `job.json` 变 CORRUPT | 维持不改（fail-closed + capability-manifest skew 已先一步拦住混配） |
| `detect_host` 的 env 仍可被同一执行者伪造 | 维持不改（fix1 §9.3 已如实登记「新 host 锚未在真机取过 codex 值」，无过度声称） |

---

## 6. 全部门禁命令的实际输出

```
$ git add -A && git status --short
M  hack/tests/test_codex_efficacy_evidence.py
M  openspec/changes/enable-codex-background-outside-voice/impl-reports/task6-real-efficacy.md
M  openspec/changes/enable-codex-background-outside-voice/impl-reports/task6-review-package.diff
M  sdflow-init/tests/test_resolve_models.py

$ /usr/bin/python3 -m pytest -q
2629 passed, 10 skipped, 3 xfailed in 262.17s (0:04:22)

$ python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致                    exit=0

$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 18 个投放面全部与真相源一致                            exit=0

$ git diff --check && git diff --cached --check
                                                                          exit=0

$ openspec validate enable-codex-background-outside-voice --strict
Change 'enable-codex-background-outside-voice' is valid                    exit=0

$ git diff --cached --stat
 hack/tests/test_codex_efficacy_evidence.py         | 115 +++++++++++++++++++--
 .../impl-reports/task6-real-efficacy.md            |  19 +++-
 .../impl-reports/task6-review-package.diff         |   5 +
 sdflow-init/tests/test_resolve_models.py           |  44 ++++++++
 4 files changed, 169 insertions(+), 14 deletions(-)
```

### 6.1 全量数字对账（**如实报告，不掩盖偏差**）

编排层给的基线是 `2585 passed, 10 skipped, 3 xfailed`。本轮新增用例 **44 条**
（efficacy 测试 78 → 116，即 +38；parity 门 +6）⇒ 期望 `2629 passed`，**实测正好 2629**。

⚠️ 我跑了**两次**全量，两次 skipped 数不同（第一次 `2628 passed, 11 skipped`、
第二次 `2629 passed, 10 skipped`）。差异是同一条用例：
`sdflow-init/tests/test_outside_voice_child_lifecycle.py:436` —— 其 skip 理由自述
「15 次高频混合信号风暴本轮一次都没复现（复现率环境敏感）」，是**已登记的环境敏感抖动**
（其 docstring 明写「MUST NOT 因为本用例经常 skip 就删除它」）。**与本轮改动无关**
（本轮未触碰该文件；两次运行的 passed+skipped 合计恒为 2639）。

### 6.2 被改的两个测试文件单独跑

```
$ /usr/bin/python3 -m pytest hack/tests/test_codex_efficacy_evidence.py \
      sdflow-init/tests/test_resolve_models.py -q -rs
147 passed in 2.41s          （116 + 31，无 skip）
```

### 6.3 契约自查

- **未勾任何复选框、未打 `task<N>-` 完成标签**（`git status` 只有 4 个 M，`superpowers-plan.md` 未动）。
- **未改** `proposal.md` / `design.md` / `specs/` / `tasks.md` / `openspec/specs/`（`git diff --cached --name-only` 亲验，零命中）。
- **未在任何文件写 legacy 池名字面串**（grep 两个名字，零命中）。
- **变异全部在 scratchpad 唯一命名目录**（`<scratchpad>/task6fix2/`，含 `mutate.py` + `parity/` 镜像树），
  变异台 `try/finally` 还原 + 仓内 `git status` 干净，**仓内零残留变异**。

---

## 7. 未修项与理由

1. **efficacy 三门仍未达标** —— 需在**真 Codex 宿主**跑一轮真实评审，账户额度限流至
   2026-07-29 10:11。**这不是可以靠改代码关掉的门**，T162 按设计保留。
2. **`declared_sites` 仍是必填入参（诚实边界）** —— 与 fix1 一致：它是「本层**应该**有哪些锚」，
   run-dir 只知道「实际 dispatch 了哪些」，拿实落集当 declared 集会让「漏收站点」自动自洽
   （HAE-09 要杀的正是这个）。**无机械捕获路径，MUST NOT 声称有。**
3. **parity 门只覆盖宿主判定这一段** —— `resolve-models.sh` 的档位解析没有 Python 对应实现，
   不存在第二份可比对物 ⇒ 无 parity 面可守（不是漏做）。
4. **`test_outside_voice_child_lifecycle.py:436` 的环境敏感 skip** —— 已登记的既有残余
   （design.md D2.2），本轮未触碰，按其 docstring 的明确要求 **MUST NOT 因常 skip 就删**。
