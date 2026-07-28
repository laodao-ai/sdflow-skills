# 实现管线替换调研：matt to-tickets/implement vs superpowers writing-plans/subagent-dev

> 2026-07-10 探索会结论沉淀。议题：能否用 matt 套件的 to-spec → to-tickets → implement → code-review
> 替换 sdflow 阶段三的 writing-plans → subagent-driven-development？
> **目标锚定：质量已被现管线保住，痛点是慢 + token 贵——分析框架 = 换了省在哪、质量护栏丢不丢。**
> 姊妹篇：[matt-pocock-workflow.md](matt-pocock-workflow.md)（套件全景）、
> [setup-matt-pocock-skills.md](setup-matt-pocock-skills.md)（位置契约铺设器深潜）。

## 1. 结论先行

**可换，但不是整链替换，而是「matt 的分解语义 × 自研轻编排」的混血。**
估计实现段 token 可砍 40-60%（结构性，见 §6 杠杆表），墙钟后续还能靠 frontier 并行再砍。
关键兼容性发现：**ship_gate 门禁可零改动（或仅 2 处 emit 提示串）兼容**（§5）。

## 2. 成本痛点的本仓实证

retro 报告（30 个 change，总评审墙钟 70.1 hr，openspec/retro/report.md 聚合①）：

| 阶段 | 墙钟(min) | 占比 |
|---|---|---|
| spec-review | 1620.6 | 39% |
| **impl（writing-plans + subagent-dev）** | **1306.6** | **31%** |
| ff / grill / code-review / done / 其他 | 合计 | 30% |

阶段三过设计门后无人类门、连续跑到 merge——impl 的 31% 几乎是纯 agent 时间
（不像 spec-review 混着人读与拍板），是全流程第二大成本块、第一大可自动化优化块。

## 3. superpowers 贵在哪：不信任税

writing-plans 开篇假设：*"assume the engineer has zero context and questionable taste"*。
全部成本结构由这一句派生：

1. **代码写两遍**——No Placeholders 规则要求计划里每步给完整代码块：主 session（最强模型）
   计划期写一遍，implementer 执行期誊抄一遍。
2. **步长 2-5 分钟 bite-sized** → 一个 change 切 8-15 个 task → 每 task 一轮
   implementer 派发 + review-package + task reviewer + fix loop，派发循环 ≥ 2N。
3. **重型交接机制**（Interfaces Consumes/Produces 块、task-brief 抽取、progress ledger）——
   全是为「task 不自含」打的补丁。

superpowers 自己文档里记录的真实翻车账单：「一次 dispatch 42k 字符，99% 是粘贴的历史」、
「一次 final-review 修复波比全部任务加起来还贵」（subagent-driven-development/SKILL.md）。
本仓旁证：scoped-test-per-task 评审亲验原生 implementer-prompt 前提已错。

**这套成本模型是为弱执行模型校准的保险；2026 年模型强度下保费过高。**

## 4. matt 管线对照：反向的信任模型

| 维度 | superpowers | matt 套件 |
|---|---|---|
| 计划产物 | 全量代码 + 精确路径 + 精确命令 | 行为级 ticket，**明令禁止**文件路径与代码片段（防过期） |
| 切分哲学 | 2-5 分钟横向小步 | tracer-bullet 垂直切片：一票打穿全层、可独立演示、sized to 一个上下文窗口 |
| 单元数量 | 8-15 task | 约 3-6 票 |
| 依赖表达 | 隐式顺序 + Interfaces 块 | 显式 Blocked-by 阻塞边（DAG），frontier = 阻塞已清的票 |
| 评审 | 每 task spec+quality 审 + fix loop + 终审 | 每票双轴审（Standards/Spec 并行子代理，各 <400 词封顶） |
| 宽重构 | 无专门处理 | expand–contract 序列（唯一的垂直切片例外） |
| 执行者假设 | 零上下文誊抄工 | 会自己探索代码库的合格 agent（TDD at pre-agreed seams） |

### 直接整链替换会断三根柱子

1. **自动化断**：matt 原生节奏是人肉的——to-tickets 第 4 步 quiz the user、
   implement 靠人「逐票跑、票间 /clear」；阶段三要求过设计门后无人类门连续到 merge。
2. **ship_gate 主锚断**：门禁读 `superpowers-plan.md` + `### Task <n>:` 标题 +
   `checkpoint(<change>:task<N>-)` 标签；matt implement 只说 "Commit your work" → gate 0/N 永卡。
3. **注入点 B 断**：code-checklists/domains 领域镜附 reviewer 的即时闭环，matt code-review 没有——
   但其 Standards 轴本读「仓内文档化标准」，天然是注入口，需显式接线。

另：**to-spec 整段冗余**——proposal/specs/design 四件套是其 spec 模板的严格超集，
入口直接 design.md → 出票。

## 5. ship_gate 兼容性发现（本调研最重要的机械层结论）

`sdflow-ship/scripts/ship_gate.py` 逐行核验：

- 完成判据契约只有三样：**文件名 `superpowers-plan.md`（:722）、`### Task <n>:` 标题集
  （plan_task_ids，fence-aware）、checkpoint 标签窗口 ∪ 复选框辅通道**。
- 任务体内容完全不设限——bite-sized 带码步骤或行为级票文，gate 不关心。
- superpowers 专名仅出现在 2 处 emit 的**提示串**（:724 `"writing-plans"`、:750 `"subagent-dev"`），
  状态机（RUN_PLAN / CONTINUE_IMPL / done_tasks resume）本身管线无关。

**推论**：tickets 文件写进 change 目录、沿用（或经小改配置化）该文件名，标题用
`### Task N: <票名>`、票体用 matt 模板（What to build / Blocked by / 验收复选框），
门禁零改动兼容；CONTINUE_IMPL 的 done_tasks resume 语义原样可用。

sdflow-ship 是 gate 驱动的 meta-orchestrator（chain 现有 skill、不取代），替换点恰好是
链序里 RUN_PLAN→writing-plans、CONTINUE_IMPL→subagent-dev 两个映射——**换管线 ≈ 换这两个
映射指向的 skill**，ship 主体与其余链（sop / code-review / done）不动。

## 6. 混血架构草图与省钱杠杆

```
设计门(不变) ─▶ 「to-tickets 语义」出票        ─▶ 自研控制器(参考 subagent-dev 力学)
                · 垂直切片 + Blocked-by DAG        · 工作 frontier
                · 行为级描述,无预写代码             · fresh implementer 子代理/票
                · 文件穿 superpowers-plan.md       · implementer 契约: TDD(matt implement 语义)
                  外衣: `### Task N:` 标题            + checkpoint(<change>:taskN-<slug>)
                · Global Constraints 节保留        · 每票 matt 双轴审(standards 轴喂
                  (design 领域约束逐字)               code-checklists/domains = 注入点B)
                       │                           · fix→re-review 环保留
                       ▼                                  │
                ship_gate 零改动兼容 ✓        冷层 sdflow-code-review(不变,承重墙) ─▶ sdflow-done
```

| 杠杆 | 机制 | 省在哪 |
|---|---|---|
| 代码不写两遍 | 行为级票替代带码 plan | 计划期 token 降一个量级 |
| 单元变粗 | 垂直切片 3-6 票 vs 8-15 task | 派发循环近乎减半 |
| 评审输出有界 | 双轴各 <400 词 | reviewer 输出封顶 |
| model 分层 | 自研编排的自由度：机械票低档、判断票高档（model-tiers.md 已有基建） | 单价降 |
| frontier 并行（后期） | 阻塞边 DAG + 垂直切片自含 + worktree 隔离 | 墙钟直接砍；superpowers 明令禁止并行 implementer，是它做不到的 |

⚠️ 并行的前置障碍：checkpoint-commit.sh 的 `add -A` 在共享工作树下会互扫兄弟票改动，
并行必须 worktree + 每票分支 + 合回，机械量不小——**首版建议串行**（token 杠杆已足），并行另立阶段。

## 7. 质量护栏为什么不丢

- **承重墙不动**：冷层 sdflow-code-review 保留（memory 实证 cold-code-review-load-bearing：
  sdflow-retro 致命 F1 由冷主审独家挖出，此层不可优化掉）。
- 实现照**已过 grill + 多镜 spec-review 的 design.md** 跑；TDD 保留（matt implement 走 /tdd，已装）；
  每票双轴审 + 修复环保留。
- 真正丢掉的是「计划期预写代码再被审」层——该层本与 spec-review 职能重叠，且制造
  plan-mandated findings 冲突（superpowers 需专段处理「计划强制写法被 reviewer 判缺陷听谁的」）。
- 代价：单票 diff 变大 → per-ticket 审漏检率可能升；兜底 = 冷层。建议拿真实 change A/B 验证
  （retro 的 impl Δ / findings 通道现成可量）。

## 8. 需被新管线重新吸收的 writing-plans 职能

| 职能 | 去向 |
|---|---|
| Global Constraints 逐字携带 | tickets 文件头保留同名节（reviewer 注意力透镜，便宜且承重） |
| Self-review spec 覆盖检查 | 票携 R-ID 标注（本仓 tasks.md 已有此惯例）→ 覆盖检查近机械 |
| Interfaces (Consumes/Produces) | 垂直切片自含 + 阻塞边天然弱化跨票接口；共享 util 场景票内一句接口约定 |
| 状态词表 DONE/BLOCKED/NEEDS_CONTEXT | 保留（subagent-dev 中值得留的部分） |
| progress ledger | 不需要——盘面即状态：tickets 文件复选框 + checkpoint 标签 + gate resume |
| model selection 节 | 移交 model-tiers.md（规则根已有） |

## 9. 开放线程

1. **粒度对门禁的语义漂移**：gate 的 N 从 ~12 变 ~4，完成判据变粗；票内验收复选框（辅通道）可补细粒度。
   → §10 部分吸收：复选框升格承重，implementer 契约须钉死「勾框=完成宣告，与 checkpoint 标签双写」。
2. **quiz-the-user 挪去哪**：并进设计门一次拍板 vs 信任自动出票。→ 仍开放（倾向前者，设计门侧拍板）。
3. **行为级票 × 弱模型组合边界**：无代码可抄时低档模型够不够——model 分层判据按票性质重标。
   → §10：Phase A 钉死 mid 档（一次只变一个变量），边界实验后置。
4. **tasks.md 与 tickets 的关系**：现状双重分解（tasks.md → plan）；新流仍双重（tasks.md → tickets），
   可否让 tasks.md 授权指引向垂直切片靠拢、使出票近机械。→ 仍开放（Phase B 议题）。
5. **落点**：天然属于 `workflow-cost-optimization` roadmap；skill 形态（新编排 skill +
   ship 接入方式）→ **已定，见 §10**。

## 10. 设计讨论结论（2026-07-10，三镜独立设计 + 对抗镜互证 workflow，用户拍板）

> 方法：系统镜/用户镜/开发循环镜三代理独立答六问（skill 拆分/ship 接入/gate 处理/机制取舍/
> 分期/命名），对抗镜逐案证伪并抽查引用行号（4 处引用失实被点名订正）。以下为收敛裁决。

### 10.1 六问裁决

| 问题 | 裁决 | 关键依据 |
|---|---|---|
| Q1 skill 形态 | **单 skill `sdflow-implement` 双模式**（用户拍板）：出票模式（to-tickets 语义，删 quiz-the-user）**落盘即返回**；ship 重跑 gate → CONTINUE_IMPL 携 done_tasks 再入执行模式 | 「落盘即返回」保住 gate 在出票后/执行前的三道校验插入点（fence/零标题/重号，ship_gate.py:727-739）——两 skill 与单 skill 的 gate 力学等价（对抗镜裁定「必须两 skill」系假二分），由维护面账收敛：description/README/setup 链接全部减半。⚠️ 同调用直通执行的变体被否决（丢 gate 插入点，违 adr/0006(b)） |
| Q2 ship 接入 | **不 fork sdflow-ship2**（三镜全票）：原地改 SKILL.md 链序 RUN_PLAN/CONTINUE_IMPL 两个映射。A/B 路由 = config.yaml 键 `impl-pipeline`（沿 model-tiers 覆盖段先例，**缺省 = superpowers**）定首跳 + 出票时写 plan 文件头 frontmatter marker 定在途归属 | gate 状态机管线无关、专名仅 :724/:750 两处 emit 提示串；fork = 842 行加固沉淀双写必漂移，adr/0007 否决 stub 的「长期维护额外面」理由逐字适用 |
| Q3 gate 处理 | 试验期 tickets 穿 `superpowers-plan.md` 外衣（gate 零改动）；**永久否决**文件名配置化（窗口锚按路径 keyed :740、零依赖不变量 :286、双源歧义）；emit 串毕业后单独小改中性词，试验期 ship 链序显式声明「此二态映射以 SKILL.md 为权威、next 仅提示」压弱模型误路由 | 完成判据契约 = 文件名 + `### Task <n>:` 标题集 + checkpoint∪复选框双通道，票体内容不设限（§5 亲验）。终局文件名迁移（改 tickets.md+旧名 fallback+双存判 UNKNOWN vs 永不改）留 Phase B 拍板——**Phase B 已在 `harden-implement-review-loop` 拍板落地（`adr/0033`）：tickets 轨改名 `tickets.md`，superpowers 轨保留 `superpowers-plan.md`，gate/route 经共享 resolver 探两名，双存在 fail-closed UNKNOWN**，与此处列出的候选之一逐字一致 |
| Q4 机制取舍 | **砍**：warm final whole-branch review（冷层紧随且承重，SDD 自记修复波成本灾难）、progress ledger（gate done_tasks resume 结构性覆盖，留则双真相源）、pre-flight 批量问人（→T10）、task-brief 抽取（票文即 brief；超阈值折中可留）。**保**：状态词表 DONE/BLOCKED/NEEDS_CONTEXT（NEEDS_CONTEXT 改从盘面自答）、每票双轴审+fix→re-review 环（standards 轴喂 code-checklists/domains=注入点 B）、report file+review-package 文件交接、Global Constraints 逐字携带、checkpoint 标签契约 | 取舍总原则：superpowers 用 prose/文件补丁解决而 sdflow 已有结构机制（gate 通道/T10/冷层/recorder）覆盖的一律砍；确定性信号与上下文经济学机制管线无关地保留 |
| Q5 分期 | 三期：**Phase A**（一个 change）= 串行混血 + config 键 + 零 gate 改动，试点 3-5 个有逻辑面的中型 change；**Phase B**（判赢后微 change）= 毕业清理（默认翻转/emit 串/文件名迁移/workflow.md 步表/sdflow-init 推下游）；**Phase C**（另立 workflow-cost-optimization leg）= frontier 并行 | 并行的契约级障碍：gate 完成窗口 = 当前分支 [plan_first_sha, HEAD] 闭区间，每票分支使标签合回前不可见、done_tasks 系统性少算——必须独立 spec-review。A/B 判据取三条结构（impl Δ 降 + 冷层严重项不升 + 护栏哨兵）**定性人读拍板、不设数字阈值**（n=3-5 上是假精度，adr/0009 小样本警告）；至少一个消费仓跑缺省键路径（dogfood 盲区）；试验期 implementer 档位钉死 mid |
| Q6 命名 | 编排 skill = **sdflow-implement**（否决 sdflow-impl，adr/0007(b) 判例：impl 非自然触发词）；ship 保名不动，**否决 sdflow-ship2** 及一切版本号后缀（adr/0007 反命名地层）；`disable-model-invocation` 实测 harness 语义前不写入 frontmatter（对抗镜判照搬会让 ship 调不动链条），触发精度靠 description 收窄 | |

### 10.2 对抗镜挖出的共同盲区（须进 Phase A 设计）

- **Reviewer ⚠️ Cannot-verify-from-diff items**（SDD:150-157）：跨票/未改动代码里的需求项 reviewer
  无法从 diff 验证、须 controller 亲自消解——垂直切片缩小但不消灭此类项，`sdflow-implement`
  执行模式契约必须保留此 controller 职责，否则静默缺口。
- 票内验收复选框与 gate checkbox 辅通道语义耦合：全勾即判该票 done（:743-744）——implementer
  契约钉死「勾框=完成宣告，与 checkpoint 标签双写」，防半态假完成。

### 10.3 回退设计（替代「fork ship2 留后路」的更优解）

用户最初提 ship2 的动机 = 未实践过 matt 管线，想保留 superpowers 流程可随时切回。裁决的
路由方案给出同等甚至更强的后路，且零 fork 成本：

1. **旧管线从未被触碰**：新 skill 纯增量（新增一个 SKILL.md + ship 链序一段条件映射文字），
   writing-plans/subagent-dev 插件原样在装；gate 零改动。
2. **缺省即旧管线**：config 键缺省 superpowers，新管线 opt-in——效果不好时什么都不用做，
   不翻键即回退；极端情况删 sdflow-implement 目录 + 还原 ship 链序一段文字，`git revert` 级成本。
3. **在途隔离**：盘面 marker 使两管线可同时在飞（change A 旧、change B 新），切换 config
   不影响任何在途 change 的续跑。
4. **对比更干净**：fork 会让 A/B 混入「两个编排器各自漂移」混杂因子；同一 ship 之下只换实现段，
   一次只变一个变量，retro impl Δ 对照归因干净。

**路由零自动判断（用户显式要求，2026-07-10 拍板）**：管线选择不引入任何模型自由裁量——
三跳信号全为手改/落盘的确定值：① `openspec/config.yaml` 的 `impl-pipeline` 键 = 人手编辑，
仅在**新出票时刻**被读一次；② plan 文件头 marker = 出票落盘后只读，在途 change 由它锁定，
改 config 不影响任何跑一半的 change；③ 键缺失/值不识别 → 一律 superpowers（fail 向旧管线）。
对在途 change 强制换管线属显式越权通道（人工改 marker + 自担产物一致性，git 留痕），
skill MUST NOT 主动建议。
