---
ship-gate:
  design_approved: false
---

# spec-review-report（第二轮）— add-sdflow-devenv

> 阶段二设计评审 · round-2（审**返工后**四件套，commit `626f741`）· 2026-07-13
> **结论先行：不建议进设计 HARD-GATE。且本轮结论不是「再补几条」——是「上一轮的返工方法本身错了」。**

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="TG-08,TG-09,TG-17,TG-26" declared="TG-05,TG-08,TG-09,TG-10,TG-11,TG-12,TG-13,TG-14,TG-15,TG-17,TG-18,TG-19,TG-21,TG-22,TG-23,TG-25,TG-26" evidence="skill 执行外部命令(make/docker/git)+泳道三态状态机+删用户文件与任意 shell 执行的信任边界+两 session 并发写" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="stale" runner="codex" reason_code="stale-rework" findings="9" truncated="false" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="20" 采纳="19" 裁掉="0" defer="1" 独立="11" sev="致7/高9/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="8" 采纳="8" 裁掉="0" defer="0" 独立="7" sev="致0/高3/中5/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="2" sev="致0/高2/中4/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="12" 采纳="11" 裁掉="0" defer="1" 独立="11" sev="致1/高1/中4/低5" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="9" 采纳="9" 裁掉="0" defer="0" 独立="3" sev="致4/高5/中0/低0" -->

## 镜阵实际构成（诚实登记）

| 层 | 跑了吗 | 说明 |
|---|---|---|
| 领域镜（backend） | ✅ | 按 `spec-checklists/domains/backend.md` 逐条过脚本层 |
| 对抗镜 × 3 | ✅ | 上轮**显式跳过**，本轮补跑：`verify-lane` 执行器 / 假绿残余 / 红线与删源 |
| 接地镜 | ✅ | 上轮**显式跳过**，本轮补跑：11 条代码事实核验 |
| DX 镜 | ✅ | 上轮**显式跳过**，本轮补跑 |
| 一致性镜 | ✅ | 本轮新增（返工引入考古层，需专审） |
| outside-voice（codex） | ✅ | `outside_voice_guard` 判 **`stale`**（exit 1）⇒ **禁止复用**上轮 codex findings，本轮重跑 |

**协议偏离登记**：outside-voice 的 context 摘录规则定死为 proposal「What Changes」+ design「Decisions」。本轮**偏离**：design 的 Decisions 已是被推翻的考古层，只喂它等于让 codex 审废稿。改喂**超集**（修订摘要 + specs 真相源全文 + 原 Decisions 一并给供对照），不做挑拣。

**计数（由 `lens_metric_emit.py` 确定性归约，非手数）**：各镜原始报出 **57** 条 → 主 session 合并去重 + 一处拆分（对抗镜2 的 F4 一条同时讲 `owned_by` 与 `kind`，因二者**修法不同**——前者可从 ledger 派生、后者无独立信号——拆为两条 canonical）→ **45 条 canonical**（43 采纳 + 2 defer + **0 裁掉**），展开 **58 镜次**。

**零 DISAGREE。**

> **信任边界（诚实登记）**：锚行计数由 emitter 从结构化 findings 确定性归约，但**输入本身**（某条 finding 该归哪些镜、裁决是否如实转录）仍是主 session 的信任边界。**本轮我先手写了「去重后 34 条」并手拼了 8 行锚——两个数字都是错的，且 `dx`/`consistency` 根本不在 lens enum 里。是 emitter + enum 契约把它挡了下来。**这条如实记，因为它恰好是本报告主题（「机械层要有独立信号」）的一个正面实例。

---

## ⛔ 核心结论：上一轮做的是「追加修订」，不是「返工」

第一轮的判决是「三根承重柱空心」。我的修法是：**在 spec 里追加新 Requirement，在 design 顶部加一张「已推翻」摘要表，正文原样留作考古层。**

本轮八镜独立证明这个修法在两个层面上失败：

### 失败一：被推翻的旧 MUST 还留在真相源里，和新 MUST 并排站着

| 位置 | 内容 | 冲突对象 |
|---|---|---|
| `spec.md:181` | 「lint SHALL **只核验 `source` 指向的文件行是否存在**」 | `spec.md:302` 的 digest 锚。**而 181 行正是第一轮判定为「恒真断言＝设计好的假绿」的那一条** |
| `spec.md:191` | Scenario 仍在示范 `source: "Makefile:11-14"` | 同上 |
| `spec.md:58` | 「状态迁移 SHALL **只由 `set-lane` 执行**」 | `spec.md:78`「`verified` **只能由 `verify-lane`** 产出」 |

**实现者读到 `spec.md:181` 就会去实现那个恒真断言。**没有任何机制阻止他——两条都是 MUST，都在真相源里。codex 的定性原样上抛：**「不要依赖 design 顶部摘要替实现者裁决 spec 内冲突。」**

### 失败二：考古层里有两张与新 Requirement **逐字相反**的施工图

一致性镜的判决（我采信）：**不可接受，必须清理。**

- **状态机图**（`design.md:129-159`）画的是 `scaffolded → verified` 由 `set-lane` 执行——**这正是 ENG-1 判定的「模型自称、脚本盖章」缺陷本身**。图上完全看不出 `verify-lane` 存在。
- **时序图**（`design.md:229-264`）画的是「写落地物 → 跑 smoke → … → 人门（含 diff 过目）」——**人门在执行之后**，正是 ENG-7 判定的 CRITICAL 缺陷。
- **数据模型 YAML 示例**（`design.md:104-118`）里 `deps: [<name>]` 裸字符串、`source: <path:line-range>`、注释「`[] ⇒ 豁免 negative control`」——最后一条与新规则「MUST NOT 靠清空 deps 绕过」**直接相反**。

**实现者写代码时照着图抄，不会逐行核对开头那张 10 行摘要表。**

---

## 🔴 面级发现（本轮最重要的东西）

> **第一轮抓的 `source: "Makefile:11-14"` + 查「那行存不存在」＝恒真断言，不是一处 bug，是一个面。返工只把被点穿的那一处改成了 digest 锚，同一个面上的其他六处原封不动。**

**面的定义：spec 里凡是写着「脚本机械判定」的地方，判定的输入要么是模型一次性自填的裸声明，要么根本不在数据模型里。**

| # | 号称「机械保证」 | 机械层实际只查了 | 真正在承担的是 | 镜 |
|---|---|---|---|---|
| **M1** | `verified` 的诚实性（`blocked_by`） | **非空** ← `blocked_by: "TODO"` 即过 | 模型自觉 | DX |
| **M2** | R1 红线（只停 `owned_by: skill`） | 字段**存在** | 模型自填 | 对抗B |
| **M3** | 「真硬件 MUST NOT 执行」（`kind`） | 字段**存在** | 模型自填 | 对抗B |
| **M4** | 门槛②（`expected-failure predicate`） | **schema 里根本没这个字段** | 无 | 对抗A · codex |
| **M5** | 门槛①（测试真跑） | `collected≥1 ∧ skipped=0` ← `assert True` **完美满足** | 冷审 | 对抗B |
| **M6** | `neg_control` 不可绕过 | 查 `deps` 非空 ← **把依赖误标 `toolchain` 即自动 `n/a`** | 模型自填 | 对抗B |
| **M7** | `isolate` 策略可行性 | 无 | 模型临场判断 | 对抗C |

**七条里没有一条的机械层在检查它声称要保证的那个语义。**

对抗镜 A 抓到的自我打脸最狠：**spec 在 328-330 行痛批「原设计 deps 无 `kind` 字段 ⇒ 真硬件识别只能靠模型自觉」，然后在自己新加的字段设计上，对 `predicate` 犯了一模一样的错。**

### 这个面的正确修法（≠ 再加字段）

按 CLAUDE.md 基准 1（**机械化优先 + 诚实边界**）：**给每个「机械判定」标注它的信号来源，然后二选一。**

- **有独立信号** → 真机械。可用信号：内容 digest · 子进程 exit code · HEAD SHA · **cleanup ledger 的运行时记录** · recipe 文本扫描
- **无独立信号** → **诚实划归语义层**（人门 + 冷审），**MUST NOT 伪装成机械**

逐条判：

| # | 有无独立信号 | 处置 |
|---|---|---|
| M2 `owned_by` | **有** ← R3 的 cleanup ledger | **从「声明」改「派生」**：只有本次运行内 skill 自己调过 `up` 的依赖才准标 `skill`，此前已在跑的一律 `operator`。**这条必须做**——R1 红线的全部效力压在这一个字段上 |
| M7 `isolate` | **有** ← 扫 recipe body 有无字面 `KEY=value` 前缀赋值 | 机械判定「可外部覆盖」vs「已固化在文本里」，命中后者**自动降级 `neg_control: n/a`** |
| M1 `blocked_by` | **部分** ← 可查「是否含可执行的修复指令片段」 | 至少加最小结构校验（WARN 起步），MUST NOT 完全不查 |
| M4 `predicate` | **有**（一旦进 schema） | **补进 deps 描述符**：`expected_failure: {exit_code \| stderr_pattern}` |
| M3 `kind` · M6 `toolchain` | **无** | **诚实划归语义层**：进 ③-pre 人门议程「本次 dep 分类清单逐条过目」（现议程里没有这一项），冷审补一镜「`kind`/`owned_by` 分类是否属实」（现四镜没有对得上的） |
| M5 门槛① | **无**（`assert True` 无机械信号） | **spec 必须诚实写出**：vacuous smoke 的最终防线是冷审语义镜，机械层堵不死。现在的写法让读者以为「①+②+冷审」是三层纵深，实际②在多条路径上缺席 |

---

## 🔴 接地实证：negative control 在本 change **自己的接地样本**上结构性失效

对抗镜 C 去读了 mqtt-console 的 `Makefile:11-14`（**proposal 第 4 行亲自援引的接地证据项目**）：

```make
integration:
	hack/mosquitto-smoke/ctl.sh start
	MQTT_HOST=127.0.0.1 MQTT_PORT=1883 ... go test -tags realbroker ./... ; status=$$? ; \
	hack/mosquitto-smoke/ctl.sh stop ; exit $$status
```

`MQTT_PORT=1883` 是 recipe 文本里的**字面 shell 前缀赋值**（不是 `$(MQTT_PORT)`）⇒ **对任何外部覆盖机制免疫**。

- R2「隔离式抽离」→ **无注入点，做不到**
- 退回停服务 → broker 启停（`ctl.sh`）**也内嵌在同一条 recipe 里**，不是 schema 假设的独立 `dep.up`/`dep.down` ⇒ **接不上**
- 改 Makefile 让它可注入 → **`spec.md:179` 明令禁止**（「已有 target 只登记，MUST NOT 改写」）

**三条路全堵死。`neg_control` 在此泳道唯一诚实的取值是 `n/a`。**

且暴露的坑比预设**更普遍**：不是「测试硬编码地址」（该项目 Go 测试规规矩矩读 `os.Getenv`），而是**「依赖生命周期与连接参数被打包进同一条 recipe 的字面文本」——这是常见且合理的写法，不是反面案例**。

> **这条动摇的是立项主张本身**：negative control 是「`verified` 不靠模型自称」的两条腿之一。若它在真实项目上的适用率远低于设计假设，这条腿是空的。**当前唯一有真实数据的样本上，它是 `n/a`。**

---

## 🔴 执行器：多条卡在「数据模型没有这个字段」或「需要非 stdlib 能力」

| # | 问题 | 镜 | 严重度 |
|---|---|---|---|
| **X1** | **进程树杀灭是 POSIX-only**。`start_new_session=True` / `os.killpg` 是 Unix 专属；Windows 的 `terminate()` 不传播到孙进程，标准库**无零依赖进程树杀灭方案**（需 `taskkill /T` 或 `psutil`——后者违反本仓零依赖纪律）。而 `setup.sh` 有 Windows 分支 ⇒ **R3 在一个官方支持的平台上形同虚设**。讽刺：团队在**锁**上专门验证过跨平台（`design.md:274`），偏偏这条 CRITICAL 红线没有 | 领域 · 对抗A | 高 |
| **X2** | **门槛①「对所有泳道强制」，但只定义了 `go test -json` / pytest 两种 runner 的解析**。spec 自己的 Scenario（`spec.md:48-50`）就把 Svelte 前端写进泳道范围。cargo / vitest / jest / ctest / gradle 一个没有。schema 里也没有 runner/adapter 字段 ⇒ 未列举 runner 只能「模型自称跑了 N 个测试，脚本解析不出真假」——**ENG-1 批判过的模式原地复活** | 对抗A · codex | **致命** |
| **X3** | **cleanup ledger 未定持久化介质**。R3 要防的正是「脚本崩溃 / `kill -9`」——而 `finally`/`SIGINT`/`SIGTERM` **对 SIGKILL 全部无效**。全文找不到 ledger 落盘位置 ⇒ 大概率是进程内存里的 list ⇒ 进程被强杀，ledger 蒸发，下次运行对遗留容器一无所知。**R3 声称要防的场景，正是它自己没防住的** | 对抗A · 对抗C | 高 |
| **X4** | **`evidence_digest` 只摘 command + smoke + source**——漏 harness / conftest / fixture / `up`·`down` 引用的 compose.yml / lockfile / 镜像 digest / 工具链版本。而 `spec.md:88` **声称**「依赖升级会令其失配」——**它检测不到自己声称覆盖的东西**。且「改 fixture 让断言失效」恰是 vacuous smoke 的主要引入路径 | 对抗A · codex | 高 |
| **X5** | **超时阈值全篇无默认值、无配置面** | 领域 | 中 |

---

## 🔴 并发：锁保护错了层，且第三条腿没人管

| # | 问题 | 镜 | 严重度 |
|---|---|---|---|
| **P1** | **CAS 只比对 `status` 一个字段**。`verify-lane` 的锁**不跨 smoke 持有**（上一轮为修活锁特意加的）⇒ 无锁状态下读 `command` 去跑 5 分钟；期间另一 session 改了同 lane 的 `command`（它的 CAS `--expect=scaffolded` 照样通过——**status 没变**）；A 跑完回来写入，`--expect` 仍成立 ⇒ **盖章 `verified`，而 lane 记的 `command` 是 B 的、执行证据是 A 的**。**上一轮修活锁的修法，亲手打开了这个洞** | 领域 · 对抗A · codex | 高 |
| **P2** | **「三 skill 共用单锁」是空的**。`spec.md:392` 要求三 skill 共锁，但 tasks 只显式改 `init.py`（2.2）；实测 `sad_scaffold.py:38` **仍用 `.sad-scaffold.lock`**，且释放不核 owner（`:135`）⇒ **第三条腿根本没人去改** | codex（接地实证） | 高 |
| **P3** | **锁保护的是元数据层，不是真实资源层**。两个 session 并行跑不同泳道（**正常使用模式**）会抢同一个端口/容器。更糟：A 停容器做阴性对照期间，B 的正向跑因容器被停而失败 ⇒ **B 的好泳道被判 `scaffolded`（真·假阴性）** | 对抗A | 高 |

---

## 🔴 安全护栏：修法本身有洞

| # | 问题 | 镜 | 严重度 |
|---|---|---|---|
| **S1** | **③-pre 否决回退对最主流的产物类型失效**。`spec.md:243` 说 `git checkout -- <files>` 回退——但 `spec.md:179` 规定 skill 的动作之一就是**「缺失的 → 新写」**（新写 smoke 是**主路径**），而 `git checkout --` **对 untracked 文件不起作用**。真能撤销的是 `git clean`，spec 全文没提；而 `git clean -f` 会**连带删掉操作者自己没 `git add` 的其他文件**——**「最后一道护栏」内部自带一个破坏性操作** | 对抗C · codex | **致命** |
| **S2** | **脱敏的修法是错的**。spec 明知命令继承 agent 的**完整环境变量**，却只要求**事后正则打码**。被执行的 recipe 或其下游脚本仍可把凭证写进文件、发往网络——**事后打码管不着**。原话上抛：**「recipe 展开不能替代执行环境隔离。」** 正解 = runner 默认走**最小环境 allowlist**，lane 显式声明需要哪些变量 | codex | 高 |
| **S3** | **backup manifest 的可提交性未定义**（`.devenv-backup/` 既不在 `.gitignore`，也没说要 commit）。入 git ⇒ **把已确认要删的内容原样搬进仓库历史，与「删源」动机直接矛盾**；走 gitignore ⇒ **「可恢复」绑死在本地文件系统**，换台机器/CI/新 checkout 就没了，「收尾告知还原方式」落空 | 对抗C · codex | 高 |
| **S4** | R8 用 MUST 语气写「过 secret 正则打码」，但正则是枚举式防御（漏一个 pattern 就等于没有）。**与本仓自己的诚实边界标准不一致**——其余残余（`covers` 正确性、vacuous smoke）都显式标注「归冷审」，唯独 R8 写成绝对语气的 MUST | 对抗C | 中 |

---

## 🟡 覆盖缺口 · DX · 天花板（合并呈现）

| # | 问题 | 镜 | 严重度 |
|---|---|---|---|
| C1 | **`testcontainer` 是压垮 ⟺ 的元凶案例，spec 花整条 Requirement 论证它，然后在 schema 里给个枚举值就没下文了**——五个 `kind` 值里唯一没有 dispatch 规则的 | 对抗B | 高 |
| C2 | ENG-11（v1 只支持行文本型入口）**只在 proposal/tasks 里，没进 spec Requirement** ⇒ 无法机械核验 | 一致性 | 高 |
| C3 | **`blocked_by` 只查非空**（见 M1）。而它是「诚实是硬要求」这条支柱的**唯一载体** | DX | 高 |
| C4 | **③-pre 人门无分级无分批**：所有 recipe body + smoke 全文一次性甩给人。6 泳道 = 几百行 ⇒ **防呆但不防疲劳，机械正确性越强、人门信息密度越高，橡皮图章化风险反而越大**。分级起点现成：**「仅登记已有 target」根本不需要人重读整份 recipe**（spec 自己说了不改内容） | DX | 高 |
| C5 | **术语外泄人门**：`neg_control: n/a` / `owned_by` / `kind: toolchain` 要操作者**当场看懂并拍板**。应由 skill 先翻译成人话后果 | DX | 高 |
| C6 | `schema_version` **有位无用**：加了字段 ≠ 有升级路径。**没有「读到未知/更高版本 ⇒ fail-closed」这条零成本红线** | 领域 · 对抗B | 中 |
| C7 | **exit 5 同时承载三种语义**（非法调用 / lane 不存在 / CAS 冲突）——前者「停下报 bug」、后者「重读重试」，处置完全不同，退出码分不出 ⇒ 只能退回解析 stderr 文本，**与本仓「机械可判据优先于字符串匹配」自相矛盾** | 领域 · DX | 中 |
| C8 | digest 的**「规范化」规则未定义**（是否剥注释/尾空白/tab——**Make recipe 的 tab 有语法意义，不能被规范化抹掉**） | 领域 | 中 |
| C9 | **tasks 缺 `doctor-gen` 任务** ⇒ R7（不替人装依赖，只给 doctor）无落点 | 一致性 | 中 |
| C10 | ENG-16 的修法（脚本**只能判名字碰撞**，语义符不符归模型+人）**未体现在 spec 文本**——Requirement 仍写「名已存在**但语义不符**」，读起来像脚本在判语义 | 一致性 | 中 |
| C11 | ENG-15 的 **draft-SAD 子点未落地**：`sad` 字段只有 `present\|missing`，不区分 SAD 生命周期（`sad_scaffold` 实有 draft→skeleton-ready→validated 三态）⇒ draft 期 contract 随时改名，`covers` 锚**悄悄失真** | 一致性 | 中 |
| C12 | **全硬件项目的天花板未承认**：ESP32/ML307C 类项目**所有**泳道 `kind: hardware` ⇒ `verify-lane` 全部 refuse ⇒ **skill 核心价值（真跑 + verified）整体退化为 0**，只剩文档产出。而这类项目正是 `embedded-test-sop` 的服务对象 ⇒ **devenv 在此交集上沦为空转的分流指针** | 对抗C | 中 |
| C13 | **触发词分流是单向的**：只在 devenv 的 description 加判据句；`sdflow-init` 的 description 现文本含「初始化」却无反向排除句，tasks 第 8 组也没这一项 | DX | 中 |
| C14 | 人门④ 把**四类性质迥异的判断**混在一道门（设计复核 / 逐条决策 / N/A 确认 / **不可逆删源**），删源与常规同级 ⇒ 易被一并快速划过 | DX | 中 |
| C15 | greenfield **零代码**子态：SM-2「≥1 条 `verified`」可能**结构性达不成**（没代码就没有能跑绿的东西） | DX | 中高 |
| C16 | SAD 投影复核的**呈现粒度未定**（逐条问答 ⇒「刚说过的话再确认一遍」）；收尾报告**基调未定**（1 verified + 5 scaffolded 算成功还是失败？下一步怎么调用？） | DX | 中 |
| C17 | **CEO-10 的双 inject 分叉未按「面治」处理**：ADR-7 明知 `init.py` 的 `inject()` 非 fence-aware，却让 devenv 自己重实现一个正确版本、**不修 `init.py`**——与同一份返工里 ENG-6（锁）被处理成「顺带给 `init.py` 补锁，面治优先于点补」**不对称**，且未说明为何 | 一致性 | 低 |
| C18 | `spec.md:356` 与 `358` **整段重复**（356 是 358 的截断旧版） | 接地 · 一致性 | 低 |
| C19 | `spec.md:306` 说 `sad_scaffold` 写侧是「行级**正则**改写」——**实测全文件 `re.sub/match/search` 零命中**，是纯字符串前缀匹配 | 接地 | 低 |
| C20 | `design.md:322` 正文仍逐字写「**无 secret 出境面**」——与同一文件第 23 行「❌ 结论错误」的修订表**自相矛盾** | 接地 · 一致性 | 中 |

---

## ✅ 接地镜核验：承重事实全部属实（上轮修的两条伪证据是真修掉了）

| 断言 | 结论 |
|---|---|
| `init.py:126` 是裸 `open(w)`，无锁无原子写 | **属实**，行号精确命中 |
| `init.py` 有 T21 注释，fence-aware 已 defer | **属实**，逐字对应 |
| `sad_scaffold`：`O_EXCL` 锁 · `LOCK_STALE_SEC = 120` · `mkstemp`+`os.replace` · **写死 `chmod 0o644`** | **全部属实**，STALE 精确等于 120 |
| 本仓零第三方依赖，无 PyYAML | **属实**（`test_anchor_contract.py:146` 有专门测试断言禁 `import yaml` ⇒ 是已固化的不变量） |
| `embedded-test-sop` 存在且覆盖真硬件手动 SOP | **属实** |
| `ship_gate` 子串检测假阳先例（dogfood 自指坑） | **属实**，`gate-anchor-line-scoped` change 与 commit `845262d`/`163a239` 佐证 |
| **proposal 的证据分层与 `06` 一致，无残留伪证据** | **属实** ← 上轮修的两条假证据（「命令虚构是实测」「88% 全是待决策项」）确认已修 |
| `sdflow-maintain` 有可挂 `devenv_lint` 的入口 | **不符（措辞误导）**：现为四类**硬编码**扫描，**无插件挂点** ⇒ 是**新增代码**，非「复用现成挂点」。tasks 5.5/8.3 已按新增排期，**不算悬空**，但「挂点」一词易误读 |

---

## 决策登记区

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [需拍板] R-Q1  返工方法：spec 内被推翻的旧 MUST 是【删】还是【留+标记】？    │
│                 我方推荐：删。理由见「失败一」——留＝两条对立 MUST 并存，    │
│                 而旧的那条是已被定罪为「设计好的假绿」的那条              │
│                                                                          │
│ [需拍板] R-Q2  design.md 考古层：【重写正文+重画两图】还是【整篇作废，       │
│                 design 只保留修订后的决策】？一致性镜判「必须清理」        │
│                                                                          │
│ [需拍板] R-Q3  negative control 的立项主张：唯一真实样本上它是 n/a。       │
│                 是 (a) 降低其地位、如实写「适用面有限，多数项目走 n/a +     │
│                 冷审」，还是 (b) 先用第二个真实样本测适用率再定？          │
│                 我方推荐 (b)——但这会把 Q2 试点的 scope 扩大               │
│                                                                          │
│ [需拍板] R-Q4  Windows 支持：(a) v1 显式声明只支持 POSIX，preflight       │
│                 fail-closed；(b) 为 R3 破例引入 psutil。推荐 (a)          │
│                                                                          │
│ [需拍板] R-Q5  M3/M6（kind/toolchain 无独立信号）：确认「诚实划归语义层」   │
│                 而非继续伪装机械？                                        │
│                                                                          │
│ [自动决策] D1  M2 `owned_by` 从「声明」改「派生」（用 cleanup ledger）      │
│ [自动决策] D2  M4 `expected_failure` 补进 deps 描述符                     │
│ [自动决策] D3  M7 `isolate` 可行性机械判定（扫 recipe 字面赋值）           │
│ [自动决策] D4  S1 回退改「touched-files transaction manifest」逐项恢复/删除 │
│ [自动决策] D5  S2 runner 走最小环境 allowlist（非事后打码）                │
│ [自动决策] D6  P2 tasks 补 `sad_scaffold` 锁协议迁移任务                   │
│ [自动决策] D7  X2 补 `test_evidence.adapter` 契约 + v1 支持矩阵；          │
│                 未知 runner **fail-closed**，MUST NOT 猜测                │
│                                                                          │
│ [已裁掉]  —   （本轮无。34 条 canonical findings 全部采纳或转拍板项）      │
└──────────────────────────────────────────────────────────────────────────┘
```

**defer（2 条，登记不做）**：
- 对抗B-F6（`evidence_digest` 失配窗口期无上限）—— 已由 proposal Q-5 如实登记为诚实边界，非隐藏缺陷
- 一致性-F9（finding 计数与可具名 findings 差 5 条）—— 报告自身已声明「数值一致性是主 session 信任边界、非机械可验」

---

## 收敛口

**不建议进设计 HARD-GATE。`ship-gate.design_approved: false`。**

本轮与上轮的区别必须讲清楚：上轮的结论是「设计有三根柱子是空的，补上」；**本轮的结论是「上轮补柱子的方法，让 spec 变成了一份自相矛盾的文档，而且没治面」**。

如果现在放行实现，实现者会：
1. 读到 `spec.md:181` 去实现那个**已被定罪的恒真断言**
2. 照着 `design.md` 的时序图把**人门放在执行之后**
3. 照着状态机图让 `set-lane` 产出 `verified`
4. 在 Windows 上写出一个杀不掉进程树的 runner
5. 撞上未列举的 runner 时**现场发明**测试计数解析
6. 用 `git clean -f` 实现 ③-pre 回退，删掉操作者的未提交文件

**建议的下一步（按依赖排序）**：

1. **先过 R-Q1..R-Q5 五个拍板项**（尤其 R-Q3——它动摇的是立项主张）
2. **重写 specs**：删旧 MUST（不是加标记）· 补 M1–M7 的信号来源标注 · 补 `expected_failure` / `adapter` / `owned_by` 派生规则
3. **重写 design**：两张图必须重画，数据模型示例必须重写；Context/安全节/Risks 表逐处订正
4. **仍不进实现** ——tasks 第 0 组（`sdflow-architecture` 首个真实试点）依旧是硬前置，且本轮**扩大了它的 scope**：试点须同时测出 **negative control 在真实项目上的可行率**（R-Q3 的答案只能从真实样本来）
5. 三件事做完后**再跑一轮镜阵**

> **元教训（写进本报告供后续复盘）**：本轮的所有发现，根子上是同一件事——**上一轮我用「点补」应对了一个「面」的问题**，且用「加摘要表 + 留考古层」代替了真正的重写。这正是 CLAUDE.md 设计基准 3（面治优先于点补）与 memory `[[point-vs-surface-fix]]` 描述的失效模式。**多镜高收敛（本轮 8 镜零 DISAGREE、7 条 canonical 由 ≥2 镜独立命中）本身就是「前序修补是点驱动的」的信号。**
