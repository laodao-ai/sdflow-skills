<!-- 本文件由 hack/gen_workflow_guide.py 从 workflow.md + prompts/ 机械生成。DO NOT EDIT。 -->
<!-- 改 prompt → 改 prompts/step*.md（单一源）；改流程 → 改 workflow.md；然后跑 --write。 -->
<!-- [fix-probe-scan-precision task4 · adr/0039] 本文件是消费仓 openspec/workflow/ 下 -->
<!-- 唯一落地文件（tools/ 与规则均全局单份共享、不再铺设）。文中对其它规则文件的提及 -->
<!-- （如 `quality-layering.md`）已降为纯文字引用，非本文件内的可点链接——那些文件不随 -->
<!-- GUIDE 分发，如需查看请见 sdflow-skills 仓 sdflow-init/assets/workflow/ 对应文件。 -->

# Spec 工作流（端到端总览）

> **定位**：从需求到实现的端到端流程总览，串起 `openspec/workflow/` 的全部规则。
> 本文给**流程骨架 + 每步归属哪条规则**；各步细则见对应规则文件，不在此重复。
> **概念入门**：这套体系的原理、设计思想与实战用法见 `~/.sdflow/workflow/sdflow-guide.html`（自包含 HTML，浏览器直接打开；随 workflow bundle 分发，不入消费仓）。
> **流程本性**：三阶段**尽量连续自动运行**——阶段内部的 `/clear` 由子代理 fresh-context 独立性替代（阶段交界两处仍 SHALL 清，见 §三.2）、
> 中途 AskUserQuestion 改报告决策登记、每步产物 checkpoint 提交；全流程**只在阶段二设计门停一次人类**。

---

## 一、完整流程（唯一线性路径）

```
 阶段一·生成 ── 人类对话岛：拷问 ──────────────────────────────────
   opsx:explore〔条件：问题模糊 / 方向未定〕                      发散,想清要不要 / 是什么
     └─ 问题已清晰则跳过，直接进 /sdflow-spec
     └─ 人示意收敛(如"开搞"/"做吧"/"开 change") → 模型自动 invoke /sdflow-spec
        │
   /sdflow-spec                            澄清(A) → 拷问(B) → 生成(C) 一次连续跑
     └─ 拷问前置于成文；产四件套 + decision-memo.md（承重件）
     └─ 相位 B 起手即 FF-0 三分支判定 + openspec new change
     └─ 相位 B 收敛 / 相位 C 终审各一次 [checkpoint]
     └─ 出口原样贴：/clear → 换档 → sdflow-spec-review（G1 交界例外之一，见 §三.2）
        │
 阶段二·设计审 ── 阶段内部连续,无 /clear（交界两处 SHALL 清:一→二、二→三，见 §三.2）──
   sdflow-spec-review 编排器               Step1 单批 dispatch(自持广审双镜 strategy/plan-eng+领域镜+对抗镜+接地镜+design-voice)→Step3 一份 report
     └─ fresh 子代理替代 /clear 保独立；中途不 AskUserQuestion(决策登记进报告)
     └─ 内部 1×[checkpoint]（sdflow-spec-review 子步）
        │
   〔HARD-GATE：用户批准设计〕            ★全流程唯一人类门——过一份 spec-review-report.md 拍板
        │
 阶段三·ship ── 过设计门后连续跑到 merge,无人类门 ─────────────────
   〔入口前 SHALL /clear（G1 交界例外之二，见 §三.2）；调 /sdflow-ship 时重述 merge 意图〕
   /sdflow-ship {change dir}                一次调用经 ship_gate 确定性台账驱动到底
     ├─ 子步骤 A：实现管线（sdflow-implement，唯一管线）
     │  └─ 逐 ticket/任务 [checkpoint]
     ├─ 子步骤 B：sdflow-code-review（每次全跑·独立冷视角·强制主审 → code-review-report.md）
     │  └─ [checkpoint]
     └─ 子步骤 C：sdflow-done（verify → hand-off.md → archive → commit → merge）
        │  (无 /clear——子 agent 调度中本就禁清；评审 fan-out 的 fresh 子代理即独立性)
        │
   hand-off.md ── 异步 ──▶ 人类读 → 决定开"清理 change" → 作为下个 change 输入
```

> **sdflow-done 含 issues sweep 子步**（§2.1，I5/I6）：verify 判完、写 hand-off 正文前，分诊**本 change**新增的
> OPEN 项入**单一批次**（key=本 change 名）→ 末尾跑 `issues.py reindex` 刷新 INDEX/批次状态 → hand-off 第 2 段引用该批次号
> （不再逐条罗列裸 ID）。脚本分工：`sdflow-issues` 的两池 `scan`/`triage` 分诊 +
> `batch add`/`reindex` 管批次与索引。细则见 `sdflow-done` skill 的 SKILL.md §2.1（配套 skill，不在本 bundle 内，随 sdflow-skills `setup.sh` 安装）。
> **跨模型 outside voice**：sdflow-spec-review / sdflow-code-review 默认开；命中 **HR-TG** 再单开一次领域 cross-model（C2/C3/C4）。调用协议见两 SKILL 的「outside-voice helper 调用协议」节；helper 契约 = `~/.sdflow/hack/outside-voice.sh` 头注释。

## 二、逐步 prompt（可直接复制）

> `{change}` = 变更短名（如 `add-pagination`）；`{change dir}` = `@openspec/changes/add-pagination`；`{topic}` = 探索主题。
> D 约束 / 触发槽 / 画图 / 领域清单已由 `openspec/config.yaml` 的 rules **自动注入** 生成——生成 prompt 无需再内联。
> `[checkpoint]` = 步末调 `~/.sdflow/hack/checkpoint-commit.sh <step> "<描述>"`（过场提交，非交互；区别于最终 `/commit-message`）。（缺失则先在运行 checkout 跑 setup.sh）

| 阶段 | 步 | command/skill | prompt（可复制） | 产出物 | 规则·条件 |
|---|---|---|---|---|---|
| 一 | 1 | /opsx:explore | /opsx:explore {topic} | — | 条件：问题 / 方向模糊、方案未定时先跑；问题清晰直接进步 2。人示意收敛（如"开搞"/"做吧"/"开 change"）→ 模型自动 invoke `/sdflow-spec`（generation-process §四 自动触发规则） |
| 一 | 2 | /sdflow-spec | 一次跑完 澄清(A)→拷问(B)→生成(C)。人可直接触发；模型 SHALL 在人示意收敛或用户描述需求且需要开 change 时自动 invoke，MUST NOT 自主判断"该开 change 了" | proposal/design/specs/tasks + decision-memo.md | generation-process §四；出口序列 = `/clear` → 换档 → `/sdflow-spec-review`（对 G1 的具名例外，见 §三.2） |
| 二 | 3 | /sdflow-spec-review | /sdflow-spec-review 独立审查 {change dir} | spec-review-report.md | 编排器：内部单批 dispatch（自持广审双镜+领域镜+对抗镜+接地镜+design-voice）→**一份**报告；中途不 AskUserQuestion（决策登记进报告）；fresh 子代理替代 /clear；内部 1×checkpoint；改动标 [spec-review-amendment]。**非平凡必跑（主审）** |
| 二 | 4 | HARD-GATE | 人工过 **一份** `spec-review-report.md`（决策登记区已摊开选项+推荐+三面后果(系统/用户/开发循环)+主次判定）→ 批准设计 | （人工：批准后才进实现） | generation-process 门；**★全流程唯一人类门** |
| 三 | 5 | /sdflow-ship | /sdflow-ship {change dir} 全自动完成任务 | tickets.md + 代码 + code-review-report.md + verify-report + hand-off + 归档 + 提交 + 合并 | 一次调用经 ship_gate 确定性台账驱动到底（实现→代码审→收尾）；阶段三无人类门（P3e）；子步骤详见 [§二.1](#二1sdflow-ship-子步骤) |

### 二.1　`/sdflow-ship` 子步骤

`/sdflow-ship {change dir}` 经 ship_gate 确定性台账驱动，内部按序执行三个子步骤（阶段内部无 `/clear`、无人类门）：

#### A. 实现管线

- **唯一管线**：路由至 `sdflow-implement` 出票执行（产出 `tickets.md`〔D5/adr-0033〕）；逐 ticket checkpoint。
- 🔴 **派 implementer / task-reviewer / fix / 终审子代理时，dispatch prompt MUST 原文携带四条通则**——子代理是 fresh context，看不见 CLAUDE.md。

#### B. sdflow-code-review

编排器：**每次全跑·独立冷·强制主审**〔P3c〕。Step1 自持 scope 审计（scope-drift + 完成度审计）+ 领域镜 + 对抗镜 + 历史镜 + 机械引用核（`findings_ref_check.py`，DD4）+ 二元裁决。能修自动修标 `[impl-review-fix]`、修不了/拿不准 defer → buglist/todolist；汇总一份 `code-review-report.md`。跨模型 outside voice（always code voice + HR-TG 领域 cross-model）。checkpoint。

#### C. sdflow-done

verify（防假✅，证据锚点）→ issues sweep 子步（§2.1：分诊本 change OPEN 项入批次 → reindex）→ hand-off.md → archive（+ delta 对码核验/同步）→ commit → merge。**必跑（闭环）**。

## 三、关键设计决策

1. **git 分支在生成起手做（带守卫）= 规则 FF-0，三分支判定**：保护分支（main/master）→ `git checkout -b feat/{change}`；已在 `feat/{本 change}` → 跳过（真幂等）；**在其它 feature 分支 → halt 问人**（从当前切出 / 回 base 切出 / 就地继续）。分支恰在生成开始时创建，spec 文件随分支落地。见 `ff-generation-constraints.md` §FF-0。
2. **`/clear` 只在两处阶段交界用，阶段内部不用（G1）**：阶段内部不用 `/clear`（评审独立性由 fresh 子代理提供，依据 `quality-layering.md`）。两处阶段交界 SHALL `/clear`：**阶段一 → 阶段二**（cache 按模型隔离 + 产/审错档纪律）、**阶段二 → 阶段三**（盘面纪律 + 产物自足性检验 + 去作者偏置）。完整推导（为什么恰是这两处、每条理由的证据、边界）见[附录 A](#附录-ag1-完整分析clear-纪律为何如此设计)。
3. **中途 AskUserQuestion → 决策全登记进报告（G2）**：评审撞到"≥2 方案/核验不了的事实"不中途弹窗，写进报告决策登记区（**≥2 方案**：选项+推荐+三面后果(系统/用户/开发循环)+主次判定；**核验不了的事实**：待核验证据+风险+默认处理，不强制三镜），继续跑完；人工在设计门一次性过报告拍板。评审 findings 互相独立不级联，攒到报告一次决即可。
4. **只在阶段二设计门停一次人类**：拷问是对话岛（人类对抗，不折叠，见 `/sdflow-spec` 相位 B）；设计门是唯一 HARD-GATE。**阶段三无人类门（P3e）**——过设计门后自动跑到 merge：遇 ≥2 方案按三级决策协议 `T10-choice`〔具名规则，取代旧「T10」单一编号；"T10" 保留为历史别名〕：①有客观判据（测试/断言/基准可判）→ 自动选并按三镜 + 主次记理由；②无客观判据 → 派 **strong 档**对抗镜复核推荐项，通过方自动选（复核记录进报告）；③复核不过或无从复核 → defer 进 buglist/todolist 由 hand-off 引导清理。禁以自评置信为唯一依据。人类再入口 = 异步读 hand-off.md。
5. **提交 = 步骤显式收尾动作 + 共享脚本兜底（G4/G5）**：不用 hook 驱动提交（"逻辑步骤完成"是语义不是事件）；每步末调 `~/.sdflow/hack/checkpoint-commit.sh`（git add -A + 固定 Conventional message，焊死本机三坑）。不 squash（保碎 commit 的细粒度回退点）。hook 仅做"有未提交产物"的警告安全网。
6. **评审两层、不重复**：
   - **设计侧**：sdflow-spec-review 编排器 = 自持广审双镜（strategy/plan-eng，按 base R 项划分）+ 本项目多镜（领域镜+对抗镜+接地镜，按 domains/ R 项划分）单批并行 dispatch 合成一份报告。base 与 domains 两层清单本就互斥，无需去重协商。
   - **代码侧（生成期已有双轴审，事后强制主审）**：`sdflow-implement` 每 ticket **双轴审**（Standards 轴 + Spec 轴，fresh-context 子代理；Standards 轴 dispatch 模板**必填槽**把 domains 领域清单前移进循环、即时 fix+re-review）；事后 **sdflow-code-review 编排器每次全跑**（Step1 自持 scope 审计 scope-drift+完成度，P3c 独立冷强制主审，实测抓循环内被说服放过的真问题）。**每 ticket 双轴审与 sdflow-code-review 并存不是重复**——前者循环内即时闭环、后者事后独立兜底，机制/职责不同，别把任一个优化掉（见 quality-layering.md）。
7. **verify 防假✅（P3f/P3h）**：阶段三去人类门后 verify 是**唯一终门**。每条 ✅ 必附机验锚点（测试名/commit/文件:行），无锚点 ✅ 降级 gap；verify 用强模型 + "Do Not Trust" 冷启、禁弱模型。见 `reference/quality-layering.md`。
8. **闭环用 `sdflow-done`**：verify → hand-off.md → archive → commit → merge，archive 子代理拿 delta **对真实代码核验后再同步** spec。尾部不再需单独 apply/verify/archive。
9. **深度按 TG / 风险**：explore（模糊才跑）；不分 S/M/L 档。〔Phase C 补：outside voice 默认开，命中 HR-TG 单开领域 cross-model〕

## 四、生成 ↔ 评审 的对称

```
  生成侧(Prevention)            评审侧(Detection)
  ──────────────────────────────────────────────
  ①结构 → config 槽       ┐
  ②约束 → config rules/D  ├─ 生成产出       sdflow-spec-review 编排器(自持广审双镜 + 多镜, 一份报告)
  ③过程 → 拷问(对抗磨硬)  ┘                sdflow-code-review 编排器(每次全跑强制主审, 一份报告)
                                          sdflow-done 闭环(verify 防假✅ → hand-off)
  两侧共用 trigger-catalog(TG) 决定深度；连续跑,只在设计门停一次
```

## 五、与规则集的关系

- 本文是**流程编排**；不重复各规则文件内容，只引用。
- `config.yaml` 生成时自动守①②；本文把 explore/sdflow-spec/sdflow-spec-review/sdflow-code-review/sdflow-done **排成连续序**。
- `reference/quality-layering.md` 管**质量分层 + shift-left 注入点**（生成期三层审、领域清单注入终审、事后 sdflow-code-review 为何是**每次全跑的强制主审**、verify 防假✅）；本文据其结论排序。

## 六、检查清单（跑一个变更时）

- [ ] 问题 / 方向清晰否？不清晰先 `opsx:explore`，人示意收敛才自动接 `/sdflow-spec`
- [ ] 生成起手是否过 **FF-0 三分支判定**（保护分支建 / 本 change 分支跳过 / 其它 feature 分支 halt 问人）？每步是否 checkpoint-commit？
- [ ] `sdflow-spec` 相位 B 拷问是否照常全深度执行（触发方式改变不缩减拷问）？
- [ ] `/clear` 只在**两处阶段交界**用过（阶段一→阶段二、阶段二→阶段三；G1 具名例外）？**阶段内部**全程无 `/clear`？
- [ ] sdflow-spec-review 是否一份报告 + 决策登记区（无中途 AskUserQuestion）？读了真实代码、过了命中领域清单、对抗裁决？
- [ ] 设计是否过 HARD-GATE（用户批准）才进阶段三？（阶段二唯一人类门）
- [ ] 阶段三实现管线是否正确路由至 `sdflow-implement`（唯一管线，无需判 impl-pipeline 键）？
- [ ] sdflow-code-review 是否**每次全跑**（Step1 自持 scope 审计 scope+完成度、领域 code-checklists、对抗、机械引用核+二元裁决）？
- [ ] 阶段三是否连续跑到 merge（**阶段内部**无 /clear——含 sdflow-implement 执行模式、code-review→done 交接、无人类门；需控上下文用 /compact）？能修的自动修、拿不准的 defer？
- [ ] sdflow-done 的 verify 是否每条 ✅ 附锚点（防假✅）？是否产出 hand-off.md？

## 附录 A：G1 完整分析（`/clear` 纪律为何如此设计）

> 本节是**演进推导**（DOC-1 附录）：正文（§三.2）只留结论，这里留完整论证。**跑流程不用读本节**——
> 只在需要理解「为什么恰是这两处，不多不少」时查。

**评审独立性由子代理 fresh-context 提供，不由 `/clear` 提供**：sdflow-spec-review/sdflow-code-review/sdflow-implement 的评审**本就 fan-out 到 fresh-context 子代理**——独立性是"子代理冷上下文"给的，不是 `/clear` 给的（依据 `quality-layering.md`）。故**阶段内部不用 `/clear`**，管线连续跑。代价：评审末尾"对抗裁决"留热主 session（看过生成过程），一丝合成层偏置——由**反静默压制**（裁掉的 finding 连理由进报告"已裁掉"区）焊死边界。**注意**：子 agent 调度（sdflow-implement）运行中仍禁 `/clear`，必须跑完再进下一步。

🔴 **上述结论只覆盖「评审独立性」这一个面，MUST NOT 据此推出「全流程不用 `/clear`」**。曾有措辞称「`/clear` 唯一作用是给评审独立上下文」——**该前提为假**，由它导出的全流程禁令是**过度泛化**：`spec-workflow` spec 的对应 Requirement 也只约束「MUST NOT 依赖 `/clear` 隔离**评审**上下文」，从未禁止全流程。

🔴 **阶段交界 SHALL 用一次 `/clear`（两处，理由各自都在上述结论射程之外）**：

- **阶段一 → 阶段二**（`/sdflow-spec` 出口序列 `/clear` → 换档 → `/sdflow-spec-review`）：① **cache 按模型隔离**——拖着阶段一的旧上下文切换模型档位 = 缓存作废、全价重付；② **产 / 审错档纪律**——阶段一的产出档与阶段二的评审档本就不同，换档才是这次 `/clear` 的真实动因。
- **阶段二 → 阶段三**（设计门通过后、`/sdflow-ship` 之前）：① **盘面纪律**——阶段三链序是「零跨步内存状态」，`NEEDS_CONTEXT` MUST 仅从盘面（design/specs/ticket 文本）自答；热编排器会拿对话记忆替代盘面，而**这一条 fresh 子代理防不住**（implementer 是冷的，回答它的编排器是热的）；② **产物自足性检验**——冷启动跑阶段三是对「四件套 + tickets 是否真的够用」的真实检验，热 session 会在盘面缺信息时无声补上、缺口永不暴露；③ **去作者偏置**——实现期若设计被证伪，热 session 倾向合理化而非叫停。**代价**：编排器需重读 SKILL 与产物（一次性），且 MUST 在调用 `/sdflow-ship` 时**重述 merge 意图**（它从调用语透传、不在盘上）。

🔴 **MUST NOT 拿「主审裁决需要冷视角」当任一处例外的理由**——那一条已被上述结论正面回答（独立性由 fan-out 的 fresh 子代理提供，不由 `/clear` 提供），拿它当依据是漏查。

**边界**：仅这两处**阶段交界**。**阶段内部一律禁 `/clear`**——阶段二内部、阶段三内部（含 sdflow-implement 调度期间、code-review → done 交接）。阶段三内部需要控上下文时用 **`/compact` 而非 `/clear`**：merge 意图不在盘上、`VERIFY_FAIL` 恢复也要重建理解，而 done 的 verify 本就是冷子代理、清不清都一样冷。

*流程 v2（三阶段连续化，单轨线性）· 配套 generation-process.md（生成）/ spec-review.md（评审）/ trigger-catalog.md（深度）/ reference/quality-layering.md（分层）*

*演进史（去掉了什么、为什么这么改）→ `workflow-history.md`——不是当前约束，跑流程不用读。*
