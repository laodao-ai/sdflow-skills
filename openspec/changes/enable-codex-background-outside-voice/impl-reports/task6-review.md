# Task 6 双轴审存档 — 真实 efficacy 证据与 T162 关闭

**票**：Task 6（R-ID: OVBG-01, OVBG-03, HAE-08, HAE-09）
**轮次**：轮 1（`3c7ff5e`）**双 FAIL** → fix1（`a9ad091`）→ 轮 2（Spec PASS / Standards FAIL）
→ fix2（`5567714`）→ 轮 3 **双 PASS**

## 🔴 本票结论：efficacy 三门**未达标**，T162 **保留**，`design.md` 一字未改

本机 Codex CLI 的 ChatGPT 登录**用量配额耗尽**（最早 2026-07-29 10:11 恢复），
**一轮 Codex 宿主评审都没跑成**。implementer 实跑两次 `codex exec`（正式 + 最小复现）均返回
`ERROR: You've hit your usage limit`，并逐条查证四条替代路径全不可行（无 `OPENAI/CODEX` env、
`~/.codex/config.toml` 无 `model_provider`/`api_key`、`ollama`/`lmstudio` 未安装、
弱模型顶替编排层违反 `model-tiers` 禁降档）。

⇒ 按 `tasks.md` 6.3 明文路径处置：**保留 T162 + 如实记录 + 不以编排 smoke 假绿**。

### 六条验收标准最终判定

| # | 判定 | 依据 |
|---|---|---|
| 1 Codex 层全站点 `host="codex"` | ❌ | 额度限流，无 codex 锚 |
| 2 层内自然 >300s 成功站点 | ❌ | 6.2 主语是「**该完整层**」，锚在 6.1 的 Codex 层；436s 站点 `host="claude"` 不在该层内 |
| 3 结构化证据 + 检查器判定 | ⚠️ | 6.1 末句是「并由确定性检查器**判定**」（「通过」在 6.3）⇒ 机制已交付且有效；但**被判对象是 probe、不是 efficacy 证据** |
| 4 未达标则留 T162 + 如实记录 | ✅ | `T162 OPEN`；`git diff --name-only -- design.md CONTEXT.md issues/` **空** |
| 5 全量回归绿 | ✅ | 轮 1 实为 ❌（见下），fix1 后转绿；轮 3 实跑 **2629 passed** |
| 6 validate --strict + 下游未手改 | ✅ | `valid` rc=0；下游 `status --porcelain` 空、canonical workflow 规则零改动 |

## 轮 1 的 Critical：**两轴独立抓到 HEAD 全量是红的**

`task6-real-efficacy.md:33` 写了两个 legacy skill 名的字面串 ⇒
`test_downstream_reference_guard::test_no_legacy_skill_references_outside_allowlist` 红。
两轴各自实跑 HEAD 得 **`1 failed, 2556 passed`**，而 implementer 自报 `2557 passed`。

**根因（可复用形态）**：该守卫扫 **`git ls-files`**（tracked 集）。implementer 跑门禁时报告
**尚未 `git add`**，守卫看不见它 ⇒ 绿；`checkpoint-commit.sh` 的 `git add -A` 纳入 tracked 后
**同一条守卫立刻红**。⇒ **自报门禁结果在这类守卫上结构性不可信，与诚实无关。**
本轮起 fix 的硬要求改为「**先 `git add -A` 再跑全量**」，让观测时点与门禁输入集对齐。

**连带面**（Spec 轴预警并应验）：编排层生成的 `-fix1` diff 包因 `-` 行原样保留旧串，
把 guard 又引红一次 ⇒ **评审交接包改放 scratchpad、不入仓**。

## 轮 2 的 Important：`host` 有可机械捕获路径却没捕获

Spec 轴指出 implementer 「host 不是盘面可派生量」的判断**在 collect 侧成立、dispatch 侧不成立**：
`resolve-models.sh` 用 `CLAUDECODE=1` / `CODEX_THREAD_ID` 判宿主，而 **dispatch 就跑在宿主 shell 里**，
`job.json` 却未落该字段 ⇒ **将来关 T162 时，唯一的决胜门仍要靠 `--host` 自报** ——
正是本 change 要消灭的「无机械锚的 ✅」。**最便宜的锚在 helper dispatch，不在 SKILL。**

**fix1 做成了真机械化**：`detect_host()` → `job.json`（进 `JOB_REQUIRED_FIELDS`，缺即 CORRUPT）
→ `derive_status` 透传 → collect witness → `emit` 从盘面搬，**`--host` 入参整个删掉**
（`inspect.signature` + `SystemExit` 双验）。既有 317 条零回归，仅动夹具 2 行（**补必填字段、非放松**）。
`job.json` 的 delta spec 措辞是「**至少记录**…」⇒ 加字段属容纳范围内，**未改任何 spec**（改了反是③的加宽）。

Spec 轴端到端实证：直调 `detect_host()` 五组 env 全对（**正信号判定、无「缺失即另一方」的负推断**）；
另造盘面 `host="codex"` 的双站点 run-dir 走完整链 → 三门全过；改单站点为 claude → 判 `mixed` 红。

## 轮 2 的 Important（Standards）：G1 `runner` 维完全无锚

定点删掉 `("runner", REQUIRED_RUNNER)` → **78 passed**。根因：断言 needle 被 **G2 的失败文本**满足
（G2 消息里本就含 `runner=claude`），**5 个参数里 4 个恒真**。
**后果非纯测试问题**：多站点层里混一个 `runner="codex"`（同族 fallback，**正是本 change 要消灭的形态**）
只要另有站点跨 300s 就会放行。

## fix2 的面治：**恒真锚有两种成因，评审只报了一种**

「测试全绿但门是假的」在本 change 已第三次出现（Task 5 主线 5 条 → Task 6 轮 1 自捕 2 条 → 轮 2 F4）。
fix2 按面治扫全 **38 条门：修前 8 条无独立锚 → 修后 0 条**，并发现：

| 成因 | 表现 | 修法 |
|---|---|---|
| ① needle 被别的门的失败文本满足 | 目标门整个删掉照绿 | 收紧 needle 为定向串 |
| ② **压根没有用例走到那一行** | **症状完全相同** | **补用例** |

⇒ **只按成因①去找「过宽的 needle」会漏掉一半。**
**判定方法只有一个且是机械的：对每个门定点删掉它 → 必须红。**

Standards 轴轮 3 抽验 19 条门 + 另抽 8 条既有门，**全红**；并确认第二类的修法（补用例）**确实让门变红**。

## 跨语言 parity 门（Standards 轴建议 → 已做）

`detect_host`（Python）↔ `resolve-models.sh`（shell）原是**两份跨语言实现、零机械等价守**。
fix2 加了一条**真对跑**的门：`run_resolve()` 实起 `bash resolve-models.sh` 子进程取 `SDFLOW_HOST`，
与 `JOB.detect_host()` 直接比较，断言 `shell_host == python_host` —— 正是 `CLAUDE.md` 基准 5
「**让工具自己回答**」（不手搓等价性证明，直接跑两边比结果）。

两轴各自双向变异实证（PY 侧冲突/兜底/宽松真值、SH 侧 `CLAUDECODE` 放宽 / `CODEX_THREAD_ID` 取反）
**全红**；且绝对值另由两侧既有用例分别钉死 ⇒ **不存在「同向漂移一起绿」**。
实测两侧语义**完全一致**，**无需上抛的真 bug** —— 该门是防将来漂移，不是修当下的洞。

## F5：关 T162 的 runbook 被本 change 自己改废

`task6-real-efficacy.md:309` 的「重开条件」仍写着 `emit --host codex`，而 `--host` 已删 ⇒
该命令现在 argparse **exit 2**，**将来关门的人照着跑必撞墙**。这是「改共享字符串漏了消费者」的同族。

fix2 做了**正确的三分**（两轴均认可）：

| 类型 | 处理 | 理由 |
|---|---|---|
| 规范性判断（§4.3「host 不是盘面可派生量」、§十.4「`--host` 自报是真诚实边界」） | **保留原文 + 🔴 supersede 批注**（明写「此判断是错的」） | 改写会抹掉「评审抓到了什么」的审计链；impl-report 体裁本就是演进史，**不适用 DOC-1 的「正文即最终态」**（那条管 design/SKILL 类文档） |
| **可执行 runbook**（§六「重开条件」） | **直接改写** | 读者会照着敲，**留原文即留地雷** |
| 命令实录（§4.2 的 235/249 行） | **未动** | 是历史事实 |

## 顺带取得的两项真实证据（非 efficacy，但是硬锚）

1. **真实 transport 全链路走通**：dispatch **1.257 秒**拿到 canonical id；`ps` 实抓 runner argv =
   四旗 + opus + `--effort high --safe-mode --no-session-persistence`；自然 **436 秒 > 300 秒**且
   **rc=0**（**旧同步天花板会把这次砍成 rc=124**）；cleanup identity 四项核验 + 子树 exited + roster 清空。
   Standards 轴独立接地核验：`duration_seconds=436.0`、`terminal_at−started_at=436`、
   `stdout_sha256` 与重算逐字节相同、mtime 01:00→01:07 佐证 7 分钟真实墙钟、
   stdout 是带 `check-permission.toml:14-17` 可核引用的**真评审意见**，非 shim。
2. **Task 5 遗留的「真实 HOME 未验」已兑现**，且在真实混配上**首次验到 OVBG-01 的 skew fail-closed**
   （新 job helper × 旧 `outside-voice.sh` ⇒ `preflight-error` + 精准 hint）。

## 全局状态（已还原并亲验）

32 条 symlink target 已全部指回运行 checkout；`~/.sdflow/hack/` 残留两个新文件
（`outside-voice-job.py` + `capability-manifest.json`，旧 `setup.sh` 不认识它们）。
**残留不造成假绿**——两轴独立核验：运行 checkout 的两份评审 SKILL 对 `outside-voice-job` **零引用**、
旧 `outside-voice.sh` 不读 manifest ⇒ **残留无任何消费者，不存在半可用态**；preflight 实跑
`ok:false / reason_code:preflight-error`。**未删**（全局 CLAUDE.md 禁未经真人确认删文件，
且删与不删可观察行为等价）。**清理 = 合并后重跑 `bash ~/.skills/sdflow-skills/setup.sh`。**

下游 `zhws_ops_api`：`git status` 干净，canonical workflow 规则零改动，
唯一产物是 gitignored 的 `.outside-voice/<run-id>/`（OVBG-05 要求保留的审计证据）。

## Minor defer

**T224**（面治枚举漏 2 条 `isinstance` 早退分支，均无独立锚；非当前假绿，但报告标题宜订正为
「**所枚举的 38 条**中 0 条」。**可复用观察：「我扫了 N 条门」本身也是一个可能不全的断言**）。

## 🔴 编排层裁断：票面工作已尽，卡点是**范围问题**不是质量问题

Spec 轴引原文判定（编排层采纳）：

> **Task 6 算「已做到尽头的未完成」** —— `superpowers-plan.md` 票面目标**自带二分出口**
> （「…才允许关闭 T162…**否则如实保留缺口**」）⇒「未证 → 如实保留」是**票面认可的合法终态**；
> `tasks.md` 6.3 已完全执行、6.4 已完成。但 6.1/6.2 是**动作项**，外部额度封锁 ⇒ **两框不可诚实勾选**。

**已勾**：第 4 / 5 / 6 条（真达标）。**未勾**：第 1 / 2 / 3 条。
**MUST NOT 打 `task6-` 完成标签** —— 打了就是假绿（gate 的标签通道会把本票算完成）。

⇒ `ship_gate` 停在 **5/6**，自动链路不进 `RUN_CODE_REVIEW`。**继续推进需人拍板**：
① 等 07-29 配额恢复补跑 efficacy；② 把 6.1/6.2 显式降为后续项（**T162 已 OPEN，天然承接**）。
**编排层不替人拍。**

### efficacy 未证是否阻断本 change 完成（Spec 轴依据，供拍板参考）

**只阻断 T162 关闭与「efficacy=0」陈述改写，不阻断本 change 完成**：
① `proposal.md` 唯一阻断条款是「**若真机存活测试失败**则本方案阻塞」——存活测试
**436s 跨 shell rc=0 成功**，条款未触发；② 可证伪假设「后台化后即使 >300s 也不再丢结果」
**被正面证实**；③ spec 内唯一 SHALL 级阻断是 OVBG-04 的 negative smoke（已绿）；
④ `tasks.md` 6.3 为未达标**预置了出口**而非中止。
**但 `proposal.md` 的 Success Metric #1（Codex 真跨模型成功率）未达成** ——
合并即等于带着头号指标未证发布，**该取舍属人拍板**。
