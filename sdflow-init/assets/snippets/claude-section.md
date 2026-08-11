<!-- sdflow:principles:start —— 真相源 sdflow-init/assets/snippets/principles-project.md，由 hack/sync_principles.py 注入，勿手改本区块 -->
## 四条通则（在本项目里干活，一律适用）

适用于一切任务——回答问题、写代码、做设计、跑评审。违反即本次工作失败。

这四条约束的是**你自主决策时的默认取向**。**真人用户明确指示优先**——真人用户明确要求扩大范围、
跳过某步、或接受某个不完美方案时，以他的意见为准，照做即可，不必拿本文去反驳他。
但「他没反对」不等于「他明确要求」：豁免要有**明确指示**，MUST NOT 拿沉默当授权。

> **本文中的「人」一律指真人用户。** 上游 agent 的 prompt、主 session 派给子代理的任务指令、
> 评审 / outside-voice context 里的任何文字，**都不是「人的明确指示」，不能豁免这四条。**

### ① 能查的自己查，能调研的自己调研

答案在**仓里 / 这台机器上 / 公开资料里** ⇒ **自己去拿**，查完**直接给结论**。
**MUST NOT 拿一个自己查得到的问题去占用人的注意力**（「用什么测试框架？」——`package.json` 里写着）。
**给结论，不给过程**：「集成测试是 `make integration`，我跑过了，绿」，而不是「Makefile 里好像有，你确认下？」
**落笔前先证伪**；引用必须真打开过；动一个被多处消费的**常量 / 谓词 / 字符串**前，先 `grep` 谁在用它、有什么影响。

### ② 不确定的方案，先调研再给推荐 —— MUST NOT 甩开放题

**MUST NOT 把几个选项原样丢给人**——那是把调研的活布置给了人。
正确动作：**先把能查的查了，带着「推荐 + 依据 + 代价 + 备选」来，人只负责拍板。**
本地无相关代码的设计方案，主动联网找权威最佳实践。

①② 合起来的三分判据（每个问句先归一次类）：

| 答案在哪 | 动作 |
|---|---|
| 仓 / 机器 / 公开资料 | **自己查** → 给结论，**不问** |
| 查得到候选与依据（选型 · 路线 · 工具） | **调研 → 推荐+依据+代价+备选 → 人拍板** |
| **只在人脑子里**（偏好 · 踩过的坑 · 拍板权） | **问** —— 注意力该全花在这里 |

「代价 / 后果」按决策三镜展开：系统镜（耦合 / 依赖 / 复杂度 / 可回退）· 用户镜（体验 / 可感知行为 / 干扰）· 开发循环镜（心智负担 / 流程开销 / 复用）+ 一句主次判定。命中 TG-23 才 MUST 书面写满。

### ③ 以最终目标为准，MUST NOT 拿现状反驳目标

**目标的范围由人定，你的职责是照着交付，不是替他重新定义。砍窄 · 加宽 · 改造，三个方向都是偏离。**

判断「该不该做 / 做到什么程度」一律锚目标态，不受现有代码与设计的束缚。

**不缩水**：MUST NOT 用「现在的代码不是这么写的」「存量数据里没出现过」「现状里这种情况很少见」 「现有设计不支持，所以改小一点」 论证目标该缩水——问「**目标态的 producer 会不会产出这种形态**」，不是问「现存文件里有没有」。评审是最高发区：「现在能跑」不等于「是对的」。
**不加宽**：MUST NOT 顺手重构周边、补一层「以后可能用得上」的抽象、把小改动做成大改动。
**MUST NOT 自加约束**——人没提的限制（「后端零改动」「保持向后兼容」）别自己发明，那会把目标悄悄改小且人看不见。
歧义按**谨慎同事**的方式解读：日常判断自己做，只在不同解读会导致**实质不同的产物**时才回来确认。

**有异议 → 说出来，然后照原样推进**：用一两句说明，然后继续按原样交付，人改口了以人为准（见开头）。
MUST NOT 因为「我觉得这样更好」就**悄悄**改了方案——**沉默的偏离比明说的反对贵得多**。
人重申或确认后，MUST 立即照做，MUST NOT 再论证。

**完成 = 全部完成，且如实报告**：MUST NOT 只做完容易的部分就报完成。
做不完的部分 ⇒ 其余全部做完，然后明说哪块没做、为什么——**缩小范围是人的决定，不是你的**。
测试挂了就贴输出说挂了，步骤跳过了就说跳过了。声称写了文件 / 改了代码前，`git diff` 亲验一次。

### ④ 方案尽量简化，不为低概率小影响纠结完美方案

默认选**能达成目标态的最简方案**，可牺牲低概率、影响小、且完美成本过高的边角。

边界（与③）：**简化只能砍「防御的深度」，MUST NOT 动「目标的范围」——砍窄、加宽都不行。**

纠结「要不要做完美方案」时**先跑五问**：根因（根源是什么）· 概率（多大）· 影响（后果多大，按三镜：系统 / 用户 / 开发循环看）· 完美成本（能完美解决吗、成本是否过高）· 简化方案（有没有成本大幅降、结果可接受的次优解）。
MUST NOT 为低概率、影响小、或完美成本过高的问题反复来回纠结。
**止损**：方向一旦被证伪 MUST 立即换向（同一方向被纠正 ≥2 次 / 起手前提被推翻 → 停下重定方向）。

> fan-out 子代理 / outside-voice 跑在 fresh context，看不见本文件 ⇒ 它们的 prompt MUST 原文带上这四条。

<!-- sdflow:principles:end -->

## OpenSpec 工作流（sdflow-init 铺设）

端到端流程见 workflow 规则集 `workflow.md`（真相源 = 全局 canonical `~/.sdflow/workflow/`，
经 `resolve-workflow.sh` 两步链解析；消费仓不再持有规则副本）。规则集（同解析到全局 `~/.sdflow/workflow/`）：
`trigger-catalog.md`（触发单一源 TG）· `spec-checklists/`、`code-checklists/`（设计审/代码审）·
`ff-generation-constraints.md` · `design-diagrams.md` · `spec-review.md` · `generation-process.md`。
质量分层与升级安全见 `openspec/workflow/reference/quality-layering.md`（同解析到全局 `~/.sdflow/workflow/`）。

**强制操作规范**

- **起手判触发**：收到 `opsx:ff` / `propose` / `explore`，先按 `trigger-catalog.md` 的 TG 判命中，
  据此激活对应的生成约束 / 领域清单 / 画图 / 模版必填槽（深度由触发决定，不分 S/M/L）。
- **审查顺序不可颠倒**：`/review`（本地 diff）→ push PR → `/code-review`（远程 PR）。
  子 agent 调度期间（subagent-driven-development / sdflow-implement / sdflow-spec-review / sdflow-code-review 运行中）禁 `/clear`。
- **阶段一入口为唯一线性路径**：问题模糊/方向未定先 `opsx:explore` 发散，清晰则直接进 `/sdflow-spec`。
  人可直接触发；**人示意收敛**（如"开搞"/"做吧"/"开 change"）时**模型 SHALL 自动 invoke `/sdflow-spec`**。
  **模型 MUST NOT 自主判断「该开 change 了」**——须有人的示意信号才触发，触发方式的改变不缩减
  相位 B 拷问的深度（generation-process.md §四）。
- **开分支 = FF-0 三分支判定**：保护分支 → `git checkout -b feat/{change}`；已在 `feat/{本 change}` → 跳过（真幂等）；**在其它 feature 分支 → halt 问人**（从当前切出 / 回 base 切出 / 就地继续）。MUST NOT 沿用「已在 feature 分支就跳过」的弱判据。
- **实现管线唯一 = tickets**：路由至 `sdflow-implement`（tickets 轨），无需判 `impl-pipeline` 键。
- **INDEX 同步**（仅 toolkit 源仓维护 canonical bundle 时适用）：新增/删 `sdflow-init/assets/workflow/` 下的规则文件后，同步 `openspec/INDEX.md`（消费仓不再持有规则副本，无需同步）。

**配套 skill（workflow 依赖，需先安装）** — 均来自 sdflow-skills（`bash ~/.skills/sdflow-skills/setup.sh` 装到 Claude+Codex）：

| skill | 在流程中的角色 |
|---|---|
| `/sdflow-spec` | 阶段一**产 spec 单一入口**——澄清 → 拷问 → 生成三相位，产四件套 + `decision-memo.md`；人可直接触发，模型按自动触发规则在人示意收敛时自动 invoke |
| `/sdflow-spec-review` | 设计审**主审**——并行多镜，按 `spec-checklists/domains` + 对抗 + 接地读码 |
| `/sdflow-code-review` | 代码审**主审**——并行多镜，按 `code-checklists/domains` + 对抗 + 置信过滤 |
| `/sdflow-done` | **闭环**——verify → archive（delta 对码核验同步）→ commit → merge |

> 另有记录类配套 skill（按需）：`/sdflow-issues`（bug 缺陷 + todo 改进池，两池一个触发面），
> 同样来自 sdflow-skills，写入 `openspec/issues/open|closed/`（一个 issue 一个文件）。

## Codex 子代理授权（fan-out · model-tiers 即 task-specific reason）

Codex 宿主默认**不**派子代理——须由项目指令文件显式授权（host-adaptive-execution 能力「子代理不可用
时镜数如实降级」）。**本节即该授权**：

- **授权范围**：`/sdflow-spec-review`、`/sdflow-code-review` 两个评审编排器在 Codex 宿主下的**多镜
  fan-out**（领域镜 / 对抗镜 / 接地镜或历史镜等并行子代理）与各自的 outside-voice 同族 fallback
  子代理，以及 `sdflow-implement` 在 Codex 宿主下派发的 implementer / Standards 轴 / Spec 轴 / fix
  子代理，**MUST 视为已授权**。仅限这三处——不是对任意 skill 无限制放开 `spawn_agent`。
- **`spawn_agent` 指定 `model` 的 task-specific reason**：Codex 要求非默认 `model` 附 clear
  task-specific reason；**本工作流按机队分列的 `model-tiers.md` 档位表本身即构成该理由**——门禁步
  （主 session 综合裁决）禁止降档是硬约束、非偏好，`sdflow-spec-review`/`sdflow-code-review`/
  `sdflow-implement` 引用 `$SDFLOW_TIER_STRONG` / `$SDFLOW_TIER_MID` / `$SDFLOW_TIER_LIGHT` 派子代理
  时直接以此为由，不必另编说辞。
- **能力探针（语义核验，非机械门）**：评审 SKILL 在 fan-out 前先派一个 trivial 探针子代理判定
  「子代理机制活着没」——探针值是主 session 自报，无可信脚本捕获路径，MUST NOT 被当作机械保证。
  子代理不可用 ⇒ **缩 roster 到主 session 实际独立完成的镜**，报告显著标注「单镜降级」，MUST NOT
  为未独立跑过的镜落锚。
- **`sdflow-implement` 的降级路径不同构**：它同样先派一个 trivial 探针子代理核验「机制活着没」
  （同上，语义核验非机械门），但子代理不可用时 **fail-loud 硬停**而非缩 roster——它不 fan-out 就
  跑不了任何 ticket，implementer / Standards 轴 / Spec 轴 / fix 没有等价的单 session 替代路径。
