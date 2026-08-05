---
schema_version: 1
change: refactor-roadmap-internalize-deps
branch: feat/refactor-roadmap-internalize-deps
generated_at: 2026-08-05T21:32:39+08:00
decision_hash: f49d3d813188
---

# 决策纪要 · refactor-roadmap-internalize-deps

## 目标态

`sdflow-roadmap` 重构为与 sdflow-spec 同构的三相位结构（A 澄清 → B 七维拷问按信号裁剪 +
memo 增量落盘 → C 生成三件套），消除 wayfinder / grilling / domain-modeling / office-hours /
matt tracker 五个外部依赖并整体移除 `openspec/matt/`，review 层外部依赖原样保留。

## 承重约束

- **C1 · matt 的消费方盘点〔spec-review-amendment SR-1：原表述「无其他运行时消费方」已被证伪，改写〕**：
  **仓内**部分成立——全仓 grep，`sdflow-implement` 的 matt 引用全是出处注释
  （SKILL.md:228/459/561-562/788/797-798、impl_route.py:5/420/431），无代码读 `openspec/matt/` 路径。
  🔴 **但仓外有 4 个活消费方**：`openspec/matt/issue-tracker.md:16` 明文把 `to-tickets` / `triage` /
  `to-spec` / `qa` 列为消费方，实测 `~/.claude/skills/` 下**这四个 skill 全部已安装**；
  它们靠 `CLAUDE.md` / `AGENTS.md` 的「## Agent skills」三段找到路径，其中「### Domain docs」
  一段（指向 `openspec/CONTEXT.md` 与 `openspec/adr/`）**与 wayfinder 完全无关**。
  ⇒ 原 C1 的检验方法（仓内 grep 路径字符串）对**仓外安装、指令驱动**的消费方结构性失明。
  **移除仍可行，但依据要换**（见 C1b）；范围是否含「Domain docs」一段属人拍板项（评审报告 Q1）。
- **C1b · matt 早于本 change 已事实废弃〔SR-33〕**：git log 实测，`sdflow-issues` 生于本仓
  **首个 commit（2026-07-03）**，早于 `openspec/matt/` 建立（2026-07-10）**一周**；
  本仓自始至终用的是 `sdflow-issues`（T1…T230），matt 的 issue-tracker 角色**从未真正投入使用**。
  ⇒ D2 的正确论证是「**matt 是历史遗留死配置，独立可删；与本 change 同批做的理由是操作成本低 +
  避免半改状态**」，**不是**「因本次改动才使其孤立」。
- **C2 · roadmap-planning spec 是最大牵连面**：`openspec/specs/roadmap-planning/spec.md`
  （176 行）至少 4 个 Requirement 锚定被删机制——讨论层路由（:49-81）、footage 落盘与引用
  边界（:83-110）、review 分档（:112-129）、收尾 checklist（:131-148）。delta 必须覆盖。
- **C3 · 冻结条款的依据 = 目标态 producer，不是本仓存量〔spec-review-amendment SR-4：原表述
  「存量 footage 真实存在」已被证伪，改写〕**：实测 `find . -type d -name footage` **全仓零命中**；
  原文引的「archive 下 wco/mlh 含 footage 引用」实为 `archive/workflow-cost-optimization/memo.md:1`
  标题里的比喻词「（memo · 考古 footage）」，不是 wayfinder 产出。
  🔴 **但冻结条款仍必须有**——判据不是「本仓现在有没有」，而是「**目标态的 producer 会不会产出这种形态**」：
  本 skill 经全局 symlink 分发给一切消费仓，**旧版 skill 确实产出过 `footage/`**，消费仓存量不可见但必然存在。
  ⇒ D7 结论不变，依据从「本仓实证」换成「目标态 producer 契约 + 跨仓分发事实」。
  **连带**：验证不能拿本仓包演练（无 footage 可触发），须构造 fixture（tasks 6.4 已改）。
- **C4 ·「历史记录」被 task-log 语境占用**：现 SKILL.md:252-253 replan 条款明文
  「保留既有 task-log.md 的历史记录」⇒ D8 弃「历史记录」选「历史存档」。
- **C5 ·「考古层」同串双语义**：DOC-1 语境（rules/doc-authoring.md:63-66、BASE-30、T169、
  CLAUDE.md:183-184）指文档正文演进史，与 roadmap 语境不同概念 ⇒ 禁全局替换（D8 范围限定）。
- **C6 · gate-0 与需求真实性两关独立**：现 SKILL.md:277 + spec:51 明文「五项全过不能免除
  野心信号检查」⇒ D6 三态路由，照 handoff 二路径图实现即静默缩水。
- **C7 · office-hours 六问结构核实**：Q1-Q6 在 office-hours/SKILL.md:1096-1155，自带按
  项目阶段裁剪路由表（:1089-1092，`Pure engineering/infra → Q2, Q4 only`）⇒ 七维吸收映射
  成立；handoff 漏列 Q3（绝望具体度），吸收时补入维度①的追问弹药。
- **C8 · bundle 牵连是三处，不是两处〔spec-review-amendment SR-13：原表述「仅一处规则 + 一处史录」
  已被证伪，改写〕**：`ff-generation-constraints.md:46-47`（`wayfinder-resolved:` 前缀禁混用）
  + `workflow-history.md:27-32`（A3 演进史）**+ `config.template.yaml:41,51`**
  ——后者两行注入规则引用 `ff-generation-constraints.md` 的「wayfinder→ff 衔接契约」章节，
  而该章节在当前文件里 grep **0 命中**（既存陈旧引用）。
  🔴 **它是消费仓 `config.yaml` 的生成模版**，改动会随 init 注入每个新下游仓 ⇒ 是**活传播面**，
  按基准 4 的 fold 判据（同片文件、低 blast radius）随本次一并订正。D10 范围相应扩到三处。
- **C9 · review 层降级路径已焊**：现 SKILL.md:449「未审待恢复」不静默条款 ⇒ D1 保留外部
  依赖不新增风险。
- **C10 · 增量落盘同构先例（范围已收窄）**：sdflow-spec B.4（B 轮数无上界，一次性落盘 =
  收敛前中断全损）⇒ D4/D9 的结构论据。
  🔴 **原文「wayfinder『map 先建、票增量 resolve』本质同模式」是过度声称**
  〔spec-review-amendment SR-4〕：**落盘节奏**同模式（都是先建载体、再增量写），
  但**状态语义不同**——票有 open/claimed/resolved/abandoned 状态机 + Blocked-by 依赖图 + frontier 查询，
  memo 是纯追加文本。⇒ 本 change 只承接**落盘节奏**与 frontier 的**清单**职能
  （经 Q2 拍板补 memo 的 `## 未决项` 小节 + 收尾 ④ 闭环），
  **明确不承接** Blocked-by 依赖图与 claim 并发语义（roadmap 场景单人操作，不需要）。

## 拍板决策

### D1：review 层保留外部依赖原样（人已拍板 2026-08-05）

`/plan-eng-review`（默认档）+ `/autoplan`（野心信号档）继续作为外部依赖，不内化、不简化，
既有降级路径（未审待恢复、不静默）原样保留。
依据：① review 价值在独立冷视角，内化进同 session = 产者自审；② 拆分标准——讨论层内化
已是完整内聚交付物，review 层是另一个能力面；③ gstack 是用户长期维护的自建套件，非脆弱三方。

### D2：openspec/matt/ 整体移除（人已拍板 2026-08-05；论证经设计门复核订正 2026-08-05）

移除 `openspec/matt/` 目录 + CLAUDE.md / AGENTS.md 的 matt 区块
（Issue tracker / Triage labels / Domain docs）。**范围不变、结论不变**（设计门 Q1 复核后确认照原样删）。

🔴 **论证已订正**〔spec-review-amendment SR-1 / SR-33〕。原论证「roadmap 重构后本仓再无 matt 的
活消费方」**不成立**，正确论证是：

1. **matt 早于本 change 已事实废弃**（C1b）：`sdflow-issues` 生于本仓首个 commit（2026-07-03），
   早于 `openspec/matt/` 建立（2026-07-10）一周；本仓自始至终用 `sdflow-issues`（T1…T230），
   matt 的 issue-tracker 角色**从未真正投入使用**。⇒ 它是**历史遗留死配置，独立可删**，
   删它与 roadmap 重构**无因果关系**；与本 change 同批做的理由是 **操作成本低 + 避免半改状态**
   （基准 4 的 fold 判据：相关、低 blast radius、执行中撞到就做掉）。
2. **仓外确有 4 个消费方，但它们从未在本仓生效**（C1）：`issue-tracker.md:16` 把
   `to-tickets` / `triage` / `to-spec` / `qa` 列为消费方，这四个 skill 本机已安装。
   删配置面 = 它们在本仓失去落点——**但按第 1 条，它们在本仓本来就没被用过**，
   移除不改变任何既有工作方式。若将来要在本仓用其中某个，重新铺配置即可（低成本、可逆）。
3. **「Domain docs」一段（指向 `openspec/CONTEXT.md` 与 `openspec/adr/`）虽与 wayfinder 无关，
   仍随之删除**——它的内容（单一上下文布局）已由本仓 `CLAUDE.md` 的 OpenSpec 托管区块承载，
   保留一份 matt 语境的重复指路只会成为第二个漂移面。

牵连：T134（domain-modeling 读 matt/domain.md）前提变化，随本 change 处置（D11）。

### D3：change 名 = refactor-roadmap-internalize-deps（人已确认 2026-08-05）

### D4：memo.md = 轻量决策纪要，不搬 schema+hash 机械层（人已拍板 2026-08-05）

包根 `memo.md` 升格为相位 B 的唯一决策载体（角色对齐 sdflow-spec 的 decision-memo），
但保持轻量：头部只记包名 + 日期，无 frontmatter/decision_hash 机械核验。
规则 3 原样保留——三件套仍不引用 memo（三件套自足是长期真相源的核心属性）。
依据：hash 层在 sdflow-spec 是为 C.1 机械门服务；roadmap 无 ship gate、无 CLI 载荷消费 memo，
且下游有 review 层 + 收尾 checklist 两道兜底。跨 session 续错包的残余风险由
create/continue/replan 显式确认挡住（五问判：低概率小影响，完美成本过高）。

### D5：术语改名——「结晶」→「生成」、「野心信号」→「商业化信号」（人已拍板 2026-08-05）

- **相位 C 命名「生成」**：与 sdflow-spec 三相位名对齐（A 澄清 / B 拷问 / C 生成）；
  「结晶」是比喻词、不自明。消费面（SKILL.md / spec / memo-template / CONTEXT.md footage 词条）
  全在本次重写范围内，额外成本≈0；`docs/` 历史文档不追改。
- **「产品/商业野心信号」→「商业化信号」**（人定名，否决了我推荐的「产品化信号」）：
  词表不变（外部用户、变现、获客、用户画像未定、"要不要做这个产品"）。
  消费面无 .py/.sh 脚本硬编码（已 grep 全仓核过），SKILL.md / roadmap-template ×2 /
  spec / INDEX.md 一行，除 INDEX 外全在重写范围内。
- **「相位 A/B/C」保留不换**（人两轮探讨后确认 2026-08-05）：候选「阶段」撞管线阶段一/二/三 +
  roadmap 产物阶段（双重占用）、「步骤」撞微观动作层（步骤套步骤）、「环节」可行但需全仓
  统一换（30+ 文件 + 6 个 .py 测试锚，属独立 change）。生成期 MUST NOT 改此词。

### D6：gate-0 通过路径保留商业化信号检查——三态路由（人已拍板 2026-08-05）

```
gate-0 通过 ∧ 无商业化信号 → 直接生成
gate-0 通过 ∧ 商业化信号命中 → Phase B（裁剪到维度①，startup 味逼问）→ 生成
gate-0 未通过 → Phase B（按信号七维裁剪）→ 生成
```

依据：gate-0 验讨论充分度、不验需求真实性，两关独立（现行 spec 明文）；office-hours
内化后检查执行体 = B 维度①单维拷问，保留的结构成本归零，砍掉 = 静默缩水。
handoff 的「二路径」图据此修正为三态。

### D7：收尾 checklist 五项 → 四项 + 存量 footage 冻结（人已拍板 2026-08-05）

- ①（Review 处置，含机械脚本门）②（三件套引用完整）③（历史存档未被引用）原样保留；
  ③ 的「历史存档」覆盖包根 memo.md 与存量 footage/。
- ④（wayfinder 闭环）整项删除——检查对象（wayfinder 票）不复存在。
  🔴 **但「未决项闭环」这个能力必须有承接物**〔spec-review-amendment SR-4·设计门 Q2 拍板 A〕：
  wayfinder 的 map + 票承载的是 open/claimed/resolved/abandoned + Blocked-by + frontier 查询，
  即「**当前还剩什么没决定**」本身是结构化、可查询、跨 session 可恢复的；而 memo 是纯追加日志，
  只记「已站稳的结论」。删掉 ④ 而不补，等于把未决的规划风险变成 memo 正文里的一句话。
  这对 roadmap **尤其要命**——它的定位明确是「超出单次 change、可跨月」，正是票据模型伺候的场景。
  ⇒ **最简补法（不建新机械层）**：memo 增一个 `## 未决项` 小节（B 相位「显式延后」的维度终态
  与拷问中冒出的悬而未决问题都落在这里），收尾 checklist ④ 扩一句「未决项小节非空时须逐条标
  已决 / 显式延后（附再触发条件）/ 放弃（附理由），MUST NOT 带未决项定稿」。
  **C10 的等价性断言相应改写**：memo + 未决项小节承接的是 frontier 的「清单」职能，
  **不承接** Blocked-by 依赖图与 claim 并发语义——那两项本 change **明确不承接**，如实声明。
- ⑤ 简化为「memo 对账」：B 相位写 CONTEXT.md/adr 走提议制 + 人确认（同 sdflow-spec B.6/B.7），
  确认写入均在 memo 留痕 ⇒ 收尾逐条对照 memo 写入记录与三件套终稿，废弃 git 基线 diff 机制。
  诚实边界：绕过提议制手改 CONTEXT.md 的场景查不到（指令层约束固有边界，如实声明）。
- 存量 footage 冻结为合法历史形态（对齐 requirements.md 兼容先例）：续跑不报错、不强推迁移、
  不新增票、不要求闭环，未决票视为历史遗留；至多一行提示。

### D8：「考古层」（roadmap 语境）→「历史存档」（人已拍板 2026-08-05）

memo.md + 存量 footage/ 的统称改为「历史存档」。候选「历史记录」被否：该词已被 task-log
语境占用（replan 条款「保留既有 task-log.md 的历史记录」），同文件一词两义。
行文纪律：「归档」继续专指 roadmaps/archive/ 与 map 归档等目录动作。
🔴 范围限定：DOC-1/BASE-30/T169 语境的「考古层」（文档正文演进史残留）是另一概念，**不改**——
同串双语义，禁止全局替换。CONTEXT.md footage 词条随 wayfinder 移除重写为「历史存档」定义。

### D9：B 起手即建包目录 + 草稿 memo，放弃即删目录（人已拍板 2026-08-05）

- B 起手**三步**〔spec-review-amendment SR-28：与 spec/tasks 统一口径，「判定进 B」是进入前提而非步骤〕：
  定 `{name}` → 判同名包 create/continue/replan（**判定前移到 B 起手**）
  → 建 `openspec/roadmaps/{name}/` + 落草稿 memo.md（含 `状态：DRAFT`）。
- 重入协议：新 session 探测 `openspec/roadmaps/*/memo.md` 存在且无定稿标记 ⇒ 呈现包 +
  memo 摘要，问人「继续 B 还是新开」（与 sdflow-spec 0.3 同构）。
- 直接生成路径（gate-0 过 ∧ 无商业化信号）：维持生成时建目录，memo 可不存在。
- 拷问中途放弃 ⇒ **删包目录**（与 sdflow-spec「删分支即净」对齐；未定稿 memo 无保留价值）；
  🔴 **continue/replan 场景放弃时 SHALL NOT 自动删除任何内容**〔spec-review-amendment SR-5〕——
  原写「只删本次新增内容」不可安全实现（append-only 的 memo 上无 run-id / manifest / 段落边界，
  「本次新增」无可执行归属判据，照做会退化成猜测性删既有内容）；改为在 task-log 记一行
  「本次 B 放弃」，残留内容由下次重入探测呈现给操作者处置。create 场景删目录**前先复述完整路径**〔SR-39〕。
- 中断损失窗口 = 两次落盘之间，如实声明，不称零损失。

### D10：bundle 牵连处置（自决 2026-08-05，已向人声明无异议）

`ff-generation-constraints.md` 的 `wayfinder-resolved:` 前缀禁混用规则**保留 + 加 legacy
标注**（消费仓存量 footage 仍可能被溯源，不能删）；`workflow-history.md` 追加一条
wayfinder 路径移除的演进记录。bundle 改动后按 dev checkout 纪律跑 setup.sh。

### D11：T134 随本 change 关 `WONTDO`（自决 2026-08-05；状态码经评审订正）

前提消解：重构后本仓工作流无 domain-modeling 调用点，matt/domain.md 随 D2 删除。
实现期以 `sdflow-issues` 的 `set-status --to WONTDO --reason "<前提消解说明>"` 处置。
🔴 **原文写的 `OBSOLETE` 是非法状态码**〔spec-review-amendment SR-3，实跑复现〕：
`issues_v2.py:46-49` 的 todo 池只接受 `OPEN|PROPOSED|DONE|WONTDO`；
且 `--evidence` 只服务 `FIXED`/`DONE`，`WONTDO` 必须配 `--reason`。
根因 = 把自然语言「已过时」当成了机器状态值。

### D12：explore 移出讨论层内部路由（自决 2026-08-05）

现行「分支 A = /opsx:explore」不再是 skill 内部分支；对齐 sdflow-spec 模式——想法尚未
成形时**先 explore 再 /sdflow-roadmap**（上游可选步，SKILL.md 入口处一句指路即可）。
讨论层内部只剩三态路由（D6）。

### D13：杂项处置（自决 2026-08-05）

- 七维拷问的商业化信号词表**内联 SKILL.md**（skill 是独立分发单元，不引仓内文件）。
- 模板：memo-template.md 重写为 B 相位纪要模板（轻量，头部包名+日期）；design/roadmap
  模板改术语；long-flow-skill-paradigm.md 的 wayfinder 段落改为历史注记。
- `docs/workflow-skills/matt-pocock-workflow.md`、`setup-matt-pocock-skills.md` 等 docs/
  历史文档**不追改**（非规则源）；`docs/external-dependencies.md` **必须更新**（活文档，
  删 wayfinder/grilling/domain-modeling 依赖节）；handoff 草稿实现后删除。
- 判定留痕总则三判定点保留、随新结构重编号（①三态路由 ②review 分档 ③收尾 checklist 四项）。

### D14：ADR 一条 + CONTEXT.md 词条**三处**，实现期落（人已确认 2026-08-05；第三处经评审补入）

- ADR：「sdflow-roadmap 讨论层内化与 matt 套件移除」——三条件全中（难逆转 / 缺上下文会
  意外（存量 footage 无产出机制）/ 真实权衡（内化分界线：讨论过程是内在职责、冷审价值恰在
  外部性 ⇒ 讨论层内化、review 层留外））。
- CONTEXT.md：① footage 词条重写为「历史存档」定义（其正文含「决策**结晶**」，一并改「生成」）；
  ② 新增「商业化信号」词条；③〔spec-review-amendment SR-15〕**`ticket（实现分解单位）` 词条**——
  正文「matt 套件中 wayfinder 的讨论 ticket（map 的 `issues/<NN>`）是另一种 ticket，需限定词区分」
  与 `_Avoid_` 行的同类表述，改为历史存档语境。
- 时机均放实现期（进 tasks.md），避免全局共享文件领先实际形态。

## 接受的边角

- **B 中断损失窗口**：两次 memo 落盘之间的讨论内容中断即丢——概率中、影响小（重问一轮即可）、
  完美成本高（逐句落盘不现实）；与 sdflow-spec 同口径，如实声明不称零损失。
- **memo 无机械身份核验**（D4 的代价）：跨 session 续错包的极端场景靠 create/continue/replan
  显式确认挡——概率低、影响可逆（生成前有人门）、完美成本 = 搬整套 hash 机械层。
- **⑤ 简化后的盲区**（D7 诚实边界）：绕过提议制手改 CONTEXT.md/adr 的写入收尾门查不到——
  属指令层约束固有边界，原 git 基线机制也只覆盖长档路径，非本次新增缺口。
- **拷问中途放弃未删目录**：残留半途包由下次重入探测呈现给人处置，不设自动清扫。
- **并发两 session 写同一包**〔spec-review-amendment SR-30：原为沉默遗漏，此处补显式裁定〕：
  本 skill 无锁机制，后写覆盖前写。**根因** = 无进程间协调层；**概率**低（单人操作场景）；
  **影响**可逆（三镜：系统镜——无状态损坏，git 可追溯回滚；用户镜——最多丢一次拷问的增量；
  开发循环镜——无）；**完美成本** = 引入 lockfile + 心跳，与「零机械层」的 D4 取向冲突；
  **简化方案** = 不做，如实写进 SKILL.md 让操作者知情。**主次：开发循环镜为主，不做。**
- **建了目录但草稿 memo 写失败**〔SR-30〕：下次重入扫不到 `状态：DRAFT` 行 ⇒ 呈现为「已存在的空包」，
  走 continue/replan 分支，操作者可见可处置。概率低、影响可逆、无需额外机制。**接受。**
- **重入命中多个未定稿包**〔SR-30〕：**不再是遗漏**——delta spec 已补规范（逐个呈现由操作者选其一，
  未选者原样保留）。
- **直接生成路径的半成品不被重入覆盖**〔SR-27〕：该路径允许 memo 不存在，而重入只扫未定稿 memo。
  概率低（C 相位连续写盘、无人类往返）、影响可逆（残包可见可手删）、完美成本 = 给直接生成路径
  也强制建 memo（与 D6 的轻量意图冲突）。**接受，如实声明不称已覆盖。**

## 三镜代价

〔spec-review-amendment SR-23〕本次命中 TG-23（≥2 合理方案）的决策共 **4 条**：D1 / D4 / D5 / D8。
原文只写满了 D1，其余三条的三镜与主次判定补如下（内容原本散在各自「依据」段，此处按 BASE-12 结构化）。

### D4（memo 轻量纪要 vs 搬 sdflow-spec 的 schema+hash 机械层）

- **系统镜**：不搬 ⇒ 无 frontmatter/hash 解析面、无第二份 schema 要维护；代价是**失去身份核验**
  （跨 session 续错包无机械拦）。🔴 注意：hash 在 sdflow-spec 是**一物两用**（身份 + draft/final 状态位），
  只砍身份核验、**状态位必须留**（见 SR-2 的 `状态：DRAFT/FINAL`）。
- **用户镜**：memo 保持可手写、可随手读，不因机械字段变成「工具产物」。
- **开发循环镜**：省掉一整套 emit/verify 脚本与其测试；roadmap 无 ship gate、无 CLI 载荷消费 memo，
  搬过来的机械层没有下游消费者。
- **主次判定：开发循环镜为主**——机械层的价值全部来自下游消费者，而 roadmap 侧没有；
  身份核验的残余风险由 create/continue/replan 显式确认承接（低概率、生成前有人门）。

### D5（术语改名：「商业化信号」vs「产品化信号」；「相位」保留 vs 换「阶段/步骤/环节」）

- **系统镜**：消费面已 grep 全仓核过——「野心信号」无 `.py`/`.sh` 硬编码，改名零机械风险；
  而「相位」若换成「环节」需动 30+ 文件 + 6 个 `.py` 测试锚（跨文件类型的重命名面，风险量级完全不同）。
- **用户镜**：「商业化信号」比「产品/商业野心信号」短且自明；「结晶」是比喻词、不自明，「生成」对齐兄弟 skill。
- **开发循环镜**：前两个改名的消费面全在本次重写范围内，额外成本≈0；「相位」改名属独立 change 的量级。
- **主次判定：系统镜为主**——决定「改哪个不改哪个」的是消费面大小与是否跨文件类型，不是措辞好坏。
  ⇒ 改前两个、保留「相位」。

### D8（「历史存档」vs「历史记录」）

- **系统镜**：「历史记录」已被 task-log 语境占用（replan 条款明文「保留既有 task-log.md 的历史记录」），
  同文件一词两义 ⇒ 未来任何针对该词的检索/改名都会误伤。
- **用户镜**：两个词可读性相当，无实质差别。
- **开发循环镜**：选「历史存档」可安全地做范围限定替换；选「历史记录」则每次都要人工判语境。
- **主次判定：系统镜为主**——一词两义的代价在检索与改名时反复付，且不可机械消解。

### D1（review 层保留外部依赖 vs 内化）
- **系统镜**：仓库继续保留 `/plan-eng-review` + `/autoplan` 两个 gstack 依赖（降级路径已焊，
  失效不静默）；耦合面不变、无新增。
- **用户镜**：新机器未装 gstack 时 review 走「未审待恢复」提示，多一步安装动作。
- **开发循环镜**：本次 change scope 收敛为一个完整内聚交付物（讨论层内化），不膨胀；
  冷审独立性不因内化受损。
- **主次判定**：开发循环镜为主——scope 内聚是一次做完的前提；系统镜代价可接受。
