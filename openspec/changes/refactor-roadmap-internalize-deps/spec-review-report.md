# 设计评审报告 · refactor-roadmap-internalize-deps

> **阶段二编排评审**（`/sdflow-spec-review`）。Step1 autoplan 广审（原生）→ Step2 并行多镜 →
> Step3 合并去重 + 对抗裁决。本报告是**阶段二唯一人类门**的输入：人过一遍决策登记区拍板即可。
>
> 评审对象盘面：`git rev-parse HEAD` = `c78c02c`（Step1 checkpoint 之后、任何修订之前）。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="TG-08,TG-09" declared="TG-08,TG-09,TG-12,TG-14,TG-18,TG-19,TG-20,TG-22,TG-23,TG-25" evidence="本 change 一次移除 5 个外部 skill 依赖（TG-08）且新增包与相位状态机含放弃/重入两条异常转换（TG-09）" -->
<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->

---

## 一句话结论

**方向对，契约面干净，但不建议现在进 HARD-GATE 放行。**
本轮出 **42 条 findings**，其中 **3 条致命 / 17 条高**。致命的三条里，两条是**承重前提被证伪**
（人是在错误依据上拍的板），一条是**照做必然报错**的任务缺陷。
另有 **2 条只有真人能拍**（Q1 / Q2）。建议：**先过决策登记区拍 Q1/Q2 → 按修订清单改四件套 →
跑一次只审增量的窄复核 → 再拍板**。

---

## 决策登记区

> 格式：`[自动决策]` = 已裁决、附理由、默认接受可覆盖；`[需拍板]` = 只有真人能定；
> `[已裁掉]` = reviewer 报了但主审判不成立，**连理由一并留档供复核**（反静默压制）。

### 🔴 [需拍板] Q1 —— matt 移除：照原样，还是拆成独立 change？

**为什么必须你来拍**：D2（移除 `openspec/matt/`）是你 2026-08-05 拍的板，
**但它所依据的承重约束 C1 已被证伪**——你当时看到的依据是「本仓再无 matt 的活消费方」。

实测（主 session 亲验）：

- `openspec/matt/issue-tracker.md:16` 明文：「当 `to-tickets`、`triage`、`to-spec` 或 `qa`
  需要发布、读取或更新工作项时：…」
- `ls ~/.claude/skills/` → **`qa` / `to-spec` / `to-tickets` / `triage` 四个 skill 全部已安装**。
- 这四个消费方靠 `CLAUDE.md` / `AGENTS.md` 的「## Agent skills」三段找到路径。
  删掉配置面 = 它们在本仓失去落点。
- 其中「### Domain docs」一段（指向 `openspec/CONTEXT.md` 与 `openspec/adr/`）
  **是与 wayfinder 完全无关的通用治理配置**。

**C1 为什么会漏**：它的检验方法是「全仓 grep `openspec/matt` 路径 + 看有无代码读它」。
这四个是**仓外安装、指令驱动**的消费方——grep 仓内代码对它们结构性失明。
🔴 **六个冷镜里有两个专门核过 C1，都只在仓内 grep 就判「成立」**；只有跳出仓库边界才照得到。

**反向证据（Claude CEO 镜实测 git log）**：`sdflow-issues` 生于本仓**首个 commit（2026-07-03）**，
早于 `openspec/matt/` 建立（2026-07-10）**一周**；本仓自始至终用的是 `sdflow-issues`（T1…T230）。
⇒ matt 的 issue-tracker 角色**从未真正投入使用**，它**早在本 change 之前就是事实性废弃**。

| 选项 | 后果（三镜） |
|---|---|
| **A. 照原样删（推荐）** | **系统镜**：4 个已装 skill 在本仓失去配置落点，但它们本就没在本仓用过（时间线证据）；**用户镜**：若你哪天想在本仓用 `/triage`，需重新铺配置；**开发循环镜**：scope 不膨胀，一次做完。**主次：开发循环镜为主。** |
| B. 拆成独立 change | **系统镜**：本 change 只删 wayfinder preflight 一处引用，回滚面更小；**用户镜**：无差别；**开发循环镜**：多跑一次完整 workflow 循环（本仓的循环固定成本高）。 |
| C. 删目录但保留「Domain docs」一段 | **系统镜**：保住通用治理指路，只删 wayfinder 相关；**用户镜**：无差别；**开发循环镜**：+5 分钟。 |

**我的推荐 = A**，但**理由要改**：D2 现在的论证是「因本次改动才孤立」（因果错），
应改为「matt 是历史遗留死配置，独立可删；与本 change 同批做的理由是操作成本低 + 避免半改状态」。
若你更在意那四个 skill 的可用性，C 是零成本的中间选项。

---

### 🔴 [需拍板] Q2 —— 「未决项闭环」能力要不要补承接物？

**问题**：wayfinder 的 map + 票承载了 **open/claimed/resolved/abandoned 状态机 + Blocked-by 依赖
+ frontier 查询**——即「当前还剩什么没决定」本身是结构化、可查询、跨 session 可恢复的。
内化后的 `memo.md` 是**纯追加日志**：只记「已站稳的结论」，不追踪「还悬而未决的清单」。
而 D7 删掉了收尾 checklist ④（wayfinder 闭环）——**唯一的未决项闭环门**，
并把存量 open/claimed 票判为「历史遗留、不阻塞收尾」。

**D7 那一步本身没错**（检查对象确实不复存在）。问题是**「未决项闭环」这个能力在新流程里没有承接物**
——这是 D7 当时没被问到的那一半。C10 说「wayfinder『map 先建、票增量 resolve』本质同模式」，
这是**未经验证的等价性断言**（三个独立冷镜同指）。

**为什么对 roadmap 尤其要命**：`sdflow-spec` 的 B 相位是单次 change、几小时到一两天；
而 `sdflow-roadmap` 的定位明确是「**超出单次 change、可跨月**」——正是票据模型被设计出来伺候的场景。

| 选项 | 代价 |
|---|---|
| **A. 最简补（推荐）** | memo 增一个 `## 未决项` 小节；收尾 checklist ④ 扩一句「未决项小节非空时须逐条标 已决/显式延后/放弃，MUST NOT 带未决项定稿」。**零新机械层，复用已有 checklist。** |
| B. 不补，如实记风险 | 在 decision-memo 里把 C10 标为「未经验证的等价性断言」，列为下一个大型 roadmap 实践中要观察的风险点。 |
| C. 补完整结构化 planning state | 与「消除外部依赖、保持轻量」的目标冲突，且属加宽。**不推荐。** |

**推荐 A**：它是「补能力」不是「加宽」——目标态里「引导人做跨月规划」本来就含这个能力，
砍掉是缩水；而 A 的实现成本约等于两行文字。

---

### [自动决策] D-A1 · autoplan mode = HOLD SCOPE（偏离缺省）

autoplan 缺省对「已有系统的迭代」取 `SELECTIVE EXPANSION`（会 surface 扩张提案）。
本轮改为 **HOLD SCOPE**：本仓 `CLAUDE.md` 基准 3/4 与通则③明确禁止「顺手加宽」，
且 D1–D14 已由真人逐条拍板。⇒ 整个 cherry-pick ceremony 跳过，火力全投「现有 scope 是否 bulletproof」。

### [自动决策] D-A2 · 三条被证伪的承重前提，一律「改依据、不改结论」

C1 / C3 / C8 三条承重约束被实测证伪。**但三条的结论都仍成立**——
- C1 → matt 该删（时间线证据更强，见 Q1）
- C3 → 冻结条款仍必要（**锚目标态**：skill 全局分发，旧版 producer 确实产出过 footage；
  「本仓没有」不是砍条款的理由）
- C8 → bundle 该改（只是牵连面从 2 处变 3 处）

⇒ 自动决策：**改写依据、保留结论**，不动 D2/D7/D10 的方向。

### [自动决策] D-A3 · Step1 复用守卫判 `section-not-found` → 自跑 design-voice

`outside_voice_guard.py` 对 `gstack-review.md` 返回 `section-not-found`（退出码 1）
⇒ 未复用 autoplan 的 codex 段，**回落自跑设计 outside voice**（`reason_code="ok"`，3 条 findings 全新全采纳）。
显式降级日志已记，非静默。

### [已裁掉] X1 · Codex DX：「直接生成快路径名存实亡，应先给 roadmap 骨架再进 B」

**裁掉理由**：gate-0 五项（`SKILL.md:265-271`）是**现行设计**，D6 是真人 2026-08-05 明确拍板保留的，
且 D6 的论证（gate-0 验讨论充分度、不验需求真实性，两关独立）站得住。
Claude DX 镜**实测**新旧 gate-0 完全未变、快路径可达性与旧版持平——两镜在此 DISAGREE，采信有实测的一侧。
重新论证一个已拍板的决定违反「人重申后 MUST 立即照做」。
**保留半条**（见 SR-40）：新增七维 B 相位**确实是新摩擦**，四件套里没有一处承认这个增量。

### [已裁掉] X2 · Codex CEO：「『商业化信号』是错的控制变量，应按决策风险（不可逆性/爆炸半径/花费/合规）路由」

**裁掉理由**：该词表是**现行 spec 已有**的分档判据；本 change 只做**术语改名、词表不变**（D5 明确）。
改判据 = 扩大目标范围（通则③的「加宽」），不属本 change scope。观点本身有道理，**若要做是另一个 change**。

### [已裁掉] X3 · Codex CEO：「未证明问题大到值得破坏性重设计，应先做一轮 baseline 度量（历史 roadmap 运行、宿主分布、续跑失败率、收敛时长）再改」

**裁掉理由**：① 目标范围由人定，D1/D2 已拍板；要求先做度量再动 = 拿方法论把已定的目标推回去。
② 该度量在本仓不可得（roadmap 包总共 4 个，其中 3 个是单文件）。
③ 但它指出的「success metrics 只量删掉的字符串、可以给一个更差的规划器发合格证」**是对的**——
这半条**已采纳**为 SR-19（验证网缺口）。

### [已裁掉] X4 · Codex 对抗镜：「『信号词表』措辞暗示可枚举匹配，实际靠语义类别判断」

**裁掉理由**：非本 delta 新引入——现行 SKILL.md 已是同样五项措辞，本次只是首次提升进 spec 层。
实现期风险等级不变。**若要收紧是行文优化，不阻塞本轮。**

---

## 二、Findings（合并去重 + 对抗裁决后）

> 置信度按 spec-review.md 四点五：**低置信项仍上抛、绝不静默滤除**（与 code-review 的数值一刀切有意不对称）。
> `✅亲验` = 主 session 自己跑命令 / 开文件确认过，不是转述镜子。

### 🔴 致命（3）

#### SR-1 · C1 承重前提证伪：matt 有 4 个已安装的活消费方 〔✅亲验 · 主 session 独家〕
见 **Q1**。六个冷镜全部漏掉——两个专门核过 C1 的都只在仓内 grep。
**教训（值得记进本仓经验）**：「无消费方」类断言的检验面 **MUST 跨出仓库边界**——
指令驱动的消费方不会在 grep 里现形。

#### SR-2 · memo「定稿标记」无定义，重入协议不可实现 〔五源收敛：hr-tg voice · Codex eng · Codex DX · Claude eng · 主 session ✅亲验〕
- delta spec 的 ADDED「B 相位拷问与增量落盘」把重入探测钉死在「memo 存在且**无定稿标记**」上，
  而**四件套全文没有任何地方定义「定稿标记」是什么字面**。
- **根因**：`sdflow-spec/SKILL.md:314-319` 的 `decision_hash` 是**一物两用**——身份核验 + draft/final 状态位
  （`留空`=草稿，B.8⑤ 补齐=定稿）。D4 只论证了「不需要身份核验」，**把状态位一起砍了**。
- 🔴 **加重**：该状态位**今天就存在**——`sdflow-roadmap/references/memo-template.md:27` 现有
  `> 状态：DRAFT / FINAL`。而 D13 / task 2.1 把新模板头部规格钉为「头部包名 + 日期」，只字未提状态字段
  ⇒ **现成的被删、替代的被否**。
- **修复（不违 D4）**：**保留** memo 头部 `状态：DRAFT / FINAL` 一行（+ 定稿日期），
  并在 delta spec 与 SKILL.md 正文里**显式点名它就是「定稿标记」判据的实现载体**。
  补规范：命中 ≥2 个 draft 怎么呈现、「新开」对既有 draft 做什么。

#### SR-3 · tasks 5.3 的 `OBSOLETE` 是非法状态码，照做必然报错退出 〔对抗镜 A3 独家 · 主 session ✅实跑复现〕
```
$ python3 sdflow-issues/scripts/issues_v2.py set-status --id T134 --to OBSOLETE --evidence "test"
ERROR: 状态码非法：OBSOLETE（pool=todo 合法值=['DONE', 'OPEN', 'PROPOSED', 'WONTDO']）
```
- `issues_v2.py:46-49`：todo 池合法终态只有 `DONE` / `WONTDO`；T134 是 `pool: "todo"`。
- **第二处错**：`WONTDO` 要配 `--reason`（不是 `--evidence`；`--evidence` 只服务 `FIXED`/`DONE`）。
- **根因**：D11 用自然语言「已过时」，被直接抄进 tasks.md 当机器状态值。
- **修复**：5.3 改写为「T134 关 `WONTDO` + `--reason`（前提消解：…）」。

### 高（17）

#### SR-4 · C3 承重前提证伪 + tasks 6.4 是恒真锚 〔接地镜 + Claude CEO/DX + Codex eng/DX，主 session ✅亲验〕
- `find . -type d -name footage` **全仓零命中**。C3 引的「footage 引用」实为
  `archive/workflow-cost-optimization/memo.md:1` 标题里的比喻词「（memo · 考古 footage）」。
- ⇒ tasks 6.4 指定 `issues-triage-2026-08` 做冻结条款演练，而**该包只有一个 `roadmap.md`**，
  演练**证不到任何冻结分支**；Success Metrics 第 5 条随之落空。整条 ADDED Requirement
  「历史存档引用边界与存量 footage 冻结」的核心分支**永远不会被走到**。
- 🔴 **条款本身不该砍**（这是通则③）：skill 经全局 symlink 分发，目标态的 producer（旧版 skill）
  确实产出过 footage，消费仓存量不可见但必然存在。**要改的是依据与验证方式，不是条款。**
- **修复**：① C3 改写为目标态论证；② 6.4 改为「构造 fixture：复制一个存量包 + 手工造
  `footage/map.md` + 一张 open 票，跑续跑/重入/收尾三条路径，断言不迁移、不新增票、不阻塞收尾」。

#### SR-5 · continue/replan「只删本次新增」不可安全实现 〔hr-tg voice + Codex eng + Codex DX + Claude eng〕
- delta 要求「continue/replan 场景只删本次新增内容，MUST NOT 动既有文件」，但 memo 无 run-id、
  无 manifest、无段落边界 ⇒ **无可执行的归属判据**；且该 Requirement 的 5 个 Scenario 里
  **只有 create 场景的放弃**。
- **后果**：agent 要么跳过清理，要么按猜测删——后者是删既有内容的破坏性动作。
- **修复（推荐前者）**：① **continue/replan 一律不自动删**，只在 task-log 留一行「本次 B 放弃」
  （与「半途包由下次重入呈现」的既有接受口径一致）；② 或 B 相位写入一律 append-only 带 run 标记。
  补 continue-abandon / replan-abandon 两个 Scenario；并按 SR-39 加「删除前复述完整路径」。

#### SR-6 · B 相位「停止条件」在 spec 里完全缺失 〔Codex DX · 主 session ✅亲验〕
`design.md:78` 与 `tasks.md:10` 都列了「停止条件」，但 delta spec 的 ADDED Requirement
**全文无任何收敛判据**（grep「停止条件」在 delta spec 零命中）。
对照 `sdflow-spec/SKILL.md:348` 的 B.5「停止信号（**最小充分条件**，MUST NOT 用形容词）」
——同构声称在这点落空。**后果**：七维无收敛判据 = 无界摩擦，或 agent 自判「够了」B 形同虚设。
**修复**：每个被裁剪进本次的维度须落一个终态（`已决` / `显式延后（附触发条件）` / `不适用`），
全部有终态才可进 C。

#### SR-7 · 骨架标「保留」的节里嵌着待删机制（**面级**，6 处）〔对抗镜 A1 + A3 交叉 · 主 session ✅逐行亲验〕

| 位置 | 骨架标注 | 内嵌的待删机制 |
|---|---|---|
| `SKILL.md:199` 规则 1 | 「硬性规则 1–5，只规则 3 改」 | 「长讨论的 footage 落 `…/footage/`」 |
| `:227` 规则 5 | 同上 | wayfinder 铺图期 Task 票整条子条款 |
| `:511` 命名规范 | **「保留」** | 「footage map 头部 `Tracker root:` 字段的锚」 |
| `:525` 下游阶段实施 | **「保留」** | fallback 三例外之一 =「需 wayfinder 跨会话铺图」 |
| `:546` 陷阱 1 | 「删 7、改 3」不含 1 | 「先进讨论层**三分支路由**」（新文件里不存在的节名） |
| `:603` CLAUDE.md 配合 | 「去 footage 行」 | 目录说明与 footage 子句用分号拼同一行，粒度歧义 |
| `:618` 参考模板 | 「参考模板」 | 「memo — 可选，考古用；**长档由 footage 取代**」（与 D9 把 memo 升格为唯一载体矛盾） |

🔴 **这是本轮最该记住的爆点形态**：不是「该删的没删干净」，是「**明确写着不用动的节，里面嵌着该删的东西**」。
且 tasks 6.1 的词表 `wayfinder|office-hours|grilling|domain-modeling|openspec/matt|野心|结晶`
**不含 `footage`、不含「三分支路由」** ⇒ `:199` / `:546` / `:603` / `:618` **机械门 100% 漏检**。
**修复**：新增一条任务「逐句核对所有标『保留』的节是否含指向已删机制的残留引用」，
并把 `footage`、`三分支路由`、`Tracker root` 加进 6.1 词表（配合 SR-16 的白名单规则化）。

#### SR-8 · create 主干路径零 Scenario 〔对抗镜 A2 · 主 session ✅亲验〕
25 个 Scenario 中只有 `:35` 与 `:119` 涉及建包，**两个 WHEN 都是「已存在」**。
「目录不存在 → B 起手即建目录 + 落草稿 memo」这条最高频路径**一个验收锚都没有**
——而「起手即建、不拖到收敛后」正是 D9 的核心。
**修复**：补一条 Scenario 锁死 create 主干。

#### SR-9 · 跨 Requirement 数据契约断裂：checklist ④ 消费的记录，B 相位从未被要求产生 〔对抗镜 A2 · 主 session ✅亲验〕
- checklist ④ 的判定依据是「**memo 中有提议与确认记录**」。
- 而 B 相位的提议制条款原文**只写**「未经确认 MUST NOT 写入 `CONTEXT.md`/`adr/`」——
  **从未要求把提议/确认事件以可辨识格式记进 memo**；它只笼统落在「承重结论 SHALL 当场追加写入 memo」下。
- 唯一测提议制的 Scenario 只测负面情形（未确认时不写），没测正面情形（确认后 memo 留可扫描记录）。
- **后果**：④ 退化成「人读整份 memo 猜哪条是 ADR 提议」。
- **修复**：B 相位补一句「提议经确认后 SHALL 以可辨识标记（如固定前缀 `[ADR确认]`）写入 memo」；
  或把 ④ 明确改为「人工通读 memo 全文核对」而不暗示可查条目。

#### SR-10 · B 中途放弃时，已写入全局的 ADR / CONTEXT 无回收路径 〔design-voice 独家〕
- B 相位经确认可写 `openspec/CONTEXT.md` / `openspec/adr/`；而「放弃」只处理包目录/本次新增，
  唯一放弃 Scenario 也仅删包目录；全局对账（checklist ④）**只发生在三件套完成后的收尾**
  ⇒ **覆盖不到 B 中途放弃**。
- **后果**：一个被放弃的、未定稿 roadmap 的临时判断，**永久污染全局真相源**。
- **修复（推荐）**：把已确认的 ADR/术语**先留在 memo，待相位 C 生成并确认终稿后再写全局**；
  若必须 B 内写，则放弃时须逐条 supersede/revert 闭环。

#### SR-11 · memo 对账无归属/版本锚，收尾 supersede 可能撤销他人结论 〔design-voice 独家 · 主 session ✅亲验〕
- D7 废弃了 git 基线 diff 改用 memo 对账。而现行 `SKILL.md:310`「共享真相源基线记录」原文明写
  「**无基线即无从机械核对**」——被废弃的正是提供**归属与版本锚**的那个东西。
- 现行还有第二道防线 `SKILL.md:312`：调用语 SHALL 声明「roadmap 探索期，决策未定稿」——
  **新设计里也整个消失了**。
- ⇒ 新设计只剩「提议制 + 无锚 memo 对账」，分不清哪条是本 roadmap 写的、写入前是什么版本。
- **修复（不必恢复整套基线 diff）**：memo 的每条全局写入记录保存**目标路径 + 精确条目 + 写入前版本锚**；
  收尾仅能变更仍匹配该锚的条目，不匹配即停下让人裁决。

#### SR-12 · 「未审待恢复」状态未被收尾四项门消费 〔design-voice 独家 · 主 session ✅亲验〕
- delta 要求 review 失败时留痕「未审待恢复」且 MUST NOT 当作已完成；
  但收尾四项只查 Review 处置 / 引用 / 历史存档 / memo 对账，**不查包状态**。
- `task-log-template.md:20` **已有** `未审待恢复` 状态取值——**门却不消费它**。
- ⇒ 冷启动执行体只要「Review 处置无未处置条目」就能收尾，review 失败照样过门。
- **修复**：收尾前置条件明确「状态为 `未审待恢复` 时必定阻塞；仅成功 review 或人类显式
  `review-waived` 才可进 checklist」，并补一条失败→恢复→重试成功的 Scenario。

#### SR-13 · C8 承重前提证伪：bundle 牵连是 3 处不是 2 处，且第三处是消费仓 config 生成模版 〔领域镜独家 · 主 session ✅亲验〕
- `sdflow-init/assets/workflow/config.template.yaml:41,51` 也含 wayfinder 引用，
  指向 `ff-generation-constraints.md` 的「wayfinder→ff 衔接契约」章节——
  而该章节在当前文件里 grep **0 命中**（既存陈旧引用）。
- 🔴 **它是消费仓 `config.yaml` 的生成模版**——这条 wayfinder 指令会注入每一个新 init 的下游仓的
  config context，是**活传播面**。proposal / design / tasks 三份产物**全文零提及**。
- **修复**：scope-check 表补一行；按基准 4 的 fold 判据（同片文件、低 blast radius）**倾向本次一并订正**。

#### SR-14 · 分发链路模型写错 + `docs/external-dependencies.md` §8 残留被自己的白名单藏住 〔hr-tg voice + Codex eng · 主 session ✅亲验〕
- **(a) 模型错**：proposal〔TG-20〕写「bundle 改动需 `sdflow-init update` 推送」。
  实测 `sdflow-init/scripts/init.py:213` docstring：「R-MRF-1 分层部署：**默认只铺 `tools/` 子树**
  （规则经全局 canonical 解析，不复制进消费仓）。`full=True` 整 bundle 铺设——**仅供 toolkit 源仓
  `update --dev`**」⇒ 消费仓跑 `update` **根本不会**收到那两个 bundle 文件的改动。
  真正的风险面是另一个：**有本地 `openspec/workflow/` 规则副本（pin）的消费仓**——遮蔽全局且
  `update` 不刷新（`init.py:329` 的「反静默守卫·陈旧遮蔽」正是为此）。
- **(b) 残留**：`docs/external-dependencies.md:148`（§8 内部跨 Skill 依赖图）仍有
  `/grilling、/domain-modeling`；tasks 5.4 **只说删 §5**，而 6.1 白名单把**整个 `docs/`** 排除
  ⇒ 残留扫描**正好照不到它**。加剧因素：该文件**在 main 上不存在**，是本分支新建的活文档（+177 行）。
- **修复**：改写 TG-20 与 Risks 的分发段为真实模型；5.4 扩到「§5 + §8」；6.1 白名单收窄（见 SR-16）。

#### SR-15 · `openspec/CONTEXT.md` 实有第三处词条，三份产物一律只认「两处」〔Claude eng 独家 · 主 session ✅亲验〕
`ticket（实现分解单位）` 词条正文明写「**matt 套件中 wayfinder 的讨论 ticket（map 的 `issues/<NN>`）
是另一种 ticket**，需限定词区分」，`_Avoid_` 行还专列「把 wayfinder 讨论 ticket 与实现 ticket 混为一谈」。
而 `proposal.md:70` / `design.md:67` / `tasks.md:37` **一律写「词条两处」**。
（附带：`footage` 词条正文还含「决策**结晶**」，是改名的第二个消费点。）
**修复**：三份产物统一改为「三处」，5.2 明确 ticket 词条改法。

#### SR-16 · tasks 6.1 的白名单是枚举式的，实测遗漏一大片 〔Claude eng + 领域镜 + 对抗镜 A3，三镜各抓到不同实例 · 主 session ✅亲验〕
实测全仓 grep（不带 `--include`），白名单**外**的合法/无关命中：

| 类别 | 实例 | 为什么不该被当残留改 |
|---|---|---|
| DOC-1 语境「考古层」 | `sdflow-architecture/references/` ×4、`openspec/adr/0020-*.md`、`openspec/issues/INDEX.md` | C5 明令禁止全局替换 |
| D10 拍板保留的规则本身 | `sdflow-init/assets/workflow/ff-generation-constraints.md:46-47` | **它就是 D10 说要保留的那条** |
| 同形异义「野心」 | `openspec/issues/open/todo/T227.md`（「spec 野心之外的加固」） | 与商业化信号无关 |
| 工具权限配置 | `.claude/settings.local.json:25` `"office-hours": "name-only"` | 全局工具授权，删了影响本机 skill 可用性 |
| 存量**活跃**（非归档）roadmap 包 | `openspec/roadmaps/issues-triage-2026-08/roadmap.md:256` | 冻结条款说不许动，白名单只豁免了 `archive/` |
| issue 记录 | `openspec/issues/{open,closed}/`、`INDEX.md`、`CLOSED.md` | 历史决策引用 |
| **自称「活文档」的参考资料** | `docs/sdflow-fable5/02-module-reference.md:6` 自述「本文是**活文档**（非冻结快照）」，§4.6 用**现在时**描述 wayfinder footage 与野心分档 | ⚠️ 反向问题：它**该改**却被 `docs/` 笼统白名单**静默放过**，会永久停在错误状态 |

对抗镜 A3 实跑：`grep -rlE "<6.1 词表>" . --exclude-dir=.git | wc -l` → **103 个文件**。
**修复**：① 白名单改为**规则化描述**而非枚举（「凡『考古层』紧邻 DOC-1/BASE-30 语境者排除」等）；
② 显式纳入 `ff-generation-constraints.md`、`openspec/issues/`、非归档存量 roadmap 包、
`.claude/settings.local.json`；③ 把 `docs/sdflow-fable5/02-module-reference.md` 从白名单**移出**并改它；
④ 裸词 `野心` 加上下文锚；⑤ 任务措辞明说「命中需人工逐条过滤，非机械 pass/fail」。

#### SR-17 · tasks 4.3 漏了 dev/runtime checkout 纪律的「还原」步 〔对抗镜 A3 独家〕
- `CLAUDE.md` 纪律原文：「…都须在开发 checkout 跑一次 `setup.sh` 才测得到——知情临时指 dev，
  **测完/合并后在运行 checkout 重跑 setup 还原**」。
- 5 个历史 archived change 改 `assets/workflow` 时 tasks 里都写了还原步
  （如 `archive/2026-07-05-three-lens-decision-framework/tasks.md:48`）；**本 change 独漏**。
- 少了这半句，运行 checkout 的全局 canonical 会在合并后继续指向旧内容。
- **附带（同镜）**：`setup.sh` 里的 `sync_principles.py --check` 是
  `if ! ...; then echo "⚠️..."; fi` ——**不是 fail-closed 门**（`set -e` 在 `if` 条件里不生效），
  警告会淹在 setup.sh 大段输出里。4.3「确认 `--check` 门绿」的验收动作应改为**单独跑**
  `python3 hack/sync_principles.py --check` 看 exit code。
- **修复**：4.3 追加还原步 / hand-off 记录，并改验收动作。

#### SR-18 · tasks 6.2「全仓 pytest 绿」在当前 baseline **不可满足** 〔对抗镜 A3 报告 · 主 session ✅隔离复跑排除并发干扰〕
```
$ /usr/bin/python3 -m pytest hack/tests/test_harden_sdflow_spec_followup_closure.py -q
FAILED ...::test_spec_authoring_requirement_ids_and_resident_identity_are_consistent
E  assert '### Requirement: SA-14 四入口选择规则' in <spec-authoring/spec.md 内容>
1 failed, 15 passed
$ grep -c "SA-14" openspec/specs/spec-authoring/spec.md   → 0
```
- 该失败**先于本分支存在**（本分支 diff 只新增 8 个文件，未碰 `spec-authoring`）。
- ⇒ 6.2 作为无条件断言不可满足：要么本 change 去修一个无关的红（scope creep），要么改验收口径。
- 对抗镜诚实声明它排除不了并发干扰；**主 session 已隔离复跑排除**。
- **修复**：6.2 改为「**相对 merge-base 无新增失败**」，或要求在隔离 worktree 里跑。
  （附带：全仓 2461 用例，本机 >280s，6.2 没给超时预算。）

#### SR-19 · 验证网测的是文档完整性，不是规划器有效性 〔Codex CEO + Codex eng + Claude eng〕
- `sdflow-roadmap` 无 `tests/`（✅亲验）⇒ **6.2 的 pytest 对本 change 主体改动零覆盖**。
- 三态路由 / 七维裁剪 / 增量落盘 / 重入 / 放弃清理 / 存量兼容——**全部只有人读终审 + 一条会空转的演练**。
- Success Metrics 四条里三条量的是「删掉的字符串 / 门禁绿」，**可以给一个更差的规划器发合格证**。
- **修复**：加一份可执行的场景核对清单（三条路由 × create/continue/replan × 中断/放弃/重入），
  作为终审 checklist 而非自动化测试（本仓无该测试面，不强求机械门——这是合法的诚实边界）。

#### SR-20 · TG-22 假设的「明确兜底路径」没有被工程化进任何运行时产物 〔Claude DX 独家〕
- proposal〔TG-22〕称在飞 wayfinder 讨论的失效影响「有**明确兜底路径**」= 手工转录 map 要点进 memo。
- 但这句只在 `decision-memo.md`（过程件）与 `design.md` Non-Goals（设计文档）——**运行时 agent 都不读**。
  delta spec 的冻结 Requirement **全文无一句**要求 agent 去读 `footage/map.md` 提炼要点。
- **后果**：半途 map 的仓续跑时走「包已存在 → continue」，B 从零拷问，历史讨论对 agent 不可见。
- **修复**：① spec 补一条 Scenario（「含 `footage/` 但无三件套 ⇒ continue 前 SHALL 提示是否先摘要写入 memo」）；
  ② 或如实把假设改为「无自动化兜底，靠操作者手工转录」。

### 中（17）

- **SR-21** 〔主 session ✅亲验〕**TG-08 命中但 design 缺两个必填槽**：`失败模式表（BASE-06）`
  与 `可观测性（BASE-11）` 在 design 的 14 个小节里皆无（只有 `## Risks / Trade-offs`，是风险叙述不是失败模式表）。
  本报告 Step1 已把失败模式表补出（见 `gstack-review.md` Section 2，**12 条错误路径 / 7 个 CRITICAL GAP**），可直接并入 design。
- **SR-22** 〔领域镜独家〕**TG-25 命中但 design 缺 BASE-29 scope-check 表**（枚举全套文档 × 是否改 × **不改的理由**）。
  领域镜已把表补出（23 行，含 2 个「**未列入**」项：`config.template.yaml`、`02-module-reference.md`）——
  BASE-29 原文强调「**未列入**比未完成更危险」。可直接并入 design。
- **SR-23** 〔领域镜独家〕**BASE-12 三镜覆盖率**：D1/D4/D5/D8 四条命中 TG-23（≥2 合理方案），
  **只有 D1 写满了三镜 + 主次判定**；D4（memo 轻量 vs 机械层）、D5（术语，候选最多的一条）、
  D8（历史存档 vs 历史记录）只有散文依据。内容其实有、格式未达标，补写成本低。
- **SR-24** 〔Claude CEO + 对抗镜 A1 + 主 session ✅亲验〕**「实战案例：博客 v2 重建」整节
  （`SKILL.md:624-635`）在骨架里无落点，四件套全文未提**；且规则 1（`:201`）与陷阱 4（`:568`）
  都用括注引用「博客 v2」案例作旁证，整节删除后成为指向真空的孤证。
  建议**删**（按 DOC-1 它本就是正文里的考古层），但要**明写**而非静默。
- **SR-25** 〔主 session ✅亲验〕**存量包有第三种形态（单文件）**：`issues-triage-2026-08/`、
  `archive/high-value-issues-cleanup/`、`archive/openspec-1.7.0-followup/` 都只有 `roadmap.md`。
  两条兼容条款（四件套包 / 含 footage 包）都没覆盖它，而收尾 ②「三件套相互引用完整」对它必然不通过。
- **SR-26** 〔Codex CEO + hr-tg voice〕**判定点①要求写 `task-log.md`，而该时点文件不存在**：
  `{name}` 在 B 起手才确定、目录在 B 起手（或直接生成路径落盘前）才建。
  诚实边界：该矛盾在现行 `SKILL.md:275` 已存在——**但本 change 把它重新写进一条新 ADDED Requirement
  并配了专门 Scenario**，是新契约面上的缺陷，不能以「现状也这样」放行。
  **修复**：改为「先在对话中显式陈述一行；包目录建立后**补记**进 task-log」。
- **SR-27** 〔hr-tg voice + Codex CEO〕**C 相位部分失败不进状态机**：状态机把「生成中」直接连到
  「三件套就绪」，无 `C-draft` 或失败恢复转换；而直接生成路径允许 memo 不存在、重入只扫未定稿 memo
  ⇒ 只写出 1-2 个三件套文件的破态**不被任何机制覆盖**。
- **SR-28** 〔Claude DX 独家 · 主 session ✅亲验〕**「B 起手三步 / 四步」四份产物二比二分裂**：
  `design.md:78` + `decision-memo.md:117` 说「四步」，`tasks.md:10` + delta spec 说「三步」。
  建议统一为「三步」（「判定进 B」是进入前提而非步骤）。
- **SR-29** 〔Claude DX 独家 · 主 session ✅亲验〕**`openspec/INDEX.md:52` 是整句陈旧**
  （含「双判据路由（explore/wayfinder/office-hours）」「票状态机 open/claimed/resolved/abandoned」
  「按野心分档」「checklist 五项软门」），而 tasks 5.5 措辞是「核对……与『野心』措辞残留」
  ⇒ 有「只替换一个词」的浅改风险。改为「按新结构整句重写」。
- **SR-30** 〔Claude eng 独家〕**三类状态机边角是沉默遗漏，不是显式接受的边角**：
  并发两 session 同包 / 建了目录但草稿 memo 写失败 / 重入命中多个未定稿包——
  本 change 自己派给 hr-tg 的 context 列了这三类，而 decision-memo「接受的边角」裁定了另外四类，
  **唯独这三类不在其中**。按基准 4 的五问，**沉默遗漏与显式裁定接受，风险性质不同**。
  补一句显式裁定即可（如「并发：无锁，后写覆盖前写——概率低、影响可逆（git 可追溯）、
  完美成本=引入锁，不做」）。
- **SR-31** 〔Claude CEO 独家 · 主 session ✅亲验〕**proposal Why 段把两类性质不同的依赖打包论证**：
  实测 `~/.codex/skills/gstack-office-hours` **存在** ⇒ office-hours **双宿主皆可用**，
  且现行 SKILL.md 的 office-hours 分支**没有任何宿主探测/降级逻辑**。
  「Codex 宿主无 X、降级常驻」只对 wayfinder/grilling/domain-modeling 成立。
  office-hours 该不该内化理由本身站得住（结构对齐 + 维护面精简），问题只在打包论证掩盖了区分。
- **SR-32** 〔Claude CEO 独家〕**「为何不并入 sdflow-spec」候选从未被分析**：design 声称「逐节同构」，
  在这种收敛程度下「两个 500+ 行 skill 长期并存」本身需要论证，D1–D14 无一条讨论过。
  **本条不主张合并**（那是加宽），只指出决策记录有洞——补一句显式论证即可。
- **SR-33** 〔Claude CEO 独家 · 主 session ✅亲验 git log〕**matt fold 的因果表述不准**：
  D2 论证是「roadmap 重构后 matt 失去全部活消费方 ⇒ 一并移除」，实际 matt 早已事实废弃。
  结论不变，措辞需准确——这直接关系 Q1 怎么拍。
- **SR-34** 〔对抗镜 A2 独家〕**裁剪基准三行只有一行有 Scenario**：正文写了「技术重构→②③④⑤⑦」
  「新产品/新项目→全七维」「商业化信号命中→①加重」，而 4 个 Scenario 只测了「技术重构」。
  后两条尤其是「信号命中即便 gate 未过也要加重①」——跨两个三态分支共用，最容易被简化成
  「只在②分支加重」。
- **SR-35** 〔Codex DX + Claude DX，两镜各实测出不同分叉〕**「与 sdflow-spec 逐节同构」过度声称**：
  design 说差异「只有两处」，实测 **≥5 处**：① B 可跳过 vs 不可跳过 ② memo 有无状态/身份层
  ③ 重入探测覆盖面 ④ **sdflow-spec 用 5 个 `references/*.md` 按需加载压密度，roadmap 骨架全内联**
  ⑤ **sdflow-spec 的 B.6（惰性钩子）+ B.7（收敛前逐条回扫）是两道防线，roadmap 只一层**
  （B.7 原文自述「B.6 漏掉的在此兜底捕获」，砍掉即砍掉兜底）。
  **修复**：改为一张分叉表，或把措辞降为「共享 A/B/C 词汇与增量落盘模式」。
- **SR-36** 〔Codex DX + Claude DX，两侧独立点名同一类〕**指令过载，且先被跳过的恰是安全/可追溯部分**。
  Claude DX **点名了三处**：**裁剪表**（agent 倾向「全跑保险」，没有机械门抓得到「没裁剪」）、
  **放弃清理**（低频 + 长节尾部）、**重入探测**（不是独立标题，而 `sdflow-spec` 把它做成「第零步」
  置于 Phase A 之前）。
  **修复**：给重入探测独立「第零步」标题置于三态路由之前；裁剪表补一条留痕要求
  （判定点①的陈述里列出实际执行的维度子集）；陷阱表补一条「放弃后半途包未清理」。
- **SR-37** 〔对抗镜 A3 独家〕**tasks 5.1「新增 ADR」缺编号/文件名/必需小节规范**：
  `openspec/adr/` 现有 36 个文件（`0001-…` 至 `0036-…`），无 template 可查，全靠读现有文件总结。
  补一句「参照现有编号规则取下一个可用编号（`0037`）」即可。
- **SR-38** 〔对抗镜 A2 独家〕**review Requirement 的三条正文承重点无独立 Scenario**：
  调用契约（整体 plan 声明）、显式覆盖、处置标注——只有默认单审/跳过/依赖失败三个场景有覆盖。
  「三件套整体 plan 调用话术」是 SR-7 明确要「存活保证」的东西，却没有验收锚。

### 低（5，一行带过 · 可审计不静默丢）

- **SR-39** 放弃清理未要求删除前向操作者**复述完整路径**，与 CLAUDE.md 全局安全规则不齐。并入 SR-5 一起改。
- **SR-40** 新增七维 B 相位的**摩擦增量**四件套里一处未承认（X1 保留的半条）。建议 Risks 补一句评估。
- **SR-41** **B 相位维度裁剪无操作者覆盖口**——review 有「显式覆盖」先例、存量形态有逃生舱、
  review 有跳过授权，唯独 B 内部的七维裁剪没有对应机制。补一句或明说取舍理由。
- **SR-42** `tasks.md` 实为 **27 条**子任务（1.1–1.8=8, 2.1–2.3=3, 3.1–3.2=2, 4.1–4.3=3, 5.1–5.6=6, 6.1–6.5=5）。
  另 tasks 无「主 spec 提升后核验」任务（archive 阶段 delta 落进 `openspec/specs/` 后再扫一遍残留词与
  逐 Requirement 对码）。
- **SR-43** `design-template.md` 实测**零命中**任何待改术语，而 tasks 2.2 把它算进「三模板术语改」——
  措辞可精确化，不影响正确性。

---

## 三、判绿的部分（同样列出，避免「只报坏消息」的失真）

| 检查项 | 结论 | 证据 |
|---|---|---|
| **spec delta 契约覆盖：有无悬空 SHALL** | ✅ **无** | 现行 spec 8 个 Requirement 逐条过：6 个被 MODIFIED/REMOVED 承接，2 个（`design.md 需求与目标态伸缩头部章`、`新项目起步的架构先行指路`）经核实不引用任何被删机制，维持不动**是正确的**。**三次独立核验一致**（Codex eng / 对抗镜 A2 / 主 session）。 |
| **3 条 REMOVED 的 Migration 是否真承接** | ✅ **三条全真** | 对抗镜 A2 逐条打开被声称的承接方 ADDED 核对文本对应，无「声称承接但实际没写」。 |
| `openspec validate --strict --type change` | ✅ 实跑通过 | `Change 'refactor-roadmap-internalize-deps' is valid` |
| `sync_principles.py --check` | ✅ 实跑绿 | `✅ 20 个投放面全部与真相源一致` |
| `sdflow:principles` 托管块保护方案是否充分 | ✅ 充分 | `sdflow-roadmap/SKILL.md` 仅 **1 个**区块（`:15`–`:154`），tasks 1.8「块外全重写、块内零字节不动」够用 |
| matt 区块是否会被 `sdflow-init update` 重铺 | ✅ 不会 | 三个 matt 小节在 `<!-- opsx-init:end -->`（`:430`）**之后**；`sdflow-init/assets/snippets/` 零 matt 命中 ⇒ 手删安全 |
| `references/` 模板改名覆盖 | ✅ 覆盖 | 5 个模板逐个 grep，命中面与 tasks 2.1/2.2/2.3 一一对上 |
| frontmatter 指路句（spec Requirement #8） | ✅ 保留 | 现 description 含「先 `/sdflow-architecture`（消费仓需已 sdflow-init）」，tasks 1.1 显式防丢 |
| 早期 handoff 草稿的简化是否被纠正 | ✅ 已纠正 | 草稿的「二路径」会静默丢掉「两关独立」，C6/D6 主动抓出并改为三态路由；C7 也补上草稿漏列的 Q3 |
| matt fold 是否违反基准 4 | ✅ 不违反 | tasks 拆成独立第 3 节，非混在 SKILL.md 重写里顺手改（因果表述另见 SR-33） |

---

## 四、镜子价值度量

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="13" 采纳="12" 裁掉="1" defer="0" 独立="10" sev="致1/高6/中3/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="25" 采纳="21" 裁掉="3" defer="1" 独立="14" sev="致1/高7/中10/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="3" sev="致0/高2/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="3" sev="致0/高3/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="0" sev="致1/高2/中1/低0" -->

**诚实边界**：分类正确性（某条 finding 该归哪个 lens）、roster 完备性、findings JSON 誊写准确
**仍是主 session 的信任边界**，emitter 只保证「给定输入的确定性归约」。
（本轮我在首次 emit 后自查出漏誊一条 hr-tg finding，已补正重出——如实记录。）

**未计入 lens 归属的 findings（4 条）**：SR-1、SR-21、SR-24（部分）、SR-25 由**主 session 自己**
在核验前提与必填槽时发现，不属任何镜的产出，故排除在度量之外而非硬塞给某个 lens。
🔴 **其中 SR-1 是本轮唯一的独家致命项**——这意味着「主 session 亲验」这一层在本轮是**承重**的，
不是走过场。

---

## 五、已应用的订正（Step4）

**已改**：37 条 findings 的修复已直接落进四件套，改动处标 `[spec-review-amendment SR-N]`
（共 **59 处**标记：spec delta 22 / tasks 18 / decision-memo 8 / proposal 6 / design 5）。
改后 `openspec validate --strict --type change` **仍绿**。要点：

| 文件 | 主要订正 |
|---|---|
| `specs/roadmap-planning/spec.md` | memo 定稿标记 `状态：DRAFT/FINAL`（SR-2）· B 停止条件三态终态（SR-6）· continue/replan 改为**不自动删**（SR-5）· 提议制**先记 memo、终稿后才写全局** + `[提议]`/`[确认]` 前缀 + 版本锚（SR-9/10/11）· 判定点①改「先陈述、建包后补记」（SR-26）· 未审待恢复**阻塞收尾**（SR-12）· 缺件存量包条款（SR-25）· 删除前复述路径（SR-39）· 维度裁剪覆盖口（SR-41）· **新增 8 个 Scenario**（create 主干 / 停止条件 / 提议写入时机 / continue 放弃 / 新产品全七维 / ①加重跨态 / 未审阻塞 / 整体 plan 话术） |
| `tasks.md` | 5.3 `OBSOLETE`→`WONTDO` + `--reason`（SR-3）· 6.2 改「相对 merge-base 无新增失败」并写明 baseline 已有无关红（SR-18）· 6.4 改构造 fixture（SR-4）· 6.1 词表加 `footage`/`三分支路由`/`Tracker root`、白名单改**规则化**并显式列 7 类（SR-7/16）· 新增 4.3 `config.template.yaml` / 4.5 还原步 / 5.6 活文档 / 6.5 缺件演练 / 6.6「保留」节逐句核对 / 6.8 主 spec 提升后核验 / 1.9 七处内嵌残留 / 1.10 实战案例显式处置 · 测试覆盖图加「是不是机械门」列 + 诚实边界（SR-19） |
| `decision-memo.md` | C1 改写（仓外 4 个消费方）+ 新增 C1b（时间线）· C3 改写为目标态论证 · C8 改写为三处 · D9 三步 · D11 状态码 · **补 4 类边角显式裁定**（SR-30/27）· **补 D4/D5/D8 三镜 + 主次判定**（SR-23） |
| `design.md` | 补**失败模式表**（13 行）+ **可观测性**节（SR-21）· 补 **BASE-29 scope-check 表**（23 行，含 2 个「未列入」项）（SR-22）· 补**与 sdflow-spec 分叉表**（6 行）（SR-35）· Risks 分发模型订正（SR-14）· 第零步重入探测提级（SR-36） |
| `proposal.md` | Why 段拆两类依赖（SR-31，含 office-hours 双宿主实测）· TG-20 分发模型订正（SR-14）· TG-22 兜底改为「无自动化兜底」（SR-20）· Success Metrics 订正 + 诚实边界（SR-18/19）· Impact 补三处遗漏文件 |

**未改（6 条，等你拍板）**：`Q1` 与 `Q2` 本身，及依赖它们的
D2 论证措辞、`tasks.md` 第 3 节（matt 删除）的去留、`proposal.md` BREAKING 段、
`design.md` 组件表 matt 行、ADR（D14）内容、以及 Q2 若选 A 需在 spec 补的「未决项」小节。

🔴 **这意味着当前盘面已不同于镜子审过的 `c78c02c`** —— 见收敛口第 3 步。

## 六、窄复核（返修增量 · 1.7 纪律要求）

设计门 Q1/Q2 拍板后（`30eb615`），按 1.7 纪律对增量 `c78c02c..30eb615`（1252 行）跑了窄复核：
**一路跨模型 voice + 一路冷子代理**，均只审增量、明确要求「不重报旧问题」。

🔴 **结果：8 条新缺陷，全部是这一轮返修引入的，无一条是旧问题。**
这直接证明「返修必须再审一轮」不是形式主义。

| # | 缺陷 | 来源 | 形态 |
|---|---|---|---|
| **NR-1** | `状态：FINAL` 定在「B 收敛时」写 —— 而 B 收敛后还要走 C 生成 + review，此间中断的半成品包**再也不被重入探测认出**（只扫 `DRAFT`）。修 SR-2 时把 C 相位的洞从「只有直接生成路径有」**扩大**到了「B 路径也有」 | voice | 修 A 引入 B |
| **NR-2** | spec 改成「continue/replan 不自动删」，但 `design.md` 状态机、`proposal.md`、`decision-memo.md` D9 **三处**仍写「只删本次新增」 | voice 报 1 处，**主 session 自查补出另 2 处** | 跨文件镜像漏改 |
| **NR-3** | 版本锚用 `git log -1` —— 对**本次要新建的 ADR** 没有可比对的 commit；且工作树未提交的改动不会让它变化 | voice | 新契约未覆盖自身产物 |
| **NR-4** | Scenario 写「跑满七维中的 ①②④⑤⑥⑦」（六维不是七维）；`design.md` 决策图的「全跑」同病 | voice | 措辞自相矛盾 |
| **NR-5** | 加了「与 sdflow-spec 实际分叉表」并在表头点名「原文曾称『差异只保留在两处』是错的」，**却没删掉 `design.md` Goals 里那句原话** —— 同一文档里靶子和打靶的话并存 | 冷镜 | 只做了修复的前半句 |
| **NR-6** | SR-36 声称「第零步置于三态路由之前」，但① 骨架散文把它列在相位 A **之后**；② 三态路由决策图**完全没同步**；③ tasks 把它塞进「写相位 B 节」的子项 —— **这条修复用来防的失效模式，被它自己的任务编排复现了一遍** | 冷镜 | 声明与落位矛盾 |
| **NR-7** | `proposal.md` 写「防线是终审人读 + 场景核对清单（tasks 6.6）」，而 6.6 是「保留」节逐句核对，**那个清单根本不存在** —— SR-19 承诺的产出物从未交付，还留了个悬空引用 | 冷镜 | 承诺未交付 + 悬空引用 |
| **NR-8** | SR-25 新增的「缺件存量包」条款无 Scenario，与同一句里的姊妹条款（存量四件套包，有 Scenario）不对称 | 冷镜 | 验收锚缺失 |

**八条已全部修复**（`7908592` + `57f1fa7`）：NR-1 改为「收尾四项全过后才写 `FINAL`」（顺带把 B 路径的
C 相位半成品也纳入重入覆盖）· NR-2 三处同步 · NR-3 加 `新建` sentinel + 如实降级为「只防已提交改动」·
NR-4 六处措辞统一 · NR-5 Goals 原句改写为指向分叉表 · NR-6 骨架顺序 + 决策图 + 任务编排三处同步
（新增独立任务 1.2，第 1 节重编号）· NR-7 补出真正的场景核对清单（**三路由 × 三生命周期 × 三中断态**
的逐格矩阵，tasks 6.8）并修正引用 · NR-8 补 Scenario。

**值得记住的两点**：

1. **NR-2 的元教训**：我在派镜子的 prompt 里**明确写了**「跨文件镜像位置漏改是高发形态」，
   然后自己就犯了，还一次犯三处；冷镜只逮到 1/3，另外 2 处是我重扫词表才出来的。
   ⇒ **派镜子时列出的高发形态，自己返修时要先自查一遍同一份清单。**
2. **NR-5/6/7 同属一个模式**：「**声称已修 → 实际只改了一半**」。三条全出自冷镜，
   且集中在同一份文档（`design.md`）与同一处交叉引用（`proposal.md` → `tasks.md`）。

### 诚实边界

🔴 **最后一次修复增量（`7908592..57f1fa7`，44 行）本身没有再过冷层。**
判据：该增量全部是上述 8 条的定点修复，且每条修完我都用 grep 重扫了对应的关键词面
（`只删本次新增` / `跑满七维` / `全跑` / `逐节同构` / 任务编号唯一性 / tasks 交叉引用存在性），
`validate --strict` 与 `anchor_lint` 均绿。按 ④ 的概率×影响÷成本，不再起第三轮。
**如实声明，不称「已全面复核」。**

## 七、收敛口

### 已完成的序列

1. ✅ **Q1 / Q2 已拍板**（2026-08-05，人：「都同意」）——
   Q1 = **A**（照原样删 matt，D2 论证改写为「历史遗留死配置 + fold 判据」）；
   Q2 = **A**（memo 加 `## 未决项` 小节 + 收尾 ④ 扩未决项闭环，零新机械层）。
2. ✅ **50 条 findings 的修复已全部落进四件套**（42 条主审 + 8 条窄复核），
   改动处标 `[spec-review-amendment SR-N]` / `〔窄复核 NR-N〕`。
3. ✅ **窄复核已跑**（见第六节）——两路冷层，8 条新缺陷全修。
4. ⏳ **待拍板**（下一步）。

### 当前状态

| 门 | 结果 |
|---|---|
| `openspec validate --strict --type change` | ✅ 绿 |
| `anchor_lint --layer spec-review` | ✅ CLEAN |
| 任务编号唯一性 / tasks 交叉引用存在性 | ✅ 自查绿 |
| 关键词面重扫（`只删本次新增`/`跑满七维`/`全跑`/`逐节同构`/`OBSOLETE`/`词条两处`/`起手四步`） | ✅ 全清 |
| checkpoint | `c78c02c` → `be9048a` → `5b1c62c` → `30eb615` → `7908592` → `57f1fa7` |

### 拍板须知

🔴 **拍板回写时的时序陷阱**：拍板批准的盘面 = 当前 HEAD（`57f1fa7`）。
按拍板回写协议，`ship-gate.design_approved: true` 与 `reviewed_sha: <40 位 OID>`
**MUST 在同一次文件写入中**落进本报告头部 frontmatter；
且若拍板前还有任何四件套改动，**MUST 先把它单独 checkpoint 提交、取得新 sha 再回写**——
否则 `/sdflow-ship` 第一次跑 gate 就会判 design 失鲜、当场 `REFUSE_START` 自锁。

### 建议

**可以放行。** 方向从头到尾没有问题（契约面无悬空 SHALL、三条 Migration 全真、
scope 判断符合基准 4、早期草稿的静默缩水已被相位 B 主动纠正）；
最初的三条致命（两条错误依据 + 一条照做必报错）与窄复核的 8 条返修洞均已定点修复并留痕。

**残余风险如实列出**（不是阻塞项，是让你知情）：
- 本 change 的主体改动（指令层行为）**无任何自动化测试面**——两道真机械门都不覆盖它。
  唯一防线是 tasks 6.8 的场景核对清单 + 终审人读。
- 最后一次修复增量（44 行）未过冷层，见第六节诚实边界。
- `tasks.md` 6.2 的 baseline 红（`SA-14`）是先于本分支存在的，本 change 不修，需另开 change。
