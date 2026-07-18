# Task 5：零改动核验、实证 smoke 与收尾记账

> **本票的价值全在证据。** 下列每条验收标准，要么给命令 + 实际输出，要么如实写「未达成 + 原因 + 缺什么」。
> 无实跑证据者一律不打勾。

- **分支**：`feat/async-outside-voice`
- **change 起点**：`e5102ba`（plan checkpoint）
- **执行时间**：2026-07-18（UTC 10:37–10:55）
- **宿主**：Claude Code（`host=claude`），voice runner = `codex`（跨模型）
- **run-id**：`20260718T103718Z-JZRIJ1`

---

## 逐条判定总表（9 条验收标准）

| # | 验收标准 | 判定 | 证据位置 |
|---|---|---|---|
| 1 | 核 outside-voice 脚本 / 合法组合矩阵 / 出境安全三件套零改动（diff 为空） | ✅ **达成** | §1（sha256 相同 + 逐符号 IDENTICAL + secret_scan 真触发） |
| 2 | 锚契约全笛卡尔回归与 change 前逐条一致 | ✅ **达成** | §2（既有 42 passed + 2125 组直接对拍 sha 相同） |
| 3 | 真实评审 smoke：voice 锚 reason_code = ok，非 timeout | ⚠️ **部分达成** | §3（envelope `>>>0` 属实；但 voice 实测 262s < 300s 同步窗口 ⇒ **从未进入 R1 Scenario 1 的 WHEN**，async 唯一要救的场景未被证。见 fix1 §3） |
| 4 | 每站点派发/终态通知/落锚三时刻单调 | ⚠️ **部分达成** | §4（单调属实；但 collect 发生在终态后 63s，**barrier 从未处于 RUNNING 等待态** ⇒「未早退」只是没机会早退。见 fix1 §4） |
| 5 | fan-out 墙钟 vs voice 完成时刻，校准「重叠非叠加」 | ⚠️ **部分达成** | §5（实测的是**两条 voice 互相重叠**，非验收标准原文的「**fan-out 墙钟** vs voice 完成时刻」；§9.5 自陈未跑任何 fan-out 编排 ⇒ 换了被测对象。见 fix1 §5） |
| 6 | 降级 smoke：回落同步 + 标注 + 外层 ≥330000ms + voice 正常完成 | ✅ **达成** | §6（实测 181s > 默认 120s，证明该断言非形式主义） |
| 7 | 错误路径：collect 只取结构化状态，不采信后台文件原始 stderr | ✅ **达成** | §7（exit 1/2/3 实跑 + 14 组 envelope 对抗用例） |
| 8 | harness 后台输出文件 TTL/权限/清理归属已实测记录，未定项显式登记 | ⚠️ **部分达成** | §9.4（落点/权限/持久性已实测；**TTL 与清理归属无法判定，显式登记为未定**） |
| 9 | Codex efficacy=0 与 DRY 全抽取两项记入待办池 | ✅ **达成** | §11（T162 / T163，均带 change 字段） |

**另有票内子目标与新发现：**

| 项 | 判定 | 说明 |
|---|---|---|
| 4.1③ 刻意构造 voice 逼近 900s（**真实模型**） | ❌ **未达成** | 模型推理时长无可控注入点，见 §9.1 |
| 4.1③ 后台跨 600000ms 上限存活（**fake runner**） | ✅ **达成** | 660s 跑满、exit 0、ppid 稳定，独立复现既有 spike，见 §9.2b |
| 4.5 exit 124 真超时端到端触发 | ⚠️ **残余** | 映射已由合成用例覆盖，真 124 未跑，见 §9.3 |
| **【新发现】子代理上下文轮次终结致后台任务被回收** | 🟡 **B8（P2，已降级）** | 初记为「主 session 空闲即回收 / P1」；该受控对比**有混淆变量**（子代理里「空闲」与「轮次终结」不可分辨）。编排层主 session 判别实验 **702s 跑满 exit 0** ⇒ 主 session 不复现。见 fix1 §1 |

> ⚠️ **本报告已被 `task5-verification-smoke-fix1.md` 返修**（双轴审后）。上表 3/4/5 三条由 ✅ 降为
> ⚠️ 部分达成，B8 由 P1 降为 P2。**以 fix1 为准**；本文件保留原始记录供追溯。

> **本票最重要的产出仍是 B8**，但**其影响面在返修后收窄**：它是**子代理上下文**的轮次终结回收
> 在飞后台任务，**不是**「主 session 让出轮次即回收」（后者已被 702s 主 session 判别实验证伪）。
> ∴ 它**不冲击** async barrier 的核心机制，只要求 barrier 的执行位焊在主 session（已落地）。
> **它仍是靠「跑不通 → 不含糊过去 → 做对照实验」挖出来的**——但当时的对照**不是单一变量**，
> 这一点由双轴审的 Standards 轴指出、由编排层的判别实验裁决。详见 fix1 §1。

---

## 0. 软链改动记录（全局环境纪律）

**结论：本次 smoke 全程未改动任何全局软链，无需还原。**

动手前记录的指向：

```
$ ls -l ~/.claude/skills/sdflow-spec-review ~/.sdflow/workflow ~/.claude/skills/sdflow-code-review
lrwxr-xr-x  .../sdflow-code-review -> /Users/cheneyzhao/.skills/sdflow-skills/sdflow-code-review
lrwxr-xr-x  .../sdflow-spec-review -> /Users/cheneyzhao/.skills/sdflow-skills/sdflow-spec-review
lrwxr-xr-x  ~/.sdflow/workflow     -> /Users/cheneyzhao/.skills/sdflow-skills/sdflow-init/assets/workflow
```

编排层授权了「临时 `setup.sh` 指向 dev」，但**实测发现该动作对本票不必要**，∴ 未执行：

```
$ shasum -a 256 ~/.sdflow/hack/outside-voice.sh sdflow-init/assets/hack/outside-voice.sh
77c89fd6…3187c8  /Users/cheneyzhao/.sdflow/hack/outside-voice.sh
77c89fd6…3187c8  .../sdflow-init/assets/hack/outside-voice.sh
```

- **helper 本体 dev 与 runtime 字节相同**（本 change 对它零改动）⇒ voice dispatch 的真实跑动无需切 dev。
- **anchor_lint 的 dev 版**直接以仓内路径 `openspec/workflow/tools/anchor_lint.py` 调用即可，无需经全局解析。
- ∴ **全局环境保持原状**；上面 `ls -l` 的三条指向在本票结束时仍然成立（未做任何 `setup.sh`）。

---

## 1. 核 outside-voice 脚本 / 合法组合矩阵 / 出境安全三件套零改动 ✅

**① `outside-voice.sh` 逐字节零改动**

```
$ git log --oneline e5102ba..HEAD -- '*outside-voice.sh' '*outside_voice_guard.py'
(空 —— 无任何 commit 触碰)

$ git show e5102ba:sdflow-init/assets/hack/outside-voice.sh | shasum -a 256
77c89fd62d50f58420cbcbb0ce171bc550964deeb6d722a020d0608e1e3187c8
$ git show HEAD:sdflow-init/assets/hack/outside-voice.sh    | shasum -a 256
77c89fd62d50f58420cbcbb0ce171bc550964deeb6d722a020d0608e1e3187c8
```

`outside_voice_guard.py` 同样字节相同（`cde17e3f…96cc`，pre==post）。
⇒ **四旗承重墙、`secret_scan`、`FRAME`、200KB 截断全部逐字未变。**

**② 合法组合矩阵零改动**（`anchor_lint.py` 本 change 有 +126 行，故须逐符号核，不能只看文件级）

按符号抽取比对 `e5102ba` vs `HEAD`：

| 符号 | anchor_lint | outside_voice_guard |
|---|---|---|
| `check_legal_combo` | **IDENTICAL** | （不存在） |
| `classify_combo` | **IDENTICAL** | **IDENTICAL** |
| `REASON_CODES` | （不存在） | **IDENTICAL** |

`anchor_lint.py` 的 diff hunk 位置为 `@@ -16,6`（锚前缀表 +1 行）、`@@ -494,6 +495`（`check_legal_combo` **之后**新增 `check_declared_sites`）、`@@ -687,6 +811`（`main` 里 +1 行调用）——**纯 additive，矩阵函数体未被任何 hunk 覆盖**。

**③ 出境安全三件套功能性实跑**（不止比字节，真触发一次）

```
$ SDFLOW_VOICE_RUNNER=codex ~/.sdflow/hack/outside-voice.sh exec --timeout 300 --context-file <含 AKIA… 的 context>
secret-hit（拒发）: 规则=aws-akid 行=2
<<<SDFLOW_EXEC_EXIT>>>3
```

⇒ `secret_scan` 真拦住、且 **D8 脱敏成立**（stderr 只出「规则类型 + 行号」，未打印命中原行/匹配值）。

---

## 2. 锚契约全笛卡尔回归与 change 前逐条一致 ✅

既有 golden 套件：

```
$ /usr/bin/python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_outside_voice_guard.py -q
42 passed in 0.23s
```

**另做了一次更强的直接对拍**（不依赖测试是否覆盖全）：把 `e5102ba` 与 `HEAD` 两版工具各自 import，
对 `host×runner×reason_code×findings` 全笛卡尔积（5×5×17×5 = **2125 组**，含越域/空串/`None`/负数 mutation）
逐组跑 `classify_combo`，dump 成 JSON 比对：

```
rows: 2125
cb1548f4…526e7  cart_pre.json
cb1548f4…526e7  cart_post.json
CARTESIAN IDENTICAL pre==post
anchor_lint vs guard agreement: True
class distribution: {'illegal': 1940, 'self-review': 130, 'same-family': 40, 'cross-model': 10, 'no-exec': 5}
```

- **2125 组分类结果 sha256 完全相同** ⇒ 与 change 前逐条一致。
- 两工具（`anchor_lint` / `outside_voice_guard` 各自重实现）**逐组一致**。
- **5 类完整分类全部出现** ⇒ 测试域未退化成只覆盖部分分支（防假绿）。

> 诚实注记：首轮我把 reason_code 域取成了 `REASON_CODES`（reuse-guard 码集），导致 `same-family` / `no-exec`
> 两类 0 出现——**这正是「域退化假绿」本身**。已扩域重跑，上表为修正后结果。

---

## 3. 真实评审 smoke：voice 锚 reason_code = ok ⚠️ 部分达成

> **返修注（fix1）**：下述 `reason_code="ok"` 属实。但本次 voice 实测 **262s < 300s 同步窗口**
> ⇒ **R1 Scenario 1 的 WHEN（voice 时长 > 外层同步窗口）从未被满足**——即 async 唯一要救的场景
> 未被本轮证实。已登记 **T165**。

真实 33KB context（本 change 的 proposal + design 节选），真实 `codex` 跨模型 runner，
经 `run_in_background` 按 SKILL ④ 的逐字命令形态派出：

```
$ SDFLOW_VOICE_RUNNER=codex ~/.sdflow/hack/outside-voice.sh exec --timeout 900 \
    --context-file openspec/changes/async-outside-voice/.outside-voice/20260718T103718Z-JZRIJ1/design-voice-context.md; \
  rc=$?; printf '\n<<<SDFLOW_EXEC_EXIT>>>%s\n' "$rc"
→ Command running in background with ID: boxfeo2jj
```

collect 得到的 envelope：

```
<<<SDFLOW_EXEC_EXIT>>>0
```

⇒ **`reason_code="ok"`，非 timeout**；voice 回传 3 条实质 findings（含对本 change 自身的批评，见 §9）。

**内层超时取值链路实证**：`openspec/config.yaml` 的 `outside-voice.async-timeout-seconds` 键**当前是注释态（缺键）**
⇒ 按协议 ① **回落默认 900**，本次即以字面 `--timeout 900` 派出。

---

## 4. 每站点派发 / 终态通知 / 落锚三时刻单调 ⚠️ 部分达成

> **返修注（fix1）**：单调（`dispatch ≤ terminal ≤ collect`）属实。但下文「barrier 未早退的正向证据」
> **过度解读**：collect 发生在终态**之后 63s**，即 barrier 检查该站点时它**早已终态、从未处于 RUNNING
> 等待态** ⇒「未早退」只是**没有机会早退**，不是「有机会早退而没早退」的实证。⑥ 的正向 barrier 语义
> （RUNNING ⇒ 让出轮次等通知）在本轮**未被执行过一次**。

`dispatch-manifest.tsv`（`/usr/bin/od -c` 验证为**真制表符** `\t`、非字面 `\t`）：

```
design-voice\tboxfeo2jj\t20260718T103810Z\n
design-voice-longrun-fake\tb28kp3z3h\t20260718T104429Z\n
```

`design-voice` 站点三时刻：

| 时刻 | UTC | 相对 |
|---|---|---|
| dispatch（manifest 落盘） | 10:38:10Z | — |
| 终态（后台输出文件 mtime） | 10:42:32Z | +262s |
| collect / 落锚 | 10:43:35Z | 终态后 +63s |

**`dispatch ≤ terminal ≤ collect` = True** ⇒ 单调成立，**落锚不早于终态通知**。

**barrier 未早退的正向证据**：全程**未轮询、未长 sleep**——dispatch 调用 <1s 即返回，
终态由 harness 完成通知推送后才 collect；`reason_code` 取自实测 envelope（0），**未在收到终态前落任何 timeout**。

---

**附带实证：per-run 不可变路径（§3.4）确已生效**——同一 change 目录下并存两代产物：

```
2026-07-18T14:17  .outside-voice/design-voice-context.md          ← 旧固定名（本 change 之前的约定）
2026-07-18T14:17  .outside-voice/hr-tg-context.md                 ← 旧固定名
2026-07-18T18:38  .outside-voice/20260718T103718Z-JZRIJ1/design-voice-context.md   ← 新 per-run
2026-07-18T18:44  .outside-voice/20260718T103718Z-JZRIJ1/dispatch-manifest.tsv
```

旧两文件停在固定路径上（下一轮必被覆盖 = HV1 跨会话 TOCTOU 的成因），
新产物落在 `mktemp -d` 占坑的 run 目录下 ⇒ 改动是真的、不是纸面声明。

**G5（父目录须仍在 `.outside-voice/` 下）实证**：

```
$ git check-ignore -v .../20260718T103718Z-JZRIJ1/design-voice-context.md
.gitignore:19:**/.outside-voice/	（命中）
$ git status --short
 M openspec/issues/todolist/2026-07-todolist.md
?? openspec/changes/async-outside-voice/impl-reports/task5-verification-smoke.md
```

⇒ 真实 33KB context（含全量设计内容）**未进入 git 索引**，checkpoint 的 `git add -A` 不会把它入库。

---

## 5. fan-out 墙钟 vs voice 完成时刻：「重叠非叠加」校准 ⚠️ 部分达成（被测对象与验收标准不同）

> **返修注（fix1）**：验收标准原文是「**fan-out 墙钟** vs voice 完成时刻」，而下表实测的是
> **两条 voice 互相重叠**（async design-voice ∥ sync 降级 voice）。§9.5 已自陈**本轮未跑任何
> fan-out 多镜编排** ⇒ 被测对象被换掉了。下表证明的是「两个后台/前台 exec 可并行」，
> **不是**「voice 与 fan-out 重叠非叠加」。后者需一次真实评审编排才能证（同 T165 的补证条件）。

本轮实际产生了两个真实 voice 的重叠窗口（async 的 design-voice 与 §6 的 sync 降级 voice）：

| | 区间 (UTC) | 时长 |
|---|---|---|
| async design-voice | 10:38:10 – 10:42:32 | 262s |
| sync（降级）voice | 10:40:25 – 10:43:26 | 181s |
| **串行叠加将耗** | | **443s** |
| **实际墙钟 span** | 10:38:10 – 10:43:26 | **316s** |

⇒ **重叠节省 127s，`span(316) < 叠加(443)` 成立** —— async 分支下 voice 时长与主 session 其他工作**重叠而非叠加**。
（期间主 session 并未空等：在 async voice 在飞期间完成了 §7 错误路径、§8 per-site 核等工作。）

---

## 6. 降级 smoke：后台不可用 → 回落同步、外层 ≥330000ms、voice 正常完成 ✅

**后台能力自探（协议 ②）真跑**：

```
$ printf PROBE_OK   （以 run_in_background 派出，task id = bc3t9robb）
→ 输出文件内容: PROBE_OK
⇒ background="available"
```

**降级分支构造**：模拟 `background="unavailable"`，按矩阵走 sync 行——内层字面 `300`、
**外层 Bash 工具超时实参显式设为 `330000` ms**：

```
SYNC_START=20260718T104025Z
<<<SDFLOW_EXEC_EXIT>>>0
SYNC_END=20260718T104326Z
SYNC_WALL_SECONDS=181
stdout bytes: 1352
```

三条断言全部实证：

1. **外层实参 = 330000ms ≥ 330000ms** ✅，且 ≥ 内层 300s + 30s。
2. **voice 正常完成 rc=0**（1352 字节 findings），**非 ~120s 被杀** ✅。
3. 🔴 **该断言不是形式主义——本次实测 181s > harness 默认 120s**：
   若沿用默认外层超时，这次**完全成功**的 voice 会在 120s 被 kill，
   进而被误落 `reason_code="timeout"`。**即「假超时」失效模式在本轮真实负载下真会发生。**
   G7 指出该面「无机械门可守、只能靠本条 smoke 抓」——**本次确实抓到了它的真实存在性。**

---

## 7. 错误路径 smoke：collect 只取结构化状态，不采信后台文件原始 stderr ✅

构造 voice `exit≠0`，且**真的经 `run_in_background` 落进 harness 托管后台文件**（即 design 关切的新持久化载体）：

后台文件 `tasks/bu82e5s7m.output` 实际内容：

```
context file not found/unreadable: …/NO-SUCH-FILE.md      ← helper 原始 stderr（绕过出境 scan）
                                                            ← 空行（printf 强制前置换行）
<<<SDFLOW_EXEC_EXIT>>>2                                    ← 哨兵 envelope
```

**三条关键实证**：

1. **stdout 与 stderr 在后台文件里被合并进同一流** ⇒ design 的关切属实：
   原始 stderr 确实与 findings 通道同处一个文件，**∴「只取 exit0 的 stdout 当 findings」这条纪律是必需的、不是冗余**。
   本次 collect 依约 **rc=2 ≠ 0 ⇒ findings 池取空**，那行 stderr **未被当作 findings 采信**（只做摘要用途）。
2. 🔴 **harness 报告的退出码 = 0，而真实 voice rc = 2**
   （notification 原文：`completed (exit code 0)`——因整条命令以 `printf` 收尾恒成功）。
   ⇒ **harness 层状态码根本不可用于判 voice 成败**，**哨兵 envelope 是唯一可信来源**。这是 F-D 设计理由的直接实证。
3. 按 ⑦ 表 `exit 2 → exec-error`（不新增枚举）✅。

**退出码表其余分支实跑覆盖**：

| exit | 构造方式 | 实测 stderr / envelope | 归类 |
|---|---|---|---|
| 0 | 正常 voice | `<<<SDFLOW_EXEC_EXIT>>>0` | ok ✅ |
| 1 | `SDFLOW_VOICE_RUNNER=bogus` | `未知 SDFLOW_VOICE_RUNNER: bogus` → `>>>1` | exec-error ✅ |
| 2 | context 不可读 | 见上 → `>>>2` | exec-error ✅ |
| 3 | context 含 `AKIA…` | `secret-hit（拒发）: 规则=aws-akid 行=2` → `>>>3` | secret-hit ✅ |
| 124 | 见 §9（未真实触发） | — | 未达成，见 §9 |

**envelope 解析契约（⑤）对抗性验证**——按 SKILL 逐字实现整行锚定正则，跑 14 组（含本轮真实捕获的 3 组）：

| 用例 | 结果 |
|---|---|
| 真实 exit 1 / 2 / 3 捕获输出 | 正确归类 ✅ |
| voice 注入**独立整行** → 2 命中 | `exec-error` ✅ |
| voice 注入**带前缀**行 | 整行锚定已滤，仅 1 命中，取真码 ✅ |
| envelope 缺失（0 行） | `exec-error` ✅ |
| 前缀噪声 / 后缀噪声子串 | 均不命中 → `exec-error` ✅ |
| 未知码 99 | `exec-error`（**未读作 ok**）✅ |
| voice 末行无尾换行与 envelope 粘连 | 0 命中 → `exec-error` ✅（证 `printf '\n…'` 前置换行的必要性）|

> 诚实注记：首轮我的「≥2 行注入」fixture 写错了（注入行带前缀，被整行锚定正确滤掉），
> 表现为 FAIL —— **是 fixture 的错、不是解析器的错**。已改成真正的独立整行注入后全绿。

---

## 8. per-site 完整性机械核实证（补 §3.5 的落地验证）

拿**真实归档报告** `archive/2026-07-17-mlh-p6-recorder-frontmatter/spec-review-report.md` 做四组：

| 场景 | 结果 |
|---|---|
| A 无 `declared-sites` 锚 | `missing-declared-sites` **红** ✅（fail-closed，不静默放行）|
| B 补正确 `declared="design-voice,hr-tg"` | per-site 核**过** ✅ |
| C **并发 2 站点漏收一个**（删 hr-tg 站点锚） | `site-missing-anchor: hr-tg` **红** ✅ |
| D 两边自洽绕过（同时缩 declared 且不落锚） | `declared-not-expected: declared=['design-voice'] expected=['design-voice','hr-tg']` **红** ✅ |

单测覆盖（Task 4 落的）：`test_ds_*` **22 个专项用例**，`pytest -k ds_` → **24 passed**。

**`declared=` CSV 边界用例**（站点词表有界 ⇒ 可枚举校验，非无界语法手搓）：

| `declared=` | 判定 |
|---|---|
| `"hr-tg,design-voice"`（顺序反） | `declared-sites-not-canonical-order` ✅ |
| `"design-voice,,hr-tg"`（空 cell） | `malformed-site-csv` ✅ |
| `"design-voice,bogus-site"`（域外记号） | `malformed-site-csv` ✅ |
| `"design-voice,hr-tg,hr-tg"`（重复） | `declared-sites-duplicate` ✅ |

**`code-review` 层同样验过**（不止测 spec-review 一层）：对真实归档
`archive/2026-07-16-add-codex-host-support/code-review-report.md` 跑该核——

```
该报告实落站点集 = {code-voice}          （只有 1 条 outside-voice 锚）
其 hr-tg 锚的 declared ∩ HR-TG ≠ ∅       ⇒ 公式重算期望集 = {code-voice, hr-tg}
→ VIOLATION: declared-not-expected  declared=['code-voice'] expected=['code-voice','hr-tg']
```

⇒ **这条历史报告本应有 hr-tg 站点锚而没有**——即新核在**真实历史语料**上抓到了一处真实遗漏，
不是只在我构造的用例里才会红。（对存量归档无追溯影响：该门只作用于新报告。）

**盲区对照实证**（证明这个核确有增量、不是重复既有门）：

```
C 场景报告的实落 outside-voice 锚条数 = 1
→ 家族级门 check_existence（≥1 即过）判: PASS —— 即漏收被放行
∴ per-site 核补的正是这个盲区
```

---

## 9. 未达成项 / 残余（显式登记）

### 9.1 ❌ 未达成：4.1③「刻意构造 voice 时长逼近 900s」的**真实模型**版本

- **原因**：helper 实际调用 `codex exec` / `claude -p`，**模型推理时长没有可控注入点**。
  本轮真实 voice 实测 262s / 181s，均 <600s——**无法靠真实模型稳定构造逼近 900s 的负载**。
- **本轮的替代做法（已跑，见 9.2）**：用 PATH fake runner 固定 `sleep 660` 压后台生命周期。
  这测的是**真正的风险面**（后台任务能否跨过 harness 600000ms 上限存活），
  而非模型推理时长——后者对本 change 的正确性没有承重作用。
- **缺什么才能真达成**：一个可控时长的真实 runner，或接受「真实模型 smoke 只验 `ok`/非阻塞/findings 入池，
  后台生命周期用 fake runner 单独验」的拆分。
- 🔴 **值得注意**：**voice 自己独立提出了同一条**（见下「voice 反馈」第 1 条）——两路独立到达同一结论。

### 9.2 🔴 长跑后台存活：**第一次尝试被意外回收，暴露一条高危未知面**

**做法**：PATH fake runner（固定 `sleep 660`，不含模型推理），经真实 helper 路径
（`outside-voice.sh` → `timeout -k 10 900` → fake codex）以 `run_in_background` 派出，内层 `--timeout 900`。

**第一次尝试（task `b28kp3z3h`）—— 未跑满，被 SIGTERM**：

```
dispatch    10:44:23Z
最后写入     10:51:02Z      ← 存活仅 399s
600000ms 上限本应在 10:54:23Z —— 远未到
输出文件末行:
  outside-voice.sh: line 207: 51309 Terminated: 15   ← timeout 进程被 SIGTERM
（**无 `<<<SDFLOW_EXEC_EXIT>>>` 行** —— 整条命令未走到收尾 printf）
```

**这不是 600000ms 上限**（399s < 600s），是**另一个回收源**。三条独立佐证指向同一时刻：

| 后台任务 | 本应 | 实际 |
|---|---|---|
| `b28kp3z3h`（sleep 660） | 跑到 10:55:23Z | **10:51:02Z 被 SIGTERM** |
| `bld2muoaz`（until-loop 守望，无限循环） | 一直循环 | **同窗口消失，输出 0 字节** |
| `bf7fa4l48`（sleep 240，10:50:37 起） | 10:54:37Z 出结果 | **同窗口消失，输出 0 字节** |

⇒ **该会话内当时在飞的全部三个后台任务，在 ~10:51:02Z 同时被回收**，且回收点**与我结束本轮对话轮次
（停止发工具调用、转入等通知的空闲态）在时间上重合**。

对照组：**同一会话早前的真实 async voice（`boxfeo2jj`，262s）完整跑完 exit 0** ——
其整个在飞期间我在**持续发工具调用**（未空闲）。

🔴 **若该假说成立，它直接冲击本 change 的核心机制**：SKILL ⑥ 明文要求
「站点仍 RUNNING ⇒ MUST **让出轮次**、等该后台任务的完成/超时通知」——
**而「让出轮次」正是本次触发回收的那个动作**。果真如此，则 barrier 在「voice 比 fan-out 慢」
（正是 async 化要救的场景）时会**把自己等的那个后台任务杀掉**，且因为杀死后不再有完成通知，
还可能**永不返回**（本轮我armed 的守望任务即一并被杀，无人再通知我）。

**与 design 所引 spike 的条件比对**：design.md:35 与 spec-review-report.md:28/81 记的那次 spike 是
「后台跑满 660s、跨 600000ms、exit 0、**ppid 全程 11092 稳定不 reparent**」——
「ppid 全程稳定」这个说法本身意味着**该 spike 期间有人在持续观察**（= 会话活跃态）。
∴ **既有 spike 与我的失败用例并不矛盾**：两者活跃度不同，spike 从未覆盖「主 session 空闲让出轮次」这一态，
**而那恰恰是 SKILL ⑥ barrier 指令要求进入的态。**

### 9.2b ✅ 对照实验：**保持活跃则 660s 跑满、跨过 600000ms 上限、exit 0**

同一命令、同一 fake runner、同一 660s、同一会话，**唯一变量 = 全程保持活跃**（期间持续发工具调用，
用 4 次 `pytest -q` 等真实工作填满等待，从不进入空闲态）：

```
RETRY_DISPATCH_AT=20260718T105757Z
OV_TRUNCATED=false
FAKE_VOICE_OK after 660s sleep
1. 问题：fake finding / 严重度：low / 证据：smoke / 建议：无
RETRY_END=20260718T110857Z

<<<SDFLOW_EXEC_EXIT>>>0
```

| 指标 | 结果 |
|---|---|
| 实际跑满 | **660s**（10:57:57Z → 11:08:57Z，分秒不差） |
| 跨 600000ms 外层上限 | **是**（660s > 600s）——Bash 工具外层上限**确实不管后台任务** |
| 退出码 | **exit 0**，envelope 恰好 1 行 |
| 进程链 | `zsh → outside-voice.sh → timeout -k 10 900 → fake codex → sleep 660` 全程完整 |
| ppid 稳定 | **是**（`66874 ← 66872 ← 66871 ← 66723 ← 66718` 全程不变，无 reparent） |

⇒ **4.1③ 的「后台跨 600000ms 上限存活」半达成**，且**独立复现了 design.md:35 所引 spike 的结论**
（660s / 跨 600000ms / exit 0 / ppid 稳定，四项逐一对上）。

### 9.2c 两次尝试的受控对比与结论

| | trial 1 | trial 2（对照） |
|---|---|---|
| 命令 / runner / 时长 / 会话 | 完全相同 | 完全相同 |
| **主 session 活跃度** | 派出后 **让出轮次、转空闲等通知** | **全程活跃**，持续发工具调用 |
| 结果 | **399s 被 SIGTERM，无 envelope** | **660s 跑满，exit 0** |

~~**单一变量 = 活跃 / 空闲。**~~ 600000ms 上限已被 trial 2 排除（660 > 600 却成功）。

> 🔻 **返修（fix1 §1）——「单一变量」措辞不成立，且与本报告 §11 自陈的未知面自相矛盾**：
> §11 已写明「本轮全部观测均发生在 **implementer 子代理上下文**中，主 session 是否同样受影响未直接测过」。
> 在子代理上下文里，「**转入空闲**」与「**该子代理轮次终结**」是**同一个动作、不可分辨** ⇒ 本对比
> **不是单一变量**，它同时改变了两个因子。∴ 上表只支持「**子代理轮次终结** ⇒ 回收」。
>
> **编排层随后在主 session 直接做了判别实验**：`run_in_background` 心跳探针（每 5s 落盘），期间**多次
> 让出轮次转空闲**等通知 → **702s 跑满、exit 0、ppid 全程稳定 53240 无 reparent、141 拍心跳无断点**，
> **跨过 B8 的 399s 死亡点、也跨过 600000ms 上限**（证据 `/tmp/mainsess_probe.log`）。
> ⇒ **「主 session 空闲 ⇒ 回收」被证伪**；B8 收窄为子代理域缺陷、P1 → P2。
> 相应地，下文「结论（高危）」段关于 barrier 的推论**不再成立**——barrier 执行位已在两评审 SKILL 的
> marker 段 ⑥ 焊死为「MUST 在主 session、MUST NOT 委派子代理」。

🔴 **结论（高危，超出本票原定范围，已另开 bug 记录）**：
**「主 session 让出轮次转空闲」与「后台任务存活」在本 harness 下是冲突的**，
而 SKILL ⑥ 恰恰把前者写成了 barrier 的 MUST 动作：

> 「站点仍 RUNNING ⇒ MUST **让出轮次**、等该后台任务的完成/超时通知」

即：**voice 比 fan-out 慢时（正是 async 化要救的那个场景），barrier 会杀掉它正在等的那个后台任务**；
且杀死后不再产生完成通知（本轮我 armed 的守望任务一并被杀），**collect 可能永不返回**。
按 ⑦「其余一切情形 → 保守 fallback exec-error」尚不至于假绿，但 **async 的收益在该路径上归零、
甚至劣于同步**（白等一场再降级）。

**诚实边界（MUST NOT 高估本结论的强度）**：
空闲态目前是 **n=1**（一次触发，但同时杀死 3 个在飞任务，属同一事件的三个观测点）；
活跃态 n=2（262s 真实 voice + 660s fake）。**我未刻意重跑第二次空闲态做双向复现**——
因为若假说为真，空闲后无人通知我，会话会挂死。∴ 结论方向明确、机制未定
（是「turn 结束」还是「子代理空闲回收」还是别的触发点，未隔离）。**建议按 P1 跟进复现与定位。**

### 9.3 ⚠️ 残余：exit 124（真超时）未实跑触发

- 本轮**未构造真实 124**。envelope→`timeout` 的映射已在 §7 的解析契约测试中覆盖（合成输入），
  但**「helper 内层 `timeout -k 10` 真打到、真返回 124」这一段未端到端跑过**。
- 代价评估：该路径由 GNU `timeout` 自身保证，且 §9.2 的长跑用例已验证「内层未到期时不误杀」的对偶面。
- **登记为残余**，未打勾。

### 9.4 ⚠️ 残余：harness 后台输出文件的 TTL / 清理归属**未定**

**已实测确定的部分**：

| 维度 | 实测结果 |
|---|---|
| 落点 | `/private/tmp/claude-501/<project-slug>/<session-uuid>/tasks/<task-id>.output` |
| 权限 | **`-rw-r--r--`（0644，同组/其他用户可读）**，umask 022 |
| 父目录链 | `/private/tmp/claude-501`、`<project>`、`<session>` 均 `drwx------`(0700)；但 `tasks/` 自身是 `drwxr-xr-x` |
| 有效保护 | **靠 0700 祖先目录，而非文件自身权限** |
| 跨会话持久 | **是**——单机现存 40 个 session 的 task 目录、143 个真实输出文件 |
| 最老留存 | 2026-07-13（**5 天前仍在**） |
| 内容 | **stdout 与 stderr 合并**（§7 实证）⇒ 未扫描的原始 stderr 会持久化落盘 |

**补充实证**：被 SIGTERM 杀掉的任务（`b28kp3z3h`）**其输出文件连同 helper 原始 stderr 一并留在盘上**
（345 字节，含 `Terminated: 15` 与进程行）——即**异常终止不触发任何清理**，落盘面与正常完成一致。

**未定（诚实登记，MUST NOT 当已知）**：

- **TTL 无法从本机语料判定**：`>7d` 的文件数为 0，但该语料本身只跨 6 天（最早 07-12 起用）
  ⇒ **区分不了「无 TTL」与「TTL ≥7d」**。拿 0 反推「有 7 天清理」是**拿现状快照当结论**，不做。
- **清理归属未见**：未观察到任何 harness 侧主动清理行为；实际回收可能仅依赖 OS 对 `/private/tmp` 的
  周期性/重启回收，**归属方无文档依据**。
- **安全含义（承 design 的既有缺口登记）**：`exit≠0` 时的**原始 stderr + 未扫描 final-message 前 3 行**
  会落进一个 **0644、跨会话留存 ≥5 天**的文件。本 change 的 collect 纪律（只取结构化状态 + exit0 stdout）
  管住了**采信面**，但**不改变落盘面**。该残余**超出本 change scope**，此处如实登记。

### 9.5 未跑：完整 `/sdflow-spec-review` 端到端编排

- 本票实证的是 **async 调度机制本身**（自探 → dispatch → manifest → 通知驱动 collect → envelope → 归类 → per-site 核），
  以逐条真实运行覆盖；**未**跑一次完整的多镜 `/sdflow-spec-review` 编排（成本高、且需切 dev 软链）。
- 影响评估：编排层的其余部分（fan-out 多镜、报告合并）**不在本 change 改动范围内**，
  本 change 的全部改动面已被上述逐条 smoke 覆盖。
- **如实登记为「部分达成」**，不冒充完整评审跑通。

---

## 10. voice 反馈（跨模型第二意见，原样转录要点）

async design-voice（codex）对本 change 提了 3 条，**其中第 1 条与我独立得出的 §9.1 完全一致**：

1. **[high]** 近 900s 的真实模型 smoke 不可控、不可重复——`tasks.md:32` 要求「刻意构造」，
   但 helper 调 `codex exec` / `claude -p`，推理时长无可控注入点。
   建议拆成两项：fake runner 固定 sleep 验后台生命周期；真实模型 smoke 只验 `ok`/非阻塞/findings 入池。
   → **本票已按此执行**（§9.1 + §9.2）。
2. **[high]** context 路径直接拼进 shell 且未引用——路径含空格/shell 元字符时会参数拆分或执行非预期命令。
   → **本票未处理**（属 SKILL 命令形态，改它会动等值门 marker 段）；**建议转 buglist/todolist 由后续 change 处理**。
3. **[medium]** dispatch manifest 不能可靠证明「本报告的本次 dispatch」——报告与锚行未记 `run-id`，
   且 dispatch 成功与 manifest 追加之间存在中断窗口。
   → **本票未处理**，同上，建议后续 change 评估。

> 按票 scope，2/3 两条**不在本票改动范围**（本票是验证票、且触 SKILL 会动等值门），故如实转录、不擅自改。

---

## 11. 收尾记账（§5.1 / §5.2）✅

| ID | 内容 | change 字段 |
|---|---|---|
| **T162** | Codex 方向 efficacy=0：架构性无法离开关键路径，待 codex `deferred_executor` 稳定或外部 claude daemon 再议 | `async-outside-voice` |
| **T163** | DRY 全抽取：把 async marker 段抽单一源注入两 SKILL，替代「两份副本 + 等值门」 | `async-outside-voice` |

均落 `openspec/issues/todolist/2026-07-todolist.md`，状态 OPEN，**显式带 `change` 字段**（防误挂）。

**另立缺陷（本票新发现，非 tasks.md 预定项）**：

| ID | 内容 | 优先级 / 状态 |
|---|---|---|
| **B8** | ~~主 session 让出轮次转空闲后…被整体回收~~ → **返修后**：子代理上下文的轮次终结会回收该上下文在飞的 `run_in_background` 任务；主 session 让出轮次转空闲**不受影响**（702s 实证） | ~~P1~~ → **P2 / VERIFIED**（见 fix1 §1） |

落 `openspec/issues/buglist/2026-07-18-buglist.md`，带 `change=async-outside-voice`。
**B8 待定位的首要问题**：本轮全部观测均发生在 **implementer 子代理上下文**中——
「主 session 是否同样受影响」未直接测过，这是决定影响面大小的关键一问（详见 B8 的 thinking 段 ②）。

---

## 12. 工作契约三项 ✅

```
$ /usr/bin/python3 -m pytest -q
1667 passed, 2 skipped in 71.36s          ← 与基线 1667 passed 一致（§12.1 fold 修复后；共跑 6 次稳定复现）

$ /usr/bin/python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致

$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 20 个投放面全部与真相源一致
```

- **未修改 change 四件套**（`proposal.md` / `design.md` / `tasks.md` / `specs/`）——设计门未失鲜。
- 全局软链未改动（§0）。

### 12.1 途中 fold 掉的一个真实缺陷（`sdflow-buglist` 测试与写入方契约不一致）

**怎么撞上的**：§11 记 B8 时，`buglist.py` 新建了当天第一个 buglist 文件
`openspec/issues/buglist/2026-07-18-buglist.md`，随后全仓 pytest **变红 1 条**：

```
FAILED sdflow-buglist/tests/test_task5_delivery_contract.py::
       test_repository_legacy_corpus_matches_independent_projection_item_by_item
AssertionError: .../2026-07-18-buglist.md: expected one legacy overview
assert 0 == 1
```

**根因（读码定的，非猜）**：

- 新建文件走 **`mode: canonical`**（frontmatter 为真相源，`buglist.py:1320`），**不写** legacy 的 `## 状态总览` 表。
- 写入方**自己的一致性自检**就是这么规定的：`buglist.py:550` —— `expected_count = 0 if model["mode"] == "canonical" else 1`。
- 而该测试的 `_reference_legacy_rows` 对**目录内每个 `.md`** 无条件断言「恰好 1 个总览表」，
  与写入方的 canonical 契约**直接矛盾**。

⇒ **defect 在测试侧，不在写入方。** 这是一条**潜伏缺陷**：存量语料恰好全是 legacy / 双写文件，
**直到有人新建当天第一个 buglist 文件才会触发** —— 即「任何人记当天第一条 bug 都会把全仓测试搞红」。
（典型 dogfood 盲区：现存语料的形态掩盖了目标态 producer 会产出的形态。）

**改法（3 行，additive，不放宽任何既有断言）**：
`_reference_legacy_rows` 在**无总览表**时返回 `None`（canonical-only，无可投影对象），调用方跳过；
`>1 个总览表`、`表体非空`、以及全部逐字段对拍**一条不动**。

**反向验证**（证明没把门改松）：

| 构造 | 修复后行为 |
|---|---|
| 双 `## 状态总览` 表 | **仍 assert 拦下** ✅ |
| canonical-only（无表） | 返回 `None` → 跳过 ✅ |
| 既有 legacy / 双写语料 | 逐字段对拍照跑，`8 passed` ✅ |

> **为什么就地 fold 而不是 defer**：它**恰好卡在本票的收尾门上**（三门须绿），根因一读即明、
> 改动面 3 行且只增不减，符合本仓「撞到相关 bug 立即做掉」的拆分标准。
> **但它确实是 `sdflow-buglist` 的资产、不是本 change 的** —— 故在此显著登记，供 code-review 复核该判断。

**等值门变异验证**（绿灯本身也要证明不是空转——「门绿」可能只是门没在看）：

```
$ 在 sdflow-code-review/SKILL.md 的 marker 段内注入 1 个字符（"锚定。" → "锚定 。"）
$ /usr/bin/python3 hack/check_async_branch_parity.py
[async-branch-parity] FAIL: async host 调度段已漂移 —— …不逐字节相同
   首个不同在段内第 27 行：
     A:     **MUST NOT** 用宽松 grep / 子串匹配 / 取末行代替整行锚定。
     B:     **MUST NOT** 用宽松 grep / 子串匹配 / 取末行代替整行锚定 。
   修：以一侧为准，把整段（含 marker 行）原样复制到另一侧
exit=1

$ 还原后
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致    exit=0
$ git status --short   → 无 SKILL.md 残留修改
```

⇒ 该门**对单字符漂移敏感、且能定位到段内行号**，绿灯有承重意义。
