# 设计：让 spec 工作流各阶段尽量连续自动运行

> **定位**：`openspec/workflow/workflow.md` 现状是 15 步手动 runbook（每步手动粘命令 + 2 个 `/clear` 会话断点 + 2 个 HARD-GATE）。
> 本文记录"把这些 step 尽量连续自动运行"的重构设计，按阶段逐段定稿。
> 状态：阶段一、二 + 提交自动化**已定稿**；阶段三及以后**讨论中**。

---

## 一、背景：15 步里真正的卡点只有 4 类

把每步按"自动化本性"归类后，真正让人必须手动接力的只有 4 类（★），其余 11 步都是机械串接（现靠手动粘命令接力）：

```
  卡点类型             出现处                本性              处理
  ────────────────────────────────────────────────────────────────
  人类多轮对话         grill                 价值在来回对抗    保留(对话岛,不折叠)
  人类批准门 HARD-GATE 批设计 / 批修复        需人类判断        保留但减负
  会话断点 /clear      评审前 ×2             为评审独立性      ★用子代理独立性替代(见原则2)
  merge 单向 git       opsx-done 内          不可逆            已默认执行,保留
  ────────────────────────────────────────────────────────────────
  其余 11 步(生成/评审/收尾)                  机械串接          自动串接 / 合并成编排 skill
```

## 二、全局设计原则（贯穿所有阶段）

1. **只在"真人类停顿"处断**：grill 对话、批设计门、批修复门、merge。其余全部连续自动流。

2. **子代理独立性替代 `/clear`**（最关键）：
   - `/clear` 唯一作用是给评审独立上下文。但 `spec-review`/`impl-review`/`subagent-dev` 的评审**本来就 fan-out 到 fresh-context 子代理**——独立性是"子代理冷上下文"给的，不是 `/clear` 给的。
   - 依据：`reference/quality-layering.md` L20-22 自认 `/clear` 在子代理独立性之上**只剩边际收益**。
   - 决策：**去掉两个 `/clear`**，评审以 fresh 子代理 dispatch 保独立，管线连续跑。
   - 接受的代价：评审末尾"对抗裁决+拍板"留在热主 session（它看过生成过程），有一丝合成层偏置。按文档"边际"判断接受之。
   - **〔grill-amendment〕反静默压制（消解与 §7.2 的矛盾）**：§7.2 把"热 controller 说服放过真问题"当严重失效来防（故要冷 impl-review 兜底）——同一偏置在合成层不能只判"边际"了事。真正的危险不是抽象偏置，是**热合成层在 finding 到达人眼/报告前把它静默丢掉**（spec 侧尤甚：spec-review 就是设计审本身，后面无冷 backstop；被合并阶段裁掉的 finding 永远进不了设计门）。故焊死规则：**热主 session 的对抗裁决只能降级 / 批注、不得静默丢弃 reviewer 子代理的 finding**；每条子代理 finding MUST 进报告——即便判不成立，也落成"〔主 session 已裁掉〕F-x：原始发现 + 裁掉理由"。人类/审计因此看得见**被裁了什么、凭什么裁**。spec-review 与 impl-review 两侧同此规则。与 Q1 假✅、Q2 反静默守卫、G2 决策摊进报告同一元原则：**任何一层评审覆盖不得无声蒸发。**

3. **中途 AskUserQuestion → 决策全登记进报告**（连续性的开关）：
   - 评审 skill 原本撞到"≥2 方案 / 核验不了的事实"会**中途停下 AskUserQuestion**——这是交互断点，让 skill 没法一口气跑完。
   - 改为：撞到决策点就把**选项+推荐+各分支后果**写进报告，继续跑完；人工在**末尾一次性**过报告拍板。
   - 为何安全：评审 findings **互相独立、不级联**（不像 grill 的答案决定下一分支该问什么），攒到报告一次决即可。甚至更好——报告里摊开两分支后果树，比中途弹窗看得更全。

4. **升级安全（绝不改上游插件）**：所有定制写在**我们能控的两处**——① `laodao-skills`（含 opsx-project-init 的 workflow bundle 源 + 自制 skill + recorder 脚本）② 消费仓 per-project 的 `config.yaml`；**绝不编辑** superpowers / openspec / gstack 插件文件。与注入点 B 同构。

5. **每步产物即时 checkpoint 提交**（见第五节）：底层压一个共享脚本兜底确定性，不用 hook 驱动提交。

6. **改在权威源、不改消费仓副本**（关键方向，易漏；本 change 归属 laodao-skills 的根因）：
   - **权威源 = `laodao-skills` 仓**：① workflow bundle 源 `opsx-project-init/assets/`（`assets/workflow/` 的 workflow.md / trigger-catalog.md / reference/quality-layering.md / spec-checklists / code-checklists、review UI、hooks、checkpoint 脚本）② 自制 skill 目录本身（`spec-review/`、`impl-review/`、`opsx-done/`、`buglist-recorder/`、`todolist-recorder/` + 新增 codex outside-voice helper）。
   - **消费仓副本 = 任何项目（含 laodao-skills 自己 dogfood 的）** `openspec/workflow/`、`openspec/tools/`、`hack/`——经 `opsx-project-init update` 重拉刷新。
   - 改动 MUST 在**权威源**做；消费仓走 `update` 采纳。**禁止只改消费仓副本**（update 覆盖 → 丢改动/漂移）。例外：`config.yaml` per-project（update 跳过），在消费仓改。
   - **bundle 结构调整（B1）**：review UI 的 `tools/` 归入 workflow bundle——源 `assets/review-tool/tools/` → `assets/workflow/tools/`；部署落点 `openspec/tools/` → `openspec/workflow/tools/`。需同步改 opsx-project-init 部署逻辑 + serve.sh/review.html/CLAUDE.md 的 `tools/` 路径引用。
     - **〔grill-amendment〕半归位（实现揭出的服务器根约束）**：review 工具靠「HTTP 服务器根 = `openspec/`」+ 根相对资产路径（`/workflow/tools/engine.js`）工作，而被审内容（`changes/`、`specs/`、`roadmaps/`）在 `openspec/` 层、**在 `workflow/` 之上**。故原文「serve.sh / review.html **整组随行**进 `workflow/`」不可行——一旦离开 `openspec/` 根：① serve.sh `cd $DIR` 起的服务器根会变成 `workflow/`，`/changes/<name>/…` 全 404；② engine.js 从 `window.location.pathname` 推 scope，根 review.html 须落 `/review.html` 才得 scope=`""`（全树）。**定案：只把工具机械 `tools/` 归入 `openspec/workflow/tools/`（随 copy_bundle 自动部署），serve.sh + 根 review.html 留 `openspec/` 根**（服务器根锚，不动，engine.js 不碰）；仅 review-stub.html 资产路径 `/tools/` → `/workflow/tools/`，+ 两个读模板的生产者（`change-review-stub.py`、`gen_review_stub.py`@opsx-roadmap-planner）改模板路径。

---

## 三、阶段一：设计与规格生成（`ff` + `grill`）——不变 + 加提交

- **流程不变**：`opsx:ff`（生成 proposal/design/specs/tasks）→ `grill-with-docs`（对抗压测：死磕分支 + 对齐术语 + 查代码 + 落 ADR）。
- **grill 是全流程唯一不可折叠的人类对话岛**，保留其多轮交互本性。
- **新增提交点**：
  - `ff` 完成 → checkpoint 提交生成产物（spec 文件在 grill 改动前先落点）。
  - `grill` **收敛后** → checkpoint 提交 design/ADR/术语更新（`/clear` 或评审前先落点）。
  - 机制见第五节（grill 多轮中途**不**提交，只在收敛后一次性提交）。

---

## 四、阶段二：规格评审——合并成一个编排 skill

### 4.1 现状 → 目标

现状是 3 个动作：`autoplan`（条件）→ `spec-review` → **step 7 手动把两份报告合并成 spec-review-verify.md**。
目标：折成**一个编排 skill**（沿用旧名 `spec-review`），直接产出**一份** `spec-review-report.md`。手动合并步（step 7）消失，两份文档 collapse 成一份。

```
  合并后的 spec-review（阶段2编排器）
  ┌──────────────────────────────────────────────┐
  │ Step1  invoke autoplan → 吃其 findings         │  ← 【决策：先按每次都跑】
  │        (autoplan 的自动决策也登记进报告)        │     (偏重,可回退成条件触发)
  │ Step2  spec-review fan-out(领域镜+对抗镜+接地镜) │  ← 主审,一直跑
  │        以 fresh 子代理 dispatch(替代 /clear)     │
  │ Step3  去重合并 + 决策登记 → 一份 report        │  ← 无中途 AskUserQuestion
  └──────────────────────────────────────────────┘
                    │
          人工 review spec-review-report.md          ← HARD-GATE(批设计),减负成"读一份报告"
```

### 4.2 关键决策（本阶段已定）

- **[采纳] 删中途 AskUserQuestion，决策全登记进报告**（原则3）。评审 findings 不级联，安全。
- **[采纳] 沿用旧名 `spec-review`**（虽已编排 autoplan，省改动面）。
- **[定] autoplan 先按每次都跑**（不再"高风险才跑"）。可回退开关：普通变更空跑四镜偏贵，日后想收回条件触发随时改。
- **防重叠**：现状规定 autoplan 已含 eng 镜、spec-review 不再重复跑 eng——合并后这条防重叠要写进 skill，别让 autoplan 的 eng 视角与领域镜重复计数。

### 4.3 报告决策登记区格式

```
  spec-review-report.md · 决策登记区
  ┌─────────────────────────────────────────────────────┐
  │ [自动决策] D1  autoplan/裁决已定,附理由,默认接受可覆盖  │  高置信 → 默认采纳
  │ [需拍板]  Q1  ≥2 方案: 选项A/B + 推荐 + 各自后果       │  人工 review 时勾
  │ [需拍板]  Q2  核验不了的事实(函数名/字段/API 路径)     │  人工确认
  │ [已裁掉]  X1  reviewer 原始发现 + 主 session 裁掉理由   │  反静默压制,可审计(不静默丢)
  └─────────────────────────────────────────────────────┘
```

> **〔grill-amendment〕"已裁掉"区（反静默压制）**：热主 session 对抗裁决时判为"不成立"的 reviewer finding **不得静默丢弃**，须落入本区（原始发现 + 裁掉理由）。人类设计门可复核"被裁得对不对"。impl-review 的 `code-review-report.md` 同设此区。

### 4.4 阶段二的 buglist / todolist：次要产物，语义要拎清

**阶段二审的是设计/规格，还没实现** → 绝大多数 finding 归宿是**当场改设计**（标 `[spec-review-amendment]`）或**进报告决策区**，不是 buglist。真正外溢的只有边角两类：

```
  finding 类型                          →  归宿
  ────────────────────────────────────────────────────────────
  设计缺陷/风险/歧义(可当场改)          →  改 design/specs, 标 [spec-review-amendment]  ← 主产物
  需人拍板(≥2 方案/核验不了的事实)      →  spec-review-report.md 决策区              ← 主产物
  ─────────────────────────────────────────────────────────────
  接地镜读真实代码时撞见的【既有】bug   →  buglist(顺手记,非本 change 引入)          ← 次要,偶发
  超本次范围的改进想法/主动延后的关注点 →  todolist                                 ← 次要
```

- **buglist 唯一合法来源 = 接地镜**：核验 spec 主张时撞见现网代码本身的 bug（跟本 change 无关但发现了）。设计缺陷**不算 bug**（还没实现，谈不上"坏"），别往 buglist 塞。
- 报告 findings 区给这两类各留一个小节 + 一句话带过（可审计，不静默丢），别喧宾夺主。

### 4.5 阶段二结束

= 人工 review **一份** `spec-review-report.md`（已替你合并 autoplan+spec-review、所有决策连选项带推荐摊开）→ 批准 → 进阶段三。

---

## 五、提交自动化设计（贯穿全流程）

### 5.1 结论：不用 hook 驱动提交

"某个逻辑步骤完成"**不是 hook 能看见的事件**：

- **Stop hook 每回合都触发**，分不清"ff 跑完"和"grill 对话中的某一轮"。
- **grill 多轮增量改 ADR**：Stop-hook-见变更就提交 = grill 过程中狂提交碎 commit（要的是收敛后一次）。
- **PostToolUse on Skill 也不行**：Skill 工具加载完就返回，不等实际工作做完。
- **编排器内部小阶段边界**（autoplan 子步 → spec-review 子步）在**一次 skill 调用内部**，任何外部 hook 都看不见。

一句话：**"逻辑步骤完成"是语义，不是事件；hook 只能反应事件。**

### 5.2 正确做法：提交 = 步骤的显式收尾动作 + 共享脚本兜底

```
  边界类型                          谁能看见         →  提交机制
  ──────────────────────────────────────────────────────────────────
  skill 之间 (ff→grill→评审)        我们的 step prompt →  prompt 末尾追加"完成后 checkpoint-commit"
  skill 内小阶段 (autoplan→          只有 skill 自己    →  编排 skill 内置提交步(我们自制,直接写进去)
    spec-review,在编排器内)
  多轮对话中途 (grill 每一轮)        没有可靠事件       →  不提交,等 grill 收敛后一次性提交
  ──────────────────────────────────────────────────────────────────
  底层确定性  全部调用同一个 hack/checkpoint-commit.sh  (git add -A + 固定 Conventional message)
```

- **共享脚本理由**：本机三个提交坑一次焊死——① commit message **禁 `\` 续行+heredoc**（本机 shell 会损坏）；② `core.fileMode=false` 权限变更要显式 `--chmod`；③ Go 文件 CRLF 别被 gofmt churn。脚本接一个步骤名参数，产出 `checkpoint(ff): 生成 proposal/design/specs/tasks` 类固定格式 message。
- **别和 `/commit-message` skill 混**：那个交互式，适合**最终**提交；checkpoint 是自动过场提交，用轻量脚本、不交互。

### 5.3 hook 唯一该出场处：安全网（只警告，不提交）

可选：`SessionEnd`/`Stop` hook 检测 `openspec/changes/` 有未提交产物就打印"⚠️ 有未 checkpoint 的产物，忘了收尾提交？"。只提醒不动手——既不 grill 中途乱提交，又兜住"模型忘了 commit"。这才是 hook 的正确用法：确定性守卫，不是确定性动作。

### 5.4 连带决策（已定）

- **[定] 不 squash 碎 commit**：一个 change 分支会有 ff/grill/spec-review/每实现任务/每 review 十几个 commit，ff 合回 master 就是十几个落主干。但现状分支**本来就是**这种粒度（subagent-dev 逐任务提交），保持一致 + 给细粒度回退点。本环境 `git rebase -i` 不可用，squash 只能 soft-reset 重提会丢粒度，不做。
- **opsx-done 兼容**：opsx-done 的 commit 步**已兼容**"实现期已逐 commit"（那时只提交归档+spec 同步这批收尾变更）。
- **[定] 阶段2编排器内部提交 2 次**：autoplan 子步产出 → 提交；spec-review 子步产出 report+amendments → 提交。留细粒度。

---

## 六、决策速查表

| # | 决策 | 取值 | 状态 |
|---|------|------|------|
| G1 | `/clear` 处理 | 去掉，子代理 fresh-context 替代独立性。〔grill-amendment〕补**反静默压制**：热合成层裁决只能降级/批注、禁静默丢 reviewer finding，被裁项连理由进报告"已裁掉"区（spec/impl 两侧，消解与 §7.2 矛盾） | ✅ 定 |
| G2 | 中途 AskUserQuestion | 删，改报告决策登记 + 末尾单次人工 review | ✅ 定 |
| G3 | 升级安全 | 定制只在 laodao-skills 权威源 + 消费仓 config，绝不改插件 | ✅ 定 |
| G4 | 提交驱动 | 不用 hook；显式收尾动作 + 共享脚本；hook 仅做警告安全网 | ✅ 定 |
| G5 | squash | 不 squash，保持碎 commit | ✅ 定 |
| P1 | 阶段一 | ff+grill 不变；ff 后、grill 收敛后各 checkpoint 提交 | ✅ 定 |
| P2 | 阶段二编排 | autoplan→spec-review→一份 report，合并成 skill（沿用名 spec-review） | ✅ 定 |
| P2b | autoplan 频率 | 先每次都跑（可回退条件触发） | ✅ 定(provisional) |
| P2c | 阶段二内部提交 | 2 次（autoplan 子步 + spec-review 子步） | ✅ 定 |
| P3a | 阶段三串接 | writing-plans→subagent-dev→impl-review→opsx-done 连续自动跑，无 `/clear`、无人类门 | ✅ 定 |
| P3b | 注入点B（domain 附终审） | **留** —— 循环内命中即触发 subagent-dev 的 fix 子代理+re-review 即时闭环，事后审无此机制 | ✅ 定 |
| P3c | impl-review | **每次全跑·独立冷视角·强制**（实测能抓真问题，非边际）；并入 gstack/review(scope+完成度)+领域镜+对抗镜+历史镜+置信过滤 | ✅ 定 |
| P3d | 官方 /code-review step | 去掉（subagent-dev production-readiness + impl-review 已覆盖；本地合并无需 gh 留痕） | ✅ 定 |
| P3e | 阶段三人类门（旧 step14） | 去掉 —— 过设计门后自动跑到 merge；能修的自动修，修不了的进 buglist/todolist → 另开 change 清理 | ✅ 定 |
| P3f | verify 位置 | 留在 opsx-done（所有修复之后，避免 stale） | ✅ 定 |
| P3g | hand-off.md | **新增**，替代 code-review-verify.md；opsx-done 内 verify 后 archive 前产出；异步人类再入口 + 下个 change 种子 | ✅ 定 |
| P3h | verify 防假✅〔grill-amendment〕 | 去人类门的**前置条件**：(a) 每条 Requirement 的 ✅ 必附机验锚点(测试名/commit/文件行)，无锚点✅降级 gap；(b) verify 子代理强模型+"Do Not Trust"冷启、**禁弱模型**；(c) hand-off 不继承 verify✅、引用项须独立复核。据真实事故 zhws T45/T46 假✅。见 adr/0001 | ✅ 定 |
| I1 | issues 目录结构 | `issues/{buglist,todolist}/*.md` + `issues/INDEX.md` + `issues/batches.md`（子目录版，near 原地重命名） | ✅ 定 |
| I2 | INDEX.md | **只生成·禁手改**，加 `reindex` 命令从 dated 文件重建（脚本一致性哲学，杜绝第三漂移源）。〔grill-amendment〕reindex **顺带同步批次状态**（拿 item 池当 ground truth，焊死 batches.md 状态漂移） | ✅ 定 |
| I3 | 批次维度 | 独立 `批次` 列 —— 源(provenance,不可变) / 批次(triage,可变) / status(生命周期,回归干净) 三分家 | ✅ 定 |
| I4 | 批次 key | 用**清理 change 名**（灵活；roadmap 阶段也可当批次容器） | ✅ 定 |
| I5 | sweep 时机 | 挂进 opsx-done 生成 hand-off 那步，每 change 完成自动分诊本 change 新增 OPEN 项 | ✅ 定 |
| I6 | sweep 范围 | 只分诊**本 change 新增项**（老项在各自 change 完成时已分诊过，不全量重诊） | ✅ 定 |
| I7 | 文件 cadence | bug 按日 / todo 按月（各自自然节奏；INDEX 统一视图无视差异） | ✅ 定 |
| I8 | per-file 状态总览表 | 保留（各文件自览，INDEX 是全局板） | ✅ 定 |
| I9 | 生效范围 | 定为 laodao-skills **toolkit 新标准**（改共享 recorder 默认路径+命名） | ✅ 定 |
| I10 | 连带改动 | 两 recorder 脚本 + review UI(engine.js/review.html) + CLAUDE.md 路径 + 一次性迁移历史文件 | ✅ 定 |
| I11 | 批次注册表 | `issues/batches.md` **单文件**；计划+完成日志合一；`PLANNED→IN_PROGRESS→DONE`；条目薄（成员生成、详细方案归真 change） | ✅ 定 |
| I12 | 债务闭环〔grill-amendment〕 | ~~主动标记逾期~~ **不做逾期催办**（判据难定、投机）；改**被动**：INDEX 摊清 open×批次 + 标 DONE，open 项下次清理自然纳入；reindex **同步批次状态**（成员全 DONE→批次 DONE、不一致标出） | ✅ 定 |
| C1 | 跨模型 outside voice 机制 | 参考 gstack plan-eng-review 的 outside-voice（default-on / 框定"找漏"/ cross-model tension / user sovereignty / 非阻塞+超时），**自包含重写、不引用 gstack** | ✅ 定 |
| C2 | spec-review 接入 | **复用 autoplan 的设计 outside voice**（always，autoplan 每次跑）+ 命中 HR-TG 单开领域专属 cross-model。〔grill-amendment〕读产出物合法（非内部依赖）；补**反静默守卫**（缺失/0 条→显式降级+回落自带 voice）；**依赖 P2b**，回退条件触发时须自跑（见 §9.2、adr/0002） | ✅ 定 |
| C3 | impl-review 接入 | **自带 code outside voice**（always，无 autoplan 重叠）+ 命中 HR-TG 单开领域专属 cross-model | ✅ 定 |
| C4 | 高风险判据 | 命中 **HR-TG 子集** = {TG-04 DB schema, TG-06 跨模块共享数据模型, TG-07 API合约, TG-08 外部依赖, TG-09 状态机, TG-16 性能/可用性 NFR, TG-17 信任边界/敏感数据, **TG-26 并发/共享可变状态（新增）**}；由 review 规划镜头步顺带判 | ✅ 定 |
| C5 | tension 适配 | spec→报告决策登记(设计门人裁) / impl→有把握自动裁决·拿不准 defer；两者守 user sovereignty（不静默自动改） | ✅ 定 |
| C6 | fallback | codex preflight → ready/not_installed/not_authed/disabled；非 ready/报错/超时 → 原生 Task 子代理 outside voice（保独立性、丢跨模型）；全程非阻塞 5min 封顶 | ✅ 定 |
| C7 | gstack 边界 | autoplan / gstack review 的 outside voice **保 gstack 原生**（不动）；自制机制**只驱动**自制 skill；spec-review"复用"= 读 `gstack-review.md` findings，不重实现 | ✅ 定 |
| G6 | 改在权威源 | 权威源 = laodao-skills（bundle assets + 自制 skill 目录）；消费仓 `openspec/workflow`·`tools`·`hack` 是副本，走 `opsx-project-init update` 采纳；**禁止只改副本**。→ 本 change 归属 laodao-skills 仓 | ✅ 定 |
| B1 | review UI 归位 | 〔grill-amendment〕**半归位**：仅工具机械 `tools/` 归 `openspec/workflow/tools/`（随 copy_bundle）；serve.sh + 根 review.html **留 `openspec/` 根**（服务器根锚——工具靠服务器根=openspec/ 才覆盖得到 changes/specs，engine.js scope 靠 /review.html）。资产路径 /tools/→/workflow/tools/ + 两 producer 改模板路径。原文"整组随行"因服务器根约束不可行，见原则6 | ✅ 定 |
| I13 | issues 标准归属 | §8 即规范定义；唯一真相源 = 两 recorder skill 的"约定速查"段（写进去），不另起 rules 文件 | ✅ 定 |

---

## 七、阶段三：实现 + 代码评审 + 收尾（过设计门后，连续自动跑到 merge）

### 7.1 骨架

```
  writing-plans → subagent-dev(实现 + task审 + 终审[通用 rubric + 注入点B:附 domains])
        │ [checkpoint]        ← 领域问题在此循环内命中即 fix子代理+re-review 即时闭环
        ▼
  impl-review 编排器(每次全跑·独立冷视角·强制，fresh 子代理替代 /clear):
     gstack/review(scope-drift+完成度) + 领域镜 + 对抗镜 + 历史镜 + 置信过滤
     · 能修的自动修 [impl-review-fix]/[staff-review-fix]
     · 修不了的/需拍板的 → buglist/todolist(defer) + 汇总 code-review-report.md
        │ [checkpoint]        ← 无人类门(P3e)
        ▼
  opsx-done: verify(最终门) → 生成 hand-off.md → archive(含 hand-off) → commit → merge
        │
        ▼
  hand-off.md ── 异步 ──▶ 人类读 → 决定开"清理 change" → 作为下个 change 输入
```

全流程只在**阶段二的设计门**停一次人类；此后实现→评审→修→verify→merge **一口气自动跑到合并**。

### 7.2 领域审"审两遍"为何不是重复（注入点B + impl-review 并存的核心理由）

这是阶段三最反直觉、也最该防止后人"优化掉"的一条。两遍领域审**机制不同、职责不同**：

```
  第一遍: subagent-dev 终审 + 注入点B          第二遍: 事后 impl-review
  ───────────────────────────────────────────────────────────────────
  时机   生成循环内                            全部实现完成后
  机制   命中即派 fix 子代理修 + re-review 闭环  出报告 → 编排器修(无 re-review 紧闭环)
  独立性 reviewer 冷,controller 热(在循环内)     完全冷独立(脱 controller)
  职责   即时修复确认(shift-left,便宜早修)      独立兜底网(实测能抓真问题)
```

- **注入点B 的不可替代性 = subagent-dev 的即时修复确认机制**：reviewer 一发现领域问题，**当场派 fix 子代理修 + re-review 到 Approved**，这套循环内闭环是事后审没有的。撤了它，领域问题只能拖到事后审、失去即时闭环。
- **impl-review 的不可替代性 = 独立冷视角 + 实测捕获**：历史经验证明它能抓出循环内被 controller 说服放过的真问题。是**强制主审、非高风险才跑的边际残差**。

> ⚠️ **对 `reference/quality-layering.md` §五的影响**：§五原结论"事后 impl-review 高风险才跑、缩成薄残差"**被本决策否决**。impl-review 升级为"每次全跑的独立强制主审"。落地时须改写 §五（保留注入点B 的 shift-left 论述，但删掉"impl-review 缩成残差"的推论）。

### 7.3 无人类门的含义（P3e，须知情）

去掉旧 step 14 后，**阶段三无任何阻塞人类门**：

- **能修的当场修**（自动修复循环，标 `[impl-review-fix]`），**不进延后池**。
- **修不了的 / 需拍板拿不准的** → 进 buglist/todolist(defer) —— **本 change 不处理**，由 hand-off.md 引导**另开清理 change**处理。
- **≥2 方案决策**：阶段三无人类门，故编排器对有把握的**自动选推荐项**（记理由），genuinely 拿不准的**延后**（非当场问人）。与阶段二"记录待人拍板"不同 —— 阶段二决策高杠杆(错设计→白做)值一个门；阶段三已实现、残差可追踪可另修，自动决策+延后可接受。
- **人类再入口 = hand-off.md**（异步，非阻塞）：事后读归档里的 hand-off 决定要不要开清理 change。

#### 7.3.1 防假✅：去人类门的前置条件〔grill-amendment〕

> **背景（真实事故）**：zhws `2026-07-todolist.md` T45/T46 记录过一次 **假✅**——`spec-review-verify.md` 把两条**根本没落实**的需求（V-20 性能基线 benchmark、V-43 估时重算）标成 ✅，靠事后人肉订正才揪出。阶段三一旦去人类门（P3e），verify（P3f）成**唯一终门**；若 verify 再吐假✅，不完整的活会**静默 merge**，且 hand-off 会把假✅当"已完成"写进异步再入口，错误固化两层。故"去人类门"**不是无条件**的——必须先给 verify 焊死防伪绿约束：
>
> - **(a) 证据锚点硬约束**：verify 报告里每条 Requirement 的 ✅ **必附一个可机验锚点**（测试名 / commit hash / 文件行号）；**无锚点的 ✅ 一律降级为 gap**。T45/T46 正是"标✅但无 benchmark 实现"——有此约束当场变红。
> - **(b) verify 禁弱模型**：verify 子代理用**强模型 + "Do Not Trust the Report" 冷启**（对齐 quality-layering 的 task-reviewer 范式）。呼应铁律"带门禁/无人逐条复核的步别用弱模型——假绿会放不完整的活过关"。
> - **(c) hand-off 不继承 verify 的 ✅**：hand-off 的"已完成"清单里，凡引 verify ✅ 的项**须独立复核**（至少复核锚点存在性），不得直接搬运 verify 结论。
>
> 一句话：**门不是靠人盯，是靠 verify 的假✅被机验锚点堵死。** 见 `adr/0001-phase3-no-gate-verify-anchors.md`。

### 7.4 产物集（三份不同 altitude，各有职责；删一份）

```
  产物                    谁产             职责                          存废
  ────────────────────────────────────────────────────────────────────────
  code-review-report.md   impl-review 编排器 详细 findings 审计(逐条+置信+裁决) 留(审计)
  verify-report.md        opsx-done verify   逐需求 done/gap 门禁记录        留(归档)
  hand-off.md 【新】       opsx-done          高层 done/not-done + 下阶段建议  留(异步再入口/下个change种子)
  code-review-verify.md   —                  原 step14 人类清单,门没了即无用   删
```

**hand-off.md 内容**：① ✅ 本 change 完成了什么（引 verify-report 的 done）② ⏳ 未完成/延后了什么（本次新增 buglist/todolist + 被延后的 ≥2 方案决策）③ ▶ 下一阶段建议（建议开哪个清理 change / 优先级）。**产出时机**：opsx-done 内 **verify 判定完之后**（verify 才权威定完整性）、**archive 之前**（随归档留档）。opsx-done 是自制 skill，加此步无碍。

### 7.5 内部提交点

- subagent-dev：逐任务提交（现状已有）。
- impl-review 编排器：产出 code-review-report + 自动修复后 → checkpoint 提交。
- opsx-done：commit 步统一提交归档 + spec 同步 + hand-off + INDEX（已兼容"实现期逐 commit"）。

---

## 八、阶段三配套：债务池与批次管理（`issues/`）

> **定位**：阶段三把"修不了的进 buglist/todolist → hand-off 引导另开 change 清理"，本节把这条**债务池的管理模式**系统化。核心洞见：现状用户已在**手动**做这件事（见 `2026-07-todolist.md` 头部的"债务分诊"把 OPEN 项归组 5A/5B/5D 待起 change），本节把手动仪式**系统化**并修掉它暴露的 smell。

### 8.0 标准归属（issues 变更的规范定义在哪）

本节 §8.1–§8.7 **就是 issues 管理的规范标准定义**（结构 / 三维度 schema / 状态词表 / 批次注册表格式 + 生命周期 / INDEX 生成规则 / sweep 协议 / 命令面）。落地时这套标准的**唯一真相源 = 两个 recorder skill 的"约定速查"段**（`buglist-recorder` / `todolist-recorder`，二者本就自包含各自约定），本 change MUST 把下述标准**写进这两个 skill 的约定段**（新增 issues 结构 / 批次 / sweep / INDEX / batches 规则）。不另起 rules 文件（避免与 skill 自含约定形成第二源）。

### 8.1 现状 smell（手动分诊暴露的）

- 状态列被塞进批次组（"归属5A(vpd)"）→ 污染干净的生命周期状态。
- `关联Change` 一格塞两件事（"phase-5·5A（源 phase-4）"）→ **源**(哪发现) 与 **target**(哪修) 混一格。
- 根因：缺一个独立的"批次"维度。

### 8.2 统一结构

```
openspec/issues/                    ← buglists/ + todolists/ 下沉合并(near 原地重命名)
├── INDEX.md          【生成·禁手改】全池 open item × 批次状态 的物化板;reindex 重建
├── batches.md        【半手维护】批次注册表:计划+完成日志合一
├── buglist/
│   ├── 2026-07-02-bug.md    按日,表+块+批次列(provenance 流水账)
│   └── ...
└── todolist/
    ├── 2026-07-todo.md      按月
    └── ...
```

### 8.3 三维度分家（I3）

```
  字段        含义                      何时写    可变?
  ────────────────────────────────────────────────────
  源change    哪个 change 发现的         记录时    不可变(provenance)
  批次        归入哪个清理 change        分诊时    可变(triage 结果)
  status      OPEN→PROPOSED→DONE         生命周期  追加式,回归干净(不再塞批次)
```

item 生命周期：`OPEN,批次∅`（发现即记）→ sweep 分诊 →`PROPOSED,批次=clear-vpd`→ cleanup change 清 →`DONE/FIXED,证据=commit`。

### 8.4 批次注册表 batches.md（I11）—— 批次的第一类身份

item 池只跟踪**条目**生命周期，不跟踪**批次**生命周期；批次从"命名"到"真开 change 清"有时间差，易悬空遗忘。故给批次第一类身份，每批一条薄记录（状态流转即完成日志）：

```
### clear-vpd — vpd 数据完整性(5A)
  状态:   PLANNED → IN_PROGRESS(change=X) → DONE(change=X, 日期) — N项清完   ← DONE 行即完成日志
  优先级: P1
  成员:   (生成) T39, T43, B17        ← reindex 从 item 批次 tag 填,不手写
  计划:   一句范围(型号级 advisory 锁 + 导出补 vpd.enabled)
```

> ⚠️ 注册表条目要**薄**：名/状态/成员(生成)/优先级/一句范围/完成记录。**详细方案属于真开的 cleanup change 的 proposal/design**，别在注册表预写第二套真相源。批次本质="一个还没出生的 change"。batches.md 跨 bug+todo，坐 `issues/` 根、两子目录之上。

### 8.5 债务闭环（I12）—— 被动可见 + reindex 同步状态〔grill-amendment〕

> **〔grill-amendment〕不做"逾期主动催办"**：早前 I12 想让 INDEX"主动标记逾期 PLANNED 批次"，但"逾期"判据难定、且属投机机器。改**被动**：INDEX 只把 open 项 × 批次**摊清楚、把 DONE 标出来**，剩下的 open 项在**下次清 bug/todo 时自然纳入考虑**，不设逾期计算、不主动喊。

```
  sweep(opsx-done/hand-off 内)  分诊本 change 新增 OPEN 项 → 新批次写 batches.md(PLANNED) + hand-off 引用
       │
       ▼
  INDEX reindex(join item池 + batches.md):
     摊清 open 项 × 所属批次 · 标出已 DONE · 顺带【同步批次状态】(见下)     ← 被动板,不催
       │
       ▼
  开 cleanup change → 批次 IN_PROGRESS → 清 item(set-status DONE) → reindex 同步批次 DONE + 留日志
```

- **reindex 同步批次状态（焊洞一：batches.md 状态不再自由漂移）**：reindex 填成员时，**拿 item 池当 ground truth 校验/同步批次 `状态`**——成员全部 DONE/FIXED → 批次判/标 DONE；仍有成员 OPEN/PROPOSED 却手标了 DONE → reindex **标不一致纠正**（不静默信自由手写的状态字段）。`PLANNED→IN_PROGRESS` 仍由人起 cleanup change 时设。
- item 清完从 INDEX 消失，但批次条目留 batches.md 作历史 → "债务确实在还"有据可查。
- 全链：hand-off(每 change 提议) → batches.md(登记 PLANNED) → INDEX(被动摊清 + reindex 同步状态) → cleanup change(清) → batches.md(reindex 同步 DONE 日志)。

### 8.6 脚本/工具增强（laodao-skills toolkit 级，I9/I10）

- 两 recorder：路径默认 `openspec/issues/{buglist,todolist}/`；表加 `批次` 列（旧文件无列时兼容留空）；scan 加维度 `--源/--批次/--open-ungrouped`；加 `triage` 命令（给 OPEN 项赋批次+转 PROPOSED）。
- 新增 `reindex`（重建 INDEX.md，join item+batches；**顺带同步批次状态**：成员全 DONE→批次 DONE、状态与成员不一致则标出纠正，见 §8.5〔grill-amendment〕）、`batch`（批次 add/set-status）命令，跨 bug+todo。
- 连带：review UI 读 issues 新路径（bundle 改，见 7.3/B1）；各消费仓迁移自己的 buglist/todolist 数据 + `CLAUDE.md` 引用属**下游**（§9，非本 change 内）。

### 8.7 与设计原则一致

- **change review 期发现的问题默认不进池**（两 recorder 已有此约定）→ 与阶段三"可修的循环内修掉、修不了的才进池 defer"同构。
- sweep 只诊本 change 新增（I6）、INDEX 只生成（I2）、批次成员生成（I11）→ 延续"脚本兜底一致性、单一真相源、不制造漂移"。

---

## 九、配套：跨模型 outside voice（spec-review / impl-review）

> **定位**：把"独立视角"推到最强版本——**换模型家族**（Claude ↔ GPT via codex）。同模型 fresh-context 只换上下文、盲区同处；跨家族盲区结构性错开，非重叠捕获最大。**参考 gstack plan-eng-review 的 outside-voice 机制，但自包含重写、不引用 gstack**（C1）。

### 9.0 gstack 边界（关键，别越界）

**两套机制井水不犯河水**：

```
  gstack 的 skill(autoplan / gstack /review)  → outside voice 保持 gstack 原生机制,不动、不改、不接管
  我们的自制 skill(spec-review / impl-review)  → outside voice 走【我们自包含重写】的机制
```

- spec-review 的"**复用** autoplan outside voice"（C2）= **读 autoplan 已产出的 `gstack-review.md` 里的 outside-voice findings**（那是 gstack 原生机制产的），**不重实现、不调 gstack 内部**。
- 我们自包含重写的机制**只驱动**：spec-review 高风险的领域 cross-model + impl-review 的 code outside voice（+ 其高风险领域 cross-model）。
- 即：**autoplan/gstack review 保原生；自制 skill 走自制机制**——各自维护，零耦合。

> **〔grill-amendment〕边界再校准（区分"复用产出物" vs "依赖内部"）**：
> - **gstack 自家 skill（autoplan / gstack review）的能力原样不动、照常使用**——包括**读它们的产出物**（如 `gstack-review.md`）。"复用 gstack 产出物（output artifact）"**合法**，它不是内部依赖。
> - "**不引用 / 不依赖 gstack·superpowers 内部工具**"这条铁律**只约束我们自制的 skill**（spec-review 自跑的 cross-model、impl-review 的 code outside voice、codex 共享 helper）：这些**不得**调用 gstack 内部 bin / 探针 / config，须**自包含重写**（C1）。
> - 一句话：**读产出物 ✓，依赖内部实现 ✗**。C2 的"复用"落在前者，合规。

### 9.1 机制要点（自 gstack 提炼）

```
  1. default-on,非 opt-in       两模型都同意 > 一模型审得细;显式 off-switch 才关
  2. preflight 探测             ready | not_installed | not_authed | disabled
  3. 框定"找漏"非"重审"          prompt:"你的活不是重复这遍 review,是找它【漏了】什么"
  4. 文件系统边界指令            "别读 ~/.claude 等 skill 定义,只看仓库代码"
  5. fallback 到 Claude 子代理   非 ready/报错/超时 → 同 prompt 派 fresh Claude 子代理,5min 封顶
  6. cross-model tension        codex 与主审分歧处中立并陈,标 TENSION
  7. user sovereignty           绝不静默自动采纳 outside voice 的建议
  8. 全程非阻塞                  所有失败 informational,不挡流程
```

> ⚠️ **修正**：早前"codex 占对抗镜一个 slot"的想法**作废**。outside voice 不是"codex 跑某张清单当一个镜"，而是**不受清单约束的整体"找漏"第二意见**——模型多样性在不约束时收益最大。

### 9.2 两处接入（点不同：设计侧已有、代码侧没有）

```
  spec-review(设计):  autoplan 每次跑 → 其自带 outside voice 已对【设计】做过 codex 第二意见
                      ∴ 【复用】autoplan 的 outside-voice findings(在 gstack-review.md),不重开(避免双 codex)(C2)
                      + 命中 HR-TG → 【单开】领域专属 cross-model(codex,聚焦命中的高风险域,"找领域镜漏的")
  impl-review(代码):  无 autoplan、无前置 outside voice → 【自带】一个 code outside voice(always,零重叠)(C3)
                      + 命中 HR-TG → 【单开】领域专属 cross-model
```

> **〔grill-amendment〕复用的两道焊缝（防静默失效）**：
> - **(1) 反静默守卫**：spec-review 读 `gstack-review.md` 时，若**文件缺失 / 解析不出 codex 段 / codex findings 为 0** → **打印显式降级日志**（"autoplan outside voice 未找到/为空 → 降级"）并**回落 spec-review 自带的 codex 设计 outside voice**（自制 helper 本为 HR-TG 而存在，顺手复用），**绝不静默当"本次无 voice"跑过**。理由：gstack 产出格式（文件名 / `codex#N` 标签约定 / 表结构）可能漂移，捞到 0 条 ≠ 本次真的没 outside voice，静默丢一整层评审覆盖是"假绿"同构。
> - **(2) C2 依赖 P2b，须显式登记**：C2"复用"成立**仅当 autoplan 每次都跑（P2b）→ gstack-review.md 每次都在**。若 OQ2 日后把 P2b 回退成条件触发，**autoplan 未跑的变更 spec-review MUST 自跑设计 outside voice**（走守卫(1) 的 fallback 路径），不得因"复用了一个没产生的东西"而漏掉整层。落地时 C2 与 P2b 两条 MUST 交叉引用。

### 9.3 高风险判据 = 命中 HR-TG 子集（C4）

**不新造风险分级**（trigger-catalog 明令"具体行为、不用风险代号"）——从 TG 里挑"做错会运行期爆炸/数据损坏/安全泄漏且难回退"的具名子集：

| HR-TG | 具体行为 |
|-------|---------|
| TG-04 | DB schema 迁移（增删改列/索引/约束/类型） |
| TG-06 | 跨模块/跨产品共享数据模型边界 |
| TG-07 | API 合约变更（endpoint/请求/响应/method/status） |
| TG-08 | 引入/改外部依赖（DB/缓存/第三方/跨服务） |
| TG-09 | 多状态生命周期 / 状态机 |
| TG-16 | 性能 / 可用性 NFR |
| TG-17 | 信任边界 / 敏感数据 |
| **TG-26** | **并发 / 共享可变状态（新增，需加进 trigger-catalog）** |

- **判定由 review 的"规划镜头"步顺带做**（它本就在判命中 TG 选领域镜）：命中集 ∩ HR-TG ≠ ∅ → 跑领域 cross-model。零新机制。
- 报告留痕：记"判定命中 TG-xx → 已跑领域 cross-model"，可审计。

### 9.4 tension 适配 G2 / P3e（C5）

gstack 是中途 AskUserQuestion；我们不这么做：

```
  spec-review: tension → 写进 report 决策登记区(选项+推荐+两方视角) → 设计 HARD-GATE 人一次性拍板 (守 G2)
  impl-review: tension → 有把握自动裁决(记理由) / 拿不准 defer 进 buglist·todolist+hand-off      (守 P3e)
  两者共守 user sovereignty 实质:outside voice 建议【绝不静默自动改代码/设计】,进报告或 defer,可审计
```

### 9.5 自包含重写（不引用 gstack，同 I9/recorder 哲学）（C1/C6）

重写进 **laodao-skills 共享 helper**，两 review skill 都调，**只依赖 codex CLI 本身**：

```
  要重写的(小)                          说明
  ──────────────────────────────────────────────────────────
  codex preflight 探针                  command -v codex + 试跑(超时) + catch-all → mode
  codex exec 包装(prompt→findings)      5min 超时,捕获 stdout/stderr
  prompt 模板("找漏"+文件系统边界指令)   ~1KB 文本,拷改
  off-switch                           自建(env `LAODAO_CODEX_VOICE=off` 或 config.yaml 一行),非 gstack-config
  fallback = 原生 Task 子代理           不用拷(Claude 原生)
```

- **保持最小**：fallback 兜底一切失败（auth 挂也回落 Claude 子代理），探针 ~15 行足够。
- **代价**：codex CLI 改接口 → 更新我们这份拷贝，不再自动继承 gstack 修复。低频可控。
- **最坏情况**（无 codex、无 gstack）：outside voice 退化成 fresh-context Claude 子代理——独立性还在，只丢跨模型。审查永不因此中断。

---

## 十、待议 / 落地清单

> **〔grill-amendment〕落地按 ROADMAP 拆 3 相串行（OQ1 定案）**：本设计不一次性落地，拆成 **Phase A 流水线骨架**（块1 连续化 + 块2 提交 + 块7 bundle 骨架）→ **Phase B issues 池**（块5 + sweep）/ **Phase C 跨模型 voice**（块6 + TG-26）。B/C 依赖 A 造出的 opsx-done/编排器地基，A merge 后各开新 change dir。**本 design.md 是三相共享真相源**（G/P/I/C/B 全量决策 + adr/0001·0002 + CONTEXT.md 术语，三相反向引用不复制）。下述"落地时"三组正对应三相；拆法、相划分、依赖序、`workflow.md` 增量改 3 次等 3 条必守约束见 [ROADMAP.md](./ROADMAP.md)。

- **阶段三落地时**：改写 `reference/quality-layering.md` §五（见 7.2）；`impl-review` skill 描述从"高风险才跑·冷独立抽查"改为"每次全跑·独立强制主审"；`opsx-done` skill 加 hand-off.md 产出步 + sweep 步。
- **issues 管理落地时**：迁移 `buglists/todolists/` → `issues/{buglist,todolist}/`；两 recorder 脚本增强（批次列/scan 维度/triage/reindex/batch 命令）；新增 `INDEX.md`(生成) + `batches.md`；改 review UI + CLAUDE.md 路径。属 laodao-skills toolkit 级变更。
- **跨模型 outside voice 落地时**：新增 `TG-26 并发/共享可变状态` 进 `trigger-catalog.md`（并回填四列 + 各消费方引用）；laodao-skills 加 codex outside-voice 共享 helper（探针/exec/prompt 模板/off-switch，自包含重写）；spec-review/impl-review 规划镜头步加 HR-TG 判定 + cross-model dispatch + tension 登记。
- 三阶段 + 提交自动化 + issues 管理 + 跨模型 outside voice **全部定稿**，下一步可据本 design 起正式变更（proposal + specs + tasks）落地 workflow.md 改写与配套 skill/脚本修订。
