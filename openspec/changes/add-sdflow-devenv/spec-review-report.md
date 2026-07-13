---
ship-gate:
  design_approved: true
---

# spec-review-report — add-sdflow-devenv

> **⚠️ 本文件含三轮评审。以下「设计门拍板记录」为最终结论；再往下的 round-1 正文为考古层，其「不建议进门」的结论已被取代。**
> 分轮明细：round-1 = 本文正文 · **round-2 = `spec-review-report-r2.md`（45 canonical，零 DISAGREE）** · round-3 = 本节汇总。

---

# 🔓 设计门拍板记录（2026-07-13）

**操作者逐条过五个拍板项 + 三条定调，最后拍定：**

> **「需要先把 skill 做出来，我再拿项目测试」**

⇒ **设计门通过，进入实现阶段。** `ship-gate.design_approved: true`（头部 frontmatter）。

## 三轮评审的核心结论：根因是**目标错位**，不是执行不力

**14 镜、100+ findings。而它们几乎全部长同一个样子：「你这个机械保证有洞」——没有一条是「这个 skill 不好用」或「它建不起环境」。**

前两版把 skill 设计成了一个**审计机器**（negative control / 测试计数门槛 / `method_digest` / `owned_by` 派生 / cleanup 记账 / `confirm-lane` 身份保证）——**这一整套都在回答同一个问题：「怎么证明模型没撒谎」。**

**而使用这个 skill 的就是那个人自己。他没有动机骗自己。在防一个不存在的攻击者，所以每一条防线都站不住。**

### 病的三次复发（方法论，值得单独记住）

| 轮次 | 修法 | 结果 |
|---|---|---|
| r1 → r2 | **点补**：把被点穿的那一处（行号锚）改成 digest 锚 | **同一个面上还有六处原封不动** |
| r2 → r3 | 写了一条**专治此病的总则**（不许硬凑假机械） | **在这条总则之下，又造了七处新的假机械** |
| r3 → now | **动病灶本身**：重新定义 skill 的目标 | 待试点检验 |

**根因：每次写下「MUST 机械保证 X」，都没有回头问「这个保证的信号从哪来」。**

## 最终设计：机械层**防漏，不防伪**（`docs/sad/07` §0.0，第一原则）

| 机械层 **MUST** 保证 | 机械层 **MUST NOT** 试图保证 |
|---|---|
| **防漏（完整性）**：三层五槽有没有留白 · 泳道有没有验证方法 · `不适用` 有没有记后果 · `human` 有没有写「为什么程序跑不了」· 未完成的有没有被逐条列出来 | **防伪（真实性）**：这个 `verified` 是不是真跑过 · 人是不是真确认了 · smoke 是不是真穿过依赖 |
| **结构检查——全部有确定性信号** | **需要信号锚——脆弱或不存在，且本就不必防** |

**删掉的一整片**（`07` 附录 A13–A20）：`negative control ⟺` · 测试计数门槛 · `isolate` · `predicate` · `kind → dispatch` · runner 白名单 · **`owned_by`**（"运行时派生"的锚**不存在**）· **cleanup 自动记账**（recipe 起的容器**不属于子进程组**）· **`confirm-lane` 身份保证**（agent session 里**模型是唯一命令执行者**，那条 MUST **永远为假**）· **`method_digest` 的"可达"覆盖**（跨语言 import 图分析，**零依赖做不到**）

**新建的**（全是防漏，全有确定性信号）：测试三层框架（**落 JSON**，一层不留白）· `executor: script` 默认首选 / `human` 降级需写明理由 · **`verified-at <sha>`** · **`human-attested` 如实标注** · digest 按文件类型分治 · 路径 containment · txn journal 记原内容

## 三条接地实证（本轮最有价值的产出，已沉淀进 `references/verification-patterns.md` 作负面知识）

1. **negative control 在本 change 自己的接地样本上结构性失效**——mqtt-console 的 `Makefile:11-14` 把连接参数与依赖启停**打包进同一条 recipe 的字面文本** ⇒ 对任何外部覆盖免疫 ⇒ 三条抽离路径全堵死。**而这种写法常见且合理。**
2. **轮询式连接观测：瞬时连接漏检率 100%**（5/5，现场实验证伪）——**采样抓不住瞬时事件，方法本身错。**
3. **`assert True` 类语义恒真，任何外部插桩都堵不住**——proxy 计数（零漏检）能证明"跟依赖说过话"，**但不能证明"断言有效"**。要堵只有变异测试（太重）⇒ **机械层堵不死，归冷审。**

## ⚠️ 进实现前必须知道：整条路线压在一个**零实证**的前提上

> **假设 A-8：模型能为 unit / integration / e2e 三层各自提出像样的验证方法，并如实自陈盲区。**
> **未验证。若证伪，语义防线无米下炊，§0.0 总则本身站不住。**

**镜阵审不出这个——只有真实项目能。** 原设计把它设成「实现前置」是**鸡生蛋**（验证它必须先跑这个 skill，而 skill 还不存在），已按操作者拍定移到**实现后的首个真实试点**（tasks 第 12 组）。**若 A-8 证伪 → 不是修 bug，是回设计桌重议总则。**

另一条如实登记的局限：**冷审子代理与提方案的模型同档同源** ⇒ 系统性盲区共享。证据——「轮询式观测漏检」这个盲区**不是冷审发现的，是人现场跑实验挖出来的**。

---
---

# 📜 以下为 round-1 报告正文（考古层，结论已被取代）

> 阶段二设计评审（`/sdflow-spec-review`）· 2026-07-13
> **⚠️ 结论「不建议进设计 HARD-GATE」属 round-1，已被 round-2/round-3 的返工与上方拍板记录取代。**

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="TG-08,TG-09,TG-17,TG-26" declared="TG-05,TG-08,TG-09,TG-10,TG-11,TG-12,TG-13,TG-14,TG-15,TG-17,TG-18,TG-19,TG-21,TG-22,TG-23,TG-25,TG-26" evidence="skill 执行外部命令(make/docker/git)+泳道三态状态机+删用户文件与任意 shell 执行的信任边界+两 session 并发写 frontmatter" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="reused-autoplan-ceo" findings="9" truncated="true" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="reused-autoplan-eng" findings="10" truncated="true" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="26" 采纳="26" 裁掉="0" defer="0" 独立="17" sev="致5/高14/中7/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="17" 采纳="16" 裁掉="0" defer="1" 独立="7" sev="致3/高11/中2/低0" -->

## 镜阵实际构成（诚实登记）

| 层 | 跑了吗 | 说明 |
|---|---|---|
| **Step1 广审（autoplan，native）** | ✅ | CEO 双声 + Eng 双声（Claude subagent × 2 + codex × 2，均真实调用） |
| **outside-voice（codex）** | ✅ 复用 | 守卫脚本 `reason_code=none`（exit 0）→ **复用不重开**（避免双 codex） |
| **接地（读真实代码）** | ✅ | Eng 两声均读了 `sad_scaffold.py` / `sad_schema.py` / `init.py`，产出代码事实级 finding（PyYAML 缺失 · `chmod 0o644` · 锁参数 120s · `inject()` 裸 `open(w)`） |
| **对抗（refute）** | ✅ | CEO / Eng 两轮 prompt 均为「证明它会爆炸」式 |
| **⛔ Step2 独立镜阵（领域/对抗/接地专职镜）+ DX 镜** | ❌ **显式跳过** | 见下 |

### ⛔ 跳过判定（显著呈现，不埋进正文）

**未跑：DX 镜 · 独立领域镜 · 独立对抗镜 · 独立接地镜。**

**理由**：CEO + Eng 四声已收敛出 **5 条 CRITICAL 直指三根承重柱**，设计需**重大返工**——继续对一份即将被推翻的设计加镜是浪费。原则 2（接地）与原则 3（对抗）已由 Eng 两声满足（见上表），非遗漏。

**未覆盖面**：DX 视角（TTHW / 错误信息质量 / 触发词可发现性）· 独立领域镜（本仓栈为 Markdown+Python，`spec-checklists/domains` 无对应领域清单 —— **这本身是清单缺口**，TG-26 并发无 Python 领域段可依）。

**⇒ 返工后 MUST 重跑完整镜阵。** 本次结论建立在 4 声之上，不是完整 8 镜。

---

## 裁决摘要

**43 条 finding（去重后 33 条 canonical）· 采纳 32 · defer 1 · 裁掉 0。**

两声**零 DISAGREE**——CEO 6/6 维度中 4 项 CONFIRMED-否、Eng 6/6 全部 CONFIRMED-否。这种收敛度本身就是信号：不是某一面镜的偏见。

### 三根承重柱都是空心的

| 柱 | 计划宣称 | 实际 |
|---|---|---|
| **`verified` 的可执行判据**（ADR-4 / SM-2 / SM-4） | 「SHALL 由脚本执行验证得出，**MUST NOT 由模型自称**」 | **`devenv_scaffold.py` 的子命令里没有一个会执行 smoke**。实际流只能是「模型跑 → 模型读 exit code → 模型调 `set-lane --status verified`」⇒ **模型自称，脚本盖章**。negative control 的机械分派所需数据（依赖类型 / 启停命令 / 泳道 kind）**根本不在数据模型里**。且它会**停掉用户正在用的服务，11 条失败模式表里没有任何一条说要恢复** |
| **`source` 出处一致性**（ADR-5 / SM-5 / lint ①） | 「lint 核验 `source` 指向的行是否存在」 | **「第 11-14 行存不存在」对任何长度 ≥14 行的文件恒为真** = 恒真断言。用户在 Makefile 顶部插三行 ⇒ 锚点全部错位、lint 全绿、命令表继续说谎 |
| **「复用已验证模式」**（ADR-10） | 「照抄 `sad_scaffold` 的锁 + 原子写」 | 照抄的是**机制**，**互斥性并不组合**——devenv 的锁挡不住 `sdflow-init`（不同锁名，且 `init.py` 的 inject 是**裸 `open(w)` 无锁无原子写**）⇒ 注入被静默吃掉。锁参数（`STALE=120s`）与**长跑 smoke** 直接冲突 ⇒ 活锁被判残留锁 ⇒ 提示用户删锁 ⇒ 两 session 同写。`chmod 0o644` ⇒ 生成的 doctor/broker 脚本**落盘即不可执行** |

### 外加一个会吃掉整个实现预算的黑洞

**嵌套 `lanes[]` 的 YAML 解析/序列化根本没有方案**：本机 `import yaml` **失败**（无 PyYAML，本仓无依赖声明，skill 靠 symlink 直接跑、无安装环节）；唯一先例 `sad_schema.parse_frontmatter` 是**手搓扁平标量解析器**（固定键白名单 + 枚举，无列表、无引号处理），写侧是**行级正则改写**——这套手法在 `lanes[]`（8 键 × 含列表 × 含中文自由文本 × 含带冒号的值）上**完全用不了**。tasks 1.2 对此**只字未提**。

### 两条立项证据本身有问题

- **「命令虚构」是伪证据**（CEO-1，CRITICAL）：proposal 称其为「接地实测暴露」，而它引用的 `06:44` 白纸黑字写「**零虚构 target，行号全中**」。归位场景实测虚构率 = **0**；新建场景**零样本**。一个 greenfield 的**预测风险**被写成了「实测暴露」，而 ADR-1 的支点正建于此。
- **「无门禁」是 dogfood 自指坑**（CEO-2，CRITICAL）：proposal 把「`assert-bindings` 无自动触发点」列为立项理由 #3，而 **`devenv_lint` 自己也没有任何触发点**（与 `ship_gate` / `sdflow-done` / `sdflow-maintain` 零集成）。更致命：R-3（防僵尸文档）的唯一缓解是「lint 每次跑都复述未完成清单」= **一个没人会跑的 lint** ⇒ 前提「渐进 DoD 不会退化成僵尸」**结构性不成立**。

---

## 决策登记区

> G2：评审中途不打断。以下**自动决策默认接受、可在设计门覆盖**；**需拍板**项由人在设计门一次性过。

### [自动决策] — 高置信，默认采纳（32 条）

全部 CRITICAL / HIGH / MEDIUM finding 见 `gstack-review.md`（CEO-1..11 · ENG-1..17 + codex 独立项）。裁决：**全部采纳**，无一条被裁掉——两声零分歧，且多条经**真实代码核验**（非推测）。

### [需拍板] — 设计门一次性过

---

**Q1 · scope 怎么切？**（CEO-4 / CEO 双声 / Eng 承重柱空心 ⇒ 更该收窄）

| 选项 | 内容 | 三面后果 |
|---|---|---|
| **A（推荐）** | **v1 只做 greenfield**，砍掉归位模式（另开 change） | **系统**：把「删用户文件」这个**全 skill 唯一不可逆操作**从一个**从未在任何地方跑过**的 v1 里摘出去 · **用户**：存量项目暂用已验证的手跑 prompt（`06` 证明它零虚构做成了）· **开发循环**：v1 体量减半，承重柱能真正修实 |
| B | 保持现状（greenfield + brownfield 同 change） | 系统：不可逆操作 + 零验证 v1 同时上路 · 开发循环：14 Req 全修，周期拉长 |

**主次判定**：**主 = 系统镜**——不可逆操作的爆炸半径不该和零验证的新能力捆在一起。CEO 两声独立得出同一结论；且 ADR-9 的合并理由是「代码共用」= **实现复用**论证，违本仓 `change-scope-one-complete-stage-result` 基准（「不按同批来源/顺手/共用」定 scope）。

---

**Q2 · 是否先跑 `sdflow-architecture` 的首个真实试点？**（CEO-6）

`add-sdflow-architecture` 昨日归档，其 hand-off 明写「**首个真实试点（最高优先）**……SM-4 证伪钟起点」——**该试点未做**。而 devenv 对 SAD 的依赖是硬的（形态四问 ← §3 外边界；`covers` ← §5 contract）。若试点发现真实 SAD 的 §3/§5 不像模板假设，**devenv 的两条高价值投影同时塌方**。

| 选项 | 三面后果 |
|---|---|
| **A（推荐）** | **先跑上游试点，就用本来要做 SM-2 的那个绿地项目** —— **一个项目的成本，同时给两个 skill 去风险**：验证真实 SAD 能否长出 devenv 需要的锚 · 验证 greenfield 的「命令虚构」风险是否真实存在（CEO-1 的空白）· 验证 `lane-patterns` 五格在**第二个样本**上是否还成立（CEO-5 的 n=1 过拟合） |
| B | 并行推进 | 若试点证伪 SAD 投影，devenv 已实现的部分要返工 |

**主次判定**：**主 = 开发循环镜**——证据依赖被搞反了（在一条自我引用的证据链上盖楼）。

---

**Q3 · negative control：保留为 `verified` 的定义（⟺），还是降为强信号？**（ENG-2/3/8/9 · codex）

两声共识：**把一个右手边没有通用实现的等式写进 spec 当 ⟺，本身就是假绿**。且它**只证「命令耦合依赖」，不证「断言有效」**（smoke body 写 `assert True` 照样能拿到「正向绿 + 反向红」）；对 **testcontainers / 内嵌 fallback**（Go/Node 主流写法）**永久误判 vacuous**。

| 选项 | 内容 |
|---|---|
| **A（推荐）** | 降为**强信号**：`neg_control: applicable \| n/a — <理由>` 独立字段（**不靠删 `deps` 绕**，那会把假阴性换成真·假绿）；仅对 `failure_policy: strict` 且**抽离机制已定义**的依赖类生效；**必须匹配依赖特定的 expected-failure predicate，普通非零不通过**；**并行强制**「smoke 含断言语句 + 至少跑了 ≥1 个测试且 0 skipped」（解析 `go test -json` / pytest `collected N items`——**有确定性信号，按基准 1 该机械化**） |
| B | 保留 ⟺，实现期补分派表 | Q-4 已承认机制未定；数据模型里**没有依赖类型字段**，「机械分派」会变回模型判断 |

---

**Q4 · `lanes[]` 的持久化：落 JSON 侧文件，还是引入 PyYAML？**（ENG-5）

| 选项 | 内容 |
|---|---|
| **A（推荐）** | `lanes` **不放 frontmatter**，放 `openspec/architecture/.devenv-lanes.json`——`json` 是**标准库、零依赖、round-trip 无损**。`environments.md` frontmatter 只留 `sad` / `mode` / `schema_version` 三个**扁平标量**（沿用 `sad_schema` 手搓解析器的能力边界）。**另：schema 必须带版本号**（`sad` 有 `sad_schema: <int>`，devenv 漏了；Q-2 已预告 monorepo 演进要动 schema，无版本键则存量文件无升级路径） |
| B | 确认宿主保底有 PyYAML + preflight fail-closed | Claude Code / Codex 宿主**并不保证**有 PyYAML |

---

**Q5 · 是否重新评估 ADR-1 的真候选？**（CEO-9 / 双声）

ADR-1 把备选 (a) 表述为「模板 + 手跑 prompt（**没有 lint**）」= **稻草人**。真正的候选**从未被评估过**：

> **已验证的归位 prompt（mqtt-console 零虚构跑通）+ 一个有触发点的 `devenv_lint`**（`06 §4.1` 已把五条机械项精确划定）

**成本是本计划的一个零头，能拿到大部分价值。** 另：`06` 自己给出的「**从构建配置直接渲染命令表**」（无双写、不需要 lint ①）也没进候选表。

| 选项 | 内容 |
|---|---|
| **A** | 重开 ADR-1，把这两条真候选与「完整 orchestrator」做**成本对照**（首次跑通时间 / 人工回合数 / 生成 diff 大小 / 维护面），而非定义式排除 |
| **B** | 维持 orchestrator 路线，但**如实记录**天花板（CEO-3：greenfield 能问出来的东西**不含** `06` 认定的全部价值——坑/护栏/盲区 day-0 根本问不出来） |

---

**Q6 · `devenv_lint` 的触发点挂哪？**（CEO-2，**这条不解决则前提 (b) 不成立**）

「无门禁」是立项理由之一，而本 skill 自己没有门禁。**必须二选一**：

| 选项 | 内容 |
|---|---|
| **A（推荐）** | 新增一条 Requirement「lint 的触发点」，把 `devenv_lint` 挂进 `sdflow-maintain` 的扫描（它本就 own 扫 `openspec/` 一致性）或 `ship_gate`。SM 改为「**在真实门上被自动调用并拦下一次真实回归**」 |
| B | **砍掉渐进 DoD**，要求最小泳道集全绿 | 「不强制 + 不检查」= 名存实亡，**两者只能选一个** |

---

### [已裁掉] — 无

**零条裁掉。** 两声零分歧，且多条经真实代码核验（非推测）。反静默压制：无 finding 被降级或丢弃。

---

## 必须在实现前收口的七条（Eng 两声共同点名）

1. **ENG-1** — 新增 `verify-lane` 子命令**由脚本自己执行正/反两跑**并原子写**执行证据**（`verified_at` / `fwd_exit` / `neg_exit` / `neg_strategy` / `evidence_digest`）；**`set-lane --status verified` 一律拒绝**（exit 5）。没有证据落盘，冷审的「诚实镜」在数据上**无从查证**（它只能读文件）。
2. **ENG-2** — `deps` 升为**结构化描述符**（`name` / `kind` / `up` / `down` / `owned_by` / `neg_control`）+ lane 加 `kind` 字段（`hardware` → `verify-lane` 直接 refuse；`toolchain` → negative control 显式 `n/a`，**你无法「抽掉」一个编译器**）。
3. **ENG-3** — **红线：只能停自己在本次运行中启动的东西**（`owned_by: skill`）；**首选隔离式阴性对照**（把 endpoint 指向必定不可达的地址，信号等价、副作用为零），「停服务」降为最后手段且必须 `try/finally` 恢复 + **恢复失败响亮报告**。
4. **ENG-5** — `lanes` 落 JSON 侧文件（Q4）。
5. **ENG-4** — `source` 改**内容 digest 锚**（`{file, target, digest}`），行号仅作 render 时的动态提示，**不作真相**。
6. **ENG-11** — v1 **显式收窄到 Makefile 型（行文本）入口**；CI 只**生成独立新文件**、不往用户既有 workflow 插 step；JSON/YAML 结构化编辑进 Non-Goals + 登记 todo。
7. **ENG-7** — **人门 diff 移到执行之前**（连同 recipe body 展开一起呈现——现在给人看的 `make integration` 这一行**零信息量**），并补「否决 → 回退」路径。

---

## 拍板记录（设计门 · 2026-07-13）

**六个需拍板项已由操作者逐条过。设计门结论：批准返工方向，`design_approved` 暂不置位——需按下表重写四件套后重审。**

| # | 拍板 | 与推荐一致？ | 连带义务（MUST） |
|---|---|---|---|
| **Q1** | **归位模式留在同一 change**（不砍） | ❌ **推翻推荐 A** | 删源护栏 MUST 从「工作区干净」**升级为逐文件前置校验 + 可恢复 backup manifest**——codex 明确指出 clean worktree **不足以**保护删除（不保证 HEAD 有效 / 待删文件已 tracked / 非 submodule / 非 symlink）。归位既然留下，这条护栏就是**它留下的代价**，不可省 |
| **Q2** | **先跑 `sdflow-architecture` 首个真实试点**（用同一个绿地项目） | ✅ | 成为**实现前置**（写进 tasks 第 0 组）；同时验证：真实 SAD 的 §3/§5 能否长出 devenv 需要的锚 · greenfield 的「命令虚构」风险是否真实存在 · `lane-patterns` 五格在**第二个样本**上是否还成立 |
| **Q3** | **negative control 降为强信号**（非 `verified` 的 ⟺ 定义） | ✅ | 改 ADR-4 / R-5 / 状态机；`neg_control: applicable \| n/a — <理由>` **独立字段**（不靠删 `deps` 绕）；必须匹配 expected-failure predicate（普通非零不通过）；**并行强制**机械门槛：解析 `go test -json` / pytest `collected N`，断言「至少跑了 ≥1 个测试且 0 skipped」 |
| **Q4** | **`lanes` 落 JSON 侧文件** | ✅ | `openspec/architecture/.devenv-lanes.json`（标准库、零依赖、round-trip 无损）；frontmatter 只留 `sad` / `mode` / **`schema_version`** 三个扁平标量（补上原设计漏掉的版本键） |
| **Q5** | **维持 orchestrator 路线，但如实记天花板** | ⚠️ 选 B（未重开 ADR-1） | proposal MUST 写明天花板：**greenfield 能问出来的东西不含 `06` 认定的全部价值**（坑 / 护栏 / 盲区 day-0 根本问不出来）。**且 MUST 修掉两条伪证据**——「命令虚构是接地实测暴露」（`06` 实测为**零虚构**）与「88% 全是待决策项」（被 `06` 的三分法证伪）。**维持路线 ≠ 维持假证据** |
| **Q6** | **lint 挂 `sdflow-maintain`** | ✅ | 新增一条 Requirement「lint 的触发点」；SM 改为「**在真实门上被自动调用并拦下一次真实回归**」。诚实边界：maintain 是**人主动跑**的 ⇒ 这是「更响的提醒」而非**硬门禁**——此局限 MUST 在 design 里显式登记，MUST NOT 佯装硬拦截 |

## 收敛口

**不建议进设计 HARD-GATE（当前四件套）。**

四声零分歧地指出：三根承重柱空心 · 两条立项证据有问题（其一与自己引用的接地回执直接矛盾）· 一个未定义的持久化黑洞 · 两个不可逆操作缺对称护栏。**这不是「修几个洞就能过」的量级——ADR-1/4/5/9/10 五条决策中有四条需要重开。**

建议路径：**先过 Q1–Q6 六个拍板项 → 按结论重写 design/specs/tasks → 重跑完整镜阵（含本次跳过的 DX 镜与独立对抗/接地镜）**。

> **本报告的信任边界**：`findings=N` 与合并池实收数的数值一致性是主 session 的信任边界、非机械可验；lens-metric 的分类正确性（某条 finding 归哪面镜）与 roster 完备性同理。emitter 只保证「给定输入的确定性归约」，不保证输入本身对不对。
