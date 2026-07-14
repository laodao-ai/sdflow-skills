# hand-off — add-sdflow-devenv

*2026-07-14 · verify: PASS（1261 tests 绿）*

---

## ✅ 完成了什么（锚点已逐条复核存在性）

### 1. `sdflow-devenv` skill 本体 —— 脑 / 手 / 记性

| 层 | 落地 | 锚点 |
|---|---|---|
| **A 脑**（skill 的全部价值） | `SKILL.md` + `references/` 5 份（testing-framework · environments-template · lane-patterns · verification-patterns · review-lenses · boundary-rules） | `sdflow-devenv/references/*.md` |
| **B 手** | `devenv_scaffold.py`（init/set-layer/set-lane/**verify-lane 真 fork**/confirm-lane/render/inject） | `test_scaffold.py` |
| **C 记性** | `devenv_schema.py`（`.devenv.json`）+ `devenv_lint.py`（**只报不拦**，退出码恒 0） | `test_schema.py` · `test_lint.py` |

**核心承诺兑现**：三层框架六槽，做不了的写「不适用 + 后果」，`⚠️ 待定` 是**合法产物**（15/15 全待定仍 exit 0）。

### 2. 首个真实试点 —— `sarvelo/mqtt-console`（A-8 拿到实证）

**A-8**（「模型能为三层提出**像样的**验证方法」——设计的地基假设，此前**零实证**）：**成立。**

- 13 条泳道横跨三层，**10 条真跑绿**（script fork，exit 0，带 commit 锚）
- **不只是文档**：真落了 `hack/doctor.sh` · `hack/e2e-live.sh` · `schema_golden_test.go` + golden fixtures · `frontend/e2e-live/live.spec.js` + `playwright.live.config.js`；Makefile 加 `race` / `doctor`
- **⑥ 盲区槽产出真发现**（最担心的一格）：指出 `happy-path.spec.js` 跑在**手写的 `wailsStub.js`** 上——一份对 Go 后端行为的手写镜像，**没有任何东西检查这面镜子照得对不对**（`assert-bindings` 只查 6 个函数名，真实绑定面 26 个）。**而且它把这个洞补上了**（新建 `wails-live-e2e` 真链路泳道，跑绿）。

### 3. 三条通则（执行期 fold）—— 托管注入，20 个投放面

① 能查的自己查 · ② 不确定的先调研再给推荐 · ③ 以目标态为准，MUST NOT 拿现状反驳目标。

真相源在 `sdflow-init/assets/`（**源 == 分发件 == `outside-voice.sh` 读的那个文件**，无第二份拷贝）；
`hack/sync_principles.py --check` 是门禁（`setup.sh` 每次跑 + `hack/tests/`）。

### 4. `workflow.md` 三分（执行期 fold）

`prompts/step*.md`（**单一源**，模型取一行 prompt 只读 552 字节，而非 19.6KB）+ `workflow.md`（骨架）+ **`WORKFLOW-GUIDE.md`（生成物，init 拷进消费仓）** + `workflow-history.md`（考古层，模型永不读）。

外加 **ff → grill 交棒规则**（`claude-section.md`：`grill-with-docs` 只能人手动触发 ⇒ **MUST 把 prompt 原样贴出来**）+ **superpowers `task-brief` 断口修复**（`Global Constraints` 不进 implementer 的 brief ⇒ 约束必须也写进每个 Task 段）。

---

## ⏳ 未完成 / 延后

### 冷层三次抓到承重级假绿 —— 这是本 change 最该被记住的事

| # | 假绿 | 谁抓到的 | 性质 |
|---|---|---|---|
| **A29** | 层状态投影「**一绿即绿**」——e2e 层 1/3 绿，标题照报「✅ 已验证」 | mqtt-console 试点 | **A25 的病换到投影函数里又长出来**；而它**曾被写进测试断言**（`# 多楼道：有一条绿就算绿`）——不是漏了，是**被当成正确行为固化了** |
| **G3** | `uncovered_contracts()` **有函数、有单测、全绿，但 `main()` 根本不调它** ⇒ 生产路径恒空。而 `references/review-lenses.md` 写着「机械部分已经算好了」——**一句会主动误导冷审子代理的谎** | **冷 verify 子代理**（用户已明示跳过 code-review，它是唯一的独立层） | **有单测 ≠ 可达** |
| **B6** | `sad_schema` 的 contract 扫描**剥 fence**，而模版要求 contract 写 **fence 内** ⇒ 真实 SAD 恒扫出 **0 条**，`sad_lint` 的 contract 不变式校验**从未触发** | 修 G3 时 dogfood 到真消费仓才暴露 | producer 说 fence 内、parser 剥 fence、**fixture 站 parser 那边** ⇒ 三方各说各话的假绿。修复后当场在 mqtt-console 抓到 **3 条真违规** |

> **⚠️ 残余风险登记**：本次 **`/sdflow-code-review` 按用户明示跳过**。而上面三条**全部由独立冷层抓出**——
> 生成 session 自己一条都没看见。**下次别跳。**

### 具体延后项

| 项 | 状态 | 影响 |
|---|---|---|
| 试点结论回灌 `references/` | ⏳ **未做** | spec 强制的负面知识已在 `verification-patterns.md`；A29/A30 的修已进代码 + SKILL.md + 模版。**Minor** |
| `/sdflow-code-review` | ⏭ **跳过**（用户明示） | 见上方残余风险 |
| **B6 的下游影响** | ⚠️ **待人处理** | mqtt-console 的 SAD 现在会被 `sad_lint` 判出 **3 条真违规**（`status=skeleton-ready` 但 `contract[validated]`）——**它们一直在那儿，只是从来没人看见**。要么升 status，要么降 contract 成熟度 |
| mqtt-console 的 `environments.md` 图例 | ⚠️ 存量 | 图例复现了 `⚠️ 待定` 字面量 ⇒ `env_pending` 报 3/10（真 2）。修已进骨架，**存量文件下次 `continue` 自愈** |

---

## ▶ 下一阶段建议

### 1. ⭐ 优先：`add-codex-host-support`（已与用户对齐，紧接着开）

**Codex 宿主下有两个会记账的假绿**：

- **outside-voice 自审**：`outside-voice.sh` 无条件 `codex exec` ⇒ 在 Codex 里是 **GPT 审 GPT**，却仍落 `runner="codex"` 锚、被 lens-metric 当成一个独立镜计入采纳率
- **`runner` 枚举是「以 Claude 为宿主」硬编码的**：折叠表 `codex → outside-voice`，于是 Codex 宿主下**普通领域镜会被折成 outside-voice**；而真 voice（Claude）会被 `outside_voice_guard.py:93` 的 `!= "codex"` 跳过 ⇒ 判 zero-findings ⇒ 重复跑

**已查清的事实**（不用再查）：

| | |
|---|---|
| 宿主正信号 | Claude = `CLAUDECODE=1` · **Codex = `CODEX_THREAD_ID=<uuid>`** |
| 反向 runner | `claude -p --model opus --output-format text --disallowedTools Write Edit NotebookEdit < prompt` —— **冒烟过了，5.8s 拿到最终文本** |
| Codex 三档 | `gpt-5.6-sol`（强）/ `gpt-5.6-terra`（中）/ `gpt-5.6-luna`（弱） |
| Codex 能否逐子代理指定 model | **能** —— `spawn_agent` 的 `model` 字段（+`reasoning_effort`）。但它默认劝阻：*"Do not set the `model` field unless … there is a clear task-specific reason"* ⇒ **我们的 model-tiers 就是那个 reason，须在 skill 里写明** |
| ⚠️ **Codex 默认不派子代理** | *"Do not spawn sub-agents unless the user or applicable **AGENTS.md/skill instructions** explicitly ask"*，且 *"requests for depth, thoroughness, research … **do not count**"* ⇒ **多镜评审可能静默退化成单镜，而报告照样写「7 镜」** |

**推荐设计**（用户已认可方向）：
- **宿主判定归脚本**（有确定性信号 = 环境变量 ⇒ 基准 1）：`resolve-models.sh` → `eval` 出 `HOST` / `TIER_STRONG|MID|LIGHT` / `VOICE_RUNNER|VOICE_MODEL`，SKILL.md **只引用变量名**，不读一张表自己判宿主
- **不变式**：**outside voice = 另一个机队的强档**（Claude 宿主 → Sol；Codex 宿主 → **Opus**）
- **`runner` 枚举收缩为 {claude, codex}**（只记家族），**锚行加 `host=`**；跨模型性 ⟺ `runner ≠ host`。`claude-fallback` 废弃（旧锚兼容：⇒ `host=claude, runner=claude`）
  - **为什么不用「加个 `claude-voice` 值」**：每支持一个新宿主就往枚举里加两个值 = **基准 5 的警号**（每轮补一个新分支 = 这个设计本来就不对）
- **AGENTS.md 级显式授权 spawn sub-agents**（否则 codex 拒派）
- 判不出宿主 ⇒ **fail-loud**，锚标 `host="unknown"`，voice 如实标降级——**宁可标 fallback，也不冒充跨模型**

### 2. 次优先

- **注入点 B 的产出从未被度量**（`lens-metric` 只覆盖 spec-review / code-review 两层）⇒ 砍不砍只能凭感觉。建议给它落锚，攒几轮看采纳率再决定
- 消费仓需跑 **`sdflow-init update`** 才拿到三条通则 + ff→grill 交棒规则 + `WORKFLOW-GUIDE.md`（`workflow.md` / `prompts/` 走全局 canonical，**即时生效，无需 update**）
- 回灌 `references/`（Minor）
