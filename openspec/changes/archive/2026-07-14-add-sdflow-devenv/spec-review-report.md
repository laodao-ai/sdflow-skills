---
ship-gate:
  design_approved: false
---

<!-- ⚠️ round-3 的 design_approved: true 已【主动撤销】——它审的是 A21/A22 之前的 spec。
     本轮（round-4）spec/design/tasks/plan 四件套已大幅改写，且有 4 条待拍板项（Q1–Q4）。
     设计门须重新拍板；拍板后由主 session 把本值改回 true。round-3 报告存于 git 历史。 -->

# spec-review-report — add-sdflow-devenv（**round-4 设计审**）

> **一句话**：**病都真，药大半有毒。**
> A21/A22 的**拆解方向站得住**（四声广审 + 三个对抗镜均未证伪），**但拆得不彻底**；而**本轮评审自己提出的修法里，有三条是「面治优先于点补」这个元病的第五、六、七次复发**——用一个新机械补一个点，而那个新机械自己的失效面比它拦的更宽。
>
> **共同解药与 A21 的一般化规则是同一条**：**让已经在跑的那个工具自己回答** + **用 txn journal 已经记下的事实**。**评审提出了这条规则，却没在自己的修法上用。**

**审查基准（操作者 2026-07-14 给定）** · §0.1 目标：**不是产出两份文档，而是建立环境** · 核心承诺：**不管什么项目**，三层不留白 · §0.0：机械层**防漏不防伪**。

**规模** · Step1 广审四声（CEO / Eng / DX / Codex-outside-voice）**46 条** → Step2 四镜（对抗 ×3 + 接地）**逐条证伪** → Step3 主 session 对抗裁决，含 **4 次机械实证，其中 2 次推翻了主 session 自己的方案**。

<!-- sdflow:step1-broad-review v1 mode="native" -->
> **Step1 广审**：autoplan 经 Skill 机制**原生执行**（非子代理转述模拟）。侧信道佐证：preamble 实跑（`BRANCH=feat/add-sdflow-devenv` · `REPO_MODE=solo` · `CODEX: AVAILABLE`）· Phase 0.5 codex preflight 通过 · 双声真实调用（Claude 冷子代理经 Agent 工具 · Codex 经 `codex exec -s read-only`）。findings 全文见 `gstack-review.md`。
> **outside-voice guard = `stale`**（前身为 round-3 产物 07-13，而 spec/07 已改至 07-14）⇒ **回落自跑 design-voice**，未复用陈旧 codex 结论。

---

## 决策登记区

```
┌───────────────────────────────────────────────────────────────────────────┐
│ [需拍板] Q1  §0.0 第一原则：修补(三道闸门入 spec 总则 + 删错误地基)          │ ★ 地基级
│ [需拍板] Q2  C5(a) 16 槽零载体：加第三份 JSON  vs  收窄 spec:537            │ ★ critical
│ [需拍板] Q3  路线顺序：是否停 Task 5+，先手跑验 A-8（零脚本，一个下午）       │ ★ 战略级
│ [需拍板] Q4  Windows：v1 支不支持（无论支不支持，现在这条路由都是错的）       │
│ [自动决策] D1–D9  高置信 + 修法已过三道闸门，默认采纳                        │
│ [已裁掉]  X1–X4  reviewer 原始发现 + 裁掉理由（反静默压制，供复核裁得对不对） │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## ★ Q1 · §0.0 第一原则 —— **修补，不推翻。机制零改动。**

**两个对抗镜表面对立，实则互补——它们看的是不同的文件。主 session 已机械核实：**

| | 第二问（代价：这个保证服务谁） | 数据问（承载 X 的字段在哪） |
|---|---|---|
| **`07` 附录** | ✅ `:820-823` | ✅ `:812-816` |
| **`spec` 总则** | ❌ **全文 grep「服务谁 / 它拦住的失效」零命中** | ❌ 只在 `:232-234`（A22 的 Requirement **内部**），**不在总则** |

⇒ **镜 A 的「实质增量 ≈ 0，是最贵的假阳」错了**——增量不在 `07`（那里确实有），**增量在 `spec` 总则**。而 **spec 是实现契约**，`07` 是设计文档。**下一个实现者读的是 spec 总则，那里只有一道闸门。**

**更要命的是 `spec:11` 总则里赫然写着**：

> 「…**且本就不必防**（使用者就是那个人自己，**他没有动机骗自己**）」

**镜 C 逐条核过 A13–A20 的实际死因，这句话承重为零**：

| 方案 | 真正的死因 | 用到「没动机骗自己」了吗 |
|---|---|---|
| A13 negative control | 信号只证「命令耦合依赖」，**不证「断言有效」** | **没有** |
| A14 测试计数门槛 | **`assert True` 完美满足它** | **没有** |
| A16 `owned_by` 派生 | **那个锚根本不存在** | **没有** |
| A17 cleanup ledger | 锚缺失 + 容器不在子进程组 | **没有** |
| A18 confirm-lane 身份 | **机械上不可区分**（「且本就不必防」是叠在后面的**冗余**第二理由） | 叠了，**但冗余** |
| A19 `method_digest` 可达 | 跨语言 import 图**零依赖做不到** | **没有** |
| A20 Markdown 解析器 | 手搓解析器前科 + **奖励空话惩罚诚实** | **没有** |

**§0.0 用一个对的结论，配了一条不成立、且不承重的理由。** 正因为理由不成立，它才必须在 `spec:208` 为自己最核心的机制写一句辩解——**那不是话术，是错误地基硬撑正确机制留下的应力裂纹**。

**两镜独立同意的核心判断（论证互补，都硬）**：

> **`set-lane --status verified` 一律拒绝，不是防伪。**
> - 〔镜 A〕它对撒谎模型**零抵抗力**——模型可以直接 Write `.devenv-lanes.json`（仓里一个普通 JSON，无签名无校验和），或走 `confirm-lane` 声称人工验证过（**A18 自己承认**：agent session 里模型是唯一执行者）。
> - 〔镜 C〕`verification.method` **由模型写**。把它设成 **`true`** 三个字符，`verify-lane` 忠实 fork、拿到 exit 0、盖 `verified`。
> - ⇒ **一个一步就能绕过、三个字符就能击穿的机制，不可能是防伪机制。** 它是**防漏**，且是最纯粹的那种：**脚本不是审计者，是执行者**——exit code 不是「待查证的证据」，**是它自己动作的返回值**。

**正确的轴线，文档自己已经写出来了**——`07:434`：

> 「凡是机械层想知道某个 make/shell/语言构造是什么意思的地方，正解都是**让那个工具自己回答**（真跑一遍）……**跑一遍，就是最强的解析器**」

**这句话被归档成 A21 的脚注，但它就是 §0.0 的一般形式**：不要**审计**（解析器猜 make 的意思），要**亲手做**（让 make 自己跑）。它同时切开了「防漏/防伪」切不开的那一格——**同一个命题「这个 `verified` 是不是真跑过」：脚本跑的 ⇒ MUST 保证（by construction）；模型跑的 ⇒ MUST NOT 试图保证（by audit，无信号）**。

### 拟议动作（**机制、字段、lint 断言、Scenario 全部不动**）

1. **`spec` 总则 + `07` §0.0 换地基论证**：**删「他没有动机骗自己」**；改为「**机械层没有能力审计任何证人**（A16 锚不存在 · A18 机械上不可区分 · A19 零依赖做不到 · A13 信号不区分目标失效）⇒ **所以它只做自己亲手做得到的事**」。
2. **三道闸门写进 `spec` 总则**（**A22 纪律的自指应用**：规范层自己也要有承载）：
   - **① 信号问**：信号从哪来？**且它必须能区分我要拦的那个失效模式**——「存在某个客观信号」**不算过**。
     > ⚠️ **这半句是一票否决权，MUST NOT 省略。** 反例 A14：`collected≥1 ∧ 0 skipped` 有货真价实的信号，**但 `assert True` 完美满足它** ⇒ 零拦截力。
     > **镜 C 的警告**：CEO 原提议的三问闸门**若不带这半句，会亲手把 A14 放回来**（它有真信号 · 服务「给模型反馈回路」· 看着便宜——三问全过）。**复活链可预测**：`verify-lane → 校验 method 非 trivial → runner 白名单 → A14`。
   - **② 数据问**〔A22〕：在数据模型里**指出承载 X 的那个字段**。指不出 ⇒ 加字段或删 MUST。
   - **③ 代价问**〔A21〕：这个保证**服务谁**（用户的产出 vs skill 的账本）？它拦住的失效×频率×代价 vs **它自己引入的**，哪个大？
3. `07:693`「脚本对到底跑没跑**零独立证据**」这句**防伪腔措辞收敛**（它与紧接着的 `:694` 自相矛盾，**是 CEO 镜误读的来源**）。

---

## ★ Q2 · `environments.md` 的 16 槽**零数据载体**（critical，**镜 A 专门去证伪它，抗辩失败**）

`spec:537` 原文：「`environments.md` / `testing-strategy.md` **由脚本从这两份 JSON 渲染**，**MUST NOT 由人手写**」——**主语是整份 md**。而两份 JSON 只有 `lanes[]` + `layers{}` + `known_blind_spots` ⇒ `07:252-260` 那 16 槽里，除「各层执行命令」可从 lanes 渲染外，**前置工具链 / 本地依赖服务 / 构建副产物 / 常见坑 / 测试选择路由 / CI 环境 / fixture 策略 / 目标平台 / 配置项清单 / 发布流程 / 回滚 / 架构决策指针 —— 全部零载体**。

**两条更硬的证据**：
- `spec:667`「`不适用` 槽 SHALL 连带记录后果」——**这句话预设 environments.md 有可判「不适用」的槽，而那些槽在数据模型里不存在。**
- `spec:46-48` 事实采集**强制向人提问** CI 平台 / 团队机器可用依赖 / 部署形态 —— **问到的答案没有任何地方可落。**

**「那是人写区」的抗辩不成立**：`07 §4.1` 把「**槽完整性**」列为「AI 全自动（机械）」——**要机械查槽完整性，槽就必须落结构化数据**，否则就是 **A20 亲手枪毙的手搓 Markdown 解析器**。

**根因 = `07` 与 `spec` 不一致**：`07:144` 只说「**正文那张命令表**由 render 渲染」（**局部**），`spec:537` 泛化成了**整份文件**（**全局**）。

**二选一（现状是两者的坏组合：声称整份机械渲染 + 没有载体 ⇒ 实现期只能丢弃信息或现场编造）**：

| 方案 | 后果 |
|---|---|
| **(a) 加 `.devenv-environment.json`** 承载 16 槽 + 事实采集结果 + `not-applicable + consequence` | `spec:537` 成立 · 槽完整性可机械查 · **但数据模型再长一截**（第三份 JSON） |
| **(b) 收窄 `spec:537`** 为「**命令表 / 泳道状态表两个托管块** MUST 从 JSON 渲染，其余为模型起草的散文」 | 数据模型不变 · **但「槽完整性」lint MUST 一并删除**，归人门 + 冷审 |

---

## ★ Q3 · A-8 是**零实证的前提**，却是 15 个 Task 的地基（战略级）

`proposal:165` / `tasks:460-461` **自己写明**：「若模型连给出『有方向』的验证方法都做不到，**这道语义防线就无米下炊，§0.0 总则本身站不住**」。
而 `tasks:66-68` 用「**鸡生蛋**」把验证它推到实现之后：「只能靠跑这个 skill 才能验证，而 skill 还不存在」。

**这个论证是错的**：核心承诺的智力载体是 Task 13/14 的 **prose**——**不需要任何脚本就能手跑**（拿一个真实项目 + 一段 prompt，看模型给出的三层验证方法经不经得起推敲）。「只能靠跑 skill 验证」是**把 skill 等同于它的 Python 部分**，而 Python 部分（containment / lock / digest）**与 A-8 完全无关**。

**接地镜的核验加重了这一条**：`sdflow-devenv/` 至今**只有 `scripts/` + `tests/`** —— **`SKILL.md` 不存在，`references/` 不存在**。已烧掉的 4 个 Task 全是基础设施（**659 行脚本 + 987 行测试**），而**核心承诺的载体一个字都没写**。

**建议**：**停 Task 5+，先写 Task 13/14 的 prose，在一个真实项目上手跑一遍**（零脚本），一次性验掉 **A-8 + 「命令虚构」+ lane-patterns 第二样本**三个未验证前提。**成本 ≈ 一个下午。跑完再决定基础设施要哪些、要多少。**

---

## ★ Q4 · Windows：v1 支不支持（**无论支不支持，现在这条路由都是错的**）

`spec:287` 把「非 POSIX」列为「**方法本身没法用程序跑**」，与「真硬件烧板 / UI 视觉判断」并列 ⇒ `executor: human`。

**但 `go test` / `npm test` / `cargo test` 在 Windows 上完全跑得了**——跑不了的是 **skill 自己的进程树杀灭实现**。把它标成 `executor: human` + `why_not_scriptable`（内容只能是「本 skill 不支持该平台」——**那不是「方法」的属性**），**正是 spec 在同一张表上方亲手禁止的混淆**（`spec:146-153`：「本机缺依赖也被标成只能人工验证 ⇒ **那是在撒谎**」）。

**修（二选一，但 `executor` MUST 保持 `script`）**：
- **(a)** 落 `scaffolded + blocked_by`：「本 skill v1 不在 Windows 执行验证（进程树杀灭未实测）——可在 WSL/CI 跑 `<cmd>` 后 `confirm-lane`」；
- **(b)** 照跑 + 清理降级 best-effort + **如实告知可能留下孤儿进程**（**与既有孤儿资源话术同型，零新机制**）。
- **且降级时机 MUST 前移到 preflight**（现在 refuse 发生在**落地物已写完、③-pre 已过之后** ⇒ 投入全部浪费）。

---

## D · 自动决策（高置信 + 修法已过三道闸门，默认采纳；设计门可覆盖）

### D1 · 时效锚**第三个洞**（假绿，**主 session 已实证**）—— 修法**换成明文快照**

```
验证时 evidence.file_digests 键 : ['Makefile', 'old_smoke.go']
攻击：lane.smoke 改指 new_smoke.go（old_smoke.go 一字未动）
stale_files() 返回             : []      ← 未失配 ⇒ verified 继续挂着
```

`stale_files()` 只遍历 `evidence.file_digests` 的**旧键**，**从不与当前 `_tracked_paths(lane)` 对账**。同理适用于 `source.file` / `selector` / `fixtures[]` / `env[]` / `deps[]` 的**任何声明变更**；**且「事后补声明 `fixtures`」是 continue 模式的主路径**。

**根因（自指）**：A21 补 `method_at_verify` 时**只接住了「method 字符串」这一块**，没接住**整个 verification plan 的声明面**——**A22 纪律在自己身上没执行。**

**✅ 采纳（镜 B 方案，优于原提议的 digest）**：
- ❌ **不要 `plan_digest_at_verify`（digest 形式）**。**镜 B 实证**：naive 复用 `plan_snapshot()` 会让**每条 verified 泳道永久报过期**——`status` 在 `SNAPSHOT_KEYS` 里，而验证成功后 `status` 必然 `scaffolded → verified`。要躲开就得维护**第二套几乎相同的 key 元组** ⇒ **正是本仓刚在 `_CONTENT_SLOTS` 上防的漂移病**。
- ✅ **存明文快照** `evidence.plan_at_verify = {method, executor, kind, source, smoke, fixtures(sorted), env(sorted), deps}`，lint 做**字段级 diff**。
  **理由**：digest 失配只能报「验证计划已改动」——**不可辨认的提醒 = 没有提醒**（DX 自己立的判据）；**明文能报「`smoke` 从 X 改成 Y」**。成本相同，且**天然规避 list 顺序假失配**。**它是 `method_at_verify` 的超集**（吸收之，不再逐字段补洞）。
- **覆盖面 MUST NOT 含** `status` / `covers` / `layer` / `strength` / `blocked_by` ⇒ **补 `covers` 锚、修 typo 不会误失效**。

### D2 · `append` **静默 override 用户 target**（**主 session 已实证**）—— **make 探针否决**，改用**已经在跑的那次执行**

**病是真的**（实证：make 打 `warning: overriding commands`，**实际跑的是 skill 追加的那条，用户原来的静默失活**）。我在 `07:754,798` 写的「**最坏后果是多一条定义，不删不改人的东西**」**在 GNU make 语义上是错的** ⇒ **「接受漏判」的唯一定价依据是错的。**

**但我上一轮提的「make 探针」修法必须撤回——主 session 实证它不是只读操作**：

```
① VERSION := $(shell echo … > /tmp/PWNED.txt)   → make -n  🔴 EXECUTED（解析期求值，-n 不阻止）
② include generated.mk + 其 remake 规则          → make -n  🔴 真把 generated.mk 【写进了仓库】
                                                    ← 不在 txn journal ⇒ ③-pre 否决时【回滚不掉】
                                                    ← 击穿「MUST NOT 破坏操作者机器状态」最高红线
③ include required.mk（缺失）
   → "make: *** No rule to make target `required.mk'.  Stop."
                                                    ← 与「target 不存在」【输出/退出码同型】
                                                    ← fail-closed = 复杂 Makefile 罢工（A21 复活）
                                                      fail-open  = 恒真断言 = 假绿。【两条路又都错】
```

**且探针发生在 ③-pre 人门之前** ⇒ 它会**在人批准之前执行用户 Makefile 里的 `$(shell …)`**（镜 A / 镜 B 独立抓到）。

**✅ 采纳（镜 B 方案，零新执行）**：**`verify-lane` 本来就要真跑 `make <selector>`，make 自己会把 `overriding` warning 打到 stderr。**

> `verify-lane` **MUST 捕获 stderr**；出现 `overriding … target '<本 lane 的 selector>'` ⇒ **fail-closed 报重名冲突 + 按 txn journal 回滚本次 append**。
> **信号** = make 自己的输出（**这才是 A21「让工具自己回答」的字面执行**）· **服务谁** = 用户的构建行为（不是 skill 的账本）· **引入什么** = **无**（verify-lane 已经在 fork make、已经在收输出）。**成本 ≈ 5 行。**
> **这一条是承重的**：不抓它，`verify-lane` 会在「用户 target 已被静默杀死」的 Makefile 上**跑出绿灯**。
> **残余**（append 后从未被 verify 的泳道）⇒ 归 ③-pre 人门 diff，**如实登记为诚实边界，MUST NOT 宣称 100% 覆盖**。

> **⭐ 给 A21 的两个补丁（本轮最重要的方法论产出）**
> 1. **「让工具自己回答」≠「为了问它而额外造一次执行」** —— 正解是**在已经发生的那次执行里读信号**。（实证：为检测而跑 `make -n`，会执行 `$(shell)` 并往仓库写文件。）**我提的探针恰恰是 A21 反对的东西的变体。**
> 2. **「让工具自己回答」≠「工具给出绝对真理」** —— make 的 target 集合是**变量环境的函数**：「这个 Makefile 里有没有 X target」**没有环境无关的答案**。**诚实边界依然存在，MUST NOT 因为「问了 make」就宣称 100% 保证。**

### D3 · skill 自己写的 smoke 会**把用户的绿测试套件搞红** —— 问题成立，**修法换掉**

**病真**：Go/Rust/TS 里一个编译不过的测试文件会让整个 package 的 `go test ./...` 直接红 ⇒ **用户跑 skill 之前测试是绿的，跑完之后他原有的测试套件挂了**。**「不伤害」红线（`spec:275`）只覆盖机器状态，不覆盖仓库可测状态。**

**非 A11 复活**（两镜独立同意）：A11 否的是「**debug 到通**」；这里说的是「**skill 自己拉的、编译不过的文件要不要留在用户仓里**」——**A11 的论证对后者一个字都没覆盖。两件事正交。**

**❌ 原提议的「编译失败 vs 断言失败」分类否决——两镜独立判定为 A14 复活**：
> `go test` 构建失败与断言失败**同为 exit 1**；`cargo test` 两者均 101；jest 均 1。要可靠分类**只能建 per-runner 输出解析 dispatch 表** ⇒ **正是 §0.0 明令禁止的「枚举 / dispatch 表 / 白名单」**，与 A14 死因**逐字同型**。
> 「一次修复重试」也否决：① 与 `spec:294` R4 正面冲突 ② **重试写出的新代码没有任何人看过就被执行了** ⇒ **击穿 ③-pre 存在的全部理由**。

**✅ 采纳（有信号、零解析器；(i) 首选，可与 (ii) 叠加）**：
- **(i) 结构隔离（最强）**：「**skill 新写的 smoke MUST 落在默认测试命令跑不到的位置**」（build tag / 独立 package / 独立 target）写成 Requirement ⇒ **编译失败在结构上不可能污染用户的默认测试命令**。**零判断。**
- **(ii) baseline 差分**：写落地物**之前**跑一次用户既有测试命令记 exit，写完再跑一次；**green → red = 确定性信号**（**不需要知道「为什么红」**）⇒ 按 txn journal 回滚该文件 + 如实写 `blocked_by`。**仍然不 debug、不重试、零 runner 知识。**
- **MUST NOT 默认自动回滚**（`scaffolded` 本就是合法态，自动删脚手架会砍掉渐进 DoD）⇒ **收尾报告显著呈现「我新写的 `<file>` 未通过验证，它可能让你既有的 `go test ./...` 变红」+ 给一键回滚**。**「不伤害」的落点是让人看得见并能撤销，不是让脚本自动分类。**

### D4 · R3「跑前 MUST 展开 recipe」与 best-effort 实现**骑墙** ⇒ 复杂 Makefile 上系统性落空

`spec:289` R3 是**防 `rm -rf` / 防偷起容器的唯一措施**，而我刚写的 Task 4.12 规定提取 **MUST 是 best-effort**、遇 `ifeq`/`define` **降级为「请查看 `<file>`」** ⇒ **凡 A21 列举的那些真实写法，R3 恒不满足** ⇒ 人拿到的**正是那个「零信息量的一行」**，橡皮图章原样发生。**MUST 与实现手段之间是空的**（A22 病型）。

**`make -n` 作展开手段随 D2 一并否决**（同样的 `$(shell)` 前置求值 + include remake 写盘）。

**✅ 采纳**：R3 降级为「MUST 展开 **或** **MUST 响亮告知「本次执行的内容未经展示」并展示整份 `source.file`**」——**降级路径必须让人看见自己在盖橡皮图章**，而不是给一行「请自行查看」就当交差。

### D5 · 悬空 MUST 家族（**A22 纪律未面治**）—— 逐条「加字段 or 删 MUST」

| # | 悬空的 MUST | 处置 |
|---|---|---|
| (a) | **`environments.md` 16 槽** | **→ Q2 拍板**（critical） |
| (c) | 泳道拍板的 **mock 边界 / 最小可用集**（`spec:124-126`） | lane 加 `purpose` / `mock_boundary` + 顶层 `minimum_viable_lane_ids` |
| (d) | **lane 级 timeout 覆盖 + 实际用值写进 evidence**（`tasks:199-200`） | 加 `verification.timeout_seconds` + `evidence.timeout_seconds_at_verify`，**或删掉这两条 MUST** |
| (e) | **`blocked_by` MUST 含「可辨认修复指引」** | **见 D6（修法必须收缩）** |
| **(f)** | **§0.3「模型 MUST NOT 预判『大概跑不了』就标 `human` 偷懒——先试着跑」**（`07:90` / `spec:143`） | **新增（镜 A 发现）**：lane 加 **`last_attempt: {at, exit, method}`**，**只能由 `verify-lane` 脚本自己写**。**「压根没试」与「planned」现在在数据上不可区分。** |
| **(g)** | **`lane_ids` 指向的泳道 MUST 存在且 `status ∈ {scaffolded, verified}`**（`spec:504` + Scenario `:110-112`） | **新增（接地镜发现）**：代码只做 truthy 检查 ⇒ 挂空壳 / 指向不存在的 id 都能过。归 Task 5 lint（跨文件 join） |

### D6 · `blocked_by` 结构化 —— **收缩**（原提议「三键均须非占位」= **A20 原样复发**）

**镜 B 抓到的致命处**：spec 与 `07` **亲自钦定**过一种合法且诚实的 `blocked_by`——

> `spec:285` / `07:566`：「**超时，未确认是环境问题还是 smoke 本身挂了**」

在「`why` / `fix` 均 MUST 非占位」之下，这句话的 `why` **只能填「未确定」⇒ 命中占位符黑名单 ⇒ lint fail-closed ⇒ 模型被迫编一个假 why 和假 fix**。**机械层奖励空话、惩罚诚实——A20 就是为杀这个而否的。**

**✅ 采纳收缩版**：`symptom` 必填 · **`why` MUST 允许显式 `unknown`** · `fix` 允许是「**下一步诊断动作**」而非「修法」。**且 spec MUST 写明：三键只保证有三个格子，不保证内容有用**（归人门 + 冷审）——否则 lint 的 `structure-ok-SEMANTICS-UNCHECKED` 后缀**在这一项上就是在撒谎**。
> **零成本等价物**（若嫌 schema breaking）：保持 `str` + 在 `references/` 给一个「症状 / 原因（可为未确定）/ 下一步」的**模版**。**评审自己写了「防敷衍靠示范比靠黑名单有效一个数量级」——那就别再加黑名单。**

### D7 · 「不管什么项目」的**罢工面**（核心承诺回归守卫）

- **封闭枚举 fail-closed**：`lane.kind` / `deps[].kind` 是封闭枚举 ⇒ **云账号 / 远程 SaaS / K8s / 模拟器 / GPU / 移动设备**无法归类 ⇒ **schema 直接拒绝，「未覆盖形态临场推导」的承诺无处落盘**。**这是 A21 同类病：一个枚举 = 一类项目被拒之门外。**
  **✅ 修**：这些字段**本就不参与机械 dispatch、本就在 spec 自己的「无独立信号」清单里**（`:569`）⇒ **改为非空字符串**，或 `other` + 必填 `kind_description`。
- **`fixtures` 声明为目录 ⇒ 直接炸**：`read_bytes()` 对目录抛 `IsADirectoryError` ⇒ verify 时**未捕获直接崩**；`stale_files` 记成**永久失配**。**✅ 修**：显式二选一（fail-closed「MUST 是文件」**或**递归 digest），**别留给实现期发明**。
- **完成门**（原 C1）：**不违反 A4**（A4 否的是「**全** verified」，本条只要「**有一条被真的试过**」；失败 / blocked / 缺依赖全部合法）。**但「已有可执行代码的项目」这个前置无信号** ⇒ **又一个封闭枚举罢工面**（**正是 C3 自己在骂的病**）。
  **✅ 采纳收缩版**：**删掉该前置**；改为**无前提的呈现型 MUST**——「**收尾时若零条 lane 有 `last_attempt` ⇒ 报告 MUST 显著呈现『本次未执行任何验证』**」；确实无法尝试 ⇒ **显式声明 + 记后果**（**与三层框架「`不适用` 连带记后果」同一条纪律、同一套机械，零新机制**）。

### D8 · 坏输入 / 校验漏网（**实测**，纯防漏，全部有确定性信号）

- `validate_lane` **不校验 `source` / `smoke` / `fixtures` / `env` / `covers`** ⇒ 实测 `fixtures: "testdata/b.conf"`（str）会让 `set.update(str)` **逐字符展开成 15 个垃圾路径**；`source: "Makefile"`（str）⇒ **`AttributeError` 裸奔逃出 `PathEscape` 契约**。**修**：补类型校验（`fixtures`/`env`/`covers` 须 **list of str**，**显式拒绝 str**）。
- **`evidence.exit` / `attested_by` 零校验** ⇒ 实测 `verified` + `exit: 1` + `executor: human` 但 `attested_by: "script"` **零错误**。而「`human-attested` 的绿 MUST 与脚本验的绿可区分」**整条依赖 `attested_by` 的正确性**。**修**：按 executor **分支**定义证据 schema（script ⇒ `at` / `exit==0` / `attested_by=="script"`；human ⇒ `at` / `confirmed_what` / `attested_by=="human"`）。**⚠️ `exit` 不能用 `if not ev.get(k)` 查**（`exit: 0` 会被判为「缺失」）。
- **`output_digest` 无任何消费者**（`method_digest` 时代的遗物）⇒ 按 A22 纪律 **删，或诚实降级为「给人事后核对的坐标」**。
- `known_blind_spots` 零校验 · `attested_by` 无枚举校验 · `_is_placeholder` 对非 str 一律返 True（`method: 123` 报「为空」，**误导**）。

### D9 · 事务 / 并发（**红线**）

- **txn journal 缺 `post_write_digest` ⇒ 回退会覆盖人的改动**：崩溃后、下次启动前**人很可能已手动改过那些文件**（崩了，人自己去改 Makefile）⇒ 按 journal **盲目回退 = 用旧内容覆盖人的新改动**。**这与 `spec:471` 自己批判 `git clean`「最后一道护栏内部自带破坏性操作」完全同型。** **修**：journal 每项加 `post_write_digest`，回退前逐文件比对，不符 ⇒ **拒绝自动回退**，列冲突文件交人。
- **陈旧锁判定不查 pid liveness**（`pid` 写了从不读）⇒ 活锁超 120s 被误判残留 ⇒ 提示删锁 ⇒ **两 session 同写**（**正是 `spec:711` 自己说的「陈旧锁检测由保护变成攻击面」**）。`os.kill(pid, 0)` 是确定性信号，**3 行**。
- **`_save` 无锁且无护栏** ⇒ 不防 lost update（**单 lane 的 CAS 保护不了整个文件**）。**修**：把 `write_lock` 收进 `save_*` 内部，**别把纪律留给调用方记**。

---

## X · 已裁掉（**反静默压制**：原始发现 + 裁掉理由，供设计门复核「裁得对不对」）

| # | 原始发现 | 裁掉理由 |
|---|---|---|
| **X1** | **「推翻 §0.0 第一原则」**（CEO，标 critical） | **不推翻。** `set-lane --status verified` 拒绝**不是防伪**（对撒谎模型零抵抗力 / 三个字符可击穿——**两镜独立同结论**）⇒ `07:694` 的辩解**成立，不是话术**。**机制一条不改。** **但降级 ≠ 驳回**：其**实质内核**（**spec 总则缺闸门 + 错误地基**）**已升格为 Q1 采纳**。 |
| **X2** | **`sad` / `mode` 零数据载体**（Codex / Eng，标 high） | **假阳。** 载体存在 = `environments.md` frontmatter 的三个**扁平标量**（`spec:537` + `07:149` 明写，**刻意留扁平就是为了能被 `parse_frontmatter` 读回**——设计的**显式取舍**）。**残余真问题降为 low-medium**：spec 未定义 render 的 **round-trip 读回路径**（`environments.md` 是 DO-NOT-EDIT 全渲染产物，而 `sad`/`mode` 的唯一持久副本**就在这份被覆盖的文件自己的 frontmatter 里** ⇒ **render MUST 先读回自身 frontmatter 再重写**）。 |
| **X3** | **「A2 纯文档编排器复活」这个定性**（CEO / Codex，标 critical） | **修辞夸大，降级。** A2 是「**设计上决定不落脚手架**」；现设计**仍落脚手架**，degenerate case 是「**未被守住**」而非「**被批准**」。且已有半道守：`layers.status: implemented` ⇒ `lane_ids` 指向的泳道 MUST ∈ {scaffolded, verified}。**全 `planned` 只在三层全 `manual`/`not-applicable` 时才合法——那是诚实的（纯人工测试项目），不是 A2。** **但底下的真缺陷成立**（§0.3「先试着跑」无承载字段）⇒ **已并入 D5(f) + D7 采纳。** |
| **X4** | **C6 的「静默」与「击穿最高红线」措辞**（severity high） | **降为 medium-high。** ③-pre 人门 MUST 展示「新写落地物 diff **全文**」⇒ **追加的 target 用户看得见**；make 在运行时也会打 `warning: overriding commands` ⇒ **破坏并非不可发现**。准确表述是「**冲突事实未被告警**」（diff 只显示「新增了 `integration:`」，**不会告诉你「你 `ifeq` 块里那条同名 target 从此失活」**），**不是「写入是静默的」**。**病本身维持成立**（错误的定价依据 = 真缺陷）。 |

---

## 元发现（**本轮最重要的产出**）

**「面治优先于点补」（CLAUDE.md 基准 3）在这个 change 上被违反了七次：**

| # | 违反 | 谁发现的 |
|---|---|---|
| 1 | **A22 的纪律**（先指认承载字段）**只在两处执行** ⇒ 至少 **6 处悬空 MUST** 仍在 | Codex · Eng · DX · 接地镜 |
| 2 | **A21 的一般化规则**（让工具自己回答）**只在 `verify-lane` 一处兑现** ⇒ append 侧（**写用户文件**）与展示侧（**安全护栏**）仍留正则 | Eng · Codex |
| 3 | **A21 的第二问**（这个保证服务谁）**只用在 make parser 一个点上** ⇒ 未扫过整个机械面 | CEO |
| 4 | **A21 的补口只接住了 `method` 字符串** ⇒ **整个 verification plan 的声明面掉出时效锚**（**已实证假绿**） | Codex · Eng |
| **5** | **本轮修法：make 探针** —— 为补 append 的漏判，引入 **4 条代码执行向量** + 一个新罢工面 | **对抗镜 B**（**推翻主 session 自己的方案**） |
| **6** | **本轮修法：「编译 vs 断言」分类** —— 为补 C4，**复活 A14 的 runner 解析器** | **对抗镜 A + B（独立收敛）** |
| **7** | **本轮修法：「已有可执行代码」前置** —— 为补 C1，**复活「封闭枚举拒收一类项目」**（**正是 C3 自己在骂的病**） | **对抗镜 A + B（独立收敛）** |

**第 5–7 条是本轮评审自己制造的。** 三条的共同解药，与 A21 的一般化规则**是同一条**：

> **让已经在跑的那个工具自己回答**（`verify-lane` 的 make stderr）· **用 txn journal 已经记下的事实**（「这文件原先存在吗」）· **baseline / 反事实的一次 exit code 比对**（**零 runner 知识**）。
>
> **评审提出了这条规则，却没在自己的修法上用。**

---

## 收敛口

**MUST NOT 进设计 HARD-GATE。**

本轮有 **4 条需拍板项**（Q1 **地基级** · Q2 **critical 且二选一** · Q3 **战略级路线顺序** · Q4 平台），且 **D1–D9 的修法会改动数据模型**（新增 `plan_at_verify` / `last_attempt` / `purpose` / `mock_boundary` / 可能的第三份 JSON）⇒ **四件套需要一次实质修订，代码需返工 Task 3/4 的 schema 与 digest**。

**建议顺序**（承 Q3 + 接地镜实证：**`SKILL.md` 与 `references/` 至今零字**）：

1. **拍 Q1–Q4**（地基 / 载体 / 路线 / 平台）。
2. **先做 Q3 的手跑实验**（零脚本，一个下午）—— **它可能改变后面所有 Task 的 scope**。
3. **据实验结果重定基础设施 scope**，再改四件套 + 返工代码。

---

## lens-metric（度量锚 · 门前草稿值，拍板时最终化）〔SR-M〕

> **诚实边界**：分类正确性（某条 finding 该归哪个 lens）+ roster 完备性 + findings 誊写准确，
> 仍是主 session 的信任边界；emitter 只保证「给定输入的确定性归约」，不保证输入本身对不对。
> **`独立` = 唯一报过 ∧ 被采纳。** 本轮 `broad` 独立仅 2 —— 广审四声高度收敛（同一批病被多声独立命中），
> 而 **`adversarial` 独立 3 / 3 采纳**：本轮对抗镜的产出全部是「广审没看见的」——**其中两条推翻了主 session 自己的方案**。

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="4" 采纳="3" 裁掉="0" defer="1" 独立="3" sev="致0/高3/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="10" 采纳="5" 裁掉="4" defer="1" 独立="2" sev="致2/高3/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="2" sev="致0/高0/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="6" 采纳="4" 裁掉="1" defer="1" 独立="1" sev="致2/高2/中0/低0" -->

<!-- sdflow:hr-tg v1 hit="TG-08,TG-09,TG-17,TG-26" declared="TG-05,TG-08,TG-09,TG-13,TG-14,TG-15,TG-17,TG-18,TG-21,TG-22,TG-23,TG-26" evidence="lane.deps 引入外部依赖(TG-08) · 泳道三态状态机(TG-09) · 路径逃逸/凭证泄漏/子进程执行(TG-17) · 跨 skill 写域锁+CAS 多进程并发(TG-26)" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="stale" runner="codex" reason_code="stale" findings="14" truncated="false" -->
