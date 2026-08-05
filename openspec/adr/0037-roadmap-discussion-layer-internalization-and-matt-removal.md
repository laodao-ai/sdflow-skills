# 讨论层内化进 sdflow-roadmap（review 层留外），openspec/matt 作为历史遗留死配置随之移除

> 状态：**Accepted**（2026-08-05，`refactor-roadmap-internalize-deps` 拷问阶段收敛，人已拍板）·
> 关联 change：`refactor-roadmap-internalize-deps`

## Context

`sdflow-roadmap`（635 行）此前的讨论层是三分支路由（explore / wayfinder 长档 / office-hours
前置验证），外部依赖 `wayfinder` / `grilling` / `domain-modeling` / `office-hours` 四个第三方
skill，其中 wayfinder 一支携带宿主探测 + 三层降级路径 + `openspec/matt/issue-tracker.md`
preflight 校验，机械面（footage 落盘、map 再入、tracker preflight、基线记录）约 150+ 行。
同构参照 `sdflow-spec/SKILL.md` 已把「B 轮数无上界 ⇒ 增量落盘收窄中断损失」的三相位结构
（A 澄清 → B 拷问 + 纪要增量落盘 → C 生成）在 change 生产路径实证过。

与此并行，`openspec/matt/` 目录（4 文件：`issue-tracker.md` / `triage-labels.md` /
`domain.md` / `setup-matt-pocock-skills-handoff.md`）是 2026-07-10 铺设的第三方套件
（matt Pocock workflow）消费约定文件，`CLAUDE.md` / `AGENTS.md` 各有三个托管区块
（Issue tracker / Triage labels / Domain docs）指向它。

设计阶段评审（spec-review-amendment）证伪了两处原始论证：

- 〔SR-1〕原表述「matt 无其他运行时消费方」不成立——`issue-tracker.md:16` 明文把
  `to-tickets` / `triage` / `to-spec` / `qa` 列为消费方，这四个 skill 在本机 `~/.claude/skills/`
  下**全部已安装**。「无消费方」类断言的检验面必须跨出仓库边界，指令驱动的消费方不会在
  仓内 grep 里现形。
- 〔SR-33〕原表述「roadmap 重构后 matt 失去全部活消费方，因而一并移除」的**因果关系不准**：
  `git log` 实测 `sdflow-issues` 生于本仓首个 commit（2026-07-03），早于 `openspec/matt/`
  建立（2026-07-10）**一周**；本仓自始至终用 `sdflow-issues`（T1…T230）追踪工作项，
  matt 的 issue-tracker 角色**从未真正投入使用**。删它与 roadmap 重构**无因果关系**。

## Decision

**两条独立但同批处置的决策，理由各自成立：**

### ① 讨论层内化（sdflow-roadmap 重构核心）

wayfinder / grilling / domain-modeling / matt tracker preflight 四个外部依赖被吸收进
`sdflow-roadmap` 自身的三相位结构（对齐 sdflow-spec 词汇与节奏，但非逐节同构——
见 `design.md`「与 sdflow-spec 的实际分叉表」）；office-hours 六问吸收为七维拷问表的
维度①。**review 层（`/plan-eng-review` + `/autoplan`）保留为外部依赖，不内化。**

**权衡点一（内化分界线）**：讨论过程是本 skill 的内在职责（拷问、裁剪、增量落盘都发生在
产出决策本身的同一条主线上），而 review 的价值恰恰在于**外部性**——同一 session 内化 review
等于让产者自审，失去独立冷视角。拆分标准（CLAUDE.md 基准 4）也支持这条线：讨论层内化本身
已是一个完整内聚的交付物，review 是另一个能力面，不该混在一起内化或简化。

### ② openspec/matt/ 整体移除

删除 `openspec/matt/` 整目录（4 文件）+ `CLAUDE.md` / `AGENTS.md` 的三个托管区块。

**matt 移除论证（按订正后的 D2，替换原「因本次改动才孤立」的因果表述）**：

1. **历史遗留死配置，独立可删**——matt 早于本 change 已事实废弃（见 Context 的 SR-33
   证据）：本仓自始至终用 `sdflow-issues` 追踪工作项，matt 的 issue-tracker 角色从未真正
   投入使用。**这条论证不依赖 roadmap 重构是否发生**——即便不做本次重构，matt 同样是可以
   独立删除的死配置。
2. **仓外确有 4 个已安装消费方，但它们在本仓从未生效**（见 Context 的 SR-1 证据）：
   `to-tickets` / `triage` / `to-spec` / `qa` 靠 `CLAUDE.md` 三区块找到 `openspec/matt/`
   路径，但按第 1 点，本仓的实际工作流从未走过这条路径。移除**不改变任何既有工作方式**；
   若将来要在本仓用其中某个 skill，重新铺配置即可（低成本、可逆）。
3. **「Domain docs」一段与 wayfinder 无关，仍随之删除**——其内容（单一上下文布局：
   `openspec/CONTEXT.md` + `openspec/adr/`）已由 `CLAUDE.md` 的 OpenSpec 托管区块承载，
   保留一份 matt 语境的重复指路只会成为第二个漂移面。
4. **与本 change 同批做的理由 = 操作成本低 + 避免半改状态**（CLAUDE.md 基准 4 的 fold
   判据：相关、低 blast radius、执行中撞到就做掉），**不是**「roadmap 重构导致它孤立」。
   任务拆分上 matt 移除是 `tasks.md` 独立的第 3 节（3.1/3.2），不是混在 SKILL.md 重写细节
   里的顺手改动，符合基准 4「一个 change 一个完整阶段结果」的拆分标准——两条决策各自独立
   成立，只是共享同一次落盘窗口。

**权衡点二（能力承接边界）**：wayfinder 的 frontier（`issues/<NN>`）在其票状态机上
承载两类职能——① 未解决问题的**清单**（哪些还没做完）② `Blocked-by` **依赖图** +
`claimed` **并发语义**（多票协作、认领防冲突）。内化后的 `memo.md` 新增 `## 未决项`
小节，**只承接①**：维度终态为「显式延后」者与拷问中冒出但本次不解决的问题，逐条落该
小节并附再触发条件。**明确不承接②**——`Blocked-by` 依赖图与 `claimed` 并发语义服务的是
「多票并发、需要防冲突协调」的场景，而 roadmap 场景是**单人操作**（一个人在一个包里拷问、
落盘、生成），不需要这层协调机制。这一边界如实写进「当前方案代价」，不是疏漏。

## Considered Options

- **本方案（讨论层内化 + review 层留外，matt 整体移除，选中）**：依据见上。
- **讨论层内化时把 review 层一并内化**（砍掉）：与权衡点一冲突——review 的独立冷视角价值
  会被同 session 产者自审吞掉；且 gstack 是用户长期维护的自建套件、非脆弱三方，没有内化
  它的必要性压力。
- **matt 只删仓外确有消费方为 0 的部分，保留「Domain docs」段**（砍掉）：`openspec/CONTEXT.md`
  + `openspec/adr/` 的布局说明已在 `CLAUDE.md` 托管区块里存在一份，保留 matt 语境的第二份
  会形成漂移面，且违反本仓一贯的单一源纪律。
- **matt 不随本 change 处置、另开单独 change**（砍掉）：按基准 4 的 fold 判据，matt 移除
  与本 change 相关（同属治理面收口）、blast radius 低（4 个仓外消费方从未在本仓生效）、
  执行中已撞到（roadmap 重构本就要清理 `openspec/matt/issue-tracker.md` preflight 引用）
  ⇒ 应 fold 进当前 change，不 defer。**注意**：fold 的理由是操作成本与执行时机，
  **不是**「因本次改动才使其孤立」——那条因果已被 SR-33 证伪，是本 ADR 要订正的核心。
- **memo 的 `## 未决项` 承接完整 frontier 语义（含 Blocked-by 图 + claimed 并发）**（砍掉）：
  roadmap 场景单人操作，不存在票并发冲突的真实需求；承接完整语义等于给一个没有多人协作
  压力的场景搬来协作工具的复杂度，属于 CLAUDE.md 基准④「简化只能砍防御深度、不能砍目标
  范围」中可以合法砍掉的低概率边角（这里连边角都算不上——场景本身不产生该需求）。

## Consequences

- **仓外 4 个已安装 skill（`to-tickets` / `triage` / `to-spec` / `qa`）在本仓失去落点**：
  它们此前从未在本仓真正被使用（结论已由 SR-33 的 git log 证据支撑），移除不改变任何既有
  工作方式；未来若要启用，重新铺配置即可（低成本、可逆），不视为破坏性变更。
- **T134**（`domain-modeling` 不识别 `openspec/matt/domain.md` 路径配置）的前提消解——
  `matt/domain.md` 随本 change 删除，该 issue 关 `WONTDO`（详见 `decision-memo.md` D11）。
- **memo 的未决项承接能力有边界**：多票并发协作场景（若未来 roadmap 场景演变出这类需求）
  不由 `sdflow-roadmap` 自身解决，需要另一层机制；本 ADR 不预留该扩展点，按 CLAUDE.md
  基准④「不为低概率、影响小的问题纠结完美方案」处理。
- **回滚代价**：单分支未合并前 `git checkout main` 即净；合并后回滚 = revert merge commit——
  `openspec/matt/` 目录与 `CLAUDE.md` / `AGENTS.md` 三区块随 revert 恢复，无不可逆动作
  （matt 目录本身不含任何本仓生成的活数据，删除前的最后状态即历史快照）。
- **`sdflow-roadmap/SKILL.md` 的实际重写（三相位骨架、七维拷问表、三态路由等）不在本 ADR
  范围内**——本 ADR 只记录「内化 vs 留外」的分界线决策与 matt 移除的治理论证，实现细节的
  权衡记录见本 change `decision-memo.md`（D1、D2、D9/C10）。
