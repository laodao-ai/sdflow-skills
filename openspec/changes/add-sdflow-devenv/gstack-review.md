<!-- sdflow:step1-broad-review v1 mode="native" -->

# gstack-review — add-sdflow-devenv（**round-4 广审** · autoplan 原生执行）

> **〔gstack-amendment · round-4 · 2026-07-14〕本文件已整体重写。** 前一版是 round-3 产物（2026-07-13 17:36），而 spec/07 已于 2026-07-14 因 **A21 / A22** 大幅改写 ⇒ `outside_voice_guard.py` 判定 **`stale`（exit=1）** ⇒ 按协议**回落自跑设计 outside voice**。round-3 内容存于 git 历史。

> **native 声明的侧信道佐证**：autoplan 经 Skill 机制**原生执行**（其 SKILL.md 指令直接进主 session，非子代理转述模拟）。运行痕迹：preamble 实跑（`BRANCH=feat/add-sdflow-devenv` · `REPO_MODE=solo` · `CODEX: AVAILABLE` · `SLUG=laodao-ai-sdflow-skills`）；Phase 0.5 codex preflight 通过；双声均为**真实调用**（Claude 冷子代理经 Agent 工具 · Codex 经 `codex exec -s read-only`）。
> **G2 适配**：autoplan 的两处人类门（premise 确认 / 最终批准）**不弹窗**，其自动决策与 findings 一并登记进 `spec-review-report.md` 决策区，设计门一次拍板。
> **跳过段**（本场景为 OpenSpec change，非 PR plan file）：restore-point · Phase 2 Design（**无 UI scope**）· TODOS.md · ship。**DX scope = 有**（本 change 即开发者工具）。
> **`.outside-voice/` 已在 `.gitignore`**（`**/.outside-voice/`）。

**审查基准（操作者 2026-07-14 给定，一切判定锚此，MUST NOT 用「现状少见」松绑目标）**
- **§0.1 目标**：技术架构定了 → 定测试策略 → **把开发/测试环境搭起来**。**关键校准：目标不是产出两份文档，而是建立环境。**
- **核心承诺**：**不管什么项目**，都给一份三层（单元/集成/e2e）测试与验证策略框架；做不了的写「不适用+后果」，要人做的写「人怎么做」；**一层都不许留白**。
- **§0.0 第一原则**：机械层**防漏不防伪**。写下「MUST 机械保证 X」前先问「**信号从哪来**」。

**本轮背景**：round-4 刚落地 **A21**（删手搓 GNU make 解析器，562→119 行，7 个罢工分支归零）+ **A22**（删一条**从未被实现**的 MUST）。**本次是对拆解结果的冷审。**

---

## 广审四声 —— **46 条 findings**

| 声 | runner | 条数 | 独有的关键发现 |
|---|---|---|---|
| **CEO**（战略/scope） | claude-subagent（冷） | 8 | 投入配比倒挂 · **A-8 前提零实证却是 15 Task 地基** · 完成态退回 A2 |
| **Eng**（架构/代码） | claude-subagent（冷，**带实测探针**） | 12 | **时效锚覆盖面无锚（假绿）** · append 正则漏判 ⇒ **静默 override 用户 target** · 坏输入静默腐蚀 |
| **DX**（开发者体验） | claude-subagent（冷） | 12 | **skill 自写 smoke 编译不过 ⇒ 打断用户既有测试套件** · `blocked_by` 三件套无字段 |
| **Codex**（outside voice） | codex（`-s read-only`） | 14 | **`environments.md` 16 槽无数据载体** · 封闭枚举 fail-closed 拒收一类项目 · `make exit 0` ≠ recipe 执行 |

---

## 一、多镜收敛（≥2 声独立命中 —— 高可信）

### C1 · 完成态允许**全部泳道停在 `planned`** ⇒ **A2「纯文档编排器」原地复活** 〔CEO F3 · Codex #5〕
**severity: critical · confidence: high**

§0.1 校准写死「目标不是产出两份文档，而是建立环境」；A2 被否理由是「只出文档 = 把最难的一半留给人」（`07:746`）。
但 **SM-3 的诚实边界自我豁免**：「**零代码 greenfield 的 `verified` 数可为 0**，达标线 = 三层框架完整 + 泳道表 + 待建清单」（`proposal.md:86`·`tasks.md:363-367`）；spec 允许 `planned` 收尾（`spec.md:179-188`）。

⇒ **greenfield（主打场景）跑完的合格产出 = 三份文档 + 待建清单、零条泳道跑绿。这就是 A2。否得对，但没执行。**

**修**：完成门要求「**已有可执行代码的项目 ≥1 条 lane 达 `scaffolded` 且有一次真实执行尝试记录（`last_attempt`）**」——失败合法，**没试过不合法**。真·零代码 greenfield 才给例外。

### C2 · Task 13/14（核心承诺的**唯一**智力载体）**零验收判据** 〔CEO F1+F2 · Codex #9 · DX F5〕
**severity: critical · confidence: high**

18 Task 中 **15 个是机械基础设施**（全 TDD）；核心承诺的载体只有 Task 13（references）+ Task 14（SKILL.md），`superpowers-plan.md:2147` 明写「**写 4 份 Markdown（无代码，无测试）**」。
验收侧：SM-1 只查槽非空+非占位（**挡不住「工具选型：待调研」这种合法空话**）；SM-7 只「记录」耗时/回答数、**不设阈值**；「模型能否提出**像样的**验证方法」是唯一真判据，而「像样」**无操作化定义**。

⇒ **18 个 Task 可以全部完成，而核心产品能力从未被验收。**

**修**（三镜方案可叠加）：① 真实 greenfield + brownfield 试点升为**阻塞 Task 19/20**（归档前必须产生实际脚手架 + 一次执行记录 + 两份文档 + 入口索引）；② **冷读者验收**——派 fresh 子代理，**只给它 `testing-strategy.md`**，要它复述「三层各自跑什么命令 / 各测什么」；答不出、或与 `.devenv-lanes.json` 对不上 ⇒ **框架不合格**（把「有用」操作化成可复现实验，**完全在既有冷审基建内**）；③ `lane-patterns.md` 每格 MUST 配「好答案 vs 空话答案」对照负例（**防敷衍靠示范比靠黑名单有效一个数量级**）。

### C3 · 「不管什么项目」与**成建制的排除**直接矛盾 〔CEO F7 · Codex #6 · DX F1/F7/F8〕
**severity: critical · confidence: high**

实际排除/收窄清单：**Windows**（非 POSIX ⇒ 全部泳道 refuse 走 human，`spec.md:287`）· **monorepo**（`proposal.md:98`，且 **spec 里一个字都没有** ⇒ 按本仓「spec 是实现契约」纪律，**它不会被实现**）· **无 `openspec/` 布局的项目**（preflight exit 3 fail-closed）· **JS/TS 生态**（`package.json` v1 MUST NOT 注入 ⇒ 强塞 Makefile 薄壳）· **无 git 仓**（行为全程未定义）。

**Windows 那条还违反 spec 自己的诚实分类纪律**：`go test`/`npm test`/`cargo test` 在 Windows 上**跑得了**——跑不了的是 **skill 自己的进程树杀灭实现**。把它标成 `executor: human` + `why_not_scriptable`（内容只能是「本 skill 不支持该平台」——**那不是「方法」的属性**），正是 spec 在同一张表上方**亲手禁止**的混淆（`spec.md:146-153`：「本机缺依赖也被标成只能人工验证 ⇒ **那是在撒谎**」）。

**修**：① 承诺措辞**钉死为「不管什么技术栈」**，把 openspec 前置 + v1 平台边界写进天花板声明；② **Windows 的 `executor` MUST 保持 `script`** —— 落 `scaffolded + blocked_by`（「本 skill v1 不在 Windows 执行验证，可在 WSL/CI 跑 `<cmd>` 后 confirm」），**或**照跑 + 清理降级 best-effort + 如实告知孤儿进程（**与既有孤儿资源话术同型，零新机制**）；③ monorepo 检测（≥2 个构建根 = **确定性信号**）进 spec 一条最小 Requirement。

### C4 · **skill 自己写的 smoke 跑不过 ⇒ 标成「合法状态」丢给用户**（且可能打断用户既有测试套件） 〔CEO F4 · DX F2〕
**severity: high · confidence: high**

A11 定死「跑一次，失败就记 `blocked_by`，MUST NOT 进 debug 循环」（`07:567`）。理由前半成立（不能无界 debug），**但结论把两类失败混成一条通道**：

| 失败 | 责任方 | 现设计 |
|---|---|---|
| 本机没装 mosquitto / 无 Docker | **环境**，skill 确实不该管 | `scaffolded + blocked_by` ✅ **对** |
| **模型刚写的 harness/smoke 编译不过、import 错** | **skill 自己刚制造的** | 也 `scaffolded + blocked_by` ❌ **把自己的 bug 标成合法状态** |

**在 Go/Rust/TS 里，一个编译不过的测试文件会让整个 package 的 `go test ./...` / `cargo test` 直接红** ⇒ **用户跑 skill 之前测试是绿的，跑完之后他原有的测试套件挂了**，而收尾报告只说「这条泳道 `scaffolded`，下次 continue」。**「不伤害」红线（`spec.md:275`）只覆盖机器状态，不覆盖仓库可测状态。**

**这与 spec 自己批判前一版的病同型**（`spec.md:153` 痛批「把两种『跑不了』混成一条通道 ⇒ **那是在撒谎**」）。

**修**：R4 拆两条。**编译/收集失败（≠断言失败、≠依赖缺失）⇒ 允许且仅允许一次修复重试；二次仍失败 ⇒ MUST 按 txn journal 回滚该文件**（**机制现成**），`blocked_by` 如实写「skill 生成的 smoke 未通过编译，已回滚，未污染你的测试套件；原始报错：…」。**「不 debug」的正确边界是「不 debug 用户的项目」，不是「不收拾自己拉的屎」。**

### C5 · **悬空 MUST 不止 A22 一处**（A22 纪律未面治） 〔Codex #1/#2/#12 · Eng F2 · DX F4〕
**severity: critical（a）· high（其余）· confidence: high**

A22 立下纪律：「**写下『MUST 覆盖 X』之前，先在数据模型里指出承载 X 的那个字段。指不出 ⇒ 加字段或删掉这条 MUST**」（`spec.md:234`）。**这条纪律只在 `fixtures`/`method` 两处执行了，没有扫全面。** 现存悬空 MUST：

| # | 悬空的 MUST | 载体现状 | sev |
|---|---|---|---|
| **a** | **`environments.md` 的 16 槽**（dev/test/deploy：构建命令·本地运行·构建产物·CI·发布·回滚…）+ 事实采集结果（`07:252-265`·`spec.md:46-48`） | **两份 JSON 只存 lanes + 三层策略 ⇒ 零载体**。而 md **MUST 从 JSON 渲染、MUST NOT 手写**（`spec.md:537`）⇒ 这些信息只能**被丢弃**或由 renderer **现场编造** | **critical** |
| b | frontmatter 的 **`sad` / `mode`**（`sad: missing` 是「MUST NOT 佯装有 SAD」的**唯一机械落点**，须跨 session 存活） | 两份 JSON 均无 ⇒ 实现期必然「render 时现场传参」⇒ **谁忘传谁把 `sad: missing` 静默洗成 ok** | high |
| c | 泳道拍板结论的 **mock 边界 / 最小可用集**（`spec.md:124-126`） | lane 模型无 `purpose`/`mock_boundary`/`minimum_viable` | high |
| d | **lane 级 timeout 覆盖 + 实际用值写进 evidence**（`tasks.md:199-200`） | lane 与 evidence **均无 timeout 字段** | high |
| e | **`blocked_by` MUST 含「可辨认修复指引」**（`spec.md:185`） | `blocked_by` 是**一个 str**，唯一校验是整段占位符黑名单 ⇒ `"依赖缺失"`/`"跑不起来"` **全部合法通过**。「是什么+为什么+怎么修」三件套**只有第一件被弱保证** | high |

**修**：逐条「加字段 or 删 MUST」。(a) → 新增 `.devenv-environment.json` 或在现有 JSON 加结构化 `environment` 段，16 槽逐一承载 + `not-applicable + consequence`；(b) → lanes.json 加 `meta: {sad, mode}`；(c) → lane 加 `purpose`/`mock_boundary` + 顶层 `minimum_viable_lane_ids`；(d) → 加 `verification.timeout_seconds` + `evidence.timeout_seconds_at_verify`，**或**删掉这两条 MUST；(e) → `blocked_by` 从 str 升为 **`{symptom, why, fix}`**，三键各自过非占位校验（**纯防漏、信号确定、~10 行**；副产品 = `environments.md` 里一张「当前阻塞与修法」表，**正是新人最需要的一节**）。

---

## 二、A21 拆解的**第三个洞**（主 session 已机械证实 —— **假绿**） 〔Codex #3 · Eng F1，两声独立收敛〕
**severity: critical · confidence: high（实证）**

**问题**：`stale_files()` 只遍历 `evidence.file_digests` 的**旧键**，**从不与当前 `_tracked_paths(lane)` 对账**。⇒ 改**声明**（而非改文件内容）⇒ 一个字节没变 ⇒ 全绿。

**主 session 实测**：
```
验证时 evidence.file_digests 键 : ['Makefile', 'old_smoke.go']
攻击：lane.smoke 改指 new_smoke.go（old_smoke.go 一字未动）
lane 当前声明的文件            : ['Makefile', 'new_smoke.go']
evidence 记录的文件            : ['Makefile', 'old_smoke.go']
stale_files() 返回             : []      ← 未失配 ⇒ verified 继续挂着
```
同理适用于 `source.file` / `source.selector` / `fixtures[]` / `env[]` / `deps[]` 的**任何声明变更**。
**且「事后补声明 `fixtures`」是 continue 模式的主路径**（人门确认后补全）⇒ **新纳入时效锚的文件永远不被检查**。
CAS（`plan_snapshot`）**不顶替**它 —— `spec.md:240` 自己写明 CAS 是「执行期间的并发保护」，**非跨时间时效检测**。

**根因（自指）**：A21 补 `method_at_verify` 时**只接住了「method 字符串」这一块**，没接住**整个 verification plan 的声明面** —— 正是 **A22 纪律在自己身上没执行**。**「面治优先于点补」（CLAUDE.md 基准 3）第二次被违反。**

**修**（两级，均纯机械、信号确定）：
1. **最小**：lint 加第三条失效判据 `set(evidence.file_digests) != set(_tracked_paths(lane))` ⇒ 报「时效锚覆盖面已变（新增/移除：…），需重验」。`_tracked_paths()` 已存在，**成本 ≈ 3 行**。
2. **彻底（推荐）**：验证时记 **`plan_digest_at_verify`**，覆盖**真正影响执行的全部不可变输入**（`executor/method/source/smoke/fixtures/env/deps/kind`）；lint **跨时间**比对它。**这一条同时吸收 `method_at_verify`（成为其超集），并一次性关掉整个声明面，不再逐字段补洞。**

---

## 三、A21 一般化规则**未面治**：`append` 侧与`展示`侧仍留正则 —— 而这两处恰是「写用户文件」与「安全护栏」 〔Eng F4+F5 · Codex #8〕

### C6 · `append_makefile_target` 重名正则漏判 ⇒ **静默 override 用户的 target**（红线）
**severity: high · confidence: high（主 session 已跑 make 实证）**

我在 `07:754,798` / `superpowers-plan.md:2050` 写的兜底理由——「**漏判 → 照常追加 → 最坏后果是多一条定义，不删不改人的东西**」——**在 GNU make 语义上是错的**。主 session 实测：
```
Makefile:9: warning: overriding commands for target `integration'
Makefile:4: warning: ignoring old commands for target `integration'
>>> skill 追加的 target      ← 实际跑的是这条；【用户原来的 target 静默失活】
```
⇒ 用户在 `ifeq` 块里定义的 `integration:`（**`spec.md:641` 自己列为必须支持的语法**）被正则漏判 → skill 追加同名 → **`make integration` 从此跑 skill 那条**。**直接击穿 `spec.md:349`「重名冲突 fail-closed，MUST NOT 静默覆盖」红线**，并踩「MUST NOT 破坏操作者机器状态」最高红线（**破坏的不是字节，是构建行为**）。

**且 `spec.md:605` 刚用一模一样的论证否决了 lint 侧的 target 存在性正则**（「正则找不到 ≠ 不存在」）—— **append 侧用同一个正则、同一个假阴方向，却被放行了**。**A21 论证的对偶面没有面治到。**

**修法（主 session 探针实验修正了 Eng 镜的建议）**：
```
Eng 镜建议：用 `make -n <name>` 判存在性
主 session 实测：不牢靠 —— 藏在【当前环境不生效的 ifeq 分支】里的 target，make -n 同样看不见
深层事实：make 的条件在【解析时】求值 ⇒「这个 Makefile 里有没有 X target」
          【没有环境无关的答案】—— target 集合是变量环境的函数
```
⇒ **「找一个 100% 可靠的检测」这条路本身是死的。** 实测出的可行解：

| 手段 | 抓得到 | 漏判方向 |
|---|---|---|
| **正则**（看**文本**） | `ifeq(CI,true)` 块里的定义（当前环境不生效，但**文本在**） | `define` 内 · 一行多 target · 续行 |
| **make 探针**（追加到**临时副本** → `make -n` → 抓 make 自己的 `overriding commands` warning） | **当前环境下的全部语法**（ifeq/define/模式规则全包）—— **make 自己喊 override = 确定性信号** | 当前环境**不**生效的条件分支 |

**两者漏判方向恰好互补 ⇒ 并用，覆盖面严格大于任一单用。** 残余（两者都漏）归 ③-pre 人门看 diff（**诚实边界**）。
**主 session 实测确认**：冲突时 make 打 `warning: overriding commands`；**不冲突时不误报**。

> **这给 A21 打了个重要补丁**：**「让工具自己回答」≠「工具给出绝对真理」** —— 工具的回答同样有边界（此处是**环境依赖**）。**诚实边界依然存在，MUST NOT 因为「问了 make」就宣称 100% 保证。**

### C7 · R3「跑前 MUST 展开 recipe」是硬 MUST，唯一实现手段却是**允许降级的 best-effort** ⇒ 在复杂 Makefile 上系统性落空
**severity: high · confidence: high**

`spec.md:289` R3 是**防 `rm -rf` / 防偷起容器的唯一措施**：「只给操作者看 `make integration` 一行 ⇒ 零信息量 ⇒ 人只能橡皮图章」。
而**我刚写的 Task 4.12**（`tasks.md:216-225`）规定提取 **MUST 是 best-effort**，遇 `ifeq`/`define`/续行 ⇒ 降级为「无法自动展开，请查看 `<file>`」。

⇒ **凡 A21 列举的那些「真实且合理」的写法，R3 恒不满足** —— 人拿到的**正是那个「零信息量的一行」**，**橡皮图章原样发生**。**MUST 与实现手段之间是空的**（A22 病型）。
**我自己制造的骑墙**：`tasks.md:224` **已写出正解**（「想要权威展开，正解是调 `make -n`」）**却没把它选为实现路径**。

**修**（二选一，别骑墙）：
**(a)** **`make -n <selector>` 作首选展开**（权威、零解析器、与 A21 一般化规则一致；**诚实标注它会 evaluate `$(shell ...)`**），正则仅作 make 不可用时降级；
**(b)** R3 降级为「MUST 展开 **或** MUST 响亮告知『**本次执行的内容未经展示**』并展示**整份 `source.file`**」——**降级路径必须让人看见自己在盖橡皮图章**，而不是给一行「请自行查看」就当交差。

---

## 四、其余单声 findings（**escalate-not-drop，全部上抛**）

### 假绿 / 假机械类
- **`make exit 0` ≠ recipe 被执行**〔Codex #4, **high**〕：target 与同名文件已存在且 up-to-date、空规则、条件展开为空 ⇒ **零执行返回 0**。**A21 删 parser 合理，但替代方案把 exit code 夸大成了不存在的保证**（`spec.md:217`/`:607-612`）。**修**：措辞降为「验证命令**被调用**并返回 0」；skill **新生成的 target MUST 强制 `.PHONY`** 并显式调用 smoke；既有 target 的有效性归 `strength`+人门+冷审。**不要恢复 parser。**
- **`verified-at <sha>` 仍造成语义假绿**〔Codex #11, high〕：主路径是在**未提交的** Makefile/smoke 上验证，却渲染成 `verified-at <HEAD SHA>` —— **该 sha 的 tree 并不包含被验证的落地物**，后来者会自然理解为「该 commit 被验证过」。**修**：`verified-near <sha> (uncommitted inputs)` + 渲染验证文件 digest。
- **坏输入静默腐蚀**〔Eng F3, 中高，**实测**〕：`validate_lane` **不校验 `source`/`smoke`/`fixtures`/`env`/`covers`**。实测：`fixtures: "testdata/b.conf"`（str 而非 list）⇒ `_tracked_paths` 的 `set.update(str)` **逐字符展开成 15 个垃圾"路径"**；`source: "Makefile"`（str）⇒ **`AttributeError` 裸奔逃出 `PathEscape` 契约**。而 JSON 是**模型自由填的**，str/list 混淆是最经典的误结构化。**修**：`validate_lane` 补类型校验（`fixtures`/`env`/`covers` 须 **list of str**，**显式拒绝 str**）。
- **`evidence.exit` / `attested_by` 零校验**〔Eng F6, 中，**实测**〕：`verified` + `exit: 1` + `executor: human` 但 `attested_by: "script"` ⇒ **`validate_lane` 返回零错误**。而「`human-attested` 的绿 MUST 与脚本验的绿可区分」**整条依赖 `attested_by` 的正确性**——**渲染层信它，机械层不查它**。两者**都有确定性信号**（`exit == 0`；`executor=="human" ⟺ attested_by=="human"`），各 2 行。**注意**：`exit` 不能用 `if not ev.get(k)` 查（`exit: 0` 会被判为「缺失」）。
- **「待调研」可冒充已回答**〔Codex #13, high〕：spec 一边说五槽必答、占位符不合法，一边宣布「工具选型**待调研**」**合法**（`spec.md:94`）；而启发式只拒**整段等于** `TODO/待定` 的少数文本 ⇒ **三层都能用包装过的待办句通过机械门**，用户仍拿不到策略。**修**：中间编排阶段可暂存「待调研」，但**最终 render/lint 前 MUST 有具体方向**，否则该层明确标未完成并**阻止「核心承诺已达成」的收尾判定**。

### 罢工 / 拒之门外类（**核心承诺回归守卫**）
- **封闭枚举 fail-closed ⇒ 「未覆盖形态兜底」承诺被 schema 拒收**〔Codex #7, **high**〕：spec 允许未覆盖形态**临场推导**（`spec.md:120-126`），但 `lane.kind`/`deps[].kind` 是**封闭枚举**（`devenv_schema.py:27-31`）⇒ **云账号 / 远程 SaaS / Kubernetes / 模拟器 / GPU / 移动设备**无法归类 ⇒ **schema 直接拒绝，临场推导结果无处落盘**。**这是 A21 同类病：一个枚举 = 一类项目被拒之门外。** **修**：这些字段**本就不参与机械 dispatch、本就是人门确认的语义字段**（`spec.md:569` 自己列在「无独立信号」清单里）⇒ **改为非空字符串**，或加 `other` + 必填 `kind_description`。
- **`fixtures` 声明为目录 ⇒ 直接炸**〔Eng F10.1, 中〕：`fixtures: ["testdata/"]` 是**极自然的目标态产出**。`read_bytes()` 对目录抛 `IsADirectoryError` ⇒ `lane_file_digests` 在 verify 时**未捕获直接崩**；`stale_files` 把它记成**永久失配** ⇒ 该 lane 永远「证据过期」。spec **未定义目录语义**。**修**：显式二选一（fail-closed 报「MUST 是文件」**或**递归 digest），**别留给实现期发明**。
- **symlink 祖先一律拒 ⇒ 以 symlink 组织的 monorepo/packages 下的文件永不能当 smoke/fixture**〔Eng F10.3, 低〕：**合理的安全取舍**，但**未登记为已知边界** ⇒ 撞上的人只看到「拒绝 symlink」而不知怎么办。

### 事务 / 并发类
- **txn journal 缺 `post_write_digest` ⇒ 回退会覆盖人的改动**（**红线**）〔Eng F9a, 中高〕：journal 记「原内容」但**不记 skill 写完后的 digest**。崩溃后、下次启动前**人很可能已手动改过那些文件**（崩了，人自己去改 Makefile）⇒ 按 journal **盲目回退 = 用旧内容覆盖人的新改动，数据丢失**。**这与 `spec.md:471` 自己批判 `git clean`「最后一道护栏内部自带破坏性操作」完全同型。** 判定「该文件自 skill 写完后有没有被人动过」**有确定性信号**。**修**：journal 每项加 `post_write_digest`，回退前逐文件比对，不符 ⇒ **拒绝自动回退**，列冲突文件交人。
- **陈旧锁判定不查 pid liveness**〔Eng F9b, 中〕：`devenv_lock.py:48-57` 首次撞锁即用 `mtime > 120s` 判残留 → 提示人删锁；**`pid` 写了却从无读取者**。笔记本睡眠 / 慢盘 / 跨多文件 inject 都可能让**活锁**超 120s ⇒ 提示删锁 ⇒ **两 session 同写**（**正是 `spec.md:711` 自己说的「陈旧锁检测由保护变成攻击面」**，且 A-6 假设已承认此风险）。`os.kill(pid, 0)` 是确定性信号，**成本 3 行**。
- **`_save` 无锁且无护栏**〔Eng F9c, 中〕：`save_lanes` 全程**不持锁**，也没有 assert 强制调用方持锁。原子写只保证「不写出半个文件」，**不防 lost update**（读全文件 → patch 一条 lane → 全量覆写；期间另一 session 新增的 lane 被**静默吞掉** —— **单 lane 的 CAS 保护不了整个文件**）。**修**：把 `write_lock` 收进 `save_*` 内部（或唯一入口 `with lanes_txn(root) as d:`），**别把纪律留给调用方记**。

### 「装饰性机械」类（**§0.0 点名要杀的**）
- **`output_digest` 无任何消费者**〔Codex #10 · Eng F7, 中〕：spec.md:214/259/558、tasks.md:175 都 MUST 要求写入，但**没有 baseline 与它比对**（输出不落盘、lint 不读、失效判据里没有它）。**它是 `method_digest` 时代的遗物。** 按 A22 纪律（指不出承载/消费 ⇒ 删）⇒ **删，或诚实降级为「给人事后核对的坐标」**（同 `at_commit` 处置）。
- **evidence 必填键不完整**〔Codex #10, high〕：现行 schema 只要求 4 个键，**不要求 `at` / `exit` / human 的 `confirmed_what`**。**修**：按 executor **分支**定义精确证据 schema（script ⇒ `at`/`exit==0`/`attested_by=="script"`；human ⇒ `at`/`confirmed_what`/`attested_by=="human"`）。
- **lint 第 6/9 条过不了信号闸门**〔Eng F11, 中低〕：**第 9 条「入口复述检测：README 出现『完整命令表』→ 告警」**——「**什么叫完整命令表**」**无确定性信号**，实现期只能变成子串/行数启发式 ⇒ **正是本仓 MEMORY 记过的 `ship_gate` 子串检测 dogfood 假阳同型病**（而 devenv 的文档天然会**演示**这些命令 ⇒ **自指假阳**）。**第 6 条「章节锚可达」**——判 `#anchor` 可达需 heading→slug 规则，各渲染器**不一致且无权威** ⇒ **又一个手搓 Markdown 解析器（A20 亲手杀掉的那个）**；且这两份文档**本就是脚本渲染的**，**锚的正确性该由渲染器 owns**。**修**：第 9 条删或改为「只查是否**逐字复制**了渲染器**自己知道的**某个已知区块」；第 6 条收缩为「链接指向的**文件**存在」，**锚部分删掉**。

### DX / 流程类
- **首跑落几条泳道无规定 ⇒ ③-pre 人门 diff 面爆炸**〔DX F3, **high**〕：`07:641` 有「**最小可用集**：首跑 = 一条能跑的泳道 + 一张待建清单」，**但这条纪律没进 spec**（`spec.md:126` 只把它列为「拍板产出 SHALL 含」的清单项，**无 Requirement 说 ③ 只落最小可用集**）⇒ 模型可能一口气落 6 条 ⇒ ③-pre 要人过目**几百行**。**而 spec 自己论证 ③-pre 存在的理由就是「只给人看一行 ⇒ 只能橡皮图章」—— 给人看六百行，结果一模一样。** **修**：「**首跑 MUST 只 scaffold 最小可用集（默认 1 条，上限 2 条），其余落 `planned`**」写成 Requirement + Scenario。**这既是最好的 DX（快速见绿），也是唯一能让 ③-pre 真正被读的办法。**
- **② 步「批量呈现」是巨型单批**〔DX F12, 中〕：三层 15 槽 + 泳道候选 + 每条的验证方法与盲区，**一屏一次点头**。方向对（减少打断），**粒度失控** —— **信息量过载导致的橡皮图章，是同一个病的另一半**。**修**：分两批（批 1 = 测试策略框架「世界观」；批 2 = 泳道 + 验证方法「执行计划」），每批内分「必须逐条拍的」vs「可默认接受、挑错即可」。
- **「人门呈现 SHALL 用人话」是无法验收的漂亮话，而它本可 100% 机械化**〔DX F6, 中高〕：`spec.md:440` 孤零零一句，**无 Scenario、无 lint、无翻译表、无例子**。**讽刺的是这三个字段全是有界枚举**（`executor` 2 值·`kind` 5 值·`layer` 3 值·`status` 3 值）⇒ **翻译就是一张 13 行的查表** —— 按本 change **自己在 A21 立的判据**（「**能不能穷举，就是能不能手搓的分界线**」），这是**可穷举侧、该固化的东西**，却被留成了散文。**修**：`references/` 加 **phrasebook 表**（字段×枚举值 → 一句后果话），render/③-pre **直接查表**；补 Scenario「③-pre 呈现中 **MUST NOT 出现裸字段名/枚举值**」。
- **「允许多报」缺批量重验出口**〔DX F9, 中〕：几乎所有泳道的 `source.file` 都是**同一个 Makefile** ⇒ 改任何一行（哪怕注释）⇒ **所有 make-target 泳道同时过期**。设计接受多报，**但成本估算漏了两件事**：① 代价不是「一次」，是 **N 条 × 每条真实跑时**（集成泳道起 broker 可能几分钟）；② **spec 里根本没有批量重验命令**（只有 `verify-lane --id X`）⇒ 用户要么逐条手敲，要么重跑整个 skill（**又过一遍 ③-pre**）。**被忽略的提醒 = 没有提醒**（**正是本 change 立项理由之一**）。**修**：`verify-lane --stale`（一键重验全部过期泳道）+ 报告**按失配文件分组**。
- **`replan` 与泳道退役无路径 ⇒ 孤儿 target/smoke 永久堆积**〔DX F10, 中〕：skill 是追加者（永不删），而 `replan` 会重走泳道设计。旧泳道从 JSON 消失后，它的 target/smoke/harness **全留在仓里，从此无人引用、无人渲染、无人 lint**。**修**：加 `retire-lane --id X`（从 JSON 移除 + 把落地物列成「以下文件/target 已无泳道引用，建议清理（skill 不自动删）」清单进收尾报告）。**「不删」不等于「不告诉」** —— 这与归位模式「删源须显著呈现」是同一条纪律，**只是没延伸到这里**。
- **maintain 健康扫描可被缺失的派生 Markdown 绕过**〔Codex #14, 中〕：扫描只在 `environments.md` 存在时触发，**而机械真相源是两份 JSON**。若运行在写 JSON 后、render 前崩溃，或 md 被误删 ⇒ maintain 把**最需要检查的半成品**当成「未使用 devenv」**静默跳过**。**修**：四个文件**任一存在即触发**；组合不完整 ⇒ 报「devenv 状态残缺」，**不得跳过**。
- **`covers[]` 的锚是否存在于 `sad.md` 有确定性信号却无人查**〔Eng F12, 低〕：「锚**存在**」（字符串在不在文件里）≠「锚**真命中**」（无信号，归冷审）。**前者是防漏，现在无人查** ⇒ 写错锚名 = 悬空引用无人知。
- **`spec.md:683` 的「缩进 fence」是不存在的构造**〔Eng F12, 低〕：CommonMark **没有**「缩进 fence」——4-space 是 indented code block（**非 fence**）；fence 只允许 ≤3 空格缩进。**措辞会让实现期发明一个不存在的东西。**
- **`_is_placeholder(v)` 对非 str 一律返回 True**〔Eng F12, 低〕：`method: 123` 报的是「method **为空**」，**误导**。应走 `_require_str` 报类型错。

---

## 五、拆洞镜的**阴性结论**（如实记录 —— **查过且干净，不是没查**）

- **`at_commit` 是否在别处仍被当机械比对基准**〔Eng F8 · Codex #11〕：**全仓 grep 后确认无残留。** `design.md:51` 标它为「机械」仅指*获取方式*（`git rev-parse HEAD`），非比对基准；`spec.md:557/627`、`tasks.md:175/182`、`07:464` 三处均已明确「给人读的坐标，不作机械比对基准」；`superpowers-plan.md:1703` 唯一断言是 `len(at_commit) >= 7`（**存在性**）。**✅ 干净。**（但**渲染措辞**仍造成语义假绿 —— 见 Codex #11，那是**另一个**问题。）
- **`SNAPSHOT_KEYS`（CAS）vs spec 声称的覆盖面**〔Eng F8〕：**一致。** `devenv_schema.py:37-38` = `status/kind/source/smoke/fixtures/env/deps` + `method/executor`，与 `spec.md:713` 的九项**逐项对得上**。唯一措辞过强：spec 称「覆盖**整个**不可变的 verification plan」，而 `layer`/`covers`/`strength` 不在内（**不影响执行，无害**）⇒ 建议措辞改为「执行相关的全部字段」。**✅ 干净。**
- **主 session 自查更正**：我一度以为 `SNAPSHOT_KEYS` 漏了 `executor` —— **是我看漏了下一行的 `SNAPSHOT_VERIF_KEYS`**，codex round-3 指出的洞是堵上的。**如实更正，不为凑发现而硬说是 bug。**

---

## 六、战略层（CEO 独有 —— **最高层级，须设计门拍板**）

### S1 · A-8（模型能为三层提出「像样的」验证方法）= **零实证的前提，却是 15 个 Task 的地基**〔CEO F2, **critical**〕
`proposal.md:165` / `tasks.md:460-461` 自己写明：「若模型连给出『有方向』的验证方法都做不到，**这道语义防线就无米下炊，§0.0 总则本身站不住**」。
而 `tasks.md:66-68` 用「**鸡生蛋**」把验证它推到实现之后：「这件事只能靠跑这个 skill 才能验证，而 skill 还不存在」。

**CEO 镜指出这个论证是错的**：核心承诺的智力载体是 Task 13/14 的 **prose**（lane-patterns 四问、五槽模板、strength 自陈要求）——**这堆 prose 不需要任何脚本就能手跑**（拿一个真实项目 + 一段 prompt，看模型给出的三层验证方法经不经得起推敲，**一小时的事**）。所谓「只能靠跑 skill 验证」，是**把 skill 等同于它的 Python 部分**，而 Python 部分（containment/lock/digest）**与 A-8 完全无关**。

**后果**：A-8 若证伪（`tasks 12.4` 自己写了「回设计桌重议 §0.0 总则」）⇒ **15 个基础设施 Task 全部白做或大改**。**这是在用最贵的顺序赌一个自己标注为「零实证」的前提。**

**建议**：**立刻停 Task 5+，先写 Task 13/14 的 prose，在一个真实项目上手跑一遍**（不需要任何脚本），一次性验掉 **A-8 + 「命令虚构」+ lane-patterns 第二样本**三个未验证前提。**成本 ≈ 一个下午。** 跑完再决定基础设施要哪些、要多少。

### S2 · 投入配比：**15/18 是机械基础设施，而它们守的多是 skill 自己的账本，不是用户的产出**〔CEO F1, critical〕
A21 自己写下了正确的**第二问**（`07:822`）：「**这个保证服务谁？它拦住的失效模式，和它自己引入的失效模式，哪个更常见？**」——**这一问只被用在 make parser 一个点上，没有扫过整个面**（**违反 CLAUDE.md 基准 3「面治优先于点补」，而这份设计恰恰把该基准写进了 Compliance**）。
**建议**：把 A21 第二问当闸门，对**每一条现存机械**做面级复审，判据 = 「它服务的是**用户的环境**，还是 **skill 的账本**」。

### S3 · §0.0 的「防漏/防伪」二分法本身有裂缝〔CEO F5, high, **confidence 中高**〕
① 真正的风险不是「人欺骗」而是「**模型是不可靠的证人**」——客观信号的价值不只在抓贼，也在**给模型一个不能自欺的反馈回路**；② **设计自己的行为承认了这一点**：`set-lane --status verified` **一律拒绝**、`verify-lane` 亲自 fork 拿 exit code —— **这就是不信模型的自报**，而 `07:694` 不得不辩解「这一条不是防伪」；③ **A21 不是被 §0.0 抓到的**（它「过了第一问」），是靠 A21 自己新增的**第二问**才倒的 ⇒ **一个抓不住自己最贵错误的第一原则，不该继续当第一原则**。

**建议**：把第一原则从「防漏/防伪」的**类别二分**，改成**统一的三问闸门**：① 信号从哪来 ② **它服务的是用户的产出，还是 skill 自己的账本** ③ 它拦住的失效频率×代价 vs 它引入的失效频率×代价。
⚠️ **这是推翻第一原则的提议，主 session 不自行裁决，直接上抛设计门（决策登记区 Q）。**

### S4 · 「最高价值的东西被 defer，价值上限被自己锁死」〔CEO F1 附, high〕
`proposal.md:34-36` 的天花板声明**自己承认**：两份文档的最高价值（**坑 / 护栏 / mock 边界 / 盲区**）**day-0 根本问不出来**，来源是**踩坑史**；而 **Q-4（harvest loop：从 buglist / code-review 机械喂坑进 testing-strategy）被列为「最高价值演进方向」然后 defer 到 v2**。
⇒ **最高价值的东西被 defer，而价值上限被自己锁死的 day-0 一次性问答 + 账本，被做成了 18 个 Task。配比反了。**

### S5 · 质量防线的两条腿：**一条无实证，一条会疲劳**〔CEO F8, high, confidence 中〕
**冷审腿**——`design.md` R-3 自己写了免责：「『轮询式观测漏检』这个盲区**不是冷审子代理发现的，是人现场跑实验挖出来的** ⇒『冷审能独立挖出同类盲区』**无实证支持**」（**冷审与提方案的模型同档同源，共享盲区**）；**人门腿**——R-6 自己写了负荷警告，R-5「人门疲劳 ⇒ 橡皮图章」单列为风险。
**这是核心承诺可兑现性的最大威胁，量级远超任何一个 digest 字段——而它只以两行 Risk 存在，零工程投入。**

**顺带：A9 可能否错了。** A9 否掉「查表式权威规格库」的理由是「工具随生态演进，固化即腐烂」——**这个理由只否得掉「工具选型表」，否不掉「验收判据」**。「什么样的验证方法算合格 / 什么样的 `strength` 自陈算诚实 / 每层的最低门槛」**十年不变**，恰恰是 §6.2 自己承认「维度稳定 ⇒ 该固化」的那一类。**现在 references 只固化了「问什么」，没固化「答成什么样算过关」** ⇒ **人门唯一的抓手是自己的直觉，冷审唯一的抓手是同源模型的直觉。**

---

## 七、被否方案的**再审**（CEO 镜独立判定）

| 附录条 | 判定 | 理由 |
|---|---|---|
| **A2**（纯文档编排器） | **否得对，但没执行** | 见 C1 —— 验收线（SM-3）允许「一条泳道都没建起来」⇒ 实际产出退回 A2 |
| **A11**（smoke 跑不绿不 debug） | **否错（至少收缩过度）** | 见 C4 —— 把 skill **自己的 bug** 划成了「合法状态」 |
| **A9**（查表式规格库） | **部分否错** | 见 S5 —— 该固化的「**合格判据**」被连坐砍掉 |
| A13–A22 | **站得住** | 拆解方向正确（让 make 自己回答 · 整文件字节 digest · 零规范化）——四声均未证伪 |

---

## 八、autoplan 自动决策（登记，设计门可覆盖）

| # | 决策 | 原则 | 理由 |
|---|---|---|---|
| AD-1 | **不**在广审阶段修改任何文件 | P6 | 本轮是评审；修法一律进 `spec-review-report.md` 由设计门拍板 |
| AD-2 | Phase 2（Design/UI）**跳过** | — | 无 UI scope（本 change = CLI skill + Markdown 编排） |
| AD-3 | outside voice **回落自跑**（guard=`stale`） | — | 前身为 round-3 产物，源文件已更新 ⇒ **复用会审到旧 spec** |
| AD-4 | 46 条 findings **全部上抛**，含低置信项 | Q3 铁律 | escalate-not-drop；设计漏掉的代价高（传导进实现），spec 评审优化**召回**而非精度 |

---

## 九、Step1 结论

**A21/A22 的拆解方向站得住**（让 make 自己回答 · 整文件字节 digest · 零规范化 —— **四声均未证伪**）。

**但拆解本身不彻底，且暴露了一个更大的面**：

1. **A22 的纪律（先指认承载字段）只在两处执行，没面治** ⇒ 至少 **5 处悬空 MUST** 仍在（含 `environments.md` **16 槽**这个 critical）。
2. **A21 的一般化规则（让工具自己回答）只在 `verify-lane` 一处兑现** ⇒ `append` 侧（**写用户文件，已实证会静默 override**）与 `展示` 侧（**安全护栏**）仍留正则。
3. **A21 的第二问（这个保证服务谁）只用在 make parser 一个点上** ⇒ 未扫过整个机械面（S2）。
4. **A21 补口只接住了 `method` 字符串** ⇒ **整个 verification plan 的声明面掉出时效锚**（**已实测假绿**）。

**四次违反同一条基准（CLAUDE.md 基准 3「面治优先于点补」）—— 这本身是本轮最重要的元发现。**

**且核心承诺（§0.1）层面有两条 critical**：**完成态允许零泳道跑绿（A2 复活）** · **核心承诺的唯一智力载体零验收**。

→ 进 **Step2 多镜**（领域 / 对抗×3 / 接地 / HR-TG cross-model），**Step3 对抗裁决**后出 `spec-review-report.md`。
