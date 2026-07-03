# Spec 工作流（端到端总览）

> **定位**：从需求到实现的端到端流程总览，串起 `openspec/workflow/` 的全部规则。
> 本文给**流程骨架 + 每步归属哪条规则**；各步细则见对应规则文件，不在此重复。
> **流程本性（重构后）**：三阶段**尽量连续自动运行**——`/clear` 由子代理 fresh-context 独立性替代、
> 中途 AskUserQuestion 改报告决策登记、每步产物 checkpoint 提交；全流程**只在阶段二设计门停一次人类**。

---

## 一、完整流程（三阶段连续化）

```
 阶段一·生成 ── 人类对话岛：grill ──────────────────────────────────
   〔问题模糊/方向未定〕opsx:explore       发散(条件,清晰则跳)
        │
   opsx:ff                                 生成 proposal/design/specs/tasks
     └─ FF-0: 不在 feature 分支 → git checkout -b feat/{change}
     └─ 按 config.yaml + trigger-catalog 生成(结构①+约束②已固化)
     └─ [checkpoint] 生成产物落点
        │
   grill-with-docs                         对抗压测:死磕分支+对齐术语+查代码+落 ADR/术语
     └─ 收敛后 [checkpoint]（多轮中途不提交,只收敛后一次）
        │
 阶段二·设计审 ── 连续,无 /clear ───────────────────────────────────
   sdflow-spec-review 编排器               Step1 autoplan(广审)→Step2 并行多镜(本项目标准)→Step3 一份 report
     └─ fresh 子代理替代 /clear 保独立；中途不 AskUserQuestion(决策登记进报告)
     └─ 内部 2×[checkpoint]（autoplan 子步 / sdflow-spec-review 子步）
        │
   〔HARD-GATE：用户批准设计〕            ★全流程唯一人类门——过一份 spec-review-report.md 拍板
        │
   〔嵌入式+SOP测试需求〕embedded-test-sop  条件触发(TG-02 ∧ 高风险/TG-18,见步骤表)
        │
 阶段三·实现+代码审+收尾 ── 过设计门后连续跑到 merge,无人类门 ────────
   writing-plans → subagent-driven-development   原子任务 TDD + 注入点B(code-checklists/domains 附终审)
     └─ 领域问题在生成循环内命中即 fix子代理+re-review 即时闭环
     └─ 逐任务 [checkpoint]（subagent-dev 现状已有）
        │  (无 /clear——子 agent 调度中本就禁清；评审 fan-out 的 fresh 子代理即独立性)
   sdflow-code-review 编排器               每次全跑·独立冷视角·强制主审
     └─ 并入 gstack/review(scope-drift+完成度)+领域镜+对抗镜+历史镜+置信过滤
     └─ 能修自动修[impl-review-fix]、修不了/拿不准 defer→buglist/todolist；一份 code-review-report.md
     └─ [checkpoint]
        │
   sdflow-done                             verify(防假✅,证据锚点) → hand-off.md → archive(+delta 对码核验/同步) → commit → merge
        │
   hand-off.md ── 异步 ──▶ 人类读 → 决定开"清理 change" → 作为下个 change 输入
```

> **去掉了什么（对比旧 15 步手动 runbook）**：两个 `/clear` 会话断点、旧 step 7 手动合并两份报告、
> 旧 step 11 独立 `gstack/review`（并入 sdflow-code-review）、旧 step 12 "sdflow-code-review 高风险才跑"（升级为每次全跑）、
> 旧 step 13 官方 `/code-review` 独立 step（P3d 弃用，插件能力仅内部借用）、旧 step 14 人类门（阶段三无人类门）。
>
> **sdflow-done 已含 issues sweep 子步**（§2.1，I5/I6）：verify 判完、写 hand-off 正文前，分诊**本 change**新增的
> OPEN 项入**单一批次**（key=本 change 名）→ 末尾跑 `issues.py reindex` 刷新 INDEX/批次状态 → hand-off 第 2 段引用该批次号
> （不再逐条罗列裸 ID）。脚本分工：`sdflow-buglist`/`sdflow-todolist` 的 `scan`/`triage` 分诊 + `sdflow-issues` 的
> `batch add`/`reindex` 管批次与索引。细则见 `sdflow-done` skill 的 SKILL.md §2.1（配套 skill，不在本 bundle 内，随 laodao-skills `setup.sh` 安装）。
> 〔Phase C 补〕sdflow-spec-review / sdflow-code-review 加**跨模型 outside voice** + 命中 **HR-TG** 单开领域 cross-model（C2/C3/C4）。

## 二、逐步 prompt（可直接复制）

> `{change}` = 变更短名（如 `add-pagination`）；`{change dir}` = `@openspec/changes/add-pagination`；`{topic}` = 探索主题。
> D 约束 / 触发槽 / 画图 / 领域清单已由 `openspec/config.yaml` 的 rules **自动注入** opsx:ff——ff prompt 无需再内联。
> `[checkpoint]` = 步末调 `~/.sdflow/hack/checkpoint-commit.sh <step> "<描述>"`（过场提交，非交互；区别于最终 `/commit-message`）。（缺失则先在运行 checkout 跑 setup.sh）

| 阶段 | 步 | command/skill | prompt（可复制） | 产出物 | 规则·条件 |
|---|---|---|---|---|---|
| 一 | 1 | /opsx:explore | `/opsx:explore {topic}` | — | generation-process ③发散；**问题模糊才跑** |
| 一 | 2 | /opsx:ff | `/opsx:ff {change}。若不在 feature 分支则先 git checkout -b feat/{change}。完成后 checkpoint-commit ff。` | proposal/design/specs/tasks | ff-generation-constraints(FF-0)+config；**必跑** |
| 一 | 3 | /grill-with-docs | `/grill-with-docs 逐分支死磕 {change dir} 的 design.md：拷问到共识、对齐术语、边界场景压测、代码与主张不符即揭穿、adr 保存到 @openspec/adr/、术语保存到 @openspec/CONTEXT.md。更新已有文档并标 [grill-amendment]。收敛后 checkpoint-commit grill（多轮中途不提交）。` | design/ADR/CONTEXT 更新 | generation-process ③对抗；非平凡变更 |
| 二 | 4 | /sdflow-spec-review | `/sdflow-spec-review 独立审查 {change dir}` | spec-review-report.md | 编排器：内部 autoplan→并行多镜→**一份**报告；中途不 AskUserQuestion（决策登记进报告）；fresh 子代理替代 /clear；内部 2×checkpoint；改动标 [spec-review-amendment]。**非平凡必跑（主审）** |
| 二 | 5 | HARD-GATE | 人工过 **一份** `spec-review-report.md`（决策登记区已摊开选项+推荐+两方后果）→ 批准设计 | （人工：批准后才进实现） | generation-process 门；**★全流程唯一人类门** |
| 二 | 5.5 | /embedded-test-sop | `/embedded-test-sop 基于 {change dir} 的 specs/ + 评审结论生成 {change}-sop.md 手工测试文档 + log-checks.yaml，存到 {change dir}。` | {change}-sop.md + log-checks.yaml | 嵌入式专属条件触发：TG-02(嵌入式固件) **∧**（启动/复位·状态机·协议 等高风险 **∨** TG-18 有测试计划）；非嵌入式天然不触发 |
| 三 | 6 | /writing-plans | `/writing-plans 按 {change dir} 的 design.md 与评审结论生成原子任务清单 superpowers-plan.md，每任务 TDD，参考 tasks.md 分组；有测试计划则附测试覆盖图。把 design 的领域约束逐字写进 plan 的 Global Constraints。生成后自动以 subagent-driven-development 执行，自动完成全部任务，每任务完成跑测试套件确认无 warning、逐任务 checkpoint-commit。final whole-branch 终审 dispatch 时把 code-checklists/domains/<命中栈>（规则根经 ~/.sdflow/hack/resolve-workflow.sh 解析）作为额外 review lens 附给 reviewer。无法自动解决的记入 buglists 或 todolists` | superpowers-plan.md + 代码 | superpowers + quality-layering 注入点 A；**必跑（计划→实现自动化）** |
| 三 | 7 | /subagent-driven-development | （由步骤 6 自动触发）每任务完成跑测试套件、逐任务 checkpoint；final whole-branch 终审 dispatch 时把 `code-checklists/domains/<命中栈>（规则根经 ~/.sdflow/hack/resolve-workflow.sh 解析）` 作额外 review lens 附给 reviewer | 代码 | quality-layering 注入点 B（领域审前移进生成循环，即时 fix+re-review 闭环） |
| 三 | 8 | /sdflow-code-review | `/sdflow-code-review 每次全跑独立审查 {change dir} 的代码变更（并入 gstack/review 的 scope-drift+完成度审计；能修的自动修标 [impl-review-fix]、修不了/拿不准的记 buglists/todolists；汇总一份 code-review-report.md）。完成后 checkpoint-commit sdflow-code-review。` | code-review-report.md | 编排器：**每次全跑·独立冷·强制主审**（P3c，非高风险才跑）；清单逐条+对抗+历史镜+置信过滤；阶段三无人类门（自动修/裁/defer，不 AskUserQuestion） |
| 三 | 9 | /sdflow-done | `/sdflow-done` | verify-report + hand-off + 归档 + 提交 + 合并 | sdflow-done skill；verify(防假✅证据锚点)→**issues sweep 子步(§2.1,已就位：分诊本change OPEN项入批次→reindex)**→hand-off.md→archive(+delta 同步)→commit→merge；**必跑（闭环）** |

## 三、关键设计决策

1. **git 分支在 ff prompt 内做（带守卫）= 规则 FF-0**：`若不在 feature 分支则 git checkout -b feat/{change}`。分支恰在生成开始时创建，spec 文件随分支落地，幂等。见 [ff-generation-constraints.md](./ff-generation-constraints.md) §FF-0。
2. **子代理 fresh-context 替代 `/clear`（最关键，G1）**：`/clear` 唯一作用是给评审独立上下文；但 sdflow-spec-review/sdflow-code-review/subagent-dev 的评审**本就 fan-out 到 fresh-context 子代理**——独立性是"子代理冷上下文"给的，不是 `/clear` 给的（依据 [quality-layering.md](./reference/quality-layering.md) 自认 `/clear` 只剩边际收益）。故**去掉两个 `/clear`**，管线连续跑。代价：评审末尾"对抗裁决"留热主 session（看过生成过程），一丝合成层偏置——由**反静默压制**（裁掉的 finding 连理由进报告"已裁掉"区）焊死边界。**注意**：子 agent 调度（subagent-dev）运行中仍禁 `/clear`，必须跑完再进下一步。
3. **中途 AskUserQuestion → 决策全登记进报告（G2）**：评审撞到"≥2 方案/核验不了的事实"不中途弹窗，写进报告决策登记区（选项+推荐+两方后果），继续跑完；人工在设计门一次性过报告拍板。评审 findings 互相独立不级联，攒到报告一次决即可。
4. **只在阶段二设计门停一次人类**：grill 是对话岛（人类对抗，不折叠）；设计门是唯一 HARD-GATE。**阶段三无人类门（P3e）**——过设计门后自动跑到 merge：能修的自动修、≥2 方案有把握自动选推荐（记理由）、genuinely 拿不准的 defer 进 buglist/todolist，人类再入口 = 异步读 hand-off.md。
5. **提交 = 步骤显式收尾动作 + 共享脚本兜底（G4/G5）**：不用 hook 驱动提交（"逻辑步骤完成"是语义不是事件）；每步末调 `~/.sdflow/hack/checkpoint-commit.sh`（git add -A + 固定 Conventional message，焊死本机三坑）。grill 多轮中途不提交、只收敛后一次。不 squash（保碎 commit 的细粒度回退点）。hook 仅做"有未提交产物"的警告安全网。
6. **评审两层、不重复**：
   - **设计侧**：sdflow-spec-review 编排器 = autoplan（广审 CEO/design/eng/DX）+ 本项目多镜（领域镜+对抗镜+接地镜）合成一份报告。**autoplan 已含 eng 镜 → 多镜不重复跑 eng**。
   - **代码侧（生成期已三层审，事后强制主审）**：subagent-dev 内三层 fresh-context 审 + **注入点 B** 把 domains 附终审（领域审前移进循环、即时 fix+re-review）；事后 **sdflow-code-review 编排器每次全跑**（并入 gstack/review scope-drift+完成度，P3c 独立冷强制主审，实测抓循环内被说服放过的真问题）。**注入点B 与 sdflow-code-review 并存不是重复**——前者循环内即时闭环、后者事后独立兜底，机制/职责不同，别把任一个优化掉（见 quality-layering.md）。
7. **verify 防假✅（P3f/P3h）**：阶段三去人类门后 verify 是**唯一终门**。每条 ✅ 必附机验锚点（测试名/commit/文件:行），无锚点 ✅ 降级 gap；verify 用强模型 + "Do Not Trust" 冷启、禁弱模型。见 [reference/quality-layering.md](./reference/quality-layering.md)。
8. **闭环用 `sdflow-done`**：verify → hand-off.md → archive → commit → merge，archive 子代理拿 delta **对真实代码核验后再同步** spec。尾部不再需单独 apply/verify/archive。
9. **深度按 TG / 风险**：explore（模糊才跑）、embedded-test-sop（嵌入式高风险才跑）；不分 S/M/L 档。〔Phase C 补：outside voice 默认开，命中 HR-TG 单开领域 cross-model〕

## 四、生成 ↔ 评审 的对称

```
  生成侧(Prevention)            评审侧(Detection)
  ──────────────────────────────────────────────
  ①结构 → config 槽       ┐
  ②约束 → config rules/D  ├─ ff 产出       sdflow-spec-review 编排器(autoplan + 多镜, 一份报告)
  ③过程 → grill(对抗磨硬) ┘                sdflow-code-review 编排器(每次全跑强制主审, 一份报告)
                                          sdflow-done 闭环(verify 防假✅ → hand-off)
  两侧共用 trigger-catalog(TG) 决定深度；连续跑,只在设计门停一次
```

## 五、与规则集的关系

- 本文是**流程编排**；不重复各规则文件内容，只引用。
- `config.yaml` 生成时自动守①②；本文把 explore/grill/sdflow-spec-review/sdflow-code-review/sdflow-done **排成连续序**。
- [reference/quality-layering.md](./reference/quality-layering.md) 管**质量分层 + shift-left 注入点**（生成期三层审、领域清单注入终审、事后 sdflow-code-review 为何是**每次全跑的强制主审**、verify 防假✅）；本文据其结论排序。

## 六、检查清单（跑一个变更时）

- [ ] 问题清晰否？不清晰先 `opsx:explore`
- [ ] ff 是否在 feature 分支上生成（FF-0）？每步是否 checkpoint-commit？
- [ ] grill 是否收敛后才提交（多轮中途不提交）？
- [ ] sdflow-spec-review 是否一份报告 + 决策登记区（无中途 AskUserQuestion）？读了真实代码、过了命中领域清单、对抗裁决？
- [ ] 设计是否过 HARD-GATE（用户批准）才进 writing-plans？（阶段二唯一人类门）
- [ ] sdflow-code-review 是否**每次全跑**（并入 gstack/review scope+完成度、领域 code-checklists、对抗、置信过滤）？
- [ ] 阶段三是否连续跑到 merge（无 /clear、无 step14 人类门）？能修的自动修、拿不准的 defer？
- [ ] sdflow-done 的 verify 是否每条 ✅ 附锚点（防假✅）？是否产出 hand-off.md？

*流程 v2（三阶段连续化）· 配套 generation-process.md（生成）/ spec-review.md（评审）/ trigger-catalog.md（深度）/ reference/quality-layering.md（分层）*
